# IDEA_SOURCE — sol_S48fix

- Fix-up list S48-1..4: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 3 (QA, 2026-10-27).
- Base code: Sol's `forge_sol_S48_gate_guard_20261026.py` (17aa0cae, sha256 21713b32…), read only; v2 is a new file.
- Exact fastchess 1.8.2 GSPRT (normalized pentanomial model, constrained-MLE LLR as in fishtest `LLRcalc`) and the
  stopping-rule simulator: copied verbatim from the Opus S44 tool (`forge_sol_S44_elo_vs_epochs.py`, working-tree
  snapshot sha256 306f435c…, 2026-10-27), which reproduces the printed figures of 23 real gates.
- Gate data: the PC's own `RESULT.md` / `RUN_INFO.json` (read-only copies), interpretation rules from the
  `forge-gate-stats` skill (stale folder names, null concurrency in old RUN_INFO, never pool conc 5 with 7/8).
- Hash/TC normalization and the git-path guard are original, standard-library code. No external project code.
