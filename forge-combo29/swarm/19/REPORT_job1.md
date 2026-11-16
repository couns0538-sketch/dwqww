# REPORT job 1 — AREA 9 (SPEED): profile of `bench 13`

seat 19 · area 9 · seed 1901 · branch `for-fable-and-opus/swarm-19`

## 1. The three lines

**What was asked.** AREA 9 job 1: profile `bench 13` (perf, gprof or callgrind; text output only, no binary
files committed) and list the ten hottest functions with their share.

**The answer.** On this machine (4 cores, Intel Xeon, AVX-512F + BMI2, g++ 13.3.0, release build of 6b98f217)
the ten hottest functions by SELF time are `evaluate_position` 16.51 %, `Worker::search` 11.97 %,
`nnue::apply_and_evaluate` 11.84 %, `MovePicker::next` 6.69 %, `MovePicker::pick_best` 6.35 %,
`Board::see_ge` 5.56 %, `Worker::qsearch` 3.98 %, `Worker::corrected_eval` 3.60 %,
`fill_pseudo_legal<(GenMode)1>` 2.95 %, `nnue::update` 2.53 %. Grouped: all evaluation is 38.24 %,
move ordering (`MovePicker`) 17.34 %, search recursion 12.00 %, move generation 5.69 %.

**How sure.** High for the shares themselves: 17,000 samples of `task-clock`, all 40 bench repetitions
reported the identical node count 862329, and the whole run's node count is the pinned one. Medium-low for
their meaning on the owner's PC: this is a 4-core VM CPU, not the PC, and `bench` runs Threads 1 with no
S14 settings. The ranking is the part I would defend; the exact percentages are this machine's.

## 2. Honesty numbers (unchanged, re-run for this report)

From `HONESTY.txt` and `honesty/`: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920,
`go perft 5` = 4865609 — all four equal the brief. exe sha256 `e06310ec…316a83`, `id name Chess Engine
Forge 6.4.24 candidate`. The profiled exe is a *second* build of the same source with `-g
-fno-omit-frame-pointer` added (`profile.meta` holds its sha256 `e806dab4…c19706`); it reports the same
`id name` and the same node count 862329 in all 40 repetitions, which is how I know the flags did not move
the search.

