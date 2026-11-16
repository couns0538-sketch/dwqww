# PC speed profile — the engine the owner actually runs, under the settings it actually gets

seat 19 · area 9 · build **PC r15** · settings **PC20** · **Threads 1** · workload `bench 13` ×40 in one process.

## 1. Why this profile is the one that matters

Every profile I published before this point was of the **base tree**, or of the PC tree under the none regime.
File 2 Rule 2 says the evaluation families are not PC-relevant because the owner's PC loads its own net — true,
and still true here (this build keeps the built-in evaluation). But the *settings* were wrong too, and file 5
supplies them: **PC20 is what the owner's PC sends to every engine.** So this is the first profile of the PC
build under PC20, which is the closest any seat can get to the owner's real search.

Valid because `bench` is self-clearing (19-F23: `src/uci.cpp:617` calls `bench_searcher.clear()` before each of
its eight positions), so all 40 repetitions were cold. **All 40 reported 587,276 nodes**, which is PC20's known
bench-13 pin — so the run is not just cold, it is the pinned tree.

- samples: **26 K** `task-clock`
- refusal lines (`unknown option` / `invalid value` / `ERROR`): **0**

## 2. Table A — ten hottest symbols, PC r15 under PC20, Threads 1

| # | symbol | self |
|---|---|---|
| 1 | `evaluate_position<false>(...)` (the built-in HCE walk) | **14.96 %** |
| 2 | `Worker::search(Board&, SearchStack*, int, int, int, bool)` | 12.46 % |
| 3 | `nnue::apply_and_evaluate(...)` | 12.05 % |
| 4 | `MovePicker::next(bool)` | 6.71 % |
| 5 | `MovePicker::pick_best()` | 6.59 % |
| 6 | **`Worker::corrected_eval(Board const&, int, SearchStack const*)`** | **5.75 %** |
| 7 | `Board::see_ge(Move const&, int)` | 5.25 % |
| 8 | `Worker::qsearch(...)` | 3.89 % |
| 9 | `MovePicker::generate_evasions()` | 2.66 % |
| 10 | `std::__introsort_loop<MovePicker::Scored*...>` | ~2.4 % |

## 3. Table B — families

| family | self |
|---|---|
| move ordering (`MovePicker::*`) | **18.33 %** |
| all evaluation (NNUE + HCE walk + glue) | 36.53 % |
| quiescence | 3.89 % |
| search recursion | 12.61 % |
| static exchange (`see_ge`) | 5.25 % |
| move generation | 4.47 % |
| legality checks | 4.61 % |
| make/unmake | 3.21 % |
| transposition table | 2.68 % |
| memset | 2.03 % |
| hash key | 1.34 % |

## 4. What changed from the base tree, and why it matters

**`corrected_eval` nearly doubled: 2.95 % (base, none) → 5.75 %, and its signature changed** to
`corrected_eval(Board const&, int, SearchStack const*)`. That is `CorrHistV2 true` doing work that does not
exist in the base tree — a correction keyed by the last two moves, read and written on the evaluation path.
**It is now the sixth hottest symbol in the engine and the second hottest PC-relevant one behind the picker.**

This is the kind of thing a base-tree profile cannot show and a PC profile under the wrong settings cannot
show either: it appears only when the option the owner actually sends is switched on.

**Move ordering stays the largest single PC-relevant family at 18.33 %**, essentially unchanged from base
(17.34–18.37 %), so my earlier ordering findings keep their standing on the PC build.

**The transposition table is 2.68 %**, down from the warm 5.77 % I retracted — consistent with 19-F18's
retraction and with bench being cold: a cold table barely replaces.

**`std::__introsort_loop` is again in the top ten (~2.4 %)** — and 19-F26 showed that under PC20 the
`sorted`-branch tie order moves the owner's own pins by 5.7–14.7 %. So the sort is both expensive *and*
load-bearing, which is the worst combination for anyone tempted to "just make it faster".

### Suspicions, not proven

- That `corrected_eval`'s doubled cost is almost entirely `CorrHistV2`. I inferred it from the signature change
  and the option being on; I did not profile with `CorrHistV2 false` to isolate it. **That is the obvious next
  experiment** and it is cheap: two profiles, one option apart.
- That the 14.96 % for `evaluate_position` would vanish on the PC because of the owner's net. File 5 says the PC
  plays its own net, which is not shared; on that machine the search returns through `static_evaluate_v3`
  before the residual path. So this column is again "not PC-relevant" — same caveat as file 2 Rule 2.

## 5. What I did NOT do

- No ablation of `CorrHistV2` (see above). Named rather than guessed.
- No timing comparison, only shares. Per `METHOD_timing_tt.md`, a timing claim on this workload needs
  alternating paired runs and ±2.9 % resolution at 6 rounds; a profile does not give that.
- I did not profile under S14 alone, so I cannot separate PC20's six options from S14's fourteen.

## 6. Files

`pcspeed/profile_pc20.sh`, `pcspeed/prof20/{profile.meta, bench.stdout.txt, refusals.txt,
perf_symbols_all.txt, perf_children.txt, stream.txt}`, `pcspeed/summary20.txt`.
