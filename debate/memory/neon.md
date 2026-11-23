# Memory file of neon

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from `date -u +%Y-%m-%dT%H:%M:%SZ`, never from my head.

## Who I am
- Name in this debate: neon
- Model: Gemini 4 Neon
- Started: 2026-11-23T03:40:08Z
- Last update: 2026-11-23T04:57:35Z
- Phase: 2 DEBATE (all three READY; Fable posted PLAN v5 & BOARD `114702Z` with 10 PC measurements; Phase 3 `debate/FINAL_PLAN.md` starts ~06:10Z our clock, hard stop 06:40Z).

## What I have read
- [x] `debate/README.md`, `debate/PLAN.md` (v5), `debate/STATE.md`, `debate/BOARD.md` (`114702Z`), `debate/READ_CHECK.md`
- [x] All 26 source files (11,566 lines), `loop/LOOP_OPTIONS.txt`, `source/R65_NOTE.txt`, `loop/build_recipe/build_forge_clang_pgo.sh`
- [x] All 10 Fable PC measurements (`fable_filter_shares_round136.*`, `fable_a1_roundtrip_round136.md`, `fable_a4_lmr_switch_same_rule.md`, `fable_n4_crosstab_round136.*`, `fable_n2_live_search_pin.md`, `fable_n8_games_round136.*`, `fable_n8_opening_key_and_soft_fixture.md` + `fable_n8_seqsim_pairs_300k.txt`)
- [x] All messages up to shared `375abc2bcf` and Astra `c804f98bf3`.

## Local verification runs (in `/tmp/forge-bin/`, repo untouched)
- Linux builds: `forge_v4` (AVX-512+PEXT), `forge_v3_pext` (AVX2+PEXT), `forge_v3` (AVX2 no-PEXT), `forge_san` (ASan+UBSan, 0 errors), `forge_cmake` (`bench 11 = 278016`).
- Verified pins: defaults `312866 / 862329 / 4865609`; r67 `226187 / 616966` (FNV-1a `290bbb0b2e578ac`, SHA-256 `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28`); `A4` switch on `595569`; `N2` live Hash pin `375880 / 156` (Hash 16) vs `375868 / 78` (Hash 32); `F1` softnodes fixture `1926 b2b3` vs `5506 g1f3`.
- Verified Astra's `N8` threefold counterexample (`H1` 0 rows `rep3=1` vs `H2` 128 searches `rep3=0`, identical 6-field FEN `... - 8 5`) AND Astra's `A7` nonterminal witness (`W1` 81 rows `drawadj` `sg 9 -15` vs `W2` 67 rows `rule` `sg 9 -30`, identical 6-field FEN `... - 8 5`).
- Verified `A7` reversible-tail key `(manifest_id, whole_6_field_FEN, reversible_tail)` from all 4 `key_history_` readers (`board.cpp:364,1311,1463-1487,1770-1809`, `uci.cpp:457`, `search.cpp:2645`): catches `114 / 129 (88.4%)` of Fable's cross-order pairs (`117/132 = 88.64%` observed vs `3/132 = 2.27%` ordered moves; `97/97` at `halfmove == 0`) while separating both counterexamples.
- Local directional `selfgame` timing on 60 EPD openings (`forge_v4`, 1T, kept in notes): `sn=2000 eval=2000` 4.62 g/s (3810 nodes/search), `sn=2000 eval=1000` 4.95 g/s (+7.28% g/s, 0/60 result diffs), `sn=4000 eval=2000` 2.58 g/s (7266 nodes/search, 0.504x rows/s).

## Proposals & convergence status (19 total: A1-A7, N1-N11, F1)
- `A1`–`A6`: ACCEPTED / TO MEASURE (`A2`), all 3 converged.
- `A7` (Astra, independently co-derived & measured by Neon): `(manifest_id, whole_6_field_FEN, reversible_tail)` opening allocator key for `N8`; Astra + Neon converged (`114/129`, both terminal and nonterminal witnesses reproduced, `halfmove == 0` home-bank seeding bonus); awaiting Fable's reply to close `N8`'s open key point.
- `N1`–`N10`: ACCEPTED / TO MEASURE (`N4, N5, N7, N9`), all 3 converged (except `N8`'s key awaiting Fable on `A7`).
- `N11`: ACCEPTED — Stage 3 of `J11` (`LB > -3` in 4,000 games at 250,000 nodes after both 20k SPRT seeds pass, `SE = 3.13`, `LB > -3` requires `> +3.13`, `72%` power at `+5`; `P1` keeps `LB > 0`) now CONVERGED 3/3 (Astra `fbf03a349d`, Neon `13019ba4cf`).
- `F1` (`J10`): ACCEPTED 3/3 (paired/pentanomial `[-3, 0]` SPRT, cap 100k = inconclusive = no adoption; verify pair-level LLR wrapper before activation).

## Next steps
- Push updated memory file; monitor both branches for Fable's response to `A7` and `N11` Stage 3 closure, any new `F2+`/`A8+` proposals, and Phase 3 `debate/FINAL_PLAN.md` (~06:10Z our clock).
