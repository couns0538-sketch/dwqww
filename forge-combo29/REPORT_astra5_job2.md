# astra5 job 2 — double extensions and fail-high blending

## Step 0 — all five PCA checks passed

The Job 1 PCA executable reproduced the no-setoption bench 11, bench 13 and perft 5 totals of 312,866, 862,329 and 4,865,609. With PC20 it reproduced bench 11 and bench 13 at 278,024 and 587,276. Each command ran in a fresh process. PCA SHA-256 was `49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a`. [Raw inputs and outputs](astra5/job2/step0)

<details><summary>Raw engine output</summary>

```text
pca-no-setoption-bench-11.txt
readyok
info string bench depth 11 nodes 312866 time 287 nps 1090125

pca-no-setoption-bench-13.txt
readyok
info string bench depth 13 nodes 862329 time 662 nps 1302611

pca-no-setoption-go-perft-5.txt
readyok
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609

pca-PC20-bench-11.txt
readyok
info string bench depth 11 nodes 278024 time 229 nps 1214078

pca-PC20-bench-13.txt
readyok
info string bench depth 13 nodes 587276 time 426 nps 1378582
```

</details>

## Step 1 — two PCAD options

In PCA `src/search.cpp:2230`, the non-PV double-extension test used a margin of 24 and permitted up to six inherited double extensions before the current move. In PCAD `src/search.cpp:2233` reads `DoubleExtMargin` and `src/search.cpp:2234` reads `DoubleExtLimit`. Defaults are at lines 127 and 128. The comparison uses `<=`, so -1 disables every two-ply extension. All source edits were made in isolated build trees. The repository deliverable is the unified diff.

```text
option name DoubleExtMargin type spin default 24 min 0 max 400
option name DoubleExtLimit type spin default 6 min -1 max 64
```

<details><summary>Literal diff -ruN output</summary>

```diff
diff -ruN pca/include/forge/search.hpp options/include/forge/search.hpp
--- pca/include/forge/search.hpp	2026-11-18 12:11:13.000000000 +0000
+++ options/include/forge/search.hpp	2026-11-18 12:11:13.000000000 +0000
@@ -272,6 +272,8 @@
 extern int SeeNoisyMultiplier;
 extern int SingularDepth;
 extern int SingularMargin;
+extern int DoubleExtMargin;
+extern int DoubleExtLimit;
 extern int IirDepth;
 extern int ProbcutDepth;
 extern int ProbcutMargin;
diff -ruN pca/src/search.cpp options/src/search.cpp
--- pca/src/search.cpp	2026-11-18 12:11:13.000000000 +0000
+++ options/src/search.cpp	2026-11-18 12:11:13.000000000 +0000
@@ -124,6 +124,8 @@
 int SeeNoisyMultiplier = 150;
 int SingularDepth = 7;
 int SingularMargin = 2;
+int DoubleExtMargin = 24;
+int DoubleExtLimit = 6;
 int IirDepth = 4;
 int ProbcutDepth = 5;
 int ProbcutMargin = 180;
@@ -207,6 +209,7 @@
         {"SeeQuietMultiplier", &SeeQuietMultiplier, 0, 200},
         {"SeeNoisyMultiplier", &SeeNoisyMultiplier, 0, 1000},
         {"SingularDepth", &SingularDepth, 2, 20},        {"SingularMargin", &SingularMargin, 0, 10},
+        {"DoubleExtMargin", &DoubleExtMargin, 0, 400},    {"DoubleExtLimit", &DoubleExtLimit, -1, 64},
         {"IirDepth", &IirDepth, 1, 20},                  {"ProbcutDepth", &ProbcutDepth, 1, 20},
         {"ProbcutMargin", &ProbcutMargin, 0, 1000},      {"QsFutilityMargin", &QsFutilityMargin, 0, 1000},
         {"QsSeeMargin", &QsSeeMargin, 0, 500},           {"AspirationDelta", &AspirationDelta, 4, 200},
@@ -2227,7 +2230,8 @@
             if (aborted_) return 0;
             if (singular_score < singular_beta) {
                 extension = 1;
-                if (!pv_node && singular_score < singular_beta - 24 && inherited_double_extensions <= 6) {
+                if (!pv_node && singular_score < singular_beta - tune::DoubleExtMargin &&
+                    inherited_double_extensions <= tune::DoubleExtLimit) {
                     extension = 2;
                 }
             } else if (singular_beta >= beta) {
```

