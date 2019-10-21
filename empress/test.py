import numpy as np
import numpy.testing as npt
from biom import Table, load_table
from biom.util import biom_open
from skbio import TreeNode
import skbio.diversity

tree = './data/crawford.tre'
table = './data/crawford.biom'

table_inmem = load_table(table)
tree_inmem = skbio.TreeNode.read(tree)
print(table_inmem)
print(tree_inmem)

ids = table_inmem.ids()
otu_ids = table_inmem.ids(axis='observation')
print(otu_ids)
cnts = table_inmem.matrix_data.astype(int).toarray().T
exp = skbio.diversity.beta_diversity(
        'unweighted_unifrac', 
        cnts,
        ids=ids, otu_ids=otu_ids,
        tree=tree_inmem
    )
print(exp.data)
