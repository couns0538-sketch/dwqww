# Memory file of fable

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from the command `date -u +%Y-%m-%dT%H:%M:%SZ`, never from your head.
If you lost your context: read `debate/README.md`, this file, `debate/BOARD.md`, then the messages newer than
"Last update" below.

## Who I am
- Name in this debate: fable
- Model: Claude Fable 5.2
- Started: 2026-11-23T10:40:56Z (this PC's clock; it differs from the others' clocks by hours: order is by git log)
- Last update: 2026-11-23T17:15:53Z
- Phase: 2 debate (READY since this update; phase 3 from about 13:10Z on my clock, stop at 13:40Z)

## What I have read to the end (26 source files, 11,566 lines: all ticked)
- [x] debate/README.md, debate/PLAN.md, debate/STATE.md, debate/READ_CHECK.md (I have seen its key: no test of me)
- [x] loop/LOOP_OPTIONS.txt, source/R65_NOTE.txt, loop/build_recipe/build_forge_clang_pgo.sh
- [x] source/src/search.cpp (3,426), board.cpp (1,811), uci.cpp (1,314), nnue_v3.cpp (993), eval.cpp (659),
  nnue.cpp (557), bitboard.cpp (207), book.cpp (193), eval_params.cpp (89), forge65.cpp (61)
- [x] source/include/forge/search.hpp (667), board.hpp (353), nnue_v3.hpp (299), bitboard.hpp (224), b4.hpp (109),
  nnue.hpp (105), eval_params.hpp (103), eval.hpp (90), tm_node_share.hpp (69), book.hpp (58), clock_plan.hpp (52),
  uci_clock.hpp (43), tm_finish.hpp (39), forge65.hpp (22), uci_output.hpp (12), uci.hpp (11)
- [x] every message of astra and neon up to the commits named at the bottom

## What I found (each with file and line, or with the figures I recomputed)

`source/src/search.cpp`
- Compiled defaults 98 to 185; reduction table 296 to 318; move picker 707 to 802; the sort at 998 to 1000 is
  `std::sort` on the score alone (equal scores ordered by the C++ library).
- The stop test runs at EVERY node when a node limit is set, at every 1,024th otherwise (1769, 1918).
- Reverse futility 2085 to 2092; null move 2094 to 2144; ProbCut 2146 to 2180; internal iterative reduction 2184
  has no exception for the root. Razoring 2073 to 2078 is guarded by `excluded.is_none()`.
- Quiet futility 2283 to 2293, history pruning 2294, SEE of quiets 2299; a quiet move that gives check goes through
  the capture branch (2304, 2317 to 2328).
- Singular search 2343 to 2368: depth `std::max(1, (depth - 1) / 2)` (2349); literals 24 and 6 at 2359.
- Late move reduction 2405 to 2446: seven hand-set terms 2409 to 2415, the history term an integer division (2416);
  `LmrDeeperShallower` 163 and 2430 to 2441 (literals 40, 2, 1), in this tree, off by default, not sent by the loop.
- Repetition wrappers 2547 to 2588: `search_cuckoo` / `qsearch_cuckoo` have no caller; `qsearch_child` is entered
  for the same node only from 1913, 1991, 2078; fixed draw score 0 at 2549 and 2561.
- Soft nodes: hard cap FOUR times the soft target (2661 to 2665); soft stop only after a finished iteration (3154).
- `static_evaluate_v3` 3367 to 3423 (lazy accumulators from the nearest valid ancestor).

`source/src/uci.cpp`
- Self-play defaults 300 to 308; `run_selfgame` 448 to 615: a game ending by mate score or score limit ends BEFORE
  its last position is recorded (518 to 537); a draw-adjudicated game HAS recorded it, with a best move that is
  then not played (542 to 552). Game-relative ply starts at 0 for a FEN (457).
- `go perft` after a failed net load ends with code 2 (1124 to 1134). Unknown option = one info line (1116 to 1117).
- `bench` 1222 to 1262: fixed depth, its own searcher: never runs the per-node stop test.

`source/src/nnue_v3.cpp`, `nnue_v3.hpp`, `nnue.cpp`, `bitboard.hpp`
- The kernel (AVX-512 / AVX2 / plain) is chosen when the program is COMPILED (nnue_v3.cpp 17 to 29, 110 to 120);
  no run-time choice anywhere in the 26 files (searched: cpuid, __builtin_cpu_supports, target_clones: nothing).
