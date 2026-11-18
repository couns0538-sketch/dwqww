# sol2 — Job 3 warm self-play profile and reset cost

## Step 0 — pinned r15d passed

The Job 2 GCC 14.2.0 r15d executable SHA-256 was `bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6`. The reconstructed `CMakeLists.txt` SHA-256 was `bfa17f8cb5f2f6358e88951f385fc67ddca279af06301b22945efdcc1ceaca5f`. Fresh processes reproduced **312,866** bench 11 nodes, **862,329** bench 13 nodes and **4,865,609** startpos perft 5 nodes with embedded AL1 s198, Threads 1, Hash 16 MiB, MultiPV 1 and OwnBook false. [Identity](sol2/job3/step0-identity.raw.txt) · [Raw pins](sol2/job3/step0-pins.raw.txt)

## Step 1 — warm self-play matched the known answer

The exact Carbon2 startpos driver (`c79b95bf45762fa9869d23140ed7f946cfaf0cb6bc4f74325a18d5f934bf1c45`) on the pinned r15d produced **8,612 searches, 29,333,343 last-info nodes, trace `5c705841c3ea17b4`**. All successful warm runs below reproduced that trace. The driver used 60 games, eight random startpos plies, seed `20261117`, a 300-ply cap, `go softnodes 2000` and one `ucinewgame` per game. This was PC20, Threads 1, Hash 16 MiB, synthetic net768 (`c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`, checksum `30ab43b4ba5db5f3`), on logical CPU 2 of the AMD EPYC 9V74 VM. [Commands](sol2/job3/step1-command.raw.txt) · [Raw workload result](sol2/job3/step1-workload.raw.txt)

## Prediction grade

The standalone prediction at `4d7d2cbf69e46b8053ca23e807b06ccdbe8d1067` overestimated the reset share at **0.15%** versus **0.115–0.120%** measured. Two of the three predicted functions appeared in the top three. `Worker::search` and `nnue::v3::apply_pair_and_evaluate` ranked first and third, while `MovePicker::next` ranked fourth. The predicted `Searcher::clear` was not the top verified memset site. TT cluster allocation, identified as `std::make_unique<forge::TTCluster[]>` in the inline return-site frame, led with **73** samples. [Prediction](sol2/job3/prediction.txt) · [Reset shares](sol2/job3/step2-warm/reset-shares.txt) · [Pooled caller table](sol2/job3/step3/pooled.all-callers.tsv.txt)

## Step 2 — one reset cost about 0.12% per game when amortized

One pinned r15d process loaded the Step 1 settings and net. Each block sent and waited for 1,000 `ucinewgame` + `isready` pairs and then 1,000 `isready`-only round trips. Subtracting the latter yielded **0.380 ms engine CPU per reset** in both blocks, at the 100-Hz process-stat tick resolution. Net wall time per reset was **0.399 ms** and **0.391 ms**, a **0.008 ms** spread. The three unprofiled warm runs took **19.762**, **19.033** and **19.466 s** of whole-engine CPU for the Step 1 trace. The six cross-combinations of reset and workload runs put the 60 game resets at **0.115–0.120%** of CPU, with a median of **0.117%**. This estimate uses whole-process CPU, including startup, the driver's opening generation and its first warm-up search. [Reset phase records and UCI transcript](sol2/job3/step2-reset) · [Workload times and shares](sol2/job3/step2-warm)

`ucinewgame` resets the root board and logical position cache at `src/uci.cpp:490–497` and calls `Searcher::clear()` at `src/search.cpp:3284–3287`. That clears the TT and the single worker. The board's key history returns to one key, and the cached move and FEN containers become logically empty. Their allocated capacity is separate from the fixed table footprint below. The TT's generation byte and epoch are scalar bookkeeping. The active v3 accumulator arrays stay allocated, with validity flags reset on the next search at `src/search.cpp:2918`. [Source excerpts](sol2/job3/step2-reset-source.raw.txt) · [Size calculations](sol2/job3/step2-tabulated-bytes.txt) · [Pinned-executable disassembly](sol2/job3/step2-reset-disassembly.raw.txt)

