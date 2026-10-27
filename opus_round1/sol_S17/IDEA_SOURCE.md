# IDEA_SOURCE (S17 game-group split + dedupe manifest)

IDEA_SOURCE: group-wise (game-level) train/validation splitting so that no game contributes positions to both sides,
as specified in Sol's S17 task (`forge_sol_all_jobs_inventory_20261026.json`, job S17). Ideas only; no engine code.

- Sol's prepared tool, tests, README and report (`sol_v1/`, unchanged; branch `forge/sol-pack31-20261025` @
  `17aa0cae`, `validation/forge_sol_pack31_20261025/forge_sol_S17_prepared_20261026`); v2 changes 5 lines for Windows.
- Group rule, tripwire and position identity: Sol's Job D / S16 code (pinned dependencies, unchanged).
- The independent audit and the real-window builder are original code (numpy as a library from the PC's read-only venv).
