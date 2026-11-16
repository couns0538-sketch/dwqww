# REPORT_deepseek5_cross1 (deepseek5, 2026-11-16 UTC) — cross-check of glmflash5's job-10 step-1 tree numbers

**What was checked:** glmflash5's job-10 step-1 rows (its report section 2) — the tree of `on80`
(LmrDeeperShallower true + LmrDeeperBase 80) and of `flat` (LmrDeeperShallower true + LmrShallowerBase 8 +
LmrShallowerDepthMul 0), depth 12, 200 positions, against the switch-off baseline.

**Its numbers:** on80 sum 11,775,205, first-3 23,624 / 37,960 / 52,840; flat sum 11,102,401,
first-3 19,141 / 26,354 / 43,866.

**My remake:** MY build (the job-17 arms exe, sha256 6e75f50248586731… — a DIFFERENT binary from its
fb9152ca… PATCHED, same base+kimi5 source), MY harness (ds5_job12_nodes.py: one process, ucinewgame +
isready before every go, setoption verified by effect), MY set file (set_O.epd = the first 200 lines of
UHO_Lichess_4852_v1.epd — the same set as its kimi5 first200.fens: its own "on" row 11,254,768 and
first-3 26,641/30,896/68,347 equal mine exactly, which pins the set identity).

**Result: AGREE — every number identical to the node.**

| quantity | glmflash5 job 10 | deepseek5 cross1 | agree |
|---|---|---|---|
| on80 sum | 11,775,205 | 11,775,205 | yes |
| on80 first-3 | 23,624 / 37,960 / 52,840 | 23,624 / 37,960 / 52,840 | yes |
| flat sum | 11,102,401 | 11,102,401 | yes |
| flat first-3 | 19,141 / 26,354 / 43,866 | 19,141 / 26,354 / 43,866 | yes |

Raw output: `ds5j17_cross1.txt` (the two harness lines + the first-3 rows pasted); the rows and their
.meta files are committed beside this report. UTC stamp: `stamps.txt` (2026-11-16T09:0xZ).

**Why it matters:** two independent builds, two independent harnesses, one set — the tree numbers that
feed the Elo discussion (M4's margin 80, M5's flat reshape) are measured the same by both helpers.
Nothing to reconcile.

Model: deepseek5 (GLM flash).
