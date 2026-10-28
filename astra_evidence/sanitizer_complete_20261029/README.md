# Complete sanitizer qualification — 2026-10-29

**Final: sanitizer qualification PASS under the unchanged repository policy.** All 56 registered tests completed in one uninterrupted run: 55 PASS and forge_tests with exactly the four pre-existing tactical diagnostics. Raw CTest exit 8; policy gate exit 0. Zero ASan/UBSan/leak reports. This is not a claim of 56/56 raw CTest passes.

The owner requested a complete passing sanitizer run after the20-minute review. Earlier hard instructions retained exactly four known forge_tests FAIL lines. This run therefore reports two separate outcomes: raw CTest, and the repository's existing sanitizer acceptance policy. It never labels known tactical failures as raw CTest passes.

The exact policy is Git blob `53b04af3ba00f77ba56e16ebdd9916ded628cc8a` from `opus_round1/ci/check_known_failures.py`, copied unmodified into the run directory. It requires those exact four diagnostics and rejects additional failing tests or sanitizer reports. The new controller additionally requires every registered test ID/name to have a normal completed result; five incomplete/invalid synthetic controls are rejected. No test expectations or engine sources changed.

Full Release serial testing previously yielded55/56PASS. The initial complete ASan attempt was interrupted by a tool-server disconnection after18completedtests; the separate remaining38-test run passed38/38. Those streams remain in ../final_review/. They are not reconstructed into a single run. The present uninterrupted_run executes all56tests anew, serially, with the repository's600-second timeout, leak detection, abort-on-ASan-error and halt-on-UBSan-error.

All ASan/UBSan targets built successfully with GCC14.2, RelWithDebInfo, h256, strict FP and the original source. Instrumentation proof records34ASan and13UBSan runtime references. The build is frozen. The original inventory captured 68 command paths. Final review classified four as generated output logs (their changes are expected), and verified all 64 actual binary/script/fixture inputs unchanged. Both the initial inventory and its correction are preserved. This test process uses its own session to preserve evidence across interactive tool connection loss; it is monitored until completion.

Reproduce with a fresh output directory:

```sh
cmake -S . -B /path/to/qualified-asan-build \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER=/usr/bin/g++-14 \
  -DFORGE_ENABLE_SANITIZERS=ON \
  '-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256'
cmake --build /path/to/qualified-asan-build -j2
python3 -B astra_evidence/sanitizer_complete_20261029/run_complete.py \
  --repo "$PWD" --build /path/to/qualified-asan-build \
  --ctest /path/to/ctest --output /new/qualification/directory
```

No speed or Elo claim. Known WAC001 tactical miss and shallow underpromotion move-preference failures remain visible; the independent factual audit is in ../final_review/tactical_failure_audit/.

IDEA_SOURCE: Owner complete-sanitizer request and Forge's existing CI policy; original completeness and recovery wrapper.

The final run took 732.91 seconds in CTest. Complete original output, including passing-test streams, is in uninterrupted_run/LastTest.log. The raw result, acceptance decision, and machine-readable receipt are in ctest.log, policy_gate.log, and receipt.json. Four additional generated test logs/reports are preserved in per_test_outputs/.
