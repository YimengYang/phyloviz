require(['jquery', 'ByteArray', 'BPTree','Empress','BiomTable'], function($, ByteArray, BPTree, Empress, BiomTable) {
    $(document).ready(function() {
        // Setup test variables
        // Note: This is ran for each test() so tests can modify bpArray without
        // effecting other test
        module('Unifrac' , {
            setup: function() {
                this.bpArray = new Uint8Array([1, 1, 1, 0, 1, 0, 1, 1 ,0, 0, 0,
                        1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]);
                this.bpObj = new BPTree(this.bpArray);

                this.names = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21"];
                this.obs = {"1": ["2","4"],"2":["4","6","7"],"3":["11","14","6"]};
                this.samp = {
                  "1": {"cat1": 0},
                  "2": {"cat2": 0},
                  "3": {"cat3": 0}
                };
                this.biomTable = new BiomTable(this.obs, this.samp);
                this.empress = new Empress(this.bpObj, null, this.biomTable, null, null);

                // rank caches
                this.r0 = ByteArray.sumVal(this.bpArray, Uint32Array, 0);
                this.r1 = ByteArray.sumVal(this.bpArray, Uint32Array, 1);

                // select caches
                this.s0 = ByteArray.seqUniqueIndx(this.r0, Uint32Array);
                this.s1 = ByteArray.seqUniqueIndx(this.r1, Uint32Array);
            },

            teardown: function() {
                this.bpArray = null;
            }
        });

        // tests unifrac
        test('Test unifrac', function() {
            var sIds1 = ["1", "3"]
            var sIds2 = ["1", "2"]
            equal(this.empress.unifrac(sIds1, sIds2));
        });


    });
});
