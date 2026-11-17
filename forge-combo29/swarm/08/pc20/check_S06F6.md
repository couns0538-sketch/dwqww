# CHECK of seat 06's S-F6 / S-F27 — the colour-mirror asymmetry, reproduced EXACTLY on the whole G set

Their claims:
> S-F6 (base): "the depth-10 search is NOT colour-symmetric: **101 of 353** G positions (28.6 %) return a bestmove
> that is not the mirror of the other side's bestmove, and **334 of 353** scores differ"
> S-F27 (PC): "the search asymmetry is PRESENT IN THE ENGINE THE OWNER PLAYS at a rate indistinguishable from base —
> PC **120/353 (34.0 %)** vs base 101/353 (28.6 %)"

## Verdict: CONFIRMS — and this time it IS an exact reproduction, at their sample size

My own harness (`check_s06f6.py`), whole G set, 353 positions and their colour mirrors, `go depth 10`, Threads 1,
Hash 16, `OwnBook false`.

| config | pairs | bestmoves not mirrored | rate | scores unequal | rate |
|---|---|---|---|---|---|
| **base 6b98f217, S14** | 353 | **101** | **28.6 %** | **334** | 94.6 % |
| PC r15, S14 only (four switches OFF) | 353 | **102** | 28.9 % | 333 | 94.3 % |
| **PC r15, S14 + the four switches ON** | 353 | **121** | 34.3 % | 334 | 94.6 % |
| PC r15, PC20 full bundle | 353 | **120** | **34.0 %** | 331 | 93.8 % |

| their number | my number | verdict |
|---|---|---|
| base **101 of 353** (28.6 %) | **101 of 353 (28.6 %)** | **exact** |
| base scores differ **334 of 353** | **334 of 353** | **exact** |
| PC **120 of 353** (34.0 %) | **120 of 353 (34.0 %)** | **exact** |

All three of their headline counts reproduce to the digit on my own harness, my own mirroring implementation and my
own process. That is the strongest form of confirmation available: not merely the same conclusion, the same numbers.

## The switch question (S-F28), at their sample size

| comparison | OFF | ON | difference |
|---|---|---|---|
| bestmove asymmetry | 28.9 % | 34.3 % | **+5.4 points** |
| score asymmetry | 94.3 % | 94.6 % | +0.3 points |

With 353 pairs the 95 % interval on a ~30 % rate is about ±5 points. **+5.4 points sits at the edge of what this
sample can resolve**, so I say what my earlier 60-pair run could not: I do **not** call it an effect, and I do **not**
call the two rates identical either. My earlier 60-pair check (08-C15) reported +8.3 points inside a ±12 interval;
at 353 pairs the estimate has settled at +5.4 points, which is a smaller and better-measured difference but still not
a clean zero. The honest statement is: **the switches are not the main cause** — the asymmetry is 28.9 % with them
off, essentially the base tree's 28.6 % — **and a small contribution cannot be excluded at this sample size.**

## What is NOT claimed
- That the asymmetry is caused by anything. Seat 06's S-F18 records three refuted causes (tie-break, aspiration
  window, accumulated root alpha) and I have not added one.
- That the +5.4 points is a real effect. It is at the resolution limit.
- Anything about Threads > 1: all of this is Threads 1.

## Why this mattered
S-F6 is the base claim that everything in seat 06's symmetry work rests on, and it had no confirmation. It now has
one that reproduces its counts to the digit, which also validates my mirroring implementation — the `board.mirror()`
plus rank-flip move translation — against a seat that built its own.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s06f6.py /tmp/s06f6.txt