</details>

Applying it to a fresh PCA tree with `patch -p1 -F0` produced the following output. [Build and compiler](astra5/job2/step1/pcad-build.txt)

```text
patching file include/forge/search.hpp
patching file src/search.cpp
```

## Step 2 — PCAD, PC20, depth 12

Every run used the Job 1 UCI search protocol, Threads 1 and Hash 16. The four default-option runs match the Job 1 node and move rows position by position. The ten changed-option runs match their specified row count, sum, three leading node counts and both row hashes. The separate SingularDepth 20 checks used only the first 20 positions for the Step 3 comparisons. [Rows, metadata and first-three counts](astra5/job2/step2)

| Suite | Setting | Rows | Node sum | Node hash | Move hash | Result |
|---|---|---:|---:|---|---|---|
| O | base | 200 | 8,315,168 | `fd609b7b1a8dd179` | `14583c86b5f56cb6` | Equal |
| O | fhb7 | 200 | 7,913,480 | `75509856e2b96287` | `1ec0bb858b7ca372` | Equal |
| O | del | 200 | 8,034,043 | `dce216236443837d` | `3b5fb2c3c8a5211a` | Equal |
| O | del_fhb7 | 200 | 8,148,181 | `2cd1ab85c28b42e1` | `3bcd4da745552b26` | Equal |
| O | sd20_base | 20 | 756,463 | `aea7e4a92ecaee79` | `d46f332b37ea9800` | Equal |
| O | sd20_fhb7 | 20 | 903,722 | `08c59b2f3c52ccf5` | `a064ad4540f618b9` | Equal |
| O | dm12 | 200 | 7,841,038 | `3036c9511ea4c4d0` | `b777ea49029deda4` | Equal |
| O | dm0 | 200 | 8,665,792 | `724960318794e924` | `7622b6327b46588f` | Equal |
| O | sm1 | 200 | 10,300,501 | `4fadaf54dfe33ce1` | `d72afa986b8d3117` | Equal |
| G | base | 353 | 17,611,204 | `60b6916f01395e99` | `0846f027e7e9b77e` | Equal |
| G | fhb7 | 353 | 15,879,039 | `48255179b3c50754` | `6c7dc5dc109bdd8b` | Equal |
| G | del | 353 | 15,429,690 | `dc1e72558bf88b8e` | `5bb03c0424a9d6bf` | Equal |
| G | del_fhb7 | 353 | 14,751,618 | `9181bbd3591c4173` | `e95cdf298e359440` | Equal |
| G | sd20_base | 20 | 519,509 | `a67edab7fedd3748` | `92c54d2300fb77e8` | Equal |
| G | sd20_fhb7 | 20 | 697,158 | `85d5ff8a5701dc84` | `bc21033f40a47a39` | Equal |
| G | dm12 | 353 | 16,925,891 | `a5bcaf0038eced2b` | `d3c14b3f726a0dec` | Equal |
| G | dm0 | 353 | 18,032,844 | `62c4476a64d7e2d9` | `a7ca690c32054c5a` | Equal |
| G | sm1 | 353 | 18,496,605 | `503d49e1299cc10c` | `65045972b4698804` | Equal |

## Step 3 — observe-only counter build and checks

PCADC adds kimi5’s pinned A25C counters. The original patch matched SHA-256 `7a6f6c322fc46fb8dc5f07efbb4e1acebb3c8b02f650af434aaa47d441fd3336`. Hunk 6 still referenced the two literals replaced in Step 1. I retained the tunable condition and ported the counter updates at the same outcome branches. The resulting diff applied to a fresh PCAD copy with zero fuzz. Applying the original counter patch to PCA first and then introducing the options gave byte-identical `src/search.cpp`. [Ported patch](astra5/job2/count_on_pcad.patch.txt) · [Cross-check](astra5/job2/step3/crosscheck.txt)

PCADC reproduced the first 20 position/node/move rows from PCAD for all nine settings on both suites, 360 comparisons. For base and fhb7 under ordinary PC20, every row matched across both complete suites. The full-suite reference counter totals below matched. The other first-20 probes discarded their counter values before prediction. [All PCADC checks](astra5/job2/step3/checks.txt)

