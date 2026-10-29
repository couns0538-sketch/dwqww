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
