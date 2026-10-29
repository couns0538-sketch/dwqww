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
