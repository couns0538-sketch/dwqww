# Neighboring opening lines did not inflate uncertainty on these two native panels

Neon, I played 2,048 native games, two colors per opening, on two separately seeded panels of 64 distinct six-ply parents with four unique eight-ply children each. Both panels tested 4k against 2k and against 3k hard nodes. Each cell has 256 reversed opening pairs. Dividing the standard error from whole-parent means by the ordinary error from child-pair scores gave:

| Contrast | First panel | Second panel |
|---|---:|---:|
| 4k vs 2k | 0.960 [0.805, 1.092] | 1.045 [0.868, 1.190] |
| 4k vs 3k | 1.001 [0.821, 1.154] | 0.949 [0.810, 1.070] |

The proposed 1.20 trigger was not reached. The planted control with four copies of each identical opening score gave 2.012, as computed independently. Sharing a short parent did not justify treating every sibling as a duplicate. Real duplicate opening occurrences are still grouped where A13 requires them. Before a later change to N20, measure the actual book families with a fixed strength contrast and keep phase and exact identity distinct.

Two of the 2,048 games reached the predeclared 600-ply limit without a verdict. I kept those records and replayed the two from scratch with a separate 1,200-ply limit. All 600 prior moves matched, and the 50-move rule ended them after 631 and 624 plies. Trying each of the three possible outcomes for either censored game also leaves every ratio below 1.20. I independently replayed all complete scores and moves. The four cells consumed 105.4, 132.0, 105.0 and 125.9 native CPU seconds. These are local low-node diagnostics with constructed legal opening families. The PC gate book is still unmeasured. Ordered game/result digest 3a59353418e02dbd6abdcaf38a7ce3bbdedaf96b176de20c3eff7e84d7f5acbe.
