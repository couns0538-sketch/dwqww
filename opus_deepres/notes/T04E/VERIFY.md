# T04E verify (adversarial pass, 2026-11-05, start 00:35 PC clock, stop by 00:55)
Verifier scratch: F:/odr/work/T04E-verify/ (own fresh fetches rk_<test>.html, viri_510.html, elo.py). Checks: (1) every
cited source number re-opened (PR body via gh api, commit message via the git-commit endpoint, test-log page fetched
anew), Elo +- recomputed from W/L/D and pentanomials; (2) reading rule and own constants; (3) licence rows re-run;
(4) Forge-has-it greps re-run and every cited lock line read; (5) duplicates against all cards and TRIED_GATES.md;
(6) card count, crew hours, UNPROVEN, names, card_lint.

Format: card | claim | verdict | evidence

## (1) Source numbers
T04E-01 | PR #818 title "Guard LMP for moves that give checks", merged 2026-03-25, squash 5e5443d798, head branch lmp-is-direct-check-again | CONFIRMED | gh api pulls/818 + git/commits/5e5443d7980b...; commit message = title + bench only
T04E-01 | STC 8+0.08 Hash 16 +2.84 +- 2.04 n=28,536 LLR 2.92 [0,3], W/L/D 7,260/7,027/14,249 (test 12650) | CONFIRMED | PR body, own fetch of recklesschess.space/test/12650/ (same totals, penta [71,3231,7438,3450,78]); recompute from penta +2.84 +- 2.04
T04E-01 | LTC 40+0.4 Hash 64 +9.46 +- 4.06 n=6,500 LLR 2.93 [0,3], W/L/D 1,681/1,504/3,315 (test 12663) | CONFIRMED | PR body + own fetch; recompute +9.46 +- 4.06. Note: "stopped early" means a normal SPRT pass at small n (LLR 2.93 > 2.89), not an abort; the card's caution (likely high) stands
T04E-01 | book UHO_Lichess_4852_v1, Threads=1, draw adj. move 30 / 6 x 10 cp, both tests | CONFIRMED | page text fields of 12650 and 12663 (win adjudication value: see addendum)
T04E-01 | context PR #735 (2026-02-27) 10k direct-check bonus, STC +3.13 / LTC +5.09 | CONFIRMED | gh api pulls/735: merged 2026-02-27, +3.13 +- 2.15 n=27,178; +5.09 +- 2.84 n=13,042
T04E-02 | Reckless PR #671, merged 2026-01-14, commit 845f49d3f1, branch nmp-tt-capture-condition, credits the Seer engine | CONFIRMED / CORRECTED | git commit title "Guard NMP on valuable piece TT captures (#671)", message "Original idea from the Seer chess engine"; the PR title itself is "nmp-tt-capture-condition" (card now says so)
T04E-02 | STC +3.43 +- 2.31 n=22,374 LLR 2.92, W/L/D 5,700/5,479/11,195 (10664); LTC +3.67 +- 2.27 n=20,816 LLR 3.17, W/L/D 5,169/4,949/10,698 (10665); Hash 16 / 64; book UHO_Lichess_4852_v1 | CONFIRMED | PR body + own fetches; recompute +3.43 +- 2.31 and +3.67 +- 2.27
T04E-02 | Viridithas PR #412 merged 2026-02-01, head nmp-tt-capture-condition, LTC 40+0.4 1 thread 128 MB +1.88 +- 1.48 n=49,814 LLR +2.95 [0,3], W/D/L 11,868/26,348/11,598, book UHO Lichess 4852 v1, no STC | CONFIRMED | gh api pulls/412 + own fetch of viri.dev/test/510/; recompute from penta [38,5840,13412,5588,29] = +1.88 +- 1.48; "likely a port" is the card's own reading of the shared branch name (reasonable, unprovable)
T04E-03 | Reckless PR #1038 "Apply decay to quiet move malus", merged 2026-05-22, commit 5e669a65b4, branch scaled-malus | CONFIRMED | gh api + git commit (message = title + bench, no mechanism text)
T04E-03 | STC +4.67 +- 2.78 n=15,778 LLR 2.98 (14855); LTC +5.18 +- 2.88 n=12,682 LLR 2.96 (14857); Hash 16 / 64; book UHO_Lichess_4852_v1 | CONFIRMED | PR body + own fetches; recompute +4.67 +- 2.78 and +5.18 +- 2.88
T04E-03 | Stockfish STC 10+0.1 +3.78 +- 2.09 n=28,096 [0,2], LTC 60+0.6 +2.18 +- 1.35 n=58,086 [0.5,2.5] (T04D-03); Patricia LTC 60+0.6 +2.39 +- 1.78 n=35,124 [0,3] (T04G-03) | UNVERIFIABLE here (second-hand) | matches notes/T04D/TABLE.md row 5 and notes/T04G/TABLE.md row 3 word for word; the sources themselves are those tracks' verifiers' job
T04E-03 | "Berserk PR 577 (T04C-04, numbers not yet filled)" | CORRECTED | notes/T04C/TABLE.md row B3 now holds STC 10+0.1 [0,2] +2.26 +- 1.55 n=52,326 LLR 2.89 passed, LTC 60+0.6 [0,2.5] +2.04 +- 1.53 n=47,970 passed (second-hand, not re-opened); card amended
T04E-04 | Reckless PR #1113 "Adjust qsearch SEE margin using quiet/noisy history", merged 2026-07-30, commit d6603046e7, branch see-history | CONFIRMED | gh api + git commit
T04E-04 | STC +4.53 +- 2.72 n=16,626 LLR 3.01 (15573); LTC +3.61 +- 2.32 n=20,184 LLR 3.00 (15575); Hash 16 / 64; book UHO_Lichess_4852_v1 | CONFIRMED | PR body + own fetches; recompute +4.53 +- 2.72 and +3.61 +- 2.32

