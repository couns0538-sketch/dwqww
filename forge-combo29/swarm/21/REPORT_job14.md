# REPORT job14 — area 1 job 1, THIRD run (SEED 2121), seat 21

**What was asked.** A third independent run of area 1's job 1, to see whether the first two
runs' picture is stable across seeds.

**The answer.** Stable. **18,797 refused, 1,203 accepted, 1,168 also valid for python-chess,
35 not (2.91 %), 0 crashes, 0 hangs, 0 sanitizer lines, 0 illegal bestmoves.** The invalid
class is unchanged: 28 adjacent-digit ranks and 7 extra-field FENs, no third class, no case
with a field count other than 6 or 7.

Three runs side by side (same engine, same driver):

| run | seed | refused | accepted | python-invalid | share | crash/hang/san/illegal |
|---|---|---|---|---|---|---|
| job1 | 2101 | 18,775 | 1,225 | 39 | 3.19 % | 0/0/0/0 |
| job7 | 2111 | 18,820 | 1,180 | 35 | 2.97 % | 0/0/0/0 |
| job14 | 2121 | 18,797 | 1,203 | 35 | 2.91 % | 0/0/0/0 |

Spread of the refused count across the three seeds: 45 (0.24 % of 20,000). The parser's
behaviour does not depend on which positions the seed happens to produce.

**How sure.** High. Same committed script (`job6/fen_rerun.py`), same ASan+UBSan build
(sha256 `73da1930…`), per-FEN tables committed, the invalid classes recomputed from the raw
table rather than assumed.

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction committed before measuring | done | `job14/prediction.txt` | 7 predictions, all held |
| R3 from SEED 2121, uniform mutation mix | done | `job14/R3.fens` (5,532), `job14/mutations3.tsv` | 20,000 FENs |
| the run | done | `job14/out/` | 20,000 rows |
| invalid-class breakdown computed from the raw table | done | this report (`python3 -c` over `asan14_results.tsv`) | 28 + 7, no third class |

## Prediction outcome

P1–P7 all held.

## Findings

No new finding: this run neither adds nor removes a class of fault. Its value is that 21-F3's
statement ("39 of 1,225, two classes, 3.2 %") is now backed by three independent seeds with
the share at 2.91–3.19 %, so the number is a property of the parser, not of one seed.

## Suspicions, not proven

- The accepted-invalid share drifts down slightly across the three seeds (3.19 → 2.97 → 2.91).
  With ~1,200 accepts per run and ~35 invalid, the standard error of that share is about 0.5
  points, so the drift is not significant; I did not test that formally.

## What I did NOT do

- Did not run the Release build for comparison.
- Did not widen the mutation alphabet, which would be the way to look for a third class.

## What I am NOT sure about

- Whether a different mutation alphabet (say, multi-character corruptions) would expose a class
  my single-character edits cannot reach. Not tested.

## Times

see `job14/stamps.txt`.

## Last command's output

```
$ git status --short
(clean)
$ ls job14
gen3.py  mutations3.tsv  out  prediction.txt  R3.fens  stamps.txt
```
