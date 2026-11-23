PROPOSAL N5: Resolve Q1 with one zero-training 250k-node match (round 136 vs round 67); if flat, pause redundant per-round 388M-window trainings/gates until P3's 2B loader is ready (reclaiming ~5.1 CPU h/day and accelerating data + P1/matches), and move 2B-era gating directly to 250,000 nodes (Q3).

KIND: explanation

EVIDENCE:
1. **Plain 388M rounds are already proven flat at 50,000 nodes (`Q1`):**
   - Plain rounds 68-78 vs round 67 at 50k (`debate/STATE.md:57-58`): `36,916` games, `-0.81 [-3.02, +1.40]` (`SE1 = 4.42 / 3.92 = 1.128` Elo).
   - Plain rounds 129-136 vs round 67 at 50k (`debate/STATE.md:19`): `29,968` games, `-0.07 [-2.52, +2.38]` (`SE2 = 4.90 / 3.92 = 1.250` Elo).
   - Inverse-variance pooled across all `66,884` plain games at 50k: `w1 = 0.786, w2 = 0.640` -> **`-0.48 [-2.12, +1.16]` Elo** (`SE = 0.84`).
   - Note that the `+2.35 [-0.10, +4.80]` direct match (`STATE.md:20-21`) was **round 87**, which was a **TD-label round** (`STATE.md:55`: "TD labels ... trained rounds 79 to 87 of the loop"), not a plain round.
   - Therefore, for plain 388M-window rounds, the standstill at 50,000 nodes is NOT a measuring-power problem masking +3 to +4 Elo gains (the 95% upper bound over 66,884 games is `+1.16` Elo).
2. **One Q1 loophole remains untested (`J3`):** Every gate in rounds 68-136 and the 30k r87 match ran at **50,000 nodes**. Under `J3` (`debate/PLAN.md:43-44`), king-bucket nets lost 10-17 Elo at 50k while gaining 29-39 Elo at 250k. Whether a recent plain candidate trained on round 67's games gains at **250,000 nodes** despite being `-0.07` at 50k has never been measured.
3. **Cost of running the stationary 388M loop while building P3/P3b (`debate/PLAN.md:25-32,85-92`, `STATE.md:22-27`):**
   - Today's loop runs ~21 rounds/day (`~320M` kept rows/day), spending `21 * 872 s = 18,312 s = 5.09` 16-thread CPU hours/day on 50k gates (`0/69` promoted) and `21 * 2,917 s = 17.02` GPU hours/day training identical-window 388M nets.
   - Pausing redundant 388M trainings and 50k gates (keeping self-play + filter running, or training only once P3 can read >388M) immediately frees **5.1 CPU hours/day** (and all GPU hours for P3 loader tests). Dedicated 16-worker self-play (`5,818 written/s * 0.9527 = 5,543 kept/s`) produces `479M` kept positions/day (+50% vs 320M/day, closing the remaining `0.95B` r67-net gap to 2.00B in ~2.0 days instead of ~3.0-3.4 days), OR frees threads to finish P1's remaining 14 CPU h + confirmation + breadth + TD twin significantly sooner.
4. **Gate depth & budget in the 2B era (`Q3`, `PLAN.md:39-44,90-92,283-284`):**
   - A 4,000-game 50k gate (`SE = 6.64 / 1.96 = 3.39` Elo, `STATE.md:18`) has only ~14% power to pass LB > 0 on a true +3 Elo gain (`P(Z > 1.96 - 3/3.39) = 0.14`) and is exposed to J3 depth reversals and J2 winner's curse (0.59x confirmation shrinkage).
   - Once P3 trains on 2B positions (`>= 4.2` GPU hours/net, `PLAN.md:90-91`), cadence drops from 21 nets/day to at most **1-2 nets/day** (e.g. one training per +150M-250M new positions, or per architecture/filter test).
   - At 1 candidate/day, a **direct 250,000-node SPRT [0, 5]** (max 4,000 games = <= 3.0 CPU h/day, avg ~1.5 h) costs **2-3.5 CPU h/day LESS** than today's 5.1 CPU h/day on 21 50k gates, while testing directly at the depth that matters. (Under `J8`, test the gate transition explicitly alongside the first 2B candidate rather than adopting on theory alone.)

COST:
- Q1 diagnostic match: 4,000 games at 250,000 nodes of existing round 136 candidate vs round 67 best net = **~3 CPU hours, 0 GPU hours** (fits into the existing match slot behind breadth/TD twin, or ahead of them if the owner wants to unlock the 5.1 CPU h/day right away).
- Pausing 388M train+gate if flat: **negative cost** (saves ~5.1 CPU h/day and ~17 GPU h/day).
- Q3 2B-era gate: ~1.5-3.0 CPU h/day at 1 candidate/day (net savings of ~2-3.5 CPU h/day vs today's 5.1 h/day).

HOW IT IS JUDGED:
1. **Q1 test:** Play 4,000 games at 250,000 nodes (equal settings per J9, same exe) of round 136's already-trained candidate vs round 67's best net.
   - If 95% LB > 0 at 250,000 nodes -> **measuring/depth-blindness problem confirmed (J3)**; do NOT pause training; instead replace the 50k gate with a direct 250k SPRT on fewer/deeper candidates and test promoting r136 (after a second seed).
   - If 95% LB <= 0 and point estimate <= +3 Elo at 250,000 nodes -> **388M stationary-window ceiling confirmed**; pause per-round 388M trainings and 50k gates until P3's >388M loader (or a new net/search/filter lever) is ready, redirecting the recovered 5.1 CPU h/day to P1/matches/self-play.
2. **Q3 gate rule (J8 check):** For the first 2B candidate (768-wide vs r67), play BOTH the legacy 50k gate and the 250k SPRT [0, 5] (max 4,000 games) so we record whether 50k and 250k agree; once training cadence is <= 2 nets/day on 2B positions, promote by direct 250k SPRT [0, 5] (cap 4,000 games) + a 2k soft-node non-regression sanity check (`LB >= -3` in 4,000 games, ~10 min) before the new net plays self-play (guarding J3 in the downward direction too).

WHAT WOULD CHANGE MY MIND:
- If round 136 beats round 67 with LB > 0 at 250,000 nodes, then the 388M window has NOT hit a ceiling (keep training, fix the gate depth immediately).
- If the owner prefers to keep the existing 388M loop running unchanged for operational continuity while building P3, limit this proposal to running the 3-hour Q1 diagnostic match and adopting the direct 250k SPRT only when P3's 2B cadence starts.
