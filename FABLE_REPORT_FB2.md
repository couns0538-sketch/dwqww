# FABLE_REPORT_FB2.md — pack FB2 (Fable 5.1, 2026-10-28) — IN PROGRESS

Base of every `fable-fb2-*` branch: `fable-nnue-arch` head `08b589e1` (= AL1 lock `d4f4312` + CI baseline + the FB1
NNUE v3 engine/trainer). No Elo claims anywhere (no gate was run); no speed claims (loaded PC: gates, self-play and
production NNUE training ran throughout; my work at `nice -n 19`, one training thread). Machine exclusive: no.
No sub-agents were used (user instruction); nothing under `F:\forge_nnue_train`, `selfplay_out` or `forge_push` was
written; all outputs are under `F:\opus_scratch\fable\`. Order after the user's request "shorter jobs first": J2,
J3, J4, J6 were finished/advanced while J1 trains; J5 and J7 come last.

| job | branch | status |
|---|---|---|
| J1 real v3 net at scale | `fable-fb2-j1` | data split DONE, trainer DONE, training RUNNING (ckpt 1: 0.016094 vs AL1 0.014417); exe/NPS/sanity games pending |
| J2 datagen upgrade | `fable-fb2-j2` | **DONE** (engine mode, FGB1 format, converter, exact round-trip tests, 10-min smoke) |
| J3 search improvements | `fable-fb2-j3` | **DONE**: four options, unit tests 121/0, identity ALL OK, CI green, 2,500 self-play games 0 errors, LMR fit, gate entries |
| J4 time management v2 | `fable-fb2-j4` | **DONE**: simulator (2000 games x 2 TCs x 3 scenarios, 0 flag losses), identity ALL OK, CI green, 220 real-clock games 0 flag losses |
| J5 SMP v2 | `fable-fb2-j5` | analysis + code + tests + TSan hook written; build running; unit tests and 1/2/3-thread measurement wait for free CPU threads |
| J6 gate design | `F:\opus_scratch\fable\GATE_BOUNDS.md` (copy `fable_fb2/j6/`) | **DONE** (proposal only) |
| J7 NNUE v4 ideas | `fable-fb2-j7` | trainer prototypes written and smoke-tested (`--l2`, `--pairwise`, `--float-exact`); the 30-minute comparison runs wait for a free CPU thread |

## J1 — real v3 net, trained at scale (`fable-fb2-j1`, folder `fable_fb2/j1/`)

### Data split (DONE)

`tools/nnue/fable_nnue_data.py split` (new; unit test `tools/nnue/test_fable_nnue_data.py` PASS on synthetic shards
with a Python-set reference: dedup, holdout/training disjointness, unaltered rows, FPOS/FHCE round trip, phase
targets, manifest check, determinism). Real run on the 35 production shards (6.4 min, one thread, read-only
inputs; log `fable_fb2/j1/logs/split_real.log`, manifest copy `fable_fb2/j1/logs/MANIFEST.json`):

| item | value |
|---|---|
| input rows | 288,302,469 (33 training shards 271,913,894 + holdout shards 013/014 16,388,575) |
| exact duplicates (board + side to move), first copy kept, holdout rows win | 85,223 removed (0.030%); 1,352 inside 013/014 |
| training rows written | **271,830,023** in 64 globally shuffled shards `F:\opus_scratch\fable\data\train\fb2_train_000..063.pos/.hce` (4.24-4.25M rows each, 9.4 GB, read-only) |
| holdout | **200,000 rows** `F:\opus_scratch\fable\data\holdout\fb2_holdout_200k.pos/.hce`, drawn from the deduplicated 013/014 pool (16,387,223 rows), phase-stratified |
| phase histogram (piece-count buckets 0..7) train | 5.77 / 18.95 / 15.31 / 12.15 / 10.81 / 10.99 / 12.73 / 13.29 % |
| phase histogram holdout | identical to 4 decimals (11549 / 37896 / 30627 / 24294 / 21614 / 21971 / 25464 / 26585 rows) |
| scratch left in place (owner may delete) | `F:\opus_scratch\fable\data\work\` 14 GB of hash partitions and scatter records |

Why 013/014 only for the holdout: the AL1 net never trained on those shards, so AL1 and every J1 net are scored on
positions neither has seen; the rest of 013/014 is used nowhere (other plies of the same games would leak).

### Reference scores on the 200k holdout (exact, S31 scorer; `fable_fb2/j1/logs/al1_fb2_holdout_score.json`)

| net | MSE b0.6 (lock blend, the decision metric) | b0.8 | b1.0 |
|---|---|---|---|
| HCE alone | 0.017141 | 0.008421 | 0.005131 |
| **AL1 lock net e32f003rec** (`src/nnue_weights.inc`, md5 f5f6a34a) | **0.014417** | 0.006808 | 0.004629 |

(The run's `--target-loss` is 0.014310, the AL1 value on the full 1M-row S16 subset, set before this number
existed; it is stricter than 0.014417, so a net reaching 0.014417 keeps training, which is harmless. The table
below compares with 0.014417.)

### Trainer upgrade (DONE; `tools/nnue/fable_nnue_train.py`, driver `tools/nnue/fable_nnue_chunks.py`)

New: `--resume` (model, Adam state, schedule position, numpy and torch RNG state; a checkpoint's config must match the
command line), `--ckpt-every-minutes` (atomic `ckpt.pt`, exported `ckNN_stepS.fnn3`, exact integer holdout score at
b0.6/b0.8/b1.0 with a per-phase breakdown, engine parity through `forge_nnue_v3_tool eval` on 10,000 positions,
`status.json`, `best.fnn3`), stop rules `--target-loss` and `--plateau N` (N checkpoints without improving the best
exact b0.6 by `--plateau-eps` 1e-5), `--max-minutes` pauses a chunk and the driver resumes it, LR warmup
(`--warmup-steps`) and the WDL-lambda schedule (`--blend-schedule linear|cosine --blend-start --blend-end`).
Smoke tests (H128, 300k rows of the S16 holdout subset; logs `fable_fb2/j1/logs/smoke_train*_log.txt`): checkpoints
with exact score + parity PASS (10000/10000, max float-int 1.02 cp), pause after `--max-minutes`, resume continues
step/seen/schedules/checkpoint numbering, stop at the horizon.

### Training run (RUNNING; `F:\opus_scratch\fable\fb2\train_j1\`, log copy `fable_fb2/j1/logs/train_j1_log.txt`)

Standalone (non-residual) H512, 8 mirrored king buckets, 8 output buckets, factoriser, QAT int16 (FB1 M3), batch
8192, Adam, LR 1e-3 cosine to 5e-5 over 93,000 steps (762M positions, about 8.7 h at the measured 24.2k positions/s
on one thread), warmup 500 steps, WDL lambda 0.9 -> 0.6 linear, shards sampled proportional to rows, buffer 8 x 250k
rows. Checkpoint every 30 min; stop when exact b0.6 <= target or 3 checkpoints without improvement. Chunks of 240 min
(driver `fable_nnue_chunks.py`; started 16:36 PC time).

| ckpt | step | positions | train min | exact b0.6 | b0.8 | b1.0 | per-phase b0.6 (few pieces -> many) | vs AL1 0.014417 | parity 10k |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 5,307 | 43.5M | 30 | **0.016094** | 0.007836 | 0.005008 | .0067 .0074 .0109 .0161 .0200 .0222 .0226 .0241 | +0.001677 (HCE is 0.017141) | PASS 10000/10000, max 1.02 cp |
| 2 | 10,374 | 85.0M | 60 | **0.015684** | 0.007508 | 0.004761 | .0059 .0069 .0105 .0155 .0195 .0220 .0223 .0239 | +0.001267 | PASS 10000/10000, max 1.02 cp |
| 3 | 15,476 | 126.8M | 90 | **0.015563** | 0.007420 | 0.004707 | .0057 .0067 .0103 .0153 .0193 .0221 .0223 .0239 | +0.001146 | PASS 10000/10000, max 1.02 cp |
| 4 | 20,602 | 168.8M | 120 | **0.015444** | 0.007341 | 0.004667 | .0053 .0066 .0102 .0152 .0192 .0218 .0222 .0238 | +0.001027 | PASS 10000/10000, max 1.02 cp |
| (next checkpoints: `status.json` in the run dir; `tools/nnue/fable_nnue_ckpt_table.py <run>` prints this table) | | | | | | | | | |

Torch quick validation (200k rows, blend 0.6) on the way: 0.105583 (0) -> 0.017014 (14.7M) -> 0.016369 (29.6M).

### Engine, NPS and sanity games (with the checkpoint-1 net; repeated with the final net if the session allows)

- `forge_fable_v3.exe` = box recipe of the J1 tree (the FB1 engine sources: `FORGE_EXTRA_SRCS="src/nnue_v3.cpp
  src/search_v3.cpp"`), sha256 `70a19218…`, 0 warnings, FMA 0; **OFF identity `ALL OK`** (bench d11/13/16/20/22 =
  312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690; `fable_fb2/j1/logs/finish_ckpt1/identity_off_v3.log`).
