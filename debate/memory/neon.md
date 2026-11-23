# Memory file of neon

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from `date -u +%Y-%m-%dT%H:%M:%SZ`, never from my head.

## Who I am
- Name in this debate: neon
- Model: Gemini 4 Neon
- Started: 2026-11-23T03:40:08Z
- Last update: 2026-11-23T05:27:02Z
- Phase: 2 EXTENSION (owner extended debate up to 2h from 05:17Z, latest stop ~07:17Z–07:20Z our clock, ending earlier when all three say "NOTHING MORE"; all three confirmed extension including Astra `848aa04f80`).

## What I have read
- [x] `debate/README.md`, `debate/PLAN.md` (v5+), `debate/STATE.md`, `debate/BOARD.md`, `debate/FINAL_PLAN.md` (DRAFT 2 `5a7a42e3e4`), `debate/READ_CHECK.md`
- [x] All 26 source files (11,566 lines), `loop/LOOP_OPTIONS.txt`, `source/R65_NOTE.txt`, `loop/build_recipe/build_forge_clang_pgo.sh`
- [x] All Fable PC measurements (14+ files in `debate/evidence/`)
- [x] All messages up to shared `5a7a42e3e4` and Astra `848aa04f80`.

## Local verification runs (in `/tmp/forge-bin/`, repo untouched)
- Linux builds: `forge_v4` (AVX-512+PEXT), `forge_v3_pext` (AVX2+PEXT), `forge_v3` (AVX2 no-PEXT), `forge_san` (ASan+UBSan, 0 errors), `forge_cmake` (`bench 11 = 278016`).
- Verified pins: defaults `312866 / 862329 / 4865609`; r67 `226187 / 616966` (FNV-1a `290bbb0b2e578ac`, SHA-256 `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28`); `A4` switch on `595569`; `N2` live Hash pin `375880 / 156` (Hash 16) vs `375868 / 78` (Hash 32); `F1` softnodes fixture `1926 b2b3` vs `5506 g1f3`.
- Verified `A7` witnesses (`H1`/`H2` 0 vs 128 searches; `W1`/`W2` 81 `drawadj` vs 67 `rule`; pinned-pawn `d6` vs `-` `sg 2 797` vs `789`), exhaustive `ep_square_` source proof, and `40/40` bit-identical live `selfgame` runs (5,114 lines) on all 40 raw-EP-diff no-adjacent-pawn pairs.
- Verified `F2` Wald expected games (`SE = 3.13` at 4,000 games -> `8,307.8` games at true 0 Elo).
- Verified `N12` live inter-game state pollution on `/tmp/forge-bin/forge_v4` (`source/src/uci.cpp:448-499` never calls `searcher.clear()`): Game 2 (`d2d4 d7d5 c2c4 e7e6 b1c3 g8f6 c1g5 f8e7`) after Game 1 (`e2e4 e7e5 ...`) gives `101` rows `drawadj` (`sg 8 11 e2e3`, 383,484 nodes) WITH `ucinewgame` vs `43` rows `rule` (`sg 8 8 e2e3`, 152,827 nodes) WITHOUT `ucinewgame`.
- Verified `N13` exact logistic-Elo pentanomial GSPRT LLR table (`±ln(19) = ±2.944439`): `[1100,3300,13200,3300,1100]` (`+4.6844`, `H1`), `[550,1650,6600,1650,550]` (`+2.3422`, continue), `[1043,3086,12000,2914,957]` (`-4.2270`, `H0`), `[957,2914,12000,3086,1043]` (`+12.7315`, `H1`); `2× LLR` bug inflates false-stop error from `5.0%` to `18.66%`.

## Proposals & convergence status (24 total: A1-A8, N1-N13, F1-F3)
- `A1`–`A8`, `N1`–`N11`, `F1`–`F3`: ALL 22 CONVERGED 3/3 (zero dissent on Draft 2 + F2/F3/A8).
- `N12` (proposed `052702Z`): `W5` cross-system consecutive-game persistent-worker `selfgame` parity against PC Windows reference + two negative controls (missing `ucinewgame`, wrong `selfgame` arg) + regenerating `W5 (b)` & `N12` pins if `W1`/new net updates the frozen manifest.
- `N13` (proposed `052702Z`): `W3 (a)` exact numerical pentanomial-GSPRT LLR + stopping-boundary parity checks on 4 fixed synthetic tables (catching `2× LLR` `18.66%` error, `[0,+3]`/`[-5,0]` wrong hypotheses, and scale/sign bugs).

## Next steps
- Push `N12`+`N13` + `F2`/`F3`/`A8` votes + updated memory; monitor both branches for Fable's and Astra's responses, any further weakest-test proposals, and Phase 3 final votes.
- Update `debate/memory/neon.md` every ~10 minutes.
