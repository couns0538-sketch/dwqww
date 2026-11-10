# AUDIT: existing tuners, receipts and parameter inventory (S1)

Everything here was gathered read-only. Evidence ids are git commits on github.com/couns0538-sketch/dwqww, paths on this PC, or files in this pack.

## 1. combo29 identity and lineage
| Item | Value | Evidence |
|---|---|---|
| Lock exe | `forge_clang_combo29_trial_w6.exe`. MD5 c0051c99695f48bf93272d96fe7548c3. SHA256 e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e. | `evidence/FREEZE.json` (also matches `locks\lock_combo29_clang_trial_w6_20261108` and the build output) |
| Build | clang 23.1.5 (llvm-mingw-20261104), ThinLTO, frontend instrumentation PGO. Recipe `clang_build.ps1`, sha256 1fd87517…. Workload 1d52720a…. Profdata c5d97fc7…. | `RUN_RECEIPT.json`, `build.log` (frozen copies under `out\freeze\parent`) |
| Source parent | `all31_m29\source_snapshot`, 20 files, manifest sha256 3389cfe3…. Every file was verified at freeze. | `evidence/FREEZE.json` |
| Lineage | AL1 s198 lock tree (git 294dbed3) → trial_w6 `src_w6` (8 files differ; the six speed switches are `#define … 0` in source and set with `-D` at build) → combo29 snapshot (only `board.hpp`, `board.cpp` and `search.cpp` differ from `src_w6`). Per QA's gate0415 `PLAN.json`, feature mask 29 = KING_LINES + SEE_HOIST + MOVE_EQ32 + Clang_PGO. | blob comparison, S1 log |
| Nearest committed relative | 7ce10a05 "parent P: trial_w6 source" on `opus-finny-cache-20261107` and `opus-smp-layout-20261107`. Its `.cpp` files equal `src_w6`; four headers differ only in switch defaults. | `git rev-parse 7ce10a05:<path>` vs `git hash-object` |
| **Git source commit of combo29** | **BLOCKED.** combo29's `search.cpp` 2ffe2556, `board.cpp` c6a2cfe5 and `board.hpp` 9a94c15f are referenced by none of the 2850 commits on the 410 refs. This was checked with `git rev-list --all --objects --missing=print`, trees only and no fetch. The build parent is the hash-bound snapshot. | S1 log; INC-01 explains why `--find-object` is not used |

## 2. Existing tuners and match runners
| Tool | Where | What it does | Tuning evidence | Disposition here |
|---|---|---|---|---|
| R9 `r9_spsa.py` + report, SVG, sim test | `opus-r9-spsa` 73eb280a `opus_r9/tuner/` | Fishtest-style SPSA counted in game pairs. Stateless `seed:k` ±1 deltas. Clamp and round plus/minus; fastchess `-repeat` pairs. Append-only `iterations.jsonl`, `history.csv`, `games/`. Resumes after the last complete record and skips a torn last line. Load governor and STOP file. | stc1: 832 pairs / 1664 games at 8+0.08, 16 params, 0 of 16 beyond 2σ. Sanity runs: LmrQuietDivisor 120→138.6 (z +1.27); LmrQuietBase 250→189.3 (z +1.48). | **Base for this pack**: imported verbatim, then extended |
| O30 `tune_spsa.py` + `.ps1` | `opus-30h-20261103` 32bb47cb `opus_30h/b/` | Port of R9. Adds CPU pinning, disk floors, a named stop event and `fixed_options`. Review nit E-006: plus and minus can round to the same integer and pure noise still moves θ. | stc8_main: 184 of 1800 pairs, 8 params; only SeeQuietMultiplier beyond 2σ (24→28, z +2.11). Exe tuned184 with switch `O30Tuned`; never gated. | Ideas only (pinning, disk floors); E-006 fixed here |
| R3 `tools/spsa` (`opus_spsa*.py`, 30 tests) | `opus-r3-spsa` a5f4f696 | Offline SPSA with a UCI value check before each session, time-loss counting, CSV state. | **No real tuning session.** Dry runs only: 3 iterations × 1 pair at 0.5+0.005 on LmrQuietBase, NullMoveMarginBase and RfpMargin; 2 × 2 pairs at 20000 nodes. It found that QsSeeMargin has plateaus of 100. | Evidence only |
| `tools/match` (`run_match.py`, `run_hourly_sprt.py`, `windows_validate.py`, `pgn_stats.py`) | AL1 lineage, e.g. 73eb280a | Reproducible fastchess match and SPRT support for CI. | Not a tuner | Not reused; the confirmation runner is independent by design |

## 3. Gate and tuning receipts relevant to the families
- `FORGE_RESULTS.md` (forge_push, read-only) has no gate with any `Razor*` or `Qs*` option. Gated search-option lines touch other families: Hindsight, HistMalusPct=125, timepack Tm*, ReSearchAdjust/FiftyDamp, TmOppClock, TmScoreLoss.
- `CR_PASS_*combo29*` (in flight on combo29): ContHistSumBase, QuietMalusDecay, ReSearchAdjust, NoisySeeHistDiv, TtCutChildDepth, Syzygy. None of the deepres patches touch the razoring or qsearch lines.
- `opus-sol-S10fix` "improving_razor" was a razoring **mechanism** experiment, rejected at screening. It is not a tuning of the RazorBase/RazorMultiplier/RazorDepth values.
- `fable52-search-gap-20261109` is an analysis pack ("NO QUALIFIED GAP") with one ETC probe tool and no engine patch.