- NPS vs AL1 (`fable_nnue_nps.py`, ABBA, 3 rounds, Threads 1, Hash 16, CPU time; the ON side runs the standalone
  ckpt-1 net `ck01_step0005307.fnn3`, the OFF side the AL1 lock net; the trees differ, so this is a per-node cost
  ratio on a loaded PC, advisory): depth 16 **ON/OFF 1.114 (+-0.014)**, depth 20 **1.063 (+-0.009)**; time per node
  0.90 / 0.94 of AL1 (`logs/finish_ckpt1/nps_vs_al1.log`). FB1's 1.17-1.19 was measured with a barely trained net on
  a smaller tree; the direction (standalone v3 faster per node than the AL1 residual path) holds.
- 200 sanity games vs AL1 at 1+0.01 (100 per colour, `fable_timeman_games.py` with `NNUEArchFile`/`NNUEArch=true` on
  the v3 side; python-chess legality of every move, crash / illegal-move / flag check only, no Elo claim):

| v3 side (ckpt-1 net) | games | moves | crashes / illegal / flags | result (v3 W-L-D) | evidence |
|---|---|---|---|---|---|
| white (ckpt-1 net) | 100 | 12,278 | 0 / 0 / 0 | 19-42-39 | `logs/finish_ckpt1/games_v3_white.json` |
| black (ckpt-2 net: `best.fnn3` was refreshed by checkpoint 2 at 17:39, between the two runs) | 100 | 12,579 | 0 / 0 / 0 | 8-52-40 | `logs/finish_ckpt1/games_v3_black.json` |

