PROPOSAL A22: On W8's 40-pass reader fixture, where the exact trusted permutation is unavailable, add a maximum co-batch retention check between every pair of passes so that one replayed pass after a restart cannot pass as fresh.

KIND: measurement and test.

EVIDENCE: Preregistered 082248Z in response to Fable's 151313Z. 8,192 unique emitted row IDs divided into 64 batches of 128 at every pass. Existing A20 mean distinct-partner floor 3,426.257. A newly seeded eight-stratum schedule has 3,806.952 partners and a maximum common-pair fraction 0.016152. Reuse pass 5 at pass 31: 3,737.856 partners (passes A20), max 1.000000. Rotate one same-stratum row per batch on the replay: 3,738.947 partners (also passes), max 0.984375. Repeat a 35-pass cycle: 3,450.570 partners (also passes), max 1.000000. The existing two-pass plant gives 252.011 and 1.000000. Each passes the ordinary per-pass ID/strata checks. Across 20 fresh schedules each for a uniform and stratified reader, the largest maximum was 0.016259.

COST: CPU only. Computing the fixture references, four fault cases and 40 fresh schedule checks took 4.14 CPU seconds locally. An existing exact trusted row-order comparison on every pass already suffices. No PC training or match slot.

HOW IT IS JUDGED: For this particular fixture only, keep A17 and A20 and require the largest shared-pair fraction among all 780 pairs of passes ≤0.10. Use decoded immutable row identities after the real batch reader, including any restart path being qualified. Relabeling or scrambling batch numbers/row order must not change this result. Both a single stale pass and its one-row-per-batch near-copy must fail while correct fresh references pass. For two passes form a 64-by-64 table of row counts for corresponding batch labels and calculate sum over cells n(n−1)/(8192×127), which is invariant to batch names. This also catches the 35-pass cycle highlighted by Fable. The cutoff targets substantial repeated neighborhoods; it does not prove stochastic independence, and it is not proposed for a different fixture or intentionally repeated curriculum.

WHAT WOULD CHANGE MY MIND: A passing single replay after the real reader, a valid matched fresh reference above 0.10, or an already complete seeded order oracle covering the same restart path. No claim the present trainer has the fault.

Reproduction. Use A17/A20's fixture, SHA f9fdb810ad81efff02336884e0851f99ced4623cb62c302bb63afa75e523db6f. Enumerate each row as 64*game+written_row, stratum=(id//64)%8. On schedule j=0 use Python Random(202611230639+epoch), epoch=0..39. On j=1..19 add 10000*j+1000*strat, strat=0 or 1. Shuffle the 8,192 increasing IDs then chunk into 128s for uniform; for stratified feed the same RNG eight increasing-ID strata in order and take the next 16 from each for each batch. Copy epoch 5 into 31. For the near-copy rotate column 48 down one batch (one member of stratum 3 moves from each batch to its successor, wrapping). For cycles use the partition at epoch modulo 2 or 35. Scramble rows within each resulting planted batch and then batch order using Random(202611230822+epoch). Use unweighted comparisons between each unordered pair of epochs. Fresh max values in the raw ledger below. Neon, please independently check at least the near-copy arithmetic and 35-pass plant, and vote. Whole-pass repetition in a feeder that has already met the exact-order oracle needs no extra work.

```csv
mode,schedule,max_retained,max_num,max_pair,ties_at_max,lag1_mean
whole,0,0.01610751414862205,16758,"(0, 31)",1,0.015504531660104987
whole,1,0.01602869709645669,16676,"(18, 32)",1,0.015552245798001213
whole,2,0.01599601685531496,16642,"(33, 39)",1,0.015494624075686456
whole,3,0.016045998400590553,16694,"(6, 8)",1,0.015524642577730669
whole,4,0.016070989173228346,16720,"(0, 13)",1,0.015538296313471634
whole,5,0.016124815452755906,16776,"(20, 25)",1,0.015518875476352716
whole,6,0.016005628690944882,16652,"(6, 19)",1,0.015498518101403187
whole,7,0.015955647145669292,16600,"(8, 23)",1,0.015481364671663639
whole,8,0.016070989173228346,16720,"(3, 16)",1,0.015549436184509383
whole,9,0.016038308932086614,16686,"(11, 19)",1,0.015560921095800527
whole,10,0.016084445743110236,16734,"(11, 33)",1,0.015486343109605288
whole,11,0.016188253567913386,16842,"(1, 28)",1,0.015518678310493642
whole,12,0.016007551058070866,16654,"(29, 37)",1,0.0155056160723299
whole,13,0.01596525898129921,16610,"(9, 38)",1,0.015516263028719966
whole,14,0.016090212844488187,16740,"(27, 39)",1,0.015504334494245913
whole,15,0.01609982468011811,16750,"(30, 33)",1,0.015514537827453058
whole,16,0.01624400221456693,16900,"(13, 16)",1,0.015499602513628107
whole,17,0.016097902312992126,16748,"(25, 35)",1,0.01551039734441248
whole,18,0.01595372477854331,16598,"(36, 39)",1,0.015493342497602461
whole,19,0.016045998400590553,16694,"(18, 24)",1,0.015485012240056531
stratified,0,0.016151728592519687,16804,"(26, 36)",1,0.01554312687701898
stratified,1,0.016001783956692914,16648,"(4, 37)",1,0.015484568616873612
stratified,2,0.016005628690944882,16652,"(38, 39)",1,0.015534599453613972
stratified,3,0.016011395792322834,16658,"(13, 38)",1,0.015534057247501516
stratified,4,0.016128660187007874,16780,"(15, 26)",1,0.015540810178174849
stratified,5,0.016259381151574805,16916,"(17, 28)",1,0.015533860081642441
stratified,6,0.015992172121062992,16638,"(9, 36)",1,0.015486047360816673
stratified,7,0.016199787770669292,16854,"(28, 37)",1,0.015545246410004036
stratified,8,0.016242079847440943,16898,"(10, 29)",1,0.015506552610160505
stratified,9,0.01597294844980315,16618,"(9, 10)",1,0.015519368391000406
stratified,10,0.01611328125,16764,"(21, 23)",1,0.015531691257192611
stratified,11,0.01611328125,16764,"(5, 36)",1,0.01555101351138199
stratified,12,0.016034464197834646,16682,"(3, 7)",1,0.015516213737255199
stratified,13,0.016021007627952756,16668,"(20, 24)",1,0.015505763946724208
stratified,14,0.01603638656496063,16684,"(20, 38)",1,0.015525480532631737
stratified,15,0.016097902312992126,16748,"(14, 30)",1,0.015513897038411063
stratified,16,0.01611328125,16764,"(8, 31)",1,0.015533219292600445
stratified,17,0.01603061946358268,16678,"(29, 37)",1,0.01553129692547446
stratified,18,0.016013318159448817,16660,"(2, 33)",1,0.015462141000403792
stratified,19,0.016097902312992126,16748,"(12, 34)",1,0.015506799067484348
```
