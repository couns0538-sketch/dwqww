# S-A1 idea sources

- **Spec:** `OPUS_TEST_PLAN.md` row 1 (G-A1, srand 1254856699); `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 38.
- **Forge work reused:**
  - S40: merge/dedupe tool;
  - S16: holdout overlap; S17: game split;
  - S32: in-engine datagen;
  - A7: frozen-data recipe and dry-parse tool;
  - S44: Elo projections; S30: learning curves.
- **PC facts used (read only):**
  - run logs in `F:\forge_nnue_train\runs` (train sizes, MEM lines, settings timestamps);
  - `queue.txt` (format, standard arguments);
  - `NETS_snapshot_20261025_1030.md` lines 1618-1626 (DirectML memory growth, mmap estimates);
  - the disk model (PowerShell `Get-PhysicalDisk`).
- **General practice (concepts only):** more and deduplicated self-play data is the usual NNUE lever. Memory-mapped
  training sets need locality, such as block shuffling, once they exceed the page cache.
