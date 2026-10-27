# O2 IDEA_SOURCE

O2 is a speed-only rewrite of existing Forge code (src/nnue.cpp), with no new evaluation idea. The
sources below are for the general techniques used. No third-party code was copied or adapted; all
code is our own.

| Technique in O2 | Source (concept only) |
|---|---|
| Incremental ("efficiently updatable") accumulator with lazy updates: record the piece changes at make-move and replay them from the nearest valid ancestor only when evaluate() is reached (already in AL1 s198, kept unchanged) | Yu Nasu, "Efficiently Updatable Neural-Network-based Evaluation Functions for Computer Shogi" (2018); Chess Programming Wiki, "NNUE" (https://www.chessprogramming.org/NNUE) |
| Fused multi-change updates: one pass per lane for 1-sub-1-add (quiet), 2-sub-1-add (capture, en passant, capturing promotion) and 2-sub-2-add (castling), instead of a copy followed by one pass per change | General NNUE implementation practice, described in public NNUE docs (Stockfish nnue-pytorch docs, "docs/nnue.md": accumulator update section, https://github.com/official-stockfish/nnue-pytorch/blob/master/docs/nnue.md), concept only; AL1 s198 already fused the first two cases |
| Register blocking of the refresh (keep a block of accumulator lanes in vector registers while all feature columns are added) | Standard loop tiling / register blocking for vectorised sums (e.g. the Intel 64 and IA-32 Architectures Optimization Reference Manual, SIMD chapters) |
| 64-byte alignment of the weight columns and accumulators so that no vector load straddles two cache lines | Intel / AMD optimisation manuals (cache-line split loads); C++17 aligned `operator new` (`std::align_val_t`) |
| Compile-time kernel selection (portable C++, SSE2, AVX2) with bit-identical results: same float operations per lane in the same order, no FMA (`-ffp-contract=off`), no `-ffast-math` | IEEE 754 binary32 semantics; GCC manual on `-ffp-contract` and `-ffast-math` |
| The exactness argument (accumulator values are integer multiples of 2^-12 well inside the 24-bit significand, so the accumulator sums are never rounded) | Our own analysis of the lock's quantised weight format (int16 / 4096), checked at run time by the parity harness |

Not used here (owned by other jobs): explicit AVX-512 kernels (Astra N25), the king-bucket refresh
cache (crew job C4).
