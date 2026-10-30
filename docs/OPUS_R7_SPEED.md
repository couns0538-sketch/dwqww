# OPUS R7 SPEED: AMD training path, data pipeline, engine NPS, gate throughput — DONE

Branch `opus-r7-speed` (from main 5176ddf7). Engine changes live on `opus-r7-nps` (from the R5D engine head
`opus-r5d-matefix` 5882c383, because main carries no engine source). PC clock times. Machine exclusive: no
(gate conc 8, the live NNUE trainer on the GPU and self-play kept running). Time: job start 16:01, commits
16:08:37-17:17:30 (11 commits on the two branches), final report ~17:25.

## Summary
| job | result | numbers |
|---|---|---|
| J1 Forge v2 net on the AMD Triton path | DONE | **1.44M pos/s vs 363-396k plain (3.6-4.0x)**, batch 4096, 1 loader thread; parity max 1.59 cp on 10k; loads + benches in Forge |
| J2 .pos -> binpack + loader | DONE | the old tool was already 7.8 s per 10M shard; `fpos2sf_mt` 2.27 s (3 threads), byte-identical, verify 0 bad / 0 mismatches; loader 3.9-5.5M pos/s |
| J3 Forge NPS (Threads 1) | DONE | top 3: HCE eval 14.4%, picker 10.9%, TT probe 10.7%; **R7TtExclusive +3.6% (d16) / +4.0% (d20)**; R7QuietGen, R7EvalPrefetch, R7PrefetchEarly no measurable gain; OFF bench identical, CI green |
| J4 gate games/hour | DONE | running gate 996-1,002 games/h at conc 8; adjudication +3.1% (0 results changed) to +6.9% (0.37% changed); mini-gate 350 -> 365/h; concurrency is the only big lever but the trainer runs at Idle priority |

**To gate**: `F:\opus_scratch\r7\j3\exe\forge_r7_j3a.exe` (sha256 `61f641d8a2b5708d7de575cccf2e525e53627fc4625912f964e13bc236481454`,
source `opus-r7-nps` `2d9889cf`) with `option.R7TtExclusive=true` vs the same exe at defaults (node-exact: only speed
differs, so a non-regression SPRT). `forge_r7_j3b.exe` (`30bb0e20...`, `c34a9739`) has the same options plus
R7PrefetchEarly and gives the same nodes; either exe works for this gate.

**Incident (owner item)**: the live self-play (`forge_selfplay.py`, 2 workers at Idle priority pinned to CPUs
12-15) stopped writing at **17:04:36**; its processes are alive at 0 CPU (still so at 17:13). Its bounded output
queue (size 4) means a blocked main process stalls the workers and engines. The stall began while my second
conc-3 mini-gate ran (17:00:58-17:07:31, 3 BelowNormal engines without an affinity mask), so my load may have
triggered it. I did not touch the processes. From 17:10 every run of mine is pinned to CPUs 0-11
(`tools/r7_gate/run_pinned.py --mask 0x0FFF`). Restarting self-play is the owner's decision.

Rules kept: BelowNormal (`nice -n 10`), at most 3 CPU threads in total, every torch run inside the R6 RAM guard
(aborts below 7 GB free; lowest free RAM seen in any of my runs: 7.73 GB, see J1), GPU runs at smoke size only
(batch 4096, 1 loader thread), nothing in `F:\forge_nnue_train` touched, no process killed, no STOP/PAUSE file,
GPL code only in `tools/nnue_pytorch_amd/`, no Elo claims. Supervisor "adopted running job" count stayed 7; the
live trainer printed 1.29-1.31M pos/s before, during and after my GPU runs.

## J1 Forge-net training on the fast AMD path: DONE
Code: `tools/nnue_pytorch_amd/forge_v2/` (README, IDEA_SOURCE). Evidence: `logs/r7/j1/`.
- **Kernel**: one Triton kernel pair for Forge's v2 shape (32 mirrored king buckets x 768, hidden 256, SCReLU
  stm|other, 8 output buckets). Both perspectives in one program, K32H3 -> Forge remap inside the kernel, backward
  with fp32 atomics and torch's clamp-gradient rule. The output layer is `x @ w2^T` + bucket gather.
