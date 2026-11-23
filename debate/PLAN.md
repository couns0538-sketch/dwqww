# The Forge plan under debate

**Version 2 (23 November 2026, before the debate). Kept by Fable; every change is listed at the bottom.**

This file was written new for this branch from the project's working plan (a long file on the PC that also holds
private notes; it is not uploaded). It says where the project wants to go, what is known, and what is planned
next, item by item. Every number carries its games, its interval (95 % unless said otherwise), its node limit
and its date where we have them. **Raw files are on the PC, not on this branch**, unless a line names a file here.
Where this file says "not checked", nobody has checked it.

## 1. The goal, the machine, the costs

- **Goal:** Forge as strong as possible, correctness first. The owner's mark is "above 3100".
  On the project's yardstick (19 November, round 67's net, 6 s + 0.06 s a move, one thread, Hash 16,
  unbalanced openings; an estimate, not a rating): +124 +/- 28 against Stockfish 19 limited to 3100
  (224-87-89), +84 +/- 28 against Stockfish 11 at full strength (141-70-89), +138 +/- 31 against Stockfish 10
  (169-56-75).
- **The machine:** one PC: 8 cores / 16 threads (AVX-512), 32 GB of memory, one graphics card with 20 GB.
  A heat line of 92 C for the processor is never crossed: matches, the tune and self-play share the threads
  under it. There is no second machine; the cloud helpers read and write text, they do not play matches for us.
- **The loop** (runs day and night): self-play at 2,000 "soft" nodes a move (the search ends when a depth
  is finished) -> filter -> train a new net from nothing on the newest 25 rounds (at most 388,000,000 kept
  positions, 40 passes, with a fixed older net as teacher for part of the target) -> gate match against the
  best net -> if it passes, a deeper confirmation match -> the best net plays the next round's self-play.
