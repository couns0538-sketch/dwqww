# The final plan for Forge (debate of 23 November 2026)

**DRAFT 2 (Astra's and Neon's objections to draft 1 are in), pushed at 2026-11-23T12:20:00Z (Fable's clock) so that Astra and Neon can object item by item before phase 3. It becomes final in phase 3; until then `debate/PLAN.md` is the plan.**

Written by Fable from `debate/PLAN.md` (version 3) and `debate/BOARD.md`. Three took part: Fable (Claude, on the
PC), Astra (OpenAI Codex), Neon (Gemini 4 Neon); all three read every file of the branch first. 19 proposals were
made (7 Astra, 11 Neon, 1 Fable); none was rejected; a change entered only with a measurement, lines of the
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
  adopted. Fallback -5 / 0 only if a timed run shows more than 4 hours at the cap (so far 2.4 hours, extrapolated from one run of 4,000 games in 5.7 minutes; W3 times it).
- **R2 (J11). A search change is tested as a bundle, in four stages:** (1) every switch off = the old node
  counts, and per switch a count of how many of 600 positions change; (2) SPRT between 0 and 5 at 20,000 nodes
  on each of two declared opening seeds, both H1; (3) 4,000 games at 250,000 nodes; (4) R1 before self-play
  uses it. **The bar of stage 3: the lower end of the 95 % interval, taken from the opening pairs, above -3** (all three; the error at this depth is +/- 6.1 at 4,000 games, so a measured +3.1 is needed; a bundle truly worth +5 passes 72 %, a true -3 passes 2.5 %). The tune's own deep match in W1 keeps its declared bar, above 0.
- **R3 (N10). A net whose speed differs** is judged in three stages: a screen at 250,000 nodes with node odds
  measured at the match's real concurrency (lower bound above 0 to go on); the proof with equal clocks at one
  declared time control on a quiet machine (lower bound above 0); then R1 and its positions a second with 16
  workers before it plays self-play.
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
  every opening and the stop answers "no information" (a wiring test with a known answer; Astra); a candidate
  at half the nodes ends in H0, one at double the nodes in H1; Astra's two made-up logs, (win, win), (loss,
  loss) and (win, loss), (loss, win), give the pair counts [1,0,0,0,1] and [0,0,2,0,0] and different statistics. The time of these runs is written down (it sets the fallback of R1).
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
- (b) The start-up check of the live searcher (Astra). BAR: after the option list, one fixed search (new game,
  start position, depth 18) gives 375880 nodes and table fill 156; with Hash 32 on purpose (375868, fill 78)
  the start script refuses to start.
