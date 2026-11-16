# REPORT_kimi5_job1 (kimi5, 2026-11-16 UTC) — job 1: the clock from the inside

1. Predicted largest overshoot: **0 ms past T** and at most ~1.5 ms (Threads 1) / ~2.2 ms
   (Threads 4) past the hard limit (B1_PREDICTION.md, written before measuring). Measured:
   **0 of 720 clocked searches exceeded T** (largest elapsed anywhere 18.00 ms on
   `go wtime 100 btime 100 winc 0 binc 0`, Threads 1, = 18 % of T), and no search even
   REACHED its hard limit (closest: 18.00 ms vs hard 20 ms, same line).
2. None found, because `clock_plan.hpp:46` clamps `hard <= available = time - Move Overhead`
   (clock_plan.hpp:34), and the worst tail after the hard stop (1024-node look cadence,
   search.cpp:1419/1561 + millisecond truncation + helper join) is bounded at ~2 ms, far
   inside the 10 ms default reserve.
3. **No patch is committed — none is needed** (proof below), so there is nothing to test at
   fixed nodes. Per the job's own branch rule, Part C is instead the three weakest points of
   the time ALLOCATION, as text only (section "Part C").

## 2. Step 0 (fresh engine process per line; Release, g++ 13.3.0, avx512f+bmi2 present so no portable flags)
- bench 11 -> nodes 312866 (tests_kimi5_job1/step0_bench11.txt)
- bench 13 -> nodes 862329 (tests_kimi5_job1/step0_bench13.txt)
- bench 16 -> nodes 3024920 (tests_kimi5_job1/step0_bench16.txt; 1440 ms -> 2.10 Mnps)
- go perft 5 -> nodes 4865609 (tests_kimi5_job1/step0_perft5.txt)
All four exact.

## 3. Table

| step | done? | evidence file | result |
|---|---|---|---|
| Step 0 pins | done | step0_*.txt | all four exact |
| Colleagues read | done | (their branches) | deepseek5 notes+job1 read; glmflash5-work absent |
| A: TIME_MODEL.md | done | tests_kimi5_job1/TIME_MODEL.md | A1-A6, every point with file:line |
| A2: Tm options | done | tests_kimi5_job1/uci_options.txt | 2 checks + 10 spins, defaults match source |
| B1: prediction before measuring | done | tests_kimi5_job1/B1_PREDICTION.md | 0 over T; <=1.5/2.2 ms past hard |
| B2(i): 300 UHO x T=20/50/100 x Threads 1,4 | done | k5_b2_uho300.out/.json, _input.log | 0/600 over T; max 18.00 ms; illegal 0 |
| B2(ii): 20 chosen worst x same | done | k5_b2_worst20.out/.json, k5_worst20.csv/.fens | 0/120 over T; max 12.36 ms; illegal 0 |
| B2 control 1: depth-1 floor | done | k5_b2_uho300.out (control1) | median 0.21 ms, max 0.76 ms |
| B2 control 2: planted 30 ms hold | done | k5_b2_ctrl2.out/.json | T=20: 300/300 over at Threads 1 AND 4 |
| B3: compare B1/deepseek5 | done | below | agreement; reserve hypothesis confirmed |
| Extra: movetime 50 at overhead 10 vs 0 | done | k5_overhead_probe.json, _input.log | median 40.45 vs 50.46 ms — reserve = overhead exactly |
| C: repair patch | not applicable | — | nothing can exceed T at default overhead (proof) |
| C: three weakest allocation points | done | below | text only, each with patch + measurement |

## 4. Findings (each: file:line + the command that shows it again)

F1. **The clock plan can never reach T.** include/forge/clock_plan.hpp:34,46: `available =
time - overhead`, `hard = max(1, min(hard, available))`. With overhead 10 every hard limit is
<= T-10. Show: `sed -n 26,50p forge-combo29/include/forge/clock_plan.hpp`, and the worked
examples in TIME_MODEL.md A1 (T=20 -> hard 5; T=100 -> hard 20; movetime 50 -> hard 40).

F2. **The search looks at the clock every <=1024 nodes, in qsearch too.**
src/search.cpp:1561 and 1419 (`(local_nodes_ & 1023U) == 0 && should_stop()`);
should_stop_with at 1265-1289; the hard test is `elapsed_ms() >= hard_limit_ms_` (1288);
only the main worker looks (1280). Show: `grep -n "1023U" forge-combo29/src/search.cpp`.

