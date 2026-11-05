# T02C sources (one line per source read: url or repo@sha | licence tier | what it gave | card id or "no card")

- worker start 06:42 (date); stop researching at 07:07 (start + 25 min, earlier than 07:30). Inputs read first (own
  records, no licence): WORKER_RULES.md (incl. Round 2), cards/TEMPLATE.md, notes/T02/TABLE.md, notes/T02/MIX.md,
  notes/T02B/TABLE.md + sources.md + licences.md, notes/T02/licences.md, notes/CRITIC.md lines 166-198 (T2 |eval| caps
  NOT COVERED, line 171), notes/CRITIC2.md (grep), tools/tried_gates.py --grep 'cap|eval.?lim|max.?score|filter|skip|
  data|datagen' (no data-filter gate among the hits). T02B TABLE row 2 already holds one web search with NOT FOUND.
- 1. commit-message grep over all 55 cached commit lists in F:/odr/cache/commits (own helper
  F:/odr/work/T02C/grep_all.py; regex of eval-limit / max-eval / eval-cap / |eval| / eval-window / eval-incorrectness
  words; hits in F:/odr/work/T02C/hits.txt, 66 lines, 30 commits; Stormphrax, PlentyChess, Alexandria, Clockwork,
  Obsidian, berserk: 0 hits; Integral is not cached) | commit messages only (GPL / AGPL / MIT / none: titles and
  messages are allowed for every tier) | 6 data-related hits: Ethereal 962c75e40b + 33f276e54e, Stockfish f09adaa4a4 +
  584d9efedc, Reckless 2e66182cd3, Lynx ee39ad14c7; the rest are search / eval code | no card
- 2. AndyGrant/Ethereal 962c75e40b (2021-07-18, "Update best network [A040B729]", mine_commits --show) | GPL-3.0,
  commit message only | net trained on 1.9B positions from the previous best net, "filtering out those with evals
  outside a 1000cp window", sigmoid coefficient changed in the same net; the only Elo is a regression test vs the
  13.00 release: +57.45 +- 1.78, 60+0.6 Threads=1, 40,000 games (chess.grantnet.us/test/12863) = cumulative, not the
  cap | TABLE row (confounded, no isolated number); no card
- 3. official-stockfish/Stockfish f09adaa4a4 (2024-01-07, PR 4919, smallnet "wider eval range", cache message lines
  1-105) | GPL-3.0, commit message only | small second net (L1-128) data: drop 3-piece rows; >= 16 pieces keep rows
  with simple eval ABOVE 750; < 16 pieces drop rows with simple eval above 3000 (a piece-count-dependent cap, but on
  material eval and for the small net only), together with a wider use range of the small net and the WDL skip off:
  STC 10+0.1 [0,2] passed, 21,920 games (W 5680 L 5381, ~+4.7); LTC 60+0.6 [0.5,2.5] passed, 147,606 games (W 36619
  L 36063, ~+1.3); local 25k nodes, that small net alone vs an L1-128 on standard data: -241.7 +- 3.2 = confounded,
  and "small second net" was already reported on 30-Oct | TABLE row (dead end for a single main net); no card
- 4. cosmobobak/viridithas@7489e701bb notes/networkhistory.txt (docs; T02B's saved copy
  F:/odr/work/T02B/viri_networkhistory_7489e701bb.txt read-only, two greps: eval-cap / filter words) | AGPL-3.0, ideas
  only (docs) | no eval-cap or eval-window experiment in 1,851 lines; only "viri11 filtering of noisy positions, more
  data, ~20 Elo" (line 19, no TC / games, confounded, "noisy" = tactical) and the 400 cp opening filter ("modern",
  T02B row 10) | no card
- 5. jw1912/bullet@da426a49b2 docs/3-data.md (33 lines) + examples/advanced/filter.rs (77 lines) | MIT, copy with
  notice (nothing copied) | the binpack loaders take a row filter; the advanced example keeps a row only if a
  viriformat Filter passes it - fields include a plain |eval| cap (max_eval) AND a cap on how far the eval disagrees
  with the game result (max_eval_incorrectness), next to min ply / min pieces / tactical / check / castling skips,
  random skipping, an optional WDL-model skip and a piece-count acceptance curve. NO Elo, TC or games anywhere; the
  example's numbers are example values (not carried over) | mechanism for TABLE rows; no card yet
- 6. lynx-chess/Lynx ee39ad14c7 (2026-09-25, "Add Viriformat filter support for eval-game result mismatch"; no PR
  attached; diff of src/Lynx/Datagen/ViriformatFilter.cs +26, filter.json +3, Utils.cs +5 read via gh api) | MIT at
  that commit, copy with notice (nothing copied) | mechanism of a cap by WDL skew: turn the row's eval into an expected
  score with a logistic and a divisor, take its distance to the game result (1 / 0.5 / 0), divide by the largest
  distance possible for that result, drop the row when the share is above a threshold; OFF by default (and the default
  threshold of 100 % drops nothing); the helper's sign convention was not checked. NO Elo, test or net built with it in
  the commit | TABLE row; no card
- 7. lynx-chess/Lynx commit messages (cache, grep of filter words: 7 titles f992ce1be4, ad16886de0, 193cd5b3e3,
  a84aba731c, e5929fa703 ...) | MIT, messages only | filter features (min game ply, positions per phase per game,
  win / draw adjudication in the EPD tool) with NO Elo, TC or games | no card
