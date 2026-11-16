# REPORT job6 — seat 20, area 10 job 1 (third check): seat 12's S-F1

**what was asked** — Reproduce an unconfirmed NEW finding: seat 12's S-F1, that `ucinewgame` silently resets the
board to startpos, so `position fen X` / `ucinewgame` / `go` searches startpos.

**the answer** — **CONFIRMS, decisively.** On a **black-to-move** position (where no legal move can be legal in
startpos), `position fen` + `ucinewgame` + `go depth 6` answers **`d2d4` — a white move**. Without `ucinewgame`
the same sequence answers `d7d6`, a black move. With a 10-ply `position startpos moves …` the same pair gives
`d2d4` (startpos) vs `d1b3` (the move-list position). The engine says nothing about the reset. Source:
`src/uci.cpp:254-257`, `(void)board.set_fen(forge::Board::StandardStartFen);` inside the `ucinewgame` branch.

**how sure** — certain. The decisive case cannot be explained by move overlap between the two boards, which was
the flaw in my first test position (its answer was legal in both).

## Honesty numbers
`/agent/repos/build-base/forge`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`,
4/4 pins (`../HONESTY.txt`). `OwnBook false` in every case so no book answer can be mistaken for a search.

## Step table
| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction, alone | done | `PREDICTION.txt` (commit before any run) | 5 predictions |
| source read first | done | `src/uci.cpp:254-257` quoted in `CHECK_s12F1.md` | the reset is there |
| first attempt | done, INCONCLUSIVE | `out_check.txt` case A | answer legal in BOTH boards — my bad test subject |
| decisive case added | done | `out_check.txt` cases A2/A3 | d2d4 (white move) on a black-to-move board vs d7d6 |
| move-list case | done | cases D/E | d2d4 vs d1b3 |
| order matters | done | case C | `ucinewgame` before `position` is safe |
| silence check | done | `check_s12f1.json` q3 | no line mentions the reset |

## Findings
1. **S-C3 = CONFIRMS seat 12's S-F1.** Show it again: `python3 check_s12f1.py <exe> .`
2. Only the order `position` → `ucinewgame` is dangerous; `ucinewgame` → `position` is fine (case C).
3. The reset is fully silent: no `info string`, no mention of startpos, and the engine never echoes a
   `position` command, so a harness cannot discover it from the transcript.

### Suspicions, not proven
- That some GUI sends `position` then `ucinewgame` (I have no GUI here). If none does, the practical risk is
  limited to tools and test harnesses — which is still how it produced six false "illegal bestmove" reports in
  seat 12's own job-1 harness.

## What I did NOT do
- I did not test `ucinewgame` during a running search (the source calls `stop_search()` first, so it should stop
  and reset; not measured).
- I did not test whether the reset also clears Hash (the source calls `searcher.clear()`, which clears the TT; not
  measured).
- I did not test the PC's Windows build.

## What I am NOT sure about
- Whether the reset was deliberate to protect against stale state between games. The code gives no comment either
  way, and I will not guess intent.

## Times: see `stamps.txt`
## The last command's output
```
$ ls forge-combo29/swarm/20/job6/
CHECK_s12F1.md  PREDICTION.txt  check_s12f1.json  check_s12f1.py  check_s12f1.txt
out_check.txt  stamps.txt
```
