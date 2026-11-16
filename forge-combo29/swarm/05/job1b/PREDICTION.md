# PREDICTION — seat 05 (area 5) job1 REPEAT with SEED + 10 — pushed BEFORE any measuring command

The brief's cycle step (c): job 1 of my area again with the next seed and a new position set (R with SEED + 10).

Build: release `/tmp/build-rel/forge`, sha256 `e06310ec...a83` (honesty 4/4, re-verified after 19-F12).
Settings: S14, Threads 1, Hash 16, `ucinewgame` + `isready` before every `go`, `go depth 12`.
Position set: **R_seed511.fens**, 200 positions from random games at `random.Random(511)`, one position every 7
plies, every FEN asserted legal and non-terminal by python-chess. This set has never been searched before.

## What differs from my first job1 run (required by the brief)
| aspect | first run (job1/) | this repeat |
|---|---|---|
| seed | 501 | **511** |
| position set | O (200 from kimi5) and G (353 from games) | **R, 200 random play positions, brand new** |
| depth | 12 | 12 (same, so results are comparable) |
| checker | `check_pv.py` + `dtm2.py` (both since audited) | same checkers, plus the parse assertions from `audit19f12/parser_audit.py` |
| expected character | G contains many tactical/mate positions | R positions are random-play middlegames, so I expect FEWER mate scores and more `cp` scores |

## Numbers, each with the range that kills it

| # | what | predicted | killed if |
|---|------|-----------|-----------|
| 1 | positions searched with a `bestmove` and at least one `info ... pv` line | 200 of 200 | any position without a pv line |
| 2 | illegal moves inside a last-PV line | 0 | 1 or more |
| 3 | positions whose final score is `mate N` | **0 to 6** (fewer than the 10 of the O+G run, because random play rarely leaves forced mates at depth 12) | more than 12 |
| 4 | of those, PV exactly consistent with 2N-1 / 2\|N\| | all but at most 1 | 2 or more inconsistent |
| 5 | sum of last depth-12 `nodes` over the 200 positions | between 10,000,000 and 40,000,000 | outside that band, which would suggest a different position character than I intended |
| 6 | median nodes per position | 60,000 to 130,000 | outside, same reason |
| 7 | the same position searched twice (control, 5 positions) gives identical score and identical node count | 5 of 5 | any difference |
| 8 | crash / hang / missing bestmove | 0 | any |
| 9 | the new S-F1 pattern (`mate N` with a PV shorter than 2N-1) reappears at least once | 1 or more | 0, which would mean S-F1 is specific to G/192 rather than a general horizon effect |

## Reasoning written down before measuring
- R positions come from random play, which produces unbalanced, material-rich positions but rarely short forced
  mates at depth 12, so #3 predicts FEWER mate scores than the 10 seen on O+G. If I instead see many mate scores, my
  generator produced something more tactical than I intended and I will say so.
- #9 is the interesting one. My S-F1 was found on one G position. If the same truncation appears in a fresh set of
  200 positions that were never involved in finding it, that is evidence the truncation is a general behaviour of
  mate reporting rather than a one-position curiosity. If it does not appear, S-F1 stays a single-position finding
  and I will say that plainly.

## Method (fixed before measuring)
- `run_rows.py` from job1, unchanged, with `positions/R_seed511.fens` as the set file (it reads stdout to `bestmove`
  before quitting, so 19-F12 does not apply); output `outR/R.d12.raw.txt` + `.meta`.
- `check_pv.py` from job1 for legality and the 2N-1 arithmetic; a JSON copy of its rows for the auditor.
- Control #7: one process, the same 5 positions searched twice without `ucinewgame` in between, plus a cold run.
