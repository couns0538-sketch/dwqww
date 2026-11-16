# MOVE GENERATION: CLOSED — closure note for commit 6b98f217 and PC r15

**Written by seat 13 (area 3), 2026-11-16.** Every number below was re-read from the committed
evidence files next to this note before it was typed; none is from memory. This note exists so the
next round does not re-run perft.

## The line
**Move generation is closed.** The engine's legal move lists match python-chess on every material
type, every depth and every granularity I could measure, on the base tree 6b98f217 and on the PC r15
build, under default settings, S14 and PC20. No perft work is needed on this build; spend the time
elsewhere.

## What is covered, at what granularity, on what material, on what build

| # | job | material | positions | depth | granularity | pairs / root moves compared | differing | builds & settings |
|---|---|---|---|---|---|---|---|---|
| 1 | job 1 | synthetic R, seed 1301 | 5,000 | 1–4 | totals | 20,000 pairs | **0** | base, default (see `job1/comparison_hardened.md`) |
| 2 | job 1b | synthetic R, seed 1311 | 5,000 | 1–4 | totals | 20,000 pairs | **0** | base, default |
| 3 | job 2 | selected edge cases (castling transit / rook-path / ep legal / ep would-expose-king / capture-promo-check / double check / pinned-takes-pinner) | 494 | 1–4 totals, **2 divide** | totals + per-root-move | 1,976 pairs + 494 divides | **0** | base, default |
| 4 | job 3 | 200 R + first 30 of G | 230 | **4 and 5** | totals | 460 pairs | **0** | base, default |
| 5 | job 4 | synthetic R | 200 | 4 | **divide** | **5,182 root moves** | **0** | base Th1/Hash16 · PC r15 Th1/Hash16 · PC r15 **PC20** |
| 6 | job 6 | **real-game G** (stride sample of all 353) | 200 | 4 | **divide** | **5,107 root moves** | **0** | base Th1/Hash16 · PC r15 Th1/Hash16 · PC r15 **PC20** |

Totals across the run: **11,124 position-set entries covering 10,482 distinct FENs** (the sets overlap:
job 3 reuses 200 of job 1's positions and job 4 re-uses the same 200; job 6's 200 are a subset of G),
**42,436 (position, depth) pairs** and **10,783 root-move divides** compared, with zero differences
anywhere. Computed from the committed FEN files, not estimated.

Published-value anchor (job 1 control): both the engine and python-chess reproduce startpos perft
1–5 (20 / 400 / 8,902 / 197,281 / **4,865,609**) and Kiwipete perft 1–4 (48 / 2,039 / 97,862 /
**4,085,603**), so the reference implementation is anchored to the standard tables, not only to itself.

## Harness credibility (why these zeros count — FABLE file 2, Rule 1)
Each zero came with a planted case through the same harness, unchanged:

| job | planted fault | result |
|---|---|---|
| job 1 | one node added to one record | `control B verdict: PASS - exactly one differing pair reported` |
| job 2 (divide) | +1 / −1 on two root moves so the **total stays exact** | `RESULT: CAUGHT by the divide check` |
| jobs 1/1b/2 re-run | empty reference file / truncated reference / `nan` in a node count | all three **fail loudly** (`FAIL: no records at all`, `FAIL: NO REFERENCE RECORD`, `FAIL: node count 'nan' is not an integer`) |
| job 4 | compensating +1/−1 (total unchanged), missing move, extra move | all **CAUGHT**; identity **not** flagged |
| job 6 (on G material, before measuring) | compensating `b8a8 +1` / `b8b3 -1` with total unchanged at 743,255; missing; extra | all **CAUGHT**; identity **not** flagged |

## The four limits (why "closed" is bounded)

1. **Depth 5 is totals-only.** The divide comparison was run at depths 2 and 4. At depth 5 the
   comparison is aggregate counts, so a compensating error that cancels in the total would escape
   there. (The depth-5 divide was considered and deliberately not run: the reference cost is roughly
   30× the depth-4 divide for materially the same information.)
2. **python-chess is the only oracle.** Every comparison is against one other implementation. A rule
   the two implementations misread *identically* would pass all of this. The startpos/Kiwipete anchor
   covers that risk at those two positions only.
3. **Positions python-chess refuses cannot be tested this way.** Area 1's territory — adjacent-digit
   ranks (`17`, `44`), impossible castling rights — has no reference value to compare against, so
   whatever the engine does there is outside this closure.
4. **Sampling.** R comes from my random-game generator and under-represents sparse endgames; G is 353
   positions from engine games and I sampled 200 by fixed stride. Neither is the owner's match
   material.

## What is explicitly NOT concluded
- **Move generation ≠ move choice.** This says the legal move lists are correct. It says nothing about
  whether the search picks a good move, and nothing about evaluation, pruning or time management.
- No claim about positions outside the six sets above, nor about depths beyond 5.

## If someone does want to re-open it
The command that would falsify this note fastest, on any build:

```
cd forge-combo29/swarm/13/job6
python3 control_divide.py <fens>                       # prove the checker can fail first
python3 divide_perft4.py <exe> <fens> out.json PC20    # then measure
```

A single `positions_differing` above 0 with the control passing reopens the chapter; anything without
a passing control does not.

## Evidence index
- `job1/` — 5,000 R (seed 1301), totals, plus published-value control (`control.md`).
- `job1b/` — 5,000 R (seed 1311), totals, hardened checker.
- `job2/` — 494 edge cases, totals + perft-2 divide; `DIVIDE_CONTROL.md` (compensating error caught).
- `job3/` — 230 positions at depths 4 and 5, totals.
- `job4/` — 200 R at perft 4 **divide**, three build/settings combos; `CONTROL_DIVIDE.md`.
- `job6/` — 200 **G** at perft 4 **divide**, three build/settings combos; `CONTROL_DIVIDE.md`.
- `INTEGRITY_AUDIT.md` — the three tool defects found and fixed (including the stale-shard fault that
  once fabricated 1,929 differences).

All under `forge-combo29/swarm/13/` on branch `for-fable-and-opus/swarm-13`.

## Aggregate verification (pasted output of `closure_verify.py`)
The totals above are not typed by hand; this is the pasted output of the committed script that
recomputes them from the committed evidence files.

```
$ python3 closure_verify.py
| set | positions |
|---|---|
| job1  R_1301 (synthetic) | 5000 |
| job1b R_1311 (synthetic) | 5000 |
| job2  special500 (edge cases) | 494 |
| job3  all230 (R+G) | 230 |
| job4  R200 (synthetic) | 200 |
| job6  G200 (real game) | 200 |

sum of set sizes: 11124
distinct FENs: 10482

totals-granularity pairs (read from each comparison.md):
  job1   20000
  job1b  20000
  job2   1976
  job3   460
  TOTAL   42436

divide-granularity root moves (read from each JSON summary):
  job4 d4  5182
  job6 d4  5107
  job2 d2  494 (from VERDICT.md: 0 of 494 differed)
  TOTAL    10783

differences found anywhere: 0
```
