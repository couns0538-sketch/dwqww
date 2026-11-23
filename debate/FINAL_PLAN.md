# The final plan for Forge (debate of 23 November 2026)

**DRAFT, pushed at 2026-11-23T12:01:01Z (Fable's clock) so that Astra and Neon can object item by item before phase 3. It becomes final in phase 3; until then `debate/PLAN.md` is the plan.**

Written by Fable from `debate/PLAN.md` (version 3) and `debate/BOARD.md`. Three took part: Fable (Claude, on the
PC), Astra (OpenAI Codex), Neon (Gemini 4 Neon); all three read every file of the branch first. 18 proposals were
made (6 Astra, 11 Neon, 1 Fable); none was rejected; a change entered only with a measurement, lines of the
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
  adopted. Fallback -5 / 0 only if a timed run shows more than 4 hours at the cap (measured so far: 2.4 hours).
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
- TEST: first the liveness table at the FINAL values (every tuned setting one step down and up, depth 12, 200
  openings + 400 game positions). Then the five matches declared on 17 November, in this order, the first that
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
  FAILS that check (nodes 1926, b2b3); a level pair must not end in H0 twice in a row; a pair with half the
  nodes on one side must end in H0. The time of these runs is written down (it sets the fallback of R1).
- (b) The speed measurement for R3: as many one-thread engines at once as the match will run, elapsed time by
  paired opening and colour. BAR: two repeats agree within their own spread before any odds are frozen.

**W4. The standstill test (N5).** Processor, about 4.5 hours (6,000 games at 250,000 nodes).
- TEST: the three newest plain candidates at the moment it starts, each 2,000 games at 250,000 nodes against
  round 67's net, pooled; LB and UB are the ends of the pooled 95 % interval.
- BAR, four outcomes: LB above 0 and UB at or above +5: a gain of unsettled size; the best of the three is
  confirmed alone with a fresh seed before any promotion; no pause. LB above 0 and UB below +5: a gain under +5;
  the best may be confirmed; the 2 billion keep their priority. LB at or below 0 and UB below +5: level within
  +5; the per-round training and gate may be paused until W8's trainer runs (a code change with its own test;
  the rows gained are timed). LB at or below 0 and UB at or above +5: inconclusive, nothing changes.
  A "depth effect" is claimed only if the difference between 50,000 and 250,000 nodes on the same three nets has
  its own lower bound above 0.

**W5. Everything the rented server day needs, proven on the PC before the day is booked (P3b).** Build +
processor; rehearsed in the PC's Linux subsystem.
- (a) The program (N2). TEST: a Linux build script with all the loop's flags, three variants (AVX-512 with
  PEXT, AVX2 with PEXT, AVX2 without), each built twice. BAR: each prints the three reference numbers, the 12
  perft counts and the two known answers with the loop's net and settings (226187 / 616966); the start script
  refuses a variant the processor cannot run (rehearsed with the wrong one on purpose); speed is compared by
  self-play, not by `bench`. Owner's direction, after the debate: full link-time optimisation against ThinLTO,
  two builds each.
- (b) The start-up check of the live searcher (Astra). BAR: after the option list, one fixed search (new game,
  start position, depth 18) gives 375880 nodes and table fill 156; with Hash 32 on purpose (375868, fill 78)
  the start script refuses to start.
