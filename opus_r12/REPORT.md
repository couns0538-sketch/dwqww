# R12 - LTO+PGO profile that includes the HalfKA net path — DONE (winner: v2t1 + -fprofile-partial-training, exe 436ed8e1)

Branch `opus-r12-pgo-net` = 7f79c349 (r10fix1, the engine source of 9E5CB644 / D8D90B68; **engine unchanged**) + R12
commits (kit v2.4, tools, logs, report, skill). No Elo or gate claim; QA gates. Machine exclusive: no (gates, NNUE
trainer w4_s4 and self-play kept running). Cores: QA freed CPUs 0/1 at 20:14 PC clock (trainer mask 0x000F -> 0x000C);
every R12 build ran pinned to 0x3 (CPUs 0+1), every timing and 12k run on CPU 0 with CPU 1 idle, all BelowNormal;
free RAM stayed >= 13 GB (runners wait below 5 GB).

## Verdict
**Keep variant B: workload v2t1 + `-fprofile-partial-training`, exe `436ed8e1b0f63811d4dcd74f2e77d9c65c1b8d9b62047142c220c99baad2c720`** (pc1 = pc2, identity ALL OK, 12k 12000/12000).
- Net path (e9_best, engine nps, 7 palindromic ABBA blocks each): **+7.22% d16 / +7.27% d20 vs plain D8D90B68** (bootstrap 1-sided 95% lower bounds +3.16% / +6.17%), **+22.08% / +22.72% vs 9E5CB644** (LB +18.79% / +21.63%). Pass: the net path is faster than the plain build.
- No net vs the lock LP FD3A5190: **-0.04% d16 / -0.81% d20** (95% CI [-0.97%, +2.37%] / [-1.75%, -0.45%]), inside the A/A band (QA < 1.3%; B vs its own byte copy -0.70% at d20): no regression beyond measurement noise. QA judges the d20 -0.8%.
- Variant A (v2t1 without partial training, e06e0348): +4.17% / +5.60% vs D8D90B68, +19.99% / +20.18% vs 9E5CB644, but -2.83% / -3.21% vs FD3A5190 with no net (CI upper ends -1.27% / -0.34%): a small no-net regression. B beats A in all four comparisons by medians (+1.23 / +1.78 net, +2.87 / +1.51 no net); that lead is about the size of the per-file timing offset seen on this PC (A vs its byte copy -3.0% d16), so it is consistent but small.
- Workload v2 exactly as specified (Threads=2 `go` searches in the profile) cannot pass the binding check: two clean builds give different exes (both variants). The gated form is v2t1; SMP stays unprofiled (owner item).

