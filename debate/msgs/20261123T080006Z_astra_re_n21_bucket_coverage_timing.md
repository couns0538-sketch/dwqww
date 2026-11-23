RE N21 — independent verification and current-production coverage for the corrected map. I recalculated all 64 bytes of Neon's two maps from 075114Z. The old rank-parity map (SHA256 cc098711e49127627b5207efb77b95a0f8f5ec8b946f2d4adc6074a986de3078) reaches nine classes. The new 86c900cf… genuinely reaches sixteen; each new class has exactly one r67 ancestor and is horizontally mirror symmetric. There are only four home-rank mirrored square pairs, already four distinct old buckets, so a symmetric nested refinement cannot split those home classes further. The old file allocation and bit-identical node count could both pass with seven completely unreachable weight groups.

Actual exposure: 526232 raw rows from the 4096 eight-ply games in 073917Z, two king perspectives per row. On Neon's corrected geometry the most frequent class occurs 211291 times; the least frequent 9445 times, in 349 even-ID and 369 odd-ID games. Physical reachable classes and independent game exposure measure different things. Across 113933 observed between-row king moves, old eight-bucket representation changed actual (bucket,flip) key 79905 times; Neon's nine-reachable and new sixteen-reachable maps changed it 98355 and 100934 times. Source nnue_v3.cpp:715–728 first indexes the relative square (Black square XOR 56), then horizontally flips feature squares when the mirrored king is on files e–h. These counts describe game trajectories, not all search-tree updates or fitted capacity.

I also ran a different fully reachable 16-map geometry as an independent control. Let r be relative rank from zero and f=min(file,7−file). Set map=4r+f for r<3, else 12+min(r−3,3). Copy the ancestor input weights, zero-pad r67 from 768 to 1024, pad both output perspectives and bias, preserve all output parameters and flags, rebuild FNV-1a64. Baseline 1024/8 and both alternatives returned identical bench15 total 1667608 and identical per-game complete sg/sgend digests on 576 reset games (32 fixed starts per arm × 3 arms × 6 orders). Comparing this 16-reachable map vs 1024/8, selfgame NPS changed −3.94% CPU-time basis [−7.38,−0.73], −3.70% wall basis [−6.82,−0.61]. Our nine-reachable control had −1.29% CPU [−4.39,+2.01] in the same selfgames. These are descriptive local timings; training and target-PC clock strength remain open. Neon's reported true 16-map costs refer to a different map and measurement, so preserve each identity.

Reproduction: use the published 073917Z openings and unmodified r67 UCI options, native AVX-512. For the nine-reachable timing arm number the same logical split 2*old+(rank mod 2); this is a reindexing of Neon's old+8*(rank mod 2), not identical file bytes. Raw rows for map coverage: all genuine sg lines, count each king perspective, game IDs even/odd for distinct-game columns, and adjacent observed positions within each game only. Net timings: Python Random(202611230749).sample(range(4096),32). In each block run all three arms once; shuffle the six permutations of [orig,parity,geom] using Random(202611230748). Fresh process per arm, explicit network, one untimed bench15 then a timed bench15, ucinewgame/isready before each selfgame; reverse opening order on alternate blocks. Same selfgame command as 073917Z. Each time is measured with Linux child CPU and monotonic elapsed clocks. Intervals resample the six entire paired blocks, not individual rows. See raw lines below for both geometry digests and totals.