- **What things cost** (from the loop's log, 22 to 23 November):
  one round about 67 minutes; of it the training 49 minutes on the card (round 136: 2,917 s) during which the
  processor already plays the next round's self-play (12.9 million positions in that time), the gate about
  15 minutes (round 135: 4,000 games at 50,000 nodes in 872 s on 16 threads). A round keeps about
  15 million positions. So a day gives about 21 rounds, about 320 million new positions, and about
  5 hours of gate matches. Every other match takes threads from self-play or from the tune.
  Rough match prices on this PC, beside the loop: 4,000 games at 250,000 nodes about 3 hours; an SPRT at
  20,000 nodes of up to 20,000 games about 3 hours.

## 2. How a change is judged here (each rule exists because of a measured mistake)

- **J1. Nets are judged by games, never by loss.** 28 candidates gated against one net: the correlation of
  gate Elo with the loss on a fresh round was -0.14. Nets also fit their own rounds: on positions they were
  trained on, the loss is about 6 % lower than on unseen ones, and a net is flattered on the games it played.
- **J2. The gate and the confirmation.** Gate: SPRT at 50,000 nodes, at most 4,000 games. A net that passes
  must also win an SPRT at 250,000 nodes (at most 2,000 games). Over the first 12 promotions the confirmation's
  Elo was on average 0.59 of the gate's (+9.4 against +16.0): a gate pass selects a lucky run.
- **J3. A gain at one depth can be gone at another.** A capture rule gained at 50,000 nodes and not at
  250,000. King-bucket nets were 10 to 17 Elo behind at 50,000 nodes and 29 to 39 ahead at 250,000 (15 November).
  A search bundle passed an SPRT [0, 5] at 20,000 nodes (4,800 games, +10.6 [+4.1, +17.1]) and was dropped
  after about -18 at 2,000 soft nodes.
- **J4. A search change** sits behind a switch whose default is the old code; first the node counts must be
  equal with the switch off; then it is tested as part of a **bundle** with an SPRT [0, 5] at 20,000 nodes,
  a second seed, 250,000 nodes (not below -3), and 2,000 soft nodes before it may play self-play.
  Reason: one idea is worth about 1 to 7 Elo, and a 4,000-game match sees about +/- 7. Eleven changes tested
  alone on 16 November all came out level, for example: no late-move pruning at PV nodes -2.4 [-9.2, +4.4],
  no double extension +1.1 [-5.8, +8.0], no cut-node term in the reduction -0.6 [-7.6, +6.4] (4,000 games
  each at 20,000 nodes).
- **J5. One bad result does not close an idea.** It is recorded as "lost alone, under these settings" and
  gets one test together with what it depends on. A bundle chosen after looking at many results is confirmed
  by a second match with another seed before it is adopted.
- **J6. Tuned search values fit the net they were tuned with.** Measured 15 November at 50,000 nodes: about
  +47 for that net; on another net the "shape" half of the values gave +11 and the 16 pruning margins +1.
  The same shape values gave +79.2 +/- 7.5 at 2,000 nodes (6,000 games), the depth of self-play.
- **J7. A number belongs to its engine, net, settings and position set.** A tree-size factor from 200
  positions carries about +/- 6 %, is taken on book openings AND on positions from games (they have disagreed
  in sign), and says nothing about strength.
- **J9. The newest net is not the best net until a match says so, at completely equal settings** (the same
  program, the same settings, the same node limit, the same openings played from both sides). The owner's rule,
  repeated on 23 November. It holds above all for the net that plays the rented server day (P3b).
- **J8. The loop's gate is not changed on one match and a plausible story.** A gate change is tested like
  any other change. (A gate at default settings once promoted a net that was weaker as a whole engine.)

## 3. Where the work stands

All numbers are in `debate/STATE.md` (written by Opus, the second Claude session on the PC). In three lines:
the best net is still round 67's (adopted 19 November); 68 rounds of candidates since then were not adopted,
and a 30,000-game direct match of a later net against it gave +2.35 [-0.10, +4.80]; the largest measured gain
that is not yet in the engine is the big tune of the search settings (+40 to +57 at 20,000 nodes on an older
engine and net); a net of width 1024 trained on 0.38 billion positions was level with 768
(+0.47 [-5.38, +6.33]; that match was stopped, see 3a and P4).

## 3a. A direction that is given: data first, then the bigger net (the owner, 23 November)

The owner decided while this debate was prepared: **first 2 billion positions, then the net**; a net of width
1024 needs at least 1 billion. The debate takes this as given. It is asked HOW: which positions count, how one
training reads 2 billion positions on this machine, and which net is then trained on them. Known today:
- The loop has kept 2,036,342,838 positions over its 136 rounds; 1,052,412,711 of them (rounds 68 to 136) were
  played by round 67's net, the others by weaker nets and partly by older versions of the engine and of the
  labelling rules. In which form each round's file lies on disk: see `debate/STATE.md`.
- New positions: about 15.25 million a round, 67 to 78 minutes a round: about 280 to 330 million a day.
  Rounds 68 and later alone reach 2 billion in about 3 more days ((2.00 - 1.05) / 0.3).
- Today's trainer keeps the whole window on the card at 40.8 bytes a kept position: 388 million fill the 20 GB
  card, 2 billion would need about 83 GB. Main memory is 32 GB. So on this PC one training on 2 billion must
  read them from disk in pieces (P3).
- Today's speed: round 136 trained 388 million kept positions for 40 passes in 2,917 s. At that rate 40 passes
  over 2 billion take about 4.2 hours (2,917 s x 2,000 / 388 = 15,036 s), before any cost of reading from disk.
  A round of self-play takes about an hour, so "a new net every round" no longer fits such a training.

- **Rented machines (the owner's plan, told on 23 November):** in one to two weeks a 64-core server for one
  day, to make the positions faster; after that a rented graphics card of the H100 or B300 class for the
  training. This PC's self-play makes about 5,800 positions a second on its 16 threads (round 135: 3,386,849
  new positions in 582 s). At the same speed per thread a 64-core / 128-thread server makes about 46,000 a
  second, about 4 billion in one day (about 2 billion if its threads are half as fast): the one day can cover
  the 2 billion. An H100 has 80 GB of memory, just under the 83 GB that 2 billion positions need in today's
  record; the B300's memory: not checked. See P3b.

## 4. The items

Status words: RUNNING, READY (can start, nothing to build), TO BUILD, WAITING (for another item), OPEN (no decision).

### P1. The big tune: finish it, then five deciding matches before its values enter the loop. RUNNING
- What: SPSA over 40 search settings, 40,000 iterations of 16 games at 20,000 nodes; 33,375 done on
  23 November 01:50. Then the final values against today's values in five matches declared in advance:
  fast (20,000 nodes), deep (250,000), at self-play depth (2,000 soft nodes), with a second net, with a second seed.
- Why: snapshots against the start values, 2,000 games each at 20,000 nodes: +40.5 [+30.6, +50.5],
  +42.8 [+33.0, +52.6], +56.6 [+46.7, +66.6].
- What is not known: the tune ran on the engine of 17 November with round 33's net; nothing is measured at
  250,000 nodes, on the clock, or with today's engine and net (J3, J6). Three settings of an earlier tuner were
  found to do nothing at their values (a margin whose steps are multiples of 100; two settings that act only
  when a third is above 0); whether any of the 40 is like that: not checked.
- A consequence to plan for: new search values change self-play itself (J6: +79 at 2,000 nodes for the last
  set). The window then holds positions scored by two different searches for 25 rounds.

### P2. The loop's decision rule. TO BUILD (two repairs), OPEN (the rule itself)
- Known: candidates were better than the best net by about +3 to +4 at 50,000 nodes again and again
  (29 nets against round 33's net: +3.5 pooled), and one 4,000-game gate cannot see that. Since round 88 the
  loop also pools its last 8 gates; the pool has not fired (rounds 129 to 136: 29,968 games,
  -0.07 [-2.52, +2.38]). The direct match (round 87's net against round 67's, 30,000 games at 50,000 nodes):
  +2.35 [-0.10, +4.80].
- Two faults in the rule's code, found 23 November, repairs planned with tests (see P12).
- Open: is the standstill since round 67 a measuring problem (real gains of +2 to +3 that the rule cannot
  bank) or a ceiling of this net at this amount of data? The numbers above do not decide it.

### P3. Data first: one training on 2 billion positions (a trainer that reads the window in pieces). TO BUILD (partly built); the direction is given (3a)
- Known: the window (388 million kept positions = 25 rounds) is what fits on the card. Since the cap is
  reached, every candidate is trained on the same amount of data as the best net, and the gates are flat
  (28 candidates against one net: +3.3 pooled, no trend). Earlier, while the window still grew: 4 of 4 rounds
  trained on more data than their opponent gained, 3 of 3 trained on less did not (16 November; size and
  composition changed together, so not clean).
- Built: a feeder that keeps the window in main memory and hands it to the card in pieces passed its short
  card tests (per-step losses equal to the live trainer's within run-to-run noise; its speed against the live trainer's was recorded as 0.95 to 1.02, and which
  way that ratio was divided has not been re-checked).
  Not yet run: 40 passes on a real window. In main memory it reaches about 450 million positions beside
  self-play: not enough for 3a. The next step reads from disk.
- Open design questions (nothing decided): (a) the store: 44 bytes a position is 88 GB for 2 billion and the
  main disk has about 57 GB free; the packed text is about 0.3 GB a round but costs about 2 minutes of parsing
  a round with 4 processes; (b) the mixing: pieces read in a fixed order are not a random order over the
  window; (c) how many passes; (d) how often a net is trained once one training takes hours; (e) which rounds
  count (next point).
- Which positions count: older rounds were played by weaker nets. The "breadth" match (STATE section 4) is the
  cheap test of whether older rounds carry information; it is trained and is next in the match slot (see P11).
- An outside figure, as a hypothesis only: public nets of this shape are trained on 1 to 20 billion positions.

### P3b. The rented days: a 64-core server for positions, then a rented card for the training. TO PREPARE
- **Four conditions set by the owner (23 November):**
  1. *Everything on the server runs by scripts, with no AI session beside it* (none will be available there):
     one start command; it checks itself first (reference numbers, perft, known answers); it restarts a
     worker that ends; it notices a full disk and a stalled worker; it stops by itself at a set time; every
     step writes a log that can be read afterwards.
  2. *The data is compressed from the moment it is written and sent to the PC while the day runs*, not at
     its end: closed pieces with a checksum each, sent as soon as they are closed, checked on arrival, sent
     again if the check differs. Sizes on this PC today: a round of about 16 million positions is 32 MB as the
     engine's own game record (moves and scores; the positions are rebuilt from it) and 289 MB as packed
     position text. So 2 billion positions are about 4 GB as game records, or about 36 GB as packed text.
  3. *Not every position is kept: scripts choose the good ones automatically* (P3c).
  4. *The program for the server is built the fastest way for its processor*: profile-guided and link-time
     optimised, profiled with self-play itself, as the PC's own program is (clang, ThinLTO + PGO,
     `-march=znver5` for the PC's Zen 5 processor; the PC's builds differ by up to 1.5 % between two builds
     of the same source, so a speed claim needs two builds a variant). Full link-time optimisation against
     ThinLTO has not been compared here.
- What must exist and be proven on this PC before the server day, so that none of its hours is lost:
  (a) a build of the engine for that server's processor and system (today's programs are built for this PC:
  Windows, AVX-512; the server is probably Linux; the PC has a Linux subsystem to rehearse on);
  (b) the self-play driver, the after-game rules, the endgame-table files they use, and the filter as one
  package that starts with one command; (c) the check that the package makes the same positions as the loop:
  the three reference numbers and the perft counts on the new build, the two known answers with the loop's
  settings and net (226187 / 616966), and a set of whole self-play games replayed with equal moves and scores;
  (d) how the data comes back and is verified (condition 2 above); (e) a rehearsal of everything at small
  scale, the scripts running alone from start to stop (condition 1).
