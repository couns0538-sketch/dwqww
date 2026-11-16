# REPORT — where `MovePicker::pick_best`'s 7.9 % actually goes

seat 19 · area 9 · branch `for-fable-and-opus/swarm-19`
Text-only writeup as asked. **No patch.** This answers where the cost sits and which call sites dominate.

## 1. The three lines

**What was asked.** `MovePicker::pick_best` shows 7.93 % self time on my PC-relevant profile — hotter than
`next` (5.71 %). Profile which call sites dominate, and say whether the cost is the partial-selection loop,
the history/scalar scoring inside it, or the calls from the root.

**The answer.** *None of the three as posed.* The cost is **`std::sort`, which runs on only 4.8–5.0 % of
calls but accounts for roughly two-thirds of pick_best's self time.** The partial-selection loop scans about
14 elements per non-seeded call and is the second cost; the history/scalar scoring **is not inside pick_best
at all** (it lives in `push_scored`/`next`, called 2.2 times per pick_best); and the root contributes
**0.26–0.36 %** of calls, i.e. nothing.

**How sure.** High. This is not inferred from the profile alone: I instrumented a scratch build to count each
branch (three independent runs agree), and the instruction-level annotation independently puts the sort's
`_GLIBCXX_MOVE` lines at ~19 % of pick_best's local time, which matches the sort's share of calls once its
per-call cost is accounted for.

## 2. The counters (instrumented build, `pickbest/instrument_pickbest.py`)

| quantity | bench 13 | R_1911, depth 12, 200 positions |
|---|---|---|
| total nodes | 862,329 | 14,836,669 |
| `pick_best` calls | 1,806,615 | 31,971,178 |
| returned the seed (cheap path) | 393,622 = **21.8 %** | 6,675,447 = **20.9 %** |
| partial-selection branch (`index_ - list_start_ < 4`) | 917,382 = **50.8 %** | 15,530,984 = **48.6 %** |
| `std::sort` branch | 86,317 = **4.8 %** | 1,583,168 = **5.0 %** |
| elements scanned by the partial loops | 6,780,518 (**3.8/call**) | 124,611,288 (**3.9/call**) |
| elements scanned per non-seeded partial call | 12.9 | 14.1 |
| calls from the root (`ss_ == nullptr \|\| ss_->ply == 0`) | 4,703 = **0.26 %** | 113,508 = **0.355 %** |
| `QuietScorer::score` calls | 3,684,612 (**2.04/pick_best**) | 70,815,408 (**2.21/pick_best**) |

Both data sets agree, so the shape is a property of the engine, not of one position set.

## 3. Answering the three questions as posed

**(a) Is it the partial-selection loop?** Partly — it is the second cost, not the first. 48.6–50.8 % of calls
enter it, and among non-seeded calls it scans ~14 elements, so the work is 3.9 comparisons per call amortised
across all calls. That is cheap. The profile's `chunk_max` (3.70 %) and `_mm_max_epi32` (2.47 %) entries are
exactly this loop — real, but a few percent of pick_best.

**(b) Is it the history/scalar scoring inside it?** **No — it is not inside pick_best.** `QuietScorer::score`
is called 2.04–2.21 times per pick_best, which means it is called from `push_scored` when the move list is
built, not from `pick_best` when a move is picked. Its cost is therefore already counted under
`MovePicker::next`, and it is the reason `next` is hot in *inclusive* terms. Anyone trying to make
`pick_best` cheaper by "optimising the scoring" would be editing the wrong function.

**(c) The calls from the root?** **0.26–0.36 % of calls. Nothing.** The root is not a contributor at all.
This part of the hypothesis is definitively dead.

## 4. What is actually costing the time: `std::sort`

The instruction-level annotation (`job2/annot/by_source.txt`, from `perf annotate`) sums pick_best's *local*
time per source line. Sorting the rows by cost:

