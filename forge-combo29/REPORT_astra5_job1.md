# astra5 job 1 — FailHighBlend and singular search

Case A. Codex (GPT-6), working as astra5. I built and ran the engines locally and pushed the evidence to `for-fable-and-opus/astra5-work`.

## Step 0 — all 15 known answers matched

Each result came from a fresh process. The lock used the unmodified Release tree at `16833ecc03b425586f91f4c8834dea8807bf4c22`. PC used the helper base `6b98f2170a3210e71beed04bbd2553972c253ed7` plus the PC r15 patch. PCA added kimi5's A2A5 patch from `5db05e095d5e81622eb0de13eb8a738a0ae1d22a`. I used GNU C++ 14.2.0 (Debian 14.2.0-19) and CMake 3.31.10. Both PC builds used `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`.

| Build | Settings | Bench 11 nodes | Bench 13 nodes | Perft 5 nodes |
|---|---|---:|---:|---:|
| LOCK | no-setoption | 312,866 | 862,329 | 4,865,609 |
| PC | no-setoption | 312,866 | 862,329 | 4,865,609 |
| PC | S14 | 242,796 | 656,517 | — |
| PC | PC20 | 278,024 | 587,276 | — |
| PCA | no-setoption | 312,866 | 862,329 | 4,865,609 |
| PCA | PC20 | 278,024 | 587,276 | — |

For the no-setoption checks I sent zero `setoption` commands. The UCI listing advertises Hash 32 and Threads 1 by default. The bench code constructs a 16 MiB searcher, and perft counts legal moves without searching a transposition table. All configured runs sent Threads 1 and Hash 16 before the ordered S14 or PC20 settings.

<details><summary>Raw engine outputs for the 15 known answers</summary>

```text
lock-no-setoption-bench-11.txt
readyok
info string bench depth 11 nodes 312866 time 234 nps 1337034

lock-no-setoption-bench-13.txt
readyok
info string bench depth 13 nodes 862329 time 641 nps 1345287

lock-no-setoption-go-perft-5.txt
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

pc-no-setoption-bench-11.txt
readyok
info string bench depth 11 nodes 312866 time 283 nps 1105533

pc-no-setoption-bench-13.txt
readyok
info string bench depth 13 nodes 862329 time 719 nps 1199344

pc-no-setoption-go-perft-5.txt
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

pc-S14-bench-11.txt
readyok
info string bench depth 11 nodes 242796 time 184 nps 1319543

pc-S14-bench-13.txt
readyok
info string bench depth 13 nodes 656517 time 515 nps 1274790

pc-PC20-bench-11.txt
readyok
info string bench depth 11 nodes 278024 time 221 nps 1258027

pc-PC20-bench-13.txt
readyok
info string bench depth 13 nodes 587276 time 467 nps 1257550

pca-no-setoption-bench-11.txt
readyok
info string bench depth 11 nodes 312866 time 485 nps 645084

pca-no-setoption-bench-13.txt
readyok
info string bench depth 13 nodes 862329 time 926 nps 931240

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
info string bench depth 11 nodes 278024 time 626 nps 444127

pca-PC20-bench-13.txt
readyok
info string bench depth 13 nodes 587276 time 700 nps 838965
```

</details>

The saved `pc_r15.patch` matched SHA-256 `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`. The PCA patch matched `0bcb88c59fe3659f4ab71a4fededd453f4713e6dd4d86e6e0c45b557ba86b991`. These are the verbatim PCA `patch -p1 -F0` output and option declarations.

```text
patching file src/search.cpp
patching file include/forge/search.hpp
option name FailHighBlend type spin default 0 min 0 max 7
option name RfpNoTtPv type spin default 0 min 0 max 1
option name RfpTtGuard type spin default 0 min 0 max 1
option name RfpCorrMul type spin default 0 min 0 max 64
```

The plain PC harness self-check produced the required stop.

```text
id name Chess Engine Forge 6.4.24 candidate
sent: setoption name FailHighBlend value 7
STOP: engine diagnostic: info string unknown option FailHighBlend
exit 1
```

