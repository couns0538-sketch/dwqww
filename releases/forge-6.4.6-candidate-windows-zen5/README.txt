Forge 6.4.6 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.6-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
This executable targets Zen5; it is not a universal x86 build.

This candidate relocates a qsearch query: gives_check is calculated inside
its existing pruning block, where the result is consumed. It skips this
read-only calculation on paths that do not use the result. Legality checks,
move counting, evaluation weights and intended search rules are unchanged.

The inherited legal-move query tries one quiet nonpromotion pawn push with
the normal king-safety check, then uses the complete original generator
fallback whenever that witness fails, including promotions.

Under Wine10, all 18,947 comparisons against the old full generator and an
independent make/unmake legality oracle passed. Fixtures, the frozen 10,000-
position corpus and deterministic walks were checked. Core tests including
six reference perft cases, all eight TT groups, rule50 regressions, and frozen
UCI/ponder tests passed. The stdin bench11 signature is 351,063 nodes with
Hash16MiB/Threads1, matching the Windows6.4.5 parent. Time/NPS is not compared.
YMM clamp/multiply/add and absence of fused arithmetic were checked. All
source, fixture, corpus, binary and tool hashes remained unchanged.

Inherited TT safety uses striped mutex-protected entry copies and opaque
probe-time destinations. Score context permits both capped clocks below90
or an exact capped-clock match (cap100), while preserving the main-search
current-clock<90 cutoff guard, raw static eval and hash-move reuse. Entry and
cluster layouts remain16/64 bytes. The below90 grouping is heuristic and does
not solve every repetition or rule50/history issue.

This is a candidate with correctness evidence. No accepted Elo gain exists.
No Windows throughput or timed match was run; any separate helper-kernel
measurement does not establish engine Elo. Native Windows, physical Ryzen
and Stockfish superiority remain unproven. The portable6.4.2 validator stays
pinned to6.4.2 and does not test this executable automatically.

Optional tests are included. From this directory, the witness oracle runs as:
forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd

Source and tests:4e15dea025c4b1ced9cbb5c9000a0cb627edcf15.
See source-hashes.json, test-hashes.json, provenance.json and SHA256SUMS.