- `FORGE_SPD_NNUE_ZMM=1` stops the compiler without AVX-512 (nnue.cpp 26 to 29); `FORGE_SPD_SLIDER_PEXT=1` without
  BMI2 (bitboard.hpp 13 to 16). The loop's build sets both with `-march=znver5` (build script 43 to 46).
- `MaxHidden = 1024` (hpp 65); loader checks 595 to 629, 608 to 610, 678 to 681; AVX2 sum at 1024 wide:
  2 x 64 x 2 x 255^2 x 127 = 2,114,092,800 of 2,147,483,647. Fused update and 4-column refresh only under AVX-512
  (444 to 516, 946 to 972; fall-back 912 to 916).

`source/src/board.cpp`, `board.hpp`, `search.hpp`
- `set_fen` validation; the position key includes the en-passant square only when a legal capture exists; game
  repetition and search repetition are two functions; SEE with pin filter. `Worker` holds the history tables: one
  copy per thread. Table entry 16 bytes, 4 to a 64-byte cluster, rule-50 guard in `score_usable`.

Facts from the PC (not on the branch) that I used in answers
- The "engine's own game record" of P3b is `raw_selfplay.binpack` (official Stockfish tools converter); the
  trainer reads text rows; nothing in the loop read the packed file back until today's test.
- The loop starts each game with `position startpos moves <8 random plies>` and `selfgame ... writeminply 8`.
- The tune's declaration (17 November): five deciding matches; liveness audit done before the tune (5 dead
  settings not tuned). I have NOT looked at the tune's current values (they stay unread until it ends).
- The loop's gate plays at 50,000 nodes, the confirmation at 250,000; candidates of rounds 134 to 136 exist.
- Self-play driver: seed per worker = config seed, round, worker, clock in ns; `ucinewgame` before every game;
  8 uniformly random plies from the start position. Teacher: `b_full` (earlier kind of net), weight 0.2,
  target = 0.8 x (0.75 x sigmoid(score) + 0.25 x result) + 0.2 x teacher; the hand-written evaluation's values
  are used only by the teacher. No-teacher run of 16 November: 487-512-1001 at 250,000 nodes (rounds 1 to 21,
  512 wide).

## Measurements I ran for the debate (raw files in debate/evidence/)
- A1: round 136 through the packed record and back: 16,005,930 rows, 0 differences; planted change caught.
- A4: 616966 / 595569 on the loop's program and on the older tree, switch off / on.
- N4: cross-table of round 136 (all rows): 39.88 % of 4-to-8-piece rows at |score| >= 600; 22.58 % of kept rows
  after a game's first 600; 11.21 % after a first 1000 (99.5 % of those rows at 600 or more).
- N2 live pin: Hash 16 = nodes 375880, hashfull 156; Hash 32 = 375868, 78; on the loop's and the published exe.
- N8 / N4 per game (round 136): 29 of 124,850 games repeat an opening, 16 whole copies; sum p^2 = 3.72e-9
  (3.7 % repeats at 20 million games, first order); first 1000: favoured side wins 73,867 of 73,933 games;
  600+ band: 665 loss rows before the filter, 0 after.
- N8 key: of the 29 shared openings, 16 have the same whole FEN and are the same game, 13 differ in the halfmove
  clock and are other games; replay: same 8 moves 3 times = same 112 rows; another move order into the same
  whole FEN = the same 112 rows. Soft fixture on the PC: nodes 1926 / b2b3 (hard), 5506 / g1f3 (soft).
- The PC's soft-node runner (own program, pairs, control mode `nodes:N`): 4,000 games in 5.7 minutes at 4 at
  once, +/- 8.0. The 1024 match's node odds: one engine at a time, one thread, 400 game positions, depth 12.
- Matches at 250,000 nodes, from the loop's log: 1,926 games in 33.5 minutes (12 at once); +/- 8.4 to 8.9 at
  2,000 games. A figure of mine for this speed (1,330 an hour) had no source and was wrong; replaced before the push.
- N8 measured further: 16 of 16 copies equal in all five fields on the raw record (the kept-rows file is not
  valid for this: the filter marks a repeated position inside a round with 32002); the opening rule drawn
  300,000 times: about 1 copy in 100 has the same eight moves in order; 129 of 129 pairs of two orders into one
  whole FEN = the same game.
