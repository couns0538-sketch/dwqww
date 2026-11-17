# REPORT job7 — area 1 job 1 AGAIN (SEED 2111, new position set), seat 21

**What was asked.** THE CYCLE 2(c): run area 1's job 1 again with the next seed and a new
position set (R built from SEED + 10), and say in the report what differs from the first run.

**The answer.** Same engine, same driver, new seed (2111) and a mutation mix weighted by
job1's measured per-kind acceptance. 20,000 FENs: **18,820 refused, 1,180 accepted, 1,145
also valid for python-chess, 35 not (2.97 %), 0 crashes, 0 hangs, 0 sanitizer lines, 0
illegal bestmoves.** The four honesty numbers still hold exactly. The one prediction that
FAILED is P4: I predicted the python-invalid share would RISE above job1's 3.2 % and it fell
to 2.97 %. I was wrong about the direction, and the reason is visible in the per-kind table:
`replace` (the only kind that produces the adjacent-digit ranks) went from 30 % of the draws
to 17.8 %, and its own acceptance rate stayed low (14.8 %).

**How sure.** High on the counts (pasted table from a committed script over the committed
per-FEN file). High that the direction of P4's miss is explained by the mix, not by a harness
change: the engine, driver and batch size are identical to job6's re-run of job1, and the
honesty numbers reproduce.

## Honesty numbers (this build, re-measured for this job)

| command | expected | got | verdict |
|---|---|---|---|
| bench 11 | 312866 | 312866 | PASS |
| bench 13 | 862329 | 862329 | PASS |
| bench 16 | 3024920 | 3024920 | PASS |
| go perft 5 | 4865609 | 4865609 | PASS |

Raw: `job7/honesty.txt`. (Slower than the Release build because this is the ASan+UBSan
build; only the node counts matter here.)

## What differs from job1 — in full

| | job1 (SEED 2101) | job7 (SEED 2111) |
|---|---|---|
| seed | 2101 | 2111 |
| R set | 5,720 positions | 5,471 positions |
| mutation mix | uniform over 5 kinds | weighted by 1 − job1's measured acceptance rate |
| driver | `run_fen.py` (already 19-F12-safe) | `job6/fen_rerun.py` (same discipline, `OwnBook false`) |
| engine | ASan+UBSan build, sha256 73da1930… | same build |
| refused / accepted | 18,775 / 1,225 | 18,820 / 1,180 |
| py-invalid share | 3.19 % | 2.97 % |

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction committed before measuring | done | `job7/prediction.txt` | 8 predictions, 1 failed |
| R2 from SEED 2111 | done | `job7/R2.fens` (5,471) | written before use |
| 20,000 mutations, weighted mix | done | `job7/mutations2.tsv` | 20,000 |
| the run | done | `job7/out/` (results, 40 raw, meta, stamps) | 20,000 rows |
| tables from a committed script | done | `job7/analyse2.py` → `job7/tables.md` | — |
| honesty re-check | done | `job7/honesty.txt` | 4/4 |

## Tables (pasted from `job7/tables.md`)

| measure | count |
|---|---|
| REFUSED | 18,820 |
| ACCEPTED | 1,180 |
| accepted & python-chess valid | 1,145 |
| accepted & python-chess INVALID | 35 |
| python-invalid share of accepted | 2.97 % |

| mutation kind | drawn | accepted | refused | acceptance rate |
|---|---|---|---|---|
| delete | 4,119 | 234 | 3,885 | 5.7 % |
| dropfld | 4,308 | 0 | 4,308 | 0.0 % |
| insert | 4,066 | 232 | 3,834 | 5.7 % |
| replace | 3,561 | 526 | 3,035 | 14.8 % |
| swapfld | 3,946 | 188 | 3,758 | 4.8 % |

Refusal reasons (counted from the raw output, top 7): `invalid FEN fields` 2,093,
`invalid FEN placement` 1,810, `too many squares in FEN rank` 626, `invalid en-passant
square` 63, `invalid castling rights` 58, `pawn on promotion rank` 26, `impossible piece
inventory` 12, `side that moved left its king in check` 7.

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 refused rises above 18,775 | **held** (18,820) |
| P2 refused in 18,000–19,700 | **held** |
| P3 accepted in 300–2,000 | **held** (1,180) |
| P4 python-invalid share HIGHER than 3.19 % | **FAILED** (2.97 %) |
| P5 0 crash / hang / san | **held** |
| P6 0 illegal bestmoves | **held** |
| P7 honesty 4/4 | **held** |
| P8 no new refusal reason above 5 % | **held** (all reasons were already in job1's output) |

## Findings

No new finding. The one that would have been new — "the accepted-invalid share depends on
the mutation mix" — is not a statement about the engine, only about my generator, so it goes
under "not sure" rather than into FINDINGS.md. The engine-side facts (21-F3's two classes,
21-F10's zero refusals on real positions) are unchanged by this run: the 35 invalid FENs here
are again adjacent-digit ranks and seven-field FENs, and 0 accepted FEN produced an illegal
bestmove.

## Suspicions, not proven

- The acceptance rate of `replace` (14.8 %) is much higher than the other kinds (4.8–5.7 %).
  That is consistent with most malformed structures failing a structural check whatever the
  edit, while a single character swap often leaves a well-formed board. I did not test that
  hypothesis directly.

## What I did NOT do

- Did not run the 20,000 FENs on the Release build (ASan+UBSan only, same as job1).
- Did not compute a second R2 with a different sampling stride; the brief fixes "one position
  every 7 plies".

## What I am NOT sure about

- Whether a mix designed to maximise ACCEPTED FENs would change any conclusion. My run says
  the accepted set is dominated by well-formed boards, but I did not search for the mix that
  maximises pathological accepts.

## Times

see `job7/stamps.txt`.

## Last command's output

```
$ git status --short
(clean)
$ ls job7
analyse2.py  gen2.py  honesty.txt  mutations2.tsv  out  prediction.txt  R2.fens  run.log  stamps.txt  tables.md
```
