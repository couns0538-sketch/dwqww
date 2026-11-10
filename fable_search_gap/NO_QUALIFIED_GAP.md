# NO QUALIFIED GAP

Result of the fable52 job "one missing search mechanism" for the Forge engine at the combo29 lock. 2026-11-09, PT. Corrected after the review; `REVIEW_LOG.md` lists what changed. Terms are explained in section 9.

## Key points

- **Verdict: NO QUALIFIED GAP.** I found no search mechanism that is both missing everywhere and supported well enough to hand to the crew as a spec.
- **Twenty candidates were checked. Nineteen are already owned** (in the lock, built, gated, rejected, or listed in the crew's research notes). `DEDUPE.md` has the references.
- **The twentieth is owned by nobody: enhanced transposition cutoffs.** I measured it in a replica search on the lock's own board and evaluation code. Four more classic ideas are also unowned; I found no evidence that would justify measuring them (`DEDUPE.md` section 5).
- **It does not qualify, because no benefit is shown.** The rule committed before the deciding run asked for a node saving clearly below 1.00. The measured range includes 1.00. A placebo change moves the same numbers about as far. A second run on 336 positions from 48 independent openings, read by a rule committed before it, gave 0.987 with range [0.954, 1.022]: not shown, and no more than about 5 % if it exists.
- **That is "not shown", not "refuted".** The first test could only have seen a saving of about 12 % or more, the second one of about 5 % or more. The time cost of the lookups is the same order as the possible saving, and this loaded machine could not settle which is larger.
- **One warning sign:** on the classic pawn-ending test position, three of eight settings of the mechanism play the drawing move at some depth. Under ten placebo-size changes the plain replica always keeps the winning move; the mechanism's settings miss it at some depth in 31 of 80 runs. One setting (6 plies) never misses.
- **Blocker:** no shown benefit, in a replica that is not the lock search.
- **Narrowest next evidence request:** one counting run inside the real lock search, described in section 6. It needs an instrumented build, which this job was not allowed to make. It costs a few crew hours and a quiet timing slot, and no gate.

Nothing here is an Elo claim.

## 1. The question and the rule

A candidate had to pass five tests:

1. Absent from the lock source.
2. Not owned: not built, queued, gating, rejected, or listed in research notes, on any branch or in any live candidate folder.
3. Evidence of need in Forge data, traced to code and to a counterexample.
4. Support from a primary source, with licence recorded.
5. A sharp way to prove it wrong.

For the one candidate that reached test 3, the measurement rule was written down and committed (`data/QUALIFICATION_RULE.md`, commit `30b96b42`, 20:55:44 PT) seven seconds before the deciding 95-position run finished writing. The rule has weaknesses, which the reviewer found; they are listed in `EVIDENCE.md` section 6. None of them turns the fail into a pass.

## 2. Where the candidates fell

| Group | Count | Examples | Fell at |
|---|---|---|---|
| Already in the lock in another form | 4 | twofold repetition rule, null-move forms, check-extension limits, aspiration fail-high handling | test 1 or 2 |
| Built or gated by the crew | 6 | upcoming-repetition test, draw-score jitter, eval-difference history, helper-thread diversity, quiet checks in quiescence, attacked-piece ordering bonus | test 2 |
| Listed in the crew's notes: rejected there, below their bar, or left without a number | 9 | depth cut after alpha rises, node-count ordering near the root, less reduction for killer moves, capture-history update in quiescence, in-check ProbCut, recapture extension, lazy evaluation | test 2 |
| Unowned | 1 | enhanced transposition cutoffs | test 3 |

Four further classic ideas have no card and no build (`DEDUPE.md` section 5). They never reached test 3. One of them, a guard against repetition-tainted table scores, is partly owned through today's `tcc21` candidate.

## 3. The unowned candidate in plain words

When the search arrives at a position, the lock asks its transposition table one question: "have I already searched **this** position deeply enough?" (`src/search.cpp:1165-1170`). If not, it starts searching the moves.

Enhanced transposition cutoffs ask a second question first: "has any position **one move away** already been searched deeply enough, with a result that refutes this one?" If yes, the node is finished without searching anything. The idea is from Plaat, Schaeffer, Pijls and de Bruin (1996), who reported 28 % better search efficiency in chess for the programs of that time (`IDEA_SOURCE.md` row 1).

**Why it adds no new kind of guess.** Suppose move `m` leads to child `C`, and the table holds an upper bound for `C` that is at or below minus beta, at the depth the search would give `C`. If the plain search tried `m` first, and nothing else happened before, it would enter `C`, take `C`'s own table cutoff, and come back with a value at or above beta. The mechanism returns that value without the call.

**Why it is still not the same search.** An earlier version of this section said the mechanism "returns exactly what the plain search would return". That was too strong. In the lock:

- Razoring, reverse futility, the null move, ProbCut and the depth cut for nodes without a hash move all run before the first move is tried (`search.cpp:1196-1285`). The shortcut skips them.
- A singular search may extend the hash move by one or two plies, or end the node early through multi-cut (`search.cpp:1348-1377`). So "the depth the search would give `C`" is not known for the hash move without running that search.
- A normal cutoff updates killers and history tables and raises the parent's child-cutoff counter, which the lock uses for reductions (`search.cpp:1450`). The shortcut does none of that.
- The child's own tests still apply: its draw test, its rule-50 limit, and whether its stored score is usable at its rule-50 count.

So the mechanism makes no new guess about the position, but it changes the path the search takes afterwards. The measurement shows how much: single positions move by large factors in both directions.

**How far the lock is from it.** The lock already computes each child's key before making the move (`key_after`, `search.cpp:1379-1383`), but uses it only to prefetch. Today's `tcc21` candidate adds a side-effect-free `peek` of a child entry. A build would still need a full move generation at the node (the lock generates moves in stages), a repetition test for the child, a rule for moves the search would extend, and a decision on whether the node writes a bound. It is a modest change, not a free one.

## 4. What I measured

Full detail is in `EVIDENCE.md` section 5. In short, for expected cut nodes with at least 6 or 8 plies left, on 91 distinct positions and 57.0 million plain-search nodes:

| Quantity | Middlegame (56 positions) | Endgame (35 positions) |
|---|---|---|
| Eligible nodes where a child entry already proves the cutoff | 3.9 to 4.2 % | 17.1 to 17.7 % |
| Share of all nodes lying below such nodes (a first-order estimate of the saving, not a ceiling) | 1.2 to 2.0 % | 7.8 to 11.1 % |
| Time cost of the lookups alone, four measurements on a loaded machine | +1.5 to +7.9 % | -2.2 to +5.0 % |
| Node count with the cutoff taken, relative to plain, 6 plies (geometric mean, 95 % range by base) | 0.99 [0.92, 1.07] | 0.88 [0.65, 1.18] |
| The same, 8 plies | 0.99 [0.93, 1.05] | 0.82 [0.62, 1.07] |
| **Placebo**, same measure | 1.00 [0.91, 1.09] | 0.96 [0.75, 1.17] |

Over all 91 positions the node ratio is 0.95 [0.83, 1.07] at 6 plies and 0.92 [0.81, 1.03] at 8 plies. The placebo gives 0.98 [0.88, 1.08].

**Second set.** After the review I ran 336 positions from 48 independent openings, with the reading rule committed first (`data/SUPPLEMENT_RULE.md`).

| Quantity | More than six pieces (213 positions) | Six pieces or fewer (123 positions) | All 336 |
|---|---|---|---|
| Eligible nodes where a child entry already proves the cutoff | 3.2 to 4.0 % | 7.8 to 9.0 % | 7.1 to 8.1 % |
| Node ratio, 6 plies (geometric mean, 95 % range by opening) | 1.02 [0.98, 1.05] | 0.94 [0.87, 1.01] | **0.987 [0.954, 1.022]** |
| The same, 8 plies | 1.01 [0.98, 1.05] | 0.95 [0.89, 1.03] | 0.986 [0.958, 1.015] |
| Placebo | 0.99 [0.96, 1.05] | 1.01 [0.96, 1.11] | 0.999 [0.962, 1.037] |
| Best move differs from plain: mechanism against placebo | 51 against 63 | 21 to 29 against 32 | 72 to 80 against 95 |

Reading by the committed rule: **not shown either way.** The range rules out a saving above about 5 % in this replica on such positions. The hand-typed endgames of the first sets had overstated how often a child entry proves the cutoff.

The controls held: the counting run reproduced the plain node count in every position, and the plain run repeated itself exactly.

## 5. The case for and the case against

**For.**

- Of the twenty candidates it is the only one nobody owns.
- It adds no new kind of guess (section 3), so it carries less tuning risk than a margin-based pruning rule.
- The opportunity is real: a child entry already proves the cutoff at 3 to 4 % of eligible middlegame nodes and at 8 to 17 % of eligible endgame nodes, depending on the position set.
- With six pieces or fewer the second set shows a 5 to 6 % node saving whose range only just includes 1.00.
- On the first 24 positions one setting showed a 13 % node saving with a range just below 1.00. That run came before the rule, so it is a hint, not a test.
- On the classic pawn ending the 6-ply setting keeps the winning move under every change tried. In the baseline run it needs 12 times fewer nodes than the plain replica at depth 40.
- Part of the plumbing exists in `tcc21`.

**Against. This is the stronger case.**

- **No benefit shown.** On the deciding run the node saving cannot be told from zero. By base position the ranges are wider still. Most of the measured saving comes from two positions.
- **Not distinguishable from a placebo.** Changing one history constant by 1 moves the mean node count, the best moves and single positions about as far as the mechanism does. This cuts both ways: no benefit beyond a placebo, and on the second set no harm to best moves beyond one either.
- **Small at best.** The second set bounds the node saving at about 5 % in this replica, with a best estimate of 1.3 %. With more than six pieces on the board there is no sign of any saving.
- **Cost of the same order.** The lookups cost a few percent of time. That is the size of the possible saving. I could not settle which is larger.
- **A wrong move on a known test.** On the classic pawn ending three of eight settings play the drawing move at some depth. Chance is an unlikely explanation: under ten placebo-size changes the plain replica keeps the winning move every time, and the mechanism's settings miss it at some depth in 31 of 80 runs. Those ten runs are closer to two or three independent tries than to ten. Most runs find the move again by depth 40. It is one position, and the cause is not established.
- **Practitioner record.** Engine authors who tried it reported about 1 % fewer nodes, a small gain only when restricted to deep expected cut nodes, or a loss in fast engines (`IDEA_SOURCE.md` row 5). I found no controlled test of it in any current engine.
- **Transfer to the lock is unknown, in both directions.** The replica has no singular search, no ProbCut, no razoring and no net. Those could make the saving in the lock smaller or larger than measured here. I have no measurement either way.
- **A gate would struggle to see it.** By the crew's own arithmetic a 3,000-game run resolves about ±5.9 Elo, and their notes say single changes of this kind usually end unproven at the cap. I measured no Elo and make no claim about where this mechanism would land.
- **Table memory matters.** All runs used a 16 MB table, as the gates do. This CPU has 96 MB of third-level cache, so that table fits in it, which makes lookups cheap. With a larger table each lookup costs more.

## 6. Blocker and the narrowest next evidence request

**Blocker.** Item 3 of the committed rule: the 95 % range of the node ratio must lie entirely below 1.00. It does not (upper end 1.025 to 1.042; 1.03 to 1.07 by base). And every number is from a replica, not from the lock search.

**Request.** One counting run inside the real lock search. No cutoff is taken, so the search and every pin stay identical. `FALSIFICATION.md` section 3 has the exact counters.

- **Build:** the `tcc21` source (it already has the child `peek`), plus a counting block under a compile switch that is off by default. At each non-PV expected cut node with no excluded move, depth at least 8, beta not a mate score, rule-50 below 90 and no cutoff from the node's own entry: generate the legal moves, compute each child key with `key_after`, peek the child entry, and count.
- **Count:** eligible nodes; nodes where some child entry proves the cutoff; how many of those through the hash move's own child; and the nodes spent below the outermost such nodes. For the hash move the child entry must be two plies deeper than for other moves, because the lock may extend the hash move and that cannot be known in advance.
- **Positions:** the engine's `bench 16` and `bench 20`, and at least 300 positions taken from real gate games at evenly spaced plies. That gives the gate's own mix of middlegame and endgame, which I could not get: I found no PGNs.
- **Controls:** node counts with the switch on must equal the pins (312866 / 862329 / 3024920 / 12389307 / 34048354 with the net on). Lookup time is measured on a quiet machine, counting on against counting off, interleaved.
- **Decision, fixed now, on the game positions as one set:**
  - Close the idea if the share of nodes below such nodes is smaller than the lookup time.
  - Write a spec if it is larger by at least 2 percentage points.
  - In between: undecided, no spec.
  - Stop and investigate if the search itself fails high at fewer than 99 % of those nodes.
- **Cost:** a few crew hours and one quiet timing slot. No gate.

An earlier version of this request closed the idea on a middlegame-only threshold of 2 %. The replica's own middlegame numbers were already under that line, and I have no data on how gate games split their clock. The reviewer pointed this out; the thresholds above replace it.

## 7. What would change this verdict

- The counting run above reaching its "write a spec" line in the real search.
- A controlled test of the mechanism in a current engine. I found none.
- A decision to gate at longer time controls or larger tables, where more child entries survive. That regime was not measured here.

## 8. Follow-ups outside this job

These are about owned work or operations. I report them and did not act on them.

1. **A proven bundle with no result on a current base.** `BundlePreset=B4` reached H1 twice against `h256_e12`. I found no run of it against any later base. (UB69 is a port of bundle B1 and UB70W50 is a different pack; both are NOT CLEAN.)
2. **Time losses in the newest gates.** 67 time losses in seven rows recorded 2026-11-07 to 2026-11-09, none in 54,667 older logged games. Those verdicts should be re-run or set aside, and the logs kept.
3. **Base labels.** The results table's base column disagrees with the gate tag in 17 rows (`EVIDENCE.md` section 2). For UB70W50 the manifest names the older LTO exe as base while the table says combo29.
4. **Lock pointer.** `CURRENT_LOCK.json` names the AL1 source folder as the lock's `tree`. The combo29 exe was built from the source in the QA pack.
5. **Rook underpromotion.** The lock exe prefers `d7c8r` at depth 17 on a standard test position. Promoting to a queen loses the new piece the same way, so this is probably a tie between equal moves (`EVIDENCE.md` section 7).
6. **Gate logs and PGNs.** 86 of 136 finished gates have no log in the mirrored folders, and I found no PGN there. Game-level failure analysis is not possible without them.
7. **Repetition-tainted table scores.** The pawn-ending result may be a case of it. The crew already meets the problem in its multi-thread mate work and in `tcc21` (`DEDUPE.md` section 5).

## 9. Terms

| Term | Meaning here |
|---|---|
| Forge | the chess engine this job is about |
| crew | the people and agents who work on Forge on this PC |
| QA, Engine QA | the role that alone schedules gates and publishes locks |
| lock | the engine build the crew currently treats as the reference |
| combo29 | the crew's name for the current lock (exe `forge_clang_combo29_trial_w6.exe`) |
| AL1, trial_w6, `h256_e12`, `ep10` | earlier locks, reference builds and nets that older gates used as their base |
| LTO | link-time optimisation, a build setting; "the LTO build" is the AL1 lock built with it |
| pins | fixed node counts of the lock (bench at five depths with and without the net, perft of two positions). A build that gives other numbers is not the lock |
| gate | a match between a candidate and a base, stopped by a sequential test |
| H1, H0, capped | the test accepted "candidate is better" (or "not worse" in a non-regression gate); it accepted the opposite; it hit its game limit with no decision |
| LLR, nElo | the test's running statistic; normalized Elo, the unit of the test's bounds |
| NOT CLEAN | a gate with time losses, crashes or illegal moves; its verdict is void |
| UHO | a type of opening book with unbalanced positions; rows that used it cannot be pooled with rows that used the older book |
| `tcc21`, `TtCutChildDepth` | one of today's live candidates and its option: before a node takes a cutoff from its own table entry, it looks at the entry of the hash move's child and cancels the cutoff if that entry disagrees |
| `t12b` | another live candidate: two lock bug fixes |
| transposition table, table | the engine's memory of positions already searched |
| hash move | the best move stored in a position's table entry |
| PV node | a node on the line the search currently thinks is best; searched with an open window |
| expected cut node | a node where the search expects one move to refute the line, so a cutoff is likely |
| child | a position one move away |
| replica | the separate search program written for this job (`tools/etc_probe`). It uses the lock's board and evaluation code and its own search |
| plain, counting, cutoff taken | the three kinds of replica run: unchanged; unchanged but counting what the mechanism would do; mechanism applied |
| placebo | the plain replica with one history constant changed by 1. Not a mechanism. It shows how far results move under an arbitrary small change |
| cut4, cut6, cut8 | the mechanism at expected cut nodes with at least 4, 6 or 8 plies left |
| all3, nohm6 | the mechanism at every non-PV node with at least 3 plies left; at expected cut nodes without a hash move with at least 6 plies left |
| geometric mean | the average of ratios taken on a log scale, so that 0.5 and 2.0 average to 1.0 |
| range by base | a 95 % range that treats a base position and the positions generated from it as one cluster |
| A/A | the same run made twice, to see the noise |
| interleaved timing (ABBA) | timing two builds in the order A, B, B, A so that drift cancels |
| Fine 70 | the classic pawn ending of `EVIDENCE.md` section 5.8 |