- 8. AndyGrant/Ethereal 33f276e54e (2020-04-29, "Tune entire evaluation using updated book and method", mine_commits
  --show) | GPL-3.0, commit message only | hand-crafted-eval tuning set: positions with |eval| >= 400 cp pruned,
  together with 3 other book changes (relabel at depth 12, dedup, ~430k new labels) and 3 tuner changes: STC 12+0.12
  SPRT [0,4] passed, +3.31 +- 2.57, 26,112 games; LTC 60+0.6 [0,4] passed, +4.82 +- 3.05, 13,120 games
  (chess.grantnet.us/test/5427 , /5428) = seven changes in one test, and an HCE tuning set, not net rows | TABLE row
  (confounded); no card
- 9. codedeliveryservice/Reckless 2e66182cd3 (2024-03-14, "Slightly increase score limit for data generation",
  message from cache) | MIT at that commit (AGPL-3.0 on today's default branch) | title only: NO Elo, TC or games; diff
  not opened (no number to gain) | no card
- 10. commit titles with filter / datagen words in 13 cached engines (viridithas, Stormphrax, PlentyChess, Alexandria,
  Clockwork, berserk, Obsidian, Tarnished, pawnocchio, Halogen, Sirius, Renegade, Starzix; list in
  F:/odr/work/T02C/filter_titles.txt, 101 titles) + full messages of viridithas d9cf394f19, f80ceba047, 4081935c60,
  cb68a4fa4d, 24fce57c45 and Clockwork 703fcc533c | titles / messages only (AGPL / GPL) | Viridithas "Tweak filtering",
  "edit to filtering", "juggle filtering constraints", "refactor to allow data filter configuration" and Clockwork's
  "phase distribution filtering script used for v2.1 data (#203)" carry NO Elo (bench line only / "No functional
  change"); Stormphrax, PlentyChess: no data-filter title at all | no card
- 11. PGG106/Alexandria c77904fa86 / PR 599 "New net (piececount filtering)" (2026-02-13; commit message + PR body
  via gh api) | GPL-3.0, PR text only | a new net whose only named change is piece-count filtering (not an |eval| cap;
  arch, data size and filter rule not stated): STC 8+0.08 [0,3] passed, +5.08 +- 2.95, 14,488 games, penta [42, 1674,
  3621, 1844, 63]; LTC 40+0.4 [0,3] passed, +2.28 +- 1.72, 37,568 games, penta [19, 4272, 9962, 4506, 25] | TABLE row
  (adjacent filter, out of this brief's scope; counter-weight to Caissa's -11 in T02 row 8); no card
- web search (|eval| cap question, 1 of 1, 06:48): "NNUE training data filter max_eval OR eval incorrectness OR max
  eval positions removed Elo SPRT test chess engine" | - | no measured eval-cap or eval-incorrectness test in the
  results: arXiv 2412.17948 (quiet-position dataset study, T02 read it: no Elo in the paper; a third-party review page
  claims ~+100 Elo for it - not verified, not followed: a quiet-position filter, not a cap), Stockfish PR 4465 (ply <= 28
  rows kept with a placeholder score for compression), c3ce220408 (T02B row 9), forum threads with settings only |
  TABLE row: NOT FOUND
- 12. cosmobobak/viriformat@0238b315ea README.md (75 lines, via gh api readme) | no licence (all rights reserved):
  README only, no source file | a byte-level game-record spec only; the row filters (|eval| cap, eval-incorrectness
  cap) are not described in it, so their exact rule is known only from the MIT Lynx port (source 6) | no card
- (own data, no licence) D:/grok-pc-data/selfplay_out/forge_selfplay_020.txt first 1,000,000 rows (the same sample as
  T02B; read-only awk, 6.8 s; row = FEN | side-to-move cp | White's result; output F:/odr/work/T02C/shard020_bands.txt)
  | own | |cp| bands: <= 500 78.955 %, 500-1000 12.800 %, 1000-1500 5.314 %, 1500-2000 2.081 %, 2000-2500 0.728 %,
  2500-3000 0.122 %, > 3000 none (writer cap). Eval against result (cp turned to White's view): eval >= +X in a game
  White lost or <= -X in a game White won: X=300 0.103 %, X=500 0.013 %, X=1000 0 %; drawn game with |cp| >= X: X=300
  1.278 %, X=500 0.279 %, X=1000 0.012 %, X=2000 0.001 %. By phase: >= 16 pieces = 53.6 % of rows, of them |cp| > 1000
  2.94 %, > 1500 0.61 %, > 2000 0.12 %; < 16 pieces = 46.4 %, of them > 1000 14.37 %, > 1500 5.61 %, > 2000 1.70 %
  (so ~89 % of the rows above 1500 cp have < 16 pieces) | TABLE rows (Forge shares per cap rule)
- (own record) lock grep `bash tools/forge_has.sh 'max.?score|eval.?limit|datagen|selfplay'` = 1 hit, src/search.cpp:1385
  (an aspiration-window line, not a cap): the lock has no datagen code; the cap lives in the writer | TABLE header
- research ended 06:51 (date): 12 numbered sources + 1 web search + own data; every source gave no card (the
  two-in-a-row stop rule was passed early and is acknowledged here; the sweep went on only to cover the brief's named
  sources). Answer = measured NOT FOUND (TABLE.md rows 1-9), one adjacent out-of-scope number (row 10), no card.
  Integral not checked (no licence, not cached) - PENDING. Files: notes/T02C/TABLE.md, sources.md, licences.md;
  cards/T02C/ is empty (no card, so card_lint has nothing to check).
