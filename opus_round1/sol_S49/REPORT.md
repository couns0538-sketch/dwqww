# S49 [Sol leftover] PC speed check that works under gate load (tool only) — DONE

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2, item 30. The spec is Sol's inventory (`jobs[]` S49). Sol never started it: there are
no S49 files on `17aa0cae`. Work and results by a sub-agent; this report text is its hand-back.

Branch `opus-sol-S49` = `d4f4312` + `0d99f02` cherry-picked (`f734f690`) + these commits:
- `b971dcc0`: tool, tests, box CI;
- `deece38c`: Linux load-probe fix;
- `57701360`: list parameters + depth guard;
- `4fc7c153`, `4af19ce3`: evidence, FILES, `[skip ci]`;
- the REPORT commit `9b1f1e33`;
- `11d5ebf7`: Windows box CI (workflow `opus-sol-s49-box-windows`, MSYS2 static build, pwsh driver, verdict script);
- the Windows evidence commit.

**Tool only:** the engine diff vs `294dbed` is empty; the synthetic slowdown is a test-only patch applied only in
CI. Machine exclusive: **no**. On the PC only `-SelfTest` and `-PlanOnly` ran (no engine). **No speed claim.**

> Running it on the PC needs a separate crew vote (README). Today it refuses: the gate driver pins fastchess and its
> engines to `0xFFF0` (CPUs 4-15), and cores 0-3 are never used, so no core is free.

## Acceptance
| line | result | evidence |
|---|---|---|
| `pc_speed_ci_<date>.ps1`, PowerShell 7, read-only except its own output dir | **PASS** | `pc_speed_ci_20261027.ps1`; static test: every write goes under `-OutDir`, no kill/delete commands; refuses protected dirs (`tests/test_pc_speed_ci.py`) |
| interleaved ABBA, one bench call per slot, ≥ 40 pairs, Idle | **PASS** | 40 test pairs (A,B / B,A) + 10 A/A control pairs per depth; each slot is a fresh engine set to Idle on the chosen core before any command; box run: 400 slots, all affinity 0x8 |
| ONE logical core not used by the gate manifest, never 0-3, refuse if none | **PASS** | used cores = live fastchess + child-engine affinity, recent RUN_INFO `affinity`, manifest affinity fields; live PC: REFUSED (`logs/step2_plan_live.log`); fixtures cover every path (chosen 15 / 14 / 3, requested gate or reserved core refused, `-BoxOnly` refused where gates run) |
| A/A control pairs, median, bootstrap 95% CI | **PASS** | percentile bootstrap of the median, 10,000 resamples, fixed seed; control CIs contain 1 in both box runs |
| per-slot CPU load and temperature; abort above 90 °C | **PASS** | per slot: machine and core load, temperature, free RAM (`slots.csv` in `logs/s49_box_40517374833.tar.gz`); sources: HWiNFO CSV (PC, 82.5 °C read in `-PlanOnly`), ACPI, Linux sysfs (box 49.85 °C); aborts above `-MaxTempC 90` or below 6 GB RAM |
| an A/A run's CI contains 1.00 | **PASS** | box run 40517374833: d13 median 1.0000 CI 0.9767-1.0230; d16 median 1.0069 CI 1.0000-1.0077 (`logs/step5_box_ci_40517374833.log`) |
| synthetic ~5% slowdown gives a CI that excludes 1.00 (box run via pwsh, labelled box-only) | **PASS** | test-only `-DFORGE_S49_SYNTHETIC_SLOWDOWN_PCT=5`: d13 0.9551 CI 0.9388-0.9579; d16 0.9576 CI 0.9501-0.9659; nodes A = B; GitHub ubuntu-24.04 runner, pwsh 7.6.9, labelled box-only |
| static check: never pins a manifest core | **PASS** | `-SelfTest` (27 checks): one `ProcessorAffinity` assignment, from the mask set only after `Select-SafeCore`; exhaustive selection test |
| README says a PC run needs a crew vote | **PASS** | `README.md` |
| tests + planted bugs | **PASS** | tests 15/15 (`logs/step3_tests.log`); 14/14 mutants caught (`logs/step4_mutants.log`) |
| Windows bench-slot path end to end (box-only) | **PASS** | GitHub windows-2022 runner, run 40521059492 on `11d5ebf7`: CIM load probes, .NET affinity + Idle, 400 slots all on core 3 (`0x8`); A/A d13 1.0000 CI 1.0000-1.0000, d16 1.0000 CI 0.9868-1.0000 (controls contain 1); synthetic 5%: d13 0.9722 CI 0.9487-0.9733, d16 0.9576 CI 0.9498-0.9602, nodes A = B; verdict PASS (`logs/step6_box_windows_40521059492.log`) |
| CI | **PASS** | opus-sol-s49-box 40517374833 and opus-ci 40517374786 (both on `57701360`): success. The earlier box runs 40509722120 and 40510697858 failed on the two portability bugs below (logs kept in `logs/ci_attempt1/2`) |