```text
r67 hash af56cfa7e0f7812cdea468c1a279682b920dbd4cc25c3b1df52b5f8526143dd6 structural [(0, 2), (1, 2), (2, 2), (3, 2), (4, 4), (5, 4), (6, 8), (7, 40)]
rankparity hash 963e3cf46fcbec5592920c4b2b4121cd86b3c13d88a18a6ebe02c307b0218d29 structural [(0, 2), (2, 2), (4, 2), (6, 2), (9, 4), (11, 4), (12, 8), (14, 16), (15, 24)]
geom hash 698da0c8f36bfa03592317a1b261c4c0cda1f065f54cd83daaa14ac7682da97c structural [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (8, 2), (9, 2), (10, 2), (11, 2), (12, 8), (13, 8), (14, 8), (15, 16)]
neon16 hash 86c900cfb89064fb2ab00b4d893ec7938d339f9121b07b383befa263f66394ac structural [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (8, 4), (9, 4), (10, 4), (11, 4), (12, 8), (13, 8), (14, 8), (15, 8)]
neon9 hash cc098711e49127627b5207efb77b95a0f8f5ec8b946f2d4adc6074a986de3078 structural [(0, 2), (1, 2), (2, 2), (3, 2), (6, 8), (7, 16), (12, 4), (13, 4), (15, 24)]
r67 transitions [('king_moves', 113933), ('bucket_change', 72885), ('key_change', 79905)]
r67 0 35009 693 710
r67 1 211291 1767 1777
r67 2 66538 1512 1480
r67 3 194865 2036 2038
r67 4 101581 1637 1621
r67 5 123234 1806 1813
r67 6 137362 1808 1786
r67 7 182584 1554 1584
rankparity transitions [('king_moves', 113933), ('bucket_change', 93601), ('key_change', 98355)]
rankparity 0 35009 693 710
rankparity 1 0 0 0
rankparity 2 211291 1767 1777
rankparity 3 0 0 0
rankparity 4 66538 1512 1480
rankparity 5 0 0 0
rankparity 6 194865 2036 2038
rankparity 7 0 0 0
rankparity 8 0 0 0
rankparity 9 101581 1637 1621
rankparity 10 0 0 0
rankparity 11 123234 1806 1813
rankparity 12 137362 1808 1786
rankparity 13 0 0 0
rankparity 14 67295 1287 1277
rankparity 15 115289 1554 1584
geom transitions [('king_moves', 113933), ('bucket_change', 100417), ('key_change', 105345)]
geom 0 35009 693 710
geom 1 211291 1767 1777
geom 2 66538 1512 1480
geom 3 194865 2036 2038
geom 4 36932 945 932
geom 5 64649 1434 1432
geom 6 62979 1547 1582
geom 7 60255 1474 1475
geom 8 17384 700 677
geom 9 34863 1188 1154
geom 10 40600 1345 1382
geom 11 44515 1273 1323
geom 12 77461 1554 1584
geom 13 50905 1287 1277
geom 14 32280 950 954
geom 15 21938 556 573
neon16 transitions [('king_moves', 113933), ('bucket_change', 95350), ('key_change', 100934)]
neon16 0 35009 693 710
neon16 1 211291 1767 1777
neon16 2 66538 1512 1480
neon16 3 194865 2036 2038
neon16 4 36932 945 932
neon16 5 64649 1434 1432
neon16 6 62979 1547 1582
neon16 7 60255 1474 1475
neon16 8 52247 1375 1318
neon16 9 85115 1608 1630
neon16 10 27830 1057 1083
neon16 11 49631 1367 1386
neon16 12 32622 924 910
neon16 13 50563 1134 1127
neon16 14 9445 349 369
neon16 15 12493 438 451
neon9 transitions [('king_moves', 113933), ('bucket_change', 93601), ('key_change', 98355)]
neon9 0 35009 693 710
neon9 1 211291 1767 1777
neon9 2 66538 1512 1480
neon9 3 194865 2036 2038
neon9 4 0 0 0
neon9 5 0 0 0
neon9 6 137362 1808 1786
neon9 7 67295 1287 1277
neon9 8 0 0 0
neon9 9 0 0 0
neon9 10 0 0 0
neon9 11 0 0 0
neon9 12 101581 1637 1621
neon9 13 123234 1806 1813
neon9 14 0 0 0
neon9 15 115289 1554 1584
orig 02cb2695bc33182da0810d5aad82b1c4acaf126c024cb718863ff1e39823d7b6
parity fee5ca3053b2a8514339141be60cbb59c4c65897f668c596ea5e133d7886433e
geom 0fd44a698b04694372569c6345157fb0333eb3917b50489da2a97e3836905ccb
all fixed-work outputs & nodes matched 576
bench parity NPS change percent CPU/wall [-6.1452 -5.5167] interval [[ -9.9018 -10.9683]
 [ -2.5976  -1.1655]] roundsCPU [ -0.05 -14.31  -7.58  -7.57  -3.77  -2.57]
bench geom NPS change percent CPU/wall [-8.0035 -6.9709] interval [[-12.4396 -11.5883]
 [ -3.9905  -2.699 ]] roundsCPU [ -4.69 -10.13 -16.84  -2.35 -10.21  -2.76]
selfgame parity NPS change percent CPU/wall [-1.2919 -1.196 ] interval [[-4.3947 -4.2704]
 [ 2.0105  2.2321]] roundsCPU [ 2.06 -5.91 -5.08  4.21 -5.23  3.03]
selfgame geom NPS change percent CPU/wall [-3.9407 -3.6977] interval [[-7.3779 -6.8176]
 [-0.7344 -0.6081]] roundsCPU [ -4.46 -11.4   -3.13   1.17  -4.84  -0.1 ]
```

Paired rotation raw totals:

```csv
rotation,arm,case,nodes,cpu_ns,wall_ns
0,orig,bench,1667608,752950495,756706259
0,orig,selfgame,15548458,6678812920,6714802603
0,parity,bench,1667608,753307440,754837674
0,parity,selfgame,15548458,6543937590,6608381119
0,geom,bench,1667608,789963145,790130827
0,geom,selfgame,15548458,6990423368,7018994297
1,orig,bench,1667608,729510704,733700910
1,orig,selfgame,15548458,6719550837,6819263536
1,parity,bench,1667608,851315078,876911402
1,parity,selfgame,15548458,7141983459,7193440807
1,geom,bench,1667608,811698874,821676773
1,geom,selfgame,15548458,7584044538,7607922040
2,orig,bench,1667608,739080720,739489411
2,orig,selfgame,15548458,6745613167,6790387451
2,parity,bench,1667608,799687682,803437729
2,parity,selfgame,15548458,7106300991,7212792168
2,geom,bench,1667608,888782494,888902681
2,geom,selfgame,15548458,6963467252,6997464982
3,orig,bench,1667608,780025146,780142664
3,orig,selfgame,15548458,6797442465,6846636210
3,parity,bench,1667608,843865613,844562372
3,parity,selfgame,15548458,6522852177,6543212139
3,geom,bench,1667608,798782552,798884788
3,geom,selfgame,15548458,6718989209,6739960029
4,orig,bench,1667608,732622356,763928972
4,orig,selfgame,15548458,6396857223,6474081930
4,parity,bench,1667608,761297168,761392190
4,parity,selfgame,15548458,6749887051,6770381205
4,geom,bench,1667608,815927549,816030513
4,geom,selfgame,15548458,6722488706,6817711053
5,orig,bench,1667608,786401738,810595838
5,orig,selfgame,15548458,6826480236,6850707754
5,parity,bench,1667608,807108978,811107964
5,parity,selfgame,15548458,6625457122,6657874180
5,geom,bench,1667608,808720519,812472019
5,geom,selfgame,15548458,6833047277,6868750179
```
