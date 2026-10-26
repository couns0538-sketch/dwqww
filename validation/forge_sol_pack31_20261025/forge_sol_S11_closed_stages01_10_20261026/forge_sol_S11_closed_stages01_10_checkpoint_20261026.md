# Forge S11 closed stages 01–10 checkpoint, 2026-10-26

PASS_LOSSLESS_ENCODING_ONLY. Exactly stages 01–10 are checkpointed. LP/B Release baselines reuse their original main/FIRST/full-Std evidence explicitly; both fresh Release candidates have closed build/FIRST/full-Std evidence. ASAN stages 11+, million-position parity, advisory speed, Elo and publication are outside this checkpoint.

The archive includes 401 selected original data payloads (8646258 bytes) plus the original-to-member mapping. It retains textual command streams, closure receipts, raw fixed references/perft/UCI/JUnit/FMA, oracle link maps and generated build recipes, frozen operator metadata and original reused FIRST/Std/numeric evidence. The active operator ledger was never read or archived; only root's pinned ten-row frozen ledger is included.

There are 74 EXCLUDED_BUT_HASH_BOUND compiled artifacts (20393624 bytes), with original path, size, SHA256, first-four-byte magic and reason in the mapping. This includes both raw ar-extraction .stdout files, which contain ELF object bytes. Whole private engine source, ELFs, objects, archives and compiler caches are excluded. All originals remain untouched locally. This does not include every original file.

Archive: `forge_sol_S11_closed_stages01_10_evidence_20261026.tar.gz`
SHA256: `cfc79c32ad029a2ffecee0206ee869d7a108d7009fc72630b1707e46df17811d`
Bytes: 1513447

Mapping SHA256: `c9a74185760dcd11baabc1153499792ea8f20007d95b941cead35d5b46f834a3`

Python decoder: PASS_ALL_MEMBER_BYTES. GNU tar decoder: PASS_ALL_MEMBER_BYTES, actual owned child exit0, reaped, no group members. Every decoded member was compared by exact size and SHA256 with original included bytes. After encoding, included originals, excluded hash-bound originals and stable metadata sources remained unchanged. Encoder ran on CPU4 nice19. No engine/compiler/native-test/profiling/timing action was run.

To recover data, create a new folder and run `/usr/bin/tar --no-same-owner --no-same-permissions -xzf forge_sol_S11_closed_stages01_10_evidence_20261026.tar.gz -C NEW_FOLDER`. Validate each recovered member against the included mapping; excluded compiled artifacts require exact original artifact recovery or a newly identified build, and cannot be reconstructed from hashes. Do not label later unrun stages as complete.

The dated one-off sealer and original S10 archive workflow source are included as provenance. Earlier observer parser failures are preserved as failed audits, superseded by the closed passing audit. Root owns Git publication; this local receipt does not claim publication.
