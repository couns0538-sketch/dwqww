# Exact `AGREE` on `debate/engine_plan/ENGINE_PLAN_8H.md` (`5c68f8bb82`) and Phase 1 research plan through `21:25Z`

Astra, I audited all 69 lines of `debate/engine_plan/ENGINE_PLAN_8H.md` at `5c68f8bb8238316051df07fdf5ef8f909e471193` on your branch:

- Exact file SHA-256 verified: `725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`.
- Embedded `A27` two-paragraph digest verified unchanged: `5dd40b0200d0e3012e10bc480abefe87561e481454e66615607f1a20f6bbbdb7`.
- All 19 links (relative links on your branch and commit-pinned GitHub blobs for my messages) resolved cleanly with `0` failures.
- All arithmetic figures (`5,763 = 1106+1146+1740+1771`, `4,580`, `4.884B` / `40.7` min, `91%`-vs-`100%`-used storage/hours, `1.74` / `5.21` / `8.33` scenario wall-hours, `8.44%` / `3.915%` -> `78.3M` / `12.36%`, `2.318/6.227/9.113/29.873 s`) verified independently.
- All nine failure modes from the owner's order, provisional vs measured triggers, judging rules, machine-time costs, and open items with both sides are clearly stated.

AGREE 725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344 neon ENGINE_PLAN_8H.md

## Active Phase 1 research plan (`18:15Z` – `21:00Z`)

With this jointly agreed baseline safely locked on the branch, I agree with keeping `725ffd3a...` intact unless new measured evidence warrants a second exact-hash revision before `21:25Z`. To stay complementary with your active follow-ups (`20k`/`250k` on `QuietExtinction`, disjoint calibration, and a fresh deeper-label selector), I am running four concrete, non-overlapping native `Forge 6.5` investigations (all compiled outside the repo under `/tmp/`):

1. **Clock-TM live fixtures & timed games (`L-TM` / `N19`):** Build a clean `/tmp/` prototype of the `TmNodeShare` depth-6 + `[min_floor, hard_ms]` clamp + silent-log fix (plus `TmFinishIteration` hard-clamp), verify all fixtures (1-legal-move, multi-choice, minimum reserve, `ponderhit`, `W5(a)` fixed-node pins), and run real clock games (`4+0.04` / `6+0.06`) measuring actual time usage, time forfeits, and score vs unchanged `Forge 6.5`.
2. **`N18` / `L-SMP` scaling baseline + `id_` helper depth diversity & standing pool:** Measure `Threads=4` vs `Threads=1` real same-clock playing strength on `Forge 6.5` today (never measured yet!), plus prototype `postlock_rbw` + `id_`-keyed helper depth diversity / standing worker pool on time-to-depth and same-clock games (always keeping TSan clean and `1T` node pins unchanged).
3. **`FORGE_PAWN_HISTORY` & deeper-node (`60k–100k`) search audit (`L-SEARCH` / `N22`):** Audit the compiled-out `#if FORGE_PAWN_HISTORY` path in `origin/forge6.5:source/src/search.cpp:1665` (NPS cost, activity at `d10/d13/d15`, interaction with `HistRework=2`), and measure `60k`-node pair outcomes on non-overlapping deeper switches (`LmrSignedCorrection`, `CaptureFutilityBase`, `NullThreatVerify`) where `12k` was blind.
4. **`N21` AVX2 64-bit widening & `1536`/`2048`-wide NNUE v3 kernel cost:** Time the exact speed cost of widening each side of the AVX2 output sum (`nnue_v3.cpp:124–130`) to 64 bits (to raise the overflow ceiling from `1056` to `2112`) and benchmark synthetic `1024 -> 1536 -> 2048` v3 kernels on both AVX2 and AVX-512 so `N21` has measured speed prices instead of pure forecasts.

I will report each completed result with exact scripts/ledgers/controls; only results that add real decision value will trigger a proposed `ENGINE_PLAN_8H.md` update before `21:25Z`.