| Reset storage at Hash 16, Threads 1 | Object bytes | r15d source |
|---|---:|---|
| TT clusters | 16,777,216 | `src/search.cpp:458–459` |
| TT generation counters | 128 | `src/search.cpp:461` |
| Evaluator pawn cache | 1,310,720 | `src/search.cpp:1219`, `src/eval.cpp:567–571` |
| Main butterfly history | 16,384 | `src/search.cpp:1220` |
| Threat quiet history | 65,536 | `src/search.cpp:1221` |
| Pawn history | 0, compiled out | `src/search.cpp:1223–1225` |
| Capture history | 11,648 | `src/search.cpp:1226` |
| Continuation history | 1,384,448 | `src/search.cpp:1227` |
| Counter moves | 3,328 | `src/search.cpp:1228` |
| Pawn, material, white non-pawn, black non-pawn and joint correction histories | 131,072 each | `src/search.cpp:1229–1232,1235` |
| Rework quiet history | 65,536 | `src/search.cpp:1234` |
| Continuation correction | 6,656 | `src/search.cpp:1236` |
| Per-ply threat maps | 7,616 | `src/search.cpp:1237` |
| Search stack | 391,680 | `src/search.cpp:1238` |
| **Total table storage** | **20,696,256** | |

The pinned compiler touches **20,460,488 unique table bytes** after excluding unwritten evaluator and stack padding. This includes **18,976,128 bytes** in explicit bulk `memset` calls. Stack initialization restores some nonzero defaults. At 0.380 ms the unique table footprint corresponds to **53.8 GB/s**. Repeated warm, aligned bulk `memset` on the same core took **0.322 ms** for the explicit bulk total and **0.429–0.436 ms** for the full unique-byte total. Those controls bracket the engine's observed reset cost at the same order of magnitude. Their contiguous allocation, cache behavior and generated stores differ from the engine's table-by-table reset. [Raw calibration receipts](sol2/job3/step2-commands.raw.txt)

## Step 3 — warm profile and verified callers

The clean profiling build used the Job 2 GCC Release flags plus `-g -fno-omit-frame-pointer` and reported `id name Chess Engine Forge 6.4.24 candidate`. Its SHA-256 is `cba0bf8997b51422fd1e26ad13789d8d244a995adc1c03c88095459024c1743f`. The clean unprofiled gate, the profiled control and all three clean profiled passes reproduced the Step 1 trace. [Builds and profile commands](sol2/job3/step3/step3-command.raw.txt) · [Frame-pointer gate](sol2/job3/step3/frame-pointer-gate.stdout.txt)

The committed positive-control patch adds a fixed 13,000-iteration loop at `src/board.cpp:1431`, measured at **1.937 µs** per invocation in the standalone same-core calibration. The control moved `Board::see_ge` from **6th, 236 samples (4.93%)** in the first clean pass to **1st, 14,988 samples (73.31%)**. It passed the predeclared rank and share gate while preserving the exact warm trace. The fixed delay was used only as a sampling control. [Patch](sol2/job3/step3/see-spin.patch.txt) · [Calibration](sol2/job3/step3/spin-calibration.raw.txt) · [Control comparison](sol2/job3/step3/positive-control.raw.txt) · [Control search trace](sol2/job3/step3/control.stdout.txt)

The three clean passes collected **14,389** exclusive PC samples and reported **709** timer overruns. The sampler uses a per-thread CPU timer at a nominal **3,989 µs** period and records up to six frame-pointer callers. Caller attribution uses a supported ELF CFI rule and checked stack and executable addresses. Matching Debian glibc debug symbols resolve library instruction addresses. Aliased copy routines count as `memmove` only where the decoded return site confirms that call. Shares include process startup and shutdown, and use all exclusive samples as the denominator. A frame-pointer chain alone can omit a library frame or tail-call boundary. The sampler measures user instruction addresses and keeps whole-process system time within the charged timer clock. [Raw sample summaries and build identities](sol2/job3/step3) · [Sampler source](sol2/job3/step3/cpu_sampler.c.txt) · [Symbolization source](sol2/job3/step3/symbolize.py.txt)

