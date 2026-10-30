# Forge self-play holdout list (2026-10-30)

Holdout shards: **forge_selfplay_013** and **forge_selfplay_014** (whole shards; game-level split).
Training set: shards 001-039 **excluding** 013 and 014 (37 shards).
Rule: zero overlap. Drop every training position whose (board + side-to-move) key also appears in 013 or 014.

| Shard | Records | .pos bytes | binpack bytes | binpack md5 |
|---|---|---|---|---|
| forge_selfplay_013 | 10,000,000 | 350,000,016 | 340,002,600 | 723229e5199143ba563f2cb11e6e626d |
| forge_selfplay_014 | 6,388,575 | 223,600,141 | 217,213,214 | 1fa19e1aaf191d85b154364b686a9cc4 |

Built files on grok-pc (not on GitHub; too large and the repo is public):
- Holdout binpack: `F:\forge_j1_data\forge_holdout_013-014_j2.binpack` (557,215,814 bytes, md5 57727d9d58661d7077d1c573b86c3538, concat of 013+014)
- Train binpack: `F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack` (10,370,064,802 bytes, md5 c84723eb54a79251334eff16f402b5fc, concat of 37 shards)
- Source .pos shards: `D:\grok-pc-data\forge_push\nnue_data\pos\forge_selfplay_NNN.pos` (FPOS v1: 16-byte header, 35 B/record)
- FEN sidecars: `D:\grok-pc-data\selfplay_out\forge_selfplay_NNN.txt` ("FEN | eval_cp | result")
- Converter log: `F:\forge_j1_data\convert.log` (J2 converter exe sha256 C3672C3D...83E2; .pos only, drops castling/EP)

Known overlaps (QA_ASTRA_A1_20261030.md): Astra A1 filtered 003 had 281 kept rows overlapping full 013/014
(160 with 013, 121 with 014). fens_12k shares 160 positions with training data, so use it for parity only, never as a loss holdout.
