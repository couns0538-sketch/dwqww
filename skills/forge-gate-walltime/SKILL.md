---
name: forge-gate-walltime
description: Read-only tools that cut or plan Forge gate wall time without changing what a gate means (speed job Job C, 2026-11-05, branch opus-speed-20261105, opus_speed/jobc) - gate_replay.py (exact fastchess 1.8.2 GSPRT replay of a finished gate with verdict check, strict PGN/log pairing, corrupt / truncated input -> exit 2, no verdict), llr_project.py (planning-only projection to the cap), queue_throughput.py (games/h per slot, idle gaps), adjudication_audit.py (settings + what draw/resign rules would save, report only), book_load_check.py, pregate_screen.py (cheap rejects before games: PE, uciok, options, pins, perft, movetime smoke, WAC), concurrency_plan.py, and their tests. Use for gate replays / audits, queue planning, a pre-gate screen of a candidate exe, or any "why does the gate queue take so long" question.
---

# Forge gate wall time (Job C of the speed job, 2026-11-05)

Rules: [[forge-pc-rules]]; gate facts: [[forge-gate-stats]], [[forge-gate-summary]]. Tools live in
`opus_speed/jobc/tools/` on branch opus-speed-20261105 (README.md = usage, RESULTS.md = numbers with sources).
Binding crew vote (unchanged by these tools): Threads=1, SPRT [0,5] normalized Elo, alpha = beta = 0.05, pentanomial,
caps 3000 search / 4000 nets / 6000 UE3A/B, UNPROVEN at the cap, one extension only if the Elo is positive.
Everything is planning input or a pre-game screen; nothing is a stop rule, nothing touches the queue or its config.

## Run
`PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe; $PY -I -B opus_speed/jobc/tools/<tool>.py ...`
(forward-slash paths; numpy for llr_project, python-chess for move checks). Tests: `$PY -I -B
opus_speed/jobc/tests/run_tests.py --tmp <scratch> --out <scratch>` (ALL PASS 09:50 and in an independent re-run 10:01).

## Facts the tools rely on (checked on the gate folders)
- Pair completion order = the log's `Finished game K` order (not the PGN write order). fastchess stops at the first
  crossing pair (13/13 replayed gates: crossing pair = printed pair count) and ABORTS partner games in flight: a
  single game in a round is legal only then (at most `concurrency` of them).
- Errors (exit 2, no verdict): other singles, 3 games in a round, colour / player mismatches, result token != Result
  tag, PlyCount != counted moves, malformed tags, NUL bytes, a file ending inside a game.
- RUN_INFO.json / RESULT.md carry a UTF-8 BOM; folder names can be stale (read the players from RUN_INFO / the log);
  PGN move comments carry the mover's score; UHO starts can be Black to move.
- The lock rejects placement-only FENs (`info string invalid FEN`): screens send six-field FENs and fail on that line.

## Numbers (RESULTS.md has the sources)
- Per concurrency slot 108-124 games/h in every setting; 10+0.1 game 28.4 s (8moves_v3) / 32.7 s (UHO). Threads=2
  conc 4 = 431-502 games/h; Threads=1 conc 8 = 993 games/h.
- Idle between gates: median 94 s (post-gate work ~29 s + pre-gate bench ~56 s); 1.25 % of the time; five gaps
  > 30 min (empty / paused queue) dominate.
- Adjudication is off in every gate; fishtest-like rules would save ~11-14 % of engine time but change 12-52 results
  per gate (crew decision, report only). Book loading 0.09-1.34 s: not worth a change.
- pregate_screen on the lock: PASS in 58 s (pins d11-d22, perft, 20-FEN smoke, WAC 55/60 at 100k nodes).
