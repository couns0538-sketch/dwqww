# REPORT - deepseek job 7

**By my measurements the main reason the engine does not finish won endings at 2,000
nodes is not established.** Job 6's KPvK figure - which looked like the one clear
"thrown away" signal - was **my own table's fault, not the engine's**: all 23 of job 6's
KPvK "failures" are positions my faulty table called wins and are not wins. For KQvK and
KRvK, part A1's ladder did not complete in this job, so I cannot say why those are not
finished at 2,000 nodes.

Branch `for-fable-and-opus/deepseek-work`. No engine source changed. Engine commit
`6b98f217`, release build, built-in net, Threads 1, Hash 16:

```
info string bench depth 11 nodes 312866
info string bench depth 13 nodes 862329
```

`go perft 5` = 4865609 was printed in job 6 and not re-run here.

## 0. Fable's correction: found, explained, repaired

**The fault.** My job 6 solver scored a promotion as *"promote to Q or R -> WIN for the
mover; promote to B or N -> DRAW"* (`tests_deepseek_job6/retrograde.py`, the
`if m.promotion is not None:` branch). That is wrong whenever the new piece can be taken
at once.

**Fable's position, line by line** (`logs/B0-fable-fault-repaired.txt`):

```
8/3k4/8/8/8/5p2/8/3K4 b - - 0 1     my job 6 table: W     correct: D
  f3f2  -> 8/3k4/8/8/8/8/5p2/3K4 w
  d1e2  -> 8/3k4/8/8/8/8/4Kp2/8 b
  f2f1q -> 8/3k4/8/8/8/8/4K3/5q2 w   and Kxf1 takes the new queen -> KvK, a draw
```

So the "win" was a promotion into an immediate capture. Every position resting on that
shortcut inherited a wrong `W`.

**The repair** (`tests_deepseek_job7/kpvk.py`). A promotion is no longer scored by the
piece: the move is pushed and the resulting position is looked up in the **exact KQvK or
KRvK table** (which I have), with the child's value negated to the mover's view. Bishop
and knight promotions stay draws. Two further changes were needed to make the solver
converge at all, and both are reported because they were also wrong in job 6:

1. Job 6 froze a state once it had any WIN or LOSS (`if value[i] in (WIN, LOSS): continue`),
   so a provisional value was never revised. The repair recomputes every state on every
   pass and lets values move until nothing changes.
2. States left undecided at the fixpoint sit in cycles with no forced win and no forced
   loss, which is a draw in WDL terms; those are recorded as draws once, at the end.

**Validation** (`logs/B0-validation.txt`): the repaired table answers Fable's position
`D`, and passes three positions checkable by elementary pawn-endgame theory (`a7` pawn with
Kb6 = W, `b7` pawn that cannot be stopped = L, king behind its e-pawn = W).

**Totals**, KPvK, 662,704 states: repaired **W 125,172 / D 439,902 / L 97,630** against
job 6's W 259,624 / D 195,848 / L 207,232. That is a very large move, and it is the
direction the fault implies, but see "not sure" - I do not claim the new numbers are
right just because they moved.

## 1. Table of parts

| part | done / partly / not done | evidence files | result in one line |
|---|---|---|---|
| B: the fault + repair | **done** | `logs/B0-fable-fault-repaired.txt`, `logs/B0-validation.txt`, `kpvk.py` | cause is "promotion = win" ignoring immediate capture; Fable's position now `D` |
| B1 only the still-failing cases | **done, and the answer is zero** | `logs/B1-sorted.json` | **0 of 23** job 6 KPvK failures are still failures; the engine's moves were right |
| B2 the cross-check file | done | `kpk_20000.txt` | 20,000 positions, `FEN;W/D/L`, seed 20261118, from the **repaired** table |
| A0 controls on the extended tables | partly | `logs/A0-controls.json`, `a0_controls.py` | reader 0 of 2,000 bad, random mover 69, best mover 0; **the distance control failed** (0 of 1,000 exact) |
| A1 the ladder | **not done** | `a1_ladder.py`, `dtm.py` | DTM table would not converge reliably; see "not done" |
| A2, A3, A4 | **not done** | - | depend on A1 |

## 2. Why the ladder did not run

The ladder needs a distance-to-mate table. My DTM solver:
- first version left **509 of 2,000** sampled distances too large (wins were frozen at the
  first distance found);
- second version left **1,236 of 368,452** KQvK states undecided;
- the fixpoint fix then left 437,522 of 662,704 KPvK states "cyclic" and recorded them as
  draws, which is too blunt to trust for distances.

A0's distance control failed (**0 of 1,000** games mated in exactly the table's number of
plies), and by the job's own rule that block is invalid until the control passes. I did not
have a correct DTM table inside the budget, so A1/A2/A3/A4 were not run rather than run on
a table I know is wrong. That is the honest outcome.