- (c) The package by scripts alone (the owner's condition 1). TEST: one start command on a small rehearsal.
  BAR: it checks itself first; it restarts a worker that was killed on purpose; it reports a full disk and a
  stalled worker (both made on purpose); it stops by itself at the set time; every step is in a log.
- (d) The packed game record as the transfer form (A1; measured once: 16,005,930 rows, 0 differences). TEST in
  the rehearsal: the same comparison with the server's Linux converter on a run whose raw text is kept. BAR:
  0 differences in all five fields; a copy with one wrong final move and a correct checksum FAILS the content
  check.
- (e) Transport and credit (A3; N8). The server sends EVERY row in closed, checksummed pieces as soon as each
  is closed; the PC checks, asks again on a mismatch, and filters at home (the filter only marks). BAR in the
  rehearsal: a piece delivered twice is credited once; a dropped piece is asked for again; a planted duplicate
  payload under a fresh delivery ID is recognised by row hashes over all five fields; an identical request
  under one manifest is credited once; two different histories or manifests with the same position both stay
  eligible.
- (f) No paid search twice (N8 a). One allocator process hands the workers their openings in batches and never
  hands one out twice inside one frozen producer; each game's eight opening moves are logged. BAR: with 2
  random plies, 200 games and the table off, the receiver reports about 42 copies; with it on, none; an
  exhausted opening space ends with a clear error. **The key of the table: the whole FEN after the random plies plus the positions since the last pawn move or capture, in order, inside one frozen producer** (Astra's candidate, after Astra's counterexample to the whole FEN alone; sufficient by the engine's three history readers; it keeps 86 % of the copies, the eight moves in order keep 2 %). Each game's eight moves are logged; refused pairs are sampled and replayed, and one replay with other rows makes the table fall back to the eight moves in order. One more BAR: Astra's two openings (one whole FEN; 0 rows and a 127-row game) are BOTH handed out.
- (g) The pilot rule (A3). The day is steered by verified, kept rows per second of paid time at the receiver.
  BAR: 2 billion kept in 24 hours need 23,149 a second; a deeper search or a stricter filter runs for the whole
  day only if the pilot's rate covers its own target; the fallback is written down before the day.
- (h) What the day plays, written down before the rental (N11): the one best proven net (R4), no second
  player; W1's values only if all five matches held, else today's list; 2,000 soft nodes; games end at 2000
  unless W10's "cut at 1000" net passed. Anything else only after a pilot declared before and succeeded. If W8's
  test is unfinished or inconclusive when the rental comes: the proven configuration, or the day is moved.
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
  today's trainer; one run with a cold file cache.
- BAR: 4.445 million rows a second or more (else the plan quotes the measured duration, not "about 4.2 hours");
  the row ids and counts the sampler visits equal the declared ones; one dropped piece and one doubled piece of
  equal length are each refused before training starts; the round mix of the batches matches a declared
  reference shuffle on a fixed fixture, and a reader that walks the rounds in order FAILS that check; on today's
  388-million window it gives a net whose hold-out loss is within 0.0001 of today's trainer's.

**W9. Before any net wider than 1024 (N3).** Build. The 1024 net itself is safe (1.55 % of room).
- BAR: the sums are widened before they are added, the loader checks the bound, a made-up worst-case net gives
  equal raw sums on all three kernels for both signs, and the reference numbers, the two net checks and the
  checking build are repeated.

**W10. The first filter experiment (P3c; N4).** Card: three trainings; processor: two matches.
- TEST: three nets on equal row counts, uniform samples of the same rounds of round 67's net, same recipe and
  seed: today's filter; score-tail thinning (keep probabilities per score band locked before training); "cut at
  1000" built Astra's way (the crossing row and all after it left out, earlier rows relabelled with the
  counterfactual result, the production filter run again). Each against the control, 4,000 games at 250,000
  nodes.
- BAR: adopted only with a lower bound above 0. If "cut at 1000" is not weaker, ending self-play games at 1000
  becomes its own candidate: its gain in games is TIMED, and it needs R1.

**W11. The teacher (N9).** Card: one training; processor: one match.
- TEST: today's window, 768 wide, same rounds, seed and recipe, teacher weight 0.2 against 0; 4,000 games at
  250,000 nodes. BAR: if the interval crosses zero the recipe stays for now; both versions are prepared for the
  2 billion, and R6 decides there.

**W12. The training recipe (P5; N11).** Card + processor, when the card is free.
- TEST: one matched pair outside the loop (same rounds, rows and seed; only the recipe differs), 4,000 games at
  250,000 nodes. BAR: lower bound above 0 to prefer the new recipe; R6 for the 2 billion. (Replaces the
  four-round trial in the loop.)

**W13. The first trainings on 2 billion (P11, P4; A6).** Rented card or the PC with W8's trainer.
- (a) 768 wide. TEST: against round 67's net by the loop's gate and confirmation, with a direct SPRT at 250,000
  nodes run beside the old gate. The result is recorded whatever it is.
- (b) 1024 wide on the same rows, recipe and seed. Needs W8's verified store, W6's checks and a technically
  valid (a); it does NOT need (a) to have beaten round 67's net. TEST and BAR: R3. Its cost is taken from a
  timed 1024 pilot. If it is put off for cost it is recorded as "width at 2 billion: not tested".
- What the paid card hours go to first, (b) or deeper labels, is the owner's choice.
- What would change the direction: (a) AND (b) level with round 67's net. Then volume at 2,000-node labels is
  not the lever and the next lever is the depth of the labels.

**W14. The first search bundle (P7; N7, A4).** After W1. Build about a day, then R2's matches.
- Candidates, each behind a switch that is off by default: no SEE pruning of quiet moves that give check; no
  reduction for a missing hash move at the root; the history term of the reduction without its dead zone (only
  if W1's final divisor leaves one); no SEE pruning of checking captures in quiescence; and the switch
  `LmrDeeperShallower` that is already in the source.
- TEST and BAR: R2, on W1's final settings. Before any game: the composition and every rounding are written
  down, and an item that changes almost none of the 600 positions is left out.

**W15. Correctness duties that stay (P8; N6).** Every build: the three reference numbers, 12 perft counts, every
option checked against the program's own list, a checking build with a planted fault that must be caught, a
second reader for every change that enters the loop. Added, each with its test first: `go perft` works when a
requested net failed to load; openings are given as start position plus moves, and the rehearsal compares each
row's ply with the position's own counter; two repetition wrappers without a caller are removed and the missing
guards get a per-position test (expected: no node count changes); the fixed draw score 0 is checked against
`DrawJitter` at the tune's final values; a comment states the contract near the 50-move limit.

**W16. Put off, with the reason.** A second player in self-play (P6): four rounds would show the trainer only
0.10 x its share; if ever, outside the loop at full dose. Tablebase probing inside the search: +18.6 in endings,
but 3 % slower self-play. More than one thread, and time handling without an increment: never measured here.
Decided against, unless new evidence comes: dropping positions whose best move is a capture; a net as its own
teacher; judging a training by its hold-out loss.

## The order by resource

- Processor: the loop and W1 (running) -> W1's five matches -> W3 -> W4 -> W7 -> the matches of W10 to W12 as
  their nets are ready -> W14.
- Build: W2 (minutes) -> W3 -> W5 (the largest piece; it decides whether the server day can be booked) -> W8
  -> W9 only when a net wider than 1024 is wanted.
- Card, between the loop's trainings: W8's tests -> W10, W11, W12 (one at a time).
- Paid: the server day only after W5 (i); the card only after W6 and W8.

## What is still open, with both sides

- Nothing is open between Astra and Fable.
- Neon agreed to the whole-FEN key before Astra's counterexample and is asked about the changed key (W5 f).
- The choices that are the owner's: what the paid card hours go to first (the wide net or deeper labels, W13), and the dates and prices of the rentals.

## What was measured on the PC for this debate

All in `debate/evidence/`: the packed record's round trip on a whole round; the switch of A4 is the rule of the
old match; pieces against score on a whole round; the live-search pin on four programs; games per opening and
who wins after a high score; the opening key (the 29 pairs, five fields, the opening rule drawn 300,000 times,
130 replayed pairs); the soft-node fixture. Corrections of our own numbers are listed on the board.
