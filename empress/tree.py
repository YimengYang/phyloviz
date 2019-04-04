from skbio import TreeNode
import pandas as pd
import numpy as np
import time
from operator import attrgetter
import empress.tools as tools

DEFAULT_COLOR = 'AAAAAA'
SELECT_COLOR = '00FF00'


class Tree(TreeNode):
    """
    Attributes
    ----------
    length
    leafcount
    height
    depth

    Notes
    -----
    `length` refers to the branch length of a node to its parent.
    `leafcount` is the number of tips within a subtree. `height` refers
    to the longest path from root to the deepst leaf in that subtree.
    `depth` is the number of nodes found in the longest path.
    """

    def __init__(self, use_lengths=False, **kwargs):
        """ Constructs a Dendrogram object for visualization.

        Parameters
        ----------
        use_lengths: bool
            Specifies if the branch lengths should be included in the
            resulting visualization (default True).

        Returns
        -------

        """
        super().__init__(**kwargs)
        self.childRem = -1

    @classmethod
    def from_tree(cls, tree, use_lengths=True):
        """ Creates an UnrootedDendrogram object from a skbio tree.

        Parameters
        ----------
        tree : skbio.TreeNode
            Input skbio tree

        Returns
        -------
        UnrootedDendrogram

        """
        for n in tree.postorder():
            n.__class__ = Tree
            n.tip_count = 0


        tree.update_geometry(use_lengths)
        return tree

    def update_geometry(self, use_lengths, depth=None):
        """Calculate tree node attributes such as height and depth.

        Parameters
        ----------
        use_lengths: bool
           Specify if the branch length should be incorporated into
           the geometry calculations for visualization.
        depth: int
           The number of nodes in the longest path from root to leaf.
        This is agnostic to scale and orientation.

        """
        # i = 0
        for node in self.postorder():
            # node.name = i
            # i += 1
            if node.length is None or not use_lengths:
                if not use_lengths:
                    if node.is_tip():
                        node.length = 5
                    else:
                        node.length = 1
                else:
                    node.length = 0

            node.depth = (depth or 0) + node.length

            children = node.children
            if children:
                node.height = max([c.height for c in children]) + node.length
                node.leafcount = sum([c.leafcount for c in children])

            else:
                node.height = node.length
                node.leafcount = 1

    def coords(self, height, width):
        """ Returns coordinates of nodes to be rendered in plot.

        Parameters
        ----------
        height : int
            The height of the canvas.
        width : int
            The width of the canvas.

        Returns
        -------
        edgeMeta : pd.DataFrame (Edge metadata)
            index : str
                Name of node.
            Node id: str
                Name of node
            x : float
                x-coordinate of node.
            y : float
                y-coordinate of node.
            Parent id:
                Name of parent
            px : float
                x-coorinate of parent
            py: float
                y-coordinate of parent
        centerX : float
            x coordinate of root node
        centerY : float
            y coordinate of root
        scale : float
            largest scaling factor in which the tree can fit in the canvas.
        """

        # calculates coordinates of all nodes and the shortest/longest branches
        scale = self.rescale(width, height)
        centerX = self.x2
        centerY = self.y2

        for node in self.postorder():
            node.x2 = node.x2 - centerX
            node.y2 = node.y2 - centerY

        self.assign_ids()
        edgeMeta = self.to_df()
        print('calculating depth level of each node')
        self.clade_level()

        print('calculating number of tips per subclade')
        self.tip_count_per_subclade()

        print('calculating clade info')
        self.create_clade_info()
        return edgeMeta

    def to_df(self):
        """ Creates a dataframe from the tree
        """
        # edge metadata
        print('starting to create dictionary')

        edgeData = []

        for node in self.postorder():
            node.alpha = 0.0
            for child in node.children:
                item = [
                        child.name,
                        child.id,
                        child.is_tip(),
                        child.x2,
                        child.y2,
                        node.name,
                        node.x2,
                        node.y2,
                        DEFAULT_COLOR,
                        DEFAULT_COLOR,
                        True,
                        True,
                        1,
                        1
                        ]
                edgeData.append(item)

        print('create pandas')
        index_list = pd.Index([
                'Node_id',
                'unique_id',
                'is_tip',
                'x',
                'y',
                'Parent_id',
                'px',
                'py',
                'node_color',
                'branch_color',
                'node_is_visible',
                'branch_is_visible',
                'width',
                'size'])
        # convert to pd.DataFrame
        edgeMeta = pd.DataFrame(
            edgeData,
            columns=index_list)
        print('done creating pandas')
        return edgeMeta

    def from_file(self, file_name):
        """ sets the (x, y) coords of each node in tree, node depth, number of tips under
        node, and clade collapse info from file
        file format:
        x
        y
        # tips
        depth
        starting angle
        total angle
        longest branch (length)
        smallest branch (length)
        """
        with open(file_name, 'r') as file:
            for node in self.postorder():
                node.x2 = float(file.readline())
                node.y2 = float(file.readline())
                node.tip_count = int(file.readline())
                node.level = int(file.readline())
                node.sa = float(file.readline())
                node.ta = float(file.readline())
                node.lb = float(file.readline())
                node.sb = float(file.readline())


    def rescale(self, width, height):
        """ Find best scaling factor for fitting the tree in the figure.
        This method will find the best orientation and scaling possible to
        fit the tree within the dimensions specified by width and height.

        Parameters
        ----------
        width : float
            width of the canvas
        height : float
            height of the canvas

        Returns
        -------
        best_scaling : float
            largest scaling factor in which the tree can fit in the canvas.

        Notes
        -----

        """
        angle = (2 * np.pi) / self.leafcount

        best_scale = 0
        for i in range(60):
            direction = i / 60.0 * np.pi

            (max_x, min_x, max_y, min_y) = self.update_coordinates(
                1.0, 0, 0, direction, angle)

            x_diff = max_x - min_x
            width_min = 0
            if x_diff != 0:
                width_min = float(width) / x_diff
            y_diff = max_y - min_y
            height_min = 0
            if y_diff != 0:
                height_min = float(height) / y_diff
            scale = min(width_min, height_min)
            scale *= 0.95  # extra margin for labels
            if scale >= best_scale:
                best_scale = scale
                mid_x = width / 2 - ((max_x + min_x) / 2) * scale
                mid_y = height / 2 - ((max_y + min_y) / 2) * scale
                best_args = (scale, mid_x, mid_y, direction, angle)

        self.update_coordinates(*best_args)
        return best_scale

    def update_coordinates(self, s, x1, y1, a, da):
        """ Update x, y coordinates of tree nodes in canvas.
        `update_coordinates` will updating the plotting parameters for
        all of the nodes within the tree.
        This can be applied when the tree becomes modified (i.e. pruning
        or collapsing) and the resulting coordinates need to be modified
        to reflect the changes to the tree structure.

        Parameters
        ----------
        s : float
            scaling
        x1 : float
            x midpoint
        y1 : float
            y midpoint
        a : float
            angle (degrees)
        da : float
            angle resolution (degrees)

        Returns
        -------
        points : list of tuple
            2D coordinates of all of the nodes.

        Notes
        -----

        """

        max_x = float('-inf')
        min_x = float('inf')
        max_y = float('-inf')
        min_y = float('inf')

        # calculates self coords/angle
        # Constant angle algorithm.  Should add maximum daylight step.
        x2 = x1 + self.length * s * np.sin(a)
        y2 = y1 + self.length * s * np.cos(a)
        (self.x1, self.y1, self.x2, self.y2, self.angle) = (x1, y1, x2, y2,
                                                            a)

        for node in self.preorder(include_self=False):
            x1 = node.parent.x2
            y1 = node.parent.y2

            # init a
            a = node.parent.angle

            # same modify across nodes
            a = a - node.parent.leafcount * da / 2

            # check for conditional higher order
            for sib in node.parent.children:
                if sib != node:
                    a += sib.leafcount * da
                else:
                    a += (node.leafcount * da) / 2
                    break

            # Constant angle algorithm.  Should add maximum daylight step.
            x2 = x1 + node.length * s * np.sin(a)
            y2 = y1 + node.length * s * np.cos(a)
            (node.x1, node.y1, node.x2, node.y2, node.angle) = (x1, y1, x2,
                                                                y2, a)

            max_x, min_x = max(max_x, x2), min(min_x, x2)
            max_y, min_y = max(max_y, y2), min(min_y, y2)

        return (max_x, min_x, max_y, min_y)

    def find_shortest_longest_branches(self):
        """ Finds the shortest and longest branches() in each node's subtree.

        Parameters
        ----------

        Returns
        -------

        """
        # TODO: make this a different data structure
        for node in self.postorder():
            if node.is_tip():
                node.shortest = [node.x2, node.y2]
                node.longest = [node.x2, node.y2]
            else:
                # calculate shortest branch node
                node.shortest = min([child.shortest for child in
                                     node.children],
                                    key=attrgetter('depth'))

                # calculate longest branch node
                node.longest = max(
                    [child.longest for child in node.children],
                    key=attrgetter('depth'))

    def node_coords(self):
        """ Returns the coordinates of all nodes in the tree
        """
        node_data = {}
        for node in self.postorder():
            coords = {'x': node.x2, 'y': node.y2}
            attr = {'color': DEFAULT_COLOR}
            node_data[node.name] = {**coords, **attr}

        # convert to pd.DataFrame
        index_list = pd.Index(['x', 'y', 'color'])
        node_data = pd.DataFrame(node_data, index=index_list).T

        return node_data

    def create_sector_info(self):
        """
        Pre-caclulates left most branch, right most branch, length of deepest branch,
        and length of shallowest branch for each node in tree
        """
        for clade in self.postorder():
            tips = clade.tips()
            clade_ancestor = clade.parent
            center_coords = (clade.x2, clade.y2)
            ancestor_coords = (clade_ancestor.x2 - clade.x2, clade_ancestor.y2 - clade.y2)
            points = [[tip.x2 - clade.x2, tip.y2 - clade.y2] for tip in tips]
            s = tools.sector_info(points, center_coords, ancestor_coords)

    def tip_count_per_subclade(self):
        """
        calculates the number of tips in each subclade of the tree.
        """
        for tip in self.tips():
            while tip is not None:
                tip.tip_count += 1
                tip = tip.parent

    def clade_level(self):
        """
        calculates the depth of each node in self.tree
        """
        for node in self.levelorder():
            node.level = len(node.ancestors())

    def create_clade_info(self):
        for clade in self.postorder():
            if not clade.is_tip() and clade is not self:
                tips = clade.tips()
                clade_ancestor = clade.parent
                center_coords = (clade.x2, clade.y2)
                ancestor_coords = (clade_ancestor.x2 - clade.x2, clade_ancestor.y2 - clade.y2)
                points = [[tip.x2 - clade.x2, tip.y2 - clade.y2] for tip in tips]
                try:
                    s = tools.sector_info(points, center_coords, ancestor_coords)
                except:
                    print(points, clade.name, clade.level)
                clade.sa = s['starting_angle']
                clade.ta = s['theta']
                clade.lb = s['largest_branch']
                clade.sb = s['smallest_branch']
            else:
                clade.sa = 0
                clade.ta = 0
                clade.lb = 0
                clade.sb = 0

    def get_clade_info(self, clade):
        info = {
            'center_x': clade.x2, 'center_y': clade.y2,
            'starting_angle': clade.sa, 'theta': clade.ta,
            'largest_branch': clade.lb, 'smallest_branch': clade.sb}
        return info

    def test(self):
        print('test')


    def polar_to_rec(r, theta):
        """
        Convert polar coordinates to rectangular
        """
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        return(x, y)

    def circular_coords(self, width, height):
        """
        Calculate circular layout coordinates

        Parameters
        ----------
        height : int
            The height of the canvas.
        width : int
            The width of the canvas.

        Returns
        -------
        edgeMeta : pd.DataFrame (Edge metadata)
            index : str
                Name of node.
            Node id: str
                Name of node
            x : float
                x-coordinate of node.
            y : float
                y-coordinate of node.
            Parent id:
                Name of parent
            px : float
                x-coorinate of parent
            py: float
                y-coordinate of parent
        arcMeta : pd.DataFrame (Arc metadata) (x1->x2, clockwise)
            id1:
            x1:
            y1:
            id2:
            x2:
            y2:

        """
        centerX = width / 2
        centerY = height / 2

        self.radius = 0
        # Calculate radius
        for node in self.preorder(include_self=False):
            node.radius = node.parent.radius + node.length

        # Calculate theta
        tips = list(self.tips())
        delta = len(tips) / (2 * np.pi)
        theta = 0
        for node in tips:
            node.theta = theta
            theta += delta
            node.x, node.y = self.polar_to_rec(node.radius, node.theta)

        # Calculate edges
        for node in self.postorder():
            node.x



        edgeMeta = self.to_df()
