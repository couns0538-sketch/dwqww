# Forge Job C — explicit known-failure relabel, 20261025

Status: correctness/test-reporting change validated; ready for isolated publication. No engine source, evaluator, network, search, TT or move ordering change. No speed, strength or training claim. Job D has not started.

Patch: `forge_sol_knownfail_h256e12_20261025.patch`  
SHA256: `4ac98f92d45f67fae8aaa8067fe28c0fca36662b3688013105f738245ee55805`  
Diffstat: `tests/tests.cpp | 62 lines; 55 insertions(+), 7 deletions(-)`; exactly one path. Final tests.cpp SHA256 `f74c959f6a157605f24f63309f531a822f1462ef9cae4cf46afd5bfc4eaabff1`.

The original expected move/score expressions remain unchanged. Only the two exact documented horizon cases can print `KNOWN_FAILURE:`; ordinary failures still increment the fatal failure counter and exit1. Existing expected outcomes remain ordinary passes. Known labels describe guarded observed behavior; they do not validate network identity.

| Case | Original6.4.24 expectation retained | Lock observed and labelled | Reason / guard |
|---|---|---|---|
| WAC001 d12 | g3g6; score>=MateValue-3=31997 | f6h5;661cp; d12; matching nonempty PV | Documented evaluation horizon. Exact case/FEN/old expectations/depth/move/score/PV required. Original deeper-mate expectation not weakened globally. |
| Unrestricted white/mirrored promotion d1 | c7c8r/c2c1r; score>100; matching PV; d1 | c6d7/c3d2;642cp each; matching PV; d1 | Alternate winning king move at shallow depth. Exact alternatives, matching PV, d1 and score>100 required. Restricted rook-win and queen-stalemate checks are untouched. |

Historical old6.4.24 exact numeric mate score and exact numeric promotion scores are **UNVERIFIED**: supplied notes record only >=31997 and >100. These numbers were not invented or rerun. Current lock scores661/642/642 were actually reproduced in this job. The deeper-search and external-analysis explanations are documented handoff evidence, not newly reproduced analysis.

| Check | Result | Original evidence |
|---|---|---|
| Unfixed exact-lock forge_tests RED | PASS as negative control | Actualexit1, original four FAIL lines, no known labels; expected-known checker exits1 |
| Candidate exact-lock target GREEN | PASS | Actualexit0; exactly four explicit known labels; no FAIL lines; checker exits0 |
| Independent source review | PASS bounded review | `forge_sol_c_review_20261025.md`; no material source-contract defect |
| Eight independent compiled mutations | PASS | Each actualexit1 with ordinary FAIL: unrelated mate expectation; WAC known move; WAC661 guard; white/black alternate king moves; promotion PV/depth guards; null-pruning expectation |
| Full original14-command CTest harness | PASS |14/14,0 failed,8.12s, actualexit0; candidate forge_tests only substituted; other13 original commands/binaries/scripts reused |
| Clean patch to lock and lock+buffix | PASS | GNU patch --fuzz=0 dryrun and actual apply; no offsets/fuzz; candidate bytes identical |
| Candidate on original buffix runtime | PASS | Only original buffix search.cpp freshly compiled; original six other core TUs reused; exit0/four known/no FAIL; buffer searchMD5=9553f697fa7bed500f945bc247d70dbf |
| New engine/performance/ASan/Windows result | UNVERIFIED / not run | Test-only relabel; no engine code changed and no new release claim |

Build provenance: GCC14.2, C++20,O3,DNDEBUG,H256,-ffp-contract=off,-fno-fast-math,-march=znver5,-static,-pthread. To avoid duplicate closed engine compilation, candidate tests link the seven exact original-lock final Linux PGO objects from the previous completed compiler-only experiment; no JobA code/macro1 core is linked. All object/source/binary hashes and exact argv are retained. Buffix runtime replaces only search.o with an original supplied-buffix macro0 compilation and keeps the other six original objects. This is a compiler-object reuse choice, not a different source version.

The separate CTest harness copies the original14 test commands, substitutes the reviewed forge_tests executable and redirects two output-log destinations so original closed evidence is not overwritten. Its exact replacements and hashes are in `forge_sol_c_full_ctest_20261025/forge_sol_ctest_harness_changes_20261025.json`. No original CTest file or executable was modified.

Idea sources only: user's JobC contract; supplied `05_jobC/JOBC_CONTEXT_known_failures_20261025.md`, original `tests/tests.cpp`, and reviewed prior-art relabel design SHA256 e1144cb952e174740d56b346076890ef5d5f2032bfc7afdd9317f02e7b521d27. Implementation written independently; the prior idea of explicit behavior-specific known labels is reused, and WAC is tightened to exact661/depth/PV. No external engine code or tuned constants imported.

Evidence roots: `forge_sol_base_red_20261025/`, `forge_sol_candidate_green_20261025/`, `forge_sol_c_native_results_20261025.json`, each `forge_sol_c_<mutation>_20261025/` original source/build-command/build-log/run-log, `forge_sol_c_patch_results_20261025.json`, `forge_sol_c_full_ctest_20261025/`, and `forge_sol_c_buffix_runtime_20261025/`. No failed approaches deleted. No owned native job remains.

Next action: root publishes this separate C patch/report/evidence, verifies immutable public retrieval, then starts JobD. Do not combine C relabel with JobA feature patch or silently amend old failure evidence.
