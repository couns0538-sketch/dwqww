# S-C4 idea sources

- **Spec:** `OPUS_TEST_PLAN.md` row 16 (G-C4, srand 610323748) and the crew risk notes (768+ widths need int16 first);
  `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 43 ("plan only").
- **Measurement idea: function-preserving widening.** Zero-padded hidden units, the same trick as net-widening
  warm starts (e.g. the earlier `widen_v4.py` mentioned in `NETS_snapshot_20261025_1030.md:1040`). Here it is used
  only to measure the speed of a wider net with an identical search tree. No code was copied.
- **Forge inputs:**
  - the lock source (`FORGE_NNUE_HIDDEN`, `nnue.cpp` layout);
  - S29's `nps_ab.py`, S37's per-stage cost table, S21's int16 range tool;
  - S44's holdout→Elo slope, A7's frozen-data protocol and dry-parse tool, S-A1's memory analysis.
- **General knowledge (concept only):** wider first layers improve eval quality at the cost of NPS. Engines usually
  pair larger widths with int8/int16 SIMD inference. Speed-to-Elo conversions follow public time-scaling results; for
  Forge they are an ESTIMATE.
