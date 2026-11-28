# Line-by-Line Review Packets: Immediate Live-Loop & Server-Day Deltas

**Prepared:** 2026-11-28 04:50 PC (Chip-free prep while Owner's Bundle Arm B completes)  
**Strict Placement Standard:** Every candidate below follows `lab-place-a-change` — zero changes placed on diagnostic metrics alone; every conditional item cites its exact declared match / SPRT gate and rollback line.

---

## Packet 1 — Live-Loop Parity `7/8` Minimal Fix (Opus `YES WITH REMARKS`)

- **Problem Proven (`LIVE_LOOP_PARITY_BIAS_AUDIT.json`, `55.5M+` rows across `r0180, r0190, r0200, r0202`):** Fixed even `random_move_count = 8` (`pipeline/config.forge.toml:274`) forces ply 7 to always be Black's blind uniform random move and ply 8 to always be White's first searched move, creating a **`+151..+154 cp` White eval bias** and **`61.2%–61.5%` White score (`2.2:1` W:B wins)**.
- **Exact Code Patch:** `C:\nnue-lab\neon\forge_fixes\patches\datagen_uci_parity_7_8_minimal.patch` (`111` lines, `sha256: 184c6d2b...`, targets ONLY `pipeline/nnloop/datagen_uci.py` — 6 minimal hunks):
  1. `L207`: Adds `_random_count_for_game(g, game_idx)` returning `(alt if game_idx & 1 else base, True)` when `random_move_count_alt >= 0`, else `(base, False)` (100% identity when key omitted!).
  2. `L220-235` (`play_game`): When `alt_active`, uses `set(range(k))` (`k ∈ {7, 8}`) and adjusts `write_min_ply = k` when `write_min_ply == random_move_count`.
  3. `L365` (`selfgame_ok`): Validates `random_move_count_alt <= random_move_max_ply + 1`.
  4. `L377-438` (`play_game_sg`): Identical `k ∈ {7, 8}` and `writeminply {write_min_ply}` for `selfgame` path.
  5. `L462-535` (worker loop): Tracks per-worker `game_idx += 1` so games alternate `8, 7, 8, 7...` cleanly.
- **Exact Config Diff (`C:\nnue-lab\pipeline\config.forge.toml:274`):**
  ```toml
   random_move_count   = 8          # the first 8 plies are random moves
  +random_move_count_alt = 7        # alternates 8 / 7 random plies to remove +153 cp White parity bias
  ```
- **Verification & Rollback:** `pilot_datagen_parity_7_8_G3_R4.json` confirmed `49.99%` White STM / `+69.99 cp` (down from `+127.1 cp` on `r0067`), zero legacy RNG drift when unset. **Rollback:** remove `random_move_count_alt = 7` (1 line).

---

## Packet 2 — Zero-C++ UCI Option `LmrDeeperShallower = true` (Gated on Declared SPRT `[0, 5]`)

- **Current Evidence:** Unbiased fresh-seed `1,000g @ 50k` (`LmrDeeper_alone_vs_base_1000g_50k`): **`+8.34 [-4.06, +20.76]`** (`255–514–231`, `LOS 90.6%`, `0` TL/IL). Already compiled into live `forge/r15dsg` — **zero C++ diff, zero rebuild, zero speed overhead**.
- **Exact Gate Before Placement:** `run_lmr_deeper_sprt.py` normalized SPRT `[0, 5]` (`alpha=0.05, beta=0.05`, `max_games=4,000`) -> must accept `H1`!
- **Exact Config Diff (`C:\nnue-lab\pipeline\config.forge.toml:214`):**
  ```toml
  -v3_uci_options = { ..., EvalSwingMult = 15 }
  +v3_uci_options = { ..., EvalSwingMult = 15, LmrDeeperShallower = true }
  ```
- **Rollback:** delete `, LmrDeeperShallower = true` from line 214 (1 line).

---

## Packet 3 — Conditional Live-Loop `OPUS_R1` (`--keep-noisy` Removal on `768w` SCReLU)

- **Gate Before Placement (`R1_TWIN_DECLARATION.json`):**
  1. `OPUS_R1_skip_vs_R1_keep_1000g_250k` (`base_r15dsg` both sides, identical standalone runner, ONLY `--keep-noisy` differs): **95% CI lower bound > 0**.
  2. If positive -> train Seed 2 of BOTH (`run_opus_r1_keep_twin.py --seed 2 --skip-noisy` and `--seed 2`), then confirm `R1-skip vs r0067` at `250k` (`1,000g`) AND clean equal-time `6+0.06` (`concurrency=7`).
- **Completed Diagnostic Note (`OPUS_R1_live768_skipnoisy`, `sha256: 4902fe65...`):** Loaded `281,241,466` quiet rows in `9.43 GB` VRAM (`-7.6 GiB` vs `17.0 GiB` keep-noisy!), trained `40/40` ep at `5.74M pos/s` (`0` pauses), `Master Gates --quick` PASS (`0 cp` parity `8/8` OB), `S1/S2` passed automatically, `ob0_ob1_cliff = 108.5 cp` (vs `143.5`), scale-free `Q/P = 9.01` vs `r0067` `5.97` *(diagnostic only; games decide!)*.
- **Exact Config Diff (`C:\nnue-lab\pipeline\config.forge.toml:357, 433` — ONLY IF ALL GATES PASS):**
  ```toml
  # Line 357: remove --keep-noisy from train_cmd
  -train_cmd  = '... --batch-size {batch_size} --keep-noisy --lr-cycles auto ...'
  +train_cmd  = '... --batch-size {batch_size} --lr-cycles auto ...'
  # Line 433: keep metadata flag in sync
  -keep_noisy = true
  +keep_noisy = false
  ```
- **Operational Cache Note:** Dropping `--keep-noisy` switches `forge_train.py`'s cache suffix from `.cache-n0c1.npz` to `.cache.npz`. Before placing, check `C:` free space (`min_free_gb = 40`): rebuilding 25 rounds of `.cache.npz` takes `~20 GiB` (deleting obsolete `.cache-n0c1.npz` outside rollback frees `~24.9 GiB`).
- **Rollback:** restore `--keep-noisy` on line 357 and `keep_noisy = true` on line 433.

---

## Packet 4 — Owner's Bundle Arm A Forensic Post-Mortem (`OWNER_BUNDLE_ARMA_PGN_FORENSICS.json`)

- **Arm A Result (`OWNER_BUNDLE_ARMA_bundleG3_vs_liveR0067_2000g_6p006`, `conc=7`, `0` TL/IL/DC):** **`-7.47 [-15.49, +0.54]`** (`449–1059–492`, `LOS 3.38%`, `ptnml=[10, 260, 502, 219, 9]`, `cpu_max_c=77.4 C`). **Verdict: DO NOT PLACE BUNDLE.**
- **PGN Ply-Bucket Diagnosis (Arm A `-43` net vs `G3` alone `-2` net):**

| Ply Bucket | `G3` Alone (`-0.35`, `480–1038–482`) | Arm A Bundle+`G3` (`-7.47`, `449–1059–492`) | Net Delta |
|---|---:|---:|---:|
| `short_le80` | `0–165–7` (`-7`) | `2–176–5` (`-3`) | `+4` |
| **`mid_81_140`** | **`135–394–148` (`-13`)** | **`98–424–149` (`-51`)** | **`-38` (`-37` fewer White wins!)** |
| `long_gt140` | `345–479–327` (`+18`) | `349–459–338` (`+11`) | `-7` |
| **Color Split** | White `+115` (`298–519–183`) / Black `-117` | White `+66` (`261–544–195`) / Black `-109` | **White `-49` net** |

- **Takeaway:** Virtually the entire `-7.1` Elo drop below `G3` alone occurred in sharp middlegame moves `41–70` (`-37` fewer White wins while losses stayed flat at `149 vs 148`), proving that stacking 4 un-retuned search changes (`SF13 + SF8 + W2_proto_1 + LmrDeeper`) on top of the 45 Big Tune parameters hurts equal-time conversion (Arm B will isolate the search bundle on `r0067` cleanly).

---

## Packet 5 — Server-Day `2.0B` Filter & Training Recipe (`STAGE2_250K_CONFIRMATIONS_DECLARATION.json`)

- **Proven Mandatory (`+651..+700 Elo`):** `--skip-fqs-noisy` (`bit0=0`) + `--skip-check` (`bit1=0`), enforced by default in `serverday_v3/run_dedup_buckets_v3.sh` and `serverday_v3/run_train_stream_gpu_v3.sh`, alongside `--hidden 1024 --king-buckets 16` (`-0.61%` NPS vs `kb=8`) and the 3 frozen disjoint anchors (`dead_draws_20k_s5disjoint`, `won_endings_syzygy_20k`, `opening_ply012_anchors`).
- **3 Positive Stage-2 `50k` Filter Leads Queued for `600g @ 250k` Confirmation (Launching Beside `R1-keep` GPU):**
  1. `--ob-reweight cc0` (`S2Q_G4b`, `50k = +14.95 [-1.47, +31.43]`, `LOS 96.29%`) -> `seed=202611960`
  2. `2%` opposite-side-castled `16k` Forge-only rescore (`S2Q_EXP_R1b`, `50k = +14.25 [-1.35, +29.92]`, `LOS 96.33%`) -> `seed=202611961`
  3. `--loss-pow 2.5` (`S2Q_G4a`, `50k = +8.34 [-7.60, +24.32]`, `LOS 84.74%`) -> `seed=202611962`
- **Negative / Rejected Tier-2 Ideas (Do NOT Enable on Server Day):** Hard Tier-2 discarding (`EXP-F1` `-8.69` eq-raw despite `+12.17` eq-ret), unweighted `first` dedup (`EXP-F2_first` `-10.43`), `sqrt(k)`-capped `dedup_avg` (`EXP-F2_avg` `-9.38` vs `first`), and aggressive blowout downweighting (`EXP-W3` `-13.21` vs `dedup_avg`).