- Decided before the day, because every position of that day carries it: which net and which search settings
  play (so P1 must be finished and judged first), and how deep each move is searched (today 2,000 soft nodes;
  with about twice the positions to spare, deeper searches for better labels are a real choice).
- For the rented card: today's trainer runs on an AMD card under Windows; its fast kernels are written in
  Triton, which also runs on NVIDIA cards (the port: not tested). If the card holds the whole window, no reading
  in pieces is needed there; if not, P3's feeder is.
- Not known: the server's exact processor, its system, the price of the hours (the owner's side), and how a
  net trained elsewhere is checked here before the loop trusts it (the trainer-against-engine check exists).

### P3c. Which positions are kept: the filter. RUNNING (today's rules), OPEN (better rules)
- Today's automatic filter (round 137: 16,009,233 positions written, 15,251,832 kept = 95.27 %): it drops
  duplicates (479,948), positions whose rule-50 counter is above 80 (175,311), positions with fewer than
  4 pieces (101,563) and positions whose score contradicts the game's result by more than 600 (579); the
  score limit of 2,000 and the ply limit dropped none. Self-play itself writes no position before ply 8.
  Positions whose best move is a capture are kept on purpose.
- Measured here: keeping capture positions won +15.4 +/- 5.9 and +15.65 +/- 5.81 (6,000 games each, on an
  earlier net and less data); dropping positions in check was level (+1.0). Both wait for one re-test on
  today's net.