- (c) The package by scripts alone (the owner's condition 1). TEST: one start command on a small rehearsal.
  BAR: it checks itself first; it restarts a worker that was killed on purpose; it reports a full disk and a
  stalled worker (both made on purpose); it stops by itself at the set time; every step is in a log.
  PROPOSED in the extension (F3, Fable; not yet voted): the run goes on after the session that started it was
  closed on purpose; the allocator is killed once on purpose and after its restart hands out no opening it
  handed out before (its table is rebuilt from its own log); the link home is cut for ten minutes, and
  afterwards every piece arrives and none is credited twice; the server deletes no piece the PC has not
  confirmed (the whole day is about 4 GB at the measured 2.01 bytes a row).
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
- (f) No paid search twice (N8 a). One allocator process hands the workers their openings in batches and never
  hands one out twice inside one frozen producer; each game's eight opening moves are logged. BAR: with 2
  random plies, 200 games and the table off, the receiver reports about 42 copies; with it on, none; an
  exhausted opening space ends with a clear error. **The key of the table: the whole FEN after the random plies plus the positions since the last pawn move or capture, in order, inside one frozen producer** (Astra's candidate, after Astra's counterexample to the whole FEN alone; sufficient by the engine's three history readers; it is proposal A7, agreed by all three; it keeps 117 of 132 copies = 88.6 % by Astra's and Neon's count with the engine's own position key, 113 by Fable's count with a finer form of the positions; the eight moves in order keep 3). The en-passant field (Astra, Neon; counted on the 132 copies): past positions are written as the engine's own key has them (a target only when a capture is legal); the current position keeps its target whenever a pawn stands ready to capture it, legal or not (Astra's pinned-pawn position shows that such a target changes scores although the key is the same). With this rule the count stays 117 of 132; with every raw target kept it is 77. Neon reached the same rule from the source on its own and replayed the 40 pairs that differ only in a target no pawn can capture: 40 of 40 identical games; all three agree on the rule, for the frozen producer with its book off (Astra); 117 of 132 is what this draw showed, not a universal rate. Two more allocator fixtures (Astra): its midgame position `k1N1r3/2p3n1/8/3pP3/p4Qb1/P2p1B2/8/4Kn2 w - d6 0 23` must get another key than the same position without the target, and the key of the opening `f2f4 e7e5 f4f5 d8f6 e1f2 a7a6 g2g3 g7g5` (a pinned pawn beside the target within the eight plies) must hold the target g6. Earlier games of the same producer whose eight moves were not logged can seed the table only where the opening's halfmove clock is 0 (99 of the 132 copies; Neon), and only when the whole key can be rebuilt from the record (Astra): a printed en-passant target is used as printed; with none printed, the record seeds the table only if no pawn stands where a hidden target beside a pinned pawn is possible; otherwise it is skipped (the receiver still finds exact duplicate games). Fixture: an importer that is given only the common FEN of the pinned-pawn case, with no move log, must not seed a key from it. Each game's eight moves are logged; refused pairs are sampled and replayed, and one replay with other rows makes the table fall back to the eight moves in order. Two more BARS (Astra; both pairs reproduced by Neon and on the PC): the two openings into the start position (one whole FEN; 0 rows and a 127-row game) are BOTH handed out, and so are `b1c3 g8f6 c3d5 b8a6 g1h3 a6b8 h3g1 f6e4` and `b1c3 g8f6 c3e4 f6g8 e4c3 g8f6 c3d5 f6e4` (one whole FEN, neither drawn at the start; 81 rows and 67 rows).
- (g) The pilot rule (A3). The day is steered by verified, kept rows per second of paid time at the receiver.
  BAR: 2 billion kept in 24 hours need 23,149 a second; a deeper search or a stricter filter runs for the whole
  day only if the pilot's rate covers its own target; the fallback is written down before the day.
- (h) What the day plays, written down before the rental (N11): the one best proven net (R4), no second
  player; W1's values only if all five matches held, else today's list; 2,000 soft nodes; games end at 2000
  unless W10's "cut at 1000" net passed. Anything else only after a pilot declared before and succeeded. If W13's
  trainings on 2 billion are unfinished or inconclusive when the rental comes (draft 1 said W8 here; Neon): the proven configuration, or the day is moved.
- (i) BAR for the whole of W5: one end-to-end rehearsal at small scale, started by one command and not
  touched until it has stopped by itself, with (a) to (f) passing inside it.

**W6. The card test before paid card hours (N8 b).** Needs a short rental or loan of an NVIDIA card.
- TEST: one pass on one round there. BAR: the exported net loads on the PC and the PC's trainer-against-engine
  check passes on at least 1,000 named positions; peak memory and rows a second are read. If the teacher stays
  (W11): the hand-written evaluation's Linux build gives the same values as the Windows one on 3,000 positions.

**W7. Which rounds count toward the 2 billion (P11; A5).** Processor, about 3 hours; nets are trained.
- TEST: "breadth" (every second row of rounds 29 to 78) against round 78's own candidate (every row of rounds
  54 to 78, equal row counts), 250,000 nodes.
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
- PROPOSED in the extension (F2, Fable; not yet voted): that net is also judged by games (R5) against the net
  of today's trainer on the same window: a paired SPRT between -5 and 0 at 250,000 nodes (alpha = beta = 0.05,
  cap 20,000 games; about 8,300 games = 2.4 hours when the truth is level). H1 = the trainer may be used for
  the 2 billion; H0 or no boundary = the cause is found first.

**W9. Before any net wider than 1024 (N3).** Build. The 1024 net itself is safe (1.55 % of room).
- BAR: the sums are widened before they are added, the loader checks the bound, `MaxHidden` is raised
  (`source/include/forge/nnue_v3.hpp` 65; Neon), a made-up worst-case net gives
  equal raw sums on all three kernels for both signs, and the reference numbers, the two net checks and the
  checking build are repeated.

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
  BAR: by its declaration on the PC if one was written before the match; if there is none, 4,000 games at
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

**W14. The first search bundle (P7; N7, A4).** After W1. Build about a day, then R2's matches.
- Candidates, each behind a switch that is off by default: no SEE pruning of quiet moves that give check; no
  reduction for a missing hash move at the root; the history term of the reduction without its dead zone (only
  if W1's final divisor leaves one); no SEE pruning of checking captures in quiescence; and the switch
  `LmrDeeperShallower` that is already in the source.
- TEST and BAR: R2, on W1's final settings. Before any game: the composition and every rounding are written
  down, and an item that changes the node count on fewer than 6 of the 600 positions is left out and listed.
  (The number 6 is a convention declared here, before the sweep, at Astra's request; no measurement stands
  behind it. Node counts measure activity; the matches decide strength.)

**W15. Correctness duties that stay (P8; N6).** Every build: the three reference numbers, 12 perft counts, every
option checked against the program's own list, a checking build with a planted fault that must be caught, a
second reader for every change that enters the loop. Added, each with its test first: `go perft` works when a
requested net failed to load; openings are given as start position plus moves, and the rehearsal compares each
row's ply with the position's own counter; two repetition wrappers without a caller are removed and the missing
guards get a per-position test (expected: no node count changes); the fixed draw score 0 is checked against
`DrawJitter` at the tune's final values; a comment states the contract near the 50-move limit. Known and written down,
not repaired unless the repair is free: an en-passant capture by a pinned pawn is in the move list before the
legality test, and the search of one position then differs with and without the target (Astra's position: 797
against 789); the opening key accounts for it (W5 f); which reader causes it has not been looked for.

**W16. Put off, with the reason.** A second player in self-play (P6): four rounds would show the trainer only
0.10 x its share; if ever, outside the loop at full dose. Tablebase probing inside the search: +18.6 in endings,
but 3 % slower self-play. More than one thread, and time handling without an increment: never measured here.
Decided against, unless new evidence comes: dropping positions whose best move is a capture; a net as its own
teacher; judging a training by its hold-out loss.

## The order by resource

- Processor: the loop and W1 (running) -> W1's matches 1 to 3 -> W3's runs -> W1's matches 4 and 5 -> W4 -> W7 -> the TD twin (W12) -> the matches of W10 to W12 as
  their nets are ready -> W14.
- Build: W2 (minutes) -> W3 (while W1's first three matches play) -> W5 (the largest piece; it decides whether the server day can be booked) -> W8
  -> W9 only when a net wider than 1024 is wanted.
- Card, between the loop's trainings: W8's tests -> W10, W11, W12 (one at a time).
- Paid: the server day only after W5 (i); the card only after W6 and W8.

## What is still open, with both sides

- The opening key (W5 f) is closed: it is A7, and all three agree.
- Astra has voted on everything that was new in draft 2 and has no dissent left: the en-passant rule of the key (W5 f), W10's advance criterion, the 1 % bar of W3 (b), "fewer than 6 of 600" in W14 (exactly six stays eligible) and the +/- 5 margin of W13. Neon agreed to draft 1 with its own list of edits, which are all in; its vote on draft 2 is awaited.
- Proposed by Fable in the extension and open: F2 (W8: the disk trainer's net is also judged by games) and F3 (W5 c: a closed session, a killed allocator, a cut link, nothing deleted before the PC confirmed it).
- The choices that are the owner's: what the paid card hours go to first (the wide net or deeper labels, W13), and the dates and prices of the rentals.

## What was measured on the PC for this debate

All in `debate/evidence/`: the packed record's round trip on a whole round; the switch of A4 is the rule of the
old match; pieces against score on a whole round; the live-search pin on four programs; games per opening and
who wins after a high score; the opening key (the 29 pairs, five fields, the opening rule drawn 300,000 times,
130 replayed pairs, Astra's two pairs of openings with one whole FEN and different games, the key that survives
them); the soft-node fixture. Corrections of our own numbers are listed on the board.
