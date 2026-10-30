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
| 4 smoke net end to end | K32H3^ 64x32x32 trained on the box CPU (2 threads, 6 epochs x 200k positions of a 17 MB Forge self-play slice, loss 0.0505 -> 0.0115; the R6 RAM guard ended the run at 7 GB free after the sixth epoch, index 5, whose checkpoint is the net), exported by the trainer's `serialize.py`, loads, **ON bench 11 = 305,623 (stable over repeats and a reload)**; WAC 300 at 200 ms: see below; 200 fast games: see below | `opus_r10/nets/smoke_k32h3_l64.nnue`, `opus_r10/logs/smoke2_train_summary.log` |
| 5 NPS vs FORGENN2 | see below | `opus_r10/logs/nps_r10.log/.json` |
| tests / CI | box build 0 warnings, FMA 0; CMake all targets + CTest: only the 4 known `forge_tests` lines (KNOWN-FAILURE CHECK: PASS); opus-ci green on `cadf1d91` (release ALL OK, ASan/TSan KNOWN-FAILURE CHECK: PASS, TSan 0 reports) | `opus_r10/logs/ctest_b1.log(.known)`, run 40986475892 |

## Integer arithmetic (why the parity is exact)
FT `clamp(a, 0, 255) * clamp(b, 0, 255) >> 9` per half, [side to move, other side]; l1 sums `s1` (scale 2^14), linear
`clamp(s1 >> 7, 0, 127)`, square `min(127, (s1^2 + 20) >> 21)`; l2 linear `clamp(s2 >> 6, 0, 127)`, square
`min(127, (s2^2 + 5) >> 19)`; output over [sq1, lin1, sq2, lin2]; total = s3 + s1[L2-2] - s1[L2-1];
raw = trunc(2 * total * 9600 / 32768) (the trainer's output value); evaluation = raw / 16 centipawns (truncated).
The `+20` / `+5` reproduce the trainer's `floor(x * 128 + 1e-5)` on the squared activations, and the square is taken of
the full-precision sum, as the trainer does.

## How the engine uses it
- `setoption name EvalFileHalfKA value <path>` loads the net (Windows path); `<empty>` (the default) or an empty value
  turns it off. A failed load prints `info string ERROR EvalFileHalfKA: <why>` and leaves the option off.
- While a net is loaded, the static evaluation is the net alone (no HCE, no FORGENN2 residual); everything else in the
  search is the lock's. Each search worker owns an accumulator stack of `MaxPly + 8` = 136 entries x 2 perspectives
  (139 KB at L1 256); the net itself is shared read-only.
- A row is built lazily when a node is evaluated: from the nearest ancestor on the path with the same own-king square
  and material state (the recorded piece changes of each ply in between are applied), else by a full refresh.
  `record_move` / `record_null_move` invalidate the child's rows; the root is refreshed at every search start.

## WAC 300 (tactics sanity, not strength)
Lock harness copy (`opus_r10/tools/wac_tactics.py`), 200 ms per position, Threads 1, Hash 16, OwnBook false, fresh
`ucinewgame` + Clear Hash per position, exe `forge_r10_b.exe`; results `opus_r10/logs/wac/`.

| eval | solved | only this side vs OFF | positions with a bestmove |
|---|---|---|---|
| OFF (lock: HCE + FORGENN2 residual) | 272 / 300 | - | 300 / 300 |
| smoke net 64x32x32 | 260 / 300 | +13 / -25 | 300 / 300 |
| R6 bench net 256x32x32 | 242 / 300 | +11 / -41 | 300 / 300 |

The ON path finds mates (mate scores on 70 and 71 positions vs 68 OFF) and answers every position. Both nets are tiny
test nets: the smoke net saw 1.2M training positions (about 0.5M distinct, Forge self-play), the R6 net is R6's
crash-fix check export (`F:\opus_scratch\r6\bench\crashfix_check`, 2026-10-29 14:07: 4 epochs x 204,800 positions of
the trainer repo's own `.pgo/small.binpack`, 12 s on the GPU). Fewer solved positions are expected and say nothing
about a trained net.

## Gate command (for a trained K32H3^ net; SPRT [0,10] nElo, cap 3000, vs AL1 s198)
Base = the queue's AL1 exe `C:\Users\Administrator\grok-pc\forge_push\bin\forge_h256_s198.exe` (sha256 `833c47f3...`,
name `base_AUTOLOCK_1_gate120_e32f003rec_s198`, as in gates G98-G123). Candidate = the R10 exe built from this branch
with the box recipe, copied to the bin folder, with the net named by the option (Windows path, no spaces). Settings as
the queue's current gates (tc 10+0.1, Threads 2, Hash 16, OwnBook false, 8moves_v3.pgn, conc 4; `<queue>` = the
queue's own start / srand):

```
fastchess.exe -engine name=cand_r10_halfka cmd=C:\Users\Administrator\grok-pc\forge_push\bin\GATE_EXE option.Threads=2 option.Hash=16 option.OwnBook=false option.EvalFileHalfKA=C:\Users\Administrator\grok-pc\forge_push\bin\NET.nnue -engine name=base_AUTOLOCK_1_gate120_e32f003rec_s198 cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_h256_s198.exe option.Threads=2 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=<queue> -srand <queue> -games 2 -repeat -rounds 1500 -concurrency 4 -sprt elo0=0 elo1=10 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -pgnout file=<gate>.pgn
```

`GATE_EXE` and its sha256 are in the "Gate exe" line below. Before queueing: `opus_r10/tools/halfka_uci_check.py <exe>
<net>` (loads, ON bench stable, bad files rejected) and the parity check of the new net (`forge-halfka-parity-test`
skill: `parity_nnue_pytorch.py` + `halfka_tool eval` on `opus_r10/parity/fens_12k.txt`, must be 12,000 / 12,000).
The two nets in this branch are test nets, not candidates: a gate with them would only measure that they are tiny.

## Open risks
- **Naming**: the job asked for HalfKAv2_hm; the R6 trainer has no set of that name. K32H3^ is HalfKAv2_hm's king
  mirroring and 704 planes plus 3 material states per king bucket. A net from another trainer version or another
  feature set has different hashes and is rejected, never misread.
- **The trainer's default net is not supported**: `Full_Threats+PP_3Wide+K32H3^` adds two more feature segments
  (threats and pawn pairs) to the FT, with a different feature hash. Training for Forge must pass `--features K32H3^`.
- **Trainer changes**: the hashes catch shape and feature-set changes, not a change in the trainer's rounding or
  activation scales. Every new trainer commit needs the 12,000-position parity run again.
- **int16 bound**: the loader rejects a net if `|bias| + 32 x max|w|` exceeds 32767 for any FT output. That bound is
  conservative (it assumes 32 active features all at the largest weight); a strongly trained net may trip it and would
  then need a tighter per-output bound or int32 accumulators.
- **Eval scale and search margins**: ON, the net is the whole evaluation; the lock's search margins (futility, razor,
  SEE, LMR) were tuned on the HCE + FORGENN2 scale. A gate measures net + margins together; a net could need an eval
  scale option or its own tuning before it can pass.
- **Memory to train on the box CPU**: nnue-pytorch held 5.1-5.4 GB private memory even at L1 64 (both smoke runs hit the
  R6 RAM guard's 7 GB floor); real training belongs on the GPU path of R6, at a size the live trainer leaves room for.
- **Speed**: the HalfKA path is slower per node than the lock's eval on the test nets (see NPS); a trained net of the
  same width costs the same per node, but its tree differs, so only a gate tells whether the net pays for itself.

## Owner items
- Train a K32H3^ net with the R6 trainer (`--features K32H3^`, L1 256 or 512 to keep the cost near FORGENN2), export it
  with the trainer's `serialize.py`, run the checks above, then queue the gate.
- The QA / Code Review notes named in the job (`/workspace/forge-hashes/QA_R6AMD_20261030.md`, `CR_R6AMD_20261030.md`)
  were not on this PC; R10 did not read them.
- The gate uses the queue's current Threads 2 / conc 4 settings; the older AL1 gates ran Threads 1 / conc 8. Pick one
  and keep it for every HalfKA gate (never pool across settings).
