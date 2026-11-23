# Neon's debate memory

Last updated: 2026-11-23T05:57:48Z (Neon's clock)
Phase: 2 DEBATE (owner-extended window through 07:17Z; final text ~06:40Z; post-07:17Z Astra+Neon addendum workflow noted)

## Current Status
- Shared branch HEAD (before this push): `9ed5066a88`; Astra branch HEAD: `833fa4599a`.
- Zero active dissent on `debate/FINAL_PLAN.md` Draft 2.
- All 30 earlier proposals (`A1`–`A12`, `N1`–`N14`, `F1`–`F4`) accepted 3/3 and written into Draft 2.
- Just voted `AGREE` (with independent checks) on:
  - `F5` (sparse pentanomial tables + all-middle A/A exact LLR `+0.008672/pair`, 339 no stop / 340 H1; also verified single-bin extremes on `fable_n13_recount.py.txt`) -> now 3/3.
  - `A13` (W4 checked-and-grouped opening clustering + 3 distinct seeds + copied-score control + matched 50k/250k) -> now 3/3.
  - `A14` (W5 positive/negative controls for after-game tablebase & lone-king result overrides; awaiting Fable).
  - `A12` primary contrast = equal passes (40 vs 40), equal steps named separately, cross-device A8 check -> now 3/3.
- Verified all **768/768** games of Astra's `F4` dataset (`053938Z`) bit-identical on `/tmp/forge-bin/forge_v4` (`0` mismatches on rows/searches/nodes/ending), plus CSV means, bootstrap CI, home-overlap arithmetic, and R1/F2 pair variances.
- Noted Fable's `N12` Windows oracle 18/18 exact pass (`fable_n12_sixgames_windows.txt`) and W1/W7/W12 PC declaration audit (`124325Z`).
- Just proposed **`N15`** (`055748Z`): fail-loud UCI `setoption` stdout gate (`unknown option` / `invalid value` / `ERROR` / `cannot load` / `sgerror`) in `W5 (b)`/`W1`/`W14` + `MateAlphaGuard` coverage in `W5 (i)` (`h2h4 b7b5 g2g4 g7g5 h1h2 c8a6 e2e3 d7d5`: `172/matescore/173/741342` `41284fe7...` ON vs `171/matescore/172/737195` `121b6606...` OFF on both AVX-512 and AVX2; omitting `MateAlphaGuard` passes `bench 11/13`, `W5 (b)` `375880/156`, and all 6 `N12` games while altering 57/64 `matescore`/`mate` games in Astra's 768-game sample).

## Next Steps
1. Watch both branches for Fable's and Astra's replies to `N15` and Fable's reply to `A14` (plus any further proposals before `~06:40Z`).
2. Continue auditing `source/` and `debate/FINAL_PLAN.md` for any remaining silent failure modes or arithmetic/test-bar holes.
3. Update `debate/memory/neon.md` every ~10 minutes (next due ~`06:08Z`).
4. When Fable issues final `debate/FINAL_PLAN.md` (without DRAFT, ~`06:40Z`), verify every rule `R1`–`R6` and item `W1`–`W16`, push `debate/msgs/<UTC>_neon_final.md`, mark memory `DONE`, and wait / finish per schedule.
