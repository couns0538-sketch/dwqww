# IDEA_SOURCE (S16 overlap check)

IDEA_SOURCE: hold-out leakage checking by exact position identity and by game, as planned in Sol's S16 task
(`forge_sol_all_jobs_inventory_20261026.json`, job S16) and his Job D filter. Ideas only; no other engine's code.

- Sol's v2 filter, runners, tests and README (`sol_v2/`, unchanged, branch `forge/sol-pack31-20261025` @ `17aa0cae`,
  `validation/forge_sol_pack31_20261025/forge_sol_after_S09_continuation_20261026/forge_sol_S16_delivery_ready_20261026`);
  v3 changes only 4 lines for Windows.
- Position identity (board32 + side to move) and the conservative ordered-text game rule with the 20-in-100
  interleaving tripwire: Sol's Job D filter (`forge_sol_datafilter_20261025.py`, sha256 `6ccf78c8…7ab3`).
- FPOS/FHCE layout: Sol's reader (same file) and the PC's `fen2bin` output (`.pos.info`).
- The scanner's 64-bit candidate key uses the public splitmix64 finalizer constants (Steele, Lea, Flood,
  "Fast splittable pseudorandom number generators", OOPSLA 2014); every candidate is confirmed byte for byte.
- numpy (BSD) is used as a library from the PC's existing read-only venv; nothing is installed.
