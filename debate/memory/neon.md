# Neon Memory (8h Continuation — Phase 1: Engine Plan & Later Stages)

Updated: 2026-11-23T18:05:15Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra edits `debate/engine_plan/ENGINE_PLAN_8H.md` on `origin/debate/server-plan-20261123-astra`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**; `clockwatch` v4 / `test_clockwatch` **NOT YET** -> Opus.
- **ACTIVE NOW — Phase 1 (Hours 1–4, `17:25Z` – `21:25Z`): ENGINE PLAN & LATER STAGES.**
  - Deliverable by `21:25Z`: `debate/engine_plan/ENGINE_PLAN_8H.md` (edited by Astra) + `AGREE <sha256> neon ENGINE_PLAN_8H.md`. Fable checks once at `21:55Z`.
- **UP NEXT — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN.**
  - Queued for `21:25Z`: Opus worker/packer (`b9e369f9d1`, 4 files), `debate/server_day/specs/` (`171134Z`, `171332Z`, `172109Z` + all unwritten programs), ordered rehearsal + measurements (`171712Z`, `172415Z`), `FINAL_FOR_THE_OWNER.md` + `AGREE` by `01:25Z`.
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only.

## Phase 1 Progress (`180515Z`)
- **`A27` AGREED 2/2:** `AGREE 5dd40b0200d0e3012e10bc480abefe87561e481454e66615607f1a20f6bbbdb7` (Astra `174810Z`, Neon `175648Z`).
- **Independently verified ALL Astra `180116Z` / `180126Z` math:** exact Clopper-Pearson UBs (`0/89=3.31%`, `0/120=2.47%`, `0/200=1.49%`, `N=99/299/598`), `drawadj` collection (`898.9` mean / `993` 95% prob), `L-WIN` `91%`-vs-`100%`-used GB & compute hours, incremental 6-piece (`3.915%` = `78.3M` of `2B`), corrected full-pulse `0.6783` core-hours (`40.7` min), and Astra's independent `stripes_dirty_` micro-harness (`1.01/1.91/2.92x` TT, `1.01/1.98/3.99x` flag line) confirming `postlock_rbw` (`+6.4%` ABBA T4, TSan `exit=0`).
- **Completed live 24-opening whole-game depth-scaling table (`180515Z`):** exact `Forge 6.5` (`Hash=32`, 4 workers): `20k` `2.318s` (`1.00x`, `159.4` sr, `1.69x` soft, `58%` D) -> `60k` `6.227s` (`2.69x`, `139.1` sr, `71%` D) -> `100k` `9.113s` (`3.93x` vs `5.00x` linear, `124.7` sr, `71%` D) -> `250k` `29.873s` (`12.89x` vs `12.50x` linear, `164.9` sr, `1.71x` soft, `46%` D).
- **Sent full line-by-line review of Astra's first `ENGINE_PLAN_8H.md` draft (`59c7c9dd`, `180515Z`):** confirmed all Astra refinements/negatives (`173331Z`, `175236Z`, `175535Z`, `175734Z`, `180116Z`, `180126Z`), requested 7 targeted updates (A27 both votes, L-GEN + teacher ceiling, multi-candidate selection + non-SF pool, QuietExtinction + overlap + 0.6783h + whole-game scaling, clock-SPSA + dual-seat `postlock_rbw` SMP proof, verified `L-WIN` + uneven-tail DDP + `L-TB` prevalence/safeguards, updated Open Items + relative `../msgs/` links).

## Immediate Next Actions
1. Commit & push `180515Z` + memory update.
2. Wait for Astra's updated `debate/engine_plan/ENGINE_PLAN_8H.md` + bounded state-model check of `postlock_rbw` + any `A28` / addendum proposal.
3. Also independently verify `postlock_rbw` in Python bounded state-space model-checker (BFS over all interleavings of `ExclusiveLease` + `lock_stripe` workers!) so BOTH seats independently verify the formal concurrency proof!
4. Final exact-byte line review & `AGREE <sha256> neon ENGINE_PLAN_8H.md` before `21:25Z`, then pivot cleanly to Phase 2 (`21:25Z` – `01:25Z` Nov 24).
