# sol2 — Job 2 r15d reconstruction, identity and profile

## Step 0 — plain-base pins passed

The unchanged Job 1 executable (`2f545495d4e3e2b59af49fbb18212ec2ed8ae297d801e58647cfea37cd18e785`) reproduced **312,866** for `bench 11`, **862,329** for `bench 13`, and **4,865,609** for startpos `go perft 5`. Each command used a fresh process with embedded AL1 s198, Threads 1, Hash 16 MiB, one PV, OwnBook false, UseNNUE true, and other options at their defaults. All three engines' pin runs below used these same settings. [Plain-base raw commands and output](sol2/job2/step0-pins.raw.txt) · [Build and host identity](sol2/job2/step0-identity.txt)

## Step 1 — r15 and r15d reconstructed and pinned

Applied the exact patches in order to separate copies of base `6b98f2170a3210e71beed04bbd2553972c253ed7`. Patch used `-p1 --fuzz=0`. All hunks applied, and both built executables passed 312,866 / 862,329 / 4,865,609 under the Step 0 settings. [Patch output, hashes and command trace](sol2/job2/step1-rebuild.raw.txt) · [r15 raw pins](sol2/job2/step1-r15-pins.raw.txt) · [r15d raw pins](sol2/job2/step1-r15d-pins.raw.txt)

| Input | SHA-256 |
|---|---|
| PC r15 patch from Swarm 5 | `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a` |
| Carbon2 P1–P6 | `034814873e2ffce7010b7b065d79b5aa0a57419cbb75cc8bfc4ff22208278cea` |
| Carbon2 E1 | `20cca10770a32af8d9b7b26b9fd9544fefb67e592b35177f68788cfd73ab7574` |
| Original Swarm 7 net generator | `d26f09cf2c5f620d9a3293b787a2dacd8b386ea325d170509952662f71041558` |
| Generated net768 | `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7` |

