---
name: forge-gate-summary
description: Summarise and check Forge fastchess gates from their own folders (F:\forge_push\gate_*) with opus_r15/tools/gate_summary.py - W/D/L, pentanomial, Elo +/- and nElo, the exact fastchess 1.8.2 GSPRT LLR, time forfeits / illegal moves / disconnects, games per hour, a reproduction check of the printed result block, and --watch for a running gate (games per 10 minutes, mean depth and seconds per move per engine) to see that it still plays at normal speed. Use for any gate result question, before citing a gate, and before / during own CPU work next to a running gate.
---

# Gate summaries (R15 tool, 2026-11-03)

Tool: `D:\o15\wt\opus_r15\tools\gate_summary.py` (branch `opus-r15-20261103`), standard library only. Read-only on the
gate folders. Older statistics background: forge-gate-stats.

## Use
```
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
nice -n 19 $PY -I -B gate_summary.py F:/forge_push/gate_X [more folders] [--json out.json]
nice -n 19 $PY -I -B gate_summary.py --all F:/forge_push [--match uho]
nice -n 19 $PY -I -B gate_summary.py F:/forge_push/<running gate> --watch --last-min 60
```
Exit 0 = every gate summarised and its log games reproduce the printed block; 1 = a mismatch / unreadable gate; a
folder without a PGN is skipped (D:\grok-pc-data\forge_push has the older layout without PGNs).

## Facts learned (checked on all 62 F: gates with a PGN, 2026-11-03: W/D/L, Ptnml, Elo, error and LLR all exact)
- fastchess prints W / D / L and Games over COMPLETE pairs only in pentanomial mode (gate68: 1392 logged games, 2 of
  unfinished pairs, printed 1390).
- The LLR uses the reference SPRT code (LLRcalc): empty pentanomial cells count 1e-3, the t-value MLE starts from the uniform pdf and
  takes at most 10 steps (an early H0 at Elo -86 printed -2.99; the fully converged MLE gives -3.68).
- The PGN's write order is not the printing order: reproduce a printed block from the log's "Finished game K (A vs B):
  result {reason}" lines before it (pair = games 2r-1 and 2r). Games in flight at an SPRT stop reach the PGN later.
- PGN Termination values seen: "normal", "time forfeit"; log reasons: "X mates", "Draw by 3-fold repetition",
  "Draw by fifty moves rule", "Draw by insufficient mating material", "Draw by stalemate",
  "X loses on time (1099ms overrun)". Folder names are stale - the opponent comes from the result line / RUN_INFO.
- Normal speed on 2026-11-03 (conc 4, Threads 2, 10+0.1, CPUs 4-15): 77-87 games per 10 min (~497 games/h),
  mean depth ~22.6 and ~0.225 s per move for both engines.
