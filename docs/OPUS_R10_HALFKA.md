# OPUS R10: HalfKA (K32H3^) inference for nets from the AMD nnue-pytorch trainer — DONE (no Elo claims)

Branch `opus-r10-halfka` = AL1 lock `d4f4312` + CI baseline `0d99f02` + R10 commits. PC clock times (2026-10-30).
Machine exclusive: no (R9's SPSA run on CPUs 0-3, a PC gate, the live trainer and self-play ran beside it; R10 work
ran BelowNormal on CPUs 4-11; the live trainer, gates, self-play and R9 were not touched).

## First finding: the trainer has no "HalfKAv2_hm"
The R6 trainer (nnue-pytorch b2614500, 2026-10-28, clone `F:\opus_scratch\r6\nnue-pytorch-amd`) has three feature
sets: `K32H3^`, `Full_Threats`, `PP_3Wide` (default `Full_Threats+PP_3Wide+K32H3^`). Its HalfKAv2_hm-family set is
**K32H3^**: HalfKAv2_hm's 32 horizontally mirrored king buckets x **3 material states** (2 = the opponent has a queen,
1 = otherwise any rook or queen on the board, 0 = none) = 96 buckets x 704 piece-square planes (both kings share plane
10) = 67,584 features, int8 FT weights, no PSQT. The network is the 2026 layout: FT with a pairwise product, **32 layer
stacks** (piece-count bucket x 4 + queen bucket), l1 -> [x^2, x] -> l2 -> [x^2, x] -> output over both hidden layers,
plus a skip output. R10 implements exactly this (the nets R6 can export with `--features K32H3^`); the threat and pawn
feature sets are rejected with a clear message. The QA / Code Review notes named in the job (`/workspace/forge-hashes/
QA_R6AMD_20261030.md`, `CR_R6AMD_20261030.md`) are not on this PC or in the repository: owner item.

## Acceptance
| job | result | evidence |
|---|---|---|
| 1 loader + `EvalFileHalfKA` (off by default) | `src/nnue_halfka.cpp` reads Stockfish-format `.nnue` from the R6 export: version `0x6A448AFA`, network / FT / 32 stack hashes, L1 from the FT hash, (L2, L3) from the network hash + exact file size, int16-overflow bound; any L1 multiple of 64 up to 4096, L2/L3 <= 64. Option OFF: **bench 312866 / 862329 / 3024920 / 12389307 / 34048354, perft5 4865609, kiwipete 193690690 = ALL OK**. Truncated, wrong-version, garbage, empty and missing files answer `info string ERROR EvalFileHalfKA: ...` and leave the lock's eval (bench back to the pin) | `opus_r10/logs/identity_off_a.log`, `uci_check_b.log`, `uci_check_smoke.log` |
| 2 incremental accumulators, AVX2 + scalar, threads | per-worker accumulator stack indexed like the search stack; lazy update from the nearest valid ancestor with the same own-king square and state (else refresh: king move, mirror flip, queen/rook state change); AVX2 kernels (int8->int16 row add/sub, pairwise product, `maddubs`+`madd` dot products) with scalar fallbacks; read-only shared net, one stack per worker | `src/nnue_halfka.cpp`, `src/search.cpp` (`halfka_evaluate`) |
| 3 parity vs nnue-pytorch | the trainer's own `NNUEReader` + C++ feature extractor (`get_sparse_batch_from_fens("K32H3")`) + fake-quantized `model.forward` (float64) vs Forge's raw output: **R6 net (256x32x32): 12,000 / 12,000 exact** (also exact in float32); **smoke net (64x32x32): 12,000 / 12,000 exact**; **untrained 1024x32x32: 2,000 / 2,000 exact**. AVX2 == scalar on every position. Incremental == refresh: **204,694 checks / 0 mismatches** on 200 random games (parent and 2-4 plies back) and 31,602 / 0 at L1 1024; in-search verify build (`-DFORGE_HALFKA_VERIFY`): **3,028,552 lazily built rows equal a full refresh** (bench 13 + four 3-thread depth-13 searches) | `opus_r10/logs/parity_*`, `walk_1.log`, `verify_search.log`, `opus_r10/parity/` |
| 4 smoke net end to end | K32H3^ 64x32x32 trained on the box CPU (2 threads, 6 epochs x 200k positions of a 17 MB Forge self-play slice, loss 0.0505 -> 0.0115; the R6 RAM guard ended the run after epoch 5 at 7 GB free), exported by the trainer's `serialize.py`, loads, **ON bench 11 = 305,623 (stable over repeats and a reload)**; WAC 300 at 200 ms: see below; 200 fast games: see below | `opus_r10/nets/smoke_k32h3_l64.nnue`, `opus_r10/logs/smoke2_train_summary.log` |
| 5 NPS vs FORGENN2 | see below | `opus_r10/logs/nps_r10.log/.json` |
| tests / CI | box build 0 warnings, FMA 0; CMake all targets + CTest: only the 4 known `forge_tests` lines (KNOWN-FAILURE CHECK: PASS); opus-ci green on `cadf1d91` (release ALL OK, ASan/TSan KNOWN-FAILURE CHECK: PASS, TSan 0 reports) | `opus_r10/logs/ctest_b1.log(.known)`, run 40986475892 |

## Integer arithmetic (why the parity is exact)
FT `clamp(a, 0, 255) * clamp(b, 0, 255) >> 9` per half, [side to move, other side]; l1 sums `s1` (scale 2^14), linear
`clamp(s1 >> 7, 0, 127)`, square `min(127, (s1^2 + 20) >> 21)`; l2 linear `clamp(s2 >> 6, 0, 127)`, square
`min(127, (s2^2 + 5) >> 19)`; output over [sq1, lin1, sq2, lin2]; total = s3 + s1[L2-2] - s1[L2-1];
raw = trunc(2 * total * 9600 / 32768) (the trainer's output value); evaluation = raw / 16 centipawns (truncated).
The `+20` / `+5` reproduce the trainer's `floor(x * 128 + 1e-5)` on the squared activations, and the square is taken of
the full-precision sum, as the trainer does.