The early nets lose more than they win against AL1, as their holdout loss predicts; the games only show that the
engine plays legally and stably with the v3 net (max 245 ms per move at 1+0.01, no flag). The chain's full-subset
score (`logs/finish_ckpt1/score_full_subset.log`, 1,024,286 rows of 013+014) ran on the ckpt-2 file:
**b0.6 0.015598** / b0.8 0.007451 / b1.0 0.004715 vs AL1 0.014310 / 0.006735 / 0.004572 and HCE 0.017059 (the
explicit re-score of `ck02_step0010374.fnn3` is in `logs/score_ck02_full_subset.log`).

## J2 — self-play datagen v2 (`fable-fb2-j2`, folder `fable_fb2/j2/`) — DONE

- Engine: UCI command `datagen ...` (`include/forge/datagen2.hpp`, `src/datagen2.cpp`, hook in `src/uci.cpp`; the
  normal paths are untouched: box exe OFF identity `ALL OK`, 0 warnings, FMA 0; `fable_fb2/j2/logs/identity_off_j2.log`).
  FGB1 compact game format (start FEN + 5 bytes per ply: move, score, flags; FNV-1a trailer), opening diversity
  (jittered random plies, softmax-sampled plies from per-move shallow searches, evaluation cap with redraw, FEN/EPD
  book), win and draw adjudication, filters (in check, capture/promotion within the first k PV moves, mate scores,
  score cap, min ply, random subsampling, optional gives-check), deterministic per-game seeds (same seed = same
  bytes), direct FPOS/FHCE output (`--pos`) and text, JSON summary; `datagen convert <fgb> <prefix>` replays the games
  with the engine's Board and recomputes the HCE labels.