F3. **Helpers never see the clock; they add <= one 1024-node interval at the join.**
search.cpp:1280 (`if (!is_main()) return false;`), join at 2745-2749 after shared_.stop.
Measured: Threads 4 maxima (2.45/4.46/16.73 ms) sit ~0.5 ms above Threads 1 at T=20/50 —
the predicted join tail, still tiny.

F4. **The budget starts when the `go` line is read, not when the search starts.**
src/uci.cpp:192 (`command_start`), 520-522 (start_time stamped for finite clocked searches),
search.cpp:2143-2147. Book probe and thread spawn are inside the budget — they can only make
the engine stop EARLIER, never later.

F5. **On a clock stop the UNFINISHED iteration's root move can be played** — only if it
already raised alpha (search.cpp:2439-2452); on a node stop never (stopped_by_nodes_). This
is a strength-relevant detail, not a safety hole: the move is still legal and bounded in time.

F6. **`time <= Move Overhead` is a separate safe path** (clock_plan.hpp:32 reserve_empty;
search.cpp:2287-2320): legal hash move instantly, else 1 ply capped at 2000 nodes, helpers
off (2696-2700). Ponder waits suspend all clock stops (1282-1283, 1286-1287); after
ponderhit the budget counts from the hit (search.cpp:1244-1254, search.hpp:585-590).

F7. **The movetime reserve IS Move Overhead, exactly.** search.cpp:2191
`hard = max(1, movetime - overhead)`. Measured: `go movetime 50` median 40.45 ms at
overhead 10 vs 50.46 ms at overhead 0 (k5_overhead_probe.json; 60 searches each; the
setoption lines are in k5_overhead_probe_input.log). This also proves the options ARRIVE
end-to-end (a 10.0 ms behavioral shift per the option word).

F8. **deepseek5's outside numbers and mine agree** (same engine, same machine class):
T=20/50/100 maxima 2.07/3.60/17.90 ms (its REPORT_deepseek5_job1.md) vs my 1.89/4.13/18.00.
Its "never overstepped in 3,600 searches" now has the source-level cause (F1-F3).

Suspicions, not proven:
- S1. Under real match LOAD (two engines, 4 busy cores, OS jitter) the helper-join tail could
  exceed my idle-machine ~0.7 ms; the 10 ms reserve covers ~14x that, but it is not measured
  under load. fastchess games at timemargin 0 would show it.
- S2. The old claim "oversteps in a third of its games with no margin" matches NOTHING in
  this commit; the emergency/clamp code (F1, F6) reads like the fix for exactly that. I found
  no path that reproduces the old behavior with Move Overhead >= 3.

## 5. From my colleagues
Read: for-fable-and-opus/deepseek5-work tip 2414264d (NOTES_deepseek5.md, 2 entries;
REPORT_deepseek5_job1.md in full; its tests_deepseek5_job1/ds5_part_a.py and
ds5_delay_wrapper.py as design reference). for-fable-and-opus/glmflash5-work DOES NOT EXIST
(checked 03:57 UTC, `git ls-remote` empty) — nothing to read there.
Applied: the harness shape (one process per line, ucinewgame+isready per position, monotonic
pipe clock, python-chess legality, planted-fault control) — re-implemented as my own
k5_b2.py/k5_delay_wrapper.py; its T=20/50/100 maxima cross-checked against mine (F8).
Checked and CONFIRMED its open question: the ~9.5 ms movetime reserve tracks Move Overhead —
proven from source (search.cpp:2191) and by experiment (F7: 40.45 vs 50.46 ms).
I did NOT read any deepseek5 patch (its branch has none yet; and its job-2 repair is
off-limits until my result is pushed — mine is "no patch needed").

## 6. What I did NOT do
- No repair patch (Part C branch not taken: nothing exceeds T at default Move Overhead).
- No fastchess games (nothing to compare at fixed nodes; games belong to a patch job).
- TmFinishIteration / TmNodeShare not measured — that is glmflash5's job 2; I only modeled
  them from source (TIME_MODEL.md A2).
- No clock lines at Move Overhead other than default, except the movetime probe (F7).
- No Threads > 4, no MultiPV, no ponder measurements (modeled in TIME_MODEL.md A5 only).

