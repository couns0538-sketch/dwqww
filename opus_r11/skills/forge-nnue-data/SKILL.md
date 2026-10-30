---
name: forge-nnue-data
description: Where the Forge NNUE training data, holdouts, runs, nets and conversion tools live on the PC, their formats, and the reusable scoring/averaging/rescoring tools. Use for any job that reads self-play data, holdouts, trainer logs or nets (datagen, dedupe, splits, rescoring, checkpoint averaging, learning curves, eval-scale checks).
---

# Forge NNUE data map (all read-only; copy to F:\opus_scratch\<job>\ before heavy use)

## Data
- **Shards.** `D:\grok-pc-data\forge_push\nnue_data\pos\forge_selfplay_NNN.pos` and `...\hce\forge_selfplay_NNN.hce`,
  31 shards (001-031).
  - FPOS v1: 16-byte header (magic `FPOS`, u32 version 1, u64 rows), then rows x 32 bytes (two 4-bit piece
    codes per byte, square-major a1..h8, codes P N B R Q K = 1-6, black = 7-12), then rows x int16 score, then rows
    x u8 meta.
  - FHCE v1: header (`FHCE`) + rows x int16 HCE eval.
- **Text.** The ordered self-play text is in `D:\grok-pc-data\selfplay_out`. The live trainer holds out exactly
  013+014 (16,388,575 rows) and trains on the other 29 shards (231.9M rows at 2026-10-27; it grows by about 10M
  rows per step).
- **Prepared copies.** Production holdout subset `F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.pos/.hce`
  (1,024,286 rows, md5 9ebe2f9c / c8723ec2); tiny data32 h000 sample `F:\opus_scratch\sol_S31\inputs\data32`;
  10k FENs `F:\opus_scratch\sol_S31\inputs\fens_10k.txt`.
- **Overlap.** 6,069 training rows share a position with the holdout (S16 removal list on branch `opus-sol-S16`).

