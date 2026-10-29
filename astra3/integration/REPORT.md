# Astra round3 A1 integration

Status: WIP. Checkpoint: 2026-10-29 00:13:34 PDT.

Base b7c177222038e9332965a95ec53ea3b94e90dbc9; branch astra3-integration. Round2 remains unchanged. Exact source order: B1 23e940b, B2 45314a5, B4 d35d41f, B5 5c6ee0d, R5A8f1ceac. Each will be a no-ff merge followed by a complete build, OFF identity, perft/kiwipete, whole-binary FMA and full CTest before advancing. The first post-B5 commit will replace positional presets and prove the reordered-field regression.

Required OFF nodes:312866/862329/3024920/12389307/34048354; perft5 4865609; kiwipete5 193690690; whole-binary FMA0. New round3 build/tests: NOT RUN yet. Compiler GCC14.2/C++20, Release strictFP recipe from the supplied pack. No gates or livePC operations.

Attached autopromote is a read-only handoff with SHA256896663b0307402a7285ba8446c8b486db168075761c2dfbd7832f0a0fcdd7b12; it will be audited later as a proposed patch only. Live PC copy, Windows and PowerShell5.1 are currently unavailable.

Twenty-minute final review is required after implementation; record real start/end timestamps and findings, not a claimed duration without work.

Next: merge B1 and qualify. Each checkpoint updates this report and is pushed within ten minutes. Round3 prompt SHA256 4f97ffdeefc0f38adad4693296b5a1f100a8d79db43c172eb358417e78555c97.

IDEA_SOURCE: user/Engine QA round3 integration and CR findings; same-repository Forge sources.

## M1: merge B1

2026-10-29 00:15:41 PDT: `git merge --no-ff --no-commit 23e940b659848f0b1611582cdd70e11b362c80f8`, clean merge. Preserved reviewed main partial-PV semantics, helper capped selection and both TB signs. WIP: full build, pins and CTest pending. No conflict resolution or new engine behavior.

### M1 qualification — 2026-10-29 00:24:10 PDT

Exe SHA256 `cc1d2ed7fbdeea50516650fd0b9d1cca539d0d6cefc11cbc8a51cfcdb2daab0b`. Exact source292d079 (merge of B1). Full Release build succeeded. CTest56/57, exit8: only the four known forge_tests lines. Startpos perft5=4865609; kiwipete5=193690690; whole-binary FMA=0.

| Depth | OFF nodes | ms | NPS |
|---:|---:|---:|---:|
| 11 | 312866 | 544 | 575121 |
| 13 | 862329 | 1280 | 673694 |
| 16 | 3024920 | 3281 | 921950 |
| 20 | 12389307 | 16022 | 773268 |
| 22 | 34048354 | 50335 | 676434 |

Commands: CMake configure/build with the rule5 GCC14 strict-FP recipe into `/tmp/forge-astra3-build-integration`; `python3 astra3/integration/tools/identity_bench.py /tmp/forge-astra3-build-integration/forge astra3/integration/M1/pins`; `python3 astra3/integration/tools/run_full_ctest.py /tmp/forge-astra3-build-integration astra3/integration/M1/ctest`; `python3 astra3/integration/tools/check_milestone.py /tmp/forge-astra3-build-integration/forge astra3/integration/M1 --source 292d079`. Original raw logs, exact executable and receipt retained under M1. No speed/Elo claim.

Next: merge B2 with both independent flags preserved. Full integration/SAN/TSan and all ON matrices still UNVERIFIED. QA clarification pending: CorrMargins1/Scale100 is published as ON343365/858019/2522546/12894582/22287047, while one prompt line demandsOFF. Preserve published semantics while resolving the conflict.

## M2: B2 merge resolution

Status WIP. Used real no-ff merge45314a5. Resolution is a union: both CMake native/UCI test registrations, both FB2 flags, both UCI handlers with the required closing brace, and both IDEA_SOURCE/old checkpoint texts retained. apply_bundle now assigns only its three owned FB2 fields (plus its existing external CorrHistPlus/HistRework/CuckooRep values), so SmpV2 AND TmSoftHardClamp, and future independent bits, survive presets without positional preservation code. Automatic iterative/timing merges retained both features; full build/identity/CTest pending.

