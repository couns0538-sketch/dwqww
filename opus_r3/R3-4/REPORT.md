# R3-4 SPSA tuning tool (`tools/spsa/opus_spsa*.py`) and 20 advertised search constants — DONE

Job R3-4 of the R3 pack: an offline SPSA tuner (Python, fastchess), the 20 most important search constants as UCI options with identical defaults, and a dry-run self-test at a very short time control with at most 2 threads. No real tuning session was run.

- **Branch:** `opus-r3-spsa` @ `8ac43ed2`, built on `2432670b` with these commits:
  - `af37dffe`: engine change.
  - `1ad40dd5`: merge of stack `2047348a`; conflict in `src/uci.cpp` resolved.
  - `704da5e3`: the tool, CTest entries, the list fix, evidence.
  - `e55dc21a`: evidence.
  - `c61e98d3`: merge of stack `330237f3`; conflict in `CMakeLists.txt` resolved.
  - `415e6eb0` and `8ac43ed2`: evidence.
- **Engine diff vs `330237f3`:** 6 files, +74/−7.
  - `include/forge/search_tune.hpp`: 2 externs and the `AdvertisedParameters` list.
  - `src/search/tune.inc`: 2 tunables and 2 table rows.
  - `src/search/alphabeta.inc` and `include/forge/corr_margins.hpp`: the null-move margin reads the new tunables.
  - `src/uci.cpp`: the option listing.
  - `CMakeLists.txt`: 2 CTest entries.
- **Tool:** `tools/spsa/`, 8 files. **Evidence:** `opus_r3/R3-4/`.

## Acceptance
| line | result | evidence |
|---|---|---|
| 1. 20 constants (LMR, null move, RFP, futility, SEE, aspiration), with reasons | **DONE**. LMR 6: LmrQuietBase, LmrQuietDivisor, LmrNoisyBase, LmrNoisyDivisor, LmrHistoryDivisor, LmrCutoffThreshold. Null move 5: NullMoveBase, NullMoveDepthDivisor, NullMoveEvalDivisor, NullMoveMarginDepth (new), NullMoveMarginBase (new). RFP 3: RfpMargin, RfpImproving, RfpDepth. Futility 3: FutilityBase, FutilityMultiplier, QsFutilityMargin. SEE 2: SeeQuietMultiplier, SeeNoisyMultiplier. Aspiration 1: AspirationDelta. Chosen for mechanism reach, a gradient SPSA can measure (bench-node scan: every one of the 20 changes the tree, from 0.9% to 23.4% for a ±10% step) and the null-move literal. QsSeeMargin is excluded (finding 1). | `tools/spsa/README.md` "Why these 20"; `logs/07_sensitivity_d13_final.log`, `logs/07c_qsseemargin_steps_d13.log` |
| Listed as spin options in every build (default = current value), the rest unlisted | **PASS**. The release `uci` reply has 51 option lines (31 + 20). The engine test checks exactly these 20, defaults equal to the config's start, same ranges, and that `setoption` then `uci` shows the new value. Control: the same test fails on the base exe. FORGE_EXPOSE_TUNABLES build: 95 lines, all 64 tunables listed once, identity ALL OK. | `logs/04_*`, `04c`, `04d`, `10*`, `10c` |
| Literal turned into a tunable, identical default | **DONE**. `beta - 24 * depth + 180` now reads `NullMoveMarginDepth` 24 and `NullMoveMarginBase` 180 in all eight alphabeta.inc instances (`corr_margins::null_move_threshold` too). The new globals are defined before the AL1 block, so every AL1 tunable keeps its address. | diff; `logs/05d` |
| Defaults keep bench/perft identical | **PASS**. `uci_check --full` ALL OK on the final merged build (bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690) and on every earlier build. FMA 0, 0 warnings (box recipe). CI release identity ALL OK with g++-14. | `logs/03c`, `03`, `03b`, `14c` |
| objdump of the search functions before/after | **DONE**. Default `Worker::search` keeps its address (0x140022300 vs 330237f3), its size and 2550 instructions. 12 normalised lines differ: the null-move test (two `lea` with the immediates become `imul`/`add` reading the two globals) and two swapped bool stack slots. `qsearch`, root search, `MovePicker::next`, `see_ge` and NNUE: 0 normalised differences (moved by 64 bytes, alignment kept). Other instances differ by 12–110 lines, except `search_cm_ce_cu_body` (CorrMargins+CorrExt+CuckooRep, register re-allocation): 729 lines. The QsSeeMargin→LmrCutoffThreshold list fix left the search code byte-identical. | `logs/05d`, `05`, `05b`, `05c` |
| Advisory ABBA CPU-time NPS A/B | **DONE (advisory)**. Against 2047348a, 10 runs each: d16 +5.28% [+0.60, +9.97], d20 +0.49% [−2.10, +3.08]. A/A control (same exe twice): d16 −1.02% [−7.08, +5.05]. No slowdown is visible above the noise; nodes matched in every run. Machine exclusive: no. | `logs/06*` |
| 2. `tools/spsa/opus_spsa.py` + helpers | **DONE**. Spall gains (a_k = a/(A+k+1)^0.602, c_k = c/(k+1)^0.101) with per-parameter c_end/r_end, fishtest's update, engine units, integer rounding at match time (deterministic or randomized) and clamping. Mini-matches through fastchess, W/L/D and pentanomial parsed and cross-checked against the per-game lines. Resumable `state.json` plus one CSV row per iteration, config JSON, and `--dry-run`, `--plan`, `--status`, `--synthetic`. Child processes run at Idle in a Windows job object, and the whole fastchess tree is killed on timeout. | `tools/spsa/` |
| 3a. Pure-Python unit test, in CTest, passing on CI Linux | **PASS**. 30/30 tests on Python 3.10 and 3.14, including the exact expected step 2·a_k·∇f and convergence on a synthetic objective. `opus_spsa_tests` and `opus_spsa_engine_options` pass locally and on CI release, ASan and TSan. | `logs/10*`, `13*`, `14*` |
| Planted bugs | **PASS**. 16/16 caught (update sign, schedule, perturbation, rounding, resume RNG, parsing cross-checks, job-object kill, CSV repair, fingerprint, theta update, engine default and list against the config); the clean copy passes. | `logs/12b` (on 704da5e3), `12` |
| 3b. Dry run at a very short TC, ≤ 2 threads, 2–3 iterations on 2–3 params, restart resumes | **PASS**. 0.5+0.005, concurrency 2, 3 params, 3 iterations × 1 pair: 2 iterations, clean stop, then the restart logged "resume at iteration 2/3" and finished. CSV rows 0–2 written once each; the last row has c_k = c_end and a_k = r_end·c_end². Repeated with the final engine (stop after 1, resume): same perturbations, deterministic. | `logs/08b–08f`, `08i`, `08_dryrun_dirs.tar.gz` |
| Nodes form and priority (extra) | **PASS**. 20000 nodes per move, 2 iterations × 2 pairs at concurrency 2; games finished out of order and the pair cross-check still held. fastchess and all 4 engines were Idle (base priority 4) in every sample. | `logs/08g`, `08h` |
| 4. README | **DONE**. How to run a real session, the example config for the 20 params, TC and game counts (pilot 4,000 games; full 40,000 games at 8+0.08, about 32 h on 8 slots, an estimate), and the table default/min/max/c_end/c_0/r_end. | `tools/spsa/README.md`, `opus_spsa_forge20.json` |
| Full local CMake build + ctest before each push | **PASS**. Before the 330237f3 merge: 38/39, known-failure check PASS. After the merge: 45/47 — `forge_tests` with its 4 known lines, and `forge_smp_tests`, which the stack documents as load-sensitive on this PC (4/5 reruns pass, and it passes on CI). | `logs/11*`, `11e–g` |
| CI green | **PASS**. 40572768902 and 40576031293 succeeded (ASan attempt 2, see above). | `logs/13_ci.txt`, `14_ci2.txt` |
| R3-5 `uci_options_regression.py` on the final engine | **PASS**. 51 options and all 20 spins swept; bench unchanged after the sweep. | `logs/15` |