- Tests: `forge_datagen2_tests` (CTest; 2147 checks, 0 failures: 153-move encoding round trip incl. castling /
  promotions / en passant, serialisation + corruption detection, 4 played games with flag/rule consistency, same
  seed byte-identical, direct == converter files) and the independent python-chess decoder
  `tools/nnue/fable_datagen_decode.py` (rows rebuilt without the engine == engine rows, byte for byte). Full CTest
  15/15 (`logs/ctest_j2.log`), CI run on the push.
- 10-minute smoke (box exe, 5000 nodes, 1 thread, `F:\opus_scratch\fable\datagen\smoke_j2.*`): **1,758 games,
  263,270 plies, 246,243 searched, 115,862 records** (filters: 24,227 in check, 64,581 noisy PV, 1,794 mate, 1,818
  score cap, 11,101 early, 38,790 subsampled), 395 opening redraws, 1,758 distinct post-opening positions, results
  495/723/540 (B/D/W), terminations adj_win 1016, adj_draw 353, repetition 147, fifty 102, max_ply 69, insufficient
  51, checkmate 19, stalemate 1; 1.26 G nodes. **Direct .pos/.hce == converted .pos/.hce (sha256 equal), python-chess
  decoder: 115,862 rows equal, 0 replay problems.** Compact file 1.43 MB vs 4.29 MB FPOS+FHCE (5 bytes per ply incl.
  the unkept plies vs 37 bytes per record). Evidence `fable_fb2/j2/logs/`.

## J3 — search improvements behind options (`fable-fb2-j3`, folder `fable_fb2/j3/`) — code DONE, self-play RUNNING

Four UCI check options, default false; all off = lock (box exe `forge_fable_j3.exe` OFF identity `ALL OK`, 0
warnings, FMA 0). `IDEA_SOURCE.md` lists the ideas (Stockfish-family techniques, own fitting method); no code copied.

| option | content |
|---|---|
| `CorrHistV2` | continuation (1- and 2-ply) correction history on top of the pawn/material corrections |
| `SingularV2` | triple extensions (non-PV, margin 80, budget 4, no TT capture), PV double extensions (margin 60, budget 3), multicut when the singular search fails high, negative extensions -3 / -2 |
| `LmrTableV2` | logistic model of P(reduced search raises alpha) fitted on **1,268,077 LMR decisions of bench 16** (quiet 1,098,387 rows, raise rate 4.1%, pseudo-R2 0.193; noisy 169,690, 2.9%, 0.342; calibrated deciles in `logs/lmr_fit_bench16.log`); reduction = lock table + 0.75 ply per sd of the fitted log-odds, continuous history term |
| `TtPruneV2` | TT move exempt from futility/history/SEE pruning, IIR at cut nodes whose TT move carries an upper bound, opponent-worsening RFP margin, improving in quiet futility and history pruning |

Tests: `forge_fb2_j3_tests` (CTest; 121 checks, 0 failures: every option changes all 6 depth-10 trees and restores
the exact node counts when switched off; CorrHistV2 arithmetic through a friend probe incl. saturation and null/root
keys; LmrTableV2 bounds/monotonicity; mates found and 25 random positions sane with all options on). Full CTest 15/15.
Self-play: `opus_selfplay_check.py` (R3-1 checker, python-chess legality of every best move, mixed go modes,
isready barriers), 500 games per option and all-on, one at a time on one thread (about 23 min each):

| configuration | games | plies | errors (crash / illegal / double bestmove / timeout / malformed) |
|---|---|---|---|
| CorrHistV2 | 500/500 | 59,794 | **0** (`logs/selfplay/CorrHistV2.summary.json`) |
| SingularV2 | 500/500 | 59,218 | **0** (`logs/selfplay/SingularV2.summary.json`) |
| LmrTableV2 | 500/500 | 60,105 | **0** (`logs/selfplay/LmrTableV2.summary.json`) |
| TtPruneV2 | 500/500 | 58,640 | **0** (`logs/selfplay/TtPruneV2.summary.json`) |
| all four on | 500/500 | 60,139 | **0** (`logs/selfplay/AllOn.summary.json`) |

