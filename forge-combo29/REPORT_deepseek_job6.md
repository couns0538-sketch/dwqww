# REPORT - deepseek job 6

Branch `for-fable-and-opus/deepseek-work`. No engine source changed. New files only in
`forge-combo29/tests_deepseek_job6/` plus this report.

Engine numbers printed first, as the job requires. Commit `6b98f217`, my release build,
built-in net, Threads 1, Hash 16:

```
info string bench depth 11 nodes 312866 time 159 nps 1967710
info string bench depth 13 nodes 862329 time 422 nps 2043433
nodes 4865609              (go perft 5)
```

All three match the PC's pins.

## A0 and B0 first, because the job says the rest does not count without them

**A0 (controls for part A), all three numbers, in `logs/A0-controls.json`:**

| control | result |
|---|---|
| the reader: random KQvK with the strong side to move | **758 checked, 0 not wins** |
| the reader: random KRvK with the strong side to move | **892 checked, 0 not wins** |
| the counter: player picking a RANDOM legal move | **121 lost half points** of 2,000 (52 win->draw, 69 draw->loss) |
| the counter: player picking a tablebase-best move | **0 lost half points** of 2,000 |

The reader and the counter both behave as the job demands, so the A1/A2 numbers below
count.

**B0 (control for part B):** the planted-fault program (`plant.c.txt`, a `char[16]`
written at index 20) is reported by this ASan+UBSan build:
`runtime error: store to address 0x502000000044 with insufficient space for an object
of type 'char'` (`logs/B0-planted.txt`). The build works.

## 1. Table

| part | done / partly / not done | evidence files | result in one line |
|---|---|---|---|
| A0 controls | done | `logs/A0-controls.json`, `a0_controls.py` | reader 0 bad of 1,650; random player 121 lost half points; best player 0 |
| A1 single moves, KQvK/KRvK/KPvK x 2 node budgets | done for 3 of the job's 10 classes | `logs/A1-all-2000.json`, `logs/A1-all-20000.json`, `a1_single.py` | KQvK **0** and KRvK **0** wins thrown away; KPvK **18/819 (2.2%)** at 2,000 nodes |
| A2 whole games | partly: KQvK and KRvK and KPvK only | `logs/A2-controls.json`, `logs/A2-controls-2000.json`, `logs/A2-KPvK-20000.json`, `a2_games.py` | at 20,000 nodes **195/200** KQvK and KRvK won; at **2,000 nodes only 146/200 and 166/200** |
| A3 up to ten failures classified | **not done** | - | see "What I did not do" |
| B0 planted-fault control | done | `logs/B0-planted.txt` | UBSan reports it |
| B1 long games 300/1,000/3,000 plies | done | `logs/B1-long-games.json`, `b1_long.py` | **30/30** games: exit 0, legal bestmove, **0 bytes stderr** |
| B2(a) mate at clock 99 | done | `logs/B2a-results.txt` | **5/5** played the only mating move, all `mate 1` |
| B2(b)(c) won ending at clock 99 and 90 | done | `logs/B2-B3.json` | clock 99: **`cp 0`** (draw, correct); clock 90: **`cp 888-993`** (win, correct) |
| B3 repetition | **not done** | `logs/B2-B3.json` | 0 usable cases found; my construction did not produce them |

**The job's stop rule:** part A1 at 2,000 nodes shows more than 5% of wins thrown away
only in **KPvK (2.2% win->draw, plus 5 draw->loss)**. That is under 5%, so I did not stop.
But A2 at 2,000 nodes shows a much larger effect (below), and that is where I would look
next.

## 2. The A1 and A2 tables

### A1, single moves

| class | nodes | positions | wins | win->draw | win->loss | draws | draw->loss | losses |
|---|---|---|---|---|---|---|---|---|
| KQvK | 2,000 | 2,000 | 783 | **0** | 0 | 129 | 0 | 1,088 |
| KRvK | 2,000 | 2,000 | 906 | **0** | 0 | 116 | 0 | 978 |
| KPvK | 2,000 | 2,000 | 819 | **18** | 0 | 582 | **5** | 599 |
| KQvK | 20,000 | 2,000 | 783 | **0** | 0 | 129 | 0 | 1,088 |
| KRvK | 20,000 | 2,000 | 906 | **0** | 0 | 116 | 0 | 978 |
| KPvK | 20,000 | 2,000 | 819 | **20** | 0 | 582 | **4** | 599 |

KPvK win->draw rate: **18/819 = 2.2%** at 2,000 nodes, **20/819 = 2.4%** at 20,000.
More nodes did **not** help (it is slightly worse), which is itself worth knowing.

