# REPORT job3 — seat 20: the unsearched-first-legal-move fallback

**what was asked** — Not a named job. While checking whether the drawn-root shortcut of seat 01's S-F5 was the
only path that returns an unsearched move, I found a second path and characterised it. This report is that work:
`go nodes 0/1`, a `stop` arriving at 0 ms, and `quit` during a search each make the engine answer with its
FIRST LEGAL MOVE.

**the answer** — The engine returns `root_candidates.front()` (the first move of its own legal-move list) with
zero nodes searched in exactly three situations: (1) `go nodes 0` (and `go nodes 1`, which stops before any node
is counted), (2) `stop` delivered with 0 ms between it and `go infinite` (20 of 20 tries), and (3) `quit` while a
search runs. Clocked searches are clean: `go wtime …` / `go movetime 1..200` always searched (0 of 65 unsearched),
and a 20-ply clock game from startpos gave 20/20 searched and 20/20 legal bestmoves. At `stop` delays of 1 ms or
more the fallback never appeared. **So this is not a game-play defect**; it is a 0-node/0-time edge.

**how sure** — certain about what the engine does (raw transcripts committed, 20 tries per cell); "not a
game-play defect" is supported by the 20-ply clock game and by the 1 ms+ stop cells, not proven for every GUI.

## Honesty numbers
`/agent/repos/build-base/forge`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`,
g++ 13.3.0, `-march=x86-64-v4`, 4 cores. Bench pins 312866 / 862329 / 3024920 / perft 4865609 all match
(`../HONESTY.txt`). Sanitizer runner proof (planted fault counted, real build 0) in `out/planted.meta`,
`out/clean.meta` — built by `plant_build.sh` + `sanrun.sh`, the runner used for the ASan build.

## Step table
| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| first, a WRONG measurement | done and discarded | `out/fallback.out.txt` | piping `go` + `quit` together means quit always wins; every case "unsearched". My criterion, not the engine, was at fault. |
| an honest interactive driver | done | `drive.py`, `out_drive1.txt` | quit during a search -> first legal move, 0 depth lines |
| book vs defect | done | `out_clockcut.txt` vs `out_clockcut_bookoff.txt` | the startpos "unsearched" cells were the OPENING BOOK (`info string book move`); with `OwnBook false` they vanish |
| clocked searches | done | `out_clockcut_bookoff.txt` | 0 unsearched in 65 tries over 3 positions x 13 go forms |
| stop delay sweep | done | `out_fallback2.txt` | 0 ms: 20/20 unsearched; 1, 2, 5, 10, 20, 50, 200 ms: 0/120 |
| a real clock game | done | `out_fallback2.txt` §3 | 20 plies, 0 unsearched, 0 illegal, 13–16 info-depth lines/ply |
| the source path | done | `src/search.cpp` (read) | see below |

## Findings
1. Only `go nodes 0` and `go nodes 1` return an unexamined move on the plain-budget path; `go depth 0` and
   `go depth 1` search normally. Show it again: `python3 fallback2.py /agent/repos/build-base/forge` §1.
2. `stop` at 0 ms after `go infinite` returns the first legal move 20/20 on three positions; at 1 ms or more,
   0/120. Show it again: same file, §2.
3. The startpos cells of `out_clockcut.txt` that looked like the fallback were the opening book answering;
   `setoption name OwnBook value false` removes them. This is a trap for anyone measuring "unsearched" replies.
4. A normal clock game (one `go` per `bestmove`, `go wtime 1000 btime 1000`) is unaffected: 20 plies, all
   searched, all legal.

### Where in the source
`src/search.cpp` (6b98f217), in `Worker::search`:
- `if (limits.nodes_specified && limits.nodes == 0) { result.best_move = root_candidates.front(); ... return; }`
- `else if (!waiting_to_ponder && hard_limit_ms_ > 0 && elapsed_ms() >= hard_limit_ms_) { result.best_move = root_candidates.front(); ... return; }`
- at the end: `if (result.best_move.is_none()) result.best_move = root_candidates.front();`
`root_candidates.front()` is the first of `board.legal_moves()`, i.e. a2a3 for white / a7a6 for black — which is
exactly what the runs show.

### Suspicions, not proven
- That `go nodes 1` is a *defect* rather than a deliberate "give me something now" answer. `go nodes 0` is
  arguably fine; `nodes 1` returning 0 nodes means the budget is spent on setup before the first node. Not proven
  against the PC's intent, and the UCI spec does not require a searched move at such budgets.

## What I did NOT do
- I did not test `stop` at 0 ms through a real GUI's timing (my driver sends stop immediately, which a GUI never
  quite does).
- I did not run the 0 ms cells under the sanitizer.
- I did not test `ponderhit` at 0 ms.

## What I am NOT sure about
- Whether any real GUI sends `go nodes 1`. It is legal UCI; I did not survey GUIs.

## Times: see `stamps.txt` and `../job1/stamps.txt` (this work ran between jobs 1 and 2).
## The last command's output
```
$ git status --short forge-combo29/swarm/20/job3/
?? forge-combo29/swarm/20/job3/
$ ls forge-combo29/swarm/20/job3/
out  out_clockcut.txt  out_clockcut_bookoff.txt  out_drive1.txt  out_fallback2.txt
drive.py  fallback2.py  fallback.sh  clockcut.py  plant_build.sh  sanrun.sh
```