## (2) Reading rule and constants
all | no source file or diff of Reckless / Viridithas read | NO EVIDENCE OF VIOLATION (a negative cannot be proven) | worker scratch F:/odr/work/T04E/ holds only commit-API listings, PR-body parses and test-log HTML; no code paraphrase in any card; every proposed value is an own start (T04E-01 bits / lmr_depth 6 range 3-12; T04E-02 type 4 range 2-5, 300 cp range 100-900; T04E-03 100 % / 8 % / 40 %; T04E-04 divisor 64, clamp 100) - no Reckless constant exists in the texts read
T04E-03 | "an MIT engine's form ... starts above the bonus and shrinks with the index" | CONFIRMED allowed | Patricia is MIT (T04G TABLE row 3); description in own words, no constant copied

## (3) Licence rows
both | Reckless aec5cb2e80 AGPL-3.0; Viridithas 7489e701bb AGPL-3.0 | CONFIRMED | tools/licence_at.py --row re-run 00:37, rows identical to notes/T04E/licences.md
both | licence at the cited commits (not only HEAD) | see addendum below

## (4) Forge-has-it
T04E-01 | forge_has 'skip_quiets = true|lmp_threshold\(' -> :149, :1062, :1067; picker drops killers / counter / quiet stage when skip_quiets (:368-394); direct_check :474-477, check squares :462-472, +12000 :532; quiet futility :1064-1068 guarded by !gives_check and sets skip_quiets; lmp_threshold = LmpBase + d^2, halved when not improving (:149-150) | CONFIRMED | lines read in src_al1s198_clean/src/search.cpp (LmpBase value: see addendum)
T04E-02 | 'tt_capture' -> :918 (defined), :1142 (LMR only); NMP condition :965-968 has depth, eval, static-eval margin, null_move_allowed, previous move, non-pawn material, TT upper-bound guard, no hash-move term; null_tries_ :969; SeePieceValue eval.hpp:32 | CONFIRMED | lines read
T04E-03 | '\-bonus' -> :747-748 (main + continuation malus to every tried quiet), :764 captures; quiets_tried in search order :1186 | CONFIRMED | lines read
T04E-04 | 'QsSeeMargin' -> :838 see_ge(move, -QsSeeMargin), QsSeeMargin = 40 (:42); qsearch futility skips checks :834; main-search quiet SEE :1071, noisy SEE :1081-1083 without history | CONFIRMED | lines read
T04E-04 | packf2 CaptSeeDiv = picker good-capture SEE floor, relax-only (src_packf2_h256/src/search.cpp:65, :486-494) | CONFIRMED | :65 declaration; comment :486-491, good_capture_floor :492-495 (cited range off by one line, harmless)
all | gate numbers quoted from TRIED_GATES.md: 67 HistMalusPct=125 -7.41; 47/48 CaptSeeDiv +3.24 / -3.94; 65 CheckOrderSee; 60 LmpOffKP +0.23 | CONFIRMED | notes/TRIED_GATES.md lines 76, 58-59, 74, 70