## 4. Parameter inventory (combo29 `forge::tune`, 51 scalars, all already UCI options because the lock is built with `FORGE_EXPOSE_TUNABLES=1`)
Status key: **T** = tuned by SPSA games (unmerged), **P** = family partly tuned, **U** = untuned, **F** = in-flight CR candidate on the same mechanism, **D** = dead at lock values, **X** = excluded (timing job / time manager).
| Family | Scalars (lock value) | Status | Evidence |
|---|---|---|---|
| LMR | LmrQuietBase 85, LmrQuietDivisor 220, LmrNoisyBase 10, LmrNoisyDivisor 340, LmrHistoryDivisor 6000, LmrCutoffThreshold 3 (+ literals tuned by R9/O30) | T (merely unmerged) + F (ReSearchAdjust, ContHistSumBase) | R9 stc1, sanity2/3; O30 stc8 |
| Null move | NullMoveMinDepth 3, NullMoveBase 3, NullMoveDepthDivisor 3, NullMoveEvalDivisor 200 (+ literal NmpEvalBase 180) | P (NmpEvalBase tuned) | R9, O30 |
| RFP | RfpDepth 8, RfpMargin 72, RfpImproving 40 | P (RfpMargin tuned) | R9, O30 |
| **Razoring** | **RazorDepth 2, RazorBase 150, RazorMultiplier 350** | **U** | none in R9/O30/R3/gates; S10 was a mechanism, not values |
| Quiet futility | FutilityDepth 7, FutilityBase 100, FutilityMultiplier 110 | T | R9 |
| LMP | LmpBase 4 | U (fallback candidate) | none |
| History pruning | HistoryPruneDepth 3, HistoryPruneMultiplier 2048 | U (fallback; history magnitudes move under the in-flight QuietMalusDecay) | none |
| SEE quiet / noisy | SeeQuietMultiplier 24 / SeeNoisyMultiplier 150 | T / U+F (NoisySeeHistDiv) | R9, O30 / CR_PASS |
| Singular | SingularDepth 7, SingularMargin 2 (+ literal double margin 24) | P | R9, O30 |
| IIR | IirDepth 4 | U (single scalar) | none |
| ProbCut | ProbcutDepth 5, ProbcutMargin 180 | P | R9 |
| **Qsearch pruning** | **QsFutilityMargin 160, QsSeeMargin 40** | **U** (R3 advertised QsFutilityMargin; no games) | R3-4 REPORT |
| Aspiration | AspirationDelta 18 | T | R9 |
| History bonus | HistoryBonusQuadratic 20, HistoryBonusLinear 48, HistoryBonusMax 2048 | U+F (QuietMalusDecay, ContHistSumBase) | CR_PASS |
| Check extension | CheckExtensionDepth 2 | U (single scalar) | none |
| Correction | MaterialCorrectionWeight 100 | U (single scalar) | none |
| Capture futility | CaptureFutilityBase 0, CaptureFutilityMultiplier 250, CaptureFutilityDepth 6 | D (base 0 disables the branch; enabling it is a mechanism change) | `search.cpp:1335` |
| Fail-low continuation | FailLowContinuationBonus 0 | D | `search.cpp:1475` |
| Time manager | Tm* (10 scalars) | X (TM gates exist; the timing job is not ours to disturb) | FORGE_RESULTS timepack, TmOppClock, TmScoreLoss |

## 5. Sensitivity on combo29 itself (bench nodes; not games, not Elo)
Measured on the frozen lock exe copy at Idle on CPUs 12–15. Raw output: `out\qual\sensitivity\combo29_lock_sensitivity_d13_d16.json`.
| Setting | d13 nodes (Δ%) | d16 nodes (Δ%) |
|---|---|---|
| defaults | 862329 (pin) | 3024920 (pin) |
| RazorBase 135 / 165 | 900054 (+4.37) / 791308 (−8.24) | 3540287 (+17.04) / 2737869 (−9.49) |
| RazorMultiplier 315 / 385 | 903506 (+4.78) / 763968 (−11.41) | 3306008 (+9.29) / 2521661 (−16.64) |
| QsFutilityMargin 144 / 176 | 793331 (−8.00) / 877190 (+1.72) | 2713052 (−10.31) / 3071864 (+1.55) |
| QsSeeMargin 0 / 99 / 100 / 199 / 200 | 862329 / 862329 / 824643 / 824643 / 1075589 | 3024920 / 3024920 / 3287728 / 3287728 / 3452465 |
| RazorDepth 1 / 3 | 772683 (−10.40) / 938799 (+8.87) | 2743991 (−9.29) / 3062325 (+1.24) |
| back to defaults | 862329 | 3024920 |

The d13 values equal R3's AL1 measurements exactly; combo29 is node-identical to AL1 at defaults. **QsSeeMargin is a step function.** SEE values are multiples of 100, so each band 0–99, 100–199, … searches an identical tree, and small SPSA steps carry no signal. It is therefore handled as an optional discrete level, as described in PLAN.md.
