# sol3 — Job 9 v3 path counts and position cache

**Step 0 passed.** The retained r15d, k11v, k11v-verify and net768 hashes matched. Fresh default and PC20 checks on r15d and k11v returned the assigned counts. The PC20 runs activated net768 checksum `30ab43b4ba5db5f3` before either bench. [Build and net pins](sol3/job9/stage0/expected_sha256.txt) · [Pin check](sol3/job9/stage0/sha256_check.txt) · [Raw-count readback](sol3/job9/stage0/pins.txt)

| Build | Default bench 11 | Default bench 13 | Default perft 5 | PC20 net768 bench 11 | PC20 net768 bench 13 |
| --- | ---: | ---: | ---: | ---: | ---: |
| r15d | 312866 | 862329 | 4865609 | 882074 | 4275906 |
| k11v | 312866 | 862329 | 4865609 | 882074 | 4275906 |

**Prediction grade.** Part A returned 15228637 evaluations including warm-up versus about 15230000 predicted. The combined same-key update share was 59.58% versus 60% forecast. Fused refresh was 18.90% versus 18%, and the literal refresh call count was 2046047 versus about 2200000. Part B matched the four-way position diagnostics and both within-mode search comparisons. The first control difference was the predicted eval at position command 2. The prediction was published alone at `a41a4c5061c387a798f04538aec888d4a299c9db`. [Prediction](sol3/job9/prediction.txt) · [Path totals](sol3/job9/partA/totals.json)

### Part A v3 evaluations counted by path

The counting build repeated k11v’s 60-game PC20 net768 workload with Threads 1, Hash 16 MiB, MultiPV 1, seed 20261117, eight random opening plies, a 300-ply maximum and `go softnodes 2000` with 8000 hard cap. All seven pins and all captured timed rows matched Job 8. The sum used **8613 raw counter lines**, one per bestmove, including 8612 timed searches and one untimed warm-up. The 42 terminal searches each reported six zero counters. [Counting patch](sol3/job9/partA/count_paths.patch.txt) · [Exact run and build hash](sol3/job9/partA/run.meta) · [Summing program](sol3/job9/partA/sum_paths.py) · [Per-search counts](sol3/job9/partA/per_search.tsv) · [First-row comparison](sol3/job9/partA/first_difference.json)

| Outcome | k11v counted | Share of all 15228637 evaluations | Carbon2 Job 15 share on its own workload |
| --- | ---: | ---: | ---: |
| Already valid | 534555 | 3.51% | 3.48% |
| Same-square update | 8169364 | 53.64% | Within 59.55% combined |
| Same-bucket update | 903756 | 5.93% | Within 59.55% combined |
| Fused refresh and update | 2877856 | 18.90% | 18.14% of all evaluations in the corresponding old case |
| Remaining `make_valid` | 2743106 | 18.01% | Within 36.97% old `make_valid` including that old case |

