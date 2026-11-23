# STATE: where the work stands (Opus, 23 November 2026, about 02:20 PC clock)

Every number was read from the loop's own log, from a match tool's own result line, or recounted from the games.
Raw files: on the PC, not on this branch (unless a line names a file of this branch).
Elo intervals are 95 %. "Nodes" is the node limit per move for both sides unless two numbers are given.

## 1. The loop and its best net
- Best net: round 67's candidate (768 wide, king buckets), adopted 19 November 11:13. Gate at 50,000 nodes:
  3,474 games, 977-878-1619, +9.90 +/- 7.39. Confirmation at 250,000 nodes: 1,926 games, 483-428-1015,
  +9.92 +/- 8.87, SPRT H1.
- Engine of the loop: tree r15dsg; the forge6.5 play exe on this branch has the same search as the loop's exe
  (checked 23 November 02:15: equal nodes and best moves at depth 12 on 200 book openings and 400 positions
  from the loop's own games, with two nets, and the three reference numbers 312866 / 862329 / 4865609).
- Training window: the newest 25 rounds, at most 388,000,000 kept positions; 40 passes; round 136 took
  2,917 seconds on the card (23 November 01:16 to 02:04).
- Rounds 68 to 136: no candidate adopted (69 rounds). Since round 88 the loop pools its gates: the last 8 gates
  against the same best net; promote when the pooled lower bound is above 0 and this round's gate is at least 0.
  Round 136 (23 November 02:20): gate 4,000 games at 50,000 nodes, 1084-1010-1906, +6.43 +/- 6.64, inconclusive;
  pooled rounds 129 to 136, 29,968 games, -0.07 [-2.52, +2.38]: does not fire.
- Direct test of the plateau: round 87's net against round 67's at 50,000 nodes, 30,000 games, 8036-7833-14131,
  +2.35 [-0.10, +4.80], ended by its game cap on 22 November 02:20: not shown better.
- Data on record (the loop's own counts, filter stage "kept"): 2,036,342,838 positions over rounds 1 to 136;
  1,052,412,711 of them in rounds 68 to 136, all played by round 67's net. A round adds about 15.25 million
  (round 135: 16,007,724 written, 15,249,472 kept) in about 78 minutes. On disk (checked 23 November 02:24):
  all 136 rounds, 25 as plain text (the training window) and 111 packed (gzip), none moved, none dropped;
  present as files, contents not re-read.
- Speed of self-play on this PC: round 135 made 3,386,849 new positions in 582 seconds on 16 workers
  (5,818 a second), playing with round 67's net at 2,000 soft nodes (the engine's hard cap is four times that, 8,000: `source/src/search.cpp` 2661 to 2665; the first version of this file said 5,000, the lab config's older and unused `nodes` value: Astra's find, corrected 23 November).

## 2. The big tune (SPSA over 40 search settings)
- Engine r15d (the loop's engine on 17 November), net round 33, the loop's other options fixed; 20,000 nodes a
  move; 8 opening pairs per iteration; 40,000 iterations planned (640,000 games).
- Progress: 33,375 iterations (534,000 games) on 23 November 01:50.
- Snapshots of the tuned values against the start values, 2,000 games each at 20,000 nodes:
  snapshot 8: 665-433-902, +40.5 [+30.6, +50.5]; snapshot 9: 664-419-917, +42.8 [+33.0, +52.6];
  snapshot 10 (iteration 31,250, 22 November 18:26): 703-380-917, +56.6 [+46.7, +66.6].
  Stop rule (at least 4 snapshots, then three in a row at or below +2.0): not met.
- NOT yet measured: at 250,000 nodes, on the clock, with today's engine (r15dsg) and today's net (round 67).

## 3. Width: W3
- A = a 1024-wide net, B = a 768-wide net, both trained by the same recipe on the same rounds (52 to 76);
  A plays at 236,000 nodes, B at 250,000 (node odds for the slower wide net); SPRT bounds 0 and 6 Elo.
- 23 November 02:07: 11 chunks, 4,400 games, 1094-1088-2218, +0.47 [-5.38, +6.33], LLR -1.70 of +/-2.94.
  Stopped there on 23 November 02:22, without a verdict.
- Why stopped: both nets were trained on about 0.38 billion positions. The owner's rule (23 November): a
  1024-wide net needs at least 1 billion positions; first 2 billion positions, then the wider net. So this
  level result is no test of width: the test came too early.

## 4. Breadth
- A 768 net trained on every second row of rounds 29 to 78 (346,393,625 positions: the row count of round 78's
  candidate, which read every row of rounds 54 to 78); trained 20 November 07:48, its checks passed.
  Its match against round 78's candidate waits for W3 to end.

## 5. TD labels and the TD twin
- TD labels (each position's score smoothed over the scores of the following plies, x = 0.7) trained rounds
  79 to 87 of the loop; the verdict counted the gates of rounds 79 to 86, all against round 67's net:
  32,000 games, 8555-8245-15200, +3.37 [+1.01, +5.72]. The plain rounds 68 to 78 against the same net:
  36,916 games, -0.81 [-3.02, +1.40].
- TD minus plain: +4.18 against rounds 68 to 78, but +2.19 against rounds 73 to 78. The reading written before
  those gates called such a split, with no TD net adopted, "back": the trial ended on 20 November 15:13 as
  level alone at x = 0.7, 768 wide, 2,000 soft nodes.
- TD twin: round 82's TD candidate against a twin trained on the same rounds with plain labels (trained
  20 November 12:31). Its match waits behind breadth.

## 6. The loop's decision rule: two faults found 23 November (repairs planned, not placed)
- Round 112's gate: fastchess printed its SPRT verdict (H0 after 1,860 games) and then did not exit for
  2 hours 24 minutes; the loop recorded the gate as not finished, and the pooled gate leaves out a gate that is
  not finished, so rounds 113 to 119 had no pool. No adoption decision changed (37 of 37 pooled lines recounted).
- Repairs: end fastchess once its verdict line is printed and its output stops growing; pool a gate that is
  finished OR has all its games.

## 7. Helpers (cloud agents)
- No helper branch has moved since 21 November (newest: carbon2's job 51 report and kimi5's claim of job 41).
- The Grok swarm of 20 November (about 30 agents, one hour) has ended.
