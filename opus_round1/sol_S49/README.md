# S49 — PC speed check that works under gate load (`pc_speed_ci_20261027.ps1`, tool only)

> **Running it on the PC (anything other than `-PlanOnly` or `-SelfTest`) needs a separate crew vote.**
> On the PC today the script refuses to run: the gate driver pins fastchess and its engines to `0xFFF0` (CPUs 4-15),
> and cores 0-3 are never used, so no logical core is free (see "PC today" below).

## What it does
- **Two exes.** It compares exe B against exe A with interleaved ABBA pairs: pair *i* runs A,B when *i* is even
  and B,A when it is odd. There are at least 40 pairs, at each depth of `-Depths` (default 16, 20).
- **Noise floor.** After every `-ControlEvery` (4) test pairs it runs one A/A control pair (A vs a byte copy A2).
- **One bench per slot.** Each slot starts a fresh engine process and sets it to priority **Idle** on the chosen
  core before any command is sent. It runs one `bench <d>` call and reads nodes and CPU time while the process
  is still alive, then sends `quit`.
- **Metric.** CPU-time NPS by default (`-Metric cpu`); `-Metric wall` uses the engine's own NPS.
- **One logical core.** The core must not be used by a gate, and cores 0-3 are never used. It refuses (exit 3)
  if no core is free. The core is the highest free one, or `-Core N` if N is free. Used cores are the union of:
  - the affinity of the live `fastchess` processes and of their child engines (read-only queries);
  - the `affinity` field of gate `RUN_INFO.json` files changed in the last `-RunInfoMaxAgeHours` (48) under
    `-RunInfoRoot` (`D:\grok-pc-data\forge_push`);
  - any per-gate `affinity` / `cores` / `cpu_affinity` field in the gate manifest `-Manifest` (none today).
- **Per slot it logs** whole-machine and chosen-core load, CPU temperature and free RAM.
  - Temperature: the HWiNFO sensor CSV (`CPU (Tctl/Tdie)`, newest row, at most 120 s old), else ACPI, else Linux
    sysfs.
  - It aborts (exit 4) above `-MaxTempC` (90) or below `-MinFreeRamGB` (6). Without any temperature source it
    refuses unless `-AllowNoTemperature` (box only).
- **Statistics.** Per depth: the median of the per-pair ratios B/A with a percentile bootstrap 95% CI (10,000
  resamples, seed 20261027), and the same for the A/A control pairs. It checks that node counts match.
- **Speed rule.** The PC rule (CI lower bound ≥ +2% at every depth, `-RuleLowerBound 1.02`) is printed as
  PASS or "not met".
- **Read-only except `-OutDir`.** `-OutDir` must be new or empty and outside `forge_push`, `selfplay_out`,
  `forge_nnue_train` and `C:\Users\Administrator\grok-pc`. The exes are copied into `<OutDir>/bin` first.
  Outputs: `plan.json`, `slots.csv`, `summary.json`, `summary.md`.

## Use
```powershell
# what it would do (core choice and probes only; no engine started)
pwsh -NoProfile -File pc_speed_ci_20261027.ps1 -PlanOnly -OutDir F:\opus_scratch\s49\plan
# the real check (PC: only after a crew vote, and only if -PlanOnly shows a free core)
pwsh -NoProfile -File pc_speed_ci_20261027.ps1 -ExeA lock.exe -ExeB cand.exe -Depths 16,20 -Pairs 40 -OutDir F:\opus_scratch\s49\run1 -Label "cand vs lock"
# a quiet box without gates (labelled box-only; core 0 kept free there)
pwsh -NoProfile -File pc_speed_ci_20261027.ps1 -ExeA lock -ExeB cand -Depths 13,16 -Pairs 40 -BoxOnly -ReservedCores 0 -AllowNoTemperature -OutDir out
# tests
pwsh -NoProfile -File pc_speed_ci_20261027.ps1 -SelfTest
python -I -B tests/test_pc_speed_ci.py
python -I -B tests/mutation_check_s49.py --work <new dir>
```
`-BoxOnly` refuses on any machine where a gate runs (a live `fastchess` process or a recent `RUN_INFO.json`).
Without `-BoxOnly`, `-ReservedCores` must include 0-3. `-FixtureLiveMask` / `-FixtureCoreCount` are test inputs and
only work with `-PlanOnly`.

## PC today (2026-10-27)
- `-PlanOnly` on the PC: the live fastchess process and the latest RUN_INFO both show `0xFFF0 (CPUs 4-15)`, and
  cores 0-3 are reserved, so the result is **REFUSED: no free core** (exit 3; `logs/step2_plan_live.log`).
- `-BoxOnly` on the PC is refused too.
- The probes work read-only: CPU 83.4 °C from the HWiNFO CSV, free RAM 11.8 GB.
- To use the tool on the PC, the gate driver would have to leave one core out of its mask (for example
  `0xBFF0`, freeing core 14) for the duration of a check. That is a crew decision, and it costs gate capacity.

## Box validation (GitHub runner, `.github/workflows/opus-sol-s49-box.yml`, `ci_s49_box.sh`)
- Builds the lock and a **test-only** synthetic 5% slowdown copy (`test_only_synthetic_slowdown.patch`,
  `-DFORGE_S49_SYNTHETIC_SLOWDOWN_PCT=5`: `bench` burns 5% of its search time; nodes unchanged; never in `src/`).
- Then runs the self-test, the Python tests, an **A/A run** (the CI must contain 1.00) and an **A/B run** against
  the slowdown (the CI must exclude 1.00). All labelled box-only.
