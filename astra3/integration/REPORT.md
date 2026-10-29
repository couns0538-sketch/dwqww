# Astra round3 A1 integration

Status: WIP. Checkpoint: 2026-10-29 00:13:34 PDT.

Base b7c177222038e9332965a95ec53ea3b94e90dbc9; branch astra3-integration. Round2 remains unchanged. Exact source order: B1 23e940b, B2 45314a5, B4 d35d41f, B5 5c6ee0d, R5A8f1ceac. Each will be a no-ff merge followed by a complete build, OFF identity, perft/kiwipete, whole-binary FMA and full CTest before advancing. The first post-B5 commit will replace positional presets and prove the reordered-field regression.

Required OFF nodes:312866/862329/3024920/12389307/34048354; perft5 4865609; kiwipete5 193690690; whole-binary FMA0. New round3 build/tests: NOT RUN yet. Compiler GCC14.2/C++20, Release strictFP recipe from the supplied pack. No gates or livePC operations.

Attached autopromote is a read-only handoff with SHA256896663b0307402a7285ba8446c8b486db168075761c2dfbd7832f0a0fcdd7b12; it will be audited later as a proposed patch only. Live PC copy, Windows and PowerShell5.1 are currently unavailable.

Twenty-minute final review is required after implementation; record real start/end timestamps and findings, not a claimed duration without work.

Next: merge B1 and qualify. Each checkpoint updates this report and is pushed within ten minutes. Round3 prompt SHA256 4f97ffdeefc0f38adad4693296b5a1f100a8d79db43c172eb358417e78555c97.

IDEA_SOURCE: user/Engine QA round3 integration and CR findings; same-repository Forge sources.
