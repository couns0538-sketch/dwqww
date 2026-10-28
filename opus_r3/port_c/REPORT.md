# R3-1 port C: S-A2 NnueInt16 + S-A4 H512 merged into the R3 stack — DONE

(Text of the sub-agent's report, saved by the main session; the agent could not write REPORT.md.)

**Branch `opus-r3-port-c`:** `2432670b` (opus-r3-cifix) + `97b01454` (merge opus-sol-SA2 `1c1a44ed`) + `a4fa82bb` (merge opus-sol-SA4 `2e3a36f2`) + `2bd88569` (this folder, `[skip ci]`). Work by a sub-agent of the main session. No gate was run; no Elo or speed claims. Machine exclusive: no.

## Design decision: NnueInt16 is a build switch
- **Why:** R3-1 requires the default PC build to be byte-identical to a PC build of `2432670b`. SA2's always-compiled option changes the binary even when it is off: accumulator entries grow from 2 to 4 KiB and the NNUE kernels get bigger. opus-offguard measured this off-path cost at −0.40% / −0.46% CPU NPS (d16 / d20).
- **What:** I followed S13's `FORGE_S13_TT_CHILD_PREFETCH` pattern and the stack's own `FORGE_NNUE_O2`.
  - New CMake option `FORGE_NNUE_INT16`, default OFF (PC recipe: `-DFORGE_NNUE_INT16=1`).
  - It compiles SA2's integer path and UCI `NnueInt16` (check, default false).
  - Without the switch the option does not exist; the CTest `nnue_int16_uci_absent` checks this.
- **Coverage in every CMake configuration:**
  - The int16 test targets compile `src/nnue.cpp`, `board.cpp` and `bitboard.cpp` themselves, with the switch and the configuration's `FORGE_NNUE_O2` state.
  - The UCI regression runs on `forge_int16` (the core's sources and settings plus the switch), or on `forge` itself in a `-DFORGE_NNUE_INT16=ON` configuration.
- **v2 nets:** NnueInt16 applies to the compiled-in network only; a v2 net keeps its float path (same precedent as S41 NetScale). This is tested below.

## Merges, conflicts and resolutions

**SA2 merge**
- `include/forge/nnue.hpp` (conflict): O2's `#if` around the 64-byte aligned `values` is kept. `integer_values`, `integer` and the int16 API follow, under `#if FORGE_NNUE_INT16`.
- `src/nnue.cpp` (conflict in the include list): union of the v2 loader's headers and SA2's. SA2's four headers are included only with the switch.
  - SA2's three hooks auto-merged at the top of `refresh` / `update` / `evaluate`. They run before both accumulator variants (AL1 loops and O2 kernels), which stay untouched.
  - The hooks and `#include "nnue_int16.inc"` are wrapped in the switch.
- `src/uci.cpp` (conflict): the stack's whole option list and setoption chain are kept.
  - `NnueInt16` is listed right after `UseNNUE`. Its handler sits between `IntendedThreefold` and `UseNNUE`.
  - Both are under the switch (`tools/resolve_uci_sa2.py`).
- `CMakeLists.txt` (conflict): union; every stack target and test is kept. The int16 targets are rebuilt on the helper `forge_nnue_int16_test_sources`, plus `forge_core_int16` / `forge_int16` and `nnue_int16_uci_absent`. The `FORGE_NNUE_INT16` option sits after the stack's switches.
- `src/nnue_int16.inc` (no conflict): kernel choice is now `FORGE_NNUE_AVX2` instead of `__AVX2__`. They are the same except under O2's `FORGE_NNUE_FORCE_SCALAR`, where `<immintrin.h>` is not included.
- `tests/nnue_int16_tests.cpp` gets an `#error` without the switch.
- `tools/nnue_int16_regression.py` gets an `--absent` mode.
- `opus_round1/ci/run_ci.sh` auto-merged with identical content.

**SA4 merge**
- `src/nnue.cpp` (conflict): O2's kernel macros are kept, followed by SA4's `#if defined(FORGE_NNUE_WEIGHTS) … #elif __has_include("nnue_weights.inc")`.
- `CMakeLists.txt` (conflict): `FORGE_NNUE_WEIGHTS_FILE` goes after the switches.
  - The H512 test target uses the int16 helper plus its own generated net and `FORGE_NNUE_HIDDEN=512`.
  - Both H256 int16 tests take `FORGE_NNUE_WEIGHTS_FILE` when it is set (`tools/resolve_cmake_sa4.py`).

**Scope:** `git diff 2432670b a4fa82bb` touches only `CMakeLists.txt`, `nnue.hpp`, `nnue.cpp` (one changed `#if` line, the rest additions) and `uci.cpp`, plus the new SA2/SA4 files and `opus_round1/sol_SA2|SA4`. The SA2/SA4 job folders are byte-identical to their branches and their SHA256SUMS verify.

## Acceptance
Logs are in `opus_r3/port_c/logs/`.

| line | result | evidence |
|---|---|---|
| Default PC build byte-identical to a PC build of 2432670b | PASS: 4 differing bytes (PE timestamp 137-138, checksum 217-218). With `FORGE_NNUE_O2=1` vs base O2: 3 bytes | `byte_identity_default_and_o2.log` |
| Default / O2 PC builds = lock pins | ALL OK (bench d11..d22, perft5, kiwipete), FMA 0 | `uci_check_full_final_default.log`, `uci_check_full_final_o2.log`, `build_final_*.log` |
| Switch-on builds (O2 off/on), NnueInt16 off | ALL OK, FMA 0 | `uci_check_full_final_int16.log`, `uci_check_full_final_int16_o2.log` |
| NnueInt16 ON reproduces SA2's pins, both O2 states | d11 330610, d13 858175, d16 2760596, d20 9564588, d22 21638970 in both | `bench_on_final_int16.log`, `bench_on_final_int16_o2.log` |
| NnueInt16 ON parity, both O2 states | 9/9 dumps byte-identical to SA2's reference dump `ba76ee81…` (and SA4's): H256 AVX2+scalar × O2 off/on; H512 smoke AVX2/scalar/AVX2+O2 `408d7a54…`; H512 split AVX2 × O2 off/on `6389c132…`. 0 build warnings | `parity_dumps.log` |
| SA2 UCI regression / absent check | all checks pass on both switch builds; `--absent` passes on the default and O2 builds | `nnue_int16_regression_*.log` |
| v2 non-interference | lock replica r1 + NnueInt16 on → 312866 / 862329 / 3024920 (v2 float tree), both O2 states | `bench_v2replica_int16on_final_int16*.log` |
| H512 per SA4's recipe | split float 312866/862329/3043192/13215819, ON 330610/858175/2760596/9564588; smoke float 343099/834267/2755018/11577336, ON 359658/890711/3140646/10867508. All match in both O2 states and in a float-only build; 5 exes, FMA 0 | `bench_h512.log`, `build_h512.log` |
| v2 code at H512 | H512 r1 replica (hidden 512) loads and searches the H512 float tree (also with NnueInt16 on, O2 off/on); an H256 v2 net is refused ("hidden size 256 != engine hidden size 512", exit status 2) | `v2_h512.log` |
| Full CMake build, all targets, JOBS=1 + full ctest | build OK (106 steps). Run 1: only forge_tests (4 known) + `hard_deadline_regression` (timing flake, 3/3 on rerun). Runs 2-3: forge_tests + `forge_smp_tests` (timing flake, 4/5 on rerun) | `cmake_default*.log`, `ctest_default*.log`, `known_failures_default*.log`, `ctest_*_rerun_default.log` |
| Flakes are not the port | `forge`, `forge_smp_tests`, `forge_debughooks`, `forge_tests`, `forge_nnue_parity_tests` are byte-identical to the main session's base CMake build of 2432670b (4 PE bytes); PC at 100% CPU | `cmake_binaries_vs_base.log` |
| CMake `-DFORGE_NNUE_O2=ON` / `INT16` / `O2+INT16`, NNUE+UCI tests | 13/13, 12/12, 12/12 pass | `ctest_o2.log`, `ctest_int16.log`, `ctest_o2_int16.log`, `cmake_*.summary.log` |
| No new warnings | 7 unique warnings in every configuration, identical to the base set; 0 in touched files | `cmake_default_warnings_vs_base.log`, `cmake_variants_warnings.log` |
| Planted bugs | control passes (40,691 checks); 6/6 mutants caught (SA2's 5 + a stale-tag port mutant), O2 off and on | `mutation_port_c_o2off.log`, `mutation_port_c_o2on.log` |
| CI | run 40570018288 success: release ALL OK + FMA 0, `forge` sha256 `3a9e13bf…` identical to base run 40565363595; known-failure check PASS in release/ASan/TSan; TSan 0 reports | `ci_40570018288_summary.log`, `ci_40570018288/` |

## Findings
- **The int16 path coexists with O2 without touching its kernels.** The hooks run before either accumulator variant, so float accumulators stay bit-identical; the parity dumps match SA2's in both states.
- **NnueInt16 is a no-op for v2 nets.** The v2 path never reads `integer`. The root refresh still computes integer accumulators, but `valid=false` makes the v2 path recompute.
- **The CI TSan job took 23 min vs 11.5 min on the base run.** Every unchanged test was about 2× slower on that runner. The new tests add 111 s there (`ci_tsan_test_times_vs_base.log`).

## Left / UNVERIFIED
- **No NPS measured** (no speed claim). The switch build's off-path cost is presumably SA2's (−0.4%, offguard), not re-measured.
- **Trainer `--weight-clip`** merged unchanged and not re-run.
- **Local ctest timing flakes** under 100% CPU on base-identical binaries; the quiet CI runner was clean.
- **H512 v2** checked only with an r1 replica (1 bucket, no threats or pawn pairs).
- **NnueInt16 + v2 net is silent, not fail-loud.** Making it fail-loud would be a follow-up.
- **SA2-folder tools need the switch now.** `opus_round1/sol_SA2/nnue_int16_dump.cpp`, `mutation_check_sa2.py` and the SA2/SA4 README build lines need `-DFORGE_NNUE_INT16=1` on the stack. The folders are left unchanged; the updated recipes are in this folder's `tools/run_parity.sh` and `mutation_check_port_c.py`.

Machine exclusive: no.

R3-1 port C | opus-r3-port-c | DONE (2bd88569) | SA2 NnueInt16 (behind new build switch FORGE_NNUE_INT16) + SA4 H512 flags merged; default exe byte-identical to 2432670b; ON pins and parity reproduce in both O2 states; H512 checks pass; opus-ci 40570018288 green
