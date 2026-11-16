# seat 20 — check of seat 06's S-F6 (the depth-10 search is not colour-symmetric)

Verdict: **CONFIRMS the substance, with a rate that differs from theirs and one of my own predictions killed.**
The asymmetry is real (18/20 positions have different scores for a position and its colour mirror), but the
*bestmove* asymmetry rate on my positions is **10 %, not their 28.6 %** — below the 20–40 % I predicted.

Raw: `check_s06f6.json`. Script: `check_s06f6.py`. `AUDIT/hardened.py`, **fresh process per search** (seat 10's
rule), S14 applied (the project setting), depth 10, `OwnBook false`.

## Results (20 positions, my own seeded walk)

| | count | rate | seat 06's figure |
|---|---|---|---|
| bestmove not the mirror | 2/20 | **10.0 %** | 101/353 = 28.6 % |
| score differs | 18/20 | **90.0 %** | 334/353 = 94.6 % |
| score difference, median | 42 cp | | — |
| score difference, max | 170 cp | | — |

The two bestmove-asymmetric cases:
- #2: P plays `h6g4`, mirror of that is `h3g5`, but M plays `c4b5` (scores 104 vs 63);
- #12: P plays `a7a5`, mirror is `a2a4`, but M plays `a1b1` (scores 5 vs 0 — a near-tie, so an ordering flip).

Both mates (#17 `mate 3`, #18 `mate 1`) are perfectly symmetric, bestmove **and** score.

Controls: the same position searched twice gives the identical bestmove and score (`c6b4`, `cp 84` both times);
a different position gives a different bestmove — so the comparator sees real differences and my harness is
deterministic.

## My own prediction was wrong, and it matters
I predicted 20–40 % bestmove asymmetry and stated that under 10 % would kill it. I measured 10.0 % — **at the kill
boundary**. So:
- seat 06's *qualitative* claim (search is not colour-symmetric) is **CONFIRMED**;
- their *rate* is **not reproduced** on my positions. Two possible reasons, and I cannot separate them: (a) their
  G set (353 positions from games) contains more sharp/tactical positions where ordering flips matter, (b) their
  harness may share a process or a TT between the P and M searches, which would inflate asymmetry. I used fresh
  processes precisely to avoid (b).

## The mechanism (consistent with the data)
Alpha-beta with hash and history move ordering explores equal-scoring moves in an order that is not
mirror-invariant; the *score* then differs slightly depending on which equal or near-equal line is resolved first.
The median 42 cp difference is real but modest, and the two asymmetric bestmoves were both near-ties (5 vs 0 cp;
104 vs 63 cp). Nothing here indicates a wrong evaluation: `eval` itself is exactly symmetric (my S-C6, 360/360
pairs with 0 difference), so the asymmetry enters through the search, exactly as seat 06's S-F7 argues.

## What I did NOT do
- I did not run their 353-position G set, so I cannot say whether their 28.6 % reproduces on their own data.
- I did not test whether a shared process inflates the rate (that would test hypothesis (b) above).
- 20 positions is a small sample; the 95 % interval on 2/20 is wide (roughly 1–32 %).

## What I am NOT sure about
- Whether 10 % vs 28.6 % is a position-set difference or a harness difference. I lean to position set, because my
  harness is the stricter one, but I did not prove it.

## Commands that show it again
```
python3 check_s06f6.py /agent/repos/build-base/forge /tmp/o 20
```