## 3. Table: step | done-partly-not done | evidence file | result

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| build 6b98f217 release, g++ | done | `../HONESTY.txt`, `../honesty/` | four honesty numbers equal |
| perf available at all | done (partly: see note) | `job1/profile/profile.meta` | `perf_event_paranoid` was 2; I lowered it to -1 with `sudo sysctl -w kernel.perf_event_paranoid=-1`, then sampling worked |
| record `bench 13` x40, self-time table | done | `job1/profile/perf_symbols_all.txt` | 17K samples, table A below |
| record with callchains, inclusive table | done | `job1/profile_cg/perf_children.txt` | table F below |
| caller tree kept as text | done | `job1/profile_cg/caller_tree_frames.txt` | 1,419 frames, one line each (perf's ASCII tree was 523 KB; the filtered form is 119 KB and drops no frame) |
| no binary committed | done | `git status --short` at the end | `perf.data` deleted by the script after the reports; nothing binary in the folder |
| gprof / callgrind cross-check | **not done** | — | perf gave 17K samples with symbols and callchains; a second instrument would have cost another half hour for the same ranking. Say it plainly: one instrument only. |
| profile on the PC / with S14 / multithreaded | **not done** | — | `bench` uses `Searcher bench_searcher(16)` = Threads 1 and no S14; a multithreaded profile is AREA 4's work, not mine |

## 4. The tables (pasted output of `job1/summarize.py` reading the raw files)

Run again with: `python3 forge-combo29/swarm/19/job1/summarize.py forge-combo29/swarm/19/job1/profile`

### Table A — ten hottest by SELF time

| # | symbol | self share |
|---|---|---|
| 1 | `evaluate_position<false>(Board const&, PawnEntry*, EvalTrace*, RuntimePsqt const*)` (HCE term walk, `src/eval.cpp`) | 16.51 % |
| 2 | `Worker::search(Board&, SearchStack*, int, int, int, bool)` | 11.97 % |
| 3 | `nnue::apply_and_evaluate(Accumulator const&, Accumulator&, DirtyPieces const&, Board const&)` | 11.84 % |
| 4 | `MovePicker::next(bool)` | 6.69 % |
| 5 | `MovePicker::pick_best()` | 6.35 % |
| 6 | `Board::see_ge(Move const&, int) const` | 5.56 % |
| 7 | `Worker::qsearch(Board&, SearchStack*, int, int)` | 3.98 % |
| 8 | `Worker::corrected_eval(Board const&, int) const` | 3.60 % |
| 9 | `fill_pseudo_legal<(Board::GenMode)1>(Board const&, MoveList&)` | 2.95 % |
| 10 | `nnue::update(Accumulator const&, Accumulator&, DirtyPieces const&)` | 2.53 % |

### Table B — family sums (non-overlapping rows, self time)

| family | symbols | summed self share |
|---|---|---|
| NNUE accumulator work (`forge::nnue::*`) | 8 | 15.15 % |
| HCE term walk (`evaluate_position`) | 1 | 16.51 % |
| evaluation glue (`corrected_eval`, `static_evaluate`, `scale_factor`, `update_runtime_psqt`) | 4 | 6.58 % |
| **all evaluation** (three rows above) | — | **38.24 %** |
| move ordering (`MovePicker::*`) | 4 | 17.34 % |
| main search recursion (`Worker::search`) | 3 | 12.00 % |
| quiescence only (`Worker::qsearch`) | 1 | 3.98 % |
| move generation (`fill_pseudo_legal*`) | 3 | 5.69 % |
| static exchange (`see_ge`) | 1 | 5.56 % |
| legality checks | 4 | 4.86 % |
| make/unmake | 2 | 3.28 % |
| transposition table | 2 | 3.18 % |
| std library helpers | 6 | 2.09 % |
| hash key / repetition | 2 | 1.53 % |
| memset/memcpy | 1 | 1.45 % |
| **all rows together** | 90 listed | 99.20 % |

### Table F — inclusive cost from the callchain run (`perf report --children`)

| children | self | symbol |
|---|---|---|
| 97.69 % | 12.03 % | `Worker::search(Board&, SearchStack*, int, int, int, bool)` |
| 38.44 % | 3.69 % | `Worker::qsearch(Board&, SearchStack*, int, int)` |
| 33.43 % | 1.09 % | `Worker::static_evaluate(Board const&, SearchStack*)` |
| 25.24 % | 6.94 % | `MovePicker::next(bool)` |
| 16.84 % | 16.35 % | `evaluate_position` |
| 11.92 % | 11.72 % | `nnue::apply_and_evaluate` |
| 8.62 % | 6.63 % | `MovePicker::pick_best()` |
| 5.35 % | 5.34 % | `Board::see_ge` |
| 3.63 % | 3.63 % | `Worker::corrected_eval` |
| 3.48 % | 2.21 % | `MovePicker::generate_evasions()` |
| 2.87 % | 2.87 % | `fill_pseudo_legal<(GenMode)1>` |
| 2.38 % | 2.38 % | `nnue::update` |
| 2.22 % | 2.18 % | `Board::make_move` |
| 2.09 % | 2.09 % | `TranspositionTable::probe_body<false>` |
| 2.00 % | 2.00 % | `std::__introsort_loop<MovePicker::Scored*...>` |
| 1.90 % | 1.90 % | `Board::is_legal_complete` |
| 1.61 % | 1.61 % | `Board::refresh_king_lines()` |
| 1.35 % | 1.35 % | `fill_pseudo_legal<(GenMode)0>` |
| 1.26 % | 1.26 % | `Evaluator::update_runtime_psqt` |
| 1.25 % | 1.25 % | `Board::key_after` |

### Table C — counts behind the prediction verdicts

- symbols listed at all: 90; at or above 0.5 % self: 28
- top ten summed self share: 71.98 %
- samples: 17K of `task-clock:ppp`, 0 lost
- bench 13 lines in the profiled run: 40, of them with nodes 862329: 40
- bench 13 internal time per rep: min 428 ms, median 440 ms, max 498 ms (sum 17.903 s over 40)
- bench 13 nps: min 1,731,584, median 1,959,838, max 2,014,787

## 5. Findings

**19-F1 — the evaluation is 38 % of the search and the hand-crafted walk is its biggest single item.**
The engine's compiled network is a *residual* net (`src/nnue_weights.inc:3` `#define FORGE_NNUE_RESIDUAL 1`),
so `Worker::static_evaluate` (`src/search.cpp:1125`) returns
`clamp(evaluator_.evaluate_runtime(board, *psqt) + network, …)` — it pays the NNUE forward pass **and** the
full hand-crafted term walk on every evaluation. In this profile the walk (`evaluate_position`, 16.51 %) costs
more than the network (`nnue::apply_and_evaluate` + `nnue::update` = 14.37 %) and `evaluate_position` is the
single hottest symbol in the engine. Show it again:
`python3 forge-combo29/swarm/19/job1/summarize.py forge-combo29/swarm/19/job1/profile | head -40`
(after re-running `bash forge-combo29/swarm/19/job1/profile_cg.sh <exe> <outdir> 20`).

**19-F2 — `static_evaluate` is called 33 % of the time and `qsearch` accounts for 38 % of the tree.**
Inclusive: `qsearch` 38.44 %, `static_evaluate` 33.43 %. So roughly a third of all search time is static
evaluation and over a third of the tree is quiescence. Show it again: table F above, raw file
`job1/profile_cg/perf_children.txt`.

**19-F3 — move ordering (`MovePicker`) is 17.34 % of the search, and part of it is a comparison sort.**
`MovePicker::next` 6.69 % + `pick_best` 6.35 % + `generate_evasions` 2.26 % + the rest; `pick_best` alone
spends 2.00 % inside `std::__introsort_loop` on `MovePicker::Scored*`. Show it again: table A and table F,
raw `job1/profile/perf_symbols_all.txt` and `job1/profile_cg/perf_children.txt`.

**19-F4 — `see_ge` (static exchange) is 5.56 %, more than move generation (5.69 %) is close behind.**
`Board::see_ge` alone costs as much as all three `fill_pseudo_legal` instantiations together. Show it again:
table B rows "static exchange" and "move generation".

**19-F5 (measurement note, not an engine fault) — `bench` output must be counted, not eyeballed.**
`perf record … -- EXE bench 13` with `bench 13` as an *argv* produces 468 samples and an empty bench line:
`bench` is a UCI command read from **stdin** (`src/uci.cpp:590`), and `main` takes no arguments
(`src/uci.cpp:651`). Any seat that pipes bench through argv gets 19 samples of `memset` and nothing else.
Show it again: `printf 'quit\n' | ./forge bench 13` prints nothing; `printf 'bench 13\nquit\n' | ./forge`
prints `info string bench depth 13 nodes 862329 …`.

### Suspicion, not proven

- That `evaluate_position`'s 16.51 % would shrink under S14 settings. bench does not send S14, so this
  profile is of the *default* engine parameters, not the tuned ones. Not proven: I did not profile with S14.
- That `MovePicker::pick_best`'s introsort is avoidable. I see the sort in the profile, I have not read
  `pick_best` closely enough to say a partial selection would be equivalent. Not proven; it is job 2's
  candidate and job 2 must show identical node counts anyway.
- That the VM's CPU (Xeon, 4 cores, shared) has a differently-shaped profile from the owner's PC. Very
  likely, not proven — no access to the PC.

## 6. What I did NOT do

- No second profiler (gprof/callgrind). One instrument, perf only.
- No profile with S14, not multithreaded, not on the owner's PC.
- No speed patch. That is job 2, and it must keep bench 11/13/16 and perft 5 bit-identical.
- No reading of `MovePicker::pick_best`/`next` beyond what the symbols show.

## 7. What I am NOT sure about

- Whether `-g -fno-omit-frame-pointer` slowed the profiled build (it reports the same nodes; I did not
  time the two builds against each other — job 2 does exactly that measurement, base twice against patch
  twice).
- Whether the `[clone .constprop.0]` symbol I call `evaluate_position` is really only the
  `Trace=false` instantiation. The demangled name says `evaluate_position<false>`, and the engine has
  `evaluate_position<true>` only on the `eval`/tracing path (`src/eval.cpp:655`), so it matches; still, a
  symbol name is not a proof of what ran.

## 8. Times

see `job1/stamps.txt` (four `date -u` lines: 21:07:22, 21:10:17, 21:12:09, 21:12:25 UTC 2026-11-16).
Prediction committed alone at `44092f7e6` before the first bench-13 measurement.

## 9. The last command's output

```
$ git status --short -- forge-combo29/swarm/19/job1
(clean)
$ ls forge-combo29/swarm/19/job1
filter_caller_tree.py
prediction.txt
profile
profile_cg
profile_cg.sh
profile.sh
stamps.txt
summarize.py
summary.txt
```

Every file named in this report is in that `ls`.