Both builds used GCC 14.2.0, libstdc++ 6.0.33, glibc 2.41, CMake 3.31.10 Release, `-march=x86-64-v4`, `-O3`, `-ffp-contract=off`, `-fno-fast-math`, the six CMake speed switches, `FORGE_MATE_ALPHA_GUARD=1` and `FORGE_NNUE_V3=1`. These are GCC builds without PGO or LTO. Binary SHA-256 values are `5eae21cde9ad26775da663237ad24106639c9b0820f1adeb245ff2775b8e626e` for r15 and `bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6` for r15d. Both loaded and activated the synthetic net after the path was set, reporting `hidden 768` and checksum `30ab43b4ba5db5f3` with the AVX-512 kernel. The embedded weights source SHA-256 was `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. [r15 compile and link lines](sol2/job2/step1-r15-build.raw.txt) · [r15d compile and link lines](sol2/job2/step1-r15d-build.raw.txt) · [r15 activation](sol2/job2/step1-r15-net.raw.txt) · [r15d activation](sol2/job2/step1-r15d-net.raw.txt)

## Step 2 — all 400 fixed-node pairs agreed

The reconstructed builds agreed on depth, score, nodes and bestmove for **200/200 per evaluation**. The input was the first 200 positions of the official UHO book (`7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`), with PC20 in the prescribed option order, one thread, Hash 16 MiB, `ucinewgame` and `isready` before each position, and `go nodes 20000`. The numbers below sum the last `info` nodes, which can be lower than the command's hard ceiling. The raw transcripts include option declarations, all replies through `readyok` and the UCI search output. [Book identity](sol2/job2/step2-book-identity.txt) · [UCI files and comparisons](sol2/job2/step2)

| Evaluation | Matched positions | Last `info` nodes per build |
|---|---:|---:|
| Embedded AL1 s198 | 200/200 | 3,055,154 |
| Synthetic net768 | 200/200 | 2,625,271 |

## Step 3 — seeded self-play matched across builds and differed from the cited pin

Carbon2's named `selfplay_driver.py` produced **8,612 searches, 29,333,343 last-info nodes, trace `5c705841c3ea17b4`** on both r15 and r15d. Each run used 60 games, PC20, Threads 1, Hash 16 MiB, net768, `go softnodes 2000`, 8 random opening plies from startpos, seed `20261117` and a 300-ply ceiling. The cited **7,670 / 25,641,316 / `ee465caeff9c0fcf`** trace comes from Carbon2's Clang 18.1.3 ThinLTO/PGO `sapphirerapids` r15d timing using FEN roots selected from `positions_250.txt`. The different positions explain why the cited trace is unsuitable as a known answer for the named startpos driver. Steps 4 and 5 therefore use the prescribed first-200-UHO fallback with the reconstructed GCC builds, net768, PC20 and `go softnodes 2000`. [Executed commands](sol2/job2/step3-commands.raw.txt) · [r15 JSON](sol2/job2/step3-r15.stdout.txt) · [r15d JSON](sol2/job2/step3-r15d.stdout.txt) · [Carbon2 Job 11 reference](https://github.com/couns0538-sketch/dwqww/blob/d15357a6c3a507db81404b44bdb51b3ee05382dc/forge-combo29/carbon2/job11/REPORT_carbon2_job11.md) · [FEN-root timing harness](https://github.com/couns0538-sketch/dwqww/blob/d15357a6c3a507db81404b44bdb51b3ee05382dc/forge-combo29/carbon2/job8/run_selfplay_hash16_abba.py)

## Prediction grade

[Prediction](sol2/job2/prediction.txt) was pushed alone at `33801ef6aa70ad5ce8df187e7200531c81d79918` before the profile and timed runs. `Worker::search` was in the top three resolved machine functions. `Worker::qsearch` ranked tenth and `nnue::v3::evaluate` missed the top three. The fused `apply_pair_and_evaluate` placed second. The **1.15× CPU** prediction missed the observed **0.968×**, outside the factor-of-1.1 band. The **1.12× wall** prediction was within the band of the observed **1.125×**. [Resolved functions](sol2/job2/step4/top15-with-libc-symbols.raw.tsv.txt) · [Paired results](sol2/job2/step5/timing-readback.txt)

## Step 4 — exclusive per-thread CPU samples

`perf` was unavailable and the kernel denied a task-clock `perf_event_open` probe. I used a per-thread POSIX CPU-timer sampler that captures the interrupted user instruction pointer every 3,989 µs of charged thread CPU time. The symbol build added only `-g`. Its `.text` matched the unprofiled r15d byte for byte. Ten separate fallback passes each searched the same 200 UHO positions and reproduced the identical timed search trace with **647,494 final nodes per pass**. The profile pooled **1,035** captured samples with **277** timer overruns reported. It includes engine startup, net load, cold `ucinewgame` at every position and shutdown. Shares are exclusive sample counts. The sampler records instruction pointers alone. Out-of-line library work and kernel I/O remain unattributed to Forge callers. [Profiler probe](sol2/job2/step4/profiler-availability.raw.txt) · [Symbol build](sol2/job2/step4/build.raw.txt) · [Profile receipts](sol2/job2/step4/profile.raw.txt) · [Trace readback](sol2/job2/step5/profile-trace-readback.txt)

The initial stripped libc lookup mislabeled sampled PCs. A readback with the matching Debian glibc build ID resolves the top hot spot to its AVX-512 `memset`. The table uses those resolved names and the modal sampled line. [Libc symbol readback](sol2/job2/step4/libc-symbol-readback.raw.txt)

| Rank | Function | Sampled file and line | Samples | Share |
|---:|---|---|---:|---:|
| 1 | `__memset_avx512_unaligned_erms` | `memset-vec-unaligned-erms.S:294` | 204 | 19.71% |
| 2 | `nnue::v3::apply_pair_and_evaluate` | `nnue_v3.cpp:892` | 88 | 8.50% |
| 3 | `Worker::search` | `search.cpp:2381` | 84 | 8.12% |
| 4 | `nnue::v3::load` | `nnue_v3.cpp:612` | 64 | 6.18% |
| 5 | `MovePicker::next` | `search.cpp:752` | 53 | 5.12% |
| 6 | `nnue::v3::refresh_from_pieces` | `nnue_v3.cpp:956` | 49 | 4.73% |
| 7 | `Board::make_move` | `board.cpp:1225` | 37 | 3.57% |
| 8 | `Board::see_ge` | `board.cpp:1490` | 32 | 3.09% |
| 9 | `Worker::corrected_eval` | `search.cpp:1421` | 30 | 2.90% |
| 10 | `Worker::qsearch` | `search.cpp:1843` | 28 | 2.71% |
| 11 | `TranspositionTable::probe_body<false>` | `search.cpp:492` | 26 | 2.51% |
| 12 | `MovePicker::pick_best` | `search.cpp:998` | 25 | 2.42% |
| 13 | `nnue::v3::apply_changes_pair` | `nnue_v3.cpp:857` | 25 | 2.42% |
| 14 | `Worker::static_evaluate_v3` | `search.cpp:3405` | 23 | 2.22% |
| 15 | `fill_pseudo_legal<GenMode 1>` | `board.cpp:547` | 23 | 2.22% |

| Subsystem | Samples | Share |
|---|---:|---:|
| Evaluation (NNUE v3) | 286 | 27.63% |
| Other runtime and libraries | 243 | 23.48% |
| Search control | 140 | 13.53% |
| Move ordering and picking | 126 | 12.17% |
| Move generation and legality | 91 | 8.79% |
| Board updates and position keys | 58 | 5.60% |
| Hash table | 43 | 4.15% |
| Static exchange evaluation | 23 | 2.22% |
| Draw and repetition checks | 12 | 1.16% |
| Other engine work | 11 | 1.06% |
| Unresolved | 1 | 0.10% |
| UCI and input/output | 1 | 0.10% |

[Full function table](sol2/job2/step4/top15-with-libc-symbols.raw.tsv.txt) · [Subsystem table](sol2/job2/step4/subsystems-with-libc-symbols.raw.tsv.txt)

## Step 5 — fallback timing

The plain r15 and r15d binaries ran alternately for ten pairs on logical CPU 2 of the AMD EPYC 9V74 cloud VM. Ten same-build r15d pairs include the requested first two-run A/A check and permit an interval for that control. Every pass matched the profiled r15d output on depth, seldepth, score, last-info and final nodes, PV and bestmove. Each pass had **200 searches, 628,693 last-info nodes, 647,494 final nodes** and the same canonical trace `4fb296a49f169ddd63789d281fc0810f2f736f37e1a8928fffc65f498b044b9b`. CPU is reaped engine user plus system time, and wall includes bring-up, UCI I/O, the Python harness and engine shutdown. Ratios divide the first by the second run within each pair. The intervals are percentile bootstrap intervals over ten paired ratios. [Per-run raw timing and identities](sol2/job2/step5/timing-rows.raw.jsonl.txt) · [Pairs, intervals and first A/A](sol2/job2/step5/timing-readback.txt)

| Comparison | Metric | Paired median | 95% interval | Ratios above 1 |
|---|---|---:|---:|---:|
| r15 / r15d | Engine CPU | 0.968× | 0.891–1.012× | 4/10 |
| r15 / r15d | Wall | 1.125× | 1.015–1.170× | 9/10 |
| r15d / r15d | Engine CPU | 1.025× | 0.927–1.121× | 7/10 |
| r15d / r15d | Wall | 1.021× | 0.932–1.127× | 7/10 |

The first A/A pair was **0.927× CPU** and **0.918× wall**. These short cold-control runs show considerable variability and the wall intervals overlap. An engine CPU gain and transfer to the owner’s PC remain unverified.

## Facts

- Both source reconstructions passed the locked anchors and all requested fixed-node comparisons. The two named startpos replay runs produced the same trace, and the fallback profile and timing runs reproduced each other's exact search outputs.
- `ucinewgame` calls `Searcher::clear()` at r15d `src/uci.cpp:490–497`. That clears the TT and workers at `src/search.cpp:3284–3287`. The TT clear at `458–464` and worker clear at `1217–1237` reset memory tables. The cold fallback does this before every measured opening. The named self-play driver clears once for each game.

## Suspicions

- The `memset` hot spot may reflect cold resets, allocations, or both. A caller-resolved profile of the validated warm self-play workload would distinguish them. It should retain the same move histories and separately account for setup, each game's initial reset, and positions reached after the opening.
- Draw and repetition checks ranked low on the fallback. These samples do not separate the repeated qsearch predicate from the other draw-path checks or establish its frequency on full game histories.

## What I did not do

Native work was confined to the cloud scratch builds and the requested replay, with only text evidence committed. The owner-PC compiler, profile and weights were outside the experiment.

## What I am not sure about

The sample overruns and repeated cold resets limit extrapolation to continuous warm self-play. The local A/B timing uses the same core for runner and engine and fixed r15-first pair order. Scheduling and harness effects remain mixed into the observed wall time.

GPT-6 (Codex), Case A. Claim, checkpoint and build/run times come from the cloud clock. [Stamps](sol2/job2/stamps.txt) · [Publication status and file layout](sol2/job2/publication-layout.raw.txt)
