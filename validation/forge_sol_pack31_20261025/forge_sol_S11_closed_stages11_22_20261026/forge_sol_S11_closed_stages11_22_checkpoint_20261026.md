# Forge S11 sanitizer stages 11–22 checkpoint, 2026-10-26

PASS_LOSSLESS_ENCODING_ONLY. Exactly the twelve closed ASAN stages 11–22 are checkpointed: four fresh strict O2/g ASan+UBSan builds, each followed by fresh FIRST bare11 and full qualification. LP suites have 14 tests and B suites 15, with no new failures and the exact four known diagnostics. Actual d11=308972, perft4 startpos=197281 and kiwipete=4085603, typed T1/T2, numeric FMA0, LeakSanitizer ON/UBSan halt, unlimited runtime virtual AS and owned cleanup were independently audited. These are correctness results, not speed or Elo evidence.

The archive includes 550 selected original data files (86886874 bytes) plus the original/member mapping: textual command streams, closure/results, FIRST/FULL references, JUnit, FMA/disassembly and generated build configuration/recipes. A fixed 26-file operator metadata allowlist contains the root-frozen22 ledger/snapshot and the closed audits; the active ledger was never read or archived. No parity stage23+ data is present.

There are 132 EXCLUDED_BUT_HASH_BOUND compiled artifacts (647498568 bytes), with original path, size, SHA256, first-four-byte magic and exclusion reason. Engine source, ELFs, objects, archives and compiler caches are not copied. All originals remain untouched locally. This is selected original data, not every original file.

Archive: `forge_sol_S11_closed_stages11_22_evidence_20261026.tar.gz`
SHA256: `c72971f5357817e9a59c5a07318425ac8e1a9e2d5bc1a26fff4c5ca04a21a9dd`
Bytes: 12006564

Mapping SHA256: `b05ccff8c84b995ec0cf271f3d1efcc5e4c9ba00a0de90cc734790728184cc80`

Python decoder: PASS_ALL_MEMBER_BYTES. GNU tar decoder: PASS_ALL_MEMBER_BYTES, actual owned child exit0, waited/reaped, no remaining group members. Both exact decoded-member size/SHA256 inventories match the included original bytes. The encoder rechecked all included originals, excluded hash-bound originals, stable metadata snapshots and final archive after encoding. CPU4 nice19; zero engine/compiler/native-test/profiling/timing actions. The prior first-ten checkpoint remains unchanged.

Restore into a new folder using `/usr/bin/tar --no-same-owner --no-same-permissions -xzf forge_sol_S11_closed_stages11_22_evidence_20261026.tar.gz -C NEW_FOLDER`, then check all members against the included mapping. Excluded binaries require exact-byte recovery or a newly identified build; a hash cannot reconstruct them. The fixed-root sealer reuses the existing S10 deterministic gzip6/PAX and dual-decoder workflow; no new native controller was added.

Root owns publication. This receipt does not claim Git publication, parity completion, speed gain or Elo gain.
