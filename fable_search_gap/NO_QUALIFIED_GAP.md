# NO QUALIFIED GAP

Result of the fable52 job "one missing search mechanism" for the Forge engine at the combo29 lock. 2026-11-09, PT.

## Key points

- **Verdict: NO QUALIFIED GAP.** I found no search mechanism that is both missing everywhere and supported well enough to hand to the crew as a spec.
- **Twenty candidates were checked. Nineteen are already owned** (in the lock, built, gated, rejected, or listed in the crew's research notes). `DEDUPE.md` has the references.
- **One mechanism is owned by nobody: enhanced transposition cutoffs.** It is real, sound in table terms and cheap to build on top of today's `tcc21` plumbing. I measured it in a replica search on the lock's own board and evaluation code.
- **It does not qualify.** On 95 positions the node saving is not statistically clear, in middlegames the table lookups cost more than they save, and on the classic pawn-ending test position one setting loses the win outright. Published practitioner experience points the same way.
- **Blocker:** no clear, reliable saving. The rule that decides this was committed before the deciding run was read.
- **Narrowest next evidence request:** one counting run inside the real lock search, described in section 6. It needs an instrumented build, which this job was not allowed to make. It costs about two crew hours and no gate time.

Nothing here is an Elo claim.

## 1. The question and the rule

A candidate had to pass five tests:

1. Absent from the lock source.
2. Not owned: not built, queued, gating, rejected, or listed in research notes, on any branch or in any live candidate folder.
3. Evidence of need in Forge data, traced to code and to a counterexample.
4. Support from a primary source, with licence recorded.
5. A sharp way to prove it wrong.

For the one candidate that reached test 3, the measurement rule was written down and committed (`data/QUALIFICATION_RULE.md`, commit `30b96b42`, 20:55 PT) before the deciding 95-position run was read.

## 2. Where the candidates fell

| Group | Count | Examples | Fell at |
|---|---|---|---|
| Already in the lock in another form | 4 | twofold repetition rule, null-move forms, check-extension limits, aspiration fail-high handling | test 1 or 2 |
| Built or gated by the crew | 6 | upcoming-repetition test, draw-score jitter, eval-difference history, helper-thread diversity, quiet checks in quiescence, attacked-piece ordering bonus | test 2 |
| Listed in the crew's notes and dropped | 9 | depth cut after alpha rises, node-count ordering near the root, less reduction for killer moves, capture-history update in quiescence, in-check ProbCut, recapture extension, lazy evaluation | test 2 |
| Unowned | 1 | enhanced transposition cutoffs | test 3 |

Four further classic ideas have no owner and no supporting evidence at all (`DEDUPE.md` section 5). They never reached test 3.

## 3. The unowned candidate in plain words

When the search arrives at a position, the lock asks its transposition table one question: "have I already searched **this** position deeply enough?" (`src/search.cpp:1165-1170`). If not, it starts searching the moves.

Enhanced transposition cutoffs ask a second question first: "has any position **one move away** already been searched deeply enough, with a result that refutes this one?" If yes, the node is finished without searching anything. The idea is from Plaat, Schaeffer, Pijls and de Bruin (1996), who reported 28 % better search efficiency in chess for the programs of that time (`IDEA_SOURCE.md` row 1).

Why it is sound in table terms: suppose move `m` leads to child `C`, and the table holds an upper bound for `C` that is at or below minus beta, at the depth the search would give `C`. If the plain search tried `m` first, it would enter `C`, take `C`'s own table cutoff, and return at once with a value at or above beta. The mechanism returns that same value without the call. It adds no new kind of guess. It only changes which move is tried "first".

Why the lock is close to it: the lock already computes each child's key before making the move (`key_after`, `search.cpp:1379-1383`), but uses it only to prefetch. Today's `tcc21` candidate adds a side-effect-free `peek` of a child entry. Those two pieces are everything the mechanism needs.

## 4. What I measured

Full detail is in `EVIDENCE.md` section 5. In short, for expected cut nodes with at least 6 or 8 plies left, on 95 positions and 57.9 million plain-search nodes:

| Quantity | Middlegame (56 positions) | Endgame (39 positions) |
|---|---|---|
| Eligible nodes where a child entry already proves the cutoff | 3.9 to 4.2 % | 17.3 to 17.7 % |
| Share of all nodes lying below such nodes (ceiling on the saving) | 1.2 to 2.0 % | 7.7 to 11.0 % |
| Time cost of the lookups alone | +2.5 to +5.7 % | +3.7 to +5.1 % |
| Node count with the cutoff taken, relative to plain (geometric mean, 95 % range) | 0.99 [0.92, 1.07] | 0.85 to 0.90 [0.69, 1.09] |

Over all 95 positions the node ratio is 0.93 to 0.96 with a range that includes 1.00, and the time ratio is 0.98 at the deeper threshold and 1.07 at the shallower one.

All controls held: the counting run reproduced the plain node count in 95 of 95 positions, the plain run repeated itself exactly, and where a cutoff was available the plain search also failed high in 100.0 % of cases.

## 5. The case for and the case against

**For.**

- It is the only mechanism I found that nobody owns.
- It is exact in the sense of section 3, so it carries less tuning risk than a margin-based pruning rule.
- The opportunity is real in endgames: about one eligible node in six.
- On the classic pawn-ending test position three of four settings reach the winning move with 7 to 12 times fewer nodes at depth 40.
- The plumbing exists in `tcc21`.

**Against. This is the stronger case.**

- **No clear saving.** Across 95 positions the mean node saving is 4 to 7 % and cannot be told from zero. The first 24 positions suggested 13 to 15 %; widening the set shrank it. That is the pattern of an effect that is mostly noise.
- **Middlegames lose.** There the ceiling on the saving is 1.2 to 2.0 % of nodes and the lookups cost 2.5 to 5.7 % of time. Games at 10+0.1 spend most of their clock in the middlegame.
- **Erratic results.** Single positions move between 0.06 and 2.2 times the plain node count. On the classic pawn ending one setting plays the drawing move at every depth from 24 to 40, where the plain replica and the lock exe both find the win (`EVIDENCE.md` section 5). A mechanism that can turn a solved position into an unsolved one needs a much stronger upside than this.
- **Practitioner record.** Engine authors who tried it reported about 1 % fewer nodes, a small gain only when restricted to deep expected cut nodes, or a loss in fast engines (`IDEA_SOURCE.md` row 5). I found no controlled test of it in any current engine.
- **The replica flatters it.** The replica orders moves worse than the lock and has no singular extensions. Where the lock's first move already cuts quickly, the saving is smaller than measured here.
- **The gate cannot see it.** By the crew's own arithmetic a 3,000-game run resolves about ±5.9 Elo. Nothing measured here suggests an effect near that size.
- **Table memory matters.** All runs used a 16 MB table, as the gates do. On this CPU that table fits in the cache, which makes lookups cheap. With a larger table the lookup cost per node is higher.

## 6. Blocker and the narrowest next evidence request

**Blocker.** Item 3 of the committed rule: the 95 % range of the node ratio must lie entirely below 1.00. It does not (upper end 1.025 to 1.042). Item 4 also fails at the shallower threshold. And every number is from a replica, not from the lock search.

**Request.** One counting run inside the real lock search. No cutoff is taken, so the search and every pin stay identical.

- **Build:** the `tcc21` source (it already has the child `peek`), plus about 40 lines under a compile switch that is off by default. At each non-PV expected cut node with no excluded move, depth at least 8, beta not a mate score and rule-50 below 90, generate the legal moves, compute each child key with `key_after`, peek the child entry, and count.
- **Count:** eligible nodes; nodes where some child entry has an upper or exact bound at or below minus beta at depth at least `depth - 1` (one more for a move the search would extend), and is not a repetition on the current path; how many of those are the hash move; and the nodes spent below the outermost such nodes.
- **Run:** the engine's `bench 16` and `bench 20`, and a fixed set of at least 200 positions of which at least 80 have twelve or fewer pieces. One thread, 16 MB, CPU and priority as QA prefers.
- **Controls:** node counts with the switch on must equal the pins (312866 / 862329 / 3024920 / 12389307 / 34048354 with the net on). Time the build with and without the switch in an ABBA pattern for the lookup cost.
- **Decision, fixed now:**
  - Close the idea for good if the share of nodes below such nodes is under 2 % in the middlegame group, or if the lookup cost is more than half of that share.
  - Otherwise write a spec. `FALSIFICATION.md` already lists what that spec would have to survive, with the classic pawn ending as its first test.
- **Cost:** about two crew hours. No games, no gate time.

## 7. What would change this verdict

- The counting run above passing its thresholds in the real search.
- A controlled test of the mechanism in a current engine. I found none.
- A decision to gate at longer time controls or larger tables, where more child entries survive. That regime was not measured here.

## 8. Follow-ups outside this job

These are about owned work or operations. I report them and did not act on them.

1. **A proven bundle with no clean result on a current base.** `BundlePreset=B4` reached H1 twice against `h256_e12`. Its only later relatives (UB69, UB70W50) are NOT CLEAN.
2. **Time losses in the newest gates.** 67 time losses in six rows recorded 2026-11-07 to 2026-11-09, none in 54,667 older logged games. Those verdicts should be re-run or set aside, and the logs kept.
3. **Base label mismatch.** The results table labels UB70W50's base as combo29; its manifest entry names the older LTO exe.
4. **Lock pointer.** `CURRENT_LOCK.json` names the AL1 source folder as the lock's `tree`. The combo29 exe was built from the source in the QA pack.
5. **Rook underpromotion.** The lock exe prefers `d7c8r` at depth 17 on a standard test position (`EVIDENCE.md` section 7).
6. **Gate logs and PGNs.** 86 of 136 finished gates have no log and none has a PGN. Game-level failure analysis is not possible without them.