2,500 games, 297,896 plies, 0 errors of any kind (each configuration also passed the checker's preflight: the
option changes the bench-11 node count, so the runner's "option did not apply" test would fire if it were inert).

Gate entries: `fable_fb2/j3/GATE_ENTRY.md` (one per option vs all-off, design 1 of GATE_BOUNDS.md).

## J4 — time management v2 (`fable-fb2-j4`, folder `fable_fb2/j4/`) — code DONE, games RUNNING

`TimeManV2` (default false; off = lock, box exe OFF identity `ALL OK`): node-based soft budget at the measured
speed, scaled by the lock's stability / effort / score-drop factors, next-iteration prediction (EBF of the last two
iterations), in-search soft node limit (budget x 130%), adaptive clock reads near the hard deadline (64..1024 nodes)
in search and quiescence. Pure decision code in `include/forge/timeman.hpp`, shared with the simulator.

| harness | result |
|---|---|
| `forge_timeman_sim 2000` (CTest): 2000 games x {1+0.01, 10+0.1} x {lock v1, v2}, 1 ms latency, Move Overhead 10 | **0 flag losses** for both; moves beyond the hard deadline 18,622 (v1) vs 4,885 (v2) at 1+0.01, 12,816 vs 0 at 10+0.1; max overshoot 2.6 ms (v1) vs 1.3 ms (v2); used/soft 1.47 vs 1.17 (v1 runs its last iteration to the hard limit) |
| same with 5 ms scheduler stalls on 5% of moves | 0 flag losses; max overshoot 6.8 / 6.0 ms (the stall itself) |
| same at 300 nodes/ms (sanitizer-like speed) | 0 flag losses; max overshoot 9.4 ms (v1) vs 2.5 ms (v2, adaptive reads) |
| real games over UCI (`fable_timeman_games.py`), 100 games at 1+0.01, TimeManV2 both sides | **PASS: 0 flag losses**; 13,079 moves, max 122 ms per move, min clock 33 ms, 2 moves used over half the remaining clock (`logs/games_1s_v2.json`) |
| 100 games at 1+0.01, lock time management both sides | PASS: 0 flag losses; 13,307 moves, max 230 ms per move, min clock 27 ms, 27 moves over half the clock (`logs/games_1s_v1.json`) |
| 20 games at 10+0.1, TimeManV2 both sides | PASS: 0 flag losses; 2,543 moves, max 955 ms, min clock 212 ms (`logs/games_10s_v2.json`) |