- **Correctness** (`test_forge_v2_kernels.py`): Triton == Grok Bot's plain path on 3 real batches (output diff
  <= 2.4e-7, every gradient <= 4.7e-10); planted errors caught 2/2.
- **Speed** (batch 4096, 1 loader thread, same data, interleaved; `logs/r7/j1/matrix1`, `pinned/`):

| path | pos/s |
|---|---|
| Grok Bot's original `train_forge_v2.py` (steady state, steps 400-600) | 363k |
| plain path in my harness (embedding_bag + Adam), 2 rounds | 396k / 386k |
| Triton FT + Adam | 1,016k / 895k |
| Triton FT + fused Adam | 1,000k / 886k (978k over a 12.4 s, 3000-step run) |
| Triton FT + fused Adam + torch.compile of the loss | 950k / 918k (no gain) |
| **Triton FT + fused Adam + pinned H2D (`--inflight 3`)** | **1,447k / 1,443k** (unpinned in the same rounds: 976k / 981k) |
| GPU-only ceilings (one batch reused): plain / Triton fused | 472k, 457k / 1,492k, 1,574k |
| data path alone (loader + H2D): setup DLL / clang23 DLL | 3.71M / 5.1M |

  The fast path is **3.6-4.0x the plain path** at the same batch; the loader is not the limit. Peak private memory
  of my process: 3.24 GB in every final configuration. Pinned without the in-flight cap held 0.75 GB more (the host
  ran hundreds of steps ahead); the cap fixed that at equal speed. Losses agree to ~1e-6 between all variants
  (atomic summation order).
- **Export + engine**: `r7_triton_s3000` (3000 steps x 4096 on shard 015 converted by J2's tool, 978k pos/s, loss
  0.0092) exported with Forge's own `tools/nnue/forge_nnue_v2.py` (fnv1a `0dd0ee89e440a9d8`, sha256 in
  `parity/ARTIFACTS_SHA256.txt`). In `forge_r7_base.exe` (the `opus-r7-nps` base, identity ALL OK): `NNUE v2:
  loaded ... king buckets 32 output buckets 8 hidden 256 mirrored`, readyok, bench 13 = 957,760 nodes (1.93M nps;
  the compiled-in net on the same exe: 862,329). Depth-8 sanity: startpos +19, queen down -782, knight up +367.
