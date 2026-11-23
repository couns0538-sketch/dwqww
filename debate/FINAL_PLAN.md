# The final plan for Forge (debate of 23 November 2026)

**FINAL TEXT, issued at 2026-11-23T13:22:08Z (Fable's clock) for the last votes. Each of the three writes one message `..._<name>_final.md` with AGREE or DISSENT for every item (R1 to R6, W1 to W16); a dissent is put beside its item, word for word. After the votes nothing above the addendum at the end is rewritten.**

Written by Fable from `debate/PLAN.md` (version 4) and `debate/BOARD.md`. Three took part: Fable (Claude, on the
PC), Astra (OpenAI Codex), Neon (Gemini 4 Neon); all three read every file of the branch first. 37 proposals were
made (15 Astra, 16 Neon, 6 Fable); none was rejected; a change entered only with a measurement, lines of the
source, or arithmetic that the others recomputed. The proofs are on the board and in `debate/evidence/`.

**How to read it.** One ordered list of work items, W1 to W16. Each has: what is done, the TEST, and the BAR,
written here before the test is run. A bar is not changed after its test has a result. Where two of us still
disagree, the DISSENT stands beside the item. `PLAN.md` holds the reasons and the numbers behind every line.

**Given by the owner, not debated:** first 2 billion positions, then the bigger net (a 1024-wide net needs at
least 1 billion). A 64-core server is rented for one day in one to two weeks, after it a card of the H100 / B300
class. On the server everything runs by scripts alone; the data is compressed from the first minute and sent
home while the day runs; scripts choose the good positions; the program is built the fastest way for the
processor it runs on (profile-guided and link-time optimised). The newest net is not the best net until a match
at completely equal settings says so. Correctness comes first.

## Rules of judging that every item below uses

- **R1 (was F1, now J10). "Not weaker at the depth of self-play"** is always this one test: a paired SPRT
  between -3 and 0 Elo at 2,000 soft nodes (alpha = beta = 0.05), every opening from both sides, the error from
  the pairs, at most 100,000 games. H1 = holds. H0 = does not hold. No boundary at the cap = inconclusive = not
  adopted. The stop is looked at after every 1,000 games (the runner's chunk; the numbers below are for that). Fallback -5 / 0 only if a timed run shows more than 4 hours at the cap (so far 2.4 hours, extrapolated from one run of 4,000 games in 5.7 minutes; W3 times it). That run's own pair counts, read from its game list during the debate: [141, 438, 757, 486, 178] in 2,000 pairs (`debate/evidence/fable_r1_old_run_pairs.txt`); with that spread the test needs about 39,000 games when the truth is exactly level (Fable's arithmetic). Astra's simulation with that pair shape (20,000 runs a point, a look every 1,000 games, the cap of 100,000): a truly level candidate ends in H1 in 90.5 % of the runs, without a boundary in 5.6 %, in H0 in 3.9 %, after 41,500 games on average (about an hour at that run's rate); one that is truly 3 Elo weaker ends in H1 in 4.0 %; one at -1.5 Elo ends without a boundary in 23.8 %, after 59,500 games on average. So about one truly level candidate in ten is not adopted by this rule; the rule stays as it is (Astra, Fable).
- **R2 (J11). A search change is tested as a bundle, in four stages:** (1) every switch off = the old node
  counts, and per switch a count of how many of 600 positions change; (2) SPRT between 0 and 5 at 20,000 nodes
  on each of two declared opening seeds, both H1; (3) 4,000 games at 250,000 nodes; (4) R1 before self-play
  uses it. **The bar of stage 3: the lower end of the 95 % interval, taken from the opening pairs, above -3** (all three; the error at this depth is +/- 6.1 at 4,000 games, so a measured +3.1 is needed; a bundle truly worth +5 passes 72 %, a true -3 passes 2.5 %). The tune's own deep match in W1 keeps its declared bar, above 0.
- **R3 (N10). A net whose speed differs** is judged in three stages: a screen at 250,000 nodes with node odds
  measured at the match's real concurrency (lower bound above 0 to go on); the proof with equal clocks at one
  declared time control on a quiet machine (lower bound above 0); then R1 and its positions a second with 16
  workers before it plays self-play. Both arms of a timed comparison of two widths run the IDENTICAL program
  (R4), profiled on a mix of both widths that is declared beforehand (N16; Neon, Astra).
- **R4 (J9). Completely equal settings** in every comparison of two nets: the same program, settings, node
  limit and openings from both sides. **R5 (J1).** Nets are judged by games, never by loss.
- **R6.** A test of one recipe, filter or teacher change on today's window only sets the ORDER of work; the
  recipe for the 2 billion is decided by a matched pair trained at that size (Astra).

## The work, in order

Resources: "processor" = the PC's 16 threads beside the loop; "card" = the PC's one card between the loop's
trainings; "build" = code and tests, no chip. Items on different resources run side by side.

**W1. Finish the big tune and judge its values (P1, P10; N1).** Processor. Running: 33,375 of 40,000 iterations.
- TEST: first the liveness table at the FINAL values (all 45 settings: the 40 tuned ones and the five left out
  as dead on 17 November; each one step down and up, depth 12, 200 openings + 400 game positions). Match 4
  needs W3 (a), which is built and proven while matches 1 to 3 run. Then the five matches declared on 17 November, in this order, the first that
  does not hold ends it: 20,000 nodes SPRT 0 / 5, cap 8,000 games; the same with a second opening seed; 250,000
  nodes, 4,000 games; R1 at 2,000 soft nodes (replaces "4,000 games, not below -5" by an addendum written before
  that match has a result); a second net (round 27's) at 20,000 nodes, 2,000 games. Played with the loop's best
  net of that day and with round 33's net; both must hold.
- BAR: matches 1 and 2: H1, or at the cap a lower bound above 0. Match 3: lower bound above 0. Match 4: H1 of
  R1. Match 5: point value not below 0. All five, or the values do not enter the loop. A setting that is dead at
  the final values keeps its start value; a partner setting that came alive is named before match 1.
- Held against the tune's own declaration on the PC (17 November 22:08; Fable, during the debate): matches,
  order and bars above are the declared ones. Its text says "A = the final values (all 40)" and "no snapshot
  is picked by its result", so the rule for dead settings is an ADDENDUM to it, written before match 1 has a
  game, and the liveness table alone names the settings (no match result). Its other duties stay: 8 games at
  once in chunks of 1,000 through its own runner; the sanitizer run of the final values before anything is
  placed (its addendum 5); and, as a record and not a bar, 400 games on the clock against Stockfish 19 at
  3100 after the placing.

**W2. The loop's two repairs (P2, P12; N11).** Build, minutes of processor.
- TEST 1: a stand-in for the match program prints its verdict, never exits and has started a child that never
  ends. BAR: the loop ends it, no child process is left, the games and the verdict (H0, 1,860 games) are kept
  and the gate is marked finished; the file before the repair must FAIL this test.
- TEST 2: replay on a copy of the state. BAR: round 113 pools rounds 106 to 113 into 14,811 pairs,
  -0.53 [-2.98, +1.93]; a gate with neither all its games nor a verdict still stops the pool.

**W3. The two measuring tools that later items wait for.** Build, then about an hour of processor.
- (a) R1's sequential stop over the PC's soft-node runner, its statistic computed from the opening pairs and not
  from single games (Neon; shown on a made-up list of pair results whose answer is known). TEST and BAR before
  its first use: the runner's own
  transcript on the fixed position shows `go softnodes 2000`, nodes 5506, best move g1f3, and its hard-node mode
  FAILS that check (nodes 1926, b2b3); the same engine against itself gives a pair total of exactly 1 on
  every opening (the wiring test; Astra). The stop's answer on that table is NOT "no information" under the
  formula below: every such pair adds +0.008672, so 339 pairs give +2.9398 and no stop, 340 pairs +2.9485 and
  H1; a stop that divides by a spread of zero there fails (Fable, after Astra's tables with empty outcomes;
  F5; agreed by all three: Astra withdrew its earlier special case and its simulation of R1 is unchanged by that; Neon recomputed the closed forms and ran the repaired script on the four one-outcome tables); a candidate
  at half the nodes ends in H0, one at double the nodes in H1; Astra's two made-up logs, (win, win), (loss,
  loss) and (win, loss), (loss, win), give the pair counts [1,0,0,0,1] and [0,0,2,0,0] and different statistics.
  Added in the extension (N13, Neon; agreed by all three): the stop's formula is written down before it is
  built: the likelihood ratio of the five pair outcomes (0, 1/4, 1/2, 3/4, 1 a pair) between the logistic-Elo
  means of -3 and 0, each maximised under its mean, with the bounds +/- ln 19 = 2.944. The runner's own stop
  function must give, on four made-up tables of pair counts [LL, LD, DD+WL, WD, WW]:
  [1100, 3300, 13200, 3300, 1100] -> +4.684, H1; [550, 1650, 6600, 1650, 550] -> +2.342, no stop;
  [1043, 3086, 12000, 2914, 957] -> -4.227, H0; [957, 2914, 12000, 3086, 1043] -> +12.732, H1 (three
  separate programs, Neon's, Astra's and Fable's, agree to six digits: `debate/evidence/fable_n13_recount.txt`;
  the normal approximation gives 4.686, 2.343, -4.228, 12.752, the same decisions, so a tolerance of 0.01
  holds only between programs of this formula). A stop with the statistic doubled stops on the second table,
  one with the hypotheses 0 / +3 gives H0 on the first, one with -5 / 0 gives +13.002 there, one with the
  sides swapped gives H0 on the fourth. Tables with EMPTY outcomes (Astra): [0, 0, 0, 250, 250] -> +4.335986,
  H1; [250, 250, 0, 0, 0] -> -4.298708, H0 (when every outcome that occurred lies on one side of both means,
  the remaining probability goes to the empty end outcome and the value is N x log(mean1 / mean0), or its
  mirror; a stop that looks only inside the outcomes that occurred, or calls empty outcomes "no
  information", fails; Fable's first recount script did exactly that, Astra caught it, it is repaired). The time of these runs is written down (it sets the fallback of R1).
- (b) The speed measurement for R3: as many one-thread engines at once as the match will run, elapsed time by
  paired opening and colour. BAR, declared before the timing (Astra): the 95 % interval of the speed ratio
  is no wider than +/- 1 % of the ratio (the 1024 match used 0.9447); if a repeat misses that too, no odds match
  is played and the comparison goes straight to equal clocks. (Not measured here: what 1 % of nodes is worth in
  Elo at this depth.)

**W4. The standstill test (N5).** Processor: 6,000 games at 250,000 nodes, about 1.8 hours with 12 games at once
(3,400 games an hour at round 67's confirmation), longer with fewer at once beside the loop.
- TEST: the three newest plain candidates at the moment it starts, each 2,000 games at 250,000 nodes against
  round 67's net, pooled; LB and UB are the ends of the pooled 95 % interval.
- BAR, four outcomes: LB above 0 and UB at or above +5: a gain of unsettled size; the best of the three is
  confirmed alone with a fresh seed before any promotion; no pause. LB above 0 and UB below +5: a gain under +5;
  the best may be confirmed; the 2 billion keep their priority. LB at or below 0 and UB below +5: a gain of +5
  is ruled out ("the three lost on average" is added if UB is below 0; "within +/- 5" only for an interval
  wholly between -5 and +5; Astra); the per-round training and gate may be paused until W8's trainer runs (a code change with its own test;
  the rows gained are timed). LB at or below 0 and UB at or above +5: inconclusive, nothing changes.
  A "depth effect" is claimed only if the difference between 50,000 and 250,000 nodes on the same three nets has
  its own lower bound above 0.
- Added in the extension (A13, Astra; agreed by all three): in the pooled
  interval an opening counts once. The three matches get three different declared opening seeds (the loop's
  matches pass `order=random` and `-srand <seed>` to the match program and draw from a book of 2,632,036
  different lines, so three seeds share about 1 opening in 3,000 by chance; equal seeds are refused). Before
  pooling, the three game lists are checked for shared openings, and the results of a shared opening stay
  together as one unit of the error (each candidate keeps the same weight in the pooled mean; the grouping
  changes only the error; Astra). Control with a known answer: one candidate's list of pair scores entered
  three times under three names must give the single candidate's interval, not one narrower by the square
  root of 3 (+/- 9 would be printed as +/- 5.2). The control's numbers, from a real match (Astra): round 52's
  1,000 pairs [20, 240, 456, 255, 29] give +5.73 [-3.2, +14.7]; entered three times and grouped by opening they
  must give the same interval; counted as 3,000 separate pairs they give [+0.57, +10.90], a "gain" made of
  three copies of one undecided match. The 50,000-node matches of the depth claim use the same three
  opening sets, and that difference is taken opening by opening.

**W5. Everything the rented server day needs, proven on the PC before the day is booked (P3b).** Build +
processor; rehearsed in the PC's Linux subsystem.
- (a) The program (N2). TEST: a Linux build script with all the loop's flags, three variants (AVX-512 with
  PEXT, AVX2 with PEXT, AVX2 without), each built twice. BAR: each prints the three reference numbers, the 12
  perft counts and the two known answers with the loop's net and settings (226187 / 616966), the net pinned by its file hash and
  its embedded checksum (Neon); the start script
  refuses a variant the processor cannot run (rehearsed with the wrong one on purpose); speed is compared by
  self-play, not by `bench`. Owner's direction, after the debate: full link-time optimisation against ThinLTO,
  two builds each. A fused AVX2 kernel is written only if the server has no AVX-512 AND the plain AVX2 build misses
  (g)'s rate (Neon).
  Added in the extension (N16, Neon; agreed by all three, the rule for an undecided timing in Fable's
  wording): THE PROFILE OF A PROFILE-GUIDED BUILD IS PART OF
  THE TEST. A build profiled on the wrong work passes every bar above. Neon built three programs from one
  source (no profile; profiled on `bench` with the net off; profiled with the loop's net, options and 30
  `selfgame` games): all three print the same known numbers, the wrongly profiled one makes 2.8 % fewer rows
  a second than the one without a profile and takes 4.8 % [3.7, 5.9] longer than the rightly profiled one
  for the same games; and a profile that is missing was dropped with a warning and exit code 0. The PC's
  own recipe
  (`loop/build_recipe/`) profiles with the net, the options and 60 `selfgame` games and stops when no
  self-play profile was written; it does not check the bench profile or what the optimised build did with
  the merged one. So: (1) the profile run uses the frozen net, the whole frozen option list and `selfgame`
  games; (2) the build FAILS when a profile file is missing or empty, or when the optimised build reports
  that it could not use the profile; compiler and profile-tool versions, flags, source and the profile's
  digest are kept; planted and required to fail: a missing profile and one from another source (Astra);
  (3) the speed is timed against the same build without a profile: two builds a variant, the order rotated,
  openings that were not in the profile run, equal rows a second of wall time at the day's real number of
  workers, and a repeat budget with three outcomes declared beforehand: measurably slower = the profile is
  wrong, it is repaired or the build without a profile is used; measurably faster = kept; neither = the
  rightly profiled build is used, as the owner directed, and the report says "gain not shown"; an undecided
  comparison waives nothing: the pilot of (g) must still meet its rate (Astra). In Neon's three
  rounds the build without a profile takes 1.85 % [-5.0, +9.2] longer than the rightly profiled one: not
  decided (Astra's interval). On the PC two builds
  of one source differed by up to 1.5 %, and the self-play profile gained 2.2 % in processor time over the
  bench profile in 9 of 10 rounds (the lab's notes of 15 and 17 November, not recounted for this debate). A
  timing from one machine is never quoted as a gain on another (Astra).
- (b) The start-up check of the live searcher (Astra). BAR: after the option list, one fixed search (new game,
  start position, depth 18) gives 375880 nodes and table fill 156; with Hash 32 on purpose (375868, fill 78)
  the start script refuses to start.
- (c) The package by scripts alone (the owner's condition 1). TEST: one start command on a small rehearsal.
  BAR: it checks itself first; it restarts a worker that was killed on purpose; it reports a full disk and a
  stalled worker (both made on purpose); it stops by itself at the set time; every step is in a log.
  Added in the extension (F3, Fable, sharpened by Astra; agreed by all three): the run goes on after the
  session that started it was closed on purpose. The allocator is killed on purpose twice: once after it has
  written a reservation and before it has handed the batch out, once after the hand-out and before the games
  are finished; after each restart no opening is handed out twice and no reservation is lost for good (its
  table is rebuilt from its own log; a retry may finish the same game, which is credited exactly once). The
  link home is cut for ten minutes; afterwards every piece arrives and none is credited twice. The PC's
  confirmation is held back on purpose after it has checked a piece: the server still holds that piece and
  deletes nothing the PC has not confirmed (the whole day is about 4 GB at the measured 2.01 bytes a row).
  Added in the extension (A11, Astra; agreed by all three): THE END OF THE LEASE is rehearsed too. The
  ten-minute cut is placed on the last transfer: the last, partly filled piece is sealed, the expected game
  ids are checked against the PC's receipts, a cut just before the last confirmation neither counts rows
  twice nor deletes an unconfirmed piece, and what is missing at the end is reported as a number. During the
  day the script recomputes the rate it still needs from the time really left: (target - rows verified at
  home) / (end of the paid time - now - the measured time for closing); if that is more than it delivers, the
  declared fallback starts (example: 2 billion in 24 hours need 23,149 kept rows a second; after two hours
  of set-up and with ten minutes kept for closing, 25,446). And the step that really ends the billing is the
  provider's own release or expiry, shown once; stopped engine processes do not prove it.
- (d) The packed game record as the transfer form (A1; measured once on 16,005,930 rows: position, move, ply and result
  equal on all of them, the score on the 15,255,460 kept rows, which is all the source file allowed). TEST in
  the rehearsal: the same comparison with the server's Linux converter on a run whose raw text is kept. BAR:
  0 differences in all five fields; a copy with one wrong final move and a correct checksum FAILS the content
  check. The report counts the games by the way they ended (draw adjudication, mate score, score limit);
  checksums are taken over the packed pieces, never over text, whose line ends differ between systems (Neon).
- (e) Transport and credit (A3; N8). The server sends EVERY row in closed, checksummed pieces as soon as each
  is closed; the PC checks, asks again on a mismatch, and filters at home (the filter only marks). BAR in the
  rehearsal: a piece delivered twice is credited once; a dropped piece is asked for again; a planted duplicate
  payload under a fresh delivery ID is recognised by row hashes over all five fields; an identical request
  under one manifest is credited once; two different histories or manifests with the same position both stay
  eligible. A game's identity for credit is the hash of its ordered five-field rows; when pieces are cut
  differently from the PC's rounds, the round boundaries that the PC's filter uses for its repeated-position
  rule are kept (Astra).
- (f) No paid search twice (N8 a; A7). One allocator process hands the workers their openings in batches and never
  hands one out twice inside one frozen producer; each game's eight opening moves are logged.
  - THE KEY of its table (A7, Astra; agreed by all three): the frozen producer + the whole FEN after the random
    plies + the positions since the last pawn move or capture, in order. Why not less: two openings with one whole
    FEN can give different games (Astra's two pairs: 0 rows against 127, and 81 against 67; reproduced by Neon and
    on the PC), because the engine's three readers of its position history go back exactly that far. Why not
    more: the eight moves in order keep 3 of the 132 copies seen in 300,000 draws of the opening rule; this key
    keeps 117 (what that draw showed, not a universal rate).
  - The en-passant field (all three): past positions as the engine's own key has them (a target only when a
    capture is legal); the current position keeps its target whenever a pawn stands ready to capture it, pinned
    or not, and drops it otherwise. Such a target changes the search although the position key is the same
    (Astra's pinned-pawn position, reproduced by Neon). The 40 copies this rule wins back against "every raw
    target" (77 of 132) replayed to identical games: 40 of 40 on Linux (Neon), and all 40 are inside the 129 of
    129 on the PC.
  - Seeding from older rounds (Neon, Astra): a record without logged opening moves seeds the table only where its
    halfmove clock is 0 AND the whole key can be rebuilt from the record (a printed target is used as printed;
    with none printed, only if no pawn stands where a hidden target beside a pinned pawn is possible); otherwise
    the record is skipped (the receiver still finds exact duplicate games).
  - Safeguard: refused requests are sampled and replayed; one replay with other rows makes the table fall back to
    the eight moves in order. Credit is given only by the receiver's verified rows (e).
  - Added in the extension (F4, Fable; agreed by all three): THE DAY NEVER
    DEPENDS ON THIS TABLE. A worker that gets no opening within a set time draws its own, as the PC's loop
    does, logs it under its own game id, and declines a late answer for a game it has started (Astra); the
    receiver's credit rule (e) removes the copies. BAR: with the allocator killed and not restarted for a
    declared interval, the workers go on, every verified game is credited once, and no finished game is
    played again. What the table is worth: 2 billion positions are about 16 million games (round 135: 124,412
    games for a round of 16 million rows); from 132 copies among 300,000 openings, growing with the square
    of the number of games, that is about 390,000 pairs with one whole FEN, of which between 55 % (16 of 29
    in round 136) and 89 % (117 of 132) are the same game: 1.3 to 2.1 % of the day, about 20 to 30 minutes of
    24 hours. So the table is the LAST part of W5 to be built, and the day is booked without it if it is not
    proven by then.
    Sharpened (Neon, Astra): the opening draws come from ONE root seed, made once for the run and kept with
    the manifest, and from each game's own id; a game id played again after a crash gets the same opening,
    two ids get draws that do not depend on each other (by chance they can still land on the same opening:
    1.86 % of 16.37 million draws did in Astra's fixture, so a whole healthy day is 98.14 % distinct). BAR,
    on the rehearsal's short outage fixture only, its game count and seed fixed beforehand (Astra): with at
    least four workers started in the same second, at least 99 % of the finished games are distinct, and two workers given the same seed on purpose must FAIL that bar (64
    workers with one seed would play one game 64 times and every other bar would still pass); a finished
    game id is never played again; the kept rows an hour during the outage meet the fallback's own pilot
    rate. The 20 to 30 minutes are a forecast: the two shares come from different counts (16 of 29 are pairs
    of positions without their move counters, 117 of 132 pairs of whole FENs).
    MEASURED by Astra on its own machine (16,370,000 openings drawn by the loop's rule, 768 games played with
    the frozen producer): 304,347 requests were repeats (1.86 %); a repeated opening cost 1.04 times the nodes
    of an average game [0.98, 1.11] (the bar declared before, within 0.90 to 1.10, was missed at the upper
    end, so the measured ratio is used): 28 minutes of the day [26.3, 29.7]. Seeding the table from home
    rounds adds about as much again (1.85 % of the requests with full move logs, 1.57 % with the careful
    importer) ONLY if those rounds were made by the same net, program and settings; for a new net or new
    settings on the server day that share is zero by design.
  - BARS in the rehearsal: with 2 random plies, 200 games and the table off, the receiver reports about 42
    copies; with it on, none; an exhausted opening space ends with a clear error; all four openings of Astra's
    two pairs are handed out (the two into the start position; `b1c3 g8f6 c3d5 b8a6 g1h3 a6b8 h3g1 f6e4` and
    `b1c3 g8f6 c3e4 f6g8 e4c3 g8f6 c3d5 f6e4`); the position `k1N1r3/2p3n1/8/3pP3/p4Qb1/P2p1B2/8/4Kn2 w - d6 0 23`
    gets another key than the same position without its target; the key of
    `f2f4 e7e5 f4f5 d8f6 e1f2 a7a6 g2g3 g7g5` holds the target g6; an importer given only the common FEN of the
    pinned-pawn case, with no move log, seeds no key from it.
- (g) The pilot rule (A3). The day is steered by verified, kept rows per second of paid time at the receiver.
  BAR: 2 billion kept in 24 hours need 23,149 a second; a deeper search or a stricter filter runs for the whole
  day only if the pilot's rate covers its own target; the fallback is written down before the day.
- (h) What the day plays, written down before the rental (N11): the one best proven net (R4), no second
  player; W1's values only if all five matches held, else today's list; 2,000 soft nodes; games end at 2000
  unless W10's "cut at 1000" net passed. Anything else only after a pilot declared before and succeeded. If W13's
  trainings on 2 billion are unfinished or inconclusive when the rental comes (Neon): the proven configuration, or the day is moved.
- (i) BAR for the whole of W5: one end-to-end rehearsal at small scale, started by one command and not
  touched until it has stopped by itself, with (a) to (f) passing inside it.
  Added in the extension (N12, Neon; agreed by all three): inside it, ONE worker that stays alive plays a
  fixed, ordered batch of at least four openings (games ending by draw adjudication, by the score limit and by
  a rule among them) through the real launcher, packer, transport and unpacker, and every game, the first AND
  the later ones, equals the PC's Windows program on the same batch with the day's frozen settings: 0
  differences in the five fields and in the end line (reason, plies, searches, nodes), compared before the
  filter marks anything. Two planted faults must FAIL: the new-game command left out between two games (the
  engine clears its tables only on that command: `source/src/uci.cpp` 448 to 499 and 873 to 875; Neon's run
  gave 43 rows where 101 are right), and one changed game setting that changes a frozen game (`writeminply 9`;
  Astra). The reference batch is made again whenever the settings change (W1's values, a new best net). The
  PC's own driver sends that command before every game (`pipeline/nnloop/datagen_uci.py` 401, not on this
  branch); a launcher written new for the server has to be shown to do the same.
  The fixture exists (Astra `20261123T053252Z`; Neon reproduced it to the last digit on its own Linux
  build): six openings in one process (N12's two, the threefold pair, the 81 / 67 pair), with rows, ending,
  searches and nodes 86 drawadj 86 302461; 101 drawadj 101 383484; 0 rule 0 0; 127 evallimit 128 530258;
  81 drawadj 81 307107; 67 rule 67 227258; game 2 without the new-game command: 43 rows, rule, 152827
  nodes; game 2 with `writeminply 9`: 100 rows, the same 101 searches and 383484 nodes; and a SHA-256 of all
  rows of game 2 for each of the three. A game with no rows keeps its id and its end line is checked apart.
  The Windows run of the same six games on the PC is DONE (Fable, during the debate; Astra's numbers were typed into the tool before its first run): the PC's Windows program gives the same rows, end reasons, searches and nodes in all six games and the same digest over every row of game 2; both planted faults change game 2 exactly as on Linux (43 rows; 100 rows; digests equal) and leave the other five games alone; a second process repeats all of it row for row (`debate/evidence/fable_n12_sixgames_windows.txt`).
  Added in the extension (A14, Astra; agreed by all three): THE RULES THAT CORRECT
  A GAME'S RESULT AFTER IT ENDED are part of the rehearsal. On the PC the driver relabels a drawn game whose
  last position is a won ending (`pipeline/nnloop/datagen_uci.py` 320 to 339 and 441, not on this branch; the
  endgame tables, 291 files, 0.9 GB, lie on the PC). In round 137 that was 947 of 124,544 games (0.76 %)
  holding 249,706 of the round's 16,009,233 raw rows (1.56 %),
  every one through the tables (474 after the ply limit, 464 after the fifty-move rule, 6 after a draw
  adjudication, 3 after a third occurrence; `debate/evidence/fable_a14_after_game_rule_round137.txt`), and a
  relabelled game carries the new result on all of its rows. When the tables cannot be opened, today's driver
  writes one line into a side file and goes on with the plain draw: nothing in the rows shows it. So, before
  the rehearsal: (1) it is written down which machine applies the rule. If the server does (the package of
  the plan's P3b: the PC's own driver with its tables), the table files travel with the package, their hash
  list is checked at the start, and a worker whose tables did not open STOPS instead of noting it. If the PC
  does, the server sends the engine's own end record and everything the rule reads, and needs no tables.
  (2) A frozen list of real games from a PC round goes through the whole path: one that the tables relabel,
  one that the material rule alone relabels if a round has one, one true draw that stays; every kept row's
  result must equal the PC's. With the tables hidden, and with the rule switched off, the run must refuse or
  disagree with the PC's rows; delivering the draw without a word FAILS. (3) Every piece carries its count of
  relabelled games, and the receiver checks it: none among 10,000 games is a FAIL (76 are expected).
  The frozen list holds the three combinations that round 137's log shows in its first three lines: Black to
  move and Black wins, Black to move and White wins, White to move and Black wins, so that a handler which
  takes the tables' answer for the side to move as the result for White cannot pass on one example (Astra).
  The engine's own result and end reason stay stored beside the corrected result. A probe that FAILED is
  recorded apart from a probe that answered "draw", and a single failed probe is shown even when other
  games of the piece were relabelled.
  Added in the extension (N15, Neon; agreed by all three): AN OPTION THAT DID NOT ARRIVE STOPS THE START. The
  engine answers a misspelt option name, a value out of range and a misspelt boolean with one `info string`
  line, says `readyok` and plays on with the default; an option line that is MISSING gives no line at all. Of
  the 21 options of the frozen list that are neither a path nor the thread count, 19 change the known node
  counts of (a) and (b) when left out; two do not: `OwnBook false` and `MateAlphaGuard true`. Without the
  guard all six games of the fixture above stay the same, while 57 of the 64 games of Astra's sample that
  ended by a mate score change (Neon; a selected subset, not a share of the day's games: Astra). So (1) the
  server's start script reads every answer line up to `readyok` and refuses to start on `unknown option`,
  `invalid value`, `ERROR`, `cannot load`, `invalid FEN`, `illegal move` or `sgerror` (the PC's own match and self-play code has refused such lines
  since 16 November; the server's start gets the same); planted and required to FAIL: one misspelt name, one
  value out of range. (2) The option lines actually sent are compared with the frozen list, line by line, in
  number and values, and with the names and bounds of the engine's own `uci` list (Astra). (3) A seventh game
  joins the fixture, opening `h2h4 b7b5 g2g4 g7g5 h1h2 c8a6 e2e3 d7d5`: with the guard 172 rows, 173 searches,
  741342 nodes; without it 171, 172, 737195 (Neon, the same on two Linux builds; Astra the same on its own, with the line left out and with `false`;
  digests in their messages; the
  PC's Windows program gives exactly the same: all three arms, both digests, and one refusal line with
  `readyok` and exit code 0 for a misspelt name, a value out of range, a value that is no number and a
  misspelt boolean; the numbers were typed into the tool before its first run:
  `debate/evidence/fable_n15_guard_game_windows.txt`).

**W6. The card test before paid card hours (N8 b).** Needs a short rental or loan of an NVIDIA card.
- TEST: one pass on one round there. BAR: the exported net loads on the PC and the PC's trainer-against-engine
  check passes on at least 1,000 named positions; peak memory and rows a second are read. If the teacher stays
  (W11): the hand-written evaluation's Linux build gives the same values as the Windows one on 3,000 positions.
- Added in the extension (A8, Astra; agreed by all three): the UPDATE is compared, not only the
  export (a trainer that skips every update still exports a net that loads and agrees with itself). From the
  same weights and optimizer state, the same rows in the same order, a few optimizer steps on the PC and on
  the rented card: the CHANGES of the predictions on fixed probe positions and the size of the update of each
  group of weights agree within a tolerance set before from the PC's own spread between two runs; the
  reference change is clearly larger than that tolerance; a run with the learning rate set to zero on purpose
  FAILS; a group frozen on purpose stays frozen. And (Fable, a fact of the PC's trainer, which is not on this
  branch): its log on the rented card must show the same `... USED` lines as on the PC, because a kernel step
  that refuses itself there goes on by itself with a slower step (on the PC's card 0.79 ms a step against 1.43
  or 2.24 ms for the two steps it falls back to); only that line shows it, and it changes what the card hours
  cost.
- Added in the extension (A10, Astra; agreed by all three): one round is not the size of the job. On the
  card and data path that will be paid for, a short run at the FULL shape before the long booking: either
  the full-size tensors are allocated and touched with the optimizer's state and one update and export run
  beside them (2 billion rows at 40.8 bytes are 81.6 GB = 76.0 GiB for the rows alone, on a card of 80; the
  PC's rounds 19 to 21 measured 50.3 bytes a USED row where the first session had given 44.7; the trainer
  uses about 91 % of the kept rows, so that is 45.9 against 40.8 bytes a kept row, about 92 GB = 85.5 GiB
  for 2 billion kept rows, and 100.6 GB = 93.7 GiB if all 2 billion were used rows (Astra's unit check);
  the two byte figures are from the lab's notes, not recounted for this debate; the measured full-shape
  allocation is the bar, not any of these), or,
  with W8's disk feeder, the full row count and the real batch size are streamed from pieces that were not
  read before, and load, transfer and update are timed. Reported apart: peak card memory, peak main memory
  with no swapping, the read rate of the disk (4.445 million rows a second at 44 bytes are 196 MB a second),
  the `USED` lines, cold against warm. A budget set too small on purpose must be refused before the long
  run. The WHOLE paid job is then projected against the owner's allowance: set-up + a cold first pass + 39
  warm passes + checkpoints and export + the checked download. A borrowed card shows that it runs; only the
  card that will be paid for shows what it costs.

**W7. Which rounds count toward the 2 billion (P11; A5).** Processor, about 3 hours; nets are trained.
- TEST: "breadth" (every second row of rounds 29 to 78) against round 78's own candidate (every row of rounds
  54 to 78; 346,393,625 rows against 346,976,049), 250,000 nodes, 2,000 games fixed, 8 at once: as declared on
  the PC on 20 November before the net existed. Its error is about +/- 9 and both guesses written there are
  +2, so "inconclusive" is the likely word.
- BAR: lower bound above 0: that mixture may count. Upper bound below 0: recent rounds only. Anything else:
  inconclusive, the rounds of the current net are the practical default (not evidence that older rows hurt).
  If breadth wins, a stride control (same rounds and quota, only the sampling inside a game differs) follows.
  In every case the manifest of the 2 billion lists per round the nets, program and result rules that made it,
  and rounds 1 to 28 get their own decision.

**W8. The trainer that reads 2 billion positions from disk (P3; A2).** Build, about 5 card hours of tests.
- TEST: the store is made and timed; then read as the real training would, same rows, batch size and steps as
  today's trainer; one run with a cold file cache. The most disk used is reported against the second disk's
  floor of 30 GB free (Neon).
- BAR: 4.445 million rows a second or more (else the plan quotes the measured duration, not "about 4.2 hours");
  the row ids and counts the sampler visits equal the declared ones; one dropped piece and one doubled piece of
  equal length are each refused before training starts; the round mix of the batches matches a declared
  reference shuffle on a fixed fixture, and a reader that walks the rounds in order FAILS that check; on today's
  388-million window it gives a net whose hold-out loss is within 0.0001 of today's trainer's.
- Added in the extension (F2 and F6; Fable, the test's final form by Astra; agreed by all three): THE NEW
  TRAINER'S NET IS ALSO JUDGED BY GAMES (R5) against the net of today's trainer on the same window. Written
  down before the training: the row ids, recipe, seed, opponents, and two separate blocks of opening pairs
  for 20,000 games each (Astra). The test: a paired SPRT between -5 and 0 at 250,000 nodes (alpha = beta =
  0.05), ONE test of at most 40,000 games. The stop is the checked function of W3 (a) over all pairs so far,
  looked at after every 1,000 games; a stop inside the match program is not used, because nobody held its
  statistic against the known tables. H1 at any look = the trainer may be used for the 2 billion. H0 at any
  look = not used, and never played again; a found defect with a changed build is a new candidate with a new
  test. No boundary at 20,000 games = a pause for the hunt for a cause (the trainer's own checks above, the
  hold-out loss, the row ids); if nothing is found, the SAME test goes on with the second block and keeps the
  first block's evidence (the look at 20,000 is an ordinary look). No boundary at 40,000 = not qualified.
  What to expect (Astra's simulation of exactly this rule from the pair counts of three of the loop's own
  2,000-game matches at this depth, pooled [55, 713, 1399, 760, 73],
  `debate/evidence/fable_f2_deep_pair_tables.txt`; 20,000 runs a point; its counts recomputed by Neon): a
  truly level trainer passes in 96.4 % and stays undecided in 0.5 %, after 10,400 games on average = 3.0
  hours at 3,400 games an hour, at most 40,000 games = 11.8 hours; one truly 5 Elo weaker passes in 3.2 %,
  one 2.5 weaker in 45.7 %.
  Added in the extension (A15, Astra; agreed by all three): THE PROGRAM THAT
  STOPS, PAUSES AND RESUMES THIS MATCH IS TESTED FIRST, with made-up pair records and no games, through the
  real entry point. Per 1,000-game look the same 500 pairs, every pair with an opening id of its own:
  (A) [10, 122, 240, 118, 10]: no stop at 20,000 games (+2.873966), the pause, and after the resume the first
  H1 at 21,000 (+3.017664, 10,500 pairs). (B) [10, 123, 240, 117, 10]: no boundary up to 40,000 (+2.151448) =
  not qualified. (C) [10, 126, 240, 114, 10]: the first H0 at 14,000 (-3.023972), and a winning block handed
  in afterwards must not reopen it. Planted and required to FAIL: a fresh table after the pause (it sees
  +0.143698 at 21,000 and never stops on A) and the bars -3 / 0 (+0.179891 at 21,000). At every look the
  program prints the five pair counts so far, the number of finished pairs and the unrounded statistic, and
  all of them are compared, not only the decision; no block may count twice (Fable, Astra): a program
  that counts the first block a second time at the resume gives the SAME decision at the same look on A
  (H1 at 21,000, with +5.891631 instead of +3.017664); it shows in the value there and on B, where it reports
  H1 at 35,000. All values recomputed with Fable's own stop function and by Neon with a third program:
  `debate/evidence/fable_a15_fixtures.txt`.
  For comparison only, these are NOT rules: stopping for good at 20,000 games would send back one sound
  trainer in eight (H1 87.7 %, no boundary 9.2 %, H0 3.1 %); a fresh run after any failure (Fable's first
  form) lets a trainer 5 Elo weaker pass in 5.6 %; a fresh run only after an undecided one gives 95.8 % and
  3.1 % but throws 20,000 games of evidence away; with a look after every pair the 20,000 form ends about
  1,500 games sooner.

**W9. Before any net wider than 1024 (N3).** Build. The 1024 net itself is safe (1.55 % of room).
- BAR: the sums are widened before they are added, the loader checks the bound, `MaxHidden` is raised
  (`source/include/forge/nnue_v3.hpp` 65; Neon), a made-up worst-case net gives
  equal raw sums on all three kernels for both signs, and the reference numbers, the two net checks and the
  checking build are repeated.
- Added in the extension (N14, Neon, sharpened by Astra; agreed by all three): those three kernels are not the
  path the search uses. The search evaluates through the fused update
  (`source/src/search.cpp` 3393 -> `apply_pair_and_evaluate`, `source/src/nnue_v3.cpp` 444 to 516, 895), with
  one loop for quiet moves and one for captures; `eval` and the kernel comparison never enter it
  (`source/src/uci.cpp` 1208; `nnue_v3.cpp` 809 to 819). So the worst-case net (both signs) AND a second,
  uneven one (different columns touched by the move, different weights for the two colours: a skipped update
  of a constant column is invisible otherwise) are checked through the fused path for a quiet move, a
  capture and the fallback (castling), on the RAW sum before it is clamped (a wrong but still large sum
  prints the same +30000) and on both child accumulators against a fresh computation; and both nets are
  searched in the checking build. The loader's bound is the narrowest lane's: at weights of 127 one 32-bit
  lane holds 260 terms (2,147,483,647 / (255 x 255 x 127)), so the AVX2 sum of one side is safe up to a width
  of 2080 and overflows at 2112, the AVX-512 one at 4192. The same checks hold for a fused AVX2 kernel if W5
  (a) ever needs one.

**W10. The first filter experiment (P3c; N4).** Card: three trainings; processor: two matches.
- TEST: three nets on equal row counts, uniform samples of the same rounds of round 67's net, same recipe and
  seed: today's filter; score-tail thinning (keep probabilities per score band locked before training; the piece mix untouched and
  captures under the same rule; Neon); "cut at
  1000" built Astra's way (the crossing row and all after it left out, earlier rows relabelled with the
  counterfactual result, the production filter run again). Each against the control, 4,000 games at 250,000
  nodes.
- BAR: a treatment is adopted as a training filter only with a lower bound above 0.
- "Cut at 1000" has a second use: ending self-play games earlier. ONE advance criterion for it (Astra's
  question; agreed by Astra and Fable, and one of the two options Neon named): the same lower bound above 0, in the same match. A rule that changes every
  self-play game needs a shown gain; a level result leaves the games ending at 2000. After it, in this order:
  a live pilot in which the kept rows per hour are TIMED end to end (never computed from the share of rows the
  cut drops), then R1 for the net trained on the pilot's rows against
  its control, before the rule stays.

**W11. The teacher (N9).** Card: one training; processor: one match.
- TEST: today's window, 768 wide, same rounds, seed and recipe, teacher weight 0.2 against 0; 4,000 games at
  250,000 nodes. BAR: if the interval crosses zero the recipe stays for now; both versions are prepared for the
  2 billion, and R6 decides there.

**W12. The training recipe (P5; N11).** Card + processor, when the card is free.
- TEST: one matched pair outside the loop (same rounds, rows and seed; only the recipe differs), 4,000 games at
  250,000 nodes. BAR: lower bound above 0 to prefer the new recipe; R6 for the 2 billion. (Replaces the
  four-round trial in the loop.)
- The TD twin (Neon: it must not drop out): round 82's candidate, trained with smoothed labels, against its
  twin trained on the same rounds with plain labels; both nets exist. It is played in the match slot after W7.
  BAR (Fable looked during the debate: the twin's folder and the log of its training hold no declaration of
  this match; a declaration found before the match stands instead): 4,000 games at
  250,000 nodes and a lower bound above 0 = smoothed labels become one arm of the pair at 2 billion (R6);
  anything else = recorded, no further trial in the loop.

**W13. The first trainings on 2 billion (P11, P4; A6).** Rented card or the PC with W8's trainer.
- (a) 768 wide. TEST: against round 67's net by the loop's gate and confirmation, with a direct SPRT at 250,000
  nodes run beside the old gate. The result is recorded whatever it is.
- (b) 1024 wide on the same rows, recipe and seed. Needs W8's verified store, W6's checks and a technically
  valid (a); it does NOT need (a) to have beaten round 67's net. TEST and BAR: R3, with both opponents named
  (Astra): the width SCREEN is 1024 against the matched 768 of (a) (R3's first stage, with node odds); the
  ADOPTION match is 1024 against the proven best net of that day with equal clocks (that 768 if it
  was adopted, round 67's net if not; R3's second stage); then R1 and the speed count. A failed screen or an inconclusive adoption match leaves
  width unresolved. Its cost is taken from a timed 1024 pilot. If it is put off for cost it is recorded as "width at 2 billion: not tested".
- What the paid card hours go to first, (b) or deeper labels, is the owner's choice.
- What would change the direction, with its margin declared now (Astra): "volume at 2,000-node labels is not
  the lever" is said only if the direct matches of BOTH (a) and (b) against round 67's net have 95 % intervals
  lying wholly between -5 and +5 (about 9,400 games each at 250,000 nodes give +/- 4 as a planning figure; the decision uses the intervals
  measured from the opening pairs). A net that merely
  failed to be promoted shows nothing of the kind. Then the next lever is the depth of the labels.
- Added in the extension (A12, Astra; agreed by all three): that sentence is about round 67's net, not about
  volume. "These two nets did not beat round 67's net by 5" and "more positions do not help" are different
  claims: a matched small net could lie at -8 and both 2-billion nets at 0. So "volume is not the lever" is
  said only from a matched pair: the 2-billion 768 against a 768 trained at the same time on a declared
  388-million subset of the SAME rows, same recipe, teacher, filter and seed, with the contrast named before
  (equal passes = the package as it would be used; equal steps = more different rows at the same work; agreed:
  equal passes is the contrast the decision uses, equal steps stays a separate question; the two nets are
  trained on two different cards, so W6's update check is run between them and the difference is recorded), and
  that pair's own interval inside the declared margin. That control fits the PC's card (2,917 seconds for 40
  passes at 388 million), so it costs no paid hour. Without it the plan records the result against round
  67's net and the next budget choice, and no sentence about volume.
- Added in the extension (A9, Astra, with Neon's two additions; agreed by all three): no paid training starts
  without a tested way to stop and go on. Today's trainer cannot do it: it saves the weights only (at the
  end, and at the ends of its rate cycles if asked), no optimizer state, no place in the schedule, no random
  state and no place in the data (Fable, from the PC's trainer, which is not on this branch); a restart from
  such a file repeats or skips batches and still gives a net that loads. TEST: one short run is split after
  step k; one arm goes on, the other is stopped, loses its work disk, takes the last complete checkpoint from
  storage outside the rented machine and goes on. BAR: the same next row ids and learning rates, the same
  step count, predictions and updates within W6's tolerance; a checkpoint write that is cut off leaves the
  one before it as the newest complete one (written under another name, then renamed); before the machine is
  given back the final checkpoint and the exported net are read again from that outside storage, their
  SHA-256 and the net file's own checksum (`source/src/nnue_v3.cpp` 627 to 629) are checked and the PC's
  export check is run. The checkpoint interval is declared before the long run (one a pass = about one pass
  of work at risk), with its measured size and transfer time.

**W14. The first search bundle (P7; N7, A4).** After W1. Build about a day, then R2's matches.
- Candidates, each behind a switch that is off by default: no SEE pruning of quiet moves that give check; no
  reduction for a missing hash move at the root; the history term of the reduction without its dead zone (only
  if W1's final divisor leaves one); no SEE pruning of checking captures in quiescence; and the switch
  `LmrDeeperShallower` that is already in the source.
- TEST and BAR: R2, on W1's final settings. Before any game: the composition and every rounding are written
  down, and an item that changes the node count on fewer than 6 of the 600 positions is left out and listed.
  (The number 6 is a convention declared here, before the sweep, at Astra's request; no measurement stands
  behind it. Node counts measure activity; the matches decide strength.)
  Before the bundle enters self-play or any timed play, the program is built again with the adopted switches
  ON in its profile run (N16, Neon): the PC's recipe records a program whose profile had not seen a switch
  and that ran at half speed with it on (0.487 against 0.984).

**W15. Correctness duties that stay (P8; N6).** Every build: the three reference numbers, 12 perft counts, every
option checked against the program's own list, a checking build with a planted fault that must be caught, a
second reader for every change that enters the loop. Added, each with its test first: `go perft` works when a
requested net failed to load; openings are given as start position plus moves, and the rehearsal compares each
row's ply with the position's own counter; two repetition wrappers without a caller are removed and the missing
guards get a per-position test (expected: no node count changes); the fixed draw score 0 is checked against
`DrawJitter` at the tune's final values; a comment states the contract near the 50-move limit. Known and written down,
not repaired unless the repair is free: an en-passant capture by a pinned pawn is in the move list before the
legality test, and the search of one position then differs with and without the target (Astra's position: 797
against 789); the opening key accounts for it (W5 f). Where it enters (Fable by reading; Astra by a trace and by
a control that removes it): the capture list holds the illegal capture (`source/src/search.cpp` 1030 to 1053);
the picker's selection swaps run over the whole list (960 to 964, 989 to 996) and leave another of two equally
scored legal captures in the fourth place at the root; the legality test comes after the pick (2228). With only
that one candidate skipped before the scoring, the run with the target equals the run without it byte for byte
(Astra). The live search keeps its behaviour.

**W16. Put off, with the reason.** A second player in self-play (P6): four rounds would show the trainer only
0.10 x its share; if ever, outside the loop at full dose. Tablebase probing inside the search: +18.6 in endings,
but 3 % slower self-play. More than one thread, and time handling without an increment: never measured here.
Decided against, unless new evidence comes: dropping positions whose best move is a capture; a net as its own
teacher; judging a training by its hold-out loss.

## The order by resource

- Processor: the loop and W1 (running) -> W1's matches 1 to 3 -> W3's runs -> W1's matches 4 and 5 -> W4 -> W7 -> the TD twin (W12) -> the matches of W10 to W12 as
  their nets are ready -> W14. W8's match of the new trainer's net (F2, F6: 3.0 hours on average, at most
  11.8) is played as soon as that net exists and goes before the matches of W10 to W12, because the paid
  card waits for W8.
- Build: W2 (minutes) -> W3 (while W1's first three matches play) -> W5 (the largest piece; it decides whether the server day can be booked) -> W8
  -> W9 only when a net wider than 1024 is wanted.
- Card, between the loop's trainings: W8's tests -> W10, W11, W12 (one at a time).
- Paid: the server day only after W5 (i); the card only after W6 and W8.

## What is still open, with both sides

- Nothing is in dispute. Every objection to the two drafts of this text was either written into it or
  withdrawn by its author, and neither Astra nor Neon had a dissent left on the second draft (Neon
  `20261123T051650Z`). A DISSENT written in a final vote is put beside its item, word for word.
- The count: 37 proposals (15 Astra, 16 Neon, 6 Fable), none rejected. 32 are written into the items above;
  5 are tests that can only be run after the debate and stand in their items with the bar written beforehand.
  Remedies of Fable's were shown wrong by Astra and replaced (the opening key; the repeat of the trainer's
  match), and a fault in Fable's own evidence script was found by Astra and repaired; the corrections are
  listed on the board.
- Eighteen of the 37 came in the two more hours the owner gave: F2, F6 and A15 (W8), F3 and A11 (W5 c), F4
  (W5 f), N12, A14 and N15 (W5 i), N13 and F5 (W3 a), A8 and A10 (W6), N14 (W9), A9 and A12 (W13), A13 (W4),
  N16 (W5 a, R3, W14). All eighteen are agreed by all three.
- After the two hours (the owner, to all three): Astra and Neon may go on between themselves until one of
  them runs out of credit; Fable reads the branch every 30 minutes and writes a change that both agree on,
  with its proof checked, into the ADDENDUM at the end of this file. The items above are not rewritten.
- The choices that are the owner's: what the paid card hours go to first (the wide net or deeper labels,
  W13), and the dates and prices of the rentals.

## What was measured on the PC for this debate

All in `debate/evidence/`: the packed record's round trip on a whole round; the switch of A4 is the rule of the
old match; pieces against score on a whole round; the live-search pin on four programs; games per opening and
who wins after a high score; the opening key (the 29 pairs, five fields, the opening rule drawn 300,000 times,
130 replayed pairs, Astra's two pairs of openings with one whole FEN and different games, the key that survives
them); the soft-node fixture. In the extension: the stop's four known tables and the two one-sided ones recomputed (N13, F5) and the made-up matches of A15; the old run's pair counts (R1) and the pair tables of the loop's own deep matches (F2); the tune's, the breadth match's and the TD twin's declarations held against the plan (W1, W7, W12); the after-game rule counted on round 137 (A14); Astra's six test games and Neon's seventh on the PC's Windows program, each with the expected numbers typed in before the first run (N12, N15). Corrections of our own numbers are listed on the board.

## Addendum: changes agreed by Astra and Neon after the debate's end

Kept by Fable. An entry is made only for a change that Astra AND Neon both agree on in a message
`..._<name>_agreed_<item>.md` (final wording, proof, both votes), after Fable has checked the proof. Each
entry names the item above that it changes; the item's own text stays as it was voted.

The final votes on the text above (each in its own message `..._<name>_final.md`): Fable
`20261123T132211Z`, Astra `20261123T062329Z`, Neon `20261123T062351Z`. All three: AGREE on every item, R1 to R6
and W1 to W16. No dissent. Before the final text was issued, Astra (`20261123T061957Z`) and Neon
(`20261123T062130Z`) each wrote that they had nothing more to propose. The debate closed at 2026-11-23T13:26:21Z
(Fable's clock).

### Changes to the items above

The first five entries (four here, one in the second list) were entered at 2026-11-23T14:32:48Z (Fable's clock). Each
entry: the items it changes, the message that holds the agreed wording and both votes, what is required, the
proof, and what Fable's own check showed and did not show.

- **A16 (changes W2, W3 (a) and W8; Astra, form with Neon). The match runner counts every game exactly once.**
  Agreed wording: `20261123T064956Z_astra_agreed_a16.md` (Astra `064019Z`, `064928Z`; Neon `064747Z`).
  - The production runner's raw-result and restart path identifies each game by its declared match, its scheduled
    opening occurrence and the candidate's colour. An identical retry counts once; a conflicting retry is refused;
    a scheduled look is made only when its whole prefix of opening pairs exists. Two scheduled occurrences may
    hold the same position: equal FENs are not one game.
  - Tests on made-up records through the runner's real entry point: games that finish out of order; a missing and
    a duplicated result in the same outcome class; a late missing result after a restore. 1,000 interleaved
    finishes give [250, 0, 0, 0, 250] and +0.018639 with no stop, whatever the order of arrival. At W8's look 21
    a duplicated win-win pair that leaves all five class counts nominal leaves only 10,499 distinct pairs: no
    look is due (that partial state stands at +2.928513); the pending pair counted once on arrival gives
    +3.017664 and H1, once, at 10,500 pairs.
  - A result summary is read as ONE complete block in the frozen orientation of the candidate: games = wins +
    losses + draws = 2 x completed pairs, and pair half-points = 2 x wins + draws. A run of 1,000 or 2,000 games
    that was cut off without a boundary is recorded as partial; "complete" needs the declared cap or the
    runner's own final verdict. A mixed or truncated summary must be refused.
  - Fable's check (`debate/evidence/fable_a16_check.txt`): all five numbers recomputed and equal. The plan's own
    evidence reader let the planted mixed summary through; it is repaired
    (`debate/evidence/fable_f2_pair_tables.py.txt`) and its six historical records are unchanged. Not shown by
    anyone yet, and owed by the agreed text: the end-to-end rehearsal on the live runner.
  - Cost: made-up records, processor seconds, no games.

- **A17 (changes W8; Astra). The new trainer's reader is checked for games, not only for rows.** Agreed wording:
  `20261123T065016Z_astra_agreed_a17.md` (Astra `064306Z`, `064928Z`; Neon `064747Z`).
  - At the real sampler's output, on a fixed fixture: row coverage and the round-composition checks stay. Added,
    with game numbers that exist only in the test: the mean share of same-game pairs inside a batch, the sum
    over games of n(n-1) divided by B(B-1), is held against a reference declared before for the chosen policy,
    seed and batch size. A shuffled reader (the control that must pass) passes; a reader that keeps blocks of one
    game in time order while matching every round count must fail.
  - Astra's fixture: both readers visit all 8,192 rows exactly once and give 16 rows per stratum in all 64
    batches; the reference holds 82.484375 distinct games a batch and a share of 0.007353054257, the planted
    reader 8 games and 0.118110236220 (16.06 times as much). Where the new reader's ordered row sequence can be
    shown EQUAL to the trusted reader's, that stronger check is used instead.
  - No production threshold and no Elo gain is claimed; W8's strength gate stays the decision.
  - Fable's check (`debate/evidence/fable_a17_check.txt`): the fixture rebuilt, all six numbers equal; 200 other
    seeds give 0.006992 to 0.007588 (the plant is 15.6 times the largest). The PC's trainer of today draws one
    random order over the whole window for every pass, so today's reader is of the shuffled kind; the check is
    for the reader that W8 builds.
  - Cost: processor seconds, no games.

- **N17 (changes W5 (a) and (i), W6, W9 and W15; Neon). A net that was asked for and is not the one that
  evaluates must stop the program, on every path.** Agreed wording: `20261123T065155Z_neon_agreed_n17.md`
  (Neon `064748Z`; Astra `065058Z`).
  - Checks that need no source change (in force before W15's repairs):
    - W5 (i): the start script sends `setoption name UseNNUE value true` (or refuses `UseNNUE false` together
      with `NNUEArch true`) and keeps the frozen order, `NNUEArchFile` before `NNUEArch`, so that N15's stop on
      an `ERROR` line is not tripped by the line the program prints when the switch comes first (`uci.cpp` 977).
    - W6: the trainer-against-engine check proves WHICH evaluator answered: the line
      `info string NNUE v3 active:` with the checksum of the exported file, no `ERROR` line, one fixed known
      position whose value is not near zero, and on every probe position the three fields
      `hce 0 nnue X total X` (never `total` alone). A planted file with a wrong checksum must fail `isready`
      with exit code 2 and an `ERROR` line.
    - W6 / W9, before W13 (b) uses a 1024-wide net: the AVX-512, the AVX2 and the plain build (with
      `-DFORGE_NNUE_V3_VERIFY=1`) give the same values, the same `bench 11` and the same `selfgame` rows on a
      1024-wide fixture, among its cases `b1 = 255, w2 = +/-127` and `max|b1| + 32 x max|w1| = 32767`; the
      reload 768 -> 1024 -> 768 in one process and the published known answers stay.
  - Repairs of the source under W15, each with a test that fails before the repair and passes after it:
    - `uci.cpp` 1203 (`eval`): with a requested net that cannot evaluate it prints the `ERROR` line and ends
      with exit code 2, as `isready`, `go`, `bench` and `selfgame` do.
    - `nnue_v3.cpp` 704 (`problem()`): `NNUEArch true` together with `UseNNUE false` (or with no usable
      evaluation) is a problem, so the program can no longer print "NNUE v3 active", answer `readyok` and
      evaluate by hand.
    - `nnue_v3.cpp` 589: the net path must be a readable regular file, and a read that fails ends in the
      loader's own error.
    - `uci.cpp` 976: `NNUEArch true` before a file is named prints the notice that `isready` already prints for
      that state, not an `ERROR` line; real load errors and `go` / `bench` / `selfgame` / `eval` stay loud.
    - `nnue_v3.cpp` 617: the loader itself refuses a residual net in a stand-alone build (or every consumer
      does), so that no caller can get one past `uci.cpp` 1002.
  - Proof by both, on untouched Linux builds with the branch's net: a missing file, the switch on, then `eval`:
    an `ERROR` line, then `hce 18 nnue 20 total 38` and exit code 0 (the same with `isready`: exit code 2);
    `UseNNUE false` with the net on: "loaded", "active", `readyok`, then `hce 18 nnue 0 total 18`; the switch
    before the file: an `ERROR` line, then `hce 0 nnue 87 total 87`. By Neon alone: on Linux a folder given as
    the net file ends the program with an uncaught exception; four builds agree bit for bit on the 768 net and
    on a made-up 1024 net; with `UseNNUE false`, `bench 11` gives 375354 instead of 226187.
  - Fable's check: the five places in the source read (`source/` on this branch is the source of the PC's program): they are
    as described. On the PC's own Windows program (the loop's, the same file as `loop/forge.exe`;
    `debate/evidence/fable_n17_a18_check.txt`): the control, the missing file with `eval` (two `ERROR` lines,
    then `hce 18 nnue 20 total 38`, exit code 0) and with `isready` (exit code 2, no `readyok`), `UseNNUE false`
    (`hce 18 nnue 0 total 18` after "active" and `readyok`) and the switch before the file (`ERROR`, then
    `hce 0 nnue 87 total 87`) all come out as reported. A folder as the net file does NOT end the Windows
    program: it answers `cannot open`; that fault belongs to the Linux builds, which is where the rented server
    runs. Two facts of the PC: its trainer-against-engine tool reads the field `total` alone
    (`pipeline/tools/v3_model_check.py` 72), so W6's part changes a tool that is in use; and the loop sends the
    file before the switch and never `UseNNUE` (`nnloop/engine.py` 76), so today's loop is not hit. Not checked
    by Fable: the four builds on a 1024-wide net and the `bench 11` figures (Neon's alone).
  - Cost: processor seconds for the fixtures and small guards in the source; no card, no games.

- **A18 (changes W1 and W14; Astra). A count of "how many positions does this setting change" starts every
  position from a fully reset program.** Agreed wording: `20261123T071114Z_astra_agreed_a18.md` (Astra
  `065145Z`, `071057Z`; Neon `070959Z`).
  - Before an option's per-position node counts are used to keep or to drop it (W1's table at the final values;
    W14's "fewer than 6 of the 600"), every independent position in every arm is searched after `ucinewgame`
    (or in a fresh process shown to be equal to it), and the nodes are stored with the position's identity.
    W1's sweep over all 45 settings and W14's bar of 6 of 600 stay as they are.
  - Two sentinels through the launcher that makes the real table: an inert option (or the same arm twice) must
    change 0 positions; a change of `IirDepth` on the FIRST position only must change the node count of exactly
    that one position.
  - Why: `setoption name Clear Hash` empties the hash table and leaves the search worker's history tables
    (`uci.cpp` 922 to 924 against 873 to 880; `search.cpp` 3272 to 3286 against 1217 to 1238). Both seats, on the
    60 positions of `loop/build_recipe/pgo_selfplay_books.epd`: after `IirDepth` 2 -> 8 -> 2 on the first
    position the node count differed on all 59 later ones, the score on 56, the move on 15; with `ucinewgame`
    on none. An inert option (`Book Depth` 10 -> 11 -> 10 with the book off): 60 of 60 "changed" after Clear
    Hash, 0 after `ucinewgame`. The two-position fixture: the second position under EQUAL settings 42,959
    against 27,059 nodes after Clear Hash, 43,614 in both arms after `ucinewgame`.
  - Fable's check: the source lines read: `ucinewgame` calls the full reset (every history table of the worker), `Clear
    Hash` only empties the hash table and the caches. On the PC's own Windows program all eight searches of the
    two-position fixture give the seats' numbers to the node (position 1: 31,797 and 39,208; position 2:
    42,959 against 27,059 after Clear Hash, 43,614 in both arms after `ucinewgame`;
    `debate/evidence/fable_n17_a18_check.txt`). The PC's tool behind W1's table (`tmp/tree_factor/tree_factor.py`,
    called by the tune's liveness script; not on this branch) already sends `ucinewgame` and `isready` before
    every search in every arm and runs the base arm twice (the zero sentinel). It has no one-position pulse:
    that sentinel is owed before the table at the final values. Not run by Fable: the two 60-position sweeps.
  - Cost: seconds; no games.

### For later, once the engine is stronger

The owner asked Astra and Neon (23 November, after the close) to look also for plans and improvements for
the time when the engine is stronger. An entry is made under the same rule as above (one message both agree
on, with proof or an explanation that really holds, checked by Fable) and carries five things: WHEN (a
condition that can be measured and that starts it), WHAT, its TEST, its BAR, and WHY IT WAITS (what it needs
that is not there yet). A forecast is called a forecast. Such an entry changes no item above and nothing in
the order of the work that is in order now.

- **A19 (Astra; one addition by Neon). Deeper searches for the self-play labels: fewer, better positions against
  more of today's.** Entered at 2026-11-23T14:32:48Z (Fable's clock). Agreed wording: `20261123T071136Z_astra_agreed_a19.md`
  (Astra `070539Z`, `071057Z`; Neon `070959Z`).
  - WHEN: W8's trainer has qualified AND the store of 2 billion positions is verified AND either a successor
    of round 67's net has passed its promotion gates or W13's matched 768 pair has really given its declared
    equivalence inside +/- 5 Elo. Then the label panel below is measured again with the producer of that day,
    the accepted new kept positions per paid hour are measured on the target machine, and both trainings and
    both matches are declared and paid for before the pilot is used.
  - WHAT: two ways of making positions under the same paid generation time, 2,000 against 8,000 soft nodes a
    move, with the same frozen producer, adjudication and filter; then two nets of the same supported width,
    start, recipe, teacher and seed policy at equal passes. If the deeper set is too small for 1024, both arms
    are screened at 768. Card, storage and transfer costs are printed apart. The panel reports the labels a
    real game writes (search state carried from move to move: "warm") beside searches from a reset program
    ("cold"), compares 8,000 with 2,000 under the same warm state, and uses the trainer's real map from a score
    to its target and its handling of mate scores. A deeper search is a reference, not the truth.
  - TEST and BAR: the two matched trainings, then 4,000 games at 250,000 nodes declared before, on new
    openings played from both sides: the lower end of the 95 % interval from the opening pairs above 0 to go
    on. Then an independent second comparison whose opponent, length, clock or nodes and bar (lower end above
    0) were fixed before the training. R1, R3 and R4 where they apply, and the receiver's paid-rate budget,
    before any use in production. Not clear or lost: 2,000 stays. The optional test of the CAUSE (are the
    labels themselves better?) holds the positions, their move histories, the training rows, the results, the
    optimizer steps and every other target fixed and changes only the search scores, both arms under one
    declared state (cold or warm); equal openings alone do not hold the games equal.
  - WHY IT WAITS: with today's net, from a reset program, labels at 8,000 nodes agree with a 128,000-node search
    on 10.18 points more moves than labels at 2,000 nodes, and their scores lie 22.05 % closer (against 512,000
    nodes the direction is the same). But 8,000 nodes gave only 25.78 % of the positions per processor second,
    only 204 of 384 games ended with the same result, and (Neon) the labels a real game writes at 2,000 nodes
    are already as close to the 128,000-node scores as the reset 8,000-node ones (98.00 against 97.21
    centipawns; reset 2,000: 124.72): the reset comparison overstates what deeper labels would add. A cheaper
    rule (deepen only where the last two iterations disagree) missed its declared bar (Astra `065752Z`). Only
    a pilot on the target machine and trained nets playing games can say whether fewer, deeper labels are worth
    a generation budget, and that needs the trainer, the store and a stronger producer first. This entry is a
    question with its test, not a forecast of a gain.
  - Fable's check: both raw files recounted with a script of Fable's own (`debate/evidence/fable_a19_recount.txt`): 3,064
    rows, 383 games, 12,639 searches; every figure above equal, also Neon's (98.00 centipawns; closer on 1,901
    rows, farther on 1,050, equal on 97). An own bootstrap over games with another seed: 8.75 to 11.72 points
    and 20.37 to 23.81 %. With the PC trainer's own map from a score to its target (sigmoid of score x 2.25 /
    400; no training row carries a mate score or a score of 2,000 or more) the mean distance to the target of
    the 128,000-node score is 0.04330 for reset 2,000, 0.03375 for the real game's 2,000 and 0.03199 for reset
    8,000: in the trainer's units the real labels close 84.4 % of the gap (97.1 % in raw centipawns), and the
    430 rows beyond 1,000 centipawns hold 54.7 % of the centipawn distance but 2.5 % of the target distance.
    Measured AFTER the agreed message, recomputed by Neon (`072612Z`), not yet recounted by Fable: with warm
    searches at both depths (Astra `072450Z`) 8,000 against 2,000 gives 6.89 points more agreement [5.45, 8.32]
    and scores 15.05 % closer [13.38, 16.86]: smaller than the reset figures, still positive. And against
    endgame tables (Astra `072543Z`): on 69 informative rows no depth from 2,000 to 128,000 played a move that
    lost the table's result, and the bar Astra had declared for it failed: agreeing more often with one deep
    search is not the same as playing objectively better moves.
