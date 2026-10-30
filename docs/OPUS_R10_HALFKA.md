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

## 200 fast games (no illegal moves)
`opus_r10/tools/fast_games.py`: fastchess, the R10 exe with the smoke net vs the same exe with the option off, 2+0.02,
Threads 1, Hash 16, OwnBook false, 8moves_v3.pgn, conc 2, pinned to CPUs 4-11 at BelowNormal (8 min 29 s, 04:13-04:21).
**200 / 200 games finished normally: no illegal move, no crash, no disconnect, no time loss** (`opus_r10/logs/
fast_games_smoke.log`, `games_smoke/fastchess.out`; the PGN, 574,523 bytes, stays in `F:\opus_scratch\r10\games_smoke`,
sha256 in `games_pgn.sha256`). The smoke net scored 0.5 / 200: a 1.2M-position test net against the lock's eval.
Its eval has the right sign (`opus_r10/logs/sign_check.log`: a queen up is +426 cp for the side to move and -395 for
the side without it, mirrored positions give equal values), but a compressed scale (a queen is about 4 pawns for the
smoke net and 2.5 for the R6 net) under search margins tuned for the lock's scale.

## NPS: HalfKA ON vs the lock's eval (FORGENN2 + HCE), first kernels
`opus_r10/tools/nps_opts_ab.py`, one exe (`forge_r10_b.exe`), option sets in a rotated order, 3 rounds, `bench 13` and
`bench 16` (Threads 1), CPU-time NPS of the bench window, CPUs 4-11 at BelowNormal beside the gate and R9 (03:46-04:11).
Gain vs OFF = median of the per-round ratios [min..max]. The ON and OFF trees differ (different evaluations), so this
mixes the cost per node with the tree shape; it is not a speed claim.

| set | d13 CPU NPS | vs OFF | d16 CPU NPS | vs OFF |
|---|---|---|---|---|
| OFF (lock eval) | 1,839,635 | - | 1,935,949 | - |
| smoke 64x32x32 | 1,472,589 | -22.0% [-22.6..-15.1] | 1,463,799 | -23.9% [-25.0..-23.6] |
| R6 256x32x32 | 1,217,223 | -33.8% [-36.0..-29.5] | 1,165,008 | -39.8% [-40.8..-39.0] |
| untrained 1024x32x32 | 743,098 | -60.1% [-60.6..-58.3] | 730,752 | -62.3% [-62.9..-61.7] |

## Where the time goes (ns per call, `halfka_tool speed`, 12,000 positions x 50, one random legal move each)
| stage | L1 64 v1 -> v2 | L1 256 v1 -> v2 | L1 1024 v1 -> v2 |
|---|---|---|---|
| refresh, one perspective | 96.7 -> 87.1 | 171.9 -> 189.4 | 540.2 -> 626.5 |
| update from the parent, one perspective | 22.6 -> 17.2 | 39.7 -> 31.4 | 126.0 -> 124.5 |
| forward (pairwise, l1, l2, output) | 288.4 -> 162.6 | 377.1 -> 218.8 | 872.5 -> 279.2 |
| forward with the scalar code | 299.2 / 300.2 | 354.2 / 333.8 | 608.3 / 676.8 |

