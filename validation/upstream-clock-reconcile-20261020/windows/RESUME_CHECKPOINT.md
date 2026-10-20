# Windows 6.4.13 continuation checkpoint

Frozen source/tests: `cecf0b9e3af5602053bcaf5c5d16ffc09f58850d`.
The interrupted completed build was reused after checking all 69 exported source
files against Git, all six actual PE binaries and the static core against build
hashes, and all 175 parent records. No rebuild was performed during resumption.

All eight existing Wine checks passed: core/perft and new clock API assertions,
TT coherence (eight groups), rule50, legal witness (18,947 comparisons), UCI,
ponder, five OwnBook transitions, and bench11 at 351,063 nodes. SIMD inspection
confirmed 256-bit operations without fused arithmetic. This is a node signature,
not a speed measurement. No timed match was run.

`releases/forge-6.4.13-candidate-windows-zen5.zip` is 10,514,835 bytes,
SHA256 `ca2512f2b7a91a3b9e391992fa8e5ebc622e79daa5a9fcc088f3b2819a74cbb7`.
The engine SHA256 is `3693e6f2ffefea3cfe100d1f1c920ad21e6cdd5fff7ef389896728773be1f56a`.
The original Windows evidence ZIP is 6,922,791 bytes, SHA256
`203cc47c0446b7e07747ea73eb41777c5c6b13db2aafa20ae04251f0b55be8d4`,
with 151 original files plus its manifest. The release embeds that exact archive.

The independent artifact audit passed all 872 checks without executing an
engine. It verifies all source/provenance, release members/checksums, raw payloads,
actual PE/core bytes, strict Zen5/static flags and unchanged parent records.
The failed first audit-helper path construction and corrected full result remain
preserved. Use `path.with_name(path.name + '.zip')` for dotted versioned stems;
`with_suffix` removes part of a name such as `forge-6.4.13-candidate-windows-zen5`.
This small harness correction changed no engine, artifact or test outcome.

All owned files are final. Native Linux ASan/UBSan and TSan results are maintained
separately by the lead task. No native Windows/Ryzen, throughput, NPS, Elo or
Stockfish superiority is established. Next action: root preserves these outputs
with the complete candidate checkpoint and pushes the distributable.