IDEA_SOURCE: Engine QA CR_ASTRA2 F3 in supplied round3 pack; same-repository B1/B2 sources.

Environment preflight: the race-free atomic two-thread GCC14 TSan probe passed outside the tracing sandbox (exit0, counter20000, empty stderr). Recipe:`g++-14 -std=c++20 -O1 -g1 -fsanitize=thread -fno-omit-frame-pointer -fno-pie -no-pie -pthread ...`. This proves runtime availability only; the full engine TSan run is still required. The probe is not an engine and has no chess identity table. M1 source receipt expanded from its unambiguous7-character prefix to the full commit SHA without rerunning or altering any native output.

### M2 qualification — 2026-10-29 00:33:06 PDT

Source `52a2983e11a08d129a3c77bcae68499f54f323eb`; exe SHA256 `31414519ac2a79eb0e373a83dc8c94b9ab4c21b4919790f3191c8b20043a4786`. Complete Release build succeeded. Full CTest 58/59, raw exit 8; failures: [['forge_tests', 'Failed']]. Original diagnostics: ['FAIL: WAC 001 expected g3g6 got f6h5', 'FAIL: WAC 001 score 623 below 31997', 'FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion', 'FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion']. Startpos perft5=4865609; kiwipete5=193690690; whole-binary FMA=0.

| Depth | OFF nodes | ms | NPS |
|---:|---:|---:|---:|
| 11 | 312866 | 442 | 707841 |
| 13 | 862329 | 959 | 899196 |
| 16 | 3024920 | 4160 | 727144 |
| 20 | 12389307 | 12466 | 993847 |
| 22 | 34048354 | 33723 | 1009647 |

Exact commands (same configured rule5 build): `cmake --build /tmp/forge-astra3-build-integration -j4`; `python3 astra3/integration/tools/identity_bench.py /tmp/forge-astra3-build-integration/forge astra3/integration/M2/pins`; `python3 astra3/integration/tools/run_full_ctest.py /tmp/forge-astra3-build-integration astra3/integration/M2/ctest`; `python3 astra3/integration/tools/check_milestone.py /tmp/forge-astra3-build-integration/forge astra3/integration/M2 --source 52a2983e11a08d129a3c77bcae68499f54f323eb`. Flags, raw output, original executable and receipt retained in M2. These timings make no speed or Elo claim. Full integrated ON matrix/SAN/TSan remains pending until the final A1 head.

A small proposed update to the existing validate-chess-engine skill is preserved under skill_update (same package/name; no duplicate skill created). Its patch/static checks and focused synthetic instruction scenarios passed; those are not engine evidence or a measured behavioral gain. No callable skill-creator/provider editor exists here, so it is PROPOSED ONLY, not installed. Next integration step: B4.

## M3: B4 merge — 2026-10-29 00:34:28 PDT

WIP. `git merge --no-ff --no-commit d35d41fbe217bc00cedf642dd22aafcd895b53f2`. Engine/CMake merged automatically; IDEA_SOURCE and historical NOTES resolved as a union. B4's existing complete metadata and override diagnostics retained for this milestone. The R3 owned-only override policy, new-handler observer routing and R5A echo integration are still pending, with new tests under tests_pending not yet run. Full build, identity and CTest started.

### M3 qualification — 2026-10-29 00:41:54 PDT

Source `8c10a4cbd6b21caf66ce8071c6bca8b9e17106b1`; exe SHA256 `db50cb6c9130d018054852bc552c8a8b38ad8ea344292962053e3baccdba9cdf`. Complete Release build succeeded. Full CTest 60/61, raw exit 8; failures: [['forge_tests', 'Failed']]. Original diagnostics: ['FAIL: WAC 001 expected g3g6 got f6h5', 'FAIL: WAC 001 score 623 below 31997', 'FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion', 'FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion']. Startpos perft5=4865609; kiwipete5=193690690; whole-binary FMA=0.

| Depth | OFF nodes | ms | NPS |
|---:|---:|---:|---:|
| 11 | 312866 | 446 | 701493 |
| 13 | 862329 | 1470 | 586618 |
| 16 | 3024920 | 4317 | 700699 |
| 20 | 12389307 | 17704 | 699802 |
| 22 | 34048354 | 34382 | 990295 |

