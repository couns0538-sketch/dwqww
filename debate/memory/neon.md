# Memory file of neon

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from `date -u +%Y-%m-%dT%H:%M:%SZ`, never from my head.

## Who I am
- Name in this debate: neon
- Model: Gemini 4 Neon
- Started: 2026-11-23T03:40:08Z
- Last update: 2026-11-23T04:28:06Z
- Phase: 2 DEBATE (all three READY; Fable posted PLAN v4, BOARD updated `112607Z`, 5 PC measurements complete; Phase 3 starts ~06:10Z our clock, hard stop 06:40Z).

## What I have read
- [x] `debate/README.md`, `debate/PLAN.md` (v4), `debate/STATE.md`, `debate/BOARD.md` (`112607Z`), `debate/READ_CHECK.md`
- [x] All 26 source files (11,566 lines), `loop/LOOP_OPTIONS.txt`, `source/R65_NOTE.txt`, `loop/build_recipe/build_forge_clang_pgo.sh`
- [x] All 5 Fable PC evidence files: `fable_filter_shares_round136.*`, `fable_a1_roundtrip_round136.md`, `fable_a4_lmr_switch_same_rule.md`, `fable_n4_crosstab_round136.*`, `fable_n2_live_search_pin.md`, `fable_n8_games_round136.*`
- [x] All messages up to shared `6e5815b218` and Astra `3087323d05`.

## Local verification runs (in `/tmp/forge-bin/`, repo untouched)
- Linux builds: `forge_v4` (AVX-512+PEXT), `forge_v3_pext` (AVX2+PEXT), `forge_v3` (AVX2 no-PEXT), `forge_san` (ASan+UBSan, 0 errors), `forge_cmake` (stock `CMakeLists.txt` -> `bench 11 = 278016`).
- Verified pins: defaults `312866 / 862329 / 4865609`; r67 `226187 / 616966` (FNV-1a `290bbb0b2e578ac`, SHA-256 `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28`).
- Verified `A4` (`LmrDeeperShallower value true` + r67) on Linux: `forge_v4` and `forge_v3_pext` both give `bench 13 = 595569` (matches Fable's two Windows trees & Astra's Linux build).
- Verified `N2` live Hash pin (now matched on 4 binaries across PC+Linux): Hash 16 `375880 / hashfull 156`, Hash 32 `375868 / hashfull 78`.
- Verified Astra's `F1` softnodes fixture (line 4 of `pgo_selfplay_books.epd`): `go nodes 2000` -> `depth 7 nodes 1926 bestmove b2b3`; `go softnodes 2000` -> `depth 8 nodes 5506 bestmove g1f3`.
- Verified `nnue_v3.hpp:120,133` (`Accumulator`/`RefreshCache` statically sized to `MaxHidden = 1024`), `search.cpp:1974,1991` (all 5 `qsearch_child` callers satisfy `!root_node && excluded.is_none()`), and `uci.cpp:529-544` (`evallimit` breaks before `records.push_back`).

## Proposals & convergence status
- `A1`–`A5`: ACCEPTED / TO MEASURE (`A2`), all 3 converged (Fable closed `A3` after Astra's answer).
- `N1`–`N9`: ACCEPTED / TO MEASURE (`N4, N5, N7, N9`) on `BOARD.md`; Neon agreed with all Fable PC findings/amendments (including `N8 (a)` receiver-side opening dedup + shared table + 200-game 2-ply control with retry guard, and `N8 (b)` Linux HCE parity if `teacher_weight > 0` stays).
- `F1`: CONVERGED 3/3 (amended `[-3, 0]` paired/pentanomial SPRT, cap 100k = inconclusive = not adopted, `A vs A` two-H0 trigger, plus Astra/Neon `go softnodes 2000` transcript preflight).
- `N10` (`P4` concurrent 1-thread speed-odds calibration + equal-clock `J9` proof + self-play yield) & `N11` (`P5` offline twin, `P6` deferred, `J4`/`P7`/`P12` unified bundle bar + process-tree kill, `Q2b` parameter decision tree): Astra + Neon converged; awaiting Fable's reply (including `QUESTION` on `W3`'s `236k/250k` calibration).

## Next steps
- Push `20261123T042806Z_neon_re_f1_n8_n9_n5_n4.md` + this memory file.
- Watch both branches for Fable's reply to `N10`/`N11`, any `F2+`/`A6+` proposals, and `PLAN.md` updates until Phase 3 (`debate/FINAL_PLAN.md`, ~06:10Z our clock).
