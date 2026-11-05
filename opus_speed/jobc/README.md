# Job C - cut gate wall time (tools for the crew to review)

Scripts that help the SPRT / fastchess gate pipeline finish sooner WITHOUT changing what a gate means. Nothing here
touches the running queue, its config, the gate folders or the lock; every tool is read-only on the gate folders and
writes only the output files named on its command line (never overwriting an existing file). The binding crew vote
stays as it is: Threads=1, SPRT [0,5] normalized Elo, alpha = beta = 0.05, pentanomial, caps 3000 / 4000 / 6000,
UNPROVEN at the cap, one extension only when the Elo is positive. The projections and audits below are planning
input, never a stop rule.

All tools run with the venv python: `PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe; $PY -I -B tools/<tool>.py ...`
(standard library + numpy for llr_project.py + python-chess for the move checks). Paths with forward slashes.
Shared code: `tools/gatelib.py` (strict PGN / log / RUN_INFO / RESULT.md readers, pairing rules, the pentanomial Elo /
nElo and the exact fastchess 1.8.2 GSPRT LLR reused from opus_r15/tools/gate_summary.py).

| tool | one line | example |
|---|---|---|
| `tools/gate_replay.py` | Replays a finished gate from its PGN (+ RUN_INFO / config / log): pentanomial counts in pair-completion order, Elo / nElo, the exact LLR after every pair, the verdict and the pair where it was reached; compares with RESULT.md / FORGE_RESULTS.csv. Truncated / corrupt / unpaired PGN -> exit 2, error, NO verdict. | `$PY -I -B tools/gate_replay.py F:/forge_push/gate_sf26bundle14_vs_AL1 --results-csv D:/grok-pc-data/forge_push/FORGE_RESULTS.csv [--series s.csv] [--json r.json] [--verify-moves]` |
| `tools/llr_project.py` | From current pentanomial counts (or a gate folder's last log block): seeded simulation of the exact GSPRT to the cap -> P(H1 / H0 before the cap), P(no decision), games to a decision. Planning only (queue ordering). | `$PY -I -B tools/llr_project.py --ptnml "30 686 1509 744 31" --bounds 0 10 --cap-games 6000 --paths 1000 --seed 1` or `--gate F:/forge_push/<gate>` |
| `tools/queue_throughput.py` | Games per hour per gate (PGN / log / RUN_INFO times), per-slot rate, slot overhead, setup time, idle gap to the next gate; groups by (threads, concurrency, book), never pooled. | `$PY -I -B tools/queue_throughput.py --roots F:/forge_push D:/grok-pc-data/forge_push --last 30 --md t.md --json t.json` |
| `tools/adjudication_audit.py` | Adjudication / book / TC / thread settings each gate used (config.json, RUN_INFO argv), how the games ended, plies and engine seconds per game, and a simulation of fastchess draw / resign / maxmoves rules on the PGN comments: games ended early, plies and seconds saved, result disagreements. Report only. | `$PY -I -B tools/adjudication_audit.py F:/forge_push/gate_X F:/forge_push/gate_Y --md a.md --json a.json` or `--all F:/forge_push --match uho` |
| `tools/book_load_check.py` | Times the opening books (copies under the scratch folder): raw read, python parse, PGN -> EPD conversion, and fastchess's own indexing (A/B launch with a non-existent engine, no game). Measure only. | `$PY -I -B tools/book_load_check.py --tmp F:/ospd/jobc/tmp --json b.json` |
| `tools/pregate_screen.py` | Cheap screens before any game: PE header, uciok, option list (vs a reference exe), isready, bench pins at pure defaults, perft 5 pins, 20-position `go movetime 200` smoke with a python-chess legality check (six-field FENs; any `info string invalid FEN` line is a FAIL), WAC subset at fixed nodes, quit. Exit 0 PASS / 1 FAIL / 3 SLOW. `--fen-selftest` injects one placement-only FEN to show the failure path. | `$PY -I -B tools/pregate_screen.py --exe CAND.exe --ref-exe LOCK.exe --wac <wac300.epd> [--opt Name=Value] [--pins d11=...,d13=...] --json p.json` |
| `tools/concurrency_plan.py` | Math only: games/h for given core counts at Threads=1 from the measured seconds per game and slot overhead of finished gates; hours to each cap; the physical-vs-logical-core caveat. | `$PY -I -B tools/concurrency_plan.py --from-throughput t.json --cores 4 6 8 12 --caps 3000 4000 6000` |
| `tests/run_tests.py` | (a) replay of 13 finished gates vs their recorded verdict / LLR, (b) 9 deliberate-failure copies x with/without log -> exit 2 and no verdict, (c) `--verify-moves`, (d) the LLR / Elo formulas against every FORGE_RESULTS.csv row. | `$PY -I -B tests/run_tests.py [--quick] --tmp F:/ospd/jobc/tmp --out F:/ospd/jobc/out` |

## Facts the tools rely on (checked on the gate folders, 2026-11-05)
- Pair completion order = the order of the log's `Finished game K` lines (pair = games 2r-1, 2r of round r; the PGN's
  write order is not the completion order). The printed block counts the pairs completed before it; pairs in flight
  at an SPRT stop finish later (gate72 confirm: 2 such games). The verdict pair in every replayed gate equals the
  printed pair count, so fastchess stopped at the first crossing pair.
