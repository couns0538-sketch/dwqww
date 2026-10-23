# Corrected Linux test harness — source review

PASS source review; no current blocker. Exact runner3990a9b6, exporter e908b4b7 and PINS ce254980 match the supplied identities. Their unified diffs match the actual changes against the original reviewed scripts, and tool pins are unchanged.

The exporter verifies clean engine6e9622fd differs from baseline1ab50b2d only in the selected network and requires the input include to match that clean commit exactly. It reads only tests/tests.cpp from f4a1ed6b, verifies SHA6dec8511, and applies that one authorized test replacement after proving a pristine baseline export. The final file set must have exactly the selected weights and pinned test changes. No remaining test-commit tree or additional production change is exported.

The runner enforces and reports this exact scope. Its original exclusive evidence, process cleanup, strict flags, full14-test gates in Release and ASan/UBSan, and first observed new-network bench/repeat logic remain unchanged. The controlled test checks null-cutoff preparation, one try, one cutoff, two nodes, score0 and board/history restoration, rather than depending on a particular network reaching that branch during broad search. Separate runtime proof was not repeated here.

Root must bind the actual include/SHA invocation to its frozen chosen artifact. This review does not establish exports, builds, tests, sanitizers or benchmark success. All original failed scripts and runs remain preserved. No engine, fixture, model or audit data evaluation was executed by this reviewer.