## 7. What I am NOT sure about
- The worst-case tail under real concurrent load (S1).
- Whether MultiPV > 1 with a clock is exactly as bounded as modeled (alt lines clear their
  own clock, search.cpp:2490-2494, and stop through the parent's; I read but did not test).
- k5_b2_*.json artifact: on the `go depth 1` control line my script parses T as "1", so
  `over_T` there means "elapsed > 1 ms" (300 with the 30 ms wrapper, 0 without) — a labeling
  artifact of the control, not an engine result.

## 8. A better way
- The engine already reports its own `time` per info line; recording it beside wall elapsed
  (my k5_b2.py does) separates engine-side latency from pipe/harness latency for free —
  max engine_time 17 ms vs max wall 18.00 ms on the same line shows harness overhead ~1 ms.
  Any future clock harness should keep both columns.
- For overshoot-past-hard, inferring `hard` from the formula risks transcription drift: one
  LOCAL-only diagnostic build printing soft/hard as an info string per search would make the
  comparison exact (never committed; bench pins unchanged).
- Control 2 is dose-shaped, not binary: with the 30 ms hold, T=50 and T=100 correctly stayed
  at 0 over T (medians ~31-36 ms). Scaling the planted delay would map the harness's exact
  detection threshold — a stronger control than a single dose.

## 9. UTC stamps (recorded at the time; file mtimes from stat)
- 03:56:31 trigger; 03:56:43 step 1 check (job 1 found, unclaimed); 03:56:58 claim pushed.
- 03:57 colleagues fetched (glmflash5 absent); build BUILD_OK before 03:58:01.
- 03:58:01-03:58:03 step 0 (all four exact); 03:58:52 TIME_MODEL.md; 03:59:01 B1 prediction.
- 03:59:22 B2(i) 300 UHO done; 03:59:23 B2(ii) worst20 done; control 2 first attempt failed
  on wrapper permissions (rerun 04:02-04:03:51 OK); 04:04:07 overhead probe; 04:04:12 report
  writing starts.

## 10. Model
kimi5 — Kimi K3 (Moonshot AI), running as a Cursor cloud agent.

---

# Part C (branch: nothing can exceed the time) — proof, then the three weakest points

## Proof that no search can exceed T with Move Overhead at its default (10 ms)
1. clock_plan.hpp:32-46: either `time <= overhead` (reserve_empty -> bounded emergency path,
   F6) or `hard <= available = time - overhead`, i.e. hard <= T - 10.
2. search.cpp:1288 + 1419/1561: the main worker stops within one 1024-node interval of
   crossing hard; elapsed_ms() truncation adds < 1 ms; helpers add <= one more interval at
   the join (1280, 2745-2749). Total tail <= ~2.2 ms on this machine (B1).
3. Therefore elapsed <= T - 10 + 2.2 < T for every T >= 20 — and B2 measured 0/720 over T
   with a harness whose planted-fault control detects 300/300 when an overshoot exists
   (k5_b2_ctrl2.out). Movetime is the same shape with hard = M - 10 (search.cpp:2191, F7).

## The three weakest points of the time ALLOCATION (text only)

W1. **Small clocks are starved twice.** Overhead is subtracted BEFORE the divisor
(clock_plan.hpp:34,43), then `available/22` floors to soft = 1 ms at T <= ~230:
at T=20 and T=50 the engine plays from a 1 ms soft limit — median spend 1.1 ms while the
hard cap is 5 ms (my B2 medians). In bullet it plays nearly blind with 80 % of the usable
budget untouched. A patch would add a small-clock floor, e.g. in clock_plan.hpp:
`if (available < 220) soft = max(soft, available/8);` (still <= hard via line 48).
Measure: fastchess at 1+0.01 and 0.5+0.005 vs base (Elo with 95 % pairs interval), plus the
depth-at-bestmove distribution at T=20/50 from my k5_b2 harness.

W2. **The stability factor has cliff edges** (search.cpp:2564-2566): 0.60 / 0.80 / 1.40 at
6/3/0 stable iterations (and the 1.40 branch needs depth >= 6). One root-move flicker moves
the budget 1.75x; a stable run past 6 iterations suddenly drops 0.80 -> 0.60. A patch would
interpolate the factor linearly in stable_iterations between the bucket values (same
endpoints, no new constants). Measure: variance of per-move times over a fixed game set at
10+0.1 (should fall at equal strength), then a fastchess Elo check.

W3. **Every clock stop fires up to 1 ms late** because elapsed_ms() truncates to whole
milliseconds (search.cpp:1253, compared at 1288). At hard = 5 ms (T=20/50) that is 20 % of
the budget spent unseen, and the UCI `time` field under-reports by the same amount. A patch
would keep microseconds internally: elapsed in `duration_cast<microseconds>`, compared
against `hard_limit_ms_ * 1000` — three lines, no behavior change at large clocks. Measure:
my k5_b2 harness — max(elapsed - hard) at T=20/50 should drop by ~1 ms; bench pins must stay
exact (a bench has no clock), verified by the four step-0 numbers.
