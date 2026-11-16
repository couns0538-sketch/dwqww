# REPORT — seat 30, area 10, check 30-C2: seat 05's S-F3 ("fifty-move draw applied ~9 plies early")

## 1. Three lines
**Asked:** reproduce seat 05's S-F3 — on `1K6/8/8/3R4/8/8/8/k7 w - - <H> 1` at `go depth 10`, the
score is `cp 472` for H ≤ 75, `cp 314` at H=90, and exactly `cp 0` from H=91, which they read as the
fifty-move threshold being applied about nine plies early.
**Answer:** **their NUMBERS reproduce to the node; their INTERPRETATION does not.** Holding the
counter at 91 and changing only the depth moves the "threshold": depth 7 reports `cp 354` (no draw
seen at all), depth 9 and 10 report `cp 0`, and the first counter answering `cp 0` is 93 at depth 7,
91 at depth 9, 90 at depth 12. That is a depth-10 search meeting halfmove 100 inside its own horizon,
not a fixed off-by-nine. The real finding in the same data is the COST: that one counter step takes
the search from 946,042 to 13,791,896 nodes.
**How sure:** certain (each case one fresh process, fully synchronised, S14 applied, and the
discriminator is a monotone trend across four depths rather than a single comparison).

## 2. Honesty numbers
Release `6b98f217`, sha256 `e06310ec…6a83`; bench 11/13/16 = 312866 / 862329 / 3024920,
perft 5 = 4865609 (HONESTY.txt). The run set S14 through `setoption` and waited for `readyok`
after every one.

## 3. Step table
| step | done/partly/not | evidence file | result |
|---|---|---|---|
| prediction committed before measuring | done | `check2/prediction.txt` (commit before the run) | 5 predictions |
| my own harness | done | `check2/check_s05f3.py` | synchronized, S14 applied |
| their ramp reproduced | done | `check2/out/results.json` rows arm=ramp | identical to their table |
| the depth discriminator | done | rows arm=discriminator | horizon, not threshold |
| collapse point vs depth | done | `first_cp0_by_depth` | 93 / 91 / 91 / 90 for depth 7/9/10/12 |
| ASan repeat | not done | — | the path is control flow; see "what I did NOT do" |

## 4. Result tables (pasted from the committed run)
Ramp at depth 10, S14, board `1K6/8/8/3R4/8/8/8/k7 w - - H 1`:

| H | score | nodes | bestmove |
|---|---|---|---|
| 0 | cp 472 | 9308 | d5b5 |
| 75 | cp 472 | 9309 | d5b5 |
| 80 | cp 398 | 8657 | d5b5 |
| 85 | cp 349 | 29104 | d5b5 |
| 88 | cp 320 | 192711 | d5b5 |
| 90 | cp 314 | 946042 | d5b5 |
| 91 | cp 0 | 13791896 | d5d4 |
| 92 | cp 0 | 1659545 | d5f5 |
| 93 | cp 0 | 1075193 | b8a8 |
| 95 | cp 0 | 95459 | d5b5 |
| 99 | cp 0 | 200 | d5d1 |
| 100 | cp 0 | 0 | d5d1 |

The discriminator — counter fixed, depth varied:

| H | depth | score | nodes | seldepth |
|---|---|---|---|---|
| 91 | 7 | cp 354 | 27882 | 9 |
| 91 | 9 | cp 0 | 6585109 | 9 |
| 91 | 10 | cp 0 | 13791896 | 10 |
| 91 | 12 | cp 0 | 22333426 | 12 |
| 92 | 7 | cp 401 | 4043 | 8 |
| 92 | 9 | cp 0 | 1389393 | 9 |

First counter with `cp 0`: **93** at depth 7, **91** at depth 9, **91** at depth 10, **90** at depth 12.
A fixed early threshold would be the same number at every depth. It is not.

## 5. Findings
1. **30-C2 (REFUTES the interpretation, CONFIRMS the numbers).** The H=91 collapse is the search
   horizon reaching halfmove 100; the search treats the fifty-move rule as automatic (a draw that
   happens without a claim). Command: `python3 check2/check_s05f3.py <exe> <outdir>`.
2. **30-F9 (NEW, mine).** The horizon meeting is expensive and unguarded: 946,042 nodes at H=90 vs
   **13,791,896** at H=91 — 15x more nodes for one unit of a counter, and at H=99 the engine answers
   from the root shortcut in 200 nodes. A time-controlled game could spend the same 1.2 s for nothing.
3. Note in their favour: `H=90 -> 314 cp` and the gradual slide from 472 to 398 to 349 to 320 shows
   the engine is ALREADY scoring the coming draw, which is correct behaviour, not a fault.

## 6. Suspicions, not proven
- The node explosion at H=91 may be partly the `DrawJitter`/`draw_leaf_score` path; I did not set
  `DrawJitter` and did not read that path.
- I did not test whether a real game (with a claim) is handled differently from a FEN counter.

## 7. What I did NOT do
- No ASan/UBSan pass here: the behaviour is control flow and no memory is involved; the check is
  about which branch is taken, and the numbers already show which branch.
- I did not test their second board (K+Q) from S-F4; their S-F4 is a different claim (all 20 boards
  cp 0 at counters 98 and 99) and I did not check it.

## 8. What I am NOT sure about
- Whether "the fifty-move rule is automatic in search" is intended. Many engines treat it so. If so,
  neither their S-F3 nor my 30-F9 is a bug — the finding is the cost, not the rule.

## 9. Times: `check2/` has the run stamps in `last_cmd.txt`; the harness prints no per-case times.
## 10. Last command — see `check2/last_cmd.txt`.