Full inputs, UCI listings, build commands and executable hashes are in the [Step 0 transcripts](astra5/job1/step0).

## Steps 1 and 2 — all eight depth-12 sets matched

All rows use PCA, PC20, Threads 1 and Hash 16. Step 1 used PC20’s SingularDepth 6. Step 2 sent SingularDepth 20 after PC20. The `fhb7` runs then sent FailHighBlend 7. Each hash uses the first 16 hexadecimal digits of SHA-256 over one value and one LF per position.

| Step | Suite | Blend | Rows | Node sum | First three node counts | Node hash | Move hash | Check |
|---:|---|---|---:|---:|---|---|---|---|
| 1 | O | base | 200 | 8,315,168 | 21812, 26844, 35173 | `fd609b7b1a8dd179` | `14583c86b5f56cb6` | Equal |
| 1 | O | fhb7 | 200 | 7,913,480 | 18623, 19820, 32078 | `75509856e2b96287` | `1ec0bb858b7ca372` | Equal |
| 1 | G | base | 353 | 17,611,204 | 31779, 46086, 84457 | `60b6916f01395e99` | `0846f027e7e9b77e` | Equal |
| 1 | G | fhb7 | 353 | 15,879,039 | 30412, 57137, 44902 | `48255179b3c50754` | `6c7dc5dc109bdd8b` | Equal |
| 2 | O | base | 200 | 7,872,425 | 15316, 35349, 27851 | `b3acd46e92320d05` | `296c7c69b055cfd1` | Equal |
| 2 | O | fhb7 | 200 | 8,464,273 | 26752, 32523, 30913 | `56bf264a91c83fac` | `451b92ec02705bfe` | Equal |
| 2 | G | base | 353 | 9,785,780 | 23141, 9625, 24306 | `ba892ddade29aaa0` | `5755b8f1445c16b6` | Equal |
| 2 | G | fhb7 | 353 | 10,512,013 | 31876, 12304, 35729 | `71bddd29608380cb` | `53bc895f0cea1f02` | Equal |

Step 1 also matched kimi5's original node count and best move for every one of the 1,106 position/run pairs. The normalized FEN order matched the pinned EPD inputs. Step 2 was checked against the supplied sums, prefixes and two ordered hashes. [Step 1 reference comparison](astra5/job1/step1-reference.txt)

## Prediction grades

