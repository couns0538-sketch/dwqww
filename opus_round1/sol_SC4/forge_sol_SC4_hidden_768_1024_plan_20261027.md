# S-C4 / G-C4: hidden layer 768-1024 — PLAN (UNPROVEN)

- **Source:** test plan row 16, G-C4 "Hidden 768-1024 (after A4 locks)", EVAL, srand 610323748;
  `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 43 ("plan only").
- **Run it only after an H512 net (S-A4 / G-A4) has locked.**
- **The crew's risk note** (test plan): "768+ widths have no benefit until int16 / SMP land".
- **What this job adds:** a measured NPS cost of width on the lock engine, a decision rule, and dry-parsed queue lines.
  No net was trained and there is no Elo claim.

## 1. Measured: what width costs the engine (float path of the lock)
**Method.** The lock already sizes the hidden layer at compile time (`FORGE_NNUE_HIDDEN`, `include/forge/nnue.hpp`).
- `opus_sc4_widen_inc.py` zero-pads the lock net (`src/nnue_weights.inc`, sha256 `a7ebcf3a…`) from H256 to H512, H768
  and H1024: zero W1 columns, zero B1, zero W2 in both halves. The new units stay exactly 0, so SCReLU(0) = 0 and the
  output only gains +0.0 terms. The wider builds therefore evaluate identically and search the same tree, and only
  their width costs time.
- **Checks:**
  - the H1024 build passes every lock pin (bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5
    4865609, kiwipete 193690690: `logs/step3_identity_h1024.log`);
  - all 72 timed runs below have the lock's node counts;
  - the H256 rebuild differs from the lock exe only in the 6 PE timestamp/checksum bytes.
- **Builds:** box recipe (`build_pc.sh` with the hidden size as a variable), FMA 0, 0 warnings (`logs/step2_builds.log`).
- **Timing:** `nps_ab.py` (S29), ABBA, fresh processes, bench d16 and d20, Threads 1, Hash 16, 6 runs per build per
  depth, Idle. The PC was loaded (gates, training, self-play, agents), so CPU-time NPS is the number to quote
  (`logs/step4_nps_ab.log`).

| width | d16 CPU-time NPS vs H256 (95% CI) | d20 CPU-time NPS vs H256 (95% CI) | node time vs H256 | float W1 size | accumulator per ply |
|---|---|---|---|---|---|
| H256 (lock) | — | — | 1.000 | 0.79 MB | 2 KB |
| H512 | **−9.50%** (−12.2 .. −6.8) | **−9.75%** (−12.8 .. −6.7) | 1.107 | 1.57 MB | 4 KB |
| H768 | **−15.70%** (−19.6 .. −11.8) | **−17.62%** (−20.0 .. −15.3) | 1.200 | 2.36 MB | 6 KB |
| H1024 | **−22.82%** (−26.8 .. −18.9) | **−23.71%** (−27.4 .. −20.1) | 1.303 | 3.15 MB | 8 KB |

- **Linear in width.** Node time grows by about **10.1% per extra 256 hidden units**: 1.101 / 1.202 / 1.303 predicted
  against 1.107 / 1.200 / 1.303 measured (mean of d16 and d20). So the width-dependent NNUE work (accumulator update,
  SCReLU and the output layer) is about 10% of node time at H256.
- **Cache footprint.** The engine converts W1 to float32 at load. From H512 up, W1 no longer fits a Zen 5 core's 1 MB
  L2. The linear fit shows no extra cache cliff up to H1024 on this CPU.
- **Consistency with S37.** S37's microbench puts NNUE update + output at about 97 of 403 ns per search-case eval.
  Not every node evaluates (TT hits, mate/draw nodes), which fits the measured 10%.

## 2. What the speed loss means (ESTIMATE)
- **In speed doublings:** log2(NPS ratio) = −0.15 for H512, −0.27 for H768, −0.38 for H1024.
- **In Elo.** If a speed doubling is worth 50-100 Elo at 10+0.1 for an engine of this level (public self-play
  time-scaling results; not measured for Forge), the speed cost is about:
  - H512: −7 to −15 Elo;
  - H768: −13 to −27;
  - H1024: −19 to −38.
- **What the net must win back.** At S44's slope of 5 ± 1.5 Elo per 1e-4 of holdout b0.6 (conc 5), it needs roughly:
  - H512: 1.5-3e-4 b0.6;
  - H768: 2.7-5.4e-4;
  - H1024: 3.8-7.6e-4;
  better than H256 at equal data. For scale, one doubling of the training data gives about 1.65e-4 (A7, 43 runs).
  **On the float path, H768-1024 is unlikely to pay off.**
- **With int16 SIMD inference (S-A2).** With 16 lanes instead of 8 and half the memory traffic, the width cost could
  fall to roughly half (ESTIMATE): about 5% per extra 256 units. That halves the bar above, which is why the crew
  ranked 768+ after int16.

## 3. Plan
1. **Preconditions.**
   - An H512 net is locked (G-A4 H1 plus its 40+0.4 confirm).
   - The S-A2 int16 path is merged and verified at H512.
   - Measure this table again on the int16 path (same zero-padding method; the widening tool is width-generic) at H768
     and H1024.
2. **Engine.**
   - Float path: no code change; the hidden size is compile-time and the shape `static_assert` in the `.inc` guards it.
   - int16 path: re-derive the int32 worst-case bound of the output sum, which grows with 2H terms (S21's range tool),
     and check that SIMD loops and alignment are correct for 768 = 3×256 (not a power of two).
3. **Decision rule** before any H768/H1024 GPU run: the int16 NPS cost against H512 must be ≤ 10% at d16/d20 (CPU-time,
   ABBA). Otherwise stop: no plausible holdout gain pays for it.
4. **Trainer.** v3b takes any `--shape` and has the same export format (int16 ×4096). Add a CPU smoke per width with
   export parity 10000/10000 (as S-A4 does for H512). Learning rate: keep the e48 recipe's 7.07e-4 for the first run;
   wider nets may want less, and S-A3's schedule arguments come later (one factor per gate).
5. **GPU** (queue lines below; PROPOSED).
   - First the 3,000-step speed lines, to measure GPU throughput per width.
   - Then the width ladder at **equal data and seed**: the A7 frozen-data protocol, `--max-train 240000000`, seed 701.
     H256 is A7's line A7-2; H512, H768 and H1024 are here. Holdout b0.6 then compares cleanly across widths.
6. **Gate G-C4.** SPRT [0,10] at 10+0.1, cap 1500, conc 8, **srand 610323748**, against the H512 lock. Confirm at
   40+0.4 with a fresh srand before any lock (EVAL change). Gate only the width whose holdout gain clears §2's bar.

## 4. Queue lines (`forge_sol_SC4_queue_lines_20261027.txt`; dry parse `logs/step7_dryparse.log`: 5/5 parse, 2/2 negatives rejected)
| line | purpose | steps | positions | GPU-h at 1.22M/s (H256 speed; wider is UNVERIFIED) |
|---|---|---|---|---|
| `resid_h768_e1_sc4_speed_s99_mt240m` | H768 GPU throughput | 3,000 | 24,576,000 | 0.01 (+ load/holdout) |
| `resid_h1024_e1_sc4_speed_s99_mt240m` | H1024 GPU throughput | 3,000 | 24,576,000 | 0.01 |
| `resid_h512_e48_sc4_bs8k_lr707e6_b06_s701_mt240m` | width ladder (skip if S-A4 already has it) | 1,406,208 | 11,519,655,936 | 2.62 |
| `resid_h768_e48_sc4_bs8k_lr707e6_b06_s701_mt240m` | width ladder | 1,406,208 | 11,519,655,936 | 2.62 |
| `resid_h1024_e48_sc4_bs8k_lr707e6_b06_s701_mt240m` | width ladder | 1,406,208 | 11,519,655,936 | 2.62 |

Training memory: W1 Adam state grows with width (768 × H × 3 floats: 9.4 MB at H1024), which is negligible next to the
data. The RAM-mode data wall of about 390M rows (S-A1) is unchanged.

## 5. Risks and limits
- The NPS table is from a loaded PC and the float path. The int16 numbers must be measured again (step 1).
- The Elo-per-doubling range is a public-results ESTIMATE, not a Forge measurement.
- S44's holdout→Elo slope has ±30% error, and S30 shows that loss has not predicted Elo reliably for us.
- Wider nets may need more data or a different learning rate; one seed per width cannot separate a small gain from seed
  noise (seed sd of b0.6 is 7.1e-6, which is small next to the bars in §2).