## Acceptance
| # | item | result | evidence |
|---|---|---|---|
| 1 | kit workload v2: v1 frozen; no net + e19 + e9, each at Threads=1 and 2; `--no-insert-timestamp` kept | done as kit v2.4 `-Workload v2`; **v2 does not reproduce** (Threads=2 part), so the gated form is **`-Workload v2t1`** (= v2 without the Threads=2 searches); v1 untouched (default) | kit_v24/FROZEN_WORKLOAD.md, logs/funcdiff_*.txt |
| 2 | LTO+PGO HalfKA exe, kit v2.3 -Expose, znver5, FMA 0, pc1 = pc2 | v2t1: **e06e0348… pc1 = pc2** (byte-identical), vfmadd 0; v2t1 + partial training: **436ed8e1… pc1 = pc2**, vfmadd 0. (v2: pc1 != pc2 in both variants -> not used) | logs/builds/*/SUMMARY.txt, logs/chain_v2t1.log |
| 2b | variant with -fprofile-partial-training (GCC >= 10: MSYS2 g++ 15.2.0) | built (`-PartialTraining`), same checks, timed | logs/builds/r10fix1_v2t1pt_* |
| 3a | no net: bench d11..d22 = lock pins, perft 4865609 / 193690690 | ALL OK in all 8 builds (plain = LTO+PGO = pins) | logs/builds/*/ident/off.compare.txt |
| 3b | net: d11/d16 = 373062/4115992 (e19), 287095/2816047 (e9) = plain D8D90B68 | ALL OK at d11, d13, d16, d20, d22 (pins = D8D90B68's counts from QA's prebench), plain = LTO+PGO; the kit's plain build = D8D90B68 except the 4 PE timestamp/checksum bytes | logs/builds/*_pc1/ident/opt1/opt2.compare.txt |
| 3c | fens_12k parity 12000/12000 | **12000/12000** for both variants and both nets: `go depth 2` result (depth, score, nodes, bestmove) identical to D8D90B68 on every FEN (the LP exe has no eval command; D8D90B68's eval = nnue-pytorch 12000/12000 in R11) | logs/fens12k_*/compare.txt, logs/fens12k_outputs.sha256 |
| 4 | speed d16 + d20, >= 7 ABBA + 3 A/A; vs D8D90B68 and 9E5CB644 with the net; vs FD3A5190 without | done on CPU 0 (BelowNormal, CPU 1 idle), fresh process per run, d16 + d20, 7 palindromic ABBA blocks + 3 A/A blocks (byte copies) per depth and mode; B: net +7.2% / +7.3% vs D8D90B68 (LB > 0), +22% vs 9E5CB644; no net -0.04% / -0.81% vs FD3A5190 = PASS (no regression beyond A/A noise); A: no-net -2.8% / -3.2% vs FD3A5190 | logs/speed_*/ |
| 5 | cores / RAM | 0/1 freed by QA, see above; never on gate cores | logs/chain_v2t1.log, logs/speed_*/speed.log |
| 6 | stop rule (< 1% over 9E5CB644 after 90 min) | not triggered: at 21:13 (90 min) the net-path gain over 9E5CB644 was already measured at +20% (d16, 7 blocks) | logs/speed_net_e9/runs.csv |
| 7 | report, sha256s, commands, logs; CR patches | this file; `D:\grok-pc-data\r12_pgo\cr_patches` | FILES.txt, SHA256SUMS |

## Exes (sha256)
| exe | sha256 | what |
|---|---|---|
| forge_ltopgo_r10fix1_v2t1_pc1.exe (= _pc2) | e06e0348da4c6d4756cde5984f5c395c1b2055cca40489bf0630db5f6c75cd7a | **A**: LTO+PGO, workload v2t1, -Expose, znver5, vfmadd 0, 4,134,595 bytes |
| forge_ltopgo_r10fix1_v2t1pt_pc1.exe (= _pc2) | 436ed8e1b0f63811d4dcd74f2e77d9c65c1b8d9b62047142c220c99baad2c720 | **B**: A + -fprofile-partial-training, vfmadd 0, 4,153,811 bytes |
| forge_ltopgo_r10fix1_w2_pc1 / _pc2 | 8f162985ac76683092c304dba734d789c8d885d57b6a735026addb45ee240492 / 18503c4dae56d55e696d918770b34b68c081f27e5be4b36326a6ef745ba12ea1 | workload v2 (with Threads=2): pc1 != pc2, not used |
| forge_ltopgo_r10fix1_w2pt_pc1 / _pc2 | 63ae405f75eaa46885449486e7b16dd9b1f725eef094ee9428854ae618a80382 / ee5c8beaa5153d2b68bfd83139b850a538dcb22b9460fafc92e27167f77614fc | v2 + partial training: pc1 != pc2, not used |
| reference 9E5CB644 | 9e5cb64426d0ee66dee576e64c07efb0178eb84364578ebde0e445ebd65a2828 | `forge_push\bin\forge_ltopgo_x_r10fix1_halfka_9e5cb644.exe` (v1 LTO+PGO) |
| reference D8D90B68 | d8d90b68f8232f6eefe91cff2564c947763ce078e997f3946db45f4b0a0e82c7 | `forge_push\bin\forge_plain_z5_r10fix1_halfka_d8d90b68.exe` (plain) |
| reference FD3A5190 | fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072 | `forge_push\bin\forge_ltopgo_x_al1s198_v23.exe` (live lock LP) |
| nets | e19 bf1e347c545e3cbbb6e68c98793d1b4eb331c3564f7749175dbadf2eed4293ff, e9 5380f8665e591a5ca62ca160122be4f5d5cf9f83f1a51c254300933c83d39f36 | `forge_push\bin\r11_e19_final_bf1e347c.nnue`, `r11_e9_best_5380f866.nnue` |
| kit script used by the v2t1 builds | build_ltopgo.ps1 35c9996ade61586cc23525481ac1463565061a032882b121fa1784951d0d6400 (commit 417c1638) | v2 builds: 0fc1a0c5... (464f5270) |
| workloads | v2t1 dca15f6620f8622ab0fbfec29cb1a405607d394aae831b0cc736b004a34767e2; v2 52b8299ed4a2412c5295eca9438170aa9af17c844fe528374033050931f6d2ee; nets_v2 8448dae96755cb65f8880226b9fcc0b3ddf8904b9435021f747e0e9c4e2c74d3; v1 1d52720a... (unchanged) | kit_v24/workload/ |

Exes are in `F:\opus_scratch\r12\builds\<tag>\src_copy\` (copies used for timing: `F:\opus_scratch\r12\exe\`).

## Workload v2 as specified does not reproduce -> v2t1
- Two clean v2 builds, minutes apart on the same pair: 8f162985 vs 18503c4d; with partial training 63ae405f vs
  ee5c8bea. All four passed every identity check; only the code differs: 12 of 4686 / 23 of 4674 functions
  (logs/funcdiff_*.txt), all hot (Worker::search, qsearch, evaluate_position, static_evaluate, MovePicker::next,
  halfka::evaluate_raw, generate_pseudo_legal, see_ge, ...).
- Cause: the 24 Threads=2 `go nodes 200000` searches share the TT between two threads; the node split and tree shape
  depend on timing, and those counts feed exactly the code PGO optimizes hardest. `bench` cannot profile SMP at all: it
  always runs its own one-thread `Searcher(16)` with an exclusive TT lease, whatever Threads is.
- So the binding pc1 = pc2 rule and an SMP profile cannot both hold. v2t1 keeps the mixed net profile (no net, e19, e9;
  bench only, node-deterministic) and reproduces byte for byte. SMP code stays unprofiled, as with v1 (owner item).

## Speed (engine nps = the engine's own bench nps; CPU-nps tables in logs/speed_*/summary.txt agree)
Net e9_best = `r11_e9_best_5380f866.nnue` (QA's speed4 net). Gain = (nps X1 + X2) / (nps REF1 + REF2) - 1 per block; bootstrap = 10000 resamples of the block median, seed 20261030. Nodes equal in every run of an exe (checked by the harness). Runs: logs/speed_net_e9/runs.csv, logs/speed_nonet/runs.csv.

| net | depth | exe | vs | n blocks | median gain | bootstrap 95% lower bound (1-sided) | 95% CI | per block (%) |
|---|---|---|---|---|---|---|---|---|
| e9_best | d16 | A (v2t1) | D8D90B68 | 7 | +4.17% | +4.11% | [+4.11%, +5.51%] | +5.51 +10.95 +4.11 +3.60 +4.17 +4.16 +4.71 |
| e9_best | d16 | B (v2t1+pt) | D8D90B68 | 7 | +7.22% | +3.16% | [+3.16%, +8.00%] | +4.76 +12.32 +7.22 +3.16 +8.00 +7.59 +2.37 |
| e9_best | d16 | 9E5CB644 | D8D90B68 | 7 | -12.73% | -14.23% | [-14.23%, -11.81%] | -11.81 -8.00 -14.23 -13.25 -15.72 -12.44 -12.73 |
| e9_best | d16 | A (v2t1) | 9E5CB644 | 7 | +19.99% | +19.42% | [+19.42%, +21.39%] | +19.65 +20.60 +21.39 +19.42 +23.60 +18.96 +19.99 |
| e9_best | d16 | B (v2t1+pt) | 9E5CB644 | 7 | +22.08% | +18.79% | [+18.79%, +25.01%] | +18.79 +22.08 +25.01 +18.92 +28.14 +22.88 +17.30 |
| e9_best | d16 | D8D90B68 | 9E5CB644 | 7 | +14.59% | +13.39% | [+13.39%, +16.60%] | +13.39 +8.69 +16.60 +15.28 +18.65 +14.21 +14.59 |
| e9_best | d16 | B (v2t1+pt) | A (v2t1) | 7 | +1.23% | -0.71% | [-0.71%, +3.29%] | -0.71 +1.23 +2.98 -0.42 +3.67 +3.29 -2.24 |
| e9_best | d16 | D8D90B68 | A (v2t1) | 7 | -4.01% | -5.23% | [-5.23%, -3.95%] | -5.23 -9.87 -3.95 -3.47 -4.01 -4.00 -4.50 |
| e9_best | d16 | 9E5CB644 | A (v2t1) | 7 | -16.66% | -17.62% | [-17.62%, -16.26%] | -16.42 -17.08 -17.62 -16.26 -19.10 -15.94 -16.66 |
| e9_best | d16 | A (v2t1) | its byte copy (A/A) | 3 | -3.02% | - | - | -3.02 -2.91 -6.65 |
| e9_best | d16 | B (v2t1+pt) | its byte copy (A/A) | 3 | -0.83% | - | - | -2.50 -0.83 -0.23 |
| e9_best | d20 | A (v2t1) | D8D90B68 | 7 | +5.60% | +4.02% | [+4.02%, +5.92%] | +5.60 +5.62 +5.10 +2.93 +4.02 +6.18 +5.92 |
| e9_best | d20 | B (v2t1+pt) | D8D90B68 | 7 | +7.27% | +6.17% | [+6.17%, +7.92%] | +7.48 +7.27 +5.22 +6.17 +6.60 +8.05 +7.92 |
| e9_best | d20 | 9E5CB644 | D8D90B68 | 7 | -12.60% | -13.49% | [-13.49%, -11.87%] | -12.99 -12.60 -20.79 -13.49 -12.31 -11.17 -11.87 |
| e9_best | d20 | A (v2t1) | 9E5CB644 | 7 | +20.18% | +18.97% | [+18.97%, +21.37%] | +21.37 +20.85 +32.68 +18.97 +18.63 +19.53 +20.18 |
| e9_best | d20 | B (v2t1+pt) | 9E5CB644 | 7 | +22.72% | +21.63% | [+21.63%, +23.52%] | +23.52 +22.73 +32.84 +22.72 +21.57 +21.63 +22.45 |
| e9_best | d20 | D8D90B68 | 9E5CB644 | 7 | +14.42% | +13.47% | [+13.47%, +15.59%] | +14.93 +14.42 +26.25 +15.59 +14.04 +12.57 +13.47 |
| e9_best | d20 | B (v2t1+pt) | A (v2t1) | 7 | +1.78% | +1.56% | [+1.56%, +2.48%] | +1.78 +1.56 +0.12 +3.15 +2.48 +1.75 +1.89 |
| e9_best | d20 | D8D90B68 | A (v2t1) | 7 | -5.30% | -5.59% | [-5.59%, -3.86%] | -5.30 -5.32 -4.85 -2.84 -3.86 -5.82 -5.59 |
| e9_best | d20 | 9E5CB644 | A (v2t1) | 7 | -16.79% | -17.60% | [-17.60%, -15.95%] | -17.60 -17.25 -24.63 -15.95 -15.70 -16.34 -16.79 |
| e9_best | d20 | A (v2t1) | its byte copy (A/A) | 3 | -2.67% | - | - | +3.16 -3.48 -2.67 |
| e9_best | d20 | B (v2t1+pt) | its byte copy (A/A) | 3 | -1.13% | - | - | -1.13 -1.70 +1.83 |
| none | d16 | A (v2t1) | FD3A5190 | 7 | -2.83% | -3.74% | [-3.74%, -1.27%] | -1.27 -3.74 -7.25 -1.59 -0.35 -2.91 -2.83 |
| none | d16 | B (v2t1+pt) | FD3A5190 | 7 | -0.04% | -0.97% | [-0.97%, +2.37%] | +2.37 -0.87 -1.26 +0.54 +2.50 -0.97 -0.04 |
| none | d16 | B (v2t1+pt) | A (v2t1) | 7 | +2.87% | +2.17% | [+2.17%, +3.69%] | +3.69 +2.98 +6.46 +2.17 +2.86 +1.99 +2.87 |
| none | d16 | FD3A5190 | A (v2t1) | 7 | +2.91% | +1.29% | [+1.29%, +3.89%] | +1.29 +3.89 +7.82 +1.62 +0.35 +2.99 +2.91 |
| none | d16 | A (v2t1) | its byte copy (A/A) | 3 | -2.50% | - | - | -2.50 -1.94 -3.08 |
| none | d16 | B (v2t1+pt) | its byte copy (A/A) | 3 | +0.15% | - | - | -1.78 +7.19 +0.15 |
| none | d20 | A (v2t1) | FD3A5190 | 7 | -3.21% | -4.49% | [-4.49%, -0.34%] | -4.49 +5.35 -8.03 -0.34 -1.07 -3.21 -3.54 |
| none | d20 | B (v2t1+pt) | FD3A5190 | 7 | -0.81% | -1.75% | [-1.75%, -0.45%] | -0.45 +6.88 -2.71 -0.98 -0.67 -1.75 -0.81 |
| none | d20 | B (v2t1+pt) | A (v2t1) | 7 | +1.51% | +0.40% | [+0.40%, +4.23%] | +4.23 +1.45 +5.78 -0.64 +0.40 +1.51 +2.83 |
| none | d20 | FD3A5190 | A (v2t1) | 7 | +3.32% | +0.34% | [+0.34%, +4.70%] | +4.70 -5.08 +8.73 +0.34 +1.08 +3.32 +3.67 |
| none | d20 | A (v2t1) | its byte copy (A/A) | 3 | -0.58% | - | - | -0.58 +4.56 -2.79 |
| none | d20 | B (v2t1+pt) | its byte copy (A/A) | 3 | -0.70% | - | - | -0.70 -0.87 +0.21 |

B vs A from the A/A blocks (originals / byte copies / pooled; logs/speed_*/B_vs_A_from_AA_blocks.txt): net d16 +2.93 / -0.98 / +2.31%, d20 +0.82 / -2.29 / -1.26%; no net d16 +3.06 / -0.18 / +0.59%, d20 -0.73 / +3.38 / +0.63%: file placement moves single comparisons by up to about 3% on this PC (R5B lesson), so B's lead over A is real in direction but small.


## Exact build commands (PC, from logs/chain_v2t1.log)
Each build = `powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "& '<kit>\build_ltopgo.ps1' ...; exit $LASTEXITCODE"`
(started by `tools/r12_build_chain.py --workload v2t1`, BelowNormal, kit affinity 3):

    & 'F:\opus_scratch\worktrees\opus-r12-pgo-net\opus_r12\kit_v24\build_ltopgo.ps1' -SrcDir 'F:/opus_scratch/r12/src_r10fix1'
      -Tag 'r10fix1_v2t1_pc1' -Work 'F:/opus_scratch/r12/builds' -Affinity 3 -Expose -Workload v2t1
      -Python 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
      -Pins 'd11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354' -PerftPins 'startpos=4865609,kiwipete=193690690'
      -CheckOpt 'EvalFileHalfKA=C:\Users\Administrator\grok-pc\forge_push\bin\r11_e19_final_bf1e347c.nnue','EvalFileHalfKA=C:\Users\Administrator\grok-pc\forge_push\bin\r11_e9_best_5380f866.nnue'
      -CheckOptPins 'd11=373062,d13=831975,d16=4115992,d20=17885060,d22=37006232','d11=287095,d13=693432,d16=2816047,d20=12332089,d22=25323515'
    # _pc2: same with -Tag 'r10fix1_v2t1_pc2' and without -CheckOpt/-CheckOptPins (binding = exe sha256)
    # variant B: same plus -PartialTraining, tags r10fix1_v2t1pt_pc1 / _pc2

Compiler lines inside the kit (g++ 15.2.0 MSYS2 ucrt64; `$F` = `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256
-ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1`):
- plain: `g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -DFORGE_EXPOSE_TUNABLES=1 -Iinclude src/*.cpp -o forge_plain_<tag>.exe`
- instrumented, per unit: `g++ $F -flto=1 -fuse-linker-plugin -fprofile-generate=<P2> -fprofile-update=single -c src/<u>.cpp -o obj_ltopgo/<u>.o`; link with `-static`
- training: `python train_driver.py forge_instr_<tag>.exe workload\frozen_train_cmds_v2t1.txt workload\nets_v2.txt train_engine_out.txt --net e19=<e19> --net e9=<e9>`
- use, per unit: `g++ $F -flto=1 -fuse-linker-plugin -fprofile-use=<P2> -fprofile-correction -Wmissing-profile [-fprofile-partial-training] -c src/<u>.cpp -o obj_ltopgo/<u>.o`
- link: `g++ $F -flto=1 -fuse-linker-plugin -fprofile-use=<P2> -fprofile-correction -Wmissing-profile [-fprofile-partial-training] -static -Wl,--no-insert-timestamp obj_ltopgo/*.o -o forge_ltopgo_<tag>.exe`
  (full line with paths: logs/builds/*/build_use.log). Warnings: plain 0; LTO+PGO 1 = the known lto-wrapper note
  "using serial compilation of 3 LTRANS jobs"; real missing-profile/coverage warnings 0.