## (5) Duplicates
T04E-01 | vs T04C-05 (history term in the LMP switch, same :1062) | NOT A DUPLICATE | different rule; both cards say gate each alone; no LMP-checks gate in TRIED_GATES (LmpOffKP, CheckExtDepthCap, CheckOrderSee are other rules); R15 C1-C6 unrelated
T04E-02 | vs T04-03 (NMP margin discount by cutoff count) | NOT A DUPLICATE | different signal; no nmp / null gate in TRIED_GATES; packb ReSearchAdjust / FiftyDamp, packa NonPawnCorr / PawnHist, E3 eval options unrelated
T04E-03 | vs T04C-04, T04D-03, T04G-03 | CANONICAL (the three are MERGED stubs pointing here) | T04C row B3, T04D row 5 / 50, T04G row 3 all say "evidence for T04E-03"; gate 67 was a uniform malus, a different direction
T04E-04 | vs T04B-01 (main-search noisy SEE + capture history), T04G-02 (split capture history), CaptSeeDiv, QsEvasionSeeNonPv (gate P27R) | NOT A DUPLICATE | different site (:838 vs :1081-1083); both cards cross-reference; QsEvasionSeeNonPv is the in-check evasion branch

## (6) Form
folder | 4 cards (2 full, 2 one-line), 57 / 54 / 1 / 1 lines, crew hours in all four, UNPROVEN in all four, no vendor names (lint), card_lint 0 findings 0 PENDING | CONFIRMED | python -I -B tools/card_lint.py cards/T04E/*.md at 00:37 and again after the edits
notes | sources.md rows 4 / 5 and TABLE.md NMP row carry the corrected ids; TABLE.md malus row still says "Berserk ... numbers not yet filled" | CORRECTED in the card and in TABLE.md | -

## Addendum (filled at the end of the pass)
T04E-01, T04E-03 | win adjudication "3 x 400 cp" | CONFIRMED | pages 12650, 12663, 14855: Win ADJ movecount=3 score=400 (own fetch)
T04E-01 | LmpBase 4 | CONFIRMED | src/search.cpp:31 int LmpBase = 4 (tunable range 0-20, :78)
T04E-01, T04E-03, T04E-04 | AGPL-3.0 at the cited merge commits 5e5443d798 (2026-03-25), 5e669a65b4 (2026-05-22), d6603046e7 (2026-07-30) | CONFIRMED | tools/licence_at.py --row; rows appended to notes/T04E/licences.md
T04E-02 | "Both AGPL-3.0" at the cited commits | CORRECTED | licence_at.py: Reckless 845f49d3f1 (2026-01-14) has NO LICENSE file (no licence = all rights reserved, same ideas-only rule); Viridithas 591aa39bd4 (2026-02-01) carries an MIT LICENSE (AGPL-3.0 only at HEAD 7489e701bb). Card Licence section amended; no violation (the stricter rule was applied, nothing copied); rows appended to licences.md
T04E-02 | PR #671 title | CORRECTED | the PR title is the branch name "nmp-tt-capture-condition"; "Guard NMP on valuable piece TT captures" is the squash-commit title; card Source line amended
all | card_lint after the edits | CONFIRMED | 0 findings, 0 PENDING in all four cards; lines 57 / 58 / 1 / 1 (T04E-02 grew by four correction lines, still under 60)
all | second-hand items not re-opened by this pass | UNVERIFIABLE | Stockfish a016abd698 and Patricia PR 172 numbers (T04D / T04G tables), Berserk 7451fd7fde numbers (T04C table B3), the Seer engine commit credited by Reckless (not read by the worker either), the "likely a port" reading of Viridithas #412, and the negative "no source / no diff read" (only no evidence against it)

## Summary
Checked 40 claims across the 4 cards: 33 CONFIRMED (every logged Elo +- error, n, LLR, bounds, book, hash, TC, branch name, merge date and W/L/D of the 9 tests reproduces from the PR bodies and from fresh fetches of the test pages; all 9 Elo +- values recomputed from the pentanomials to 0.01; all 16 cited lock lines and the packf2 lines read as described; both HEAD licence rows and the 3 AGPL cited-commit rows reproduce; gate numbers from TRIED_GATES.md reproduce), 4 CORRECTED (T04E-03 Berserk numbers now filled from T04C row B3, also in TABLE.md; T04E-02 PR title vs commit title; T04E-02 licence at the cited commits: Reckless no-licence at 845f49d3f1, Viridithas MIT at 591aa39bd4), 3 UNVERIFIABLE (second-hand sibling numbers, the port reading, the negative reading claim). 0 VIOLATIONS, 0 DUPLICATES (T04E-03 is the canonical malus card the three MERGED stubs point to; T04E-04 / T04B-01 and T04E-01 / T04C-05 are different sites and cross-reference each other). Lint clean. No card deleted; nothing written outside cards/T04E/, notes/T04E/ and F:/odr/work/T04E-verify/.
