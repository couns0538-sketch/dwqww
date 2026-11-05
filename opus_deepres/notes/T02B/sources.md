# T02B sources (one line per source read: url or repo@sha | licence tier | what it gave | card id or "no card")

- worker start 00:06 (date); stop researching at 01:14 (start + 70 min; earlier than 07:30). Inputs read first (own
  records, no licence): WORKER_RULES.md (incl. Round 2), cards/TEMPLATE.md, cards/T02/*, notes/T02/TABLE.md, MIX.md,
  sources.md, licences.md, notes/CRITIC.md (T2 rows 60-72, 171-174), notes/TRIED_GATES.md (no datagen / data-filter
  gate in it), skill forge-selfplay-datagen (SKILL.md, 64 lines: live rules at lines 18-21).
- 1. Witek902/Caissa commit messages (cache Witek902__Caissa__2022-01-01__now, `--grep` datagen words: 136 hits;
  `--show` 3683f575e1, 1af30b96de, 57735299e6, 82e6ec67b1, 011717321c) | MIT, copy with notice (nothing copied) |
  the selfplay-tool commits ("Selfplay improvements" 2026-10-03 / 2026-04-26, "Eval randomization" 2023-07-17,
  "Selfplay: Injecting random moves" 2023-06-11) carry NO Elo, games or test link; eval-ml-8-152B (net + data,
  confounded): LTC +7.32 +- 3.54 [0,3] 9,072 games, STC +1.58 +- 1.19 [0,2] 91,412 games | no card (no logged Elo for
  a generator setting)
- 2. Witek902/Caissa@57cae7ef71 src/utils/SelfPlay.cpp (826 lines; read lines 20-45, 90-122, 262-360 + one grep) |
  MIT, copy with notice (nothing copied) | mechanisms: random opening moves drawn only from SEE-non-losing legal moves
  (Forge draws from all legal moves); opening skipped when the first search |score| exceeds a cap; eval randomisation
  flag on in every datagen search; win adjudication needs search score AND static eval past a threshold for N moves
  after a minimum ply (default threshold = infinite, i.e. off); draw adjudication |score| < threshold for N moves after
  ply 80 (default threshold 0 = off); Syzygy WDL adjudication <= 5 pieces when not in check; all game positions are
  stored (row filters live in the trainer). No Elo in the file | evidence for T02B cards (mechanism only)
- 3. cosmobobak/viridithas commit messages (cache cosmobobak__viridithas__2024-01-01__now; `--grep` datagen words: 40
  hits; `--show` 09630caf93, dc3a7de582, d0436e5d4a, 8735c38ba8, 05dcdb5b6e, 7c16e0072f, 0a42d95ca0, 1173545de4) |
  AGPL-3.0, ideas only (commit messages) | datagen commits "Add opening-eval filtering" (2025-08-02), "Relax
  over-agressive opening filtering" (2025-08-19), "Reintroduce odd-even openings in datagen" (2025-10-18), "Turn off
  evaluation scaling for datagen" (2025-12-08): NO Elo in any of them; the experiment results live in a notes file | no card
- 4. cosmobobak/viridithas@7489e701bb notes/networkhistory.txt (1,851 lines, a docs file; grep + lines 770-830,
  1222-1300, 1340-1420 read) | AGPL-3.0, ideas only (docs) | (a) "perseverance": drop data generated before
  2023-04-01 + upsample the newest engine's data 4x, 200-superbatch run vs temperance: 25k fixed nodes +7.24 +- 3.94,
  SPRT [0,3] 12,578 games (chess.swehosting.se/test/9601); LTC 40+0.4 +8.44 +- 3.90, [0,3] 7,946 games (/test/9602)
  = recency purge, MIX.md item 3; (b) "requiem": several changes incl. "less early-ply filtering" -1.29 fixed nodes /
  -10.62 STC, confounded (/test/9945); (c) "modern": removing new data AND 400 cp filtered openings -10.34 +- 4.80 STC
  8+0.08, 5,714 games (ob.expositor.dev/test/19), confounded; (d) loader shuffle: random skipping 0.75 -14.31 +- 2.64
  STC 20+0.2 (20,022 games, /test/189), skipping 5/6 + warmup +3.12 (/test/192) - loader, not datagen | evidence
  for MIX.md item 3 (recency purge); no card
- 4 (cont.). same file, lines 186-232 (gemstone and a Viridithas dataset built on it) | AGPL-3.0, docs | a Viridithas dataset = gemstone's 963M-position set
  + ~250M extra DFRC positions (~21 % of the set), same arch: classical STC 8+0.08 -5.11 +- 4.22, SPRT [0,3] failed,
  12,912 games; DFRC STC +18.36 +- 6.96 (4,488 games) vs gemstone; "grimoire" (+444M classical positions) -0.37 +-
  2.90 (27,224 games) | TABLE row (DFRC openings: drop for a classical gate); no card
- 5. official-stockfish/Stockfish commit messages from the cache official-stockfish__Stockfish__2020-08-01__2024-12-31
  (grep of datagen words; `--show` d53071eff4, 85f8ee6199; b939c80513 grep lines only; no new fetch) | GPL-3.0, commit
  messages only (no source) | d53071eff4 (PR 3521, nn-7e66505906a6, 2021-06-03): previous 64B binpack + a 2B binpack
  generated from an opening book of positions whose static eval differs strongly from a depth-9 search ("wrongNNUE"
  book), same arch HalfKAv2^, retrained (max_epochs 400, epoch-359 net; corrected by verify from "40 epochs"): STC 10+0.1 [-0.5,2.5] passed, W 6254 L 6028 D 52310 (64,592
  games, ~+1.22); LTC 60+0.6 [0.5,3.5] passed, W 1998 L 1826 D 41736 (45,560 games, ~+1.31) (tests 60b7c79a457376eb8bcaa104
  / 60b85307457376eb8bcaa182); generator settings in the same message: depth 9, multipv-2 random moves within 100 cp,
  3 random moves up to ply 8, eval_limit 32000 (= no cap). 85f8ee6199 (2022-07-04): data + DFRC data AND a modified loss:
  classical STC ~+1.19 (135,008) / LTC ~+3.11 (28,864), 25k nodes +4.2 +- 1.6, FRC STC +29.78, DFRC STC +55.25 -
  confounded. b939c80513 (RL round, 2021-07): eval_limit 1500, random multipv 12 within 100 cp, 10 random moves up to
  ply 80, write_min_ply 10 - confounded (+1.62 / +1.03) | T02B-01 (wrong-eval book), TABLE rows
- 6. https://tests.stockfishchess.org/api/get_run/60b7c79a457376eb8bcaa104 and /60b85307457376eb8bcaa182 (fishtest run
  records of d53071eff4) | GPL-3.0 project, test logs | STC 10+0.1 / LTC 60+0.6, book noob_3moves.epd, 1 thread, SPRT
  [-0.5,2.5] / [0.5,3.5] elo_model normalized, both accepted; W/L/D as in the commit | T02B-01
- (own records, no licence) D:/grok-pc-data/dwqww git show opus-r8-datagen:r8/README.md (5dd3a57d, lines 55-80) |
  own | R8 driver data options: --openings (UCI move lists from startpos), --opening-plies 8, --max-ply 300,
  --adjudicate-cp 2000, --adjudicate-plies 4, --max-score 3000, --check-nodes; lock grep: no datagen / chess960 /
  multipv code (forge_has.sh: 0 hits each) | T02B-01, TABLE.md
- 4 (cont.). same file, lines 862-872 + 1013-1040 (umwelt, broadside, spigot) | AGPL-3.0, docs | "spigot" = broadside
  minus data before 2024-05-01 + 25k-node data upsampled x4: 25k nodes -18.62 +- 6.63, SPRT [0,3] failed, 4,222 games
  (chess.swehosting.se/test/10790) vs delenda; "umwelt" from-scratch net + more 25k-node data -2.18 +- 2.79 (24,186
  games, /test/10275) - both confounded; together with "perseverance" (+7.24 / +8.44) the recency-purge evidence is
  mixed | TABLE rows (recency, nodes per move); no card
- continuation worker start 00:22 (date); stop researching at 01:02 (start + 40 min, earlier than 07:30). Read first:
  WORKER_RULES.md (incl. Round 2), cards/TEMPLATE.md, this folder (1 card, sources 1-6), notes/CRITIC.md rows 52-72 +
  171-174, notes/T02/TABLE.md, notes/T02/MIX.md, skill forge-selfplay-datagen (64 lines), tools/tried_gates.py
  --grep 'zero|skip|filter|datagen|draw|adjud|book|opening' (1 of 110 gates, a book trial; no data-filter gate).
- 7. official-stockfish/nnue-pytorch commit messages (cache 2021-11-01__now, grep of filter words) + PR 450 text
  (gh api pulls/450) + commit metadata of d87c248fbe (title "update", 12 added lines in the C++ data loader; diff NOT
  opened) + gh compare | GPL-3.0, commit titles / PR text only | "skip zero evals (#450)" = squash commit f5c9d01569
  (2026-04-15): the loader skips rows whose score is exactly 0; Forge's npt pin b26145006e (F:/nnue_pytorch
  SETUP_REPORT.md) is 106 commits ahead of f5c9d01569 and 0 behind = the pin contains it (whether it is unconditional
  is not stated in the PR text; source not read). Also "Implement simple_eval_skipping (#321)" (2025-06-28, a
  material-imbalance skip used for a small second net) and "Skip positions with score equal to VALUE_NONE (#219)" |
  TABLE rows (zero-score skip; simple-eval skip)
- 8. official-stockfish/Stockfish 9bdf2f8d4c (2026-04-15, nn-f68ec79f0fe3, PR 6730 text via gh api) + fishtest
  records api/get_run/69db95f43ca80bdf151d4913 and /69ddd9003ca80bdf151d4c4d | GPL-3.0, commit message / PR text /
  test logs only | net trained with a recipe yaml (Disservin/nettest@8da0a21503 threats.yaml, not opened) + the
  zero-eval skip, vs master (net nn-7bf13f9655c8, trained by another author, recipe not stated): STC 10+0.1,
  UHO_Lichess_4852_v1.epd, 1 thread, SPRT [0,2] normalized accepted, 106,272 games W 27916 L 27489 D 50867 (~+1.40);
  LTC 60+0.6, same book, [0.5,2.5] accepted, 29,748 games W 7775 L 7470 D 14503 (~+3.56). The PR text says the zero
  rows "are actually mostly skipped" already "except a very small percentage" = confounded with the recipe | TABLE
  row (zero-score skip), evidence only
- 9. commit-title sweep of 9 cached repos (Ciekce/Stormphrax, Yoshie2000/PlentyChess, gab8192/Obsidian,
  jhonnold/berserk, PGG106/Alexandria, codedeliveryservice/Reckless, Adam-Kulju/Patricia, Alex2262/AltairChessEngine,
  TerjeKir/weiss; grep of datagen / in-check / adjudication / eval-limit / DFRC / random-move / multipv words) |
  commit titles only (GPL / AGPL titles; MIT ones not opened) | datagen commits ("datagen tweaks", "datagen setting
  changes", "dont do mat scaling in datagen", "update datagen for incheck", ...) carry NO Elo; in-check hits are all
  search changes | no card
- 4 (cont.). viri_networkhistory_7489e701bb.txt lines 10-60 + 1229-1256 | AGPL-3.0, docs | early rows without TC /
  game counts: viri12 / viri14 / viri18 = data re-analysed with the newest own net +50 / +25 / +23.9 +- 7.2 (vs the
  previous net); viri22 = same data re-evaluated with the HCE at depth 8: -10.5 +- 4.5 vs viri21; "oculist" (maybe
  opening-filtered data, author unsure): 25k nodes -11.33 +- 5.31 (6,654 games, ob.expositor.dev/test/15) - confounded
  | evidence for MIX.md G1 (net teacher beats HCE labels) and the relabel pipeline; no card
- (own data, no licence) D:/grok-pc-data/selfplay_out/forge_selfplay_020.txt first 1,000,000 rows (read-only, awk,
  3.6 s): cp == 0 rows 25,881 = 2.588 %, of them 84.6 % from drawn games (drawn-game rows overall 30.4 %); |cp| <= 10
  6.98 %, |cp| <= 25 12.89 % (corrected by verify 2026-11-05: two recounts agree; the worker's 5.21 / 27.50 did not reproduce) | TABLE row (zero-score skip: Forge share)
- web search (in-check question, 1 of 1): "NNUE training data skip positions in check filter Elo test result
  datagen" | - | no isolated in-check Elo anywhere in the results (arXiv 2412.17948 = the Xiangqi study T02 already
  read; SF PR 4314 = card T02-02; forum anecdotes) | TABLE row: explicit NOT FOUND
- web search (|eval| cap question, 1 of 1): "chess NNUE training data maximum eval cutoff filter positions |score|
  above threshold removed Elo gain test" | - | no test of a plain |eval| cap; nearest: SF dataset-filter commits
  (c3ce220408, 37160c4b16 "positions with only one legal move were removed", both confounded, TABLE row 9 of T02) |
  TABLE row: explicit NOT FOUND
- web search (draw-ratio question, 1 of 1): "self-play training data draw rate rebalance downsample drawn games NNUE
  chess engine Elo" | - | no measured Elo for draw down-sampling / result rebalancing in an NNUE engine (a 2018 Lc0
  mailing-list thread on temperature and draw rate, not NNUE; arXiv 2412.17948 eval-band targets without Elo) |
  TABLE row: explicit NOT FOUND
- 10. https://talkchess.com/viewtopic.php?p=965869 ("Best practices for NNUE training data generation?", 8 posts,
  2024-06-27..30; forum thread 1 of 5) | forum | settings only (fixed 5-10k nodes, a couple of random plies, skip
  capture best moves and in-check positions, 100M+ positions), NO Elo, TC or games anywhere | no card
- 5 (cont.). Stockfish c3ce220408 (2023-04-25) and 37160c4b16 commit messages from the cache | GPL-3.0, messages only |
  c3ce220408: dedup preferring the later score + filter extension + binpack minimiser, local 25k nodes 1.2 +- 2.6,
  confounded; 37160c4b16 adds "all positions with only one legal move were removed" (T02 TABLE row 9, confounded) | no card
- 1 / 9 (cont.). cached commit messages: Reckless 460b614e37 (2024-10-14, "Improve data generation method": opening
  book for datagen + draw adjudication; NO Elo); Caissa c84df9fce5 (2026-07-25, random quiet near-equal positions as a
  plain-FEN self-play book; "no functional change", NO Elo) and the Caissa net commits since 2026-05 (no isolated
  datagen-setting test) | AGPL titles / MIT messages | no card
- (own record, no licence) D:/grok-pc-data/dwqww git show opus-r14b-fast-loader:opus_r14b/item1/LOADER_SPEC.md
  lines 32-57 (the crew's own-words spec of the npt loader) | own | the live npt line already skips a zero-score
  "placeholder" row: same game (ply rising), previous |score| > 100, decisive result, score == 0 (line 36-38), plus
  VALUE_NONE rows; filtered / wld_filtered / simple_eval_skipping are rejected at start-up (line 41) | TABLE row
  (zero-score skip = EXISTING in the npt line)
- stop rule reached at 00:42: sources 7, 8, 9 and 10 gave no new card in a row (rule: stop after 2); research ended.
- (own data, no licence) same shard 020 sample, per derived game block (11,438 blocks, 87.4 rows each): White's result
  46.7 % W / 27.5 % D / 25.9 % L; stored cp is side-to-move (turned to White's view, every decisive block's last row
  agrees with its result: 4,500 W blocks end >= +1000, 2,320 L blocks end <= -1000, none the other way) | TABLE rows 4-5
- (own records) F:/opus_scratch/r6/nnue-pytorch-amd (the live npt build): HEAD 1902d02, `git merge-base --is-ancestor
  f5c9d01569 HEAD` exit 0 (log titles only); skill forge-halfka-parity-test lines 12-13 (`halfka_tool eval <net> <fens>
  <out>`) | TABLE row 6, card T02B-01 scorer
- wrap-up 00:52: 10 sources used (1-10); card T02B-01 finished as PARTIAL (lint 0 findings, 60 lines); TABLE.md 21
  rows, no PENDING verdict; licences.md 17 rows.
