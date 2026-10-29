# B5 native qualification — 2026-10-29

Base b7c177222038e9332965a95ec53ea3b94e90dbc9; frozen implementation fde944ae38e6bbfef0b38f2c4a207e08285fcc1d. Branch astra2-singularv2 is independent of B1–B4. PORT_NOTES.md records the exact same-repository Fable J3 provenance, every changed engine/build line and CorrHistPlus interactions. The requested Opus attribution was not corroborated; the bundle documentation identifies the Fable source actually ported.

## Release evidence

Full build passed. Full CTest: 56/57 passed, raw exit 8. Only forge_tests failed, with the same four known tactical diagnostics; SmpExactNodes passed. New native regression: 96/96 checks. The native UCI regression passed, including actual N1/manual identity, invalid values, both CorrExt refusals, no partial preset mutation and OFF restoration. Its original transcript is retained. UCI baseline RED is preserved as uci_red.json/transcript.

All required OFF pins and startpos perft5 passed on this exact B5 executable. SingularV2 and N1 are actual changed searches; their numbers are not identity requirements or strength evidence. BENCH_RESULTS.md records all qualification nodes, milliseconds and NPS. full_ctest/LastTest.log additionally contains every native d9/d8 result and UCI d11 record.

NNUE object inspection passed: 256-bit arithmetic, FMA 0. frozen_sources.sha256 verifies all nine compiled/test source files. qualification.json records compiler, strict-FP flags, exact source and binary hashes. No source/test changes were made after this freeze.

## Reproduction

Use the CMake flags in qualification.json, configure and build all targets. Then:

```sh
python3 qualification_driver.py /path/to/build/forge fresh_pins '{"OFF":[],"SingularV2":["setoption name SingularV2 value 1"],"N1":["setoption name BundlePreset value N1"]}'
python3 ctest_driver.py /path/to/build fresh_ctest
python3 ../../tools/check_nnue_simd.py /path/to/build/CMakeFiles/forge_core.dir/src/nnue.cpp.o
```

Run the first two commands from this evidence directory; output directories must be new. CTest retains its actual exit status, including known failures.

## Decision and limits

Release correctness qualification complete; candidate remains default OFF and needs independent equal-time gating. No speed or Elo claim. A separate full ASan/UBSan build/run is in progress under sanitizers/; until its completed receipt exists, its result is UNVERIFIED. TSan, Windows, external tablebases and integration with B1/B2/B4 are UNVERIFIED. CorrExt and SingularV2 deliberately cannot be combined because their path budgets have different units. CorrHistPlus=4 is compatible and is the N1 pairing.

IDEA_SOURCE: Forge's own FB2-J3 singular-extension experiment and the user's round-two gate requirements.