- Not measured here: any rule that looks at how quiet a position is, at the gap between its static
  evaluation and its search score, at the spread of piece counts over the kept set, or at how many
  positions one game may contribute. Public trainers use rules of these kinds (as hypotheses for this
  engine; sources to be named in the debate by whoever proposes one).
- Why it matters more now: with 2 to 4 billion positions made in a day there is room to keep only the
  better half, so a filter rule can be judged by training two nets on equal numbers of positions (kept by
  the old rule against kept by the new one) at completely equal settings (J9).

### P4. Width: the 1024-wide net. STOPPED until P3 (3a)
- Known: 1024 against 768, same recipe and rounds, node odds for the slower net: 4,400 games,
  +0.47 [-5.38, +6.33], no verdict. Both nets were trained on about 0.38 billion positions, under the floor
  the owner names for this width, so the match says nothing about width with enough data; it was stopped on
  23 November. Earlier steps point the same way: 768 against 512 on the same data about +34 (16 to
  17 November), while a 768 net on only 96 million positions had lost about -10 against 512.
- Plan: the wide net is trained again when one training can read at least 1 billion positions (P3), and is
  then judged against the best net with node odds for its speed. Which shape (width, king buckets, output
  buckets) is open.

### P5. The training recipe as a bundle, four declared rounds. READY
- What: one learning-rate cycle instead of several, a smaller weight decay on the first layer (0.1), a result
  share of 0.35 instead of 0.25 in the target, 40 or 60 passes; four loop rounds, their pooled gates against
  the pool of the plain rounds.
