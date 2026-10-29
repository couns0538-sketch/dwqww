# Astra round 2 checkpoint — 2026-10-29

Requested baseline: origin/forge-bundle-int, verified b7c177222038e9332965a95ec53ea3b94e90dbc9.
Original /workspace/dwqww remains untouched (uncommitted work and missing old /tmp object alternate).
This checkout is isolated in /tmp/forge-astra2. Only astra2-* work branches; no force pushes/deletions.

B1 in progress: original SmpV2 lives on fable-fb2-j5 bf6839e9e65108db76f028532dc15f9587a41fe7,
not the bundle base. Port the narrowly scoped default-OFF option and reproduce/fix the actual selector.
B2 pending: TimeManV2/J4 also excluded from bundle; shared base allocator exhibits soft > hard.
B3 pending source clarification: base v2 loader already reads size/header before weights; requested v3 loader
is on fable-nnue-arch, absent from bundle. Do not silently substitute versions.
B4-B7 pending, in requested order. B5 original SingularV2 is identified in fable-fb2-j3; opus source investigation pending.

Baseline Release build in progress: GCC 14.2, C++20, -march=x86-64-v3 -mtune=znver5
-fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256. Build /tmp/forge-astra2-build-base.
Initial configure failed because sparse checkout omitted bench/benchmark.cpp; recovered existing bench/ and reconfigured.
No tests or bench results yet. Pins d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354;
startpos perft5 = 4865609. Do not claim Elo or speed from these checks.

IDEA_SOURCE: user round-two specification and this repository's existing Forge implementations only.

B3 clarification accepted: stay on bundle v2, add malformed-file regression coverage, only patch a proven gap.
V3 port explicitly deferred as a separate later job. B1 historical selector RED: 66 checks / 21 failed assertions
from exact J5 selector bytes, preserved with source SHA. Candidate implementation in progress.

Baseline all-five bench pins PASS: 312866 / 862329 / 3024920 / 12389307 / 34048354.
Original perft helper sent unsupported `perft 5` and got no output; this was a harness error, not an engine failure.
Correct invocation `go perft 5` returns 4865609. Both transcripts retained; corrected qualification_driver_v2.py.
B1 real selector standalone GREEN 66/0 after historical RED 66/21. Complete candidate build and baseline CTest running.

Baseline complete CTest: 54/55, only forge_tests with the four existing tactical FAIL diagnostics; SmpExactNodes
passed in this run. B1 actual-port abort-tuple RED: 74 checks, one failure before the SmpV2-only completed-result
retention guard. Selector source and actual worker path now corrected; final native build/tests still pending.
