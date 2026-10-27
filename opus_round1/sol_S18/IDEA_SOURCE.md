# IDEA_SOURCE (S18 Filter threshold sweep + small ablation)

- Job spec: Sol inventory `jobs[]` id S18 (`validation/forge_sol_pack31_20261025/forge_sol_all_jobs_recovery_20261026/forge_sol_all_jobs_inventory_20261026.json`, branch `forge/sol-pack31-20261025` head 17aa0cae). It asks for a result-vs-score disagreement filter sweep (none/200/300/400/500) and small CPU H256 runs scored on one unfiltered holdout.
- Filter ("D filter"): Sol's own S16 tool `forge_sol_datafilter_v2_20261026.py` (sha256 5dd0c009...) on the S16 codec `forge_sol_datafilter_20261025.py` (6ccf78c8...). It is used unchanged.
- Training recipe: the f006 recipe as Sol recovered it (`forge_sol_S09_f006_recipe_20261026.json`, 97b4a2a8...), with the 2-epoch smoke exception that Sol preregistered. The trainer is the lock-archive v3b trainer (5cebba4d...) and is used unchanged.
- Controller: Sol's v4 confirmed-exit remaining4 controller (643e71ea...) is the design source. The Windows port is our own code. No engine code and no new engine option: this is a tool/smoke job.
- No third-party (GPL) code was copied.