The lock's eval in the same tool: FORGENN2 refresh 387-433 ns (both perspectives), update 55-58 ns (both), evaluate
46-49 ns, plus the HCE (public `evaluate`, an upper bound of the search's runtime path) 243-249 ns. 21,741 of 24,000
perspective-moves kept the orientation (an update); the rest need a refresh (king move, mirror flip, state change).
Findings that drove v2: the first AVX2 forward was **slower than the plain C++ loop** at L1 1024, because GCC
vectorises the scalar dot product with AVX-512 VNNI (`vpdpbusd`, zmm) under `-march=znver5`; the forward also zeroed a
4 KB buffer per call; the l1 layer did one horizontal sum per output.

## Speedup done in R10 (v2 kernels, outputs unchanged)
- l1 and l2 weights are regrouped at load time into blocks of 4 inputs x every output; the forward broadcasts each
  block of 4 inputs and multiplies it with all outputs at once (AVX-512 VNNI `dpbusd` on znver5, AVX2 `maddubs`+`madd`
  elsewhere), **skipping blocks whose 4 inputs are zero**, with no horizontal sums; the output layer's dot product uses
  VNNI; no zero fill of the 4 KB input buffer; the accumulator update loads each chunk of the parent row once, applies
  all changes in registers and stores once; AVX-512 row kernels for refresh.
- Proof: raw outputs **byte-identical to v1 (and so to nnue-pytorch) on 12,000 + 12,000 + 2,000 positions with both the
  AVX-512 VNNI build and an AVX2-only build (`-march=x86-64-v3`)**, SIMD == scalar on every position
  (`opus_r10/logs/parity_v2_kernels.log`); walk 311,568 + 49,934 checks, 0 mismatches, in both builds (`walk_v2.log`);
  in-search verify **3,208,448 rows equal a full refresh** (Threads 3, `verify_search_c.log`); OFF identity ALL OK
  (`identity_off_c.log`); ON bench unchanged (489,790 / 305,623) and every bad file still rejected (`uci_check_c_*.log`).
- Speed, same net in both builds, so the trees are identical (equal node counts on every run) and the ratio is the
  per-node cost alone. `nps_opts_ab.py` with the new `exe=` sets (v1 `forge_r10_b.exe` vs v2 `forge_r10_c.exe`), 10
  rounds in rotated order, CPU-time NPS, CPUs 4-11 at BelowNormal beside the gate and R9 (04:24-04:35); `nps_ci.py`:
  geometric mean of the paired ratios with a 95% t-interval (`opus_r10/logs/nps_v2_*.log/.json`):

  | net | d13 | d16 |
  |---|---|---|
  | R6 256x32x32 | **+22.8% [+20.0, +25.6]** | **+20.1% [+18.3, +21.9]** |
  | A/A control (v1 vs v1) | -0.0% [-1.8, +1.8] | -0.1% [-1.6, +1.3] |
  | smoke 64x32x32 | +17.9% [+15.4, +20.6] | +16.2% [+13.6, +18.9] |
  | untrained 1024x32x32 | L1024_PENDING | - |

  Measured on the loaded PC, so the numbers are advisory; the PC speed rule (lower bound >= +2% at d16 and d20 on the
  quiet runner) was not run. The OFF path is not touched by v2 (OFF identity is the lock's; see the OFF A/B below).

## Next speedups (measured where they come from; none of them done)
1. **64-byte alignment** of the FT weight rows and the accumulator rows. The v2 AVX-512 refresh got slower than v1's
   AVX2 one at L1 256 and 1024 (172 -> 189 ns, 540 -> 627 ns): the vectors are 16-byte aligned, so every 64-byte load
   or store of a row crosses two cache lines.
2. **Vectorised activations**: 2 x 32 scalar square / clamp steps per evaluation. They can be done exactly in 32-bit
   lanes, because the square saturates at 127 for |s| >= 16,321 (l1) and |s| >= 8,160 (l2): clamp |s| to 16,383 / 8,191
   first.
3. **Refresh cache per feature bucket**: 9.4% of the perspective updates in the timing set are refreshes (king move,
   mirror flip, queen/rook state change), at 5-6x the cost of an update. Keeping the last row and piece set per
   (perspective, bucket) turns a refresh into a difference against the cached position.
4. **Prefetch FT rows when the move is recorded**: at L1 1024 an update costs 125 ns vs 31 ns at L1 256 (a 69 MB weight
   table; the rows miss the caches). `record_move` knows the changed features one ply before they are needed.
5. **Net width**: the forward cost grows little with L1 (219 ns at 256, 279 ns at 1024), the update and refresh costs
   grow linearly. A trained net of the same strength is cheaper at 256-512 than at 1024.

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