Commit `63a8b677c28c9323de50f3d3904deb586caa9916` fixed the following bounds after Step 2 and before the first depth-14 process. Each grade uses the unrounded ratio of node sums and includes both endpoints. The two PC20 targets used disclosed totals. The two SingularDepth 20 targets were forecasts. [Frozen prediction](https://github.com/couns0538-sketch/dwqww/blob/63a8b677c28c9323de50f3d3904deb586caa9916/forge-combo29/astra5/job1/prediction.txt)

| Suite | SingularDepth | Predicted ratio | Accepted range | Measured ratio | Grade |
|---|---:|---:|---:|---:|---|
| G | 6 | 0.9305 | [0.9304, 0.9306] | 0.93050 | Inside |
| G | 20 | 1.0900 | [1.0150, 1.1500] | 1.12639 | Inside |
| O | 6 | 0.9702 | [0.9701, 0.9703] | 0.97017 | Inside |
| O | 20 | 1.0750 | [1.0100, 1.1400] | 1.09145 | Inside |

## Step 3 — depth 14, FailHighBlend 7 versus base

All measurements use PCA with PC20, Threads 1 and Hash 16. Both arms of each comparison use the displayed SingularDepth. Each bootstrap draw sampled paired position indices with replacement, retained the original suite size and took the ratio of the two node sums. The interval uses sorted draws 100 and 3899, counting from zero, from 4,000 resamples with seed 20261118.

| Suite | SingularDepth | Positions in each arm | Base nodes | FHB7 nodes | FHB7 / base | Paired bootstrap interval | Changed best moves |
|---|---:|---:|---:|---:|---:|---:|---:|
| G | 6 | 353 | 41,052,503 | 38,199,553 | 0.93050 | [0.87089, 0.99006] | 98 |
| G | 20 | 353 | 22,800,966 | 25,682,767 | 1.12639 | [1.07092, 1.18449] | 83 |
| O | 6 | 200 | 19,377,109 | 18,799,184 | 0.97017 | [0.91608, 1.02614] | 40 |
| O | 20 | 200 | 22,738,793 | 24,818,281 | 1.09145 | [1.03482, 1.14644] | 52 |

From the repository root, `sh forge-combo29/astra5/job1/grade.sh` recounts the eight TSVs, prints the number of rows it read in each, verifies both ordinary-PC20 pairs of known sums, and grades all four ratios. [Row files and metadata](astra5/job1/rows) · [Command output](astra5/job1/grades.txt)

## Facts

At depth 14, FailHighBlend 7 reduced the measured PC20 node sum by 6.95% on G and 2.98% on O. With SingularDepth raised from 6 to 20, it increased the sum by 12.64% on G and 9.15% on O. Both growth intervals lie wholly above 1. The ordinary PC20 interval lies below 1 on G and spans 1 on O. The same sign reversal appeared at depth 12 on both suites. An independent recount reproduced the four pairs of depth-14 node totals, intervals, move-change counts and prediction grades from the TSVs.

The comparison always uses the base at the same singular setting. Raising SingularDepth also moved the unblended baseline itself, from 41.05M to 22.80M nodes on G and from 19.38M to 22.74M on O at depth 14. Pooling the two suites would obscure that difference.

## Suspicions

Kimi5 saw fewer double extensions under blending on G at depth 12. Suppressing the singular test reverses the aggregate effect on both suites here, which supports an interaction between fail-high blending and singular search. The experiment switches the whole singular test, including extensions, negative extensions and multi-cuts. It cannot allocate saved nodes among those decisions.

## What I did not do

I ran fixed-depth searches with the built-in evaluation. I ran no games, strength tests, timing comparisons or instrumented counter builds. I did not change the engine source in the repository.

## What I am not sure about

These position-bootstrap intervals quantify variation when resampling the supplied suites. Generalization to a different opening or endgame mix, a different depth, or equal-time playing strength remains open. The greater best-move agreement in one arm does not tell us which moves are better.

## Reproduction

The position inputs are `forge-combo29/tests_kimi5_job25/{G,O}.epd` at kimi5 commit `5db05e095d5e81622eb0de13eb8a738a0ae1d22a`. G has 353 lines and SHA-256 `af3aefd80fcea207b215e95560f5921aa7a3bb9186d4cdfadf2e567207b5c54d`. O has 200 lines and SHA-256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`. Each row uses four position fields followed by `0 1`. Each TSV has its own `.meta` file with the ordered UCI settings, executable hash, engine name and completed row count. The runner waits for `readyok` after each `ucinewgame`, then takes nodes from the last info line with both depth and nodes before `bestmove`.

To replay each stage from the repository root, point `PCA_EXE` to the rebuilt executable and `EPD_DIR` to the pinned inputs. Choose a fresh `ROWS_DIR`. [Build transcript](astra5/job1/step0/build-provenance.txt)

```sh
python3 forge-combo29/astra5/job1/run_step.py 1 "$PCA_EXE" "$EPD_DIR" "$ROWS_DIR"
python3 forge-combo29/astra5/job1/run_step.py 2 "$PCA_EXE" "$EPD_DIR" "$ROWS_DIR"
python3 forge-combo29/astra5/job1/run_step.py 3 "$PCA_EXE" "$EPD_DIR" "$ROWS_DIR"
```

## Pre-commit working tree and evidence files

```text
$ git status --short && ls -R forge-combo29/astra5
 M forge-combo29/NOTES_astra5.md
 A forge-combo29/REPORT_astra5_job1.md
M  forge-combo29/astra5/job1/stamps.txt
M  forge-combo29/astra5/job1/step0/build-provenance.txt
forge-combo29/astra5:
job1

forge-combo29/astra5/job1:
analyze.py
audit_step1.py
grade.sh
grades.txt
harness-selfcheck.txt
harness.py
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
```
