# S-A1 (G-A1) More self-play data, dedupe first, H256 retrain recipe — DONE (recipe + queue lines; UNPROVEN)

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 38; `OPUS_TEST_PLAN.md` row 1 (G-A1, srand 1254856699).
- **Branch:** `opus-sol-SA1` = `d4f4312` + `0d99f02` cherry-picked (`c8448944`) + this job.
- **Scope:** design and scripts only (`[skip ci]`), no engine change, no GPU, nothing queued.
- **Overlap:** the dedupe/merge scripts are COVERED by `opus-sol-S40`, with `opus-sol-S16` and `opus-sol-S17` for the
  existing shards, so this job reuses them. The retrain recipe builds on `opus-sol-A7` and `opus-sol-S44`.

## Acceptance
| item | result | evidence |
|---|---|---|
| dedupe/merge scripts | **COVERED**: S40's merge tool, already run on real data. 304,696 rows of a second folder → 246,035 kept against all 30 shards and the holdout. S16: 6,069 holdout-overlap rows inside the training shards (0.0026%). The generator dedupes its own output (SQLite FEN set) | recipe §1 |
| h256 retrain recipe | **DONE**: the e48 production recipe on 500M frozen positions (`--max-train 500000000`) with `--mmap-data`, after two PC checks (mmap identity/speed at 32M; mmap speed at 500M) | recipe §4 |
| queue lines use only existing v3b arguments | **PASS**. All 5 lines parse with the unchanged v3b parser (positive control: f070 reproduces its own settings dump); 2/2 negative controls rejected | `logs/step1_dryparse.log`, `logs/step1_dryparse.json` |
| sample | the S40 real merge (its branch) is the sample; the 32M smoke lines are the PC sample for the trainer side | S40 REPORT, queue lines 1-2 |
| GPU hours | G-A1 retrain 5.46 h at 1.22M/s (4.96 h measured rate); smokes and speed check about 0.01 h each | recipe §5 |
| gate | SPRT [0,10] 10+0.1, cap 1500, conc 8, srand 1254856699 against the current lock; 40+0.4 confirm before any lock | recipe §4 |

## Findings
1. **Data grows about 37.5M training positions per day.** It went from 137.4M (2026-10-25 03:23 UTC) to 241.9M
   (2026-10-27 22:18), in 10M shards about every 6.4 h. So 0.5B comes in about 7 days and 1B in about 20, or about 4.6
   and 13.5 days with S32's datagen if deployed.
2. **RAM-mode training ends near 390M rows on this PC.** v3b uses about 44 B per row while training (10.75 GB at 242M,
   with 10.5 GB still free). 0.5B needs `--mmap-data`, which has never run on the PC (CPU smokes only: RAM == mmap).
3. **At 1B the page cache cannot hold the data** (37 GB). Random row order then means random 4 KB reads per batch, which
   likely throttles training (ESTIMATE). A 3,000-step speed check at full size (queue line 3) measures it before the
   real run is spent. If it fails, the next step is a block-shuffled loader, which is a new trainer job.
4. **argparse accepts unique prefixes.** `--epoch 48 --mmap` parses as `epochs=48, mmap_data=True`, so a typo can
   silently pick another option. The dry parse shows what a line really means.

## Files
- `forge_sol_SA1_more_data_recipe_20261027.md`, `forge_sol_SA1_queue_lines_20261027.txt`;
- `opus_a7_dryparse.py` (A7's tool, byte-identical);
- `README.md`, `IDEA_SOURCE.md`, `REPORT.md`, `FILES.txt`, `SHA256SUMS`, `logs/step1_dryparse.{log,json}`.

How it was run: read-only parsing of the PC run logs and queue (CPU, `nice -n 19`, `-I -B`); no trainer code ran.
Machine exclusive: no.

## Left / UNVERIFIED
- DirectML identity and speed of `--mmap-data` (queue lines 1-3 measure them).
- The 390M-row RAM ceiling and the page-cache estimate.
- The growth projection.
- Any training or Elo result. The +14 Elo arithmetic in recipe §4 is an extrapolation, not a claim.
