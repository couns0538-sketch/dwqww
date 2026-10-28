# R3-3 idea sources

No engine idea is new in this job; it turns the merged features into gate entries.

- **Gate format and settings:** the live PC runner `forge_queue.ps1 v3-6day r7` (Build-Args, Static-ArgCheck,
  Void-Check, Run-Gate, H1-Confirm; read from a copy) and its manifest `forge_gates.json` (entries such as G121
  RefutLmr and G125 e48f042 as templates), `6_gate/GATE_RULES.md` and `6_gate/pc_examples/qa_add_gate_f042.ps1` of the
  AL1 lock package.
- **srand discipline:** `forge_push\autonomy\common_autonomy.ps1` (Used-Srands, Fresh-Srand range
  300000000 + uint32 mod 1700000000, Max-Start + 3000), OPUS_TEST_PLAN.md rule "fresh srand, never reused".
- **Per-feature facts:** the job REPORTs (`opus_round1/<JOB>/REPORT.md`, and `sol_S12`, `sol_SA2`, `sol_SA4` on their
  branches), R3-1's cross-checks in `opus_r3/R3-1/logs/`.
- **SPRT model:** forge-gate-stats skill (normalized GSPRT, t = nElo · sqrt(2) · ln10 / 800, bounds ±ln 19); the
  normal approximation of the LLR as a random walk is the textbook SPRT approximation (Wald), used here only to
  estimate decision rates, labelled "approx model".
- **Ranking:** own judgement from the REPORTs' measured speed, node changes and risks, plus related PC ledger rows
  (FORGE_RESULTS.csv); no external source.
