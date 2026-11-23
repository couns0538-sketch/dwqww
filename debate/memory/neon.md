# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T17:56:48Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files (`engine_lines`, `uciproc`, `test_uciproc`, `record`, `test_record`, `budget` v7 `76817bad`, `test_budget` `52ef5a14`) **3/3 YES**; `clockwatch` v4 / `test_clockwatch` **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES.**
  - Deliverable by `21:25Z`: `debate/engine_plan/ENGINE_PLAN_8H.md` + `AGREE <sha256> neon ENGINE_PLAN_8H.md`. Fable checks once at `21:55Z`.
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Note: Opus published worker/packer (4 files) — queued for `21:25Z` server-day review block!
  - Also `debate/server_day/specs/`, ordered rehearsal + measurements (`171712Z`, `172415Z`), `FINAL_FOR_THE_OWNER.md` + `AGREE` by `01:25Z`.
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Exact `Forge 6.5` Live Test Harness (Outside Repo)
- Exact binary `/tmp/neon_forge65_exact/forge` + 4 matched ablation builds `/tmp/neon_ablate_{orig_gxx,dirty_rbw,dirty_acq,nolock_diag,postlock_rbw}/forge` (all bit-exact `1T bench 11 = 226187`, `bench 13 = 616966`).

## Phase 1 Agreements & Completed Measurements (`175648Z`)
- **`A27` AGREED (`175648Z`):** `AGREE 5dd40b0200d0e3012e10bc480abefe87561e481454e66615607f1a20f6bbbdb7 neon A27.` (unseen-game validation diagnostic with target-neutral independent reference + 3-level overlap report).
- **Reviewed & agreed Astra's 4 reports:** `998da7706f` (opening families `0.949–1.045`, planted `2.012`), `644e4e0faf` (4 native nets on SF17.1 500k referee), `8bd6c533b8` (direct 3-way triangle + exact `clock_plan.hpp`/`search.hpp:287`/`tm_node_share.hpp` checks).
- **Delivered all 6 complementary Neon later-stage packages in Astra's 7-part structure (`175648Z`):**
  1. **`L-SMP` (`N18`+):** Isolated TT lock ablation on 8 openings (`go movetime 600`, `Hash=64`, 2 ABBA passes): `T1` noise (`+0.5%`), `T2`: `dirty_rbw +5.3%` (`nolock_diag +10.6%`), `T4`: `dirty_rbw +8.1%` (`nolock_diag +16.8%`). Strictly-stronger **`postlock_rbw`** (`lock(stripe)` FIRST, then `if (!stripes_dirty_.load(seq_cst)) stripes_dirty_.store(true, seq_cst)`): `1T bench 11 = 226187`, **TSan exit=0, zero warnings**, ABBA `T4` **`+6.4%` NPS** (`6.562M -> 6.980M`, zero overlap)! Stage 2 lockless TT only if `T8/16` still `< 75%` efficiency + `>= +10%` lock headroom.
  2. **`L-TM` (`N19`+):** Corrected per Astra's exact source check: per-control truth table (`mtg==0` vs `mtg>0`), `TmNodeShare` depth<6 guard + final `[min_floor, hard_ms]` clamp + silent log, optional cumulative-drop / mate-loss clock candidates, clock-SPSA for the 10 untuned `Tm*` tunables.
  3. **`L-SEARCH` (`N22`+):** 22 dormant switches swept d10/d13/d15 (`LmrSignedCorrection` `0/20->1/20->6/20`, `NullThreatVerify` `3/20->11/20->18/20`, `CaptureFutilityBase=120` `-12.1%` at d15, `LmrLateParentRelief` flips `+1.9%->-2.5%`); overlaps flagged (`ThreatHistory`+`HistRework=2` `+19.7%`, `SoundMatePruning`+`MateAlphaGuard` `+10.3%`); keep failed dormant switches disabled (no forced deletion unless branch-cost profiled); measure real games/hour before scaling SPSA cost.
  4. **`L-WIN` (new):** Anchored in `FINAL_PLAN.md` PC metrics (`2,917s`/`388M`, `4.445M` rows/s, `44.7–50.3 B/used row`, `196–224 MB/s`): separates (A) storage/RAM two-level streaming shuffle, (B) I/O stall vs GPU>=85% compute ceiling -> DDP + exact `W6`-style gradient-accumulation equivalence test, (C) multi-generation eviction trigger (`>=+50` Elo & `>=25%` fresh data).
  5. **`L-TB` (new beyond `W16`/`A25`):** Live 400-game `selfgame` exposure (`50,882` kept rows): `<=5` pieces = `8.44%` rows / `25.75%` games; `6` pieces = `3.91%` rows / `11.75%` games -> `<=6` = `12.36%` rows across `37.50%` games (anchored with round 137's `947` games / `1.56%` rows relabeled by 5-piece). Three tracks: 5-piece tournament, 6-piece NVMe SMP contention benchmark, offline 6-piece training-store rescoring (zero self-play NPS tax).
  6. **`L-GEN` (new beyond `A19`):** Live 400-game `selfgame` + `128k`-node terminal audit FALSIFIED my pre-measurement `evallimit`/`drawadj` bug suspicion on `r67` (`0/120` `evallimit` `<1000cp`, `0/89` `drawadj` `>=200cp`, `2.79%` dup positions) -> turned into post-stronger-net scale-drift trigger + opening-saturation monitoring + equal-cost mixed-budget hypothesis.

## Immediate Next Actions
1. Commit & push `175648Z` + memory update.
2. Wait/poll Astra's branch (`AwaitShell`, ~2-minute intervals) for Astra's responses, any formal addendum drafts (`N24`+, `A28`+), and the first draft of `debate/engine_plan/ENGINE_PLAN_8H.md`.
3. While waiting, run any targeted follow-up check Astra asks for (e.g., `N22` real games/hour scaling at `20k / 60k / 100k / 250k` nodes on exact `Forge 6.5` so `L-SEARCH`'s cost table uses real measured game-time multipliers instead of naive node ratios!).
