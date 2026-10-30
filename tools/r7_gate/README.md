# Gate throughput tools (R7 J4)

All read the PC's gate files read-only (copy a PGN to scratch first) or run their own fastchess in a scratch folder.

| tool | what it measures |
|---|---|
| `pgn_rate.py <games.pgn>` | games/hour of a fastchess run from its PGN tags (GameStartTime/EndTime/Duration), game length, terminations |
| `adjudication_sim.py <games.pgn> --rate R` | replays every game's per-move score/time comments under several resign/draw rule sets: share adjudicated, results changed, mean game time, projected games/hour, pentanomial Elo before/after |
| `cpu_survey.ps1 [-Seconds 20]` | CPU per group (gate, NNUE trainer, self-play, Grok Bot, this job, other) from process CPU-time deltas |
| `mini_gate.sh <out> <exe> <rounds> <srand> <start> [flags]` | a conc-3 copy of the PC gate (same fastchess, options, tc, book) for a flag set; prints games/hour |
| `book_load_time.py <fastchess> <exe> <out> <book> pgn|epd` | time from fastchess start to the first game (opening book indexing) |
| `pgn_book_to_epd.py <book.pgn> <out.epd>` | EPD copy of a PGN book (loses the move history; for the load-time comparison only) |

Recipes:
```
python -I -B tools/r7_gate/pgn_rate.py F:/opus_scratch/<copy>.pgn --last-minutes 60
python -I -B tools/r7_gate/adjudication_sim.py F:/opus_scratch/<copy>.pgn --rate <games/hour>
powershell -NoProfile -ExecutionPolicy Bypass -File tools/r7_gate/cpu_survey.ps1 -Seconds 20
bash tools/r7_gate/mini_gate.sh F:/opus_scratch/r7/j4/<name> <exe> 20 1100276691 1 -resign movecount=3 score=600 twosided=true
```