- Known: single recipe changes were level alone. 60 against 40 passes: one match +7.8 [-0.4, +16.0]
  (2,000 games at 250,000 nodes), but in the loop four 60-pass rounds and four 40-pass rounds against the same
  net gave +3.72 and +3.22. Smoothed labels (TD): eight rounds +3.37 [+1.01, +5.72] against round 67's net,
  the plain rounds before them -0.81 [-3.02, +1.40]; but against only the last six plain rounds the difference
  halves, so it was recorded as "level alone" (STATE section 5). Its twin match is trained and waits.

### P6. A second player in part of self-play. TO BUILD
- What: while no candidate passes the gate, every round is played by the same net, so the window fills with one
  player's games. Proposal: a declared trial of four rounds in which a share of each round's games is played
  by a second net (the newest candidate, or the previous best), the gate unchanged.
- Known: two splits of the gate history point in opposite directions. Rounds 39 to 66 (window filling with
  round 33's net's games): +5.24 early, +1.44 late. Rounds 68 to 78 (filling with round 67's net's games):
  rounds 68 to 72 about -4.6 +/- 1.9 (one standard error), rounds 73 to 78 about +1.1 +/- 1.4. Both splits were
  chosen after seeing the numbers. Neither is a result; only the intervention can tell.
- To build: where self-play takes its net (a share setting, default 0 = today), and a record of which net
  played each game.

### P7. Search work on today's engine. WAITING for P1
- Why waiting: the tune moves 40 settings; a bundle measured on the old values would have to be measured again.
- Candidates from earlier trees on the PC (they are NOT in `source/`, which is the loop's tree; each is a
  switch or a setting): the reduction's seven hand-set terms as settings; a deeper / shallower re-search
  after a reduced search beats alpha (+8.7 [+0.3, +17.1] in 2,000 games at 250,000 nodes, one seed; its tree
  is 12 % larger on game positions and 14 % smaller on openings at depth 16); limits of the double extension
  (it costs 18 % of the tree on game positions at depth 12; switching it off was level in games); tablebase
  probing in the search (+18.6 +/- 3.7 from 6-to-9-piece endings at 2,000 nodes; as a whole engine it played
  self-play 3 % slower, so: not now).
- Two facts of the source on this branch that the tune's values meet:
  `source/src/search.cpp` line 2416: `if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);`
  is an integer division, and the loop sends `LmrHistoryDivisor 5643`: every history value between -5642 and
  +5642 changes the reduction by nothing. Line 2184: the depth reduction for a node without a hash move has no
  exception for the root.
- Never measured here: more than one thread; the time handling without an increment.

### P8. Correctness duties that stay whatever the debate decides
- Every build prints the three reference numbers; 12 published perft counts; every option the loop sends is
  checked against the program's own list before a match; a checking build (address and undefined-behaviour
  checks) with a planted fault that must be caught; a second reader for every change that enters the loop.

