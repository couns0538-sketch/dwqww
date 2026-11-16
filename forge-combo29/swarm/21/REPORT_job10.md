# REPORT job10 — CHECK of 08-F5 (reserve-empty clock branch), seat 21

**What was asked.** THE CYCLE 2(a): reproduce an unchecked finding from another seat with my
own harness. 08-F5 (seat 08, area 8) was unchecked by anyone.

**The answer.** **CONFIRMS 08-F5**, including its two discriminating numbers exactly:
the `wtime 1` answer equals the `go depth 1` answer in **8 of 8** positions and equals the
first legal move in **1 of 8**. `wtime 10 winc 10` gives the same answer as `wtime 10 winc 0`
in 8 of 8, so the increment does not lift the search out of reserve-empty. Median wall time
0.10–0.46 ms, maximum 0.64 ms over all clock cases. 0 illegal bestmoves.

**How sure.** High. Eight of my own positions (O's first 8), one fresh process per position,
`OwnBook false`, monotonic timing from writing `go` to reading `bestmove`, the safe driver
(19-F12), FEN acceptance asserted, an empty-bestmove read raises, and every bestmove checked
for legality with python-chess. The depth-1 reference is the only thing that separates
"shallow search" from "play the first legal move", and both are measured here.

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction committed before measuring | done | `job10/prediction.txt` | 6 predictions |
| 8 positions × 5 searches, fresh process each | done | `job10/out/pos_*_raw.txt` | 40 searches |
| legality of every bestmove | done | `job10/out/summary.md` | 0 illegal |
| timing | done | same | max 0.64 ms |

## Table (pasted from `job10/out/summary.md`)

| measure | value |
|---|---|
| positions | 8 |
| wtime1 == go depth 1 | 8 of 8 |
| wtime1 == first legal move | 1 of 8 |
| wtime10+winc10 == wtime10 | 8 of 8 |
| illegal bestmoves | 0 |
| median wall time, wtime10 | 0.302 ms |
| median wall time, wtime1 | 0.457 ms |
| median wall time, wtime0 | 0.106 ms |
| median wall time, wtime10+winc10 | 0.100 ms |
| max wall time, any clock case | 0.641 ms |

Per-position answers are in the raw files; one representative row: position 5
(`8/6k1/3p4/3P2PP/4KP2/4N3/8/8 w`) has `go depth 1` = `e4f5` and first legal = `e4f5`, the
single position where the two coincide — which is why the 1-of-8 figure is not zero.

## Prediction outcome

All 6 held (P1–P6).

## Findings

`21-C4 | CONFIRMS 08-F5` — added to FINDINGS.md.

## Suspicions, not proven

- 08-F5 says the reserve test runs before the increment is used. My measurement is consistent
  with that (8/8 identical), but I did not read the clock-plan code to confirm the order; the
  observation is behavioural only.
- Seat 08's own median (0.14–0.17 ms) is lower than my 0.30–0.46 ms. That is very likely a
  build difference (mine is a plain Release build; the machine and load differ). It does not
  affect the claim, which is about the branch taken, not the exact microsecond.

## What I did NOT do

- Did not test `movestogo` with `wtime 10`.
- Did not check 08-F6 (the `wtime 30` hard-limit overrun), which is a different finding.
- Did not run under a sanitizer (a timing claim, no memory question).

## What I am NOT sure about

- Whether the 1-of-8 coincidence at position 5 is genuinely "depth 1 and first legal agree" or
  a coincidence of the reserve-empty branch picking the same move. Both are consistent with
  the measurement; I did not instrument which.

## Times

see `job10/stamps.txt`.

## Last command's output

```
$ git status --short
(clean)
$ ls job10
check_08f5.py  first8_G.fens  out  prediction.txt  stamps.txt  set_G.fens
```