## Runs and nets
- `F:\forge_nnue_train\runs\<run>\`: `epochNNN-stepXXXXXXXXX.{pt,bin,inc,json}` per epoch plus `<run>.log`.
  - `.pt` = config + model state + Adam state.
  - `.bin` = float32 W1^T (768 x 256), B1, W2, B2.
  - `.inc` = the engine export (x4096, int16).
- Settings dump: log line 6. Final holdout line: see the S30 table `F:\opus_scratch\sol_S30\out\final_table.csv`.
- Supervisor: `F:\forge_nnue_train\supervisor.log`. NEVER start anything named train_resid* (see forge-pc-rules).

## Tools to reuse
- `opus-sol-S31/forge_sol_S31_avg_ckpt.py`: average `.inc` / `.bin` / `.pt`; score a holdout (trainer metric
  without torch); parity against `forge::nnue` (lock `nnue.cpp` + `LA/5_nnue/tools/nnue_check.cpp`). Float64 vs
  float32 can differ by 1 cp at an integer boundary.
- `opus-sol-S20/opus_rescore*.py`: chunked, resumable engine rescoring (depth N, 50k-line chunks,
  `progress.json`); `fen2bin.exe` / `hce_dump.exe` in `F:\opus_scratch\rescore_d8\bin`; a loader check through
  the v3b loaders (AST-extracted from a renamed trainer copy).
- `opus-sol-S16` (overlap scanner), `opus-sol-S17` (game-group split, leak audit), `opus-sol-S18` (CPU smoke arms
  with renamed trainer copies), `opus-sol-S30` (log parsing, learning-curve fits), `opus-sol-S19` (score->WDL
  scale fit), `opus-sol-S21` (int16 range study, Python forward == engine).
- `opus-sol-S40/forge_sol_S40_merge_datagen_20261027.py`: dedupes a second self-play folder against the training
  shards and the 013/014 holdout, then writes sealed FPOS/FHCE shards with an md5 manifest.
- `opus-sol-S32`: in-engine datagen (`FORGE_DATAGEN`, default off). It writes `.pos/.hce` directly, about 1.5x faster
  than forge_selfplay.py; `--convert` = fen2bin + hce_dump.
- `opus-sol-A7/opus_a7_dryparse.py`: dry-parses queue lines with the UNCHANGED v3b parser, `ast`-extracted from a
  renamed copy. Positive control: a finished run's argv must reproduce its own `settings_*.txt` JSON. Watch out:
  argparse accepts unique prefixes, so `--mmap` silently means `--mmap-data`.
- Trainers on branches: v3c (`opus-sol-S50`: `--epoch-positions`, `--recent-weight`, `--init-weights`), v3d
  (`opus-sol-SA3`: `--lr-schedule cosine|linear|wsd`, `--lr-schedule-epochs`, `--lr-decay-frac`). Their defaults are
  byte-identical to v3b; none is deployed without CR.

## Training facts (measured 2026-10-27; re-check before reuse)
- **Throughput:** v3b averages 1.344M positions/s over a whole run (39 runs; the A7 spec uses 1.22M).
- **Data growth:** about 37.5M training positions per day, added as 10M shards. There were 241.9M at 2026-10-27 22:18 UTC.
- **Memory:** v3b RAM mode uses about 44 bytes per row while training (10.75 GB at 242M), so it ends near 390M rows
  on this PC. Above that, `--mmap-data` is needed, and it has never run on the PC.
- **Frozen data:** `--max-train N` keeps the first N positions in generation order (stable across resumes and days).
  Use it whenever runs must be compared at equal data (A7).
- **Effect sizes per doubling** (A7, 43 runs): data −1.65e-4 b0.6, epochs −3.3e-5; seed sd of FINAL b0.6 7.1e-6.
  Loss has not predicted Elo reliably (S30).

## FPOS meta byte and the trainer loss (verified against the S31 scorer, FB1 2026-10-28)
- `meta & 1` = side to move (1 = black); `(meta >> 1) * 0.5` = white's game result (0, 0.5, 1); the meta array
  starts at byte `16 + 34 * rows` (after the boards and the int16 scores).
- Loss: `pred = sigmoid((net_cp + hce_cp) * 2.25 / 400)` (residual nets), target `b * sigmoid(clamp(score * 2.25/400,
  +-40)) + (1 - b) * stm_result`, MSE; the lock blend is b = 0.6. Holdout subset `holdout_013_014_s16` (1,024,286
  rows) scores: AL1 lock net b0.6 0.014310 / b1.0 0.004572; HCE alone b0.6 0.017059 / b1.0 0.005074
  (`F:\opus_scratch\fable\logs\al1_holdout_score.json`, S31 scorer `score --nets <inc> --pos <pos> --hce-dir <dir>`).
- NNUE v3 (branch `fable-nnue-arch`): `tools/nnue/fable_nnue_train.py` (CPU torch, 1 thread, ~21k pos/s at H512,
  QAT on the engine grid, `score` for v3 files), `tools/nnue/fable_nnue_v3.py` (format, exact integer reference).
  Under `python -I` the script directory is not on `sys.path`: sibling imports need `sys.path.insert(0, dirname(__file__))`.

## R11 sources and binpacks (2026-10-30) - see [[forge-nnue-pipeline]]
- `selfplay_out` holds only text; the supervisor converts each sealed shard 1:1 to `forge_push\nnue_data\pos\*.pos` +
  `hce\*.hce` (+ `.info` with `records=`; HCE "forge=1ab50b2d evaluate_uncached"). 39 shards on 2026-10-30.
- R8 v5 self-play (live since 2026-10-29) writes `D:\grok-pc-data\selfplay_out_r8v5_20261029` (`.part` while writing);
  a shard's `.dedup.pos` is final once its `.dedup.json` exists; there is no `.hce` (R11 generates it with
  `F:\opus_scratch\rescore_d8\bin\hce_dump.exe` sha256 a88e519d, which reproduces the production .hce exactly).
- Astra A1's filtered set (release astra-a1-data-results-20261030) = 9,206,371 rows of forge_selfplay_003 in order.
- J1 binpacks (owner, 2026-10-29): `F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack` 304,999,573 records,
  `forge_holdout_013-014_j2.binpack` 16,388,575; 34 bytes/record (no chaining: constant ply 40, null king move);
  byte-identical to R11's writer for the same rows. Never overwrite them (the live trainer reads them).
- R11 output: `D:\grok-pc-data\r11_nnue\data` (train/, holdout/, MANIFEST.json, train_files.txt, holdout_files.txt,
  HOLDOUT_TEST.json); dedup key = 32-byte board + stm; holdout 013/014 first in the registry.
