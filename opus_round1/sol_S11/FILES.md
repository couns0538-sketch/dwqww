# FILES — opus_round1/sol_S11 (job S11, branch opus-sol-S11)

Engine/test changes (vs the AL1 s198 lock tree 294dbed) are in `patch.diff`: CMakeLists.txt,
include/forge/{material_key_table.hpp (new), search_options.hpp (new), search.hpp},
src/{search.cpp, search/options.inc (new), uci.cpp}, tests/material_key_tests.cpp (new).
Code commits: ad05f62b (option + table + test), faff1c46 (material_key kept inlined). All evidence below
was produced from faff1c46 (tracked sources unchanged in 86a5d560, which only adds tools and CI).
REPORT.md is written by the main session (sub-agents cannot write it).

| file | bytes | what |
|---|---:|---|
| IDEA_SOURCE.md | 1883 | idea source (Sol's S11 preparation, profile_notes reserve "material_key table-sum") |
| patch.diff | 24658 | `git diff 294dbed HEAD` without opus_round1/, .github/ |
| uci_check_opt.py | 2913 | AL1 identity (opus_round1/ci/uci_check.py) plus `--set Name=value` and `--expect-option` |
| build_pc_scalar_nnue.sh | 2911 | PC recipe with src/nnue.cpp on its scalar path (also Linux via GPP/ARCH/LINK_STATIC) |
| scalar_nnue_prelude.hpp | 817 | test-only forced include: undefines MinGW's _M_X64/_M_AMD64 for the scalar nnue.cpp |
| nps_onoff.py | 5370 | same-binary NPS of a check option, OFF vs ON, ABBA, median/mean/CI, node check |
| nps_ab.py | 4162 | verbatim copy of opus-O3 opus_round1/O3/nps_ab.py (c7eb247a): two-exe NPS A/B |
| codegen_compare.sh | 2135 | verbatim copy of opus-O3 opus_round1/O3/codegen_compare.sh (c7eb247a) |
| plant_bug.py | 1325 | plants mutant 1 (key relabelling) or 2 (two material classes merged) in a COPY |
| run_s11_evidence.sh | 6857 | PC evidence driver: steps build, identity, ctest, mutation, codegen |
| FILES.md | — | this index |
| SHA256SUMS | — | sha256 of every file here except itself |

Evidence archives (`evidence/`, one per step; `tar -xzf` gives `<step>/...`; all output of the step):

| archive | bytes | contents |
|---|---:|---|
| s11_step1_build.tar.gz | 7198 | build_pc.log (PC exe sha256, FMA 0), build_scalar_nnue.log (macros, FMA 0, packed/scalar counts), nnue_functions.dis (scalar exe forge::nnue:: disassembly) |
| s11_step2_identity.tar.gz | 827 | identity_{pc,scalar}_{off,on}.log (AL1 bench x5 + perft5 + kiwipete), identity_pc_standard_tool.log |
| s11_step3_ctest.tar.gz | 2997 | cmake_build.log, ctest_release.log, ctest_known_release.log, material_key_tests_release.log |
| s11_step4_mutation.tar.gz | 1697 | mutation_check1.log (test FAILS 4/14; bench cannot see a relabelling), mutation_check2.log (ON bench MISMATCH, OFF exact) |
| s11_step5_codegen.tar.gz | 3121 | codegen_lock_vs_s11.log (per-function table, symbols, call sites, normalised diffs, new corrected_eval) |
| s11_step6_nps_pc.tar.gz | 2222 | nps_onoff_pc.log (same binary OFF vs ON, 5 runs, d16 d20), nps_ab_lock_vs_s11off_pc.log (10 runs); machine exclusive: no |
| s11_step7_ci.tar.gz | 6022 | opus-ci run 40478253767 (release identity, ctest/known for release, asan, tsan, build/configure logs) and opus-sol-s11-nps run 40478254153 (Linux identity off/on incl. scalar NNUE, NPS lock vs off, same-binary off vs on, 10 runs) |

Note: nps_onoff_pc.log was produced before nps_onoff.py gained the MACHINE_EXCLUSIVE header override
(default "no"); the measured part of the script is unchanged.
