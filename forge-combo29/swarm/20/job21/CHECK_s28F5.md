# seat 20 — check of seat 28's S-F5 (the increment is ignored below Move Overhead)

Verdict: **CONFIRMS the substance and CORRECTS the threshold.** The increment really is ignored at tiny clocks, but
the boundary is **13/14 ms, not 10/11 ms** — so `wtime 11 winc 1000` is still ignored, which seat 28's sentence says
it is not ("at `wtime 11 winc 1000` it jumps to 2048 nodes / depth 6").

Raw: `check_s28f5.json`. Script `check_s28f5.py`. Fresh process per search, `OwnBook false`, hardened driver.

## The measurements

| wtime | winc 0: nodes / depth | winc 1000: nodes / depth | verdict |
|---|---|---|---|
| 5 | 41 / 1 | 41 / 1 | **identical — increment ignored** |
| 10 | 41 / 1 | 41 / 1 | **identical** |
| 11 | 896 / 5 | 896 / 5 | **identical** (seat 28 says it jumps here — it does not) |
| 12 | 896 / 5 | 896 / 5 | identical |
| 13 | 896 / 5 | 896 / 5 | identical |
| **14** | 896 / 5 | **2450 / 6** | **differs — increment first used** |
| 16 | 896 / 5 | 5120 / 6 | differs |
| 20 | 896 / 5 | 6842 / 6 | differs |
| 30 | 896 / 5 | 17,458 / 10 | differs |
| 100 | 11,336 / 9 | 31,603 / 11 | differs |

All 18 answers are legal moves; none hangs; every one finished in 2–55 ms.

## The exact threshold
Sweeping 11..25: **11, 12, 13 ignore the increment; 14 is the first value that uses it.** So the boundary sits at
`time <= 13` with the default overhead (13 = overhead 10 + 3, which is consistent with `time - overhead <= 3` being
rounded up to the 1 ms floor: `available = time - overhead` = 1..3 ms, and `soft = max(1, available/divisor + ...)`
yields a 1 ms budget that cannot reach a deeper ply).

## The source, quoted (include/forge/clock_plan.hpp:25-32)
```
const std::int64_t overhead = overhead_ms > 0 ? overhead_ms : 0;
const std::int64_t time = time_ms > 0 ? time_ms : 0;
const std::int64_t increment = increment_ms > 0 ? increment_ms : 0;
if (time <= overhead) return ClockPlan{0, 0, true};
```
That early return explains the `wtime <= 10` cliff exactly. It does **not** by itself explain 11, 12 and 13 also
ignoring the increment — there the budget is 1–3 ms, and adding `increment * increment_percent / 100` should help.
So there is a second effect between 11 and 13 that the cited line does not cover, and I could not identify it from
this measurement alone. I state that rather than pretend the single line explains everything.

## Where my predictions went
1 **held for the substance** (`wtime 5`: identical) but my prediction 3 ("`wtime 10` behaves like 5, `wtime 11` does
not") was **killed**: 11, 12 and 13 also ignore it.
2 held (41 nodes, depth 1 at wtime 5 and 10).
4 held (all legal, no hangs).
5 held (the early return is there, quoted).

## What I did NOT do
- I did not find the mechanism for 11–13 ignoring the increment.
- I did not vary `Move Overhead` to test whether the boundary tracks it (my prediction would be that it does).
- I did not test `movestogo` together with an increment.

## What I am NOT sure about
- Whether 14 being the first value that uses the increment is an artefact of the 1 ms floor or of an interaction
  with `increment_percent`. Worth one more sweep with `Move Overhead 0`.

## Commands that show it again
```
python3 check_s28f5.py /agent/repos/build-base/forge /tmp/o
sed -n '25,33p' /agent/repos/base/forge-combo29/include/forge/clock_plan.hpp
```
