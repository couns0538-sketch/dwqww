# T02C VERIFY (adversarial check of the |eval|-cap sub-track; verifier start 06:57, board slot S2)

Scope: cards/T02C/ is empty (the worker's answer is NOT FOUND, no card), so the check is of the three notes
(TABLE.md, sources.md, licences.md): every cited number re-opened, the reading rule, tuned constants, licence rows,
the lock grep, duplicates, names, lint. Verdict: **the NOT FOUND answer stands; every number checked matches; no
licence or number violation, no duplicate; one cap violation: the stop-after-2-sources rule (WORKER_RULES line 34)
was passed early, 12 sources / 0 cards, self-reported in sources.md with the reason (covering the brief's named
sources) - logged for the coordinator, it blocks nothing.** Wrap-up note checked at 06:57 and 07:00: absent.

## Sources re-opened (numbers recomputed from W/L/D; Elo = -400 log10(1/score - 1))
| TABLE row | source | re-read via | worker's number | recomputed / found | state |
|---|---|---|---|---|---|
| 1 | Ethereal 962c75e40b (2021-07-18) | gh api commit message (not in the commit cache: `--show` says "not in the cached range", sources.md line "mine_commits --show" is inexact) | +57.45 +- 1.78, 40,000 games, regression vs 13.00; 1000cp window + sigmoid change in the same net | W 9019 L 2465 D 28516 -> +57.45; "filtering out those with evals outside a 1000cp window", "sigmoid coefficient was changed" | CONFIRMED (confounded, cumulative) |
| 2 | Ethereal 33f276e54e (2020-04-29) | gh api commit message | STC +3.31 +- 2.57, 26,112 games; LTC +4.82 +- 3.05, 13,120 games; |eval| >= 400 pruned, several changes | STC 12+0.12 [0,4] W 4981 L 4732 D 16399 -> +3.31; LTC 60+0.6 [0,4] W 1826 L 1644 D 9650 -> +4.82; "Prune all positions with abs(eval) >= 400cp" is item 2 of a multi-item list | CONFIRMED (confounded, HCE tuning set) |
| 6 | Stockfish f09adaa4a4 / PR 4919 | commit cache `--show` + gh api message (commit text only) | STC 21,920 games ~+4.7; LTC 147,606 ~+1.3; >= 16 pieces keep simple eval > 750, < 16 drop > 3000, 3-piece rows removed, local 25k nodes | STC <0,2> W 5680 L 5381 D 10859 -> +4.74; LTC <0.5,2.5> W 36619 L 36063 D 74924 -> +1.31; rule lines match; author date is 2023-12-13, 2024-01-07 is the commit date (licence row uses the commit date; no change) | CONFIRMED (small second net, confounded) |
| 10 | Alexandria c77904fa86 / PR 599 | commit cache `--show` | STC +5.08 +- 2.95, 14,488, penta [42,1674,3621,1844,63]; LTC +2.28 +- 1.72, 37,568, penta [19,4272,9962,4506,25] | penta -> score 0.50732 -> +5.08 (8+0.08 [0,3], LLR 2.97); 0.50327 -> +2.28 (40+0.4 [0,3], LLR 2.95) | CONFIRMED (out of scope, flagged for the coordinator) |
| 5 | Lynx ee39ad14c7 | gh api commit metadata | 2026-09-25, mismatch filter, +26 / +3 / +5 lines in three files, no Elo | date 2026-09-25, title "Add Viriformat filter support for eval-game result mismatch", ViriformatFilter.cs +26, filter.json +3, Utils.cs +5; no test numbers in the commit | CONFIRMED (MIT: diff read is allowed) |
| 4 | bullet da426a49b2 examples/advanced/filter.rs | gh api file (MIT) | fields max_eval and max_eval_incorrectness next to min ply / pieces / tactical / WDL skips and a piece-count curve; example values not carried over | fields present (max_eval, max_eval_incorrectness, min_ply, min_pieces, filter_tactical, wdl_filtered, wdl model params, piece_count_acceptance); no Elo | CONFIRMED |
| 3, 7, 8, 9 | SF d53071eff4 / b939c80513 (pointer to T02B row 2), Viridithas networkhistory, 55-list commit sweep, 1 web search | not re-run (negative results; the T02B pointer is a cross-reference, not a new claim) | NOT FOUND | - | UNVERIFIABLE here within the 10-minute budget (negative findings; nothing to recompute) |

## Own data (independent awk over the first 1,000,000 rows of shard 020, read-only)
Recount: |cp| > 1000 8.245 %, > 1500 2.931 %, > 2000 0.850 %, > 3000 none; >= 16 pieces 53.6 % of rows (0.61 % of them
above 1500), < 16 pieces 46.4 % (5.61 % above 1500), share of the > 1500 rows with < 16 pieces 88.9 %; eval >= 300
against a decisive result 0.103 %, drawn game with |cp| >= 300 1.278 %. All equal to TABLE / sources.md (8.25 / 2.93 /
0.85 %, ~89 %, 1.38 % = 0.103 + 1.278). CONFIRMED.

## Rules
- Reading rule: GPL / AGPL sources (Ethereal, Stockfish, Alexandria, Clockwork, Viridithas) = commit messages, PR text,
  docs only; Stockfish and nnue-pytorch source never opened; MIT (bullet, Lynx, Reckless) source / diff allowed;
  viriformat (no licence) README only. No violation found.
- Tuned constants: the Forge proposal in the TABLE closing paragraph is an own start (2000 = Forge's own
  win-adjudication line) and an own range (1000-2500, justified by Forge's own row shares); the other engines' values
  (1000 cp window, 400, 750 / 3000 / 16 pieces, 10000 / 2500 example) appear only as the sources' own settings. OK.
- Licence rows: all 10 rows re-run with tools/licence_at.py --row; identical to notes/T02C/licences.md.
- Forge has it: `bash tools/forge_has.sh 'max.?score|eval.?limit|datagen|selfplay'` = 1 hit, src/search.cpp:1385
  (aspiration window), as stated. tools/tried_gates.py --grep 'cap|eval.?lim|max.?score|filter|skip|datagen' = only
  search-option / net gates, no data-filter gate. CONFIRMED.
- Duplicates: no card in cards/T02C/, so none possible; the "evidence for T02-03" pointer is right
  (cards/T02/T02-03-wdl-consistency-skip.md exists and is the WDL-consistency skip).
- Names: tools/novendor_filter.py over notes/T02C/*.md leaves the text unchanged; grep for vendor / model-company
  names: 0 hits.
- Lint: no card file, so card_lint has no input (a literal unmatched glob makes it trap on a missing file; not a card
  finding). Nothing to lint.
- Caps: 12 numbered sources + 1 web search (<= 15), 2 engines deep-read (bullet, Lynx), 0 forum threads. One
  acknowledged deviation: the "stop after 2 sources in a row without a card" rule was passed early (sources 1-12 all
  gave no card); sources.md says so and gives the reason (covering the brief's named sources). Logged, not a licence
  or number violation.

## Corrections made to the notes
None needed (no number differed). Two record notes, no edit: (a) Ethereal commits were re-read through gh api, the
commit cache does not hold them; (b) SF f09adaa4a4 author date 2023-12-13 vs commit date 2024-01-07.

## Left open
- The sign convention of Lynx's logistic (worker's PENDING) was not checked here either; it does not change the
  NOT FOUND answer.
- Integral (no licence, not cached): still unchecked, as the worker says.
- GPU wall time of the proposed one-change cap ablation: PENDING with the crew (worker's own statement).