| Suite | Blend | A25C lines | Tests [0] | Double extensions [2] | Multi-cut [3] | TT lower [7] | RFP [10] |
|---|---|---:|---:|---:|---:|---:|---:|
| G | base | 353 | 176,423 | 67,359 | 31,604 | 1,202,904 | 4,748,667 |
| G | fhb7 | 353 | 164,148 | 39,128 | 29,016 | 1,041,548 | 4,134,563 |
| O | base | 200 | 48,220 | 5,794 | 11,268 | 342,931 | 2,212,993 |
| O | fhb7 | 200 | 47,952 | 2,124 | 9,361 | 313,345 | 2,080,561 |

The assignment supplied reference values for all five displayed G slots and the first two O slots. The three remaining O columns are recounts from the complete Step 3 runs.

## Prediction grades

The prediction was committed and pushed as `b0f44724c4c0288f320e427f74b3d567ce04306c` after Step 3 and before any full Step 4 run. The interval applies to the predicted class even if a different class won. Four of eight forecasts got both the winner and its interval right. [Frozen prediction](https://github.com/couns0538-sketch/dwqww/blob/b0f44724c4c0288f320e427f74b3d567ce04306c/forge-combo29/astra5/job2/prediction.txt)

| Forecast | Predicted class | Point | Inclusive bounds | Actual winner | Predicted class rate ratio | Winner rate ratio | Class | Interval for predicted class | Joint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q1 G proportional | 5 | 1.55 | 1.20 to 1.90 | 5 | 1.770096 | 1.770096 | yes | yes | pass |
| Q1 G absolute | 10 | 0.96 | 0.91 to 0.995 | 10 | 0.980961 | 0.980961 | yes | yes | pass |
| Q2 G proportional | 8 | 1.16 | 1.02 to 1.34 | 8 | 1.215893 | 1.215893 | yes | yes | pass |
| Q2 O proportional | 8 | 1.13 | 1.01 to 1.31 | 7 | 1.028195 | 0.968081 | no | yes | miss |
| Q2 G absolute | 10 | 0.95 | 0.89 to 0.99 | 7 | 0.997832 | 0.962616 | no | no | miss |
| Q2 O absolute | 10 | 0.96 | 0.90 to 0.995 | 10 | 0.993361 | 0.993361 | yes | yes | pass |
| Q3 G nearest | sm1 | 1.00 | 0.83 to 1.17 | dm0 | 0.681683 | 1.137104 | no | no | miss |
| Q3 O nearest | dm0 | 1.00 | 0.80 to 1.20 | dm12 | 1.755457 | 0.668420 | no | no | miss |

Class 4/8, interval for predicted class 5/8, joint 4/8.

## Step 4 — event rates at depth 12

PCADC used PC20 first, Threads 1 and Hash 16. Runs completed on G before O. All 4,977 searches reproduced both nodes and best move for their FEN. Every search printed exactly one A25C line with 16 counters, and both counter partitions closed per search. DoubleExtLimit -1 produced zero two-ply extensions in each applicable search. SingularDepth 20 produced zero singular tests in each applicable search. The rates divide a suite’s total events by its total nodes and multiply by 1,000.

`base` and `fhb7` use ordinary PC20. `del` uses DoubleExtLimit -1 and `sd20` uses SingularDepth 20. In those pairs the `fhb7` arm adds FailHighBlend 7 after the named control. `dm12`, `dm0` and `sm1` all use FailHighBlend 7 followed by DoubleExtMargin 12, DoubleExtMargin 0 or SingularMargin 1, respectively. TT lower, upper and exact count main-search cutoffs by stored bound. RFP counts taken reverse-futility returns. Undefined rate ratios correspond to controls with zero events in both arms.

| Suite | Setting | A25C lines | Nodes | tests | ext+1 | ext+2 | multicut | ext-2 | ext-1 | none | TT lower | TT upper | TT exact | RFP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G | base | 353 | 17611204 | 10.017657 | 2.490574 | 3.824781 | 1.794539 | 0.581846 | 0.864166 | 0.461752 | 68.303337 | 7.177647 | 1.779890 | 269.638975 |
| G | fhb7 | 353 | 15879039 | 10.337401 | 3.060702 | 2.464129 | 1.827315 | 0.867748 | 1.513253 | 0.604256 | 65.592634 | 8.107481 | 1.898163 | 260.378666 |
| G | del | 353 | 15429690 | 8.952999 | 5.804783 | 0.000000 | 1.527510 | 0.450301 | 0.641166 | 0.529239 | 67.382754 | 5.979900 | 2.043009 | 262.198268 |
| G | del_fhb7 | 353 | 14751618 | 9.306166 | 5.107033 | 0.000000 | 1.728624 | 0.685687 | 1.134926 | 0.649895 | 64.124220 | 7.296962 | 2.030218 | 257.206226 |
| G | sd20_base | 353 | 9785780 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 62.298151 | 5.471511 | 1.895812 | 266.640779 |
| G | sd20_fhb7 | 353 | 10512013 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 59.969199 | 6.652770 | 1.776349 | 266.062647 |
| G | dm12 | 353 | 16925891 | 10.683219 | 2.403478 | 3.293948 | 1.902588 | 0.907190 | 1.597966 | 0.578049 | 65.194618 | 8.629797 | 1.833877 | 266.431410 |
| G | dm0 | 353 | 18032844 | 10.359542 | 1.041156 | 4.349175 | 1.928370 | 0.923149 | 1.587270 | 0.530421 | 63.200902 | 8.553393 | 1.677606 | 266.689104 |
| G | sm1 | 353 | 18496605 | 10.280697 | 3.276331 | 2.607289 | 2.007882 | 0.542478 | 1.428370 | 0.418347 | 66.287570 | 8.039800 | 1.862991 | 263.765377 |
| O | base | 200 | 8315168 | 5.799041 | 1.631476 | 0.696799 | 1.355114 | 0.839189 | 0.602513 | 0.673949 | 41.241620 | 3.700106 | 1.945120 | 266.139301 |
| O | fhb7 | 200 | 7913480 | 6.059534 | 1.575034 | 0.268403 | 1.182918 | 1.164090 | 1.096231 | 0.772858 | 39.596360 | 4.302911 | 1.932020 | 262.913535 |
| O | del | 200 | 8034043 | 5.879605 | 2.377010 | 0.000000 | 1.362328 | 0.820259 | 0.612145 | 0.707863 | 42.063753 | 3.637397 | 1.954682 | 264.925269 |
| O | del_fhb7 | 200 | 8148181 | 5.922794 | 1.807765 | 0.000000 | 1.126141 | 1.127491 | 1.084782 | 0.776615 | 39.056202 | 4.180442 | 1.944483 | 261.830831 |
| O | sd20_base | 200 | 7872425 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 36.508446 | 3.125847 | 1.389280 | 293.840970 |
| O | sd20_fhb7 | 200 | 8464273 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 35.343142 | 3.213980 | 1.351799 | 291.890160 |
| O | dm12 | 200 | 7841038 | 6.008006 | 1.351989 | 0.465755 | 1.170253 | 1.165662 | 1.078939 | 0.775408 | 39.282937 | 4.208371 | 1.946681 | 262.576332 |
| O | dm0 | 200 | 8665792 | 5.716269 | 0.461585 | 1.223200 | 1.134807 | 1.139653 | 1.074224 | 0.682800 | 37.384234 | 4.168459 | 1.722058 | 263.143057 |
| O | sm1 | 200 | 10300501 | 5.777195 | 2.003883 | 0.295423 | 1.430998 | 0.583952 | 0.929761 | 0.533178 | 39.476041 | 3.795641 | 1.769817 | 260.962743 |

### Ratios of matched event rates

| Suite | Treatment/base | Node ratio | tests | ext+1 | ext+2 | multicut | ext-2 | ext-1 | none | TT lower | TT upper | TT exact | RFP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G | fhb7/base | 0.901644 | 1.031918 | 1.228914 | 0.644254 | 1.018264 | 1.491371 | 1.751114 | 1.308617 | 0.960314 | 1.129546 | 1.066450 | 0.965657 |
| G | del_fhb7/del | 0.956054 | 1.039447 | 0.879797 | undefined (0/0) | 1.131662 | 1.522733 | 1.770096 | 1.227979 | 0.951641 | 1.220248 | 0.993739 | 0.980961 |
| G | sd20_fhb7/sd20_base | 1.074213 | undefined (0/0) | undefined (0/0) | undefined (0/0) | undefined (0/0) | undefined (0/0) | undefined (0/0) | undefined (0/0) | 0.962616 | 1.215893 | 0.936986 | 0.997832 |
| O | fhb7/base | 0.951692 | 1.044920 | 0.965404 | 0.385194 | 0.872929 | 1.387160 | 1.819430 | 1.146761 | 0.960107 | 1.162916 | 0.993265 | 0.987879 |
| O | del_fhb7/del | 1.014207 | 1.007346 | 0.760521 | undefined (0/0) | 0.826630 | 1.374554 | 1.772099 | 1.097127 | 0.928500 | 1.149295 | 0.994782 | 0.988320 |
| O | sd20_fhb7/sd20_base | 1.075180 | undefined (0/0) | undefined (0/0) | undefined (0/0) | undefined (0/0) | undefined (0/0) | undefined (0/0) | undefined (0/0) | 0.968081 | 1.028195 | 0.973022 | 0.993361 |

From `forge-combo29/astra5/job2`, `python3 counters.py table step4` regenerates the rates, matched ratios and summed values of all 16 slots. It prints the A25C line count for every file and checks both closure identities and both disabled-event controls per search. `python3 counters.py grade step4 prediction.txt` regenerates the grades. [Raw rows](astra5/job2/step4) · [All 16 slot totals and rate tables](astra5/job2/step4-tables.md)

## Answers to Q1–Q3

**Q1. G with DoubleExtLimit -1.** Minus-one extensions [5] rose from 0.641166 to 1.134926 per 1,000 nodes, a factor of 1.770096 and the largest proportional shift. The node ratio was 0.956054. Reverse-futility returns [10] had the largest absolute change, falling from 262.198268 to 257.206226 per 1,000. In PCADC `src/search.cpp:2262–2279` the positive-extension, multi-cut and minus-two branches all precede the cut-node minus-one outcome. Line 2286 consumes the resulting extension in child depth. Lines 1988–1995 count taken reverse-futility returns before the bit-1 score blend. This identifies the two moving events. Their downstream subtree costs are unmeasured.

**Q2. SingularDepth 20.** On G, upper-bound TT cutoffs [8] had the largest proportional change, rising from 5.471511 to 6.652770 per 1,000 (1.215893×). Lower-bound TT cutoffs [7] had the largest absolute change, falling from 62.298151 to 59.969199 (−2.328952 per 1,000). On O, lower-bound cutoffs [7] moved most proportionally, from 36.508446 to 35.343142 (0.968081×). RFP returns [10] moved most absolutely, from 293.840970 to 291.890160 (−1.950810 per 1,000). The G and O tree ratios were 1.074213 and 1.075180. In PCADC `src/search.cpp:1876–1889` the TT guard requires a valid bound that cuts at the current search window. Lines 1988–1995 implement the RFP gate and return. Blending changes scores returned or stored at lines 1701–1702, 1772–1773, 1993–1995 and 2433–2439. Reduced lower-cutoff density is consistent with expanding a larger tree. The counts alone cannot assign those extra nodes to a particular failed cutoff.

**Q3. Restoring the ordinary PC20 double-extension rate.** On G, dm0 was closest, with a gap of 0.524394 events per 1,000 from base. Dm12 was almost tied, at 0.530833. The dm0 node total was 18,032,844 against 17,611,204 (1.023942×). On O, dm12 was closest, with a gap of 0.231044 per 1,000 and 7,841,038 versus 8,315,168 nodes (0.942980×). The forecast missed both winners. In PCADC `src/search.cpp:2262–2268`, lowering DoubleExtMargin directly relaxes the inner non-PV condition. Changing SingularMargin affects the upstream threshold at line 2250 and the excluded-move search window at line 2257. Restoring the rate of one event does not restore the rest of the tree.

| Suite | Fhb7 setting | Base ext+2/1k | Setting ext+2/1k | Abs distance/1k | Ext+2 rate ratio | Tree nodes/base | Closest |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G | dm12 | 3.824781 | 3.293948 | 0.530833 | 0.861212 | 0.961087 |  |
| G | dm0 | 3.824781 | 4.349175 | 0.524394 | 1.137104 | 1.023942 | yes |
| G | sm1 | 3.824781 | 2.607289 | 1.217492 | 0.681683 | 1.050275 |  |
| O | dm12 | 0.696799 | 0.465755 | 0.231044 | 0.668420 | 0.942980 | yes |
| O | dm0 | 0.696799 | 1.223200 | 0.526401 | 1.755457 | 1.042167 |  |
| O | sm1 | 0.696799 | 0.295423 | 0.401376 | 0.423971 | 1.238760 |  |

## Step 5 — nodes spent in outermost singular verifications

The 17th slot counts worker nodes spent in the reduced search that excludes the transposition-table move. PCADC plus the new slot snapshots `local_nodes_` around `search_child` at `src/search.cpp:2256–2265`. An outermost-call flag charges nested verification visits once. The counter includes quiescence nodes reached inside verification. The ordinary search of the chosen move occurs afterward. On 160 separate first-20 checks and all 2,212 full rows, the new build matched PCADC in node count, move and all 16 original slots. [Patch](astra5/job2/step5/slot16.patch.txt) · [Full recount](astra5/job2/step5/rows/full-summary.txt)

| Suite | Setting | Rows | Search nodes | Outermost verification nodes | Verification nodes / 1,000 |
|---|---|---:|---:|---:|---:|
| G | base | 353 | 17,611,204 | 2,001,882 | 113.670934 |
| G | fhb7 | 353 | 15,879,039 | 1,874,826 | 118.069236 |
| G | del | 353 | 15,429,690 | 1,504,615 | 97.514273 |
| G | del_fhb7 | 353 | 14,751,618 | 1,561,510 | 105.853473 |
| O | base | 200 | 8,315,168 | 707,463 | 85.081023 |
| O | fhb7 | 200 | 7,913,480 | 717,561 | 90.675784 |
| O | del | 200 | 8,034,043 | 694,442 | 86.437426 |
| O | del_fhb7 | 200 | 8,148,181 | 720,563 | 88.432375 |

On G with double extensions disabled, verification nodes rose by 56,895 and nodes outside verification fell by 734,967. Their sum is the observed overall reduction of 678,072 nodes. The remaining shrink occurred outside the excluded-move search. The slot’s share of all nodes rose in every pair. The normalized fhb7/base ratios were 1.038693 (G) and 1.065758 (O) under ordinary PC20, and 1.085518 (G) and 1.023080 (O) with DoubleExtLimit -1.

## Facts

Disabling two-ply extensions separates the suites. With blending, the G depth-12 node ratio rises from 0.901644 to 0.956054 and the O ratio from 0.951692 to 1.014207. Disabling all singular tests puts both ratios above 1. The matched bases, node sums and event densities are in the Step 4 table. Every result uses the built-in evaluation, Threads 1 and Hash 16.

## Suspicions

The extra minus-one outcomes on G can shorten later child searches and may help explain the reduction outside verification. Counting visits in the downstream children chosen after each outcome would test that explanation. Under SingularDepth 20, fewer taken lower-bound cutoffs per 1,000 nodes on both suites may contribute to growth, but positions reached, stored bounds and search windows change together.

## What I did not do

I ran no playing-strength matches or equal-time tests. I did not measure the subtrees of children after an extension decision or estimate the counterfactual cost of missed cutoffs.

## What I am not sure about

An event’s change per 1,000 nodes gives its frequency conditional on the resulting tree. It does not establish how many nodes that event caused or saved. Q3 ranks are suite-specific. The G margin-0 and margin-12 distances differ by about 0.00644 double extensions per 1,000 nodes.

## Recounting the evidence

From `forge-combo29/astra5/job2`, these commands read the committed results and report the row counts.

```sh
python3 counters.py table step4
python3 counters.py grade step4 prediction.txt
python3 step5/check_slot.py step4 step5/rows/first20 --first20
python3 step5/check_slot.py step4 step5/rows/full
```

## Pre-commit working tree and evidence files

```text
$ git status --short && ls -R forge-combo29/astra5
 A forge-combo29/REPORT_astra5_job2.md
M  forge-combo29/astra5/job2/stamps.txt
forge-combo29/astra5:
job1
job2

forge-combo29/astra5/job1:
analyze.py
audit_step1.py
grade.sh
grades.txt
harness-selfcheck.txt
harness.py
job2-polls.txt
prediction.txt
rows
run_step.py
stamps.txt
step0
step1-reference.txt
step1.txt
step2.txt
step3.txt

forge-combo29/astra5/job1/rows:
G_base_d12.tsv
G_base_d12.tsv.meta
G_base_d14.tsv
G_base_d14.tsv.meta
G_fhb7_d12.tsv
G_fhb7_d12.tsv.meta
G_fhb7_d14.tsv
G_fhb7_d14.tsv.meta
G_sd20_base_d12.tsv
G_sd20_base_d12.tsv.meta
G_sd20_base_d14.tsv
G_sd20_base_d14.tsv.meta
G_sd20_fhb7_d12.tsv
G_sd20_fhb7_d12.tsv.meta
G_sd20_fhb7_d14.tsv
G_sd20_fhb7_d14.tsv.meta
O_base_d12.tsv
O_base_d12.tsv.meta
O_base_d14.tsv
O_base_d14.tsv.meta
O_fhb7_d12.tsv
O_fhb7_d12.tsv.meta
O_fhb7_d14.tsv
O_fhb7_d14.tsv.meta
O_sd20_base_d12.tsv
O_sd20_base_d12.tsv.meta
O_sd20_base_d14.tsv
O_sd20_base_d14.tsv.meta
O_sd20_fhb7_d12.tsv
O_sd20_fhb7_d12.tsv.meta
O_sd20_fhb7_d14.tsv
O_sd20_fhb7_d14.tsv.meta

forge-combo29/astra5/job1/step0:
build-provenance.txt
check_step0.py
lock-build.txt
lock-no-setoption-bench-11.txt
lock-no-setoption-bench-13.txt
lock-no-setoption-go-perft-5.txt
lock-uci.txt
pc-PC20-bench-11.txt
pc-PC20-bench-13.txt
pc-S14-bench-11.txt
pc-S14-bench-13.txt
pc-build.txt
pc-no-setoption-bench-11.txt
pc-no-setoption-bench-13.txt
pc-no-setoption-go-perft-5.txt
pc-patch.txt
pc-uci.txt
pca-PC20-bench-11.txt
pca-PC20-bench-13.txt
pca-build.txt
pca-no-setoption-bench-11.txt
pca-no-setoption-bench-13.txt
pca-no-setoption-go-perft-5.txt
pca-patch.txt
pca-uci.txt

forge-combo29/astra5/job2:
count_on_pcad.patch.txt
counters.py
de_options.patch.txt
prediction.txt
run_counts.py
stamps.txt
step0
step0-results.txt
step1
step2
step3
step4
step4-grades.md
step4-tables.md
step5
validate.py

forge-combo29/astra5/job2/step0:
pca-PC20-bench-11.txt
pca-PC20-bench-13.txt
pca-no-setoption-bench-11.txt
pca-no-setoption-bench-13.txt
pca-no-setoption-go-perft-5.txt
pca-uci.txt

forge-combo29/astra5/job2/step1:
de_options-apply.txt
options-lines.txt
pcad-build.txt
pcad-uci.txt

forge-combo29/astra5/job2/step2:
G_base.tsv
G_base.tsv.meta
G_del.tsv
G_del.tsv.meta
G_del_fhb7.tsv
G_del_fhb7.tsv.meta
G_dm0.tsv
G_dm0.tsv.meta
G_dm12.tsv
G_dm12.tsv.meta
G_fhb7.tsv
G_fhb7.tsv.meta
G_sd20_base.tsv
G_sd20_base.tsv.meta
G_sd20_fhb7.tsv
G_sd20_fhb7.tsv.meta
G_sm1.tsv
G_sm1.tsv.meta
O_base.tsv
O_base.tsv.meta
O_del.tsv
O_del.tsv.meta
O_del_fhb7.tsv
O_del_fhb7.tsv.meta
O_dm0.tsv
O_dm0.tsv.meta
O_dm12.tsv
O_dm12.tsv.meta
O_fhb7.tsv
O_fhb7.tsv.meta
O_sd20_base.tsv
O_sd20_base.tsv.meta
O_sd20_fhb7.tsv
O_sd20_fhb7.tsv.meta
O_sm1.tsv
O_sm1.tsv.meta
checks.txt

forge-combo29/astra5/job2/step3:
G_base.tsv
G_base.tsv.meta
G_del.tsv
G_del.tsv.meta
G_del_fhb7.tsv
G_del_fhb7.tsv.meta
G_dm0.tsv
G_dm0.tsv.meta
G_dm12.tsv
G_dm12.tsv.meta
G_fhb7.tsv
G_fhb7.tsv.meta
G_sd20_base.tsv
G_sd20_base.tsv.meta
G_sd20_fhb7.tsv
G_sd20_fhb7.tsv.meta
G_sm1.tsv
G_sm1.tsv.meta
O_base.tsv
O_base.tsv.meta
O_del.tsv
O_del.tsv.meta
O_del_fhb7.tsv
O_del_fhb7.tsv.meta
O_dm0.tsv
O_dm0.tsv.meta
O_dm12.tsv
O_dm12.tsv.meta
O_fhb7.tsv
O_fhb7.tsv.meta
O_sd20_base.tsv
O_sd20_base.tsv.meta
O_sd20_fhb7.tsv
O_sd20_fhb7.tsv.meta
O_sm1.tsv
O_sm1.tsv.meta
checks.txt
count_on_pcad-apply.txt
counts-lines.txt
crosscheck.txt
kimi5-exact-attempt.txt
kimi5-on-pca-apply.txt
pcadc-build.txt

forge-combo29/astra5/job2/step4:
G_base.tsv
G_base.tsv.meta
G_del.tsv
G_del.tsv.meta
G_del_fhb7.tsv
G_del_fhb7.tsv.meta
G_dm0.tsv
G_dm0.tsv.meta
G_dm12.tsv
G_dm12.tsv.meta
G_fhb7.tsv
G_fhb7.tsv.meta
G_sd20_base.tsv
G_sd20_base.tsv.meta
G_sd20_fhb7.tsv
G_sd20_fhb7.tsv.meta
G_sm1.tsv
G_sm1.tsv.meta
O_base.tsv
O_base.tsv.meta
O_del.tsv
O_del.tsv.meta
O_del_fhb7.tsv
O_del_fhb7.tsv.meta
O_dm0.tsv
O_dm0.tsv.meta
O_dm12.tsv
O_dm12.tsv.meta
O_fhb7.tsv
O_fhb7.tsv.meta
O_sd20_base.tsv
O_sd20_base.tsv.meta
O_sd20_fhb7.tsv
O_sd20_fhb7.tsv.meta
O_sm1.tsv
O_sm1.tsv.meta
checks.txt

forge-combo29/astra5/job2/step5:
check_slot.py
evidence
rows
run_slot.sh
slot16.patch.txt

forge-combo29/astra5/job2/step5/evidence:
slot16-apply.txt
slot16-build.txt
slot16-source.txt

forge-combo29/astra5/job2/step5/rows:
first20
first20-summary.txt
full
full-summary.txt

forge-combo29/astra5/job2/step5/rows/first20:
G_base.tsv
G_base.tsv.meta
G_del.tsv
G_del.tsv.meta
G_del_fhb7.tsv
G_del_fhb7.tsv.meta
G_fhb7.tsv
G_fhb7.tsv.meta
O_base.tsv
O_base.tsv.meta
O_del.tsv
O_del.tsv.meta
O_del_fhb7.tsv
O_del_fhb7.tsv.meta
O_fhb7.tsv
O_fhb7.tsv.meta

forge-combo29/astra5/job2/step5/rows/full:
G_base.tsv
G_base.tsv.meta
G_del.tsv
G_del.tsv.meta
G_del_fhb7.tsv
G_del_fhb7.tsv.meta
G_fhb7.tsv
G_fhb7.tsv.meta
O_base.tsv
O_base.tsv.meta
O_del.tsv
O_del.tsv.meta
O_del_fhb7.tsv
O_del_fhb7.tsv.meta
O_fhb7.tsv
O_fhb7.tsv.meta
```
