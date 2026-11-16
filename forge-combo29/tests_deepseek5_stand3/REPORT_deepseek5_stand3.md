# REPORT_deepseek5_stand3 (deepseek5, 2026-11-16 UTC) — does a search leave anything behind?

**What was asked (the standing job S3):** 200 UHO positions, `go nodes 20000`, three protocols — (a) a
fresh process per position, run twice; (b) ONE process with `ucinewgame` before each position; (c) one
process WITHOUT `ucinewgame` — and the comparison of every line (bestmove, score, nodes).

**The answer in three lines:**
- (a) fresh vs fresh: **0 of 200 positions differ** (the search is reproducible process to process).
- (b) one process with `ucinewgame` vs the fresh runs: **0 of 200 differ** — bestmove, score and nodes
  identical on every position: **`ucinewgame` returns the engine to the fresh-process state exactly.**
- (c) one process WITHOUT `ucinewgame`: **199 of 200 differ** — the control that proves the comparison
  sees a difference (the example, position 2: fresh cp46 at 19,000 nodes; bare cp77 at 9,341 — the
  leftover state changes both the score and the search's size).

**How:** one build (the job-26/28 RegretTop count build, exe sha 59106ede… — its count-only mode with
no option set = the plain engine's tree), one thread, Hash 16, OwnBook false; the runs' rows are
`fresh1.rows`, `fresh2.rows`, `newgame1.rows`, `bare1.rows` in this folder (one line per position:
index|bestmove|score|nodes). The comparison command (committed: `compare_stand3.py`) prints the three
lines above; the search driver is `stand3_run.py` (committed).

**The known-answer form:** (a)'s zero is the reproducibility identity; (b)'s zero against (a) is THE
answer (nothing crosses `ucinewgame`); (c)'s 199 is the sensitivity control — without it, (a)/(b)'s
zeros could be a blind comparison.

**What I did not do:** set G (the standing job's text said 200 UHO positions; G was not asked);
the per-position breakdown of (c)'s one NON-differing position (position 1 — the first search of the
bare process naturally matches the fresh one).

**What I am not sure about:** nothing in the counts; the one caveat is that the build carries my
counters (the count-only mode's identity was verified in job 26 and re-verified here by the anchor
property of (a)).

**Model:** the runtime serving this Cursor cloud-agent run identifies as GLM, trained by Z.ai; the
agent name for this work is deepseek5.
**times:** see stamps.txt.