### P9. Decided against, with the reason (a proposal to reopen one needs new evidence)
- Dropping positions whose best move is a capture: keeping them won +15.4 +/- 5.9 and +15.65 +/- 5.81
  (6,000 games each, on an earlier net).
- A net as its own teacher: -8.3.
- Judging or stopping a training by its hold-out loss (J1).

## 5. The order as it stands before the debate

1. P1 to its end and its deciding matches (the processor's first job beside the loop).
2. P2's two repairs (minutes).
3. P3b: everything the rented server day needs, rehearsed here; and P3: the trainer for 2 billion positions
   (on the rented card, or in pieces on this PC). Until then the loop runs as it is: its rounds are positions.
4. The match slot meanwhile: breadth (do older rounds count?) -> the TD twin (P5).
5. The first trainings on 1 to 2 billion positions: 768 and 1024 wide on the same data, each judged against
   the best net (P4).
6. P5 or P6 as a four-round trial in the loop only if it does not disturb 3 (one trial at a time, or their
   effects mix).
7. P7 after the tune's values are in.

## 6. What we most want from the debate

- Q1. Standstill since round 67: measuring problem or ceiling? Which single experiment separates the two at
  the lowest cost on this machine, and what result would show each?
- Q2. Data first is given (3a). What is the fastest correct way on this machine to train one net on 2 billion
  positions (store, mixing, passes, how often a net is trained), and which positions should count? Then: which
  net for that data, and how is it judged against round 67's net when its speed differs?
- Q2b. The rented days (P3b): what must be proven before the server day, what should that day's games look like
  (which net, which settings, how many nodes a move, one player or several), and how is its output checked?
- Q2c. Which positions are good (P3c)? Name a filter rule, the evidence for it, and the two-net test that
  would show it here. What is the smallest and safest form in which the server's output can travel?
- Q3. Are the gate's depths right (50,000 nodes, then 250,000) for nets that learn from 2,000-node games and
  gain with depth? What would a better rule cost in games per day?
- Q4. From your reading of `source/`: what would you change first for strength, with file and line, and how
  would it be tested as a bundle under J4?
- Q5. From your reading of `source/`: what is wrong or fragile? Correctness comes first.

## 7. Three more items, written by Opus (the second Claude session on the PC; unchanged but for their numbers)

Numbers: see `debate/STATE.md`. Processor costs assume the PC's 8 cores / 16 threads with the loop running
beside; card costs the one card of 20 GB. P10 goes with P1, P11 with P3, P12 with P2 and P7.

### P10 (Opus): Finish the big tune, then confirm its values on TODAY's engine and net before the loop uses them.
- WHY: it is the largest gain measured in this project: snapshot 10 of the tuned values against the start values,
  2,000 games at 20,000 nodes, 703-380-917, +56.6 [+46.7, +66.6] (snapshots 8 and 9: +40.5, +42.8). But it was
  tuned on engine r15d with round 33's net at 20,000 nodes; the loop now plays r15dsg with round 67's net, and a
  gain measured at shallow depth has vanished at 250,000 nodes before (a capture rule here did exactly that).
- COST: the tune's last 6,625 iterations (106,000 games at 20,000 nodes, 8 at once) are about 14 processor hours
  of play; the confirmation about 3 hours (4,000 games at 250,000 nodes) plus 1.5 hours on the clock. Card: none.
- HOW IT IS JUDGED (bar written now): final tuned values against the loop's current values, both on today's exe
  and net: (1) SPRT [0, 5] at 20,000 nodes must end H1; (2) 4,000 games at 250,000 nodes with the lower bound of
  the 95 % interval above 0; (3) 2,000 games at 6+0.06 not below -5 at the point value. All three, or no adoption.
- WHAT WOULD CHANGE OUR MIND: a level or negative result at 250,000 nodes. Then the tune fitted shallow search;
  next would be the few settings that moved furthest, tested as one bundle at 250,000 nodes, not the whole set.

### P11 (Opus): Data first (the owner's order of 23 November: "first we get 2b positions then the net"): train on 2 billion positions with a trainer that reads its window in pieces; only then a 1024-wide net.
- WHY: the owner's rule: a 1024-wide net needs at least 1 billion positions. W3 (1024 against 768, both on
  rounds 52 to 76, about 0.38 billion) was level: 4,400 games, +0.47 [-5.38, +6.33]: too early to test width.
  The loop's own counts hold 2,036,342,838 kept positions over rounds 1 to 136, 1,052,412,711 of them from
  rounds 68 to 136 (played by round 67's net). But today's trainer keeps its whole window on the card at
  40.8 bytes a kept position: 388 million is about 16 GB of the card's 20 GB, 2 billion would be about 83 GB.
  Meanwhile 69 rounds of candidates sit level with round 67's net (pooled rounds 129 to 136: 29,968 games,
  -0.07 [-2.52, +2.38]), each trained on the same 25 rounds.
