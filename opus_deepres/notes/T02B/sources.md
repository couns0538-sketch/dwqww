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
- 4 (cont.). same file, lines 186-232 (gemstone / gemini) | AGPL-3.0, docs | "gemini" = gemstone's 963M-position set
  + ~250M extra DFRC positions (~21 % of the set), same arch: classical STC 8+0.08 -5.11 +- 4.22, SPRT [0,3] failed,
  12,912 games; DFRC STC +18.36 +- 6.96 (4,488 games) vs gemstone; "grimoire" (+444M classical positions) -0.37 +-
  2.90 (27,224 games) | TABLE row (DFRC openings: drop for a classical gate); no card
- 5. official-stockfish/Stockfish commit messages from the cache official-stockfish__Stockfish__2020-08-01__2024-12-31
  (grep of datagen words; `--show` d53071eff4, 85f8ee6199; b939c80513 grep lines only; no new fetch) | GPL-3.0, commit
  messages only (no source) | d53071eff4 (PR 3521, nn-7e66505906a6, 2021-06-03): previous 64B binpack + a 2B binpack
  generated from an opening book of positions whose static eval differs strongly from a depth-9 search ("wrongNNUE"
  book), same arch HalfKAv2^, retrained 40 epochs: STC 10+0.1 [-0.5,2.5] passed, W 6254 L 6028 D 52310 (64,592
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
