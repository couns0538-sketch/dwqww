# IDEA_SOURCE — sol_S33fix

- Fix-up S33-1: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 3 (QA, 2026-10-27).
- Inputs: Sol's S33 advice pages, plan table (md + csv) and planner documentation (17aa0cae, read only).
- Fastchess-printed gate figures: the PC's gate `RESULT.md` files (read-only copies).
- Exact fastchess 1.8.2 GSPRT: functions copied verbatim from the Opus S44 tool (`forge_sol_S44_elo_vs_epochs.py`,
  snapshot sha256 306f435c…), which reproduces the printed LLR of 23 real gates; tilting as in Sol's planner.
- Label/figure checker and renderer: original, standard library only.