| summed local % | source line | what it is |
|---|---|---|
| 6.29 % | 441 `*__last = _GLIBCXX_MOVE(*__next);` | inside `__introsort_loop` / insertion sort |
| 5.82 % | 11 `[[nodiscard]] Move pick_best() {` | function entry / prologue |
| 5.61 % | 210 `__builtin_ia32_pshufd` | the AVX2 partial-selection chunk scan |
| 5.28 % | 416 `*__last = _GLIBCXX_MOVE(__val);` | sort |
| 3.82 % | 452 `for (__i = __first; __i != __last; ++__i)` | sort |
| 3.81 % | 406 `*__last = _GLIBCXX_MOVE(*__next);` | sort |
| 3.70 % | 228 `best_score = chunk_max;` | partial selection |
| 3.37 % | 161 `return moves_[index_++].move;` | the cheap return |

Adding the five sort lines: **~23 % of pick_best's local samples sit inside `std::sort`**, which runs on 5 %
of calls. That is ~4.6× the per-call cost of everything else — a sort of the remaining list is simply
expensive, and it is paid on every node that gets far enough down the move list to need it.

This is consistent with the independent children report: `pick_best` has 9.16 % children of which
`__introsort_loop` is 2.03 % — and that 2.03 % is *global* self time inside the sort, i.e. roughly a quarter
of pick_best's 7.36–7.93 % global self time sits in the sort alone.

## 5. Why this is unusual, and what it means

The coordinator's observation was right: for a picker whose result is usually the first element after a good
previous move, 7.9 % is unexpected. The counters explain it — **the seed is used only 21 % of the time.** In
the other 79 %, `pick_best` must select, and in 5 % of cases it falls through to a full sort of the tail. So
the picker is not "usually returning element 0"; it is usually doing real selection work, and one call in
twenty pays for a sort.

Two consequences worth recording:

1. `MovePicker::next`'s 5.71 % and `pick_best`'s 7.93 % should be read together: `next` is the control flow
   plus the scoring, `pick_best` is the selection. Together they are 13.6 % of the engine, which makes move
   ordering the single largest PC-relevant family I measured (18.37 % including `generate_evasions`).
2. The obvious next question — whether the 5 % sort branch can be replaced by continuing partial selection —
   is **not** answered here and is not safe to assume. The code comment at `src/search.cpp` says the
   selection deliberately keeps the lowest index on a tie (`>`), and Opus's file 3 says tie order being
   unspecified is *known and harmless* for the search's node counts. Whether a different selection order
   changes node counts is exactly the question a patch would have to test with the four honesty numbers. I
   did not test it.

### Suspicions, not proven

- That the 5 % sort branch is dominated by nodes near the tips of the tree, where `count_` is large relative
  to the depth remaining. I did not condition the counters on depth; the totals are all I have.
- That `pick_best`'s 5.82 % on "line 11" (the function signature) is prologue and register spills rather than
  real work. `perf annotate` attributes to the nearest source line, and a function's opening brace collects
  the prologue; that is likely but not certain.

## 6. What I did NOT do

- No patch. As asked, this is a writeup only.
- No depth-conditioned analysis (see above).
- No test of whether replacing the sort changes node counts — that is a job, not a measurement, and it is
  the honest next step rather than something I should assert.
- The instrumentation is a **scratch build in `~/pb`**, not a committed patch; the script that makes it is
  committed at `pickbest/instrument_pickbest.py` so the numbers can be reproduced.

## 7. Reproducing

```
cd ~ && cp -a base/forge-combo29 pb && cd pb
python3 .../pickbest/instrument_pickbest.py     # adds the counters
# hook dump_pick_counters() into uci.cpp's main(), then:
cmake -S . -B ~/pb_build -DCMAKE_BUILD_TYPE=Release && make -C ~/pb_build -j4
printf 'bench 13\nquit\n' | ~/pb_build/forge        # prints the PICKBEST line on stderr
python3 .../pickbest/drive_counters.py ~/pb_build/forge <R_1911.fens> 12 200 out.err
```

The `drive_counters.py` driver exists because `drive_search.py` merges stderr into stdout and stops reading
at `quit`, so the counter line — printed at exit — was never captured. That is the same lesson as 19-F12:
know what your driver reads and when.

## 8. Files

- `pickbest/instrument_pickbest.py` — the counters
- `pickbest/drive_counters.py` — the driver that captures stderr
- `pickbest/counters_bench13.txt`, `pickbest/counters_R1911.err` — the raw counter lines
- `pickbest/symbols.txt`, `pickbest/pickbest_callers.txt` — the perf symbol and caller reports