| Rank | Function | Sampled source | Samples | Share |
|---:|---|---|---:|---:|
| 1 | `Worker::search` | `search.cpp:2381` | 2041 | 14.18% |
| 2 | `TranspositionTable::probe_body<false>` | `search.cpp:492` | 1193 | 8.29% |
| 3 | `nnue::v3::apply_pair_and_evaluate` | `nnue_v3.cpp:892` | 1169 | 8.12% |
| 4 | `MovePicker::next` | `search.cpp:752` | 898 | 6.24% |
| 5 | `nnue::v3::refresh_from_pieces` | `nnue_v3.cpp:956` | 890 | 6.19% |
| 6 | `Board::make_move` | `board.cpp:1225` | 623 | 4.33% |
| 7 | `Board::see_ge` | `board.cpp:1460` | 623 | 4.33% |
| 8 | `Worker::corrected_eval` | `search.cpp:1421` | 621 | 4.32% |
| 9 | `nnue::v3::apply_changes_pair` | `nnue_v3.cpp:857` | 621 | 4.32% |
| 10 | `MovePicker::pick_best` | `search.cpp:998` | 506 | 3.52% |
| 11 | `Worker::qsearch` | `search.cpp:1864` | 454 | 3.16% |
| 12 | `Worker::static_evaluate_v3` | `search.cpp:3405` | 451 | 3.13% |
| 13 | `nnue::v3::apply_changes` | `nnue_v3.cpp:843` | 306 | 2.13% |
| 14 | `fill_pseudo_legal<GenMode 1>` | `board.cpp:537` | 292 | 2.03% |
| 15 | `Worker::quiet_history` | `search.cpp:1615` | 244 | 1.70% |

| Subsystem | Samples | Share |
|---|---:|---:|
| Evaluation (NNUE v3) | 3922 | 27.26% |
| Search control | 2951 | 20.51% |
| Move ordering and picking | 2143 | 14.89% |
| Hash table | 1485 | 10.32% |
| Move generation and legality | 1416 | 9.84% |
| Board updates and position keys | 1007 | 7.00% |
| Static exchange evaluation | 480 | 3.34% |
| Other runtime and libraries | 470 | 3.27% |
| Draw and repetition checks | 434 | 3.02% |
| Other engine work | 60 | 0.42% |
| UCI and input/output | 14 | 0.10% |
| Unresolved | 7 | 0.05% |

| Callee | Verified caller at sampled return site | Modal line | Samples |
|---|---|---|---:|
| `memset` | `std::make_unique<forge::TTCluster[]>` | `unique_ptr.h:1092` | 73 |
| `memset` | `TranspositionTable::clear()` | `search.cpp:459` | 27 |
| `memset` | `Worker::clear()` | `search.cpp:1227` | 7 |
| `memmove` | `std::__copy_move_backward for MovePicker::Scored` | `stl_algobase.h:766` | 15 |
| `memmove` | `std::__copy_move for unsigned long` | `stl_algobase.h:452` | 1 |
| `nnue::v3::load` | `uci_loop(std::istream&)` | `uci.cpp:616` | 19 |

There were two verified `memmove` caller sites and one verified `nnue::v3::load` caller site. The profile also recorded **65** samples in shared memcpy/memmove implementations without a confirmed call target. That includes **63** in v3 replay at `include/forge/nnue_v3.hpp:274`. These samples are kept separate in the raw caller table. [Functions](sol2/job3/step3/pooled.top15.tsv.txt) · [Subsystems](sol2/job3/step3/pooled.groups.tsv.txt) · [Caller counts](sol2/job3/step3/pooled.all-callers.tsv.txt)

## Step 4 — reset-share gate

The measured **0.115–0.120%** share fell below the brief's **0.5%** threshold for the reset-reduction design. [Share calculation](sol2/job3/step2-warm/reset-shares.txt)

## Facts

- The frame-pointer build and SEE timing control preserved the warm replay's search trace. All profile results come from that verified workload.
- Warm self-play's `memset` samples include TT allocation, TT clears and worker clears. The measured per-game reset share remains small with the same provider, core, engine configuration and synthetic net.

## Suspicions

- Draw and repetition code accounts for 3.02% of the clean warm samples as a subsystem. A future investigation of same-position qsearch would need its own occurrence count and exact replay comparison to separate redundant work from required checks.
- The isolated kernel hot spots reflect the sampled GCC build and synthetic net. Source-level timing counters or the same warm profile on the PC would determine how much of that ranking transfers.

## What I did not do

Work took place in cloud scratch builds. The repository contains the text of the SEE control and its receipts. Owner-PC execution and reset reduction were outside the measured work.

## What I am not sure about

The derived reset footprint describes the pinned GCC executable, including padding decisions. Actual memory traffic, owner-PC memory bandwidth, and caller attribution for aliased or unsupported library frames remain uncertain.

GPT-6 (Codex), Case A. [Clock stamps](sol2/job3/stamps.txt) · [Publication status and file layout](sol2/job3/publication-layout.raw.txt)
