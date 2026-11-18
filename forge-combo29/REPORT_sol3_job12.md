# sol3 — Job 12 fuller tables, resize and consolidated patch

**Step 0 passed.** The retained r15d, k11v, k13 and net768 SHA-256 values matched Job 11. Fresh k13 default pins were bench 11 = 312866, bench 13 = 862329 and startpos perft 5 = 4865609, with no options sent. [Identity readback](sol3/job12/stage0/input_hashes.txt) · [Exact commands](sol3/job12/stage0/commands.txt) · [Raw pin output](sol3/job12/stage0/stdout.txt)

**Prediction grade.** Both fixed-size pairs and the resize matched. The full-miss shares were 32.31% at Hash 1 and 6.76% at Hash 4, versus forecasts of about 36% and 7%. C1 changed timed row 1 at game 0, ply 8 as forecast. The quiet-history cleanup was predicted. I missed the unused Board accessor and test friend. The forecast TT wrapper, `format_score` and possible NNUE helper deletions were absent. All actual hunks were unused-code deletions or indentation. kF matched every warm signature and all four cold cells as forecast. The immutable prediction was published at `66f5d93cd39180539546a438367c1dc9363df404`. [Prediction](sol3/job12/prediction.txt) · [Checkpoints](sol3/job12/stamps.txt)

### Part A1 fixed Hash sizes

The saved k11v and k13 builds used PC20, Threads 1, MultiPV 1, net768, 60 games with seed 20261117, eight opening plies and a 300-ply maximum. Each search sent `go softnodes 2000` with a hard cap of 8000. The fixed-size driver sent a single Hash option at setup. k13 matched k11v across every recorded field at each same size. [Hash 1 setup](sol3/job12/partA/A1/Hash1/k13/setup_check.txt) · [Hash 1 trace readback](sol3/job12/partA/A1/Hash1/k13/readback.json) · [Hash 4 setup](sol3/job12/partA/A1/Hash4/k13/setup_check.txt) · [Hash 4 trace readback](sol3/job12/partA/A1/Hash4/k13/readback.json)

| Pair | Searches | Last-iteration nodes | Legacy trace | Terminal | Final sum | At 8000 | Final trace |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| Hash 1 | 8764 | 29439169 | `b72fa7fe0a709ef7` | 47 | 37480119 | 1173 | `66f89334379e4a59` |
| Hash 4 | 8878 | 30296581 | `519a22169c4a8568` | 46 | 37370982 | 1044 | `66aa075b8b9cec12` |

### Part A2 counted TT coverage

I reused the exact Job 11 k13 counting executable. Hash 1 matched the uninstrumented Hash 1 trace and seven pins. I also replayed the counting build at Hash 4 to measure that prediction. It matched the uninstrumented Hash 4 trace and seven pins. Each sum includes the untimed warm-up. [Counting diff](sol3/job11/partA/count_tt_paths.patch.txt) · [Summing command](sol3/job12/partA/sum_counts.py) · [Hash 1 readback](sol3/job12/partA/A2/Hash1/totals.json) · [Hash 4 readback](sol3/job12/partA/A2/Hash4/totals.json)

| Quantity | Hash 1 | Hash 4 |
| --- | ---: | ---: |
| Counter lines | 8765 | 8879 |
| Owned probes | 36709153 | 36659274 |
| Hits | 19109233 | 18835392 |
| Misses with empty slot | 5739820 | 15345088 |
| Full-cluster misses | 11860100 (32.31%) | 2478794 (6.76%) |
| Owned stores | 16923886 | 16857777 |
| Matched destinations | 6277158 | 6048015 |
| Empty supplied destinations | 3797679 | 9528935 |
| Unmatched occupied destinations | 6849049 | 1280827 |
| Unmatched stores on full-probe proposals | 6848708 | 1280663 |
| Matched re-finds with a relocated slot | 0 | 0 |
| Helper returned slot 0 | 3276275 | 742500 |
| Helper returned slot 1 | 3089481 | 660182 |
| Helper returned slot 2 | 2905866 | 610906 |
| Helper returned slot 3 | 2588478 | 465206 |

The first full-cluster helper call was game 0, ply 12 at Hash 1 and game 0, ply 15 at Hash 4. The totals distinguish selection of an occupied destination at store time from the earlier full-miss proposal.

### Part A3 resize before game 30

k11v and k13 began at Hash 16 for games indexed 0 through 29. Before game 30 each sent `setoption name Hash value 4` and `isready`, then waited for `readyok` and entered the original new-game sequence. The traces agreed on every recorded field for all 8809 timed searches. [Driver diff](sol3/job12/partA/A3/driver_resize.diff) · [k11v receipt](sol3/job12/partA/A3/k11v/resize_check.txt) · [k13 receipt](sol3/job12/partA/A3/k13/resize_check.txt) · [Paired trace readback](sol3/job12/partA/A3/k13/readback.json)

