# Imported round-two historical checkpoints

Current round-three state: astra3/integration/REPORT.md. Historical pending statements below are retained verbatim as evidence, not current task status.

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

User B1 review on 21ecf2c: restore main-thread partial-iteration behavior; cap selector depth comparison at
requested depth; protect losing TB scores; replace brittle node-cap pin with behavioral assertions. Changes in progress.
Pre-review candidate full Release build completed; binary SHA256 3855161fa385bbf7d75312ca3e5a47561b74f2fd4baa08ac0b9fad284019728a.
Its OFF and ON Threads=1 benches both matched all five pins; perft5 4865609. Native selector 74/74 and 16 UCI
searches passed before this review; these are historical pre-review results, not qualification of the upcoming changes.

B1 user-review corrections implemented and native-linked tests PASS 99/99. Main partial-iteration behavior
matches OFF across five fresh node caps; both TB signs protected; selector comparison depth capped at the
requested depth/mate limit. Fixed-move regression expectation removed. Independent source review PASS.
Rebuilt all Release targets; reviewed binary pin/perft checks and complete CTest are running serially.

B1 COMPLETE after user review: source931bd49; Release99nativechecksPASS, CTest56/57 (onlysamefourforge_testslines), OFF/ONall5pinsPASS, perft54865609, NNUEFMA0. SeeB1/final_qualification.json andBENCH_RESULTS.md. B2 nowimplementing onindependentastra2-tm-softhard fromb7; B3v2tests,B4protocol,B5SingularV2,B6matrix,B7report pending.

## Imported B2 checkpoint

# B2 continuation checkpoint — 2026-10-29

Base b7c177222038e9332965a95ec53ea3b94e90dbc9. Implementation97da33b.
TmSoftHardClamp default OFF: caps nominal and scaled soft time at hard time; no J4 port.
Release build PASS. Native32,433 checks PASS; header-only UBSan32,424 PASS, zero diagnostics.
OFF/ON pins all exact; perft5 4865609; NNUE FMA0. No speed/Elo claim.
Full CTest55/57: four known forge_tests diagnostics plus an intermittent two-thread mate test failure,
independently reproduced on untouched baseline in adaptive replay12. Keep original failed full run.
Read astra2_evidence/B2/README.md and qualification.json for exact commands, hashes and all results.

B1 completed after review on astra2-smpv2-mate23e940b. B3 now executing test-only v2 loader coverage
on astra2-nnue-loader. B4 protocol, B5 SingularV2, B6 matrix and B7 final report remain.
IDEA_SOURCE: user round-two invariant and this repository's original allocator.

# B4 continuation checkpoint — 2026-10-29

Base b7c177222038e9332965a95ec53ea3b94e90dbc9; final source2beaad8.
All64 tunables advertised; unknown names diagnosed; accepted actual changes after B1-B4 presets diagnosed.
OFF resets preset tracking. Invalid/refused/no-op assignments retain old values and do not claim overrides.
Native Release150 and debug155 checks PASS; full CTest56/57 (onlyfourknownforge_testslines).
Allfive OFF pins and perft54865609 PASS, FMA0. No search values changed; no speed/Elo claim.
Actualfastchess-strict, Windows and full-engine sanitizer qualification remain UNVERIFIED.
Read astra2_evidence/B4/README.md for all original evidence and reproduction commands.

B1 final23e940b; B2 final45314a5 (additional baseline SMP mate-test failure preserved);
B3 final9a09e76. B5 now implementing defaultzero SingularV2/N1 on its own b7 branch.
B6 bench matrix and B7 final report remain. When combining branches, new B1/B2/B5 option setters
must use B4's assign_option observer and retain each feature's preset ownership rules.
IDEA_SOURCE: user strict-UCI requirements and Forge's own option registry.

# B5 completed checkpoint — 2026-10-29

Base b7c177222038e9332965a95ec53ea3b94e90dbc9; frozen implementation fde944ae38e6bbfef0b38f2c4a207e08285fcc1d. SingularV2 defaults0, N1 is CorrHistPlus4+SingularV2. Same-repository Fable J3 port, with CorrExt mutual exclusion; PORT_NOTES.md lists every changed engine/build line and interactions.

OFF nodes312866/862329/3024920/12389307/34048354. ON404121/1005954/4120585/11497954/34264955. N1277579/814055/2651984/18648191/40304213. Startpos perft54865609, NNUEFMA0. Native96/96, UCI27checksPASS. Release and complete leak-enabled ASan/UBSan CTest each56/57, rawexit8: only the four known forge_tests diagnostics, zero sanitizer findings in the completed outside-sandbox run. Preserve interrupted sandbox attempt separately.

No speed or Elo claim. Candidate is ready for independent review and equal-time N1/SingularV2 gates; not accepted into the integration branch. Windows, TSan, actual Syzygy files and combined B1/B2/B4 integration are unverified. Exact commands, source/binary hashes and every bench record are in astra2_evidence/B5. Do not repeat completed qualification without a changed source or a specific unresolved question.

IDEA_SOURCE: this repository's FB2-J3 experiment and user's isolated validation requirements.
