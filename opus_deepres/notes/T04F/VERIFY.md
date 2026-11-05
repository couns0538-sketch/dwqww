# T04F verify (adversarial pass, 2026-11-05 00:46-00:59 PC clock)

Scope: cards/T04F/*.md (3 cards) and notes/T04F/{DIFF,TABLE,sources,licences}.md. Method: every cited commit
message re-fetched with gh api (Caissa MIT: diffs of the three carded commits also read; Stockfish / Stormphrax:
commit message and PR text only, never source), the six fishtest run records in F:/odr/work/T04F/fishtest/ re-read
with the worker's runargs.py, Elo recomputed from W/L/D, licence rows re-run with tools/licence_at.py --row, every
forge_has.sh grep re-run, every cited lock line re-read in src_al1s198_clean, duplicates checked against
`ls cards/*/`, notes/TRIED_GATES.md (tools/tried_gates.py --grep), D:/o15/cands/INDEX.md (R15 C1-C6, x1 / x2b) and
the P27R source (own code). Scratch: F:/odr/work/T04F-verify/ (nothing kept there).

Verdicts: CONFIRMED / CORRECTED / UNVERIFIABLE / VIOLATION / DUPLICATE.

## Cards

| card | claim | verdict | evidence |
|---|---|---|---|
| T04F-01 | a677c89 "QSearch: Aggressive check evasion pruning", W 5052 L 4810 D 15669, n=25,531, +3.3 +- 2.6, llr 2.95 (-2.94 / 2.94), H1 | CONFIRMED | commit message (gh api); Elo from W/L/D = +3.29; committer date 2023-08-23 (author 2023-08-20) |
| T04F-01 | a677c89: "1 thread" | CORRECTED | the cutechess block states no thread count, TC or book; card now says "threads not stated" |
| T04F-01 | a677c89 mechanism = break after the first evasion whatever its score | CONFIRMED | diff (MIT): `if (node->isInCheck) break;` placed after `bestValue = score;` inside the new-best block, no mate guard; bestValue starts at -Inf in check since c8a30a7. The commit also moved the futility / SEE / underpromotion block out of the `!isInCheck` guard, but in check that block is unreachable (the break fires first; the diff asserts `!isInCheck` inside it). So the +3.3 belongs to the unguarded stop; the card's mated-score guard is the card's own variant (card already says so) |
| T04F-01 | c8a30a7 "QSearch tweaks": stop at the first quiet evasion + futility retune, +5.9 +- 4.8, n=8,606, llr 3.18 (-3.18 / 3.18) | CONFIRMED | message + diff: `if (move.IsQuiet()) break;` under `bestValue > -TablebaseWinValue`, QSearchFutilityPruningOffset 142 -> 90, bestValue init -> -Inf, prefetch moved; Elo from W/L/D = +5.85 |
| T04F-01 | HEAD form Search.cpp:1421 @57cae7ef71 | CONFIRMED | local copy F:/odr/work/T04F/caissa_57cae7ef71/Search.cpp:1421 `if (node->isInCheck) break;`, bestValue = -InfValue at :1247 |
| T04F-01 | Stockfish 392b529 (PR 3221): STC 10+0.1 noob_3moves [-0.25,1.25] LLR 2.97 N=22,632 W 2,433 L 2,264 D 17,935 ~+2.6; LTC 60+0.6 [0.25,1.25] LLR 2.94 N=105,432 ~+1.0; Threads 1 | CONFIRMED | commit message + fishtest records 5fa59405 / 5fa5b609 (tc, threads 1, book noob_3moves.epd, logistic bounds); Elo +2.59 / +1.04 |
| T04F-01 | Stormphrax PR 203: 8+0.08 +3.91 +- 2.57 n=20,596 [0,3]; 40+0.4 +3.36 +- 2.27 n=22,018 | CONFIRMED (numbers) | PR text: W 5115 L 4883 D 10598 -> +3.91; W 5108 L 4895 D 12015 -> +3.36; Threads=1, Hash 32 / 128 MB, LLR bounds (-2.25, 2.89) |
| T04F-01 | Stormphrax PR 203 "is the guard the lock already has" | UNVERIFIABLE | the PR body is title + result blocks only; the mechanism is a reading of the title (GPL-3.0: source may not be read). The card uses it as "guard only", not as a number for the cut: acceptable as labelled |
| T04F-01 | lock: all evasions searched s:801-805, pruning only under `!in_check && best_score > -MateInMaxPly` s:831-839, mated only with no legal move s:865; forge_has 'generate_evasions' -> s:414, s:538 | CONFIRMED | lines re-read; grep re-run (2 hits) |
| T04F-01 | P27R QsEvasionSeeNonPv is another rule; R15 C2 QsMovePrune acts only out of check | CONFIRMED | P27R src (own code, qa_stage_sf26p27r_20261030/src_p27r/src/search.cpp:838-840): in check, non-PV, after >= 1 evasion, skip evasions failing SEE; gate P27R-AL1 +4.63 n=3,000 cap. C2 patch: new test inside `if (!in_check && best_score > -MateInMaxPly)`. Neither is a count-based stop: no duplicate |
| T04F-01 | no other engine's constant as a Forge value | CONFIRMED | option QsEvasionLimit 0-4, gate value 1 = the mechanism itself (one evasion), second line 2 own |
| T04F-02 | Caissa 2fd8f56: TC 6+0.06, W 1914 L 1770 D 4061, n=7,745, +6.5 +- 5.3, llr 2.95, bundle (capture bit + table merge + null-move pointers) | CONFIRMED | message (TC=6+0.06 stated); Elo from W/L/D = +6.46; diff (MIT): `continuationHistory[prevIsCapture][color][prevColor][prevPiece][prevTo]`, counterMoveHistory removed, `isNullMove` break removed |
| T04F-02 | 2fd8f56: "1 thread" | CORRECTED | not stated in the message; card now says "threads not stated" |
| T04F-02 | HEAD MoveOrderer.hpp:75, MoveOrderer.cpp:158-176 | CONFIRMED | local copy: hpp:75 `continuationHistory[2][2][2][6][64] // prev is capture, ...`; cpp:158-177 InitContinuationHistoryPointers |
| T04F-02 | Stockfish 2e96c51 (PR 2344): STC 10+0.1 [0.5,4.5] LLR 2.95 N=79,702 W 17,720 L 17,164 D 44,818 ~+2.4; LTC 60+0.6 [0,3.5] LLR 2.96 N=29,147 W 4,907 L 4,651 D 19,589 ~+3.1; Threads 1, 2moves_v1 | CONFIRMED | message + fishtest 5d97945e / 5d97ccb9 (BayesElo bounds, book 2moves_v1.pgn, threads 1); Elo +2.42 / +3.05 |
| T04F-02 | Stockfish 472de89 (PR 2362): STC [0,4] N=61,908 ~+2.3; LTC [0,4] N=49,057 ~+2.2 | CONFIRMED | message + fishtest 5da8aa67 / 5da8e99d (10+0.1 / 60+0.6, threads 1, 2moves_v1); Elo +2.28 / +2.17 |
| T04F-02 | lock: pointer `(*continuation_history_)[moved piece][to]` at s:842, :974, :1011, :1121, :1355; type h:253-254; read plies 1-2 s:704-712; written 1, 2, 4 s:720-727; clear s:579; table 1.38 -> 2.77 MB | CONFIRMED | grep re-run (5 hits); lines re-read; 13 x 64 x 13 x 64 x 2 B = 1,384,448 B, x2 = 2,768,896 B |
| T04F-02 | "Not in TRIED_GATES ... nor in R15 / FB2 options" | DUPLICATE | D:/o15/cands/INDEX.md section c5_conthistsplit: R15 C5 `ContHistSplit` = "follow-up (continuation) history split by evasion / capture of the indexing move", exe forge_ltopgo_c5chs.exe (pc1 = pc2 PASS, pins PASS, smoke PASS), patch c5_conthistsplit.patch: `continuation_for(in_check, capture, piece, to)` picks one of 3 extra tables (capture / evasion / both) at the same three pointer sites the card names. Not yet gated (tools/tried_gates.py --grep ContHist: only ContHist4Pct gates 31-33 / 68). The card's capture-only option is C5's capture half; its Caissa + Stockfish STC / LTC numbers are evidence for that prepared line. Status line marked; Forge fit corrected |
| T04F-03 | Caissa 47fc56a: 8+0.08, W 1886 L 1743 D 4075, n=7,704, +6.4 +- 5.3, llr 2.95, bundle of 3 items incl. "cycle detection only in non-PV nodes" | CONFIRMED | message lists the three bullets and TC=8+0.08; Elo from W/L/D = +6.45 |
| T04F-03 | 47fc56a: "1 thread" | CORRECTED | not stated; one-liner now says "threads not stated" |
| T04F-03 | HEAD Search.cpp:1114-1158: twofold = draw only in non-PV and only when the earlier node is not the root (ply > 0); otherwise threefold | CONFIRMED | local copy :1114-1158 (`if (!isPvNode && prevNode->ply > 0) return true; if (repCount++ >= 1) return true;`) |
| T04F-03 | lock: any in-tree match incl. the root = draw in every node type, board.cpp:903-916 (`i >= root_index`), via is_draw s:700 in search and qsearch; forge_has 'cuckoo\|upcoming\|game_cycle' = 0 | CONFIRMED | board.cpp:903-917 re-read; is_draw called at s:780 (qsearch) and s:893 (search); grep re-run (0 hits) |
| T04F-03 | duplicates | CONFIRMED none | no other card, gate option or R15 candidate touches repetition (grep twofold / threefold / repetition over cards/*/: only T04F-03 and T12-03's checklist; TRIED_GATES: none; INDEX.md: none) |
| all three | prior crew code named in the task: packb (ReSearchAdjust / FiftyDamp, gates 12 / 35 / 40 / 41), packa (NonPawnCorr / PawnHist / NonPawnCorrWeight, gates 14 / 34 / 38 / 39 / 43), E3 (EvalMatScale / EvalOptimism / EvalRule50Damp, gates UE3A-C) | CONFIRMED no duplicate | FORGE_RESULTS.md / TRIED_GATES.md option strings: LMR re-search adjust, rule-50 damping, correction keys, pawn history and eval post-processing; none touches qsearch evasions, the continuation-history key or in-tree repetition |

## Notes (DIFF.md / TABLE.md spot checks)

| row | claim | verdict | evidence |
|---|---|---|---|
| TABLE 16 / DIFF 94 | 8bd0321 "+5.0 +- 4.6 n=9,299 H1"; HEAD keeps `!isRootNode` at S:1929 | CONFIRMED | message (2023-10-18, llr 2.97); local copy S:1929 |
| TABLE 8 / DIFF 97 | 222642f +3.6 +- 3.5 n=17,336 H1; d940dec 10+0.1 +2.05 +- 2.29 n=24,206 | CONFIRMED | messages (222642f llr 3.19 at -3.18 / 3.18; d940dec [-2.5,0.5] non-regression, Threads=1 Hash=16MB) |
| TABLE 43 / 47 | Stormphrax PR 304 +2.17 +- 1.72 n=47,966 / +2.69 +- 1.93 n=29,202; PR 203 numbers | CONFIRMED | PR text; Elo from W/L/D +2.17 / +2.69, +3.91 / +3.36 |
| TABLE header | "1 thread unless noted" for the 2022-2023 cutechess blocks | UNVERIFIABLE | the blocks state no thread count; treat every Caissa cutechess number as threads-not-stated (cards corrected) |
| DIFF C / D, TABLE 44-48 | HAS rows 44-46, 48 and the remaining ~40 table rows | not re-checked (20-minute cap); the three carded rows and three sampled rows all reproduce |

## Rules

| check | verdict | evidence |
|---|---|---|
| reading rule | CONFIRMED | sources.md: Caissa (MIT) source + diffs; Stockfish: commit messages + fishtest API records; Stormphrax: PR text; no GPL / AGPL source named anywhere; this pass read the same classes only |
| licences | CONFIRMED | tools/licence_at.py --row re-run: Caissa MIT at 57cae7ef71, a677c890f9, c8a30a7d11, 2fd8f56e40, 47fc56acc5; Stormphrax GPL-3.0 at d1468d99e3 and at the PR 203 head 3219c3021b; Stockfish GPL-3.0 at 392b529c3f, 2e96c513ad, 472de897cb (rows appended to licences.md) |
| names | CONFIRMED | no vendor / model-company name in cards or notes (branch and path names of this project only) |
| no Forge Elo claim | CONFIRMED | every Forge estimate carries UNPROVEN |
| caps | CONFIRMED | 3 cards (<= 4), 2 full + 1 one-liner, 54 / 60 / 1 lines after the verify edits (<= 60; T04F-02 was 56, the Status mark added 3 lines and one correction line, trimmed to 60); crew hours in all three; <= 15 external sources; 1 engine deep-read |
| card_lint | CONFIRMED | 0 findings, 0 PENDING before and after the verify edits |

## Summary
Checked 3 cards (23 card-level claims) + 4 note rows + 6 rule checks. Corrected: "1 thread" on the three Caissa
cutechess results (not stated); T04F-02 Forge fit (R15 C5 ContHistSplit exists). Duplicate: T04F-02 of the prepared,
ungated R15 C5 ContHistSplit (capture half); kept as evidence for that line. Unverifiable: Stormphrax PR 203
mechanism (title only); Caissa thread counts. Violations: none. Every number in the three cards reproduces from
its source.
