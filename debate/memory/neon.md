# Memory file of neon

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from `date -u +%Y-%m-%dT%H:%M:%SZ`, never from my head.

## Who I am
- Name in this debate: neon
- Model: Gemini 4 Neon
- Started: 2026-11-23T03:40:08Z
- Last update: 2026-11-23T05:13:13Z
- Phase: 2 DEBATE -> DRAFT AUDIT (Fable posted `debate/FINAL_PLAN.md` DRAFT `W1`–`W16` at `725bb9e6c9`; Astra and Neon completed item-by-item audits + closed current-EP pinned-pawn edge case; waiting for Fable's revised `FINAL_PLAN.md`; Phase 3 ~06:10Z our clock, hard stop 06:40Z).

## What I have read
- [x] `debate/README.md`, `debate/PLAN.md` (v5), `debate/STATE.md`, `debate/BOARD.md` (`120101Z`), `debate/FINAL_PLAN.md` (DRAFT `725bb9e6c9`), `debate/READ_CHECK.md`
- [x] All 26 source files (11,566 lines), `loop/LOOP_OPTIONS.txt`, `source/R65_NOTE.txt`, `loop/build_recipe/build_forge_clang_pgo.sh`
- [x] All 12 Fable PC measurements (including `fable_n8_counterexample_pc.md` and `fable_n8_windowkey.*`)
- [x] All messages up to shared `936c404f13` and Astra `be2beeea71`.

## Local verification runs (in `/tmp/forge-bin/`, repo untouched)
- Linux builds: `forge_v4` (AVX-512+PEXT), `forge_v3_pext` (AVX2+PEXT), `forge_v3` (AVX2 no-PEXT), `forge_san` (ASan+UBSan, 0 errors), `forge_cmake` (`bench 11 = 278016`).
- Verified pins: defaults `312866 / 862329 / 4865609`; r67 `226187 / 616966` (FNV-1a `290bbb0b2e578ac`, SHA-256 `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28`); `A4` switch on `595569`; `N2` live Hash pin `375880 / 156` (Hash 16) vs `375868 / 78` (Hash 32); `F1` softnodes fixture `1926 b2b3` vs `5506 g1f3`.
- Verified Astra's `N8` threefold counterexample (`H1` 0 rows `rep3=1` vs `H2` 128 searches `rep3=0`, identical 6-field FEN `... - 8 5`) AND Astra's `A7` nonterminal witness (`W1` 81 rows `drawadj` `sg 9 -15` vs `W2` 67 rows `rule` `sg 9 -30`, identical 6-field FEN `... - 8 5`).
- Verified `A7` reversible-window key `(manifest_id, whole_6_field_FEN, ordered reversible window)` from all `key_history_` readers (`board.cpp:364,1311,1463-1487,1770-1809`, `uci.cpp:457`, `search.cpp:2645`) and reconciled Fable's `113/132 (85.6%)` vs Neon/Astra's `117/132 (88.6%)` (`114/129` cross-order) to the exact 4 pairs (`#3, #31, #33, #129` 1-based in `fable_n8_seqsim_pairs_300k.txt`): `fable_n8_windowkey.py.txt:31` used `b.epd(en_passant="fen")` (pseudo-legal EP) on intermediate positions instead of `en_passant="legal"` (matching `Board::key_` at `board.cpp:1646-1655`).
- Verified Astra's pinned-pawn current-EP witness (`k1N1r3/2p3n1/8/3pP3/p4Qb1/P2p1B2/8/4Kn2 w - d6 0 23` vs `-`: `sg 2 797 a4b5` vs `sg 2 789 a4b5`), audited ALL `ep_square_` readers in `source/` (`board.cpp:434,582-586,715-718,871-879,1060,1188-1200,1207,1248,1298,1362,1653`, `search.cpp:1861,2378`), proved **adjacent-pawn current EP** (keep EP iff `(attacks::pawn(them, ep) & pawns[us]) != 0`, pinned or unpinned) + **legal historical EP** is 100% sound by construction, and verified **40/40 bit-identical live `selfgame` runs (5,114 `sg`+`sgdone` lines)** on all 40 raw-EP-diff no-adjacent-pawn pairs (`117/132 = 88.6%` recovered while separating pinned-pawn + `H1`/`H2` + `W1`/`W2`).

## Proposals & draft audit status (19 total: A1-A7, N1-N11, F1)
- ALL 19 proposals converged 3/3 (including `A7` / `N8` reversible-window key, `N11` Stage 3 `LB > -3` in 4,000 games at 250k nodes, `F1` paired SPRT `[-3, 0]`).
- Posted full item-by-item audit of `debate/FINAL_PLAN.md` DRAFT (`20261123T050426Z_neon_draft_audit_w1_to_w16.md`):
  - Answered Fable's `W5 (f)` question (`AGREE`), reconciled `113/132` vs `117/132` legal-EP normalization.
  - Backed Astra's 5 catches (`W1`/`W3` order, `W3 (a)` deterministic `A vs A` + synthetic `[1,0,0,0,1]` vs `[0,0,2,0,0]` paired fixture, `W4` lower-tail wording, `W5 (d)/(e)/(f)` score scope + round boundaries + nonterminal witness, `W13 (b)` explicit opponents & equivalence rule).
  - Flagged 5 Neon catches (`18->19` proposal count, `W1:46` all 45 settings not just 40 tuned, `W5 (h)` `W8->W13` typo, legal-EP normalization + `halfmove == 0` historical seeding, plus small completeness pins on `W5 (a)/(d)`, `W8`, `W9` (`source/include/forge/nnue_v3.hpp:65`), `W10`, `W12`/TD twin).
  - Backed Astra's additional pre-declared numerical bars on `W3 (b)` (odds calibration precision), `W10` (explicit deep-match threshold replacing "not weaker"), and `W14` (explicit pre-sweep flip-count threshold replacing "almost none"), plus closed Astra's current-EP pinned-pawn witness with exhaustive `ep_square_` source proof + `40/40` live `selfgame` check (`20261123T050603Z`, `20261123T051000Z`).
  - All other sections (`R2`, `R4`–`R6`, `W2`, `W6`, `W7`, `W11`, `W13 (a)`, `W14`, `W15`, `W16`) ready to AGREE as written.

## Next steps
- Push audit message + updated memory; monitor both branches cleanly for Fable's revised `FINAL_PLAN.md`, any follow-ups, and Phase 3 finalization (~06:10Z our clock, hard stop 06:40Z).
- Keep updating `debate/memory/neon.md` every ~10 minutes.
