# Neon's debate memory

Last updated: 2026-11-23T06:08:47Z (Neon's clock)
Phase: 2 DEBATE (owner-extended window through 07:17Z; new proposals before ~06:25Z; final text ~06:40Z; post-07:17Z Astra+Neon addendum workflow noted)

## Current Status
- Shared branch HEAD (before this push): `a319355cf6`; Astra branch HEAD: `5d701fc49d`.
- Zero active dissent on `debate/FINAL_PLAN.md` Draft 2.
- All 36 earlier proposals (`A1`–`A15`, `N1`–`N15`, `F1`–`F6`) now have 3/3 agreement after our `060846Z` reply:
  - `A15`: Neon independently verified all 9 LLR values (fixtures A/B/C + reset + `-3/0` + Fable's double-counted block 1) and voted `AGREE` (including Fable's per-look LLR & pair-count check).
  - Astra `060545Z`: `AGREE` on both `F4` wording ("independent, reproducible draws keyed by different IDs", `>=99%` scoped to short outage rehearsal fixture) and `A10` units (`50.3 * 2e9 = 100.6 GB = 93.69 GiB`).
  - `N15`: Windows parity DONE (`fable_n15_guard_game_windows.txt`), matching both Linux builds to the exact SHA-256 (`41284fe7...` ON, `121b6606...` OFF/omitted) and all 4 faulty option lines.
- Just proposed **`N16`** (`060847Z`): Linux PGO profile workload (`NNUEArch=true` + frozen `.fnn3` + ALL `LOOP_OPTIONS.txt` + `selfgame`), non-empty profile consumption enforcement (`-Werror=missing-profile` / `.profdata` check), and interleaved `selfgame` speed-over-plain-`-O3` bar in `W5 (a)`, plus matching-profile PGO rebuilds before clocked/self-play timing in `W14` and `R3`.
  - Evidence: `loop/build_recipe/build_forge_clang_pgo.sh:84-108` (`fair-eval` 0.487 vs 0.984 half-speed regression), plus live Linux `g++ 13.3.0` experiment (180 interleaved `selfgame` games, bit-identical pins `226187 / 616966 / 375880/156`): `pgo_good` `37.673s` (`+1.85%` vs plain `-O3`, `+4.81%` vs `pgo_bad`), `plain_o3` `38.371s`, `pgo_bad` `39.484s` (`-2.82%` slower than plain `-O3`!).

## Next Steps
1. Watch both branches for Fable's and Astra's replies to `N16` (and any new proposals before `06:25Z`).
2. Keep updating `debate/memory/neon.md` every ~10 minutes (next due ~`06:19Z`).
3. Do a final clean read-through of `debate/FINAL_PLAN.md` before `06:40Z` so our Phase 3 vote (`debate/msgs/<UTC>_neon_final.md`) is fast, accurate, and covers every `R1`–`R6` and `W1`–`W16`.
4. After `07:17Z`, follow the owner's guidance if any addendum work continues or end cleanly once Phase 3 Final is complete (never reply to the user until Phase 3 Final is done).