- COST: the breadth match first, about 3 processor hours, no new code. The loader: about one day of work and
  about 5 card hours of tests. One training on 2 billion positions, 40 passes, at round 136's speed (388 million
  in 49 minutes) is about 4 card hours plus the reading from disk (to be measured). If only positions of the
  current net count: about 62 more rounds (about 3.4 days of the loop) to reach 2 billion of them.
- HOW IT IS JUDGED: (1) breadth (every second row of rounds 29 to 78) against round 78's own candidate (every
  row of rounds 54 to 78, the same row count) at 250,000 nodes: lower bound above 0 = older rounds count toward
  the 2 billion; otherwise only rounds of the current net count. (2) The loader reads today's 388-million window
  in pieces and must give a net whose hold-out loss is within 0.0001 of today's trainer's before any larger run.
  (3) The 2-billion 768 net must win the loop's gate and confirmation against round 67's net. (4) Only then the
  1024 net on the same 2 billion, against that 768 net with node odds for the slower net, at 250,000 nodes.
- WHAT WOULD CHANGE OUR MIND: a 2-billion 768 net level with today's: then volume at this label depth is not
  the lever, and the next lever is label quality (deeper self-play searches per position).

### P12 (Opus): Keep the loop's one decision rule sound, and test search ideas only as bundles.
- WHY: two faults found on 23 November: round 112's gate printed its verdict and then did not exit for
  2 hours 24 minutes, so it was recorded as not finished and the pooled gate had no pool for rounds 113 to 119;
  and the pooled gate leaves out a gate that has all its games but is marked not finished. Separately: one search
  idea is worth about 1 to 7 Elo, and a 4,000-game match sees about +/- 7, so eleven changes tested alone on
  16 November all came out level.
- COST: the two repairs are small code changes with tests (processor minutes). A bundle test is an SPRT [0, 5]
  at 20,000 nodes (up to about 20,000 games, about 3 processor hours), then 4,000 games at 250,000 nodes.
- HOW IT IS JUDGED: repair 1: a stand-in for fastchess that prints the verdict and never exits; the loop must end
  it, keep the verdict (H0, 1,860 games) and mark the gate finished; the file before must fail this test.
  Repair 2: replayed on a copy of the state, round 113 must pool rounds 106 to 113 into one pool of 14,811 pairs,
  -0.53 [-2.98, +1.93], and a gate with neither all its games nor a verdict must still stop the pool.
  A bundle is adopted only with H1 at 20,000 nodes AND a lower bound above 0 at 250,000 nodes.
- WHAT WOULD CHANGE OUR MIND: bundles that pass at 20,000 nodes and fail at 250,000 nodes, twice in a row. Then
  shallow tests mislead for this engine and the first stage of every test moves to 250,000 nodes.

## Changes to this file

- Version 1, 23 November 2026: first upload, before the debate.
- Version 2, 23 November 2026, before the debate: the owner's conditions for the rented server day (all by
  scripts, compressed and sent from the first minute, automatic filtering, the fastest build for its
  processor) in P3b; the new item P3c (the filter) and question Q2c; rule J9 (equal settings); P2 quotes the
  newest pool; the feeder's speed line worded with its doubt.
