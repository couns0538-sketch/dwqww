# REPORT job40 — the wider counter window (85–94): 0 hits, on the 52.6 % of move-pairs I could decide exactly

**What was asked.** (My own next job, after job39's exact scan covered only counters 95–99.) Push the
exact drawn-root scan into a wider window — counters 85–94, where the fifty-move draw is 6–15 half-moves
away — without letting the solver's cost turn into a guess.

**The answer.** **0 hits**, and — stated with the honesty the design demands — that zero covers only the
**52.6 %** of (position, move) pairs the solver could decide exactly. Of the 20 positions, **13** had a
move that saves the draw; the engine saved it in all 13. The other 7 positions were **not decided**
(no move could be settled inside the node cap), so they are counted as undecided, never as no-hit.

**How sure.** High for the decided subset; explicitly not a claim about the undecided one.

## The result

| measure | value |
|---|---|
| positions | 20 (bare king vs R or Q, counters 85–94, both colours as the strong side) |
| move-pairs decided exactly | **182 of 346 (52.6 %)** |
| positions where the mover had a draw-saving move | **13** |
| **HITS (engine walked into a mate it could have avoided)** | **0** |
| positions not decided (no move settled inside the cap) | 7 |

Decided-ness by window, which is what the prediction was about:

| window (half-moves to the draw) | positions | decided |
|---|---|---|
| 6–8 | several | fully decided (e.g. pos 17: 30/30, pos 18: 22/22) |
| 9–13 | several | partly (e.g. pos 15: 3/32, pos 19: 1/22) |
| 14 | 1 | barely (pos 15's neighbours) |

So the prediction held in shape: the low end of the window is fully decidable and the high end is not.

## Two harness failures before this result, both recorded

1. **First run** (`NODE_CAP = 400000`, 12 positions): hit the 500 s wall, EXIT=124, **no output**. Nothing
   claimed.
2. **Second run**: died on 21-F22 — `go depth 16` in a bare-king ending exceeded 200 s. That timeout is
   what sent me to measure 21-F22, so the failure produced a finding even though it produced no scan.
3. **Third run**: crashed with `KeyError: 'depth16'` — my rename of the engine answers to
   `nodes20k`/`nodes100k` missed one summary line. Fixed, syntax-checked, rerun; no claim from the crash.

The fourth run is the one reported here, and it uses `go nodes` only (never `go depth`), so 21-F22's
explosion cannot reach it.

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 solver decides ≥ 60 % of move-pairs within the cap | **slightly missed — 52.6 %**. I report the miss; the cap (20,000 nodes/solve) is why, and a larger cap decides more at the cost of the wall clock |
| P2 ≥ 90 % of decided positions save the draw | **held** — 13 of 13 |
| P3 any hits are reproducible | not applicable (no hits) |
| P4 both colours appear among decided positions | **held** — both `white_strong` and `black_strong` rows |
| P5 0 crashes / sanitizer lines in the reporting run | held |

## Findings

`21-F23 | NEW` — extending the exact window to counters 85–94 leaves the result unchanged: on the
**52.6 %** of move-pairs the solver could decide (182 of 346 across 20 bare-king positions), **0 hits**;
all 13 positions that offered a draw-saving move had it taken by the engine at both `go nodes 20000` and
`go nodes 100000`. This is the wider-window half of 21-F21 and it agrees with it. The 7 undecided
positions are not evidence either way and are labelled as such.

Combined statement for the owner: across two exact scans — 50 positions in the 1–5 half-move window
(21-F21, 0 hits) and 20 positions in the 6–15 window (21-F23, 0 hits on 52.6 % decided) — **no position
has produced a move whose forced result was worse than an available alternative.**

## Suspicions, not proven

- The undecided 7 are mostly near the 13–14 half-move end, where a solve needs far more than 20,000
  nodes. Whether a hit hides there is genuinely unknown; a bigger cap or a tablebase would answer it and
  I have neither cheaply.

## What I did NOT do

- Did not raise the cap high enough to decide the 13–15 half-move positions (each solve would cost
  minutes).
- Did not test material other than a lone R or Q on the strong side.

## What I am NOT sure about

- Whether "no hit in the decidable region" generalises to the undecidable one. My two scans are
  consistent and that is all they support.

## Times

see `job40/stamps.txt` — including the three failed runs.
