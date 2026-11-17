# STATUS — option-surface audit

Base commit `6b98f217`. Branch `swarm/options`. PR
[#87](https://github.com/couns0538-sketch/dwqww/pull/87).

## One-line state

**No correctness violation found in any of the 18 switches.** 51 tunables clean,
perft 5 clean on all 18, and **all five properties clean on all 18 switches —
18 fully-clean rows, no gaps**. The substantive correction in this run is a
**finding this audit raised and then withdrew** — §4.

## 1. Results

| item | result | evidence |
|---|---|---|
| Honesty pins, baseline | bench 11/13/16 = 312866 / 862329 / 3024920, perft 5 = 4865609, exact | `evidence/pins-per-switch.json` |
| Perft 5 under each of 18 switches | **18/18 = 4865609** | `evidence/pins-per-switch.json` |
| **51 tunables × 5 values** | **255 cells, 51/51 correct, 0 crashes, 0 clamp mismatches** | `evidence/tunables.json` |
| Tunables that reach the search | **51/51** — none inert | `evidence/tunables.json` |
| Legality, 200 positions @ d12 | **18/18 switches clean**, 0 illegal, 0 unplayable PV | `evidence/switch-arms.json` |
| Mate, 30 proved fixtures | **18/18 clean, 0 unsound, every claimed mate proved** | `evidence/mate-summary.json` |
| Terminal roots | **18/18 = 6/6** | `evidence/switch-arms.json` |
| Drawn-root bail | **18/18 = 4/4** | `evidence/switch-arms.json` |
| Sanitizer | **18/18 clean**, 200/200 positions each, 0 lines, planted faults caught every run | `evidence/sanitizer/` |
| Option interference | 16 pairs, 0 order-dependent; **null is weak by construction** | `evidence/interference.json` |
| Inert options | `OwnBook`, `NnueFile` — both explained by known behaviour | `evidence/interference.json` |

## 2. The pin sweep

Bench node counts move for 15 of 18 switches. Expected: `bench` is a search, so a
search heuristic changes it. **Perft is the pin a search switch cannot move** — it
never consults evaluation, history, pruning or the clock. **18 of 18 leave perft 5
at 4,865,609**, with the baseline reproducing all four pins first.

## 3. Why the interference null is weak, stated rather than implied

Every option handler is a plain assignment (`src/uci.cpp:383-473`), so setting A
then B leaves the same values as B then A. **Order-independence is true by
construction**, and 0-of-16 is the expected result, not a discovery.

The report's `UseNNUE > NNUEArch > NnueFile` precedence is **gating on a value**,
not ordering. An order test cannot find a second instance; a value test can. The
value test (no-effect sweep) ran and found only `OwnBook` (clock-only, not
`go depth`) and `NnueFile` (embedded net) — both already in the report.

## 4. A finding raised and WITHDRAWN

`ContHist4PlyRead` was reported mid-run as making a **false mate claim**. **That
finding is withdrawn. Unsound went 5 → 0 across all 19 arms.**

The flag used PV length as evidence: `mate 12` with a 14-move PV that never
mates. But the PV comes from a depth-12 search and **cannot exceed 12 moves**,
while `mate 12` needs 19–23 plies. The short PV was guaranteed by the depth and
proved nothing.

Re-decided by proving the position after each arm's own bestmove, under longest
defence — the only sound test on the wire — every flagged row is a **true claim
with an over-long distance**. `scripts/rejudge.py` recomputed all 19 arms from
stored rows and prints the before/after count.

Three separate defects in this audit's own checker had to be fixed to get there:

1. PV length used as evidence of a mate's existence.
2. The wrong side assumed to move after the bestmove — backwards for every
   negative claim, which is the trap that makes a mate checker wrong on exactly
   those rows.
3. `prove()` returning `None` for both "no mate" and "exhausted budget", folded
   into one verdict, producing a confident FALSE on a position whose mate exists.
   Fixed by retrying at 12× budget before accepting a refutation.

Each was caught by one check disagreeing with another, not by reading code. All
three now have controls in `mate_controls()`.

**This is the most useful result in the run**: a plausible, reproducible,
switch-attributable "correctness bug" that dissolved under a sound predicate. Had
it shipped, it would have been a confident wrong answer about a switch that is
correct.

## 5. What is NOT done

Nothing in the assigned scope is unfinished.

| item | status |
|---|---|
| ASan+UBSan, 18 switches | **complete.** 18/18 clean, 200/200 positions each, 0 sanitizer lines, planted faults caught in every run. |
| Deeper mate corpus | **a lead, not a gap.** 30 fixtures; the deepest is mate-in-5. Mate-in-7 would exercise more of the pruning the switches touch, and `QuietExtinction`'s 7 missed mates are the most likely place a difference would show. |

## 6. Honest summary

The tunables row is the substantive new result: 255 cells, no crash, no clamp
mismatch, and — what a clamp-only check would have missed — **all 51 demonstrably
reach the search**.

The switch table is a clean bill: 18 switches × 5 properties, every cell a count,
no gaps. **No correctness violation exists in any switch in this set.** The pin
gate was verified per switch before any property was measured, so the rows are
not measured on builds that were never validated.

The withdrawal in §4 is worth more than either result, because it is the case
where this audit was wrong in the direction that would have caused harm:
accusing a correct switch of inventing a mate. Three separate bugs in the
audit's own checker had to be found — by checks disagreeing with each other, not
by reading the code — before the null was trustworthy. A clean bill that had
shipped with any one of those bugs in place would have been a confident wrong
answer about a switch that is correct.