Exact commands (same configured rule5 build): `cmake --build /tmp/forge-astra3-build-integration -j4`; `python3 astra3/integration/tools/identity_bench.py /tmp/forge-astra3-build-integration/forge astra3/integration/M3/pins`; `python3 astra3/integration/tools/run_full_ctest.py /tmp/forge-astra3-build-integration astra3/integration/M3/ctest`; `python3 astra3/integration/tools/check_milestone.py /tmp/forge-astra3-build-integration/forge astra3/integration/M3 --source 8c10a4cbd6b21caf66ce8071c6bca8b9e17106b1`. Flags, raw output, original executable and receipt retained in M3. These timings make no speed or Elo claim. Full integrated ON matrix/SAN/TSan remains pending until the final A1 head.

## M4: B5 merge — 2026-10-29 00:45:03 PDT

WIP. Real no-ff merge5c6ee0d. Retained both timing and SingularV2 UCI test registrations, all source citations and historical checkpoint text. FB2 fields temporarily retain SingularV2 as the4th bool so the existing N1 initializer means what B5 measured; independent SmpV2/timing follow it. apply_bundle explicitly assigns its newly owned singular_v2 field, preserving both independent flags. Corrected stale BUNDLES/header exclusions. All search hooks and CorrExt exclusivity remain B5's reviewed implementation.

Full build/OFF qualification now starts. Per QA requirement, the FIRST commit after this merge will contain the named-preset F1 fix, static assertions and reordered-field negative proof; there will be no intervening evidence-only commit. M4 raw evidence will be included with that commit. No N1 gate is run.

### CorrMargins requirement resolved — 2026-10-29 00:48:19 PDT

The user explicitly confirmed: qualify CorrMargins=1, CorrMarginsScale=100 against R5A ON343365/858019/2522546/12894582/22287047; CorrMargins=0 withScale100 must retainOFF pins. Preserve queued gate semantics. This supersedes the contradictory single line in the supplied pack; it is no longer an acceptance blocker.

### M4 qualification — 2026-10-29 00:52:53 PDT

Source `0fe9b372dec2072bbd29daaef7f2bf4ca0ff6f00`; exe SHA256 `09e238a6a98541079700f0d79ce44df6747ea7f640352061e223409f657dc5a0`. Complete Release build succeeded. Full CTest 62/63, raw exit 8; failures: [['forge_tests', 'Failed']]. Original diagnostics: ['FAIL: WAC 001 expected g3g6 got f6h5', 'FAIL: WAC 001 score 623 below 31997', 'FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion', 'FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion']. Startpos perft5=4865609; kiwipete5=193690690; whole-binary FMA=0.

| Depth | OFF nodes | ms | NPS |
|---:|---:|---:|---:|
| 11 | 312866 | 387 | 808439 |
| 13 | 862329 | 1165 | 740196 |
| 16 | 3024920 | 3553 | 851370 |
| 20 | 12389307 | 13134 | 943300 |
| 22 | 34048354 | 42682 | 797721 |

Exact commands (same configured rule5 build): `cmake --build /tmp/forge-astra3-build-integration -j4`; `python3 astra3/integration/tools/identity_bench.py /tmp/forge-astra3-build-integration/forge astra3/integration/M4/pins`; `python3 astra3/integration/tools/run_full_ctest.py /tmp/forge-astra3-build-integration astra3/integration/M4/ctest`; `python3 astra3/integration/tools/check_milestone.py /tmp/forge-astra3-build-integration/forge astra3/integration/M4 --source 0fe9b372dec2072bbd29daaef7f2bf4ca0ff6f00`. Flags, raw output, original executable and receipt retained in M4. These timings make no speed or Elo claim. Full integrated ON matrix/SAN/TSan remains pending until the final A1 head.

## F1 HIGH: first commit after B5 merge

M4 is qualified above. Replaced every production preset, includingOFF, with named C++20 designators and converted all nonempty FB2 Options test initializers. Added compile-time N1/independent-bit assertions and exhaustive runtime preset preservation combinations. The pre-fix copied-header proof passed normally and FAILED the two intended N1 assertions after swapping only SmpV2/SingularV2 declarations; exact original/brokencopies and diagnostics are retained under F1_pending, never used as live engine code. Post-fix permutation verification follows. This first post-merge commit contains the repair; full engine requalification of it remains WIP. Toolingprovenance confirms an official serial-built Fastchess with -strict and private PS7.5.2; no games or supplied scripts were executed.