The timed workload alone recorded 15227146 evaluations and 2046010 literal `refresh_from_pieces` calls, or 1768.13 evaluations and 237.58 calls per timed search. Opus quoted sol2’s corresponding r15d rates of 1768 evaluations and 571.74 refreshes per search on this workload. The AVX-512 fused path does its own refresh inline. The literal function call count excludes those inline refreshes. [Complete totals](sol3/job9/partA/totals.json) · [Earlier figures in the handoff](https://github.com/couns0538-sketch/dwqww/blob/157b1d5a0a89c9c9548a1823fb4e75e1585a39ce/forge-combo29/soak_all/FABLE_TO_sol3_9.md)

| Timed k11v counting build | Searches | Last-iteration nodes | Legacy trace | Terminal | Final sum | At 8000 | Final trace |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| Observed | 8612 | 29333343 | `5c705841c3ea17b4` | 42 | 35918624 | 971 | `5356dbb3a5f1bee3` |

### Part B position parser

The four runs replayed the same **17257 position commands**, fixture seed 2026111809 and SHA-256 `9f2b4826ddc5f4d53f310a1c778d66c970e905fe88747d9900df05618833309c`. The stream has two forms of each of the 8612 timed warm positions and 33 targeted commands. It exercises 60 growing startpos sequences and the equivalent growing suffixes from black-to-move FEN roots, forks, take-backs of 1, 2 and 10 plies, an illegal move and its continuation, FEN rights and clocks, long repetitions, castling, en passant, and promotion to all four pieces. The seeded interleavings include searches, Hash changes and new games. [Coverage and inputs](sol3/job9/partB/stream_coverage.json) · [Generator](sol3/job9/partB/make_stream.py) · [Runner](sol3/job9/partB/uci_stream.py)

All runs used PC20 and net768 with Threads 1, Hash 16 MiB and MultiPV 1. Each position received `go perft 1`, `eval` and `isready`. The injected searches used depth 4 or 2000 hard nodes and waited for `bestmove`. Reset mode also sent `ucinewgame` and waited for `isready` before each position command. That clears the stored move prefix. The comparison excludes startup and synthetic reset barriers, and strips only time, nps and hashfull numeric fields from search info. Across all four runs, the 406478 position-diagnostic and original readiness lines were byte-identical, SHA-256 `a722fc91f154a0862e80b18ed834ac92bc1396313bac22b3c1739f3e5976ed01`. The six injected searches yielded 36 normalized lines per run, byte-identical within each mode. The combined hashes below retain the search lines in their original order. [All four position comparisons](sol3/job9/partB/all_four_common.json) · [Cached searches](sol3/job9/partB/cached_search.json) · [Reset searches](sol3/job9/partB/reset_search.json)

| Build | Mode | Raw stdout lines | Combined normalized lines | Combined normalized SHA-256 |
| --- | --- | ---: | ---: | --- |
| [r15d](sol3/job9/partB/r15d_cached/summary.json) | Cached | 406614 | 406514 | `d79543edb1749cdec2cc529e25efc706ef9cc7cebbece9c465589b166e903bfb` |
| [k11v](sol3/job9/partB/k11v_cached/summary.json) | Cached | 406614 | 406514 | `d79543edb1749cdec2cc529e25efc706ef9cc7cebbece9c465589b166e903bfb` |
| [r15d](sol3/job9/partB/r15d_reset/summary.json) | Reset | 423871 | 406514 | `51224121217805f1c2d938d759ab57117d3fdfbd57a220b8a1f5cf2cadf61a05` |
| [k11v](sol3/job9/partB/k11v_reset/summary.json) | Reset | 423871 | 406514 | `51224121217805f1c2d938d759ab57117d3fdfbd57a220b8a1f5cf2cadf61a05` |

The planted build accepts any same-length move text under the same root at the prefix test in `src/uci.cpp:119`. Its reset run matched unplanted k11v in both comparisons. In cached mode, the first difference was at the `eval` after position command 2, `position startpos moves e2e4 e7e5 g1h3`, immediately after the `g1f3` fork. The first 62 common lines matched. At common line 63, reset returned `info string eval hce 0 nnue 322 total 322` (raw line 165), and cached returned `info string eval hce 0 nnue 127 total 127` (raw line 163). The perft lines in that block still matched. The cached prefix consumed the entire requested move list and kept the preceding fork’s board. [One-line patch](sol3/job9/partB/cache_control.patch.txt) · [Raw-line provenance and fixture command](sol3/job9/partB/first_control_difference.json) · [Reset control comparison](sol3/job9/partB/control_reset_common.json)

## Facts

- Both new binaries used CMake Release, GCC 14.2.0, Debian libstdc++ from GCC 14.2.0-19 and `-march=x86-64-v4`. The counting executable SHA-256 is `9d239792ded56d652c4d0c7c4a9848eec165a5ab713d05a125c3844db13e505f`. The prefix-control executable SHA-256 is `3463f98679c930907f6d3479bd57a6fa17793d905aa8806e91a6044b08347bd2`. [Counting build](sol3/job9/partA/build.txt) · [Control build](sol3/job9/partB/control_build.txt)
- I reset counters before the main search and emitted them once on its return. The first five fields are disjoint v3 evaluation outcomes. The last field counts literal `refresh_from_pieces` calls, including calls with no changed columns. [Patch](sol3/job9/partA/count_paths.patch.txt) · [Raw counted UCI](sol3/job9/partA/observed.engine.stdout.txt)
- Independent fixture validation reproduced the final FEN for each startpos/FEN pair and the legal prefixes of the crafted cases. I compared the parser against both another build and a reset run of the same build. [Fixture validation](sol3/job9/partB/stream_coverage.json) · [Exact commands](sol3/job9/partB/k11v_reset/commands.txt)

## Suspicions

The older literal refresh rate is consistent with the fused path absorbing roughly one function call when it runs. The two Part B mode hashes differ where the injected searches can see different retained transposition history. The per-position diagnostics and the within-mode search checks passed.

## What I did not do

I ran no strength match or speed test. The checked-in files are evidence and reproducible diffs. The count and control source trees and build products stayed in the scratch workspace.

## What I am not sure about

More than one thread, a game clock, speed (no timing in this job), the PC's own net and compiler.

The parser check observes legal move lists, evaluation and six fixed searches on this stream. It samples what can be detected through those UCI outputs. [Clock and checkpoints](sol3/job9/stamps.txt)