| Pair | Searches | Last-iteration nodes | Legacy trace | Terminal | Final sum | At 8000 | Final trace |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| Hash 16 to 4 | 8809 | 30015878 | `6a05736004e3736f` | 43 | 37127904 | 1048 | `8575b9cf2f3994d1` |

The resize segments independently matched all 4306 constant-Hash-16 rows through game 29 and all 4503 constant-Hash-4 rows from game 30 for each build, including last-info fields after excluding time, nps and hashfull. [Partition readback](sol3/job12/partA/A3/partition_readback.txt)

### Part A4 planted owned hit mask at Hash 1

I used the existing Job 10 C1 executable, whose one-line AVX-512 probe shift is `<< 2U` instead of `<< 3U`. The legacy hash changed from `b72fa7fe0a709ef7` to `30f45873fc46d7b4`. The warm-up already differed at opening index 0, ply 8. Timed row 1 at the same game and ply repeated the difference. k13 reported 2864 nodes with score cp -222, while C1 reported 3037 nodes with score cp -125. Both returned `b3b4`. [C1 patch](sol3/job10/step3/C1.patch.txt) · [Hash 1 setup](sol3/job12/partA/A4/setup_check.txt) · [First timed difference](sol3/job12/partA/A4/gate.txt) · [Warm-up lines](sol3/job12/partA/A4/control_warmup.txt)

### Part B1 consolidated patch and r15d base

The minute-45 check found the file on Carbon2's branch. The path history and a byte comparison identify `2674c6bf09a55c70d02a23cc85fe07229dca8cce` as the patch's source commit. Its SHA-256 is `3d2ce085a8b76478942d4e29d7a74512eb3ecd2d328d224e27f711a48e46cb30`. I checked the pinned 29-file list from the Carbon2 handoff against the plain r15d tree. Then I applied the patch to a fresh copy with `patch -p1 -F0`. [Poll records](sol3/job12/B1/partB_poll.txt) · [Commit and blob](sol3/job12/B1/source_commit.txt) · [Patch digest](sol3/job12/B1/patch.sha256.txt) · [Pinned r15d list](sol3/job12/B1/r15d.expected.sha256)

```text
CMakeLists.txt: OK
include/forge/b4.hpp: OK
include/forge/bitboard.hpp: OK
include/forge/board.hpp: OK
include/forge/book.hpp: OK
include/forge/clock_plan.hpp: OK
include/forge/eval.hpp: OK
include/forge/eval_params.hpp: OK
include/forge/nnue.hpp: OK
include/forge/nnue_v3.hpp: OK
include/forge/search.hpp: OK
include/forge/tm_finish.hpp: OK
include/forge/tm_node_share.hpp: OK
include/forge/uci.hpp: OK
include/forge/uci_clock.hpp: OK
include/forge/uci_output.hpp: OK
src/bitboard.cpp: OK
src/board.cpp: OK
src/book.cpp: OK
src/book_data.inc: OK
src/eval.cpp: OK
src/eval_params.cpp: OK
src/eval_params_table.inc: OK
src/nnue.cpp: OK
src/nnue_v3.cpp: OK
src/nnue_weights.inc: OK
src/polyglot_keys.inc: OK
src/search.cpp: OK
src/uci.cpp: OK
```

```text
patching file include/forge/b4.hpp
patching file include/forge/board.hpp
patching file include/forge/eval.hpp
patching file include/forge/nnue_v3.hpp
patching file include/forge/search.hpp
patching file src/board.cpp
patching file src/nnue_v3.cpp
patching file src/search.cpp
patching file src/uci.cpp
```

### Part B2 literal k13 to kF comparison

The recursive comparison found ten hunks across three files. The k13 hunk start lines below identify each one. The live cached gives-check accessor and its consumer still appear in kF. `src/board.cpp`, `CMakeLists.txt` and the halfmove-only `may_repeat` definition are byte-identical. The parity-prefix storage and repetition scan from piece 14 are absent. [Literal diff](sol3/job12/B2/literal_diff.txt) · [Whitespace-insensitive diff](sol3/job12/B2/ignore_space_diff.txt) · [Classification](sol3/job12/B2/classification.txt)

| File | k13 hunk start | Change |
| --- | ---: | --- |
| `src/search.cpp` | 903 | Remove unused quiet-history score assignment |
| `src/search.cpp` | 960 | Remove two unused quiet-history accessors |
| `src/search.cpp` | 1016 | Remove MovePicker quiet-history score and epoch members |
| `src/search.cpp` | 1351 | Remove epoch snapshot from quiet generation |
| `src/search.cpp` | 2543 | Reindent the eval-swing history update |
| `src/search.cpp` | 2611 | Reindent the null-move child search |
| `src/search.cpp` | 2999 | Reindent the PV quiet-history bonus |
| `include/forge/board.hpp` | 221 | Remove uncalled `cached_king_lines` accessor |
| `include/forge/search.hpp` | 218 | Remove unreferenced `S13TTTestAccess` friend declaration |
| `include/forge/search.hpp` | 627 | Remove the Worker quiet-history epoch field |