- **Parity** (10,000 positions from `nnue_v2_tool positions`, engine eval = `nnue_v2_tool eval` built from the
  same tree with the exe's flags): float trainer vs engine **max 1.59 cp** (mean 0.52, 0 positions over 2 cp),
  dequantised max 0.9998 cp (the engine truncates), feature keys 20,000/20,000, output bucket 10,000/10,000,
  Triton vs torch reference 0.0006 cp. PARITY PASS.
- Recommended command: `train_forge_v2_fast.py --backend triton --fused-adam 1 --pinned 1 --inflight 3`.
- Limits: pipeline proof, not a strength-tested net (12M positions). Bigger batches, more loader threads and L1 >= 1024
  were not run (PC rules while the live trainer runs).

## J2 Data pipeline speed: DONE (the old converter was already seconds, not hours)
Code: `tools/nnue_pytorch_amd/fpos2sf_mt/` (README, IDEA_SOURCE, `j2_check.sh`). Evidence: `logs/r7/j2/`.
- **Measured first**: Grok Bot's `fpos2sf.exe` converts a full 10M-position shard (015) in **7.8-8.2 s** (1 thread),
  and the live trainer loads its 305M positions from 37 `.pos` files in 7 s (its log). Neither step takes hours on
  this PC; the full 37-shard training set would take ~4 min with the old tool.
- **New `fpos2sf_mt`** (same CLI + `--threads`, streams 30,841-record units): full shard **6.0 s / 3.2 s / 2.27 s**
  with 1 / 2 / 3 threads (1.67M / 3.09M / 4.40M records/s, 3.4x the old tool at 3 threads; the 37 shards in ~1.2
  min), peak working set **8.5-12.8 MB**. The output is **byte-identical** to `fpos2sf.exe` for every case tried
  (sha256 `84e8ee6f...` for the full shard at 1, 2 and 3 threads; `.bin`; skip 7 / stride 3 / ply 17 /
  score-mult 2.5 / max 500k with `--fen-out`; a copy with planted bad records).
- **Verify** (`--verify`, own decoder square by square + the training loader's sequential reader): full shard
  10,000,000 records, **0 bad source records, 0 format errors, 0 mismatches, 0 missing**, loader reader 10,000,000
  records / 0 mismatches (5.2 s). Planted: 6 bad source records are skipped by both tools (bad=6, identical
  output, verify OK); a 1-byte corruption is reported as exactly 1 mismatch (VERIFY FAILED).
- **Loader** (nnue-pytorch C++ stream, K32H3, no skipping, CPU only, 2 rounds): setup DLL 3.93-3.98M pos/s,
  clang23 DLL 5.47-5.52M pos/s, the same with 1 and 2 worker threads: a serial stage inside the DLL (the binpack
  reader), not Python, sets the rate. It is 2.7-3.8x what the fastest J1 training path consumes (1.44M pos/s), so it
  is not the training bottleneck; a parallel binpack reader is left as an idea.
- **Finding (owner)**: binpack's move codec turns the converter's king-square dummy move (from == to) into
  `Move::null()` (from = to = square 64). With nnue-pytorch's default `filtered=True`, `isCapturingMove()` then reads
  `pieceAt(64)`, one past the 64-entry array (undefined behaviour). Grok Bot's and my trainers use `filtered=False`,
  so nothing is affected today; never train these files with `filtered=True` (or give FPOS records a real legal
  move in a future format).

## J3 Forge NPS (Threads=1): DONE, one real gain (+3.6-4.0%), two neutral options
Engine branch `opus-r7-nps`: base `opus-r5d-matefix` 5882c383, profile workflow `4c3577d7`, **engine change
`2d9889cf`**, report `5dd37b7d` (`opus_r7/j3/REPORT.md` there). Patch copy: `logs/r7/j3/`.
- **Top 3 hotspots** (perf on a quiet GitHub runner, bench 16, self time): HCE `evaluate_position` 14.4% (the eval
  is residual HCE + network), `MovePicker::next` 10.9%, `TranspositionTable::probe` 10.7%; then `nnue::update` 8.3%.
  In the PC's MinGW build every TT probe and store calls `__emutls_get_address` (emulated `thread_local`) inside
  `lock_stripe()` and then defers the lock, because bench and UCI `go` at Threads 1 already hold an exclusive lease.
- **Options** (`type check default false`, node-exact): `R7TtExclusive` (lock-free probe/store twins for the lease
  holder), `R7QuietGen` (quiet-only generation in the picker's quiet stage, same moves in the same order),
  `R7EvalPrefetch` (prefetch the child's HCE pawn-cache entry).
- **Identity**: OFF = every lock pin (bench 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete
  193690690); each option ON and all three ON: the same numbers. Quiet generator test: 816,100 positions identical
  in content and order, a planted mutant fails. Nodes equal in all 125 NPS runs.
- **NPS** (same exe, option via setoption, fresh process per run, 95% CI of paired ratios, A/A control
  -0.02% / -0.98%): **R7TtExclusive +3.59% [+1.38, +5.84] at d16, +3.97% [+1.23, +6.77] at d20** (15 runs; CPU time
  +3.07% / +3.80%); real, but the lower bounds miss the PC's +2% eligibility rule. R7QuietGen -0.08% / -1.51% and
  R7EvalPrefetch -0.60% / -1.33%: no measurable gain (intervals include 0), not suggested for a gate.
- **R7PrefetchEarly** (`c34a9739`, child TT prefetch from `Board::key_after_r7` before the extension block):
  `key_after_r7` exact for 29.4M moves (only double pushes creating a legal en passant differ, by design);
  identity ALL OK; NPS 6 runs -2.11% (d16) / +1.46% (d20): no clear gain, not suggested.
- **Instructions** (callgrind bench 13, Linux CI, same nodes): R7TtExclusive -1.26%, R7QuietGen -0.35%,
  R7EvalPrefetch +0.08%. **CI**: opus-ci run 40895783124 on `2d9889cf` green (release, ASan+UBSan, TSan, incl.
  `forge_r7_quiet_gen_tests` and `uci_options_regression`); profile runs green; `c34a9739` runs queued at report time.
- **Gate**: `F:\opus_scratch\r7\j3\exe\forge_r7_j3a.exe` (sha256 `61f641d8...`, source `2d9889cf`) with
  `option.R7TtExclusive=true` vs the same exe at defaults (node-exact, so a non-regression SPRT fits).

## J4 Gate throughput: DONE (measured; nothing on the running gate was changed)
Tools: `tools/r7_gate/` (README). Evidence: `logs/r7/j4/`.
- **Before (the running gate R5A_1, conc 8, 10+0.1, read from its PGN)**: **996 games/h** over 1.61 h (1,002 in the
  last hour); mean game 28.3 s, 143 plies, every game ends "normal" (no adjudication configured). Theoretical
  8 x 3600 / 28.32 s = 1,017/h, so the between-game overhead is only ~2%.
- **Key fact**: at a fixed time control a game lasts ~28 s whatever the engine speed, so games/hour depends only
  on concurrency, time control, game length (adjudication) and that ~2% overhead. NPS, affinity and book format
  change game quality, not games/hour.
- **Adjudication** (offline replay of all 1,626 games' score/time comments, `adjudication_sim.py`):

| rule | adjudicated | results changed | games/h (from 1,002) | Elo of the same games |
|---|---|---|---|---|
| none (played) | 0% | - | 1,002 | +4.92 |
| E resign 4x1000 two-sided + draw 40/10/5 | 46% | 0 | 1,033 (+3.1%) | +4.92 |
| A resign 3x600 two-sided + draw 34/8/8 | 64% | 6 (0.37%) | 1,071 (+6.9%) | +4.92 |
| B resign 3x400 two-sided + draw 34/8/20 | 70% | 14 (0.86%) | 1,120 (+11.7%) | +4.07 |

  Real check at conc 3 (`mini_gate.sh`, 40 games each, same openings and seed, CPUs as the gate):
  **before 350 games/h -> after (rule A + `engine=false` log) 365 games/h (+4.3%)**, 16/40 adjudicated. The 40-game
  samples are noisy; the 1,626-game replay is the better estimate. Adjudication saves less than the ply counts
  suggest because at 10+0.1 the late moves are played fast.
- **Engine log**: `-log ... engine=true` wrote 1.07 GB for 1,600 games (25.5 MB per 40 games in the mini-gate) but
  fastchess itself uses only 0.03 CPUs: turning it off saves disk (~2 GB per 3,000-game gate), not time.
- **Concurrency** (`cpu_survey.ps1`, 20 s): the PC was 61-73% busy (gate 8.0 CPUs, trainer 1.3, self-play ~2.1).
  More gate games in parallel is the only big lever (conc 10: ~+25% games/h), but **the live trainer runs at Idle
  priority and the gate engines at BelowNormal, so extra gate threads would take CPU from the trainer first**;
  self-play (Idle, pinned to CPUs 12-15) is the same. Owner item: raise the trainer to BelowNormal (or start extra
  gate games at Idle) before raising concurrency; I did not change any priority.
- **Book loading** (`book_load_time.py`, 3 runs each): fastchess starts the first game **0.10 s** after launch with
  the 8 MB, 34,700-opening PGN and 0.016 s with an EPD copy. Once per gate start: not a lever (and an EPD book drops
  the opening move history).
- **Suggested flags** for the next gates (owner decision; adjudication changes a few results):
  `-resign movecount=3 score=600 twosided=true -draw movenumber=34 movecount=8 score=8` (or rule E for zero
  changes), and `-log ... engine=false`.

## What is left (owner items and ideas)
- Gate R7TtExclusive (above). R7QuietGen, R7EvalPrefetch and R7PrefetchEarly stay OFF in the tree.
- Self-play stall since 17:04:36 (see Incident).
- J1: bigger batches (8192) and 2 loader threads were not run (a batch-8192 / 2-thread run was refused by this
  session's permission classifier as a risk to the live trainer); a real training run with the fast path (more
  data, holdout scoring, then a gate) is the next step.
- J2: the binpack null-move hazard with `filtered=True` (J2 finding); a parallel binpack reader if the loader ever
  becomes the limit.
- J4: owner choices: adjudication flags, `engine=false` logging, and the trainer's Idle priority before any
  concurrency increase.
- J3: HCE `evaluate_position` (hotspot 1) is untouched; ideas: the no-TLS path for `hashfull()`.
