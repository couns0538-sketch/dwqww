# IDEA_SOURCE — S49 PC speed check under gate load (tool only)

- **The job**: Sol's S49 spec, `F:\opus_scratch\sol_inventory_17aa0cae.json` `jobs[]` id S49 ("PC speed check that
  works under gate load (Sol, tool only)"): `pc_speed_ci_<date>.ps1`, PowerShell 7, interleaved ABBA, one bench
  call per slot, >= 40 pairs, Idle, ONE logical core not used by the gate manifest and never cores 0-3 (refuse if
  none free), A/A control pairs, median + bootstrap 95% CI, per-slot load and temperature, abort above 90 C. Sol
  never started it (no S49 files on `17aa0cae`).
- **Method sources** (general techniques, own code):
  - paired ABBA ordering against linear drift;
  - A/A controls for a noise floor;
  - the percentile bootstrap (Efron 1979) of the median;
  - CPU-time rate measurement of a pinned, Idle-priority process (Windows `ProcessorAffinity` / `PriorityClass`,
    .NET `System.Diagnostics.Process`).
- **PC conventions taken from the PC's own scripts** (read only, no code copied):
  - the gate driver's affinity `0xFFF0 (CPUs 4-15)` in `RUN_INFO.json`;
  - "affinity and priority set before any command is sent" from QA's `qa_checks_abba.ps1` method note;
  - the HWiNFO sensor CSV column `CPU (Tctl/Tdie)` that `conc7_watch.ps1` also reads.
- **Synthetic slowdown**: own test-only patch (`test_only_synthetic_slowdown.patch`), a busy wait of N% of the bench
  search time, so wall and CPU time grow by N% with the node count unchanged.
- **Tests**: own (`tests/test_pc_speed_ci.py`, `tests/mutation_check_s49.py`, the script's `-SelfTest`).
- No code from any other engine or project.