### Part B3 kF build, warm and hard-node runs

kF built in CMake Release with GCC 14.2.0, Debian libstdc++ from GCC 14.2.0-19 and `-march=x86-64-v4` using the k13 flags. The kF SHA-256 is `340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea`. I verified all five pins against k13. [Build](sol3/job12/B3/pins/build_F.txt) · [Hashes](sol3/job12/B3/pins/input_hashes.txt) · [Pins and commands](sol3/job12/B3/pins/pins.txt)

| Build | Default bench 11 | Default bench 13 | Default perft 5 | PC20 net768 bench 11 | PC20 net768 bench 13 |
| --- | ---: | ---: | ---: | ---: | ---: |
| k13 | 312866 | 862329 | 4865609 | 882074 | 4275906 |
| kF | 312866 | 862329 | 4865609 | 882074 | 4275906 |

The unchanged Job 6 driver ran the same PC20 net768 60-game workload and seed as Part A at Hash 16. All 8612 compared rows and all seven signatures matched k13. [Run command](sol3/job12/B3/warm/run.meta) · [Warm readback](sol3/job12/B3/warm/readback.json)

| Builds | Searches | Last-iteration nodes | Legacy trace | Terminal | Final sum | At 8000 | Final trace |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| k13 and kF at Hash 16 | 8612 | 29333343 | `5c705841c3ea17b4` | 42 | 35918624 | 971 | `5356dbb3a5f1bee3` |

kFf combines kF with the exact Job 5 final-node probe. The hunk applied with a reported 123-line offset and no fuzz. kFf SHA-256 is `3b3915ee55dfc7dcc6211c7cf834d21a3a705a634d0b26bd92714b30bbffab00`. The cold cells reused all 389 Job 7 FENs per run, PC20, Threads 1, Hash 16 MiB, MultiPV 1 and the same per-position resets. B2 uses embedded AL1 s198 and N2 uses net768. The readback compares final nodes, bestmove and last-iteration score against the saved k11f output. [Probe patch application](sol3/job12/B3/cold/patch_apply.txt) · [Build and input hashes](sol3/job12/B3/cold/build_and_helper.sha256.txt) · [Independent checker](sol3/job12/B3/cold/check_cold.py)

| Node limit | Cell | k11f/kFf rows equal | k11f at limit | kFf at limit | Above limit |
| ---: | --- | ---: | ---: | ---: | ---: |
| 50000 | [B2](sol3/job12/B3/cold/50000/B2/gate.txt) | 389/389 | 389 | 389 | 0 |
| 50000 | [N2](sol3/job12/B3/cold/50000/N2/gate.txt) | 389/389 | 389 | 389 | 0 |
| 250000 | [B2](sol3/job12/B3/cold/250000/B2/gate.txt) | 389/389 | 388 | 388 | 0 |
| 250000 | [N2](sol3/job12/B3/cold/250000/N2/gate.txt) | 389/389 | 389 | 389 | 0 |

In B2 at the 250000 limit, fixture row 165 again finished at depth 64 with 220357 nodes in both builds. Both returned `g1h1` with score `mate -4`. [Exact FEN and raw lines](sol3/job12/B3/cold/below_limit.txt)

## Facts

- The independent warm trace checks and the Job 11 counters established equal rows and one replacement-helper call per observed full-cluster probe at both smaller Hash sizes. The store categories record the selected destination before the admission check. [Hash 1 raw counters](sol3/job12/partA/A2/Hash1/counters.tsv) · [Hash 4 raw counters](sol3/job12/partA/A2/Hash4/counters.tsv)
- The final stack still contains the single-thread AVX-512 TT code from k13. The k13-to-kF recursive source comparison found only the production-unused removals and three indentation edits. The test friend is unreferenced within the compared tree. [Literal source diff](sol3/job12/B2/literal_diff.txt)
- The Part B file was identified from the minute-45 fetch before opening it. B1 used a fresh copy of the independently pinned r15d sources. [Polling and pinned patch receipt](sol3/job12/B1/source_commit.txt)

## Suspicions

The difference in full-miss rates is consistent with smaller tables developing full clusters sooner. Match of the independent constant-size traces on either side of the resize supports the interpretation that the new allocation was effective before game 30.

## What I did not do

I ran no timing test or strength match. Hash 2 and Hash 8 were reserved for the missing-file contingency. The patch and probe were applied in scratch trees.

## What I am not sure about

More than one thread, a game clock, speed (no timing in this job), the PC's own net and compiler (clang on Windows), Hash sizes other than the ones you ran.

The comparison covers the record fields and positions in the stated fixtures and the exact resize boundary used here. [Complete checkpoint record](sol3/job12/stamps.txt)