CI (opus-ci release / ASan / TSan) on the J4 head: success. Reading: v2 never runs a move into the hard deadline
at fast TC (the lock's last iteration does, 27 moves over half the clock vs 2), i.e. it keeps a larger reserve;
whether that plays better is a gate question (GATE_BOUNDS design 1).

## J6 — gate design (`F:\opus_scratch\fable\GATE_BOUNDS.md`, copy in `fable_fb2/j6/`) — DONE (proposal only)

Key facts: 970 games/h; at the PC's 77% draw rate 1 Elo = 2.16 nElo, so [0,10] nElo is [0, 4.6] Elo; the expected
games to decide at elo1 are 2 x 2.944 x 0.9 / (0.002878 x nElo1)^2 = 25,600 ([0,5]), 6,400 ([0,10]), 2,850 ([0,15]);
the 1500-game cap decides nothing below about +13 Elo (simulation of 10 designs x 8 true Elos, the normal GSPRT that
reproduces gate38's printed LLR 1.11). Recommendation: search features [0,10] cap 6000 (P(H1) 0.96 at +8, 0.61 at
+5, false accept 3%), speed changes = quiet-runner NPS + non-regression [-10,0] cap 3000, nets = holdout first then
[0,20] cap 1500 screen. Ranking by expected Elo per gate hour under stated priors: J1 net (wide prior; only after it
beats AL1), CorrHistV2, LmrTableV2, TtPruneV2, SingularV2, R3 search changes, TimeManV2, then the speed switches
(not worth an Elo gate). Simulator `fable_fb2/j6/gate_bounds_sim.py`, tables `gate_bounds_tables.md`.

## J5 — Lazy SMP v2 (`fable-fb2-j5`, folder `fable_fb2/j5/`) — code written, measurements pending

Analysis of the R3-6 data (`fable_fb2/j5/IDEA_SOURCE.md`): the lock's helpers run the same depth sequence in lockstep
with the main thread (lead 0.5-0.6 ply), so the main thread's critical path shrinks only to 0.80x (T2) / 0.68x (T3)
of its single-thread nodes while total nodes inflate 1.7-2.0x; R3-6's "helpers past depth" fix removed idle time
but not the duplication (no time-to-depth gain on quiet runners). Fix implemented behind `SmpV2` (default false,
inert at Threads 1): odd helpers search one ply ahead, even helpers use 2x/3x aspiration windows, and the deepest
completed result of any thread is reported (`fb2::smp_depth_skew`, `smp_aspiration_multiplier`,
`smp_select_result`). Tests `tests/fb2_j5_tests.cpp` (CTest; 3 threads for seconds); the CI TSan hook now also runs
SmpV2 searches at Threads 2/3/4. Measurement tool `tools/smp/fable_smp_ttd.py` (R3-6's 30 positions, fixed depths,
fresh process per run, paired on/off ratios). Build in progress; the Threads 2/3 runs need the CPU budget that the
training and the J3 self-play occupy (scheduled after the self-play, Threads 3 while the training is paused at a
checkpoint boundary).

## J7 — NNUE v4 ideas (`fable-fb2-j7`, folder `fable_fb2/j7/`) — prototypes written, runs pending

Trainer-only prototypes on top of the J1 trainer: `--l2 N` (second layer 2H -> N -> 1), `--pairwise` (us*them
interaction term), `--float-exact` (float holdout metric so prototypes without a v3 file compare with the baseline),
plus the existing `--hidden 1024` and `--king-buckets 16`. Smoke-tested (prototype checkpoints as `.pt`, float
score + per-phase breakdown, `logs/smoke_*`). Protocol in `fable_fb2/j7/README.md` (30 minutes per run on one
thread, same data/seed/batch/LR/WDL schedules as J1, float holdout b0.6 on the 200k FB2 holdout at 10/20/30 min).

| run | 10 min | 20 min | 30 min (positions seen) |
|---|---|---|---|
| baseline H512 / 8 king buckets | 0.017107 (14.0M) | 0.016408 (27.5M) | **0.016088** (41.3M) |
| H1024 / 8 (half the throughput) | 0.017935 (7.6M) | 0.016738 (14.9M) | running |
| H512 / 16 king buckets | queued | | |
| H512 / 8 + second layer 16 | queued | | |
| H512 / 8 + pairwise term | queued | | |

(The J1 run's exact score at 43.5M positions was 0.016094: the float metric and the integer file agree to 1e-5.)

## Next steps for the next model
1. J1: watch `F:\opus_scratch\fable\fb2\train_j1\status.json`; the driver resumes after a crash; restart by hand with
   the command in `fable_fb2/j1/README.md` plus `--resume <run>/ckpt.pt`. When it stops: build the exe
   (`FORGE_EXTRA_SRCS="src/nnue_v3.cpp src/search_v3.cpp" build_pc.sh ... forge_fable_v3.exe`), identity, NPS
   (`fable_nnue_nps.py <exe> best.fnn3 3 16 20`), 200 games vs AL1 (`tools/timeman/fable_timeman_games.py` with
   `--opt-white NNUEArch=true --opt-white NNUEArchFile=<best.fnn3>`, then colours swapped), score `best.fnn3` on the
   full 1M-row subset and compare with 0.014310.
2. J3: read `fable_fb2/j3/logs/selfplay_*` when the runs finish (0 errors expected), record them in the report.
3. J4: record `games_1s_v1.json` and `games_10s_v2.json`.
4. J5 and J7 as specified in the brief.
