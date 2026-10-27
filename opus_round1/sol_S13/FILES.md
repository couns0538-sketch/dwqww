# FILES — opus_round1/sol_S13 (job S13, branch opus-sol-S13)

Engine/test changes (vs the AL1 s198 lock tree 294dbed) are in `patch.diff`: Sol's four production files,
ported verbatim in 8557326e (CMakeLists.txt option block, include/forge/search.hpp, src/search.cpp,
src/uci.cpp, all inside `#ifdef FORGE_S13_TT_CHILD_PREFETCH`), plus tests/tt_prefetch_probe_tests.cpp and
its 9 CMake lines (cb6f8789). No other source file changes. All PC evidence was produced from cb6f8789
(tracked sources unchanged in 4b8b99cf, which only adds tools and CI). REPORT.md is written by the main session.

| file | bytes | what |
|---|---:|---|
| IDEA_SOURCE.md | 1837 | idea source (Sol's cc3efc96 patch and notes) |
| patch.diff | 17605 | `git diff 294dbed HEAD` without opus_round1/, .github/ |
| run_s13_evidence.sh | 7895 | PC evidence driver: steps build, identity, ctest, negative, codegen |
| checker_rereview_controls.py | 3564 | 8 extra controls against Sol's unchanged source contract (S13-1 re-review) |
| ci_s13.sh | 5894 | Linux CI with the switch on: release (default vs lock, identity, ctest, NPS), asan, tsan |
| uci_threads_session.py | 1859 | TSan job: Threads 2/4 UCI session with TtChildPrefetch on, waits for bestmove |
| uci_check_opt.py | 2913 | copy from opus-sol-S11 86a5d560: AL1 identity with `--set` / `--expect-option` |
| nps_onoff.py | 5370 | copy from opus-sol-S11 86a5d560: same-binary NPS OFF vs ON (ABBA, median, CI) |
| nps_ab.py | 4162 | verbatim copy of opus-O3 opus_round1/O3/nps_ab.py (c7eb247a) |
| codegen_compare.sh | 2135 | verbatim copy of opus-O3 opus_round1/O3/codegen_compare.sh (c7eb247a) |
| FILES.md | — | this index |
| SHA256SUMS | — | sha256 of every file here except itself |

Evidence archives (`evidence/`, one per step; `tar -xzf` gives `<step>/...`):

| archive | bytes | contents |
|---|---:|---|
| s13_step1_build.tar.gz | 462 | build_pc_default.log, build_pc_switch_on.log (sha256, FMA 0) |
| s13_step2_identity.tar.gz | 1252 | identity_default_vs_lock.log (cmp -l: 5 bytes = PE timestamp + checksum; disassembly identical; AL1 identity), identity_switch_on_{off,on}.log, uci_session_switch_on.log |
| s13_step3_checker.tar.gz | 1557 | checker_rereview_run.log: verbatim-port check (first attempt compared CRLF scratch output and is superseded in the same log), Sol's 10 tests, contract, 8 extra controls |
| s13_step4_ctest.tar.gz | 3161 | cmake_build_{default,switch_on}.log, ctest_*.log, ctest_known_*.log, probe_{default,switch_on}.log (with link-map member lists) |
| s13_step5_negative.tar.gz | 969 | negative_diagnostic.log: both new prefetch statements removed (option kept): probe FAILS 2/8 coverage checks |
| s13_step6_codegen.tar.gz | 788 | codegen_lock_vs_s13on.log: per-function table, prefetch instruction counts |
| s13_step7_nps_pc.tar.gz | 1360 | nps_onoff_pc.log: switch-on exe, TtChildPrefetch OFF vs ON, 5 runs, d16 d20; machine exclusive: no |
| s13_step8_ci.tar.gz | 9814 | opus-ci run 40481055829 (default build) and opus-sol-s13-ci run 40481055934 (switch on: release, asan, tsan) logs |

Environment note: the Windows PC clock runs about 9 h ahead of UTC (GitHub server time 09:32 = PC 18:32 on
2026-10-27), so `date -u` stamps in the PC logs are PC clock; CI logs carry runner time.