### F1 rolling checkpoint — 2026-10-29 01:02:11 PDT

Independent read-only review found no correctness blocker. Identical compile probes show the old reordered header fails its intended assertions and the named version passes both layouts; after-header hash matches the source. Full Release build completed; first four OFF depths match pins, d22/CTest/kiwipete remain running or pending. Evidence in F1 is explicitly partial until qualification.json exists. Added a fixed-reference final option-matrix runner (not yet executed); it checks all supplied R5A singles without deriving expected nodes from the candidate. No speed/Elo claim.

### F1 qualification — 2026-10-29 01:05:09 PDT

Source `a19a4477a1e502d675e505c741d9d7abc0511d8a`; exe SHA256 `7e876391a72dda02ebed8677d6df026e96afbd10a0d8b676fe31f0578f74504e`. Complete Release build succeeded. Full CTest 62/63, raw exit 8; failures: [['forge_tests', 'Failed']]. Original diagnostics: ['FAIL: WAC 001 expected g3g6 got f6h5', 'FAIL: WAC 001 score 623 below 31997', 'FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion', 'FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion']. Startpos perft5=4865609; kiwipete5=193690690; whole-binary FMA=0.

| Depth | OFF nodes | ms | NPS |
|---:|---:|---:|---:|
| 11 | 312866 | 477 | 655903 |
| 13 | 862329 | 1123 | 767879 |
| 16 | 3024920 | 4809 | 629012 |
| 20 | 12389307 | 16100 | 769522 |
| 22 | 34048354 | 48422 | 703158 |

Exact commands (same configured rule5 build): `cmake --build /tmp/forge-astra3-build-integration -j4`; `python3 astra3/integration/tools/identity_bench.py /tmp/forge-astra3-build-integration/forge astra3/integration/F1/pins`; `python3 astra3/integration/tools/run_full_ctest.py /tmp/forge-astra3-build-integration astra3/integration/F1/ctest`; `python3 astra3/integration/tools/check_milestone.py /tmp/forge-astra3-build-integration/forge astra3/integration/F1 --source a19a4477a1e502d675e505c741d9d7abc0511d8a`. Flags, raw output, original executable and receipt retained in F1. These timings make no speed or Elo claim. Full integrated ON matrix/SAN/TSan remains pending until the final A1 head.

Native pre-R5A contract run completed:101 cases,97 failed,4 passed. Missing active echoes and non-owned override messages are demonstrated with original streams. Four response-deadline failures during an environment slowdown are NOT counted as intended regression proof; raw failures are preserved for follow-up. No engine process remains from this run. F1 full qualification is complete above. Next: exact R5A merge and integrated contract repair.

## M5: exact R5A merge and integration repairs — 2026-10-29 01:11:59 PDT

WIP. `git merge --no-ff --no-commit 8f1ceac1eff16de202931e22958bbe9c1543c888`; CMake conflicts resolved as a union of both native targets/tests. UCI conflict resolution is in progress with one advertisement loop and all reviewed guards retained. Nominal depth metadata is being added without changing selector ranking. The old B4 test expectations for non-owned option override messages are explicitly changed to the user's seven-owned-field contract; actual no-op/invalid/refusal coverage remains. The exhaustive native option test is registered for this pinned h256 integration build.

The pre-R5A timeout audit shows all four timed-out child inputs contain only `uci` and cleanup `quit`: none had loaded an NNUE fixture or started search. PawnPairs/PureNnue produced no startup output; CorrMargins/CorrExt later produced uciok. These are retained as startup/scheduling failures, not intended regression evidence. Fixture files are0.4–5.1MB, and available memory was31GB; no resource-limit violation is demonstrated.

M5 source resolutions are now complete. F6 adds nominal_depth metadata at the end of SearchInfo and copies it through completed/terminal Worker results and SmpBestThread; ranking still compares capped actual depth. Tests-first syntax check failed solely because the field was absent, then passed after adding it; raw proof is in F6. Native test counts remain pending. SearchInfo layout changes require rebuilding every dependent target. The new UCI listing/diagnostic changes are reviewed as protocol-only; full OFF and ON qualification must establish identity. No engine binary has yet been built from M5.
