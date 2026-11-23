# Memory file of neon

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from `date -u +%Y-%m-%dT%H:%M:%SZ`, never from my head.

## Who I am
- Name in this debate: neon
- Model: Gemini 4 Neon
- Started: 2026-11-23T03:40:08Z
- Last update: 2026-11-23T05:37:33Z
- Phase: 2 EXTENSION (owner confirmed full 2-hour window to 07:17Z our clock, final text for votes ~06:40Z; Fable checking PC pre-existing declarations for W1/W7/W12; Astra running 16.37M-draw + 384v384 node-cost control for F4).

## What I have read
- [x] `debate/README.md`, `debate/PLAN.md`, `debate/STATE.md`, `debate/BOARD.md`, `debate/FINAL_PLAN.md` (DRAFT 2 `a2f6fa6865`), `debate/READ_CHECK.md`
- [x] All 26 source files (11,566 lines), `loop/LOOP_OPTIONS.txt`, `source/R65_NOTE.txt`, `loop/build_recipe/build_forge_clang_pgo.sh`
- [x] All Fable PC measurements (including `fable_n13_recount.*`)
- [x] All messages up to shared `9325190e70` and Astra `ae37fa5b79`.

## Local verification runs (in `/tmp/forge-bin/`, repo untouched)
- Linux builds: `forge_v4` (AVX-512+PEXT), `forge_v3_pext` (AVX2+PEXT), `forge_v3` (AVX2 no-PEXT), `forge_san` (ASan+UBSan, 0 errors), `forge_cmake` (`bench 11 = 278016`).
- Verified pins: defaults `312866 / 862329 / 4865609`; r67 `226187 / 616966` (FNV-1a `290bbb0b2e578ac`, SHA-256 `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28`); `A4` switch on `595569`; `N2` live Hash pin `375880 / 156` (Hash 16) vs `375868 / 78` (Hash 32); `F1` softnodes fixture `1926 b2b3` vs `5506 g1f3`.
- Verified `A7` witnesses (`H1`/`H2`, `W1`/`W2`, pinned-pawn `d6` vs `-`), exhaustive `ep_square_` source proof, and `40/40` bit-identical live `selfgame` runs (5,114 lines).
- Verified `N12` live inter-game state pollution (`101` vs `43` rows) AND independently reproduced Astra's unified 6-game persistent-worker golden fixture bit-for-bit across all 6 games & all 3 Game-2 SHA-256 digests (`163821da...`, `ecca95c7...`, `39c876ed...`).
- Verified `N13` exact logistic-Elo multinomial-MLE pentanomial GSPRT LLR across all 3 independent programs (`+4.684394`, `+2.342197`, `-4.227008`, `+12.731538`).
- Verified `N14` per-lane `int32` thresholds (`H <= 2080` safe on AVX2 `sum0`: `2,147,125,500 <= INT32_MAX`; `H = 2112` overflows `2,180,158,200`) and audited `apply_pair_and_sum_avx512` (`nnue_v3.cpp:444-516`) vs `output_sum_with` (`807-818`) vs `eval` (`uci.cpp:1208`).
- Verified `F4` (`16.37M` games -> `2.10%` dup = `30.2 min / 24h`), `A10` (`2B * 40.8 B = 76.00 GiB`; `4.445M * 44 B = 195.58 MB/s`), `A11` (`23,149/s` vs `25,446/s` at `21h50m`; `13.89M` rows / 10 min).

## Proposals & convergence status (30 total: A1-A12, N1-N14, F1-F4)
- `A1`–`A8`, `N1`–`N13`, `F1`–`F3`: ACCEPTED 3/3.
- `A9` (paid-GPU checkpoint & full-state resume), `A10` (target-card full-shape VRAM/RAM/disk pilot), `A11` (server lease-closeout & remaining-time rate), `A12` (W13 operational incumbent vs causal volume wording): Astra proposed, Neon AGREE, Fable reviewing.
- `F4` (allocator optional/built last/fail-open + multi-worker deterministic `(run_root_seed, worker_id, game_seq)` replay & `>= 99%` unique-payload bar): Fable proposed, Neon AGREE, Astra measuring 16.37M-draw + 384v384 node-cost proxy.
- `N14` (`W9` & `W5 a` raw pre-`finish()` fused `apply_pair_and_evaluate` quiet/capture/fallback test + child accumulator check + asymmetric fixture + `H <= 2080` narrowest-lane loader ceiling): Neon proposed, Astra AGREE + sharpened (Neon accepted sharpenings), Fable reviewing.

## Next steps
- Push reply + updated memory; monitor Fable's PC declaration audit (`W1`/`W7`/`W12`) & responses to `A9`–`A12` + `N14`, plus Astra's `F4` 16.37M-draw measurement.
- Continue auditing `source/` / `FINAL_PLAN.md` for any remaining weak tests; update `debate/memory/neon.md` every ~10 minutes; final votes after ~`06:40Z` (hard stop `07:17Z`).
