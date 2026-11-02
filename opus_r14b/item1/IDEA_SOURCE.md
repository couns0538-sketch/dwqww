# Idea sources for R14-B item 1 (fast npt loader)

| what | source | licence | how it was used |
|---|---|---|---|
| binpack record / chunk layout, piece codes, zig-zag score code | nnue-pytorch data_loader (`lib/binpack.h`, `lib/training_data_entry.h`, `lib/chess.h` in `F:\opus_scratch\r6\nnue-pytorch-amd`) | nnue-pytorch is GPL-3.0 (some files carry an older MIT header; treated as GPL, ideas only per Couns's rule) | read to learn the file format; parser written from LOADER_SPEC.md, no code copied, translated or paraphrased |
| skip-filter rules (placeholder zero, early-ply curve, adaptive piece-count filter), window + scratch timing, thread split | nnue-pytorch `training_data_loader.cpp`, `lib/parallel_dataloader.h` | GPL-3.0 | behaviour described in my words in LOADER_SPEC.md (needed for bit-identical batches), implemented from that description; formula shapes kept equal so floating-point results match |
| K32H3 feature index, block state, queen bucket, batch memory layout | nnue-pytorch `training_data_loader.cpp`, `data_loader/_native.py` | GPL-3.0 | same as above; the trainer's own `SparseBatch.get_tensors` is called at run time inside the trainer (not copied) |
| `std::shuffle`, `std::mt19937_64` | libstdc++ (GCC 15.2) | GPL-3.0 with the GCC Runtime Library Exception | called as the standard library; identical toolchain keeps the permutation equal |
| "no seed reaches the loader; one decode worker is deterministic" | R6 `opus-r6-amd-nnue` LOADER_NOTES.md (`dl_equal.py` stream mode) | own (Opus) | confirmed again here (logs/equality) |
