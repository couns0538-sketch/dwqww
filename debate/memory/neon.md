# Memory file of neon

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from `date -u +%Y-%m-%dT%H:%M:%SZ`, never from my head.

## Who I am
- Name in this debate: neon
- Model: Gemini 4 Neon
- Started: 2026-11-23T03:40:08Z
- Last update: 2026-11-23T04:47:41Z
- Phase: 2 DEBATE (all three READY; Fable posted PLAN v4, BOARD `112607Z`, 5 PC measurements; awaiting Fable's answers to N10, N11, A6, F1 closure + softnodes check, and Astra's N8 5-field MEASURE; Phase 3 starts ~06:10Z our clock, hard stop 06:40Z).

## What I have read
- [x] `debate/README.md`, `debate/PLAN.md` (v4), `debate/STATE.md`, `debate/BOARD.md` (`112607Z`), `debate/READ_CHECK.md`
- [x] All 26 source files (11,566 lines), `loop/LOOP_OPTIONS.txt`, `source/R65_NOTE.txt`, `loop/build_recipe/build_forge_clang_pgo.sh`
- [x] All Fable PC evidence files: `fable_filter_shares_round136.*`, `fable_a1_roundtrip_round136.md`, `fable_a4_lmr_switch_same_rule.md`, `fable_n4_crosstab_round136.*`, `fable_n2_live_search_pin.md`, `fable_n8_games_round136.*`
- [x] All messages up to shared `65fa840a1c` and Astra `8487e46e8c`.

## Local verification runs (in `/tmp/forge-bin/`, repo untouched)
- Linux builds: `forge_v4` (AVX-512+PEXT), `forge_v3_pext` (AVX2+PEXT), `forge_v3` (AVX2 no-PEXT), `forge_san` (ASan+UBSan, 0 errors), `forge_cmake` (`bench 11 = 278016`).
- Verified pins: defaults `312866 / 862329 / 4865609`; r67 `226187 / 616966` (FNV-1a `290bbb0b2e578ac`, SHA-256 `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28`).
- Verified `A4` (`LmrDeeperShallower value true` + r67) on Linux: `forge_v4` and `forge_v3_pext` both give `bench 13 = 595569`.
- Verified `N2` live Hash pin (4 binaries across PC+Linux): Hash 16 `375880 / hashfull 156`, Hash 32 `375868 / hashfull 78`.
- Verified Astra's `F1` softnodes fixture (line 4 of `pgo_selfplay_books.epd`): `go nodes 2000` -> `depth 7 nodes 1926 bestmove b2b3`; `go softnodes 2000` -> `depth 8 nodes 5506 bestmove g1f3`.
- Verified `nnue_v3.hpp:120,133`, `search.cpp:1974,1991`, `uci.cpp:529-544`, `fable_n8_games.py.txt:43-105` (line 83 hashes only `ra[0]` FEN).

## Proposals & convergence status
- `A1`–`A5`: ACCEPTED / TO MEASURE (`A2`), all 3 converged.
- `A6` (Astra: separate `1024 @ 2B` training/screen prereq from `768 @ 2B` beating `r67`, keep incumbent equal-clock promotion separate): Neon AGREE (`65fa840a1c`); awaiting Fable.
- `N1`–`N9`: ACCEPTED / TO MEASURE (`N4, N5, N7, N9`) on `BOARD.md`. On `N8 (a)`: Astra & Neon converged on keying allocator by `(generator_manifest_id, ordered_8_ply_move_sequence)` + 5-field receiver game digest + bounded-retry `< 400`-game 2-ply control; Astra asked Fable a 5-field `MEASURE` on the 29 round-136 pairs (`8487e46e8c`).
- `F1`: CONVERGED 3/3 (amended `[-3, 0]` paired/pentanomial SPRT, cap 100k = inconclusive = not adopted, `A vs A` two-H0 trigger, plus Astra/Neon `go softnodes 2000` transcript preflight).
- `N10` (`P4` concurrent 1-thread speed-odds calibration + equal-clock `J9` proof + self-play yield) & `N11` (`P5` offline twin, `P6` deferred, `J4`/`P7`/`P12` unified bundle bar + process-tree kill, `Q2b` parameter decision tree): Astra + Neon converged; awaiting Fable's reply (including `QUESTION` on `W3`'s `236k/250k` calibration).

## Next steps
- Push updated memory file; share directional Linux `selfgame` `evallimit 1000` / `softnodes 4000` timing only if helpful; monitor both branches with longer intervals for Fable's reply to `N10`, `N11`, `A6`, `N8` 5-field `MEASURE`, and any `F2+` proposals until Phase 3 (`debate/FINAL_PLAN.md`, ~06:10Z our clock).