- N8 after astra's counterexample (two openings, one whole FEN): replayed on the PC = 0 rows against 127 rows.
  The engine reads its history in three functions, all bounded by the halfmove clock (board.cpp 1463, 1474,
  1770; callers search.cpp 1592, 1601, 2551 to 2584, 2790, 2797 and uci.cpp 424; `key_history()` has no caller,
  `history_size()` is a length). Key whole FEN + window in order: 113 of 132 copies kept (300,000 draws), the
  ordered moves 3. The PC's driver does send an opening that is already a third occurrence (its rule test runs
  before each random ply only); the engine ends it with 0 searches.

## Proposals and where they stand (see BOARD.md)
- ACCEPTED: A1, A3, A4, A5, A6, N1 (changed), N2, N3, N6, N8 (my first AND my second key shown wrong by astra; the key is
  now astra's candidate: whole FEN plus the positions since the last pawn move or capture, in order; neon is
  asked), N10, N11 (stage 3 of the bundle rule closed at "lower bound above -3", all three), F1 (mine; J10).
  TO MEASURE AFTER THE DEBATE: A2, N4, N5, N7, N9.
- I dropped two drafts (server build, net shape limit) because neon had posted the same points first (N2, N3);
  my additions went into my replies.
- AFTER THE CLOSE, in the addendum of FINAL_PLAN.md since 2026-11-23T14:32:48Z: A16, A17, N17, A18 (list 'Changes to the
  items above') and A19 (list 'For later'). Each from ONE agreed message with both votes; my checks are in
  debate/evidence/ (fable_a16_check, fable_a17_check, fable_n17_a18_check, fable_a19_recount). The way: read the
  agreed message, redo its numbers or read its source lines, run its fixture on the PC's own program behind
  the loop's gate, then write the entry with what my check showed AND what it did not.
- SECOND BATCH, in the addendum since 2026-11-23T15:13:13Z: A20 (changes W8: the reader mixes afresh on all 40 passes),
  and in the list 'For later' N18 (threads), N19 (clock), N20 (measuring a stronger engine), N21 (net shapes
  after 1024, with the correction of the 16-bucket fixture), A21 (a second training seed). My checks:
  fable_a20_n20_n21_check, fable_n18_n19_check, fable_a21_n21b_w7_check, fable_a19_warm_recount (the recount
  A19's entry still owed). What differed from the seats on the PC is written in each entry, not smoothed.
- THE LOOKS since this push: no fixed 30 minutes any more. A fetch-only watcher on the PC wakes me 45 minutes
  after the first new message named `_agreed_` (or one that asks Fable something), so that items that come
  together are one look; the CLOSING look is at 12:40Z on astra's and neon's clock (11:40 PC), five minutes
  after their six hours end. What is not on a branch by then is not in the plan.
- THE OWNER, about 15:00Z to 15:10Z mine: what I cannot solve alone within 10 minutes, and what Opus and I cannot
  solve together within 10 minutes, I bring to astra and neon at once as a message
  `..._fable_question_<subject>.md` (file and line, exact command, expected against got, what is ruled out).
- THIRD BATCH, in the addendum since 2026-11-23T16:13:34Z: A22 (adds to A20: no pass may replay an earlier one; my check
  fable_a22_check, with the edge that a replay of up to 37 of 128 rows a batch stays under the bar) and, for
  later, N22 (search settings after a stronger net; fable_n22_depth_check: astra's 360 searches equal on the
  PC). A19 cites astra's referee table (fable_a19_referee_recount: equal to the digit). A18's entry: the
  one-position pulse exists in the PC's tool and its sentinel run is done (Opus), recounted by me.
- MY QUESTION 153513Z (a killed process tree still readable after the wait) is answered by neon 084106Z and
  astra 084947Z; what I took from them is in my message of this push. The W5 Linux build hand-offs (neon
  083018Z, astra 090010Z) are read; the server-day build follows them, with the PC loop's own self-play
  command in the profile step.
- FOURTH BATCH, in the addendum since 2026-11-23T17:15:53Z: A23 (W5: bind reservation, final position write and result
  per game id; fable_a23_check: the PC's N12 games 5 and 6 are the two histories, 81 and 67 rows, digests
  equal) and N23 (W1: no set-back of a tuned value on 0 of 600 at one step alone; fable_n23_check: every
  number equal on the PC; with the tune's own steps 12 and 3 the SEE examples are not silent, the depth
  thresholds from 14 are; on this tune (a) and (b) name exactly the five untuned settings). N23 stopped the
  placing of the PC's script for W1's table, which set dead tuned values back.
- READ AT THIS LOOK, no entry: A24 (astra, W8: bind each example's input, bucket and targets to its source
  id at the training batch boundary) is a proposal without a second vote. Closed by their own bars, nothing
  for the plan: output-bucket interpolation, width 768 -> 640 after training, the quiet-move prior in the
  real move picker, the pawn-push shortcut, lane reordering, the N20 opening recipe. Open measurements:
  neon's refresh / fused kernel study, astra's forced-move clock games, draw-rule follow-through.

## What I still owe
- An answer to every new message, by name, in git order. Nobody owes an answer on the key: it is A7 (astra), accepted by all three. MY SLIP at 12:01Z: I merged five messages (astra 045047Z, 045117Z, 045230Z; neon 045136Z, 045430Z) without reading them, because I listed new files only at the first fetch of a turn; I asked neon a question it had answered. From now on: after EVERY merge, `git diff --name-only <last read commit>..HEAD -- debate/msgs`, and the last read commit is the line at the bottom of this file. W10's advance criterion is "the same lower bound above 0" (I had drafted an SPRT -5 / 0 and took it out before pushing: a level result is no reason to change every self-play game). The en-passant rule of the key: past positions legal, the current position with its target when a pawn stands ready to capture (117 of 132; every raw target: 77). Neon's audit of the draft is in draft 2. Neon reached the same en-passant rule on its own (051000Z: every reader, 40 of 40 replays); astra agreed to it and to every new bar of draft 2 (051450Z, 051512Z) and has NO dissent left; astra's 051545Z qualifies neon's pre-seed note (only when the whole key can be rebuilt): in the plan. Neon voted the same (051650Z): NO dissent on draft 2 from either. My own correction: W4's "4.5 hours" had no measurement behind it (1.8 hours with 12 at once). THE OWNER EXTENDED THE DEBATE at 12:17Z on my clock: up to two more hours from then if all three think the plan can still be improved; it ends when each says more debate no longer improves it. Phase 3 at the latest 13:50Z mine (06:50Z theirs), last stop 14:20Z (07:20Z). I asked both for the item with the weakest test and proposed F2 (W8: the disk trainer's net also judged by games, SPRT -5 / 0 at 250,000 nodes) and F3 (W5 c: closed session, killed allocator, cut link, nothing deleted before the PC confirmed it): astra AGREES with both (052049Z, with sharper kill points) and proposed A8 (W6: compare the UPDATE on the rented card, a zero-learning-rate run must fail): I agree. Neon AGREED on F2, F3, A8 (052702Z) and proposed N12 (persistent-worker game parity against the PC) and N13 (four known tables for the stop rule): astra and I agree. I proposed F4 (the day never depends on the opening table; built last; worth 1.3 to 2.1 % of the day): astra agrees with the fallback, the rest is open. THE OWNER (three messages between 12:27Z and 12:35Z mine; the last one counts): the debate runs for THE TWO HOURS he gave and ends at 14:17Z mine (06:17 PC); neon has enough credit and is waited for however long it takes; astra got two subagents from him, I get none. Final text for the votes at about 13:40Z mine (05:40 PC). My part until then: hold the plan's bars against the PC's earlier declarations (W1's five matches, breadth, TD twin). Astra's part: the paid items (W5, W6, W13). N13's four values recounted by my own program: equal to six digits (debate/evidence/fable_n13_recount.txt). STATE at this update: 30 proposals (12 astra, 14 neon, 4 fable); all 11 of the extension ACCEPTED by all three (F2, F3, F4, A8, A9, A10, A11, A12, N12, N13, N14) and written into the draft final plan (W3 a, W5 c/f/i, W6, W8, W9, W13). Astra is measuring F4's cost ratio on its own machine. I OWE the Windows run of astra's six-game fixture (tool written: n12_sixgames.py with astra's numbers typed in before the run; the PC's loop gate said WAIT for heat at 12:33Z, 12:35Z, 12:38Z and 12:41Z mine). THE OWNER at about 12:41Z mine: AFTER the two hours astra and neon may go on between themselves until one runs out of credit; I read the branch every 30 minutes and take an agreed, proven improvement into an addendum of the final plan (no watcher after the two hours, only 30-minute timers). Astra measured F4: 28 minutes of the day [26.3, 29.7]. I held W1, W7, W12 against the PC's declarations: W1 needs an addendum for the dead-setting rule and keeps its sanitizer run; W7 is 2,000 games fixed (+/- 9); the TD twin's match has no declaration that I found. The old soft-node run's pair counts for astra: [141, 438, 757, 486, 178]. ASTRA FOUND A FAULT IN MY EVIDENCE SCRIPT (054147Z): n13_recount.py looked only inside the outcomes that occurred and failed on [0,0,0,250,250] and [250,250,0,0,0]; repaired (full support), astra's +4.335986 / -4.298708 reproduced; both tables are in W3 (a). What follows and is NOT YET VOTED: the same engine against itself gives +0.008672 a pair under the declared formula (H1 at 340 pairs), so W3 (a)'s old known answer "no information" was wrong; I asked both (astra calls it F5 and AGREES, 054727Z; neon's vote awaited). THE WINDOWS SIX-GAME RUN IS DONE (the gate said GO at 12:46Z mine): all equal to astra's Linux run, digests and both plants included (`debate/evidence/fable_n12_sixgames_windows.txt`). A13 (astra, 054630Z: an opening counts once when W4 pools three matches): I agree, in W4 with three declared seeds, an overlap check and the copied-list control; neon's vote awaited. Astra's R1 simulation (054523Z) is in R1: level -> H1 90.5 %, no boundary 5.6 %, H0 3.9 %, 41,500 games on average. For astra's F2 ask (054539Z) I posted six saved deep matches' pair tables (three played to their cap, pooled [55, 713, 1399, 760, 73], variance 0.0413). A14 (astra, 054851Z: the after-game result rules in W5's rehearsal): I agree; a real gap of the draft (the plan's P3b named them, W5 did not). PC facts: round 137 relabelled 947 of 124,544 games, all through the tables; tables that do not open leave only one line in a side file. In W5 (i) now; neon's vote awaited. Astra simulated F2 (055236Z): level -> H1 87.7 %, no boundary 9.2 %, H0 3.1 %, 9,800 games = 2.9 h; in W8 now, with the stop function of W3 (a) at looks of 1,000 games. I PROPOSED F6 (one repeat with a fresh seed when the hunt for a cause finds nothing; level 98.5 %, -5 Elo 5.6 %, -2.5 Elo 56 %): OPEN, no vote yet. Totals now: 34 proposals (14 astra, 14 neon, 6 fable); A13, A14, F5 wait for neon. F6: astra DISAGREED with my form (055610Z: no repeat after H0) and gave a stricter one (one repeat only after a cap + clean audit): I took it; level 95.8 %, -5 Elo 3.1 %, -2.5 Elo 45 %; then astra gave a simulated better form (055726Z): ONE test to at most 40,000 games in two declared blocks, a pause at 20,000 for the hunt, first block's evidence kept; level 96.35 %, -5 Elo 3.15 %, -2.5 Elo 45.69 %, 10,352 games on average, worst case 11.8 h. I AGREE; it is in W8 and changes F2's cap; agreed by astra and fable, waits for neon. NEON CAME BACK (055747Z): AGREE on F5, A13, A14, A12's contrast; it replayed astra's 768 games (768 of 768 equal) and confirmed my Windows run and both pair tables. So F5, A13, A14 are accepted by all three; only F6 waits for neon. N15 (neon 055748Z; astra agrees 055858Z; I agree): an option that did not arrive stops the start; MateAlphaGuard left out passes every pin and the six games; a seventh game catches it. In W5 (i). The Windows run of the seventh game is DONE (13:02Z mine, gate GO): all three arms and both digests equal to neon's and astra's Linux runs, four faulty option lines each one refusal line + readyok + exit 0; evidence fable_n15_guard_game_windows.txt. Totals: 35 proposals (14 astra, 15 neon, 6 fable). AT 13:01Z MINE EVERYTHING IS AGREED BY ALL THREE: neon voted F6 (060022Z, continuous 40,000), astra confirmed the look at 20,000 is ordinary (055933Z) and asked for one operative wording of W8 (060041Z): done. N15's refuse list got `invalid FEN`, `illegal move`, `sgerror` (neon); astra reproduced the three guard arms. 30 accepted into the plan, 5 are tests after the debate, none rejected. A13 got astra's real-round control (round 52: [-3.2, +14.7] against the naive [+0.57, +10.90]). Astra added to A14 (055533Z): winner against side to move in three combinations from round 137's first three log lines, the engine's result kept beside, failed probes apart from draw answers: in W5 (i). Look cadence: 1,000 games, declared in R1 and W8 (astra 055431Z: every pair would be 8,300 games for F2). A15 (astra 060531Z): three made-up matches through the real stop-and-resume wrapper of W8 (A: H1 at 21,000 after no stop at 20,000; B: nothing to 40,000; C: H0 at 14,000), plants: reset at the pause, bars -3/0. All six values reproduced with my own function (tmp/fable_scratch/debate/a15_check.py; evidence fable_a15_fixtures.txt). I AGREE and added: compare the printed statistic and pair count too (a wrapper that counts block one twice at the resume decides the same on A, +5.891631; B catches it, H1 at 35,000). In W8; ACCEPTED BY ALL THREE (neon 060846Z, nine values from a third program; astra 060809Z / 060811Z: five counts, finished pairs, unrounded statistic at every look). N16 (neon 060847Z; astra agrees 060958Z, 061021Z; I agree): the PGO profile is part of the test (W5 a, R3, W14). My addition: three declared outcomes of the timing; undecided = the rightly profiled build is used as the owner directed, report says 'gain not shown' (waits for both votes). Totals now 37 proposals (15 astra, 16 neon, 6 fable), 18 from the extension; 32 accepted into the plan, 5 tests after the debate. Astra 060545Z, two wording corrections, both taken: W5 (f) two ids get INDEPENDENT draws (not 'different openings') and the 99 % distinct bar is for the rehearsal's short fixture only (a healthy day is 98.14 %); W6 '50.3 bytes' is per USED row (about 91 % of kept): 92 GB = 85.5 GiB for 2 billion kept rows, 100.6 GB = 93.7 GiB if all were used. debate/PLAN.md is VERSION 4 since 13:0xZ mine (a change list of the extension's sixteen items pointing to the final plan's W-items). PHASE 3 SINCE 2026-11-23T13:22:08Z: FINAL_PLAN is issued as the final text (no DRAFT line; 'still open' rewritten; an ADDENDUM section at its end for what astra and neon agree on after the end). My own vote is posted (`..._fable_final.md`, AGREE on R1 to R6 and W1 to W16). ALL THREE VOTES ARE IN (astra `062329Z`, neon `062351Z`): AGREE on every item, no dissent. THE DEBATE IS CLOSED since 2026-11-23T13:26:21Z; the votes stand in the first paragraph of FINAL_PLAN's addendum section. The plan is planted in the lab (C:/nnue-lab, not on this branch); the owner and Opus are told. FROM NOW: a look about every 30 minutes (wake timers); a change astra AND neon both agree on (ONE message `_agreed_<item>.md` with final wording, proof and both votes; I check the proof) is written as an entry of the addendum section, pushed, planted again, and the owner is told; nothing above the addendum is rewritten. Until one of the two runs out of credit or the owner deletes the branches. THE OWNER at about 13:37Z mine: I check every 30 minutes for the next 6 hours (last look about 19:40Z mine = 11:40 PC), astra and neon go on for those 6 hours and ALSO look for plans for the time when the engine is stronger. The addendum section has two lists since then: 'Changes to the items above' and 'For later, once the engine is stronger' (an entry there: WHEN, WHAT, TEST, BAR, WHY IT WAITS). Same rule for both lists. Astra WITHDREW its own stop (052358Z: the owner confirmed the extension to it directly): latest stop 07:17Z theirs = 14:17Z mine = 06:17 PC; the final text goes out when all three have said NOTHING MORE, at the latest 13:50Z mine. Astra traced and controlled the pinned en-passant capture (052306Z, 052319Z): selection swaps at search.cpp 960 to 964 and 989 to 996; in W15. MY SLIP at 12:23Z: a fix-up step failed its assert and the next step ran anyway (only the second was guarded): the pushed text said "2 to 3 times" and "without a word"; corrected one push later. Every step of a chain is guarded, not only the last. The owner: neon sometimes waits 180 s for its shell. Astra corrected two texts of mine after that (N5's lower-tail cell; J10's "level pair" control): both taken over, see BOARD. The DRAFT of `debate/FINAL_PLAN.md` is on the branch since 2026-11-23T12:01:01Z: every objection to an item W1 to W16 is answered and written beside the item.
- The hourly summary for the owner (in BOARD.md's last section).
- Phase 3: `debate/FINAL_PLAN.md` from about 13:10Z on my clock.

## My next step
- Watch both branches; carry astra's commits over; answer replies to my additions and to F1.
- Go through the plan's items nobody has touched yet (P5, P6, P12, the order in section 5) and post what my
  reading supports.

## Last shared commit read
shared e57c1b8 and astra 362e7e2 (every message up to these two is read and answered).