## Time (measured from commits and logs)
Commits 19:52:52 - the final commit (`git log -1 --format=%ci opus-r12-pgo-net`; report finished after 22:48) PC clock (job start 19:43, first look at the PC). Waiting for a free pair 20:02 - 20:14.
v2 builds 20:14 - 20:29 (4 builds), v2t1 builds 20:29 - 20:42, 12k identity 20:41:51 - 20:42:08,
speed net (e9) 20:42 - 20:59, no net 20:59 - 22:03 (55 min of it waiting: the pair was busy 21:02 - 21:57, blocks only start on a free pair).

## Not done / owner items
- Code Review first (patches in `D:\grok-pc-data\r12_pgo\cr_patches`), then QA gates exe 436ed8e1... (variant B);
  GATE_EXE = that sha256. Gate pairing is QA's call under the kit rule "same build mode and same workload on both
  sides": a net-vs-net gate on this one exe (e19 vs e9) is same-mode by construction; the lock source (AL1 s198) has
  no EvalFileHalfKA, so it cannot be trained with v2t1, and a net-vs-lock LP gate would pair v2t1 (436ed8e1) with v1
  (FD3A5190) - a rule question for QA/CR, not decided here.
- CR decision: SMP profiling (Threads >= 2 code: shared-TT `lock_stripe` path, helper threads) is impossible under the exe-sha256 rule; options are a changed rule (pc2 rebuilt from pc1's archived .gcda) or leaving SMP unprofiled (v1 and v2t1 both do). `-fprofile-partial-training` covers functions that never ran, not cold blocks inside hot functions.
- Only e9_best was timed (QA's speed4 net); e19 shares the identity and 12k checks but has no speed run.
- The A-vs-B decision with several byte copies per variant (`tools/r12_pooled.py`) was prepared but not run: the pair was busy again at 22:46 and the budget was used up. Its waiting runner was neutralised by renaming its copy exes to `*.exe.parked` (F:\opus_scratch\r12\exe\copies): it exits at its first run instead of timing anything.
- No-net d20 block 2 (21:01:28 - 21:02:02) ended right before the pair became busy; it is the outlier block (+6.88% B vs FD); the median without it is -0.89%, same conclusion.
- The box script build_ltopgo.sh is unchanged (v2 / v2t1 are PC-only: Windows net paths, driver call).
- Leftover background processes of this job: none doing work; the parked copies runner waits for the pair and then exits.