## Findings
1. **QsSeeMargin cannot be tuned with small SPSA steps.** SEE balances are multiples of 100 (`SeeValue` {100, 300, 300, 500, 900}), so every margin from 0 to 99 searches the identical tree. Bench d13 is 862329 nodes at 0, 40 and 99, 824643 at 100–199, and 1075589 at 200. It was left out; LmrCutoffThreshold (15.5% for ±1) took the slot.
2. **fastchess `-strict` stops the whole run at the first time forfeit.** This happened at 0.5+0.005 at Idle on the loaded PC: "Timeouts: 1", exit 1 (`logs/08a`). The tool therefore runs without `-strict` by default. Instead, before every session and resume it sets each tuned option and requires the engine to show the new value, and it counts time losses per iteration.
2b. **The CI ASan runner can hang in apt-get** (30 minutes in the Toolchain step of 40576031293 attempt 1). Re-running the failed job fixed it.
3. **CaptureFutilityMultiplier is dead** (0.00% node change), as S08-4 and S-A6 said.
4. **Codegen:** the default search keeps its placement. Only the instance that runs with CorrMargins+CorrExt+CuckooRep all on was re-allocated by GCC.
5. **Iterations are synchronous**, so the example config uses 8 pairs per iteration on 8 slots to keep the wait for the slowest game short.
6. **The stack tracks 8 `__pycache__/*.pyc` files**, which ctest runs rewrite (not touched here).

## Left / UNVERIFIED
- No real tuning session was run, by the spec. The c_end values are heuristics (5–10% of the default) that a pilot should confirm. No Elo or speed claim.
- NPS is advisory only (loaded PC, machine exclusive: no). Only fastchess 1.8.2 (f618e34) was used; CI runs the tool against a fake fastchess.
- The sensitivity scan measures tree size at bench d13, not strength.
- Machine exclusive: no.
