# IDEA_SOURCE (R7 J2, fpos2sf_mt)

| idea | source | use |
|---|---|---|
| FPOS v1 -> FEN -> `chess::Position::tryFromFen` -> TrainingDataEntry rules (castling/ep "-", constant ply, king-square dummy move, result sign, score clip) | Grok Bot's `F:\nnue_pytorch\forge_tools\fpos2sf.cpp` (GPL tree, read only) | `convert()` is that code unchanged, so the output is byte-identical |
| binpack chunk layout (`BINP` + u32 size, 32-byte packed entries, big-endian move count, 1 MiB flush rule) | nnue-pytorch `data_loader/cpp/lib/binpack.h` (`CompressedTrainingDataEntryWriter`), GPL-3.0 | parallel chunk building that reproduces the writer's flush points |
| record decoding for the verify (`unpackEntry`, `packedSfenValueToTrainingDataEntry`, `CompressedTrainingDataEntryReader`) | same library | the decoder the training loader uses |
| FPOS layout | Forge `src/datagen.cpp` (read only) | header and SoA layout |
| parallel units + ordered emit, bounded memory | own (R7) | `--threads`, peak working set 8.5-12.8 MB on a 10M shard |
