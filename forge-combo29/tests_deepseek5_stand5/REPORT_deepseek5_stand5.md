# REPORT_deepseek5_stand5 (deepseek5, 2026-11-16 UTC) — 300 self-play games at 5,000 nodes, no adjudication

**What was asked (the standing job S5):** 300 self-play games at `go nodes 5000` by my own runner (the
moves always sent from the game's START position), played to the end with no adjudication; the endings
counted first; every game replayed with python-chess: every move legal, and every draw the runner
claimed is one python-chess agrees with.

**The answer:**
- **Endings of the 300 games:** mate **174**, repetition **72**, fifty-move **28**, insufficient
  material **17**, the 300-ply cap **8**, stalemate **1** — no illegal moves, no crashes, no
  disconnects, no lost bestmoves.
- **The replay:** **0 games with an illegal move; 0 games whose re-derived ending differs from the
  runner's** — every one of the 300 games' moves is legal in python-chess, and every ending (including
  all 72 repetition claims and all 28 fifty-move claims) re-derives exactly.
- The protocol that made it honest: `position fen <start> moves <all moves>` before EVERY move (the
  job-15 lesson), the endings derived from the python-chess board alone, and the actual third
  occurrence (`is_repetition(3)`) as the repetition rule.

**How:** the runner is `stand5_run.py` (committed); the 300 start positions = the first 200 lines of
the UHO book + the first 100 of set G (the same sets the session has used); the exe = the job-26/28
RegretTop count build (sha 59106ede… — its count-only mode with no option set = the plain engine).
The rows: `games.rows` (one line per game: index|start fen|ending|plies|final fen|the moves); the
replay: `replay.txt`.

**What I did not do:** the strength side (the same-engine self-play says nothing about Elo); the
opening book's fairness (each opening used once, no colour pairing — the S5 spec's shape).

**What I am not sure about:** nothing in the counts; the cap's 8 games (the 300-ply limit) are the
runner's own rule, not the game's — they would have continued.

**Model:** the runtime serving this Cursor cloud-agent run identifies as GLM, trained by Z.ai; the
agent name for this work is deepseek5.
**times:** see stamps.txt.
