# T04H VERIFY (adversarial verifier, 2026-11-05 01:09-01:29 PC clock)
Scratch: F:/odr/work/T04H-verify/ (own pentanomial script ptnml_verify.py, live api/get_run records, commit messages).
Method: every number re-fetched live (fishtest api/get_run, gh api commit message), Elo recomputed with own arithmetic
(pentanomial mean per pair, 95 % = 1.96 sigma through the logistic curve; logistic W/L/D Elo for the "~" miner numbers);
licence rows re-run; lock lines re-read in src_al1s198_clean; greps re-run; duplicates checked against all cards/*/,
notes/T04/TABLE.md, notes/T04C/TABLE.md, notes/TRIED_GATES.md.

| card | claim | verdict | evidence |
|---|---|---|---|
| T04H-01 | STC 5f49203c: 10+0.1, Threads=1, noob_3moves.epd, logistic SPRT [-0.25,1.25], LLR 2.95, n=29,968, Ptnml 146/2432/9671/2560/175, +2.16 +- 1.80 | CONFIRMED | live record: W/L/D 3381/3195/23392, LLR 2.946, elo_model logistic; own ptnml +2.16 +- 1.80, logistic +2.16 |
| T04H-01 | LTC 5f494bea: 60+0.6 [0.25,1.25] LLR 2.96 n=84,952 +1.17 +- 0.74 | CONFIRMED | live record: W/L/D 4619/4333/76000, Ptnml 86/3765/34481/4065/79, LLR 2.956; own ptnml +1.17 +- 0.74 |
| T04H-01 | mechanism quote "add if previous leaf is in search tree and we didn't find a counter move, else remove ..." and that both halves were in the test | CONFIRMED | commit message c02b3a4c7a (gh api) has that text and both test links; run info of 5f49203c reads "If previous node is ttPv and we find a good move, consider child node as ttPv" = the card's fail-low-under-ttpv-parent reading (added to the card by verify) |
| T04H-01 | e31f97e "Remove ttPv tree shrinking" dropped the remove half, non-reg STC ~-0.25 n=270,408 / LTC ~+1.45 n=34,368 | CONFIRMED | message: W/L/D 71593/71785/127030 -> -0.26; 9135/8992/16241 -> +1.45; bounds <-2.25,0.25> non-reg; text says only the shrinking step was removed |
| T04H-01 | 1b31e26 "Consider more nodes as ttPv nodes" STC ~+0.73 n=82,528 / LTC ~-0.09 n=310,440 / VLTC ~+1.02 n=59,496 | CONFIRMED | message W/L/D 21627/21453/39448 -> +0.73; 78879/78956/152605 -> -0.09; 15158/14983/29355 -> +1.02; all three are non-regression bounds <-1.75,0.25> (the card says "later widening" and "non-reg" context is in the message: "Remove depth condition in propagation rule") |
| T04H-01 | commit date 2020-08-30 | CONFIRMED (committer date) | author date 2020-08-28; licence_at row also says 2020-08-30; not material |
| T04H-01 | lock: ss->tt_pv set once at search.cpp:919, stored unchanged at :1214; LMR :1137-1139; ProbCut store :1023; qsearch :793 / :868; excluded search saves / restores :1093-1096; bound at :1212; null move current_move none :972; root ss = &stack_[4] :1360 | CONFIRMED | forge_has 'tt_pv' re-run = the same 10 hits; lines read |
| T04H-01 | not in TRIED_GATES, no existing card grows the ttpv set | CONFIRMED | tried_gates.py --grep (ttpv / history / replacement / aging ...) = 0 of 110; cards mentioning ttpv: T04B-03, T04B-04, T04C-02, T06B-01 all consume the bit (LMR / singular), none propagates it |
| T04H-01 | licence row Stockfish c02b3a4c7a GPL-3.0 | CONFIRMED | licence_at.py --row re-run, identical |
| T04H-01 | own start depth 5, no source constant | CONFIRMED | the depth condition is in no text read (message, PR 3075 body, run info); 1b31e26 says only that a depth condition existed and was removed |
| T04H-02 | STC 5e2ff5ef: 10+0.1 [-1,3] LLR 2.95 n=13,302 W/L/D 2647/2507/8148 +3.62 +- 3.69 | CONFIRMED | live record Ptnml 237/1540/2956/1632/260, LLR 2.952, logistic model, noob_3moves.epd, Threads=1; own ptnml +3.62 +- 3.69, logistic +3.66; lower edge -0.07, so "consistent with zero at 95 %" holds |
| T04H-02 | LTC 5e2fff38: 60+0.6 [0,2] LLR 2.95 n=15,797 W/L/D 2137/1960/11700 +3.81 +- 2.71 | CONFIRMED | live record Ptnml 96/1443/4628/1547/130, LLR 2.945; own ptnml +3.81 +- 2.71 |
| T04H-02 | test note "apply it on ex-pv nodes only" | CONFIRMED | run info of both records: "Take 2 (...): apply it on ex-pv nodes only" |
| T04H-02 | message quote "keep past PV (ttPv) nodes as close as possible to current PV nodes" | CONFIRMED | commit message 71e0b5385e |
| T04H-02 | "no later Stockfish title or message 2020-2026 removes it" | CORRECTED (claim was wrong) | cache grep of all Stockfish messages 2016-now (F:/odr/cache/commits, pattern ttpv / past pv + bonus / remov): 6ccb1cac5a "Revert 5 recent patches" (2020-01-31, 3 days after 71e0b53) reverted exactly this patch after a regression test of the merged batch showed negative Elo (issue 2531); removing it alone passed as a simplification STC 10+0.1 {-1.5,0.5} n=46,100 W/L/D 8853/8727/28520 Ptnml 796/5297/10749/5387/813 = removal +0.93 +- 1.93, LTC 60+0.6 n=16,920 W/L/D 2161/2055/12704 Ptnml 115/1498/5006/1569/130 = removal +2.11 +- 2.60 (own arithmetic). The worker's grep missed it because the revert's title has no ttPv word. A re-add was not found by the same grep (ttpv / past PV / former PV / ex-pv together with bonus / stat / history / remove / simplify, all cached messages 2016-now); a re-add worded without those terms would escape it. Card Source and Expected gain corrected; the card's case (an LTC pass) is therefore not durable at the source. acb0d20 part: not re-checked (UNVERIFIABLE, not material now) |
| T04H-01, T04H-03 | the cited commits were not reverted | CONFIRMED | the same cache grep for c02b3a4 / "Add / remove leaves" and 9451419 / "remplacement" / "Increase chance that PV" finds no revert; the only later references are e31f97e (shrinking half) and 1b31e26 (depth condition), as the cards say |
| T04H-02 | lock :1198 passes depth + (best_score > beta + 100), :1200 plain depth, :1203-1204 quarter bonus without cutoff, update_quiet_stats :729-750 one bonus for best move and malus of tried quiets | CONFIRMED | forge_has re-run (12 hits) and lines 1195-1215 read |
| T04H-02 | T04G TABLE row 12 (Altair PR 50 bundle +1.64 +- 1.86) is a related, different row | CONFIRMED as different | pv-node flag in a bundle, not the stored ttpv bit; card calls it a caution, not a duplicate |
| T04H-02 | licence row 71e0b5385e GPL-3.0; own start 1 range 0-2 | CONFIRMED | row re-run identical; the source's bonus form is in no text read |
| T04H-03 | STC 61ae0683: 10+0.1 UHO_XXL_+0.90_+1.19 [0,2.5] LLR 2.93 n=46,744 +2.17 +- 1.60 | CORRECTED (precision) | live record W/L/D 12108/11816/22820, Ptnml 156/5221/12344/5477/174, LLR 2.934, Threads=1; own ptnml +2.17 +- 1.60. The bounds are normalized-Elo bounds (elo_model "normalized", angle brackets in the message), not logistic as in the 2020 tests: noted in the card by verify |
| T04H-03 | LTC 61ae9736: 60+0.6 [0.5,3] LLR 2.94 n=88,464 +1.57 +- 1.07 | CONFIRMED (nElo bounds) | live record W/L/D 22912/22513/43039, Ptnml 84/9133/25393/9544/78, LLR 2.937; own ptnml +1.57 +- 1.07 |
| T04H-03 | message "Increase chance that PV node replaces old entry"; run note "Allow for more depths (+2) replacement if pv" | CONFIRMED | commit message 9451419912 and run info (spelt "replacment") |
| T04H-03 | own start 3 range 0-8, not the source's +2 | CONFIRMED | the source's +2 appears only in notes (sources.md, allowed as a quoted test note); the card proposes its own value |
| T04H-03 | lock :294 overwrite test has no pv term, :300 writes the pv bit, :272-280 victim choice has no pv term | CONFIRMED | lines 255-301 read: test is `bound == BoundExact || !same_position || depth + 4 > entry->depth || generation differs` |
| T04H-03 | no duplicate | CONFIRMED | no card or T04 / T04C table row couples the pv bit to replacement; T04C B1 (entry age / refresh on hit) is a different rule |
| notes row 4 / evidence B1 | d47aa63 STC 6620faee 10+0.1 UHO_Lichess_4852_v1 [0,2] LLR 2.94 n=152,256 +1.11 +- 0.89; LTC 66231ab5 60+0.6 [0.5,2.5] LLR 2.95 n=51,564 +2.34 +- 1.41; rule "age of this TT entry, not of the position" | CONFIRMED (nElo bounds) | live records and message re-read; own ptnml +1.11 +- 0.89 / +2.34 +- 1.41; lock :265-267 refreshes the generation on a hit (opposite), as the note says |
| notes TABLE rows 7-8 (PlentyChess #284, #359) | numbers from PR text | UNVERIFIABLE in this pass | not re-fetched (time cap); no card rests on them |
| notes TABLE "~" miner rows 9-28 | logistic W/L/D numbers from commit messages | UNVERIFIABLE in this pass (titles only, no card rests on them) | only e31f97e and 1b31e26 were recomputed (above, both confirmed) |
| licences.md | 9 rows (Stockfish x4, PlentyChess x2, Stormphrax, Obsidian, Berserk) | CONFIRMED | all 9 licence_at.py --row re-runs identical |
| all | reading rule | CONFIRMED as far as checkable | sources.md lists only messages, PR bodies, run records and titles; F:/odr/work/T04H holds only run JSONs, two own scripts and two own md files, no source file; cannot prove a negative beyond that |
| all | no vendor / model-company names in cards/T04H, notes/T04H | CONFIRMED | grep (vendor and model names) = 0 hits |
| all | at most 4 cards, crew hours, UNPROVEN labels, lint | CONFIRMED | 3 cards (2 full of 57 / 53 lines, 1 one-liner); crew h in every card; "UNPROVEN" in every Forge estimate; card_lint 0 findings / 0 PENDING on all three (re-run after the verify edits below) |
| all | other engines' tuned constants | CONFIRMED none proposed | TtPvFailLowDepth 5 (0-20), TtPvHistPlies 1 (0-2), TtPvStoreBonus 3 (0-8) are own; the lock's +4 at :294 is the lock's own |
| all | prior own code (TRIED_GATES packb ReSearchAdjust / FiftyDamp, packa NonPawnCorr / PawnHist, E3 eval options; R15 D:/o15/cands/INDEX.md grep ttpv / history bonus / replacement: only x1_ttcutoffhistory, a history update on a TT cutoff, which card T04H-02 already names as another site) | CONFIRMED no overlap | packb = re-search adjust + fifty-move damping, packa = correction history, E3 = eval post-processing; none touches the ttpv bit, the history depth term or TT replacement |

## Verdict
- Checked: 34 claims (3 cards fully, the d47aa63 evidence note, licences, greps, duplicates, lint). CONFIRMED 30,
  CORRECTED 2 (T04H-02 removal claim: reverted at the source; T04H-03 bounds are normalized-Elo, a precision fix),
  UNVERIFIABLE 2 (PlentyChess PR numbers in TABLE rows 7-8 not re-fetched; "~" miner rows 9-28 except the two
  recomputed; neither carries a card), VIOLATION 0, DUPLICATE 0.
- Cards changed by verify: T04H-01 (one confirming sentence in Mechanism), T04H-02 (Source removal check rewritten,
  caution in Expected gain), T04H-03 (bounds unit). No card deleted, Status lines unchanged (no violation, no duplicate).
- card_lint after the edits: 0 findings / 0 PENDING on all three; lines 58 / 60 / 1 (cap 60).
- Coordinator items: (1) T04H-02 now rests on a source result that the source itself reverted; its STC was already
  consistent with zero. Consider demoting it to a one-liner or dropping it. (2) T04H-01 and T04H-03 stand as written
  (0 to +2 Elo UNPROVEN each). (3) Rows 7-8 and the "~" rows of TABLE.md are un-re-checked notes only.