### A2, whole games from tablebase-WON starts

| class | nodes | starts | won by mate | repetition | fifty-move |
|---|---|---|---|---|---|
| KQvK | 20,000 | 200 | **195** | 5 | 0 |
| KRvK | 20,000 | 200 | **195** | 5 | 0 |
| KPvK | 20,000 | 200 | **197** | 3 | 0 |
| KQvK | **2,000** | 200 | **146** | 47 | 7 |
| KRvK | **2,000** | 200 | **166** | 30 | 4 |

"repetition" means the defender could claim a threefold repetition; see
`logs/A2-note-repetition.txt` for the checked example and the exact python-chess
predicate (`can_claim_threefold_repetition()` true, not automatic). "fifty" means the
halfmove clock reached 100.

## 3. Findings, each with a test that can be re-run

**F1 (most costly). At 2,000 nodes - the depth the PC's self-play uses - the engine
throws away 27% of won KQvK games and 17% of won KRvK games.**
KQvK: 146/200 won, 47 lost to a claimable repetition, 7 to the 50-move rule. KRvK:
166/200, 30 and 4. At 20,000 nodes this falls to 195/200 for both (5 repetitions each).
Re-run: `python3 a2_games.py tables-all.json KQvK,KRvK 2000 out.json 20261118`.
This is the half-point loss the job was looking for, and it is large enough to matter
for self-play labels at 2,000 nodes.

**F2. KQvK and KRvK single moves are clean: 0 of 783 and 0 of 906 wins thrown away, at
both node budgets.** Re-run: `a1_single.py tables-all.json KQvK,KRvK 2000 out.json
20261118`. So the A2 losses in F1 are not from single-move blunders; they come from the
long conversion, which is consistent with F1's repetition/50-move tallies.

**F3. KPvK single moves throw away 2.2% of wins, and more nodes does not help.**
18/819 -> 20/819 from 2,000 to 20,000 nodes. The engine's own scores on those positions
are `cp 0` or a small positive, e.g. `8/3k4/8/8/8/5p2/8/3K4 b - - 0 1` (a win) played
`d7e6` to a draw with `score cp 214`. Re-run: `a1_single.py tables-all.json KPvK 2000
out.json 20261118`; the failing lines are in `logs/A1-all-2000.json` under
`classes.KPvK.failures`.

**F4. The 50-move rule is handled correctly at the boundary in the cases I tested.**
At clock 99 a won KQvK with no mate available scores `cp 0` (a draw), at clock 90 the
same kind of position scores `cp ~900` (a win). At clock 99 with a mate in one, the
engine plays the mate 5/5. Re-run: `b23.py tables-all.json outdir 20261118`.

**F5. Long games are memory-safe and produce legal moves.** 30 games of 300, 1,000 and
3,000 plies under ASan+UBSan: exit 0, legal `bestmove`, nothing on stderr. Re-run:
`b1_long.py build-asan/forge outdir 20261118`.

## 4. Suspicions, not proven

- **F1's repetition losses look like the engine not knowing how to make progress**, not
  like a bug in a rule. The saved games show pure shuffling (`Qd4-g4-g3`,
  `Kh7-h8-h7`). I did not test whether this is the evaluation, the 50-move damping
  (`rule50_damped_static`), or something else.
- **The "more nodes does not help" result in F3** suggests the KPvK errors are
  evaluation errors, not search-horizon errors. I did not verify that.
- **KRvK at 20,000 nodes loses 5/200 to repetition**, so even the "easy" classes are not
  clean end-to-end.

## 5. Which files of the repository I opened

`src/search.cpp` (TT probe and store, the 50-move damping, HindsightDepth),
`include/forge/search.hpp`, `src/uci.cpp`, `CMakeLists.txt`. I did **not** open
`include/forge/nnue_v3.hpp` or `src/nnue_v3.cpp` in this job. I read the job files
`FABLE_TO_deepseek_1..6.md`.

## 6. Start and end of each part, recorded stamps

| part | start | end | wall |
|---|---|---|---|
| tablebase download attempts (all failed) | 13:03:20 | 13:03:40 | <1 min |
| retrograde solver written, KQvK solved | 13:03:40 | 13:07:47 | ~4 min |
| KRvK and KPvK solved | 13:08:05 | 13:17:07 | ~9 min (concurrent) |
| A0 controls | 13:08:30 | 13:17:10 | ~9 min (incl. waiting for tables) |
| A1 both node budgets, three classes | 13:17:14 | 13:18:04 | <1 min |
| A2 controls and KPvK | 13:18:17 | 13:18:57 | <1 min |
| B0 planted fault, ASan build | 13:19:05 | 13:19:20 | <1 min |
| B1 long games | 13:19:20 | 13:19:51 | <1 min |
| B2/B3 script, fixes and runs | 13:19:30 | 13:21:00 | ~1.5 min |
| report | 13:21:00 | 13:29:00 | ~8 min |