## Findings
- **On the PC the check cannot run today.** Gates hold 4-15, and 0-3 are reserved (where training sits). Using it
  needs a crew decision to leave one core out of the gate mask (e.g. `0xBFF0` frees core 14), at some gate capacity.
- **The box runs caught two portability bugs.** Both are fixed and the failed attempts' logs are kept in
  `logs/ci_attempt1/2`:
  - PowerShell's comma binds tighter than `-` and broke the Linux load probe.
  - `pwsh -File … -Depths 13,16` bound "13,16" as 1316. The engine clamps bench to depth 64, which never finishes.
    Lists are now parsed explicitly, and depths outside 1..24 are refused before any engine starts.
- **CPU-time clock ticks quantize the ratios** (the d16 A/A lower bound is exactly 1.0000). Use d16/d20 for the +2%
  rule, as the spec says.
  - On Windows the tick is 15.625 ms: all 400 slot CPU times of the Windows run are multiples of it. A d13 slot
    (0.55 s) spans about 35 ticks, so one tick is 2.9% and the d13 A/A CI collapses to 1.0000-1.0000; at d16
    (1.76 s) one tick is 0.9%. The PC runs the same Windows clock, so d16/d20 apply there too.

## Left / UNVERIFIED
- A PC run needs a crew vote and a free core.
- The Windows bench-slot path end to end: **verified on a Windows runner** (box-only, section below). Still not run
  in a slot run: the HWiNFO temperature source (the runner VM has no sensor; it ran with `-AllowNoTemperature`;
  on the PC the probe read 82.5 °C in `-PlanOnly`) and the live gate-affinity scan with real gates (fixtures and
  the PC `-PlanOnly` only).
- No PC speed measurement; nothing claimed.

## Windows box run (follow-up, added by the main session)
Workflow `opus-sol-s49-box-windows`, run 40521059492 on `11d5ebf7`, success (`logs/step6_box_windows_40521059492.log`,
artifact `logs/s49_box_windows_40521059492.tar.gz`). The same push also ran the Linux box (40521059352) and opus-ci
(40521059609): both success.
- **Box:** GitHub windows-2022 runner, 4 logical CPUs (AMD EPYC 9V74), Windows Server 2022 (NT 10.0.20348), pwsh 7.6.8.
  Builds: MSYS2 UCRT64 g++ 16.2.0, static (`ci_s49_build_windows.sh`); lock `1ddd3547…`, test-only synthetic 5%
  slowdown `a443dbbe…`; both identity ALL OK (bench d11/13/16, perft5, kiwipete).
- **Tool checks on Windows:** `-SelfTest` 27 checks, 0 failures; Python tests 15/15 OK.
- **Plan:** no gate processes, reserved core 0, free 1-3 → core 3 (highest free core). Probes: CIM machine load 0-1%,
  free RAM 13 GB, temperature source none.
- **Slots:** 2 runs × 200 slots (40 test pairs + 10 control pairs per depth, d13 and d16). Every slot: a fresh process
  at Idle with affinity `0x8` (core 3) before any command; mean machine load 2%.

| run | depth | median B/A | 95% CI | A/A control median, CI | nodes A = B |
|---|---|---|---|---|---|
| A/A (lock vs lock) | d13 | 1.0000 | 1.0000-1.0000 | 1.0000, 0.9714-1.0147 | yes |
| A/A (lock vs lock) | d16 | 1.0000 | 0.9868-1.0000 | 1.0135, 0.9914-1.0270 | yes |
| synthetic 5% slowdown | d13 | 0.9722 | 0.9487-0.9733 | 0.9865, 0.9608-1.0294 | yes |
| synthetic 5% slowdown | d16 | 0.9576 | 0.9498-0.9602 | 0.9957, 0.9871-1.0090 | yes |

- **Verdict PASS** (`s49_box_verdict.py`): every A/A CI contains 1.00, and the 5% slowdown CI excludes 1.00 at both
  depths, below it. This closes the Windows half of the box validation; the Linux box (run 40517374833) gave the same
  picture.
- Box-only, labelled as such; nothing measured on the PC, no speed claim.
