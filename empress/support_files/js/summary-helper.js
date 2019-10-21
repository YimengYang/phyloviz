define([], function() {

    /**
     * @class SummaryHelper
     * Class functions for generating summary used in empress
     */
    function SummaryHelper() { };

    /**
     * Returns unifrac value for 2 set of sample IDs given biom table
     * @param {BiomTable} biomTable - biom table that contains info about samples
     * @param {BPTree} tree - bp tree
     * @param {Array} sIds1 - First array of sample IDs to calculate unifrac for
     * @param {Array} sIds2 - Second array of sample IDs to calculate unifrac for
     *
     * @return{Number}
     */
     SummaryHelper.unifrac = function(biomTable, tree, sIds1, sIds2) {
        var uniq = 0;
        var total = 0;
        uniqObs1 = biomTable.getSampleObs(sIds1);
        uniqObs2 = biomTable.getSampleObs(sIds2);

        for (var i = 1; i <= tree.size; i++) {
            if (tree.postorderselect(i) !== tree.root()) {
                var treeIndex = tree.postorderselect(i);
                var node = tree.name(treeIndex);

                var inObs1 = uniqObs1.includes(node);
                var inObs2 = uniqObs2.includes(node);
                if (inObs1 ^ inObs2){
                  uniq += tree.length(treeIndex);
                } else if (inObs1 || inObs2) {
                  total += tree.length(treeIndex);
                }
            }
        }
        return uniq / total;
    };

    return SummaryHelper;
});