- At an SPRT stop fastchess ABORTS the partner games still in flight: they have a `Started game` line, no
  `Finished game` line and are absent from the PGN (gate68: games 1391 and 1393). A single game in a round is
  therefore legitimate only when the match stopped by SPRT and the partner was started but never finished; at most
  `concurrency` such singles. Every other single, a round with 3 games, swapped-colour or player mismatches, a
  result token that differs from the Result tag, a PlyCount that differs from the counted moves, a malformed tag
  line, NUL bytes or a file that ends inside a game are errors: exit 2, no verdict.
- PGN move comments `{score/depth time, tl=...}` carry the MOVER's score (checked: +M1 at the mating move). UHO
  gates start from an EPD position with either side to move (PGN `FEN` tag): the adjudication simulation and the
  move numbers honour it.
- RUN_INFO.json / RESULT.md are UTF-8 with BOM (read with utf-8-sig). Folder names can be stale: the opponent and
  the candidate are taken from RUN_INFO / the log. Time stamps are the PC wall clock; the PGN zone label is ignored.
- The lock rejects a placement-only FEN with `info string invalid FEN: FEN must contain six fields` and keeps its
  old position: the screen sends six-field FENs only and fails on any such line.
- The PGN tags EngineWhiteAuthor / EngineBlackAuthor and the UCI `id author` line are dropped at parse time and never
  reach an output file.

## Limits
- gate_replay.py needs the gate's own log for the exact completion order; without it the PGN GameEndTime (1 s
  resolution) orders the pairs and singles are refused.
- llr_project.py assumes the future pairs follow the current counts (Dirichlet posterior or plug-in); early in a
  gate the projection is wide. It is an ordering aid, not a stop rule. At `--step 1` it needs about 1 min per
  1000 remaining pairs with 1000 paths on two Idle CPUs; `--step 5` is 5x faster (a simulated stop can then be
  late by up to 4 pairs).
- `results/` holds copies of the small output files that RESULTS.md cites (the scratch originals stay under
  `F:/ospd/jobc/out/`; the PGN copies of the failure tests and the book copies under `F:/ospd/jobc/tmp/`).
- pregate_screen.py runs ONE engine at a time on the caller's CPU mask / priority (CPUs 0-1 at Idle in this job);
  its times are not speed measurements. A hung engine is killed (it is the tool's own child process).
- adjudication_audit.py simulates the rules on the recorded scores; a rule that had been active would also have
  changed the later moves, so the saved plies / seconds are an upper bound of a projection.
- book_load_check.py measures on copies; fastchess with a non-existent engine indexes the book and then exits.
