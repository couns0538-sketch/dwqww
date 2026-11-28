# CHECKPOINT_LATEST — 2026-11-28 10:12 PC (CLEAN PRE-SSD SHUTDOWN COMPLETE)

## Status: SAFE FOR PC SHUTDOWN (0 Processes Running, 0 Partial Jobs)
- **Owner Order (`OPUS-2811-SSD-SHUTDOWN`, 09:38 PC):** Obeyed completely, **28 minutes ahead of deadline**!
- **`NEON-2811-AFTER-THE-SSD` Posted:** `C:\nnue-lab\neon\NEON_TO_OPUS.md` (`10:12 PC`) for Opus to generate `FOR_THE_USER/52_AFTER_THE_SSD_PASTE_INTO_NEON.txt` by `10:50 PC`.
- **Completed Declared Matches:** **`76`** (`0` TL/IL/DC, `C:\nnue-lab\neon\forge_fixes\ALL_MATCHES_SCOREBOARD.md`).
- **Completed Seed-2 Training & Gates (`R1_SEED2_GATES_SUMMARY.json`, `all_ok=True`):**
  - `OPUS_R1_live768_keepnoisy_seed2\cand.fnn3` (`67fcfaea...`, `hard_pass=True`, `Q/P=6.46`).
  - `OPUS_R1_live768_skipnoisy_seed2\cand.fnn3` (`4f19f204...`, `hard_pass=True`, `LOSS=0.004549`, `VAL=0.008539`, `Q/P=8.49`, `0` GPU cooling pauses).
- **Skip-Noisy Placement Package:** Officially accepted by Opus (`OPUS-2811-PACKAGE-COMPLETE`, `8/8` pytest PASS, listed for Fable Monday).
- **Running Processes (`10:10:20 PC`):** **`0`** `fastchess`, **`0`** `forge`, **`0`** Neon `python` processes!

## Exact Post-Restart Resume Procedure (After SSD Install & PC Boot)
1. **MANDATORY Pre-Start Checks:**
   - Verify HWiNFO is logging (`age < 90 s`).
   - Verify `D:\nnue folder2\NNUE_LAB_OVERFLOW_MARKER.txt` and `F:\nnuelabs  3\NNUE_LAB_OVERFLOW_MARKER.txt` exist (if missing, STOP and tell Opus!).
   - Run `C:\nnue-lab\tmp\fable_scratch\tools\mem_room.py` before each start.
   - Respect hard `92 C` CPU ceiling (never cross `92 C`; act at `90 C`), never overlap parse + match.
2. **Locked Match Queue (in Order):**
   1. `OPUS_R1_skip_vs_R1_keep_SEED2_SPRT_0_10_250k` (`R1_SEED2_DECLARATION.json`, `nodes=250000`, `SPRT [0,10]` cap `3,000g`, `seed=202611953`, `conc=7` on idle PC).
   2. `OPUS_R1_skip_vs_r0067_2000g_6p006` (`R1_SEED2_DECLARATION.json`, live PGO `forge.exe` both sides, `tc=6+0.06`, `2,000g`, `seed=202611954`, `conc=7`, 100% idle + `CLOCK_MATCH_RUNNING`).
   3. `CLK_LmrDeeperShallower_SPRT_0_10_6p006` (`run_lmr_deeper_clock_sprt.py`, live PGO `forge.exe` + `r0067` both sides, `LmrDeeperShallower=true`, `tc=6+0.06`, `SPRT [0,10]` cap `4,000g`, `seed=202611971`, `conc=7`, 100% idle + `CLOCK_MATCH_RUNNING`).
   4. Final freeze (`HANDOFF_12H_DATA_QUALITY.md` `0` markers + `stage_teamwork_delivery_w11.py --live --confirm-quest-complete YES_COPY_TO_TEAMWORK`) -> `<!-- GOAL_COMPLETE -->`.
