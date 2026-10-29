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
