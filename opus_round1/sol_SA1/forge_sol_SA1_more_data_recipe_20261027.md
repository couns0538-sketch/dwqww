# S-A1 / G-A1: more self-play data (dedupe first), retrain at H256 — recipe (UNPROVEN)

- **Source:** test plan row 1: G-A1 "More self-play data to 0.5-1B+ (dedupe first), retrain at h256", gate srand
  1254856699; `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 38 ("S-A1 dedupe/merge self-play data + h256 retrain recipe
  (scripts + sample)").
- **Status:** design and scripts only. No GPU use, nothing queued; the queue lines in §5 are PROPOSED.

## 1. What already exists (reused, not redone)
| need | covered by | state |
|---|---|---|
| dedupe a second self-play folder against the training shards and the 013/014 holdout, write sealed FPOS/FHCE shards | **S40** `forge_sol_S40_merge_datagen_20261027.py` (branch `opus-sol-S40`) | DONE. 17 tests, 22/22 mutants, v3b loads its output (RAM == mmap). Real read-only run: 304,696 rows → 246,035 kept (80.7%) against all 30 shards |
| holdout overlap inside the existing training shards | **S16** (`opus-sol-S16`) | 6,069 of 231.9M training rows share a position with 013/014 (0.0026%); 0 straddling games |
| leak-free game split | **S17** (`opus-sol-S17`) | leak 0 on 2,930,566 real rows |
| faster generation | **S32** (`opus-sol-S32`) | in-engine datagen v2, 1.58x positions per wall second against forge_selfplay.py (advisory); needs CR before deployment |
| recipe and length vs data | **A7** (`opus-sol-A7`), **S44** (`opus-sol-S44`), **S30** (`opus-sol-S30`) | 43 runs: per doubling, data moves b0.6 by −1.65e-4 and epochs by −3.3e-5; S44 projects +4.9 Elo for 1.5x data and +8.5 for 2x at e48 (conc 5) |

The main generator already deduplicates its own output: forge_selfplay.py keeps a persistent SQLite set of 4-field FENs
(S32 finding). So "dedupe first" means three things:
- run S40 on any second folder before adding it;
- leave the 6,069 holdout-overlap rows. They are 0.0026% of training, and the sealed shards stay unchanged;
- report holdout numbers with that caveat.

## 2. Data growth (measured from the run logs)
The training-set size printed at the start of each e48 run (`train: N positions`, log line 6), against the run's start
time (from its `settings_<unix time>.txt`):

| run start (UTC) | training positions |
|---|---|
| 2026-10-25 03:23 (f006) | 137,381,087 |
| 2026-10-25 18:55 (f029) | 161,913,894 |
| 2026-10-26 04:56 (f039) | 181,913,894 |
| 2026-10-26 19:41 (f055) | 201,913,894 |
| 2026-10-27 09:21 (f066) | 221,913,894 |
| 2026-10-27 22:18 (f074) | 241,913,894 |

- **Rate:** +104.5M in 66.9 h, i.e. **about 37.5M positions per day**, added as 10M shards about every 6.4 h.
- **Projection at this rate:**
  - 0.5B is reached in about 6.9 days (about 2026-11-03);
  - 1B in about 20.2 days (about 2026-11-17).
- **With S32 datagen** (1.5x, after CR and deployment): about 4.6 and 13.5 days (ESTIMATE).

## 3. Memory: the 0.5B+ wall
- **RAM mode.** v3b loads the training set into RAM by default. Its private memory scales with the rows:
  - 8.87 / 9.22 / 9.56 GB after load at 222M / 232M / 242M (run logs line 8);
  - 10.75 GB while training at 242M (`resid_h256_e48_f074…_fb8k.log`, MEM lines at epoch 6), with 10.5 GB still
    available to the system;
  - that is about **44 bytes per row** while training.
- **The PC's limit.** It has about 21 GB for the trainer plus free memory. The supervisor's 4 GB free floor leaves at
  most about 17 GB, so **RAM mode ends near 390M rows** (ESTIMATE, with the current self-play and gates running).
  0.5B needs about 22 GB; 1B about 44 GB.
- **`--mmap-data`** keeps only the shuffle order (4 bytes per row) and the batch buffers private. That is about 3 GB at
  0.5B, and the 37 bytes per row of `.pos` + `.hce` (18.5 GB at 0.5B) go through the page cache.
  - It never ran on the PC. CPU smokes gave identical outputs: `NETS_snapshot_20261025_1030.md:1620` box smoke, and
    S40's real-data smoke (RAM == mmap).
  - The data sits on one NVMe SSD (Crucial CT1000P5PSSD8; C:, D: and F: are partitions of disk 0).
  - Training reads rows in random order, so once the data exceeds the page cache every batch becomes about 8,192 random
    4 KB reads. At 1.3M rows/s that is up to about 160 batches/s.
  - At 0.5B the cache (about 18 GB) roughly holds the data. At 1B (37 GB) about half the reads miss, which likely
    throttles training (ESTIMATE). Hence step 2 below.

## 4. The recipe (one factor per gate: data)
1. **Smoke `--mmap-data` on the PC now** (queue lines 1-2: 32M rows, 2 epochs, seed 99, RAM vs mmap). Pass:
   - epoch-2 `.inc` md5 equal, which shows DirectML identity;
   - mmap positions/s at least 90% of RAM mode;
   - no new memory growth (MEM lines flat).
2. **Size check when 0.5B sealed rows exist** (line 3: 1 epoch, 3,000 steps, all 500M rows, mmap). Pass: positions/s
   at least 1.1M (the e48 runs average 1.34M). If it fails, stop and file a trainer job for a block-shuffled loader
   (shuffle within page-sized blocks, then across blocks); that needs new trainer code. Do the same check before any 1B
   run.
3. **The G-A1 retrain** (line 4). It is the e48 production recipe:
   - v3b, H256 residual, batch 8192;
   - lr 7.07e-4, cosine to a 1% floor, warmup 300;
   - blend 1.0 → 0.6.
   Two settings change: `--max-train 500000000` freezes the data at the first 500M positions in generation order (A7 §4:
   identical on every launch and resume), and `--mmap-data` is added. GPU time: 2,929,680 steps x 8,192 =
   23,999,938,560 positions / 1.22M/s = **5.46 h** (4.96 h at the measured 1.344M/s).
4. **Gate.**
   - SPRT [0,10] at 10+0.1, cap 1500, conc 8, **srand 1254856699**, against the current lock;
   - then a 40+0.4 confirm with a fresh srand before any lock (EVAL change, test-plan rule).
   - The expected gain is UNPROVEN. 500M is about 3.3x the 151.9M rows of AL1's run (f003rec s198), and A7's fit gives
     −1.65e-4 b0.6 per doubling, i.e. about −2.8e-4. S44's slope of 5 ± 1.5 Elo per 1e-4 (conc 5) puts that near +14
     Elo, but S30 warns that loss has not predicted Elo for us. Only the gate decides.
5. **1B:** repeat steps 2-4 with `--max-train 1000000000` (10.9 GPU-h at 1.22M/s) only after the 0.5B net is gated.

## 5. Queue lines (file `forge_sol_SA1_queue_lines_20261027.txt`; dry parse `logs/step1_dryparse.log`)
| line | when | steps | positions | GPU-h at 1.22M/s |
|---|---|---|---|---|
| `resid_v3smoke_sa1_ram_s99` | now | 7,812 | 63,995,904 | 0.01 |
| `resid_v3smoke_sa1_mmap_s99` | now | 7,812 | 63,995,904 | 0.01 |
| `resid_h256_e1_sa1_mmapspeed_s99_mt500m` | at ≥ 500M sealed rows | 3,000 | 24,576,000 | 0.01 (+ load and holdout) |
| `resid_h256_e48_ga1_bs8k_lr707e6_b06_s502_mt500m_mmap` | after steps 1-2 pass | 2,929,680 | 23,999,938,560 | 5.46 |

**Dry-parse result.**
- All lines parse with the unchanged v3b argument parser (the 33 `add_argument` calls of a byte-identical renamed copy,
  md5 `b6758004`). The positive control (f070's argv reproduces its own settings dump) holds.
- Both negative controls are rejected: v3c's `--init-weights`, and `--mmapdata`.

**Hazard found by the dry parse.** argparse accepts unique prefixes. `ABBREV_demo` with `--epoch 48 --mmap` parses as
`epochs=48, mmap_data=True`, so a typo in a queue line can silently select a different option. Review queue lines with
this dry parse before queueing them.

## 6. Left / UNVERIFIED
- DirectML behaviour of `--mmap-data`, and its throughput beyond the page cache: steps 1-2 measure them.
- The memory ceiling of about 390M rows in RAM mode is an estimate from one run's MEM lines; it moves with self-play,
  gate and agent load.
- The data-growth projection assumes today's generator setup.
- No GPU run, no gate, no Elo claim.