**Total: about 26 minutes of the 60 allowed.**

## 7. What I did not do

- **Syzygy was not used: the mirror is unreachable from this machine.** HTTPS to
  `tablebase.lichess.ovh` fails the TLS handshake (`UNEXPECTED_EOF_WHILE_READING`) and
  plain HTTP returns 403. The job's fallback applies, so I did KQvK, KRvK and KPvK by
  retrograde analysis. **All seven other classes (KBNvK, KQvKR, KRvKP, KQvKP, KPvKP,
  KRvKB, KRvKN) were not measured at all**, and A2's KBNvK and KQvKR rows do not exist.
- **A3 (classify up to ten failures) is not done.** I saved the failing lines but did
  not write the per-failure classification.
- **B3 is not done.** My construction search did not produce 200 cases where the engine
  has both a repeating move and a winning non-repeating move; it produced 0 and I
  stopped rather than ship a weak version. Note that A2 already shows the *behaviour*
  (47 and 30 repetition losses at 2,000 nodes) even though B3's designed test did not
  run.
- I did not build a DTZ table, so A2's defender does not hold out maximally - it picks a
  random legal move among those that keep its WDL. That makes the engine's task *easier*
  than against best defence, so F1's rates are a lower bound.
- I did not run KBNvK or KQvKR (no tables).
- I did not test the 50-move rule at clocks other than 90 and 99.
- I did not change any engine source.

## 8. What I am not sure about

- **My retrograde tables have one real bug found and fixed during this job, and I cannot
  rule out another.** The first KPvK solve gave 424 wins out of 662,704 states because I
  negated a terminal win recorded in my own move list (a promotion to queen counted as a
  loss). After the fix it gives 259,624 wins and the A0 reader control passes 758/758
  and 892/892. KQvK and KRvK were solved before the fix but contain no promotions, so
  the sign path never fired for them; the A0 control on both is what makes me willing to
  use them.
- **The A0 reader control only covers positions where the strong side is to move and
  the win is easy to state.** It does not verify the drawn and lost verdicts, so a
  systematic error in those would survive it.
- **F1's numbers depend on my defender being weak (random among WDL-best).** Against
  a DTZ-optimal defender the loss rate at 2,000 nodes could be different, probably
  worse but not necessarily.
- **"repetition" in A2 is a claimable threefold, not an automatic draw.** In a real
  game the defender must claim it; my harness ends the game at the claim. I verified this
  distinction on one game and state it rather than call it a draw.
- **Whether the PC's training loop would even see F1** depends on how the self-play
  games are adjudicated; if a game is truncated at some ply limit the repetition would be
  scored as a draw anyway, so the label is wrong either way, but I did not check the PC's
  adjudication.
- **I did not verify my KPvK win/draw split against any published figure.** My sample of
  2,000 random KPvK positions contains 819 wins and 582 draws, which is plausible (many
  K+P vs K positions are draws) but is not an independent check of the table. The
  independent checks I have are the two A0 reader runs (KQvK and KRvK only) and the
  counter.

## 9. A better way

**9.1 Get one table into the machine and use it for all ten classes.** The whole part A
design assumes Syzygy. From this machine the mirror is blocked; a single
`.rtbw`/`.rtbz` pair for KQvKR is a few hundred KB. If the job is going to be run from a
cloud machine again, either ship the needed files with the job, or state the fallback
classes up front (as it does) and cut part A to those three so that the report is not
mostly "not measured". Check which is better by comparing the cost of one `.rtbw` upload
against the cost of a job that can only answer 3 of 10 classes.

**9.2 For A2, use a DTZ table for the defender.** The job says "the defender plays a
tablebase move that holds out longest (`probe_dtz`; any consistent rule, say which)". With
WDL only, no such rule exists, so the measured loss rate is a lower bound. A DTZ table
for KQvK is small.

**9.3 Measure the conversion, not only the single move.** F2 shows single moves are
clean while F1 shows whole games are not. The natural next job is "from 200 won KQvK
positions, how many are still won after N plies at 2,000 nodes", which isolates the
long-conversion failure from the evaluation and is cheaper than A2's full games.