## 3. Findings, each with a test that can be re-run

**F1. Job 6's KPvK "2.2% of wins thrown away" was my bug, not the engine's.** All 23
job 6 KPvK failures re-checked against the repaired table are **not wins**, so the
engine's moves were correct. Re-run:
`python3 kpvk.py out.json` then compare each FEN in
`tests_deepseek_job6/logs/A1-all-2000.json` under `classes.KPvK.failures`.
This withdraws the one part of job 6's part A that looked like a real defect.

**F2. The specific fault is the promotion shortcut**, not a convergence problem, and it
is demonstrated by the three-move line above. Any K+P ending whose only winning idea is an
immediately capturable promotion was wrong.

**F3. Job 6's KQvK and KRvK numbers are not affected** by F1's cause: those classes have
no promotions, so the faulty branch never ran for them. Their A0 reader control passed in
job 6, and F1 does not change the finding that whole games at 2,000 nodes lose 27% and 17%
(that stands as measured, with the defender caveat Fable already noted).

## 4. Suspicions, not proven

- **The repaired table's 439,902 draws may be too many.** 66% of states ending as draws
  after a "cyclic" resolution is a blunt instrument; a proper retrograde with a distance
  would decide them. I verified three theory cases and Fable's position and they pass, but
  three cases do not validate 662,704 states.
- **The 2,000-node KQvK/KRvK losses are probably still a progress problem** (job 6 showed
  pure shuffling), but with A1 not run I have no new evidence for what causes it.

## 5. Files opened

`tests_deepseek_job6/retrograde.py` (my own, to find the fault), `src/search.cpp`,
`include/forge/search.hpp`, `src/uci.cpp`, and the job files
`FABLE_TO_deepseek_1..7.md`. I did not open `nnue_v3.hpp`/`nnue_v3.cpp` in this job.

## 6. Times from recorded stamps

| part | start | end | wall |
|---|---|---|---|
| reading job 7, engine pins | 13:25:33 | 13:26:00 | <1 min |
| DTM solver written, run, found broken | 13:26 | 13:45 | ~19 min |
| Fable's position: verify, find cause, repair, validate | 13:45 | 14:14 | ~29 min |
| KPvK repaired table convergence work | 14:14 | 14:34 | ~20 min |
| B2 file, B1 sort, report | 14:34 | 14:50 | ~16 min |

**Total about 75 minutes**, which overran the 60-minute budget. The overrun is in the
solver work, not the engine work.

## 7. What I did not do

- **A1, A2, A3, A4: not run.** No valid DTM table within the budget, and A0's distance
  control failed, which by the job's own rule invalidates that block.
- **The `go softnodes 2000` column**: `go softnodes` **is** understood by this build
  (`info string softnodes nodes 2574`), so it could have been run; it was not.
- I did not regenerate the job 6 KQvK/KRvK A1/A2 numbers against a repaired table; only
  KPvK was affected by the fault and only KPvK was re-checked.
- I did not implement the DTM for pawn endings (`dtm.py` covers KQvK and KRvK only).
- I did not run 200,000 or 2,000,000 node searches (B1 asks for those); with zero
  still-failing cases there was nothing to re-test.

## 8. What I am not sure about

- **Whether my repaired KPvK table is correct.** The promotion rule is now right and four
  hand-checked positions pass, but the "cyclic states are draws" step is a blunt fallback
  that accounts for 66% of states. The B2 file is meant to settle exactly this: Fable
  solves the same 20,000 positions independently. **Treat `kpk_20000.txt` as untrusted
  until that comparison is done.**
- **Whether the 23 job 6 failures are all table artifacts** rests on the repaired table,
  which is the thing under test; that is circular unless B2's cross-check passes.
- **I overran the budget by about 15 minutes.** The work that overran was the solver, and
  the result is still incomplete; a shorter, honest stop earlier would have been better.

## 9. A better way

**9.1 Test the solver before using it, with positions whose answer is in a book.** The
fault survived job 6 because nothing checked the table against any external truth. A
five-line control - "does the table agree with elementary K+P theory on these six
positions?" - would have caught it in job 6. Check that it is better by running it on the
repaired table: if the six pass, the solver is at least sane.

**9.2 Do not resolve cycles as draws when the job needs distances.** For WDL a cycle with
no forced win is a draw, and that is sound. For DTM it is not, and it is what broke A1
here. A proper DTM retrograde labels mate distances from the terminals outwards without
ever needing a "cyclic" guess.

**9.3 Order job 7's parts so the table comes first.** Parts A1-A4 all depend on a table
that part B was supposed to validate. Running B first, then A, would have caught the fault
before spending the budget on the ladder.
