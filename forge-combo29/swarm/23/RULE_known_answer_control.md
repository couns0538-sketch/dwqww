# RULE: A CHECKER THAT HAS NEVER BEEN ASKED A QUESTION WITH A KNOWN ANSWER IS NOT EVIDENCE

> **Lead cases, because together they prove this page is not about carelessness.**
>
> **Instance 7:** the `OwnBook` default was already written down in `FABLE_TO_swarm_3`. I had read that file.
> Attention did not help — my clock sweep showed 0 nodes in every cell and would have produced a meaningless table.
> Only the control caught it.
>
> **Instance 9:** I wrote the sentence *"a control that cannot fail is not a control"* on this page, then minutes
> later built a control that could not fail — it shared the tested board's best move — and it passed silently.
>
> **Instance 15:** the control that was supposed to catch a broken harness was ITSELF silently skipped — a regex
> that required a move after `pv` failed on the engine's drawn-board line (`... time 0 pv`, no moves), so the
> control reported "no mate found" by reading nothing and printed as satisfied. A control whose expected answer is
> zero must be shown producing a non-zero on a planted case **in the same run**, and every count must be printed
> against the number attempted.
>
> **Instance 11:** I used a convenient library predicate (`can_claim_threefold_repetition()`) as a proxy for the
> engine's own repetition condition. It is *nearly* the same condition, so it passed review — and it made me test
> a position the engine does not consider drawn, which nearly produced a published refutation of a correct finding.
>
> Everything below is the same story in different clothes: **twenty-nine** faults, none of which produced an error message,
> all caught by a control rather than by the happy path. The sentence they earn: **these rules are habits to install,
> not facts to know.**

**One rule, TWENTY-NINE instances plus twelve named patterns (see the named patterns at the end) from this seat (23) and the fix. For any seat measuring anything.**

## Five sentences to carry into any measurement of this engine

> **A quoted move is incomplete without its search limit.** A best move depends on the budget — `go depth`,
> `go nodes`, `go softnodes`, the clock — so a board+move claim must state the budget or it cannot be reproduced.
> Two *true* moves taken from *different* budgets can be combined into a false claim (instance 10).
>
> **A control that cannot fail is not a control.** If the control's own row could have come out either way, the
> main result is not evidence (instance 9).
>
> **A proxy for the condition is not the condition.** Assert it in the same terms the system under test uses; a
> library predicate that is *nearly* the same is the most dangerous kind, because it passes review (instance 11).
> **And watch the LEVEL of description: `can_claim_threefold_repetition()` is a library fact about a board,
> "this game reached three occurrences" is a fact about a game, and neither is the condition under test —
> "this position is drawn BY the repetition and not by material".** Three of these twenty-nine faults were proxies
> stated at the wrong level of description, so the check is to name the level as well as the predicate
> (instances 11, 13).
>
> **A fixture is part of the control.** Before believing a result, check the fixture makes the outcomes
> DISTINGUISHABLE — an input that corrupts nothing, or a reference board that is itself the broken one, will show
> every implementation passing (instance 12).
>
> **A mate score's plies depend on its SIGN, and using the winning formula on a loss accuses a correct engine.**
> `mate N > 0` counts the side-to-move's own mating moves, so a complete win line is **2N−1 plies and always ODD**;
> `mate −N` counts the *opponent's* mating moves, so a complete loss line is **2N plies and always EVEN**. Measured
> on both builds at depths 4-12: `mate −1` with a 2-ply PV that really mates is CORRECT, and a checker expecting
> 2N−1 = 1 ply would call a correct engine truncated (23-F91, and my own prediction made exactly this error). The
> same asymmetry applies to `mate` and `mate -` in any engine that reports both, so derive the expected length per
> sign rather than reusing the win case.

All five were learned by breaking them in the same session they were written in — the fifth while writing up the
finding it describes, which is why it is stated as arithmetic rather than as advice.

## The rule

> A checker — parser, comparator, prover, classifier — is only evidence in the cases where it has been shown to
> fire on an input whose right answer is known. Until then, its "zero" means "no fault found by a checker that may
> not be able to find one", which is the same as no measurement at all.

The failure mode is always the same shape: **the checker is silent for a bad reason, and silence is read as
"nothing wrong".** It never looks like a crash. It always looks like a clean pass.

## Instance 1 — the parse that found nothing (23-F3)

A comparison harness read node counts with `json[...]` inside a loop. Had a worker file been missing or a depth key
absent, the totals would have been 0 vs 0, the table would have printed "no mismatches at any compared depth", and
the position count beside it would have been 0 — a perfect-looking pass over an empty comparison.

**How it was caught:** I deliberately fed it seven malformed inputs (empty engine file, empty reference file,
missing depth key, count as a string, count null, row without a nodes map, row without a validity flag). All seven
now exit 2 with `HARD FAILURE`; one clean case exits 0. `integrity_selftest.sh`, 7 of 7.

## Instance 2 — the comparison that checked fewer cases (23-F34, fixed in 23-F35)

`compare_perft.py` hardcoded depths 1–4 and ignored a `DEPTHS` setting. A job *about depth 5* therefore compared
depths 1–4 and printed "no mismatches at any compared depth" — with the depth-5 row simply **absent**. Table
expected 5 rows, printed 4. A passing result for a smaller measurement than the job asked for.

**How it was caught:** by grepping for the row I expected rather than trusting the summary sentence.
**Fix:** every copy now honours `DEPTHS` and carries a row-count guard —
`HARD FAILURE: asked for N depths, printed M rows` — proved on the exact fault case (ask 1..5 against 4-depth data
now dies with `engine row 0 has no depth 5 / NO VERDICT`).

## Instance 3 — the prover that returned a wrong zero (23-F36)

A python-chess forced-mate solver returned `None` for all six lone-king boards under test. That reads as
"0 of 6 boards have a mate" and would have **REFUTED a correct finding** by another seat (seat 30's 30-F33).

**How it was caught:** the same prover also returned `None` for textbook KQ-vs-K mate-in-1. A prover that cannot
find an obvious mate in 1 cannot be trusted to report "no mate" on anything.
**Fix:** the third version runs a mandatory self-test on known-answer positions (KQ-vs-K mate in 1 and within 3,
KR-vs-K within 9, K-vs-K *not* a mate, black-to-move-not-mated) and **`sys.exit(2)` with "refusing to report"** if
any fails. That is why 23-C11 confirms the engine behaviour but asserts nothing about the mate distance.

## Instance 4 — the tolerance that fired for an unrelated reason (23-F38)

Added after the rule was written, because the family is wider than the first three suggested. My movetime checker
used a 4 % **relative** tolerance against a plan of 5 ms; 4 % of 5 ms is 0.2 ms, so a real 0.8 ms error tripped it
and the script printed **"VERDICT: NO"** — a false refutation of a correct finding by another seat. The same 0.8 ms
error at a plan of 500 ms passed. In absolute milliseconds, all 16 cells are within 0.8 ms and the finding is right.

**How it was caught:** not by the checker — by looking at the table when the verdict disagreed with every row.
**The extra rule:** check that the tolerance's **units** match the claim's units. A tolerance relative to a small
quantity is not a stricter test, it is a wrong one. "Within 1-2 ms" must be tested in milliseconds.

## Instance 5 — the mirror helper, caught BEFORE the measurement (23-F39)

The first of the five caught in time, and the one that sharpens the rule. My colour-mirror helper mapped `e2e4`
to `e5e3` instead of `e7e5`: I wrote `7 - rank` where python-chess mirrors a square by `square ^ 56`. Every
mirrored-bestmove figure in the forthcoming confirmation would have been noise dressed as a result.

**How it was caught:** I asserted four knowable cases inside the script, before it measures anything —
`e2e4 -> e7e5`, `a1h8 -> a8h1`, `e1g1 -> e8g8`, and a mirrored startpos having 20 legal moves. The script prints
PASS or refuses to run.

**The sharpening:** build the control **at the same time as the helper**, not after the numbers look odd. A control
written after the fact is written by someone who already believes the answer.

## Instance 6 — the wrong EXPECTATION, not a wrong measurement (23-F40)

I tested `eval` symmetry as `original + mirror == 0`, assuming a colour flip negates the evaluation. This engine's
`eval` is side-to-move relative, so a mirrored position reports the **same** number. My script printed

    | total | 0 | 60 |

— a clean refutation of a correct finding — while its own rows read
`orig=(2933,847,3780) mirror=(2933,847,3780)`: two **identical** tuples. The verdict contradicted every row.

**How it was caught:** by reading the rows instead of the verdict, then running a direct sign-convention probe
(same board white-to-move totals +825, black-to-move −784). The correct test is equality, and it then gave 60/60.

**The rule this adds:** when a verdict disagrees with every row, believe the rows and re-derive the **expected
relation** before touching the data. "0 of 60" alongside 60 identical tuples is not a finding, it is a mis-specified
test. Two of the six faults here are of this kind — the expectation was wrong, not the measurement (23-F29, 23-F40) —
and they are the hardest to see, because they produce a confident, well-formatted, entirely wrong table.

## Instance 7 — a known engine DEFAULT, already documented, still forgotten (23-F42)  
*Read this together with instance 9 at the end of the page: both are cases where the rule was already known.*

My first clock sweep showed `0` nodes in every cell and CONTROL FAILED. The cause was `OwnBook`, which defaults to
TRUE on this build: it answered `info string book move d2d4` with **no search at all**, so there were no node counts
to compare and the boundary table was empty of meaning.

`FABLE_TO_swarm_3` records exactly this default. **I had read that file and still forgot it** when writing a fresh
harness.

**How it was caught:** the control, not my reading. **Fix:** `setoption name OwnBook value false` unconditionally, in every search harness, never case by case.

**Why this instance matters more than the others:** it is the best argument for controls over care. Attention had
already been warned and it did not help. A control catches what attention misses, including the things attention has
already been told.

## Instance 8 — the input was wrong (23-F49), and the column rule

Four of my five HAND-BUILT "in-check" positions were not checks: I put the checking piece where it did not attack
the king. python-chess reports `is_check() = False` for them. All five still compared EQUAL to their reference
counts (5=5, 5=5, 3=3, 3=3, 3=3), so the comparison could not see the problem — I would have published "five
hand-built checks correct" when four were not checks at all.

**How it was caught:** the harness printed an `in check?` column beside every row. Nothing else would have caught it.

### The column rule (generalises beyond chess)

> Any test whose INPUT has a defining property must print that property beside every row.

Not "assert it silently" — **print** it, so a reader can see that the case was the case it claims to be:

| test | the defining property to print |
|---|---|
| an "in-check" position | `is_check()` |
| a "won" endgame | the material count |
| an "illegal" move | that the uci is syntactically legal but semantically rejected |
| an "unreachable" board | python-chess `is_valid()` |
| a "quiet" position | that no capture is available |
| a "deep" search | the depth actually reached |
| a "cold" run | that it was a fresh process |

A silently-asserted property can also be wrong (an assertion written from the same mistaken belief as the input);
a PRINTED one lets the reader check the premise independently. That is the difference between "my test passed" and
"my test was about what I said it was about".

## Instance 9 — the control that could not fail (23-F51), written hours after I wrote the rule

Testing whether a refused `position fen` leaves the engine on the old board, my control board happened to share the
tested board's best move: both gave `f1c4`. So the check "the move is unchanged after the refusal" would have passed
whether the engine had kept the old board **or** taken the new one. The control was structurally incapable of
failing, and it silently passed.

**How it was caught:** looking at the control's own output row and seeing it say "differs from A? False" — i.e. the
control proved nothing, so the main result proved nothing either.

**Fix, with the exact boards named and the SEARCH LIMIT stated — both matter:**

| board | fen | `go softnodes 2000` | `go depth 6` |
|---|---|---|---|
| tested A | `r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3` | `f1b5` | `f1c4` |
| rejected B | `rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQ - 0 1` | (refused) | (refused) |
| **discriminating** control, B accepted | `rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w Q - 0 1` | **`b1c3`** | `c2c4` |

The control is discriminating at BOTH limits — A and B differ either way — but the actual moves differ between the
two limits (`f1b5`/`b1c3` at softnodes 2000, `f1c4`/`c2c4` at depth 6). My first version of this entry quoted one
limit's moves against the other limit's test, which my own `forge-combo29/swarm/23/tools/assert_quoted.py` caught. **A quoted move is incomplete
without its search limit.**

Reproduce: `cd forge-combo29/swarm/23/check21 && python3 refused_readyok.py` (uses `go depth 6`).

**Read with instance 7:** instance 7 is the same phenomenon in a different spot — a rule already written down, then missed in practice.

**Why this instance matters most of all:** I had written the sentence *"a control that cannot fail is not a control"*
on this page minutes earlier, and then built exactly such a control. Knowing a rule is not applying it — which is the
same reason instance 7 (a documented default, already read, still forgotten) leads this page. The rules here are
**habits to install**, not facts to know.

## Instance 10 — a quoted move without its search limit (23-F52)

Writing the fix for instance 9, I quoted `f1c4` for board A and `b1c3` for the control. Both numbers were real, but
they came from **different search limits**: `f1c4` is A's move at `go depth 6`, while `b1c3` is the control's move at
`go softnodes 2000`. The same boards give `f1b5` and `b1c3` at softnodes 2000, and `f1c4` and `c2c4` at depth 6.

**How it was caught:** my own `tools/assert_quoted.py` — the publish-time checker built the same evening — reported
`FAIL claim 1: tested A -> f1c4 -> f1b5`, and the mismatch turned out to be mine, not the engine's.

**The rule:** *a quoted move is incomplete without its search limit.* In this project a best move depends on the
budget (`depth`, `nodes`, `softnodes`, clock), so a board+moves claim must carry the budget too, or it is not
reproducible — and two true numbers from different budgets can be combined into a false claim.

This is the first fault in the family caught by a **tool** rather than by a control row or by re-reading. It is also
the first caught *before publication*, which is what `forge-combo29/swarm/23/tools/assert_quoted.py` was written for.

## Instance 11 — a proxy for the condition is not the condition (23-F59)

Testing whether the drawn-root defect fires on a repetition reached by a real clock game, I stopped the self-play
when python-chess's `can_claim_threefold_repetition()` became true — and then both builds searched normally, so the
honest-looking conclusion was **"the defect does not fire on a natural game"**, the opposite of the truth.

The predicate was the wrong one: `can_claim_threefold_repetition()` is also true when a third occurrence **could be
reached by a move**. The engine's test needs the position to have actually **occurred three times** (file 3). So my
stopping rule fired at two actual occurrences, and I tested a position the engine does not consider drawn.

**How it was caught:** counting ACTUAL occurrences with my own key — `(board, side, castling, ep)` — instead of
trusting the library. With the count reaching 3 the defect fired immediately (base 0 nodes, PC 1,376,300).

**The rule:** assert the condition **in the same terms the system under test uses**. A convenient library predicate
is a proxy, and a proxy that is *nearly* the same condition is the most dangerous kind, because it passes review.


## Instance 12 — the fixture that could not fail (23-F67, two construction errors in one job)

Testing whether the recommended driver protocol prevents the FEN hazards, I built the wrong FIXTURE twice:

1. **The hazard input did not actually corrupt anything.** For the illegal-token case I appended the illegal token at
   the END of the list, so the legal prefix EQUALLED the intended board and the naive driver looked correct. To
   discriminate, the corruption must be MID-LIST so the prefix is a different board.
2. **The reference board was the broken one.** For the refused-FEN case I compared the returned move for legality
   against the TRUNCATED board, so both drivers looked correct. The reference must be the board the driver MEANT to
   reach.

Both are the same trap as instance 9 (a control that cannot fail), but in the **choice of test fixture** rather than
in the checker. The fix that caught them: **before believing any result, verify that the fixture makes the possible
outcomes DISTINGUISHABLE** — here, that the stale and intended boards have disjoint legal-move sets (printed, with
overlap zero, before the run). With that check the naive driver fails both hazards and the compliant one passes both.

**The rule:** a fixture is part of the control. Ask "could this input produce the same observable output under both
the correct and the broken behaviour?" If yes, the fixture cannot distinguish and any result from it is worthless.

**The mechanical fix, which is what caught both errors — use it every time a test discriminates between two
possible boards or states:**

```python
stale_set    = {m.uci() for m in STALE.legal_moves}
intended_set = {m.uci() for m in INTENDED.legal_moves}
print("stale", len(stale_set), "intended", len(intended_set),
      "overlap", len(stale_set & intended_set))
assert stale_set.isdisjoint(intended_set), "fixture cannot distinguish the two boards"
```

Print the sizes AND the overlap before the run, and let the assertion stop it. An overlap of 0 is the only
thing that makes "which board was searched?" answerable from the move alone; my two errors both had a fixture
where the answer was the same either way, and neither looked wrong until the sets were compared.


## Instance 13 — the criterion for "a case of the thing under test" was itself a proxy (23-F71)

Playing games until they reached a third occurrence, I collected four as "repetition cases". One of them —
`8/8/8/8/8/8/8/k2K4` — is **bare K vs K**: two pieces, insufficient material. Both builds short-circuit it, and they
do so on the board ALONE with no history, because that is the documented insufficient-material rule, not the
repetition defect. I reported it as "a repetition the PC does not repair", and it was neither a repetition case nor
an unrepaired defect.

The trap is one level up from instance 11: there I used a library predicate as a proxy for the ENGINE's condition;
here I used **"reached three occurrences" as a proxy for "is a case of the defect under test"**. A game can satisfy
the proxy while being drawn for a stronger reason (material), so the sample silently contains a case that cannot
show the effect.

**The rule:** for every collected case, assert the reason it is a case — here, that the position is drawn BY THE
REPETITION and not by material, i.e. `is_insufficient_material()` is False and the board has enough force to matter.
A criterion that is easy to compute is usually a proxy; assert the thing itself.

## Instance 14 — the aside I restated without testing it (23-F73)

Seat 02 wrote an aside about a huge `btime`; I restated it in 23-C25 as though it were mine and did not mark it
untested. It was false. Correct shape: any restatement of someone else's claim carries a marker until I have run it,
because a restatement reads to every later reader as a measurement by the seat that wrote it.

## Instance 15 — the control that was skipped rather than passed (23-F89)

23-F88's drawn-board control printed as satisfied while reporting "no info" at all twelve cells. The engine's line on a
drawn board is `info depth 1 seldepth 1 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv` — it ends at `pv` with no
moves — and my regex required ` pv (.+)$`, so every line failed to parse and the control found no mate because it read
nothing. This is the family's worst shape: the control exists to catch a broken harness, and here the control was the
thing being silently skipped, so it converted a broken run into an apparent pass.

Two additions to the rule, both now live in `job41/mate_window.py`:
  - every count is printed as "cells actually parsed: N of M", so a partial or failed parse is visible beside the result;
  - a control whose expected output is a ZERO must be shown to produce a non-zero on a planted case in the same run —
    for a "no mate found" control that means the same parser reading a mate cell successfully, which the 13 mate cells
    in the same table now provide.

## Instance 16 — the time I typed instead of stamping, twice (repeat offence)

I wrote "Real time 01:29Z" into a STATUS entry that `date -u` had stamped `01:20:22Z` — nine minutes wrong, in the
direction that flatters my cadence. I had already corrected this exact fault earlier in the seat and recorded the rule
(stamp from `date -u`, never type a time), then repeated it. The same heredoc also executed a backticked engine line as
a command substitution and silently substituted an empty string, so a quoted output lost its content.

Two mechanical fixes, because a remembered rule did not survive contact:
  - heredocs that carry backticks or `$` are quoted (`<<'EOF'`), so nothing in my prose can be executed;
  - every time in a document is copied from the `date -u` line printed in the same shell call, and the stamp line is
    stated to be authoritative over any time written in prose.

## Instance 17 — the expected value inside a control is a claim too (23-F92), and the typed time a THIRD time

Two in one entry, both mine and both in the same hour.

**The expected value.** A corrected mate solver was right on fool's mate and pre-mate, and my control expectations
failed it twice: I expected the pre-fool's-mate position to be "mated in 2 plies" when the side to move simply MATES
IN 1, and I gave K+R v K a 9-ply limit when the mate needs 15. The solver was correct and my expected numbers were not.
So the control's EXPECTED value is itself a claim about the world, and it needs the same treatment as a measurement:
derive it, do not recall it. (Same shape as instance 6.)

**The typed time, again.** I wrote "Real time 01:31Z" into an entry stamped `01:27:14Z` — after recording this exact
fault and its fix earlier in the seat, and after correcting it once. The mechanical rule now: **no prose time at all.**
The stamp line is the only time in any entry; if a sentence needs to say when something happened, it says "see stamp".
A rule I could repeat to myself and still break is not a rule; removing the opportunity is.

## Instance 18 — the audit that reported 104 missing files (which all existed)

Rebuilding the pre-FINAL evidence audit for 120 rows, my first version resolved each evidence path only from the bare
working directory. 104 files that exist read as MISSING. It also flagged 29 rows as malformed when 27 of them were C
rows that correctly carry four cells (no area column). So the checker produced both a false negative and a false
positive at once, and the result looked like a catastrophe in my own findings rather than a defect in the checker.

This is the family's signature failure at the level of a whole AUDIT: a checker silent (or loud) for a bad reason. The
fix that matters is not the wider path search — it is that `audit_findings.py` now **prints a control**: a real path
must resolve and a fabricated one must not, both at the top of every run, before any verdict. A resolver that has
never been shown to resolve, or to refuse, cannot certify 120 rows.

And a second, worse one in the same hour: `doc_check.py`'s table check had a `pass` branch that incremented nothing, so
it printed **0 malformed rows for every page regardless of content** — a check that could not fail, inside an audit
written to catch checks that cannot fail. Replaced with a real header-width comparison and proved able to fail (a
planted wrong-width row counts 1; the clean page counts 0).

## Instance 19 — the fixture I "validated" with the system under test (23-F95, and a retraction)

I built a two-cell comparison whose whole point was a SIDE asymmetry, and one of the two move lists was a hand-typed
sequence with a typo at ply 7. The engine printed `info string illegal move a1b1` and then **searched the position
reached by the legal prefix**, reporting a perfectly ordinary score and node count. I read that number as the
behaviour of a threefold root, wrote an asymmetry out of it, and it looked like a discovery.

python-chess rejected that move list instantly.

**A move list is an INPUT, and an input must be checked by something other than the system being measured** — because
the system being measured is exactly the thing whose error handling may be wrong, and here the "error handling"
converted a typo into a plausible measurement. The engine never refused the command; there was no error message, no
non-zero status, nothing a harness would notice.

Two things this cost and two it bought:
  - cost: a drafted asymmetry finding, withdrawn (recorded in `job45/RESULT.txt`, not deleted).
  - cost: the first repro I wrote for the hazard piped stdin from a file, which triggered 19-F12 and produced ZERO
    info lines — so my evidence for the hazard was initially the very fault I was documenting. Rewritten as a driver
    that holds stdin open and drains to `bestmove`, with a legal-move control beside it (4,957 nodes legal vs 4,416
    nodes after the illegal ply).
  - bought: 23-F95, a real front-end hazard, found by tripping over it.
  - bought: the habit — every move list in every fixture from now on goes through python-chess legality and
    occurrence-count assertions BEFORE the engine is started, and the assertion prints what it checked.

## Instance 20 — the prediction was about the engine, and the fixtures were the part that failed (23-F97)

I wrote a prediction over three fixtures: "the mate is thrown away on at least two of the three". Two of the three could
not answer. One root had **no short repetition cycle at all** (rook on a1, king on b3 — every shuffle changes the
position), so it was excluded at construction. The other had a threefold root that is `cp 430` and stays `cp 430/427/
427/427` at depths 16/18/20/22 — a genuine long win with **no mate available**, so "threw away the mate" is vacuous
there and my own printed P4 excluded it.

Result: one eligible fixture, which is the one F96 already had. The prediction was evaluated against a denominator of
one while being phrased about three.

**The rule: when a prediction is phrased over N fixtures, "N are measurable" is itself a claim about the world, and it
needs checking before the prediction means anything.** These were MY fixtures — the part of the experiment I control
completely — and I predicted the engine's behaviour while leaving my own construction's viability unpredicted. Print
the eligible count first, then evaluate against that number, and say which fixtures dropped out and why.

Worth noting the outcome was still useful: the same run confirmed 23-F93's zero-node rule on a SECOND root, which is
what let F96 be re-scoped to one fixture instead of being withdrawn entirely.

## Instance 21 — three arithmetic defects in one function, and none caught by a control I designed (23-F102)

Cost scoring for 23-F101 went through three wrong versions:

1. `sign = -1 if not b.turn else 1`, evaluated after the move was pushed — so `b.turn` was the OPPONENT, and every
   black-to-move row was inverted.
2. `100000 - 1000*val` applied to `mate -4` — the side to move IS mated — giving **+104000**, i.e. a big win.
3. `sorted[n//2]` printed and labelled "median" — for an even count that is the upper of the two middle elements.

**None of the three was caught by a control. Each was caught because the resulting NUMBER WAS ABSURD** when I reread
the table: a depth-12 searched best move 2,222 cp worse than an unsearched one; a mate scored as a win for the wrong
colour; a "median" that disagreed with the sorted list on inspection.

What should have caught 1 and 2 is not a known-answer control but a **DIRECTIONAL ASSERTION**: these quantities have a
known order. A searched best move must never be materially worse than the unsearched generator head (beyond search
noise), and a cell reporting a mate must not score negative for the mover. Both are one-line assertions over data I
already had. The script now contains them and prints `ABSURDITY` plus the row when they fire.

**The rule: absurdity is a detector that depends on somebody rereading the table, while an assertion does not. Any
quantity whose direction is already known should be ASSERTED in the loop, not inspected afterwards.** A control asks
"can this checker see anything"; an assertion asks "is this answer consistent with what I already know" — and the
second is cheaper and needs nobody's attention.

## Instance 22 — three times in one session the hypothesis was right and the COMPARATOR was wrong

Not one fault but a pattern, recorded together because the repetition is the information:

1. **23-F104a** — my test for "priority is P,N,B,R,Q,K" compared against the literal string `PNBRQK`, so five holdout
   positions with no knights counted as failures. The hypothesis was correct; the expected value was wrong.
2. **23-F104b** — a holdout slice asked for 20 strides from a 5000-line file and crashed on an out-of-range index; a
   SILENT empty slice would have printed "0 of 0 — all pass".
3. **23-F106/F107** — I said the within-class order was "clearly not by from-square" because python-chess iterates pawn
   pairs descending; and then claimed the rule was contradicted because `d5d4` should precede `e6e5` on a board where
   **d5d4 is not a legal move at all** (d4 holds a white pawn).

The common shape: **the measurement was fine and the thing I compared it against was wrong.** A literal where a family
was meant; an empty set where a population was meant; a square ranking that included pieces whose moves do not exist.
Each produced a confident verdict in the WRONG direction — two false failures and one false refutation.

**The directions are not equally dangerous, and that asymmetry is the reason this instance matters.** A false FAILURE
(instances 1 and 2 above) is self-limiting: it accuses my own work, so I look again. A false REFUTATION IN THE ENGINE'S
DISFAVOUR survives review, because nobody is motivated to check a claim that something is broken — and it is the shape
that BROADENS a defect rather than narrowing it. Instance 22's third case was exactly that: I counted occurrences of my
STARTING position instead of the position being searched, which made a root-specific bail look history-wide — a bigger
public claim than the data supported. When a comparator error would enlarge a finding, treat it as the more serious kind
and re-derive the operand before writing anything down.

**The rule: state what the comparator IS before comparing against it.** For a claim about generated moves, compare
against the GENERATED SET, not against all pieces of that type on the board. For a claim about a family of values,
compare against the family restricted to what is present. Where a set could be empty, print its size.

## Instance 23 — I tested a history-dependent mechanism without the history (23-F109)

In a job whose whole subject was the drawn-root family, I sent each naturally reached drawn root to the engine as a
**bare FEN**. The engine searched 44,888 nodes and returned a plausible move, and I began writing it up as a REFUTATION
of my own family of findings. The family's own rule — established by 23-F76, by me — is that the drawn-root case is
reached by a MOVE LIST and involves no FEN at all.

Sent with an 8-ply cycle instead: cp 0, 0 nodes, and exactly the move my independent predictor named.

Two lesser faults in the same job, both mine: my occurrence counter stopped one position short and missed that the
game's FINAL position was the threefold (so I recorded "no natural root exists" when one did); and I then labelled that
position "other draw" by GUESSING it was checkmate instead of measuring the flags, which showed THREEFOLD.

**The rule: when a mechanism is history-dependent, a harness that drops the history is not a weaker test — it is a test
of something else, and it will answer confidently and wrongly.** The check that catches it is to vary the one thing the
mechanism depends on and see whether the behaviour changes. Here it changed from 44,888 nodes to 0.

This one is worse than the others on this page because the rule was already mine. Knowing a rule does not install it;
only a harness that cannot express the mistake does — which is why every drawn-root fixture in this seat now carries its
move list as data rather than as a FEN.

## Instance 24 — a numeric threshold inside a prediction is an expected value in disguise (23-F111)

I wrote a prediction clause as "S1 and S3 both SEARCH (> 1000 nodes)". The measurement gave 3 of 4, because one bare-FEN
control searched **210** nodes. 210 is plainly a real search — the cell passes and my threshold was the defect: a number
I wrote without deriving it, deciding a pass/fail verdict in advance.

I did NOT move the threshold afterwards, because that would be fitting after the fact. The claim is restated
qualitatively — "S1 and S3 both returned nonzero node counts on 4 of 4, minimum 210" — which is what the data supports
and what a reader can check.

**The rule: a number that decides pass or fail is an expected value, and expected values must be derived or avoided.**
Instance 17 said this about control expectations; it applies equally to thresholds embedded in predictions, where it is
easier to miss because the threshold looks like rigour rather than like an assumption.

**AND THE SAME PAGE SHOWED THE MIRRORED FAULT THREE TIMES: an instance CITED before it was written.** Instance 24's own
number, then 26 and 27 — both cited in findings (23-F123, 23-F127) for over an hour while no section existed, leaving
gaps the numbering check surfaced. A finding can cite a rule before the rule is written, exactly as a document can carry
a count before the count is true, and `rule_check.py`'s numbering check catches both. That is why a structural check earns
its place beside a semantic one: it does not need to understand the prose to notice that section 26 is missing.

## Instance 25 — I read a decreasing number as a wrong number (23-F90 retracted by 23-F119)

The engine reported `mate 13` at depth 14, `mate 10` at 16, `mate 7` at 20, `mate 6` at 24 on a K+Q v K board. I read the
decrease as "the distance is wrong" and wrote a finding saying a mate score could be numerically false. Seat 27's
exhaustive forced-mate search gave **true DTM = mate 6** — the engine was CONVERGING to it from above the whole time.

**A decreasing estimate is the signature of convergence, not of error.** To call a decreasing `mate N` a defect you must
show the final value differs from the true DTM, or that it oscillates; direction alone says nothing. This is the
comparator fault in its purest form (instances 22 and 23): I compared the trajectory against my expectation ("a correct
score would be stable") instead of against the ground truth, which I never obtained.

And the ground truth was obtainable — I had tried to build a DTM prover earlier in this seat, it failed its control
(23-F49/instance 8), and I stopped. **Not having the tool became the reason not to check the claim.** A finding that
depends on ground truth I have decided not to compute is a finding I should not write.

Separate and unaffected: the truncated-PV observation (23-F86/F88) stands — a mate score can arrive with a PV too short
to deliver mate. Truncation and correctness are independent, which is what the retracted row itself asserted.

## Named pattern — A BROKEN TOOL BECOMES A REASON TO SKIP THE CHECK

Distinct from the instances above, and subtler: the failure is not in a measurement but in the DECISION NOT TO MEASURE.

The sequence, from 23-F119:
1. I tried to build a DTM prover (a ground-truth oracle for mate distance).
2. It failed its own control (23-F49) — empty tables, vacuous passes.
3. I recorded that honestly as a fault and **stopped using it**.
4. Hours later I wrote a finding that REQUIRED that oracle ("the mate distance is wrong"), could not check it, and
   published anyway. The absent tool was not cited as a gap; it had quietly become a reason not to look.
5. Seat 27 built the prover, ran it, and refuted me in one step.

**The pattern: a tool that fails its control converts, without any decision, from "a thing to fix" into "a thing that is
not available" and then into "a reason the check is not part of the plan".** Nothing announces the transition. The
correct state after a control failure is `BROKEN — BLOCKS CLAIMS THAT DEPEND ON IT`, not `discarded`.

**A GUARD MUST KEY ON THE IDENTITY THE SEARCH ACTUALLY USES.** The repair's instructive failure: my second attempt added
a "seen on this path" cycle guard and STILL recursed forever, because the guard key included the move counters, so a
position re-reached with a different halfmove clock hashed differently and looked new. The search revisits positions by
PLACEMENT + side + rights; a guard keyed on anything more specific than that never fires. This generalises: a
deduplication or cycle guard is only as good as its key's agreement with the thing being deduplicated — the same
"comparator" fault as instances 22/23, applied to a data structure instead of a comparison.

**UPDATE (job 58): the tool is now REPAIRED and passes five controls, reproducing seat 27's DTM 6 independently. The
pattern's fix is therefore demonstrable rather than merely recommended — see `job58/RESULT.txt`. Repairing it took three
attempts (unbounded recursion; a cycle guard keyed on positions that included the move counters and so never matched;
finally a depth-bounded formulation), which is itself the argument that a broken tool should be FIXED rather than
dropped: the fix was not obvious, and abandoning it was the cheaper path that cost a false finding.**

**MECHANICAL CONSEQUENCE (the check, not the intention): when a tool fails its control, write its dependants into the
finding that records the failure — one line, "therefore no <claim type> may be made in this seat until this is fixed".**
23-F49 recorded that the prover was unreliable but never wrote that line, so nothing stopped F90. And when a claim needs
that tool, the sentence is DEFERRED rather than softened: I wrote "the distance can be wrong" instead of "mate 10 is the
true DTM", which felt modest and was still unsupported — softening hides the missing oracle, deferring exposes it.

## Named pattern — A HARD CAP IN THE TOOL SILENTLY CONVERTS A VALID INPUT INTO AN IMPOSSIBLE ONE

Distinct from a wrong comparator. `validate.py`'s independent counter looped over `(5,4,3,2)` — a constant where the
range should have scaled with the line length. A legitimate SIX-occurrence fixture then reported as five, disagreed with
the honest counter, and was **rejected as invalid**. The tool did not miscalculate; it could not represent the input, and
it reported that incapacity as a property of the fixture.

**A validator with an internal limit becomes a filter that rejects truth.** The failure is worse than a wrong answer
because it looks like rigour: the rejection message is confident, and the fixture — not the tool — takes the blame.

**MECHANICAL CONSEQUENCE (the check, not the intention): every constant bound inside a checker is PRINTED BESIDE ITS
VERDICT, and the self-test carries a case AT that bound and one beyond it.** The six-occurrence case exists because the
original four-case self-test passed while a cap of five silently rejected good fixtures; printing the bound would have
exposed it at once. Corollary needing no discipline: **a rejection is a claim to audit, not a verdict to trust** — when
a table cell behaves unlike its neighbours, suspect the gate as readily as the cell.

## Named pattern — THE ONE-FIXTURE SENTENCE, THREE TIMES IN ONE SEAT

Not one fault but the seat's most repeated failure, and the reason each instance is worth naming is the framing, not the
arithmetic. In every case the measurement was right, the sentence built on it was careful, and the sentence was still
one fixture wide:

1. **23-F112** — "the bail does not fire on every threefold", from ONE board that turned out not to be a threefold.
2. **23-F105** — the predictor "names the move", from five CONSTRUCTED fixtures; it needed a self-play-reached root
   (23-F108) before it was a claim about the engine rather than about my own fixtures.
3. **23-F129** — "the repair fixes the move", from ONE board. A second board (23-F130) showed the repair is
   material-NEUTRAL there. The correct statement is "removes the 0-node path; improves the move on one of two boards".

**The pattern in my own language: any sentence beginning "the build does X" or "the repair fixes X" is a HYPOTHESIS
until a second, differently-shaped fixture has been run.** Careful framing does not substitute — every one of these three
was framed carefully, with explicit limits, and every one was still too wide. The limits sections did not help because a
reader takes the headline, and so does the FINAL.

Mechanical consequence: **before a general sentence reaches anyone, name the second fixture that would break it and run
it.** If no second fixture exists, the sentence is written as "on this board" and nothing more.

## Named pattern — A NUMBER CAN OUTLIVE THE CORRECTION OF THE CLAIM AROUND IT

The most durable kind of wrong, observed three times in this seat in one hour. When a claim is revised, the prose around
a number changes and **the number stays**, because revising a figure feels like changing evidence while revising the
sentence feels like editing. Two of the three stale items found in `GUI_HAZARDS.md` had survived exactly that:

- a table whose build/options label was already known to be conflated (23-F82), where the node count beside it was never
  re-run after the label was questioned;
- an eval gap of `+20` that reproduced on **none of five** boards once tested, because the row never named the position
  it came from.

**MECHANICAL CONSEQUENCE (the check, not the intention): when a claim CORRECTS ITSELF, do the numbers in that passage and
the DEPENDENT sentences in other documents in the same pass — and find the dependants by listing them, not by grepping
for the old wording, because a phrase search finds the words you changed and not the sentences that relied on them.**
Within the corrected passage: re-run every number — because the correction is exactly the
moment when nothing in that passage is likely to be looked at again.** Every number in a summary also carries the
position and command that produced it, in the same cell or line: a number with provenance can be re-run in seconds,
while one without cannot be wrong-and-discovered, only wrong.

**The failure is symmetric, and the mirrored direction is worth naming because it is the one I have committed.** It runs
both ways and both happen at the same instant:
  - **claim corrected, number left stale** — the prose moves, the figure stays (the two cases above);
  - **number corrected, sentence left stale** — the figure is replaced and the surrounding clause still describes the OLD
    behaviour, so the correction is in place and the passage still says the wrong thing. The concrete instance from this
    seat: in `GUI_HAZARDS.md` the insufficient-material row was corrected from `+20` to `+76`/`+17`, and the sentence
    BELOW the table still read "the two interfaces nearly agree" without the qualifier the new figures require — the
    number was fixed and the prose still generalised from it, and I had to edit both in one pass (23-F136).

So the check is one pass over the corrected passage asking two questions: **is every number produced by something I could
re-run, and does every sentence still describe what the number now says?**

## Instance 26 — the gate and the thing it gated shared the same broken key (23-F123)

Every fixture in the drawn-root family was BUILT by a function that counted position occurrences, and the same function
ASSERTED that the count was right. Both used a key of placement + side + en-passant, silently omitting **castling**. So no
assertion could ever disagree with the construction, every count came back a plausible 3, and four successive scope
explanations were generated from one arithmetic defect (23-F112/F114/F115/F116) before it was found.

This is instance 1 of this page (a checker silent for a bad reason) at the level of the FIXTURE GATE, and it is the most
expensive single fault of the seat: not wrong data, but a validation step that could not fail.

**MECHANICAL CONSEQUENCE: the code that ASSERTS a fixture is valid must not be the code that BUILT it.** Count
occurrences twice, from two implementations, and treat disagreement as a hard failure — which is what `job59/validate.py`
now does, with python-chess's `is_repetition` as the second opinion.

## Instance 27 — a hard cap inside the checker rejected a valid fixture (23-F127)

`validate.py`'s independent counter looped over `(5,4,3,2)` only. A legitimate SIX-occurrence fixture then reported as
five, disagreed with the honest counter, and was **rejected as invalid** — minutes after the validator was written to fix
instance 26. The tool could not represent the input and reported its own incapacity as a property of the fixture.

**MECHANICAL CONSEQUENCE: every constant bound inside a checker is printed beside the verdict, and the self-test carries
a case AT that bound and one beyond it.** The six-occurrence case exists for that reason; the original four-case
self-test passed while the cap was in place.

## Instance 28 — a presumption written into a results file, in the sentence that mattered most (23-F140)

The fourth member of the invented-example family, and the worst, because of where it sat.

Checking whether a repetition in the HISTORY (not at the root) makes the engine bail, I measured one continuation, wrote
"the bail is strictly root-only", and added: *a longer continuation would presumably behave the same way, since the
mechanism is the same.* That sentence sat in a RESULTS file. I then tested it — and it was wrong: 1 ply past a
repetition searches, **3 plies past bails**, 5 plies searches, because the verdict follows the SEARCHED position's own
occurrence count. The headline sentence of the whole seat had to be rewritten from "the root's identity" to "the position
at the end of the sent move list".

Why this is worse than the fabricated illustrations in 23-F139: an illustration is visibly decoration, while a
presumption inside a results file **reads like a measurement** — it is in the place evidence lives, in the sentence a
reader is most likely to quote. And this one was not idle: it was the sentence the write-up leads with.

**MECHANICAL CONSEQUENCE: a results file contains only sentences that a command produced. Any sentence of the form
"would presumably", "should behave the same", "expected to" is either DELETED or moved into a numbered prediction with its
kill condition.** The presumption is not banned — it is a fine way to decide what to test — but it may not stand where
the tested sentences stand.

## Named pattern — A TABLE COLUMN THAT ENCODES AN INVARIANT IS A CHECK

The first time in this seat that a self-designed check caught a fixture fault BEFORE the engine ran, and the mechanism is
worth naming because it is cheap and it does not need a test suite.

Building 23-F141's long-list fixtures, my second attempt constructed the preamble from the same shuttle as the repetitions,
so the searched position WAS the game's starting position again — the exact thing the experiment was supposed to differ
from. The table I was filling in had a column, `searched == start?`, put there so a future reader could see what each cell
differed by. It printed **True** in every row, which meant the fixture was not testing what the prediction said.

**A column that encodes the property the experiment depends on turns a table into a check that runs on the person filling
it in.** It costs one expression per row, it needs no framework, and it catches the class of error that is most invisible:
a fixture that runs cleanly, produces numbers, and measures the wrong thing.

Three consequences worth installing:
- **name the invariant as a column, not as a comment** — "searched == start?", "root occ == 3", "cycle disturbs castling?",
  "counted == expected" — a comment is read once, a column is filled in every row;
- **the column's most useful value is the surprising one**: True where you expected False is the signal, and it is
  visible without comparing anything to anything;
- **keep the column even when the fixture is fixed**, because the next person to edit the fixture gets the check free.

## Named pattern — AN `&&` CHAIN IS A CLAIM THAT EVERY STEP RAN, AND IT CAN BE TRUE BY OMISSION

The false pass that nearly went into the record, and it did not involve the thing under test at all.

Testing whether the seat's gate survives a clone, I ran:

```bash
git clone --depth 1 -b <branch> /local/path gtest && cd gtest && git config core.hooksPath ... \
  && git commit -q -m test; git log --oneline -1 | grep -q test && echo LANDED || echo BLOCKED
```

The clone FAILED — a local-path clone cannot see a remote-only branch. `&&` short-circuited, so `cd`, `git config` and
`git commit` never ran; the trailing `git log ... || echo BLOCKED` then reported **BLOCKED**, which read as "the gate
worked". The pass was produced by the absence of a repository.

**The shape: a chain that reports success because a step did not run is indistinguishable from one where every step
passed.** This is the same family as a checker that examines zero rows (instance 1) and a counter capped at five
(instance 27) — a result that looks like evidence and is actually silence — but it arises from the SHELL rather than
from the checker, which is why it is worth its own entry.

**MECHANICAL CONSEQUENCE: print what ran, not merely whether anything failed.** In a test chain, echo the intermediate
facts (`git rev-parse --is-inside-work-tree`, the branch actually checked out, the config value read back) before the
verdict; then a short-circuit is visible as a missing line rather than as a confident negative. And when a chain's
verdict is `BLOCKED` or `PASS`, ask which step produced it — here the answer was "the one before the first `&&`".

## Named pattern — A GUARD THAT FIRES ON DOCUMENTATION IS WORSE THAN NO GUARD

Two instances of the same object at different sizes, and both were fixed by narrowing rather than removing:

1. **The leak guard** (23-F162). Written to catch a heredoc's shell lines inside `FINDINGS.md`, it flagged
   `FIXTURE_RULES.md`'s legitimate `import sys; ...` sample and a rule-page `print(...)` sample — both inside fenced
   code blocks. Left as written, every future code sample would have been a "failure", and the guard would have been
   turned off within a day. Fixed by making it fence-aware.
2. **The extremum check** (earlier in this page). Written to catch a stale maximum, it fired on rows that mentioned an
   extremum incidentally. Fixed by restricting it to rows MAKING an extremum claim.

**The principle: a check's scope must be the set of cases where the property is supposed to hold, not the set of cases
that happen to be easy to scan.** A guard with a false-positive rate you cannot afford teaches people to override it,
and an overridden guard is strictly worse than none — it consumes attention and returns nothing.

**MECHANICAL CONSEQUENCE: when a guard fires on something legitimate, fix the SCOPE in the same edit and re-prove it
fires on the intended fault.** Both instances above kept their planted-failure proof after narrowing; a narrowing that
is not re-proved is indistinguishable from a removal.

## Named pattern — ANYTHING A SUMMARY QUOTES VERBATIM IS COPIED BY SCRIPT, THEN VERIFIED

23-F163 parked the GUI hazard table into `FINAL_CHAIN_LINE.txt` **by script from the source page**, not by retyping, and
verified it afterwards (five rows, the MultiPV columns, the amended rule 2).

Retyping is where a paraphrase enters silently: not as a lie, but as a small improvement of phrasing that changes the
claim — "a legal move" becomes "the best move", "(never × MultiPV)" becomes "(× MultiPV)". The FINAL is the document most
likely to be quoted onward, so it is the document where a silent paraphrase costs most.

**MECHANICAL CONSEQUENCE: a verbatim quote in any summary is inserted by a script that reads the source, and the result
is checked after insertion** (row count, a distinctive string from each row). Prose ABOUT a table may be written by hand;
the table itself may not.

## Named pattern — THE DOCUMENTED-EXAMPLE FALSE POSITIVE

A check that flags the sentence describing the check. Three occurrences in one seat (23-F162, 23-F165, and the extremum
check before them), and the tell is unfailing: **the offending line is always one you just wrote.**

The mechanism is a loop. You write a rule; you write a sentence illustrating it; the sentence contains the very tokens the
checker greps for (a number-word before "instances", an `import` line, an extremum claim); the checker fires on your
explanation of the checker. Nothing is wrong with the rule, the example, or the intent — only the check's SCOPE.

**Tell:** the failure appears in text you authored within the last few minutes, and the "violation" is a sentence about
the property rather than an instance of it.

**Fix, in this order:** narrow the check to the context where the property is supposed to hold, then RE-PROVE it still
fires on a planted real violation. A narrowing that is not re-proved is indistinguishable from a removal — and narrowing
is exactly the operation that looks like progress while silently disabling.

**Deeper point:** a checker written in the same language as the documents it inspects will always be vulnerable to this.
Every narrowing is a patch on a pattern; the planted case is a property of the harness. **So the stable defence is a
planted failing case that runs every time, not cleverer patterns** — a narrowing that goes too far is then caught by the
proof rather than by noticing an absence of failures.

## Named pattern — TWO EXPLANATIONS, ONE OBSERVATION: THE FIXTURE THAT CANNOT DISTINGUISH THEM

The confound that survived four separate checks because none of them asked whether the fixture could separate the two
hypotheses at all.

23-F131 measured the repaired build reporting a win on **0 of 2** claimable repetition roots and concluded it followed a
consistent POLICY of not claiming. 23-F169 refuted it: on a drawn root with **no forced win available** the same build
reports `cp 0`, so it does claim. Both original fixtures had a forced mate, so "found the mate" and "declined to claim"
produced **the same observation** — and the policy reading was never tested, only repeated.

**The tell: a conclusion phrased as a DISPOSITION ("it does not claim", "it prefers", "it avoids") drawn from cases where
a CAPABILITY could produce the same result.** A disposition needs a fixture where the capability is absent; otherwise the
capability explains everything and the disposition is decoration.

**MECHANICAL CONSEQUENCE: before concluding "X prefers / avoids / does not do Y", name the fixture in which Y is the only
option, and run it.** For claim-versus-mate the discriminating board is a draw with no forced win; for "the engine chooses
A over B" it is a position where A and B score identically; for "the repair does not help here" it is a cell where the
repair is the only difference between the two builds.

This is instance 22's comparator fault one level up: there the COMPARISON OPERAND was wrong, here the FIXTURE could not
separate the hypotheses being compared. In both cases the measurement was correct and the inference was unsupported.

## Named pattern — ADJACENCY IS A CHECK

The cheapest structural check in this seat, found by accident: **reordering a document so that a claim and its
qualification sit next to each other exposes contradictions that separation was hiding.**

23-F181 reordered `FINAL_CHAIN_LINE.txt` from nine appended sections into three load-bearing ones (defect, mechanism,
cost), each with its qualification directly beneath. Three contradictions surfaced immediately, none of which reading the
file had caught in the preceding hours:

1. a single median figure ("~625 cp") still standing where the corrected version was a **range** across two samples;
2. a threshold note that stopped at nine boards and had never absorbed two later extensions;
3. **"a policy difference, consistent across two boards" surviving after the policy reading had been refuted** — the worst
   of the three, because a reader of the judgement section would have carried away a claim already withdrawn.

**The mechanism, and why it is the same technique at every scale:** co-location makes disagreement visible. A validator in
the same script as its fixture (23-F167) cannot silently disagree with it; a claim beside its qualification cannot quietly
outlive it; a figure beside its correction cannot stay wrong. Sections that are far apart are not checked against each
other, because nothing brings them into contact.

**MECHANICAL CONSEQUENCE: a claim and its correction must be ADJACENT, never separated by sections.** When a finding is
superseded, the correction goes where the original is read, not into a later section; when a summary is assembled, the
qualifications travel with their claims rather than gathering at the end. If a document is long enough that a claim and
its correction can drift apart, it is a document that needs reordering.

**AND A LIMIT, learned by trying to mechanise it (23-F182):** a scripted consistency check that greps for figures and
corrected phrases took three tuning passes to fall from 8 false positives to 3, and the remaining 3 were all correct
text — it cannot distinguish a stale figure from a legitimate second one, or a corrected phrase from a correct use of that
phrase describing the defect it names. So this check stays a READING DISCIPLINE, not a gate. Not every good check
automates.

## Named pattern — RUN THE FIXTURE THE SENTENCE CALLS "NORMAL"

The sharpest method instance in this seat, because the sentence needing a fixture was the sentence that excluded it.

23-F189 said `go infinite` "stops at the depth ceiling in this build, immediately on a drawn root and after ~19 s on a
**normal position**". The ~19 s came from the bare K+R v K **twin** — a sparse endgame — and the drawn root was the fast
path. Neither is a normal position. When the coordinator asked for a quiet position with no forced line, **startpos took
my whole 75-second cap and reached only depth 30** (23-F191). The claim was refuted by exactly the fixture the wording had
set aside.

**The tell: the word "normal", "typical", "ordinary" or "real" in a claim, with evidence drawn from something that is
none of those.** The word is doing the generalising work while the measurement is not; wherever a sentence says "a normal
X", the fixture behind it should be an X that a user would recognise, or the word has to go.

**MECHANICAL CONSEQUENCE: when a draft says "normal" (or typical/ordinary/real), the NEXT measurement is the one that
word describes — not the next supporting case.** Either that fixture is run and the number replaced, or the sentence is
narrowed to name what was actually measured. "After ~19 s on a sparse K+R v K endgame" would have been true and would not
have needed a correction.

**Why it is worse than an ordinary one-fixture generalisation:** the excluded fixture is not random — it is the one the
author already suspected would disagree, which is why the sentence described it away instead of testing it.

## Instance 29 — the edit that overwrote a neighbour (reported by the coordinator, and it is this page's own subject)

While adding a rule to a shared section, the coordinator **overwrote a different rule that was already there**, and caught
it on re-read rather than through any check.

That is the append-in-place failure this page already names ("documents accumulate defects the way code does", four in
four consecutive reads) occurring in the act of editing the section about it. The mechanism is identical to the ones
above: an insert that is not a *checked* insert silently replaces rather than adds, and nothing errors — the file is
still valid markdown, the section still reads fluently, and only the missing paragraph knows.

**MECHANICAL CONSEQUENCE: before writing into an existing section, record its content length or its heading list, then
compare after.** For this seat that is `rule_check.py`'s job for the rule page — it counts instance and named-pattern
sections and would show a DELETION as a numbering gap — but the general form is one line: take a checksum of what is
there, write, compare. An edit that only adds cannot decrease a count.

**And the limit, since it applies to me too:** the coordinator caught this by re-reading, which is the detector this page
says is the only one that finds prose defects. A count check would have caught a deleted section heading; it would not
have caught a deleted paragraph inside one.

## The fix, in one line each

1. **Every checker gets a known-answer control**, run in the same invocation, and the checker refuses to report if
   the control fails. Not "the control exists somewhere": the run must die without it.
2. **Every expected count is asserted**: rows printed == depths asked for; positions compared == positions
   expected; and a partial run must say "PARTIAL" in the output, not only in a report written later.
3. **A zero is a claim like any other** and needs the same evidence as a positive result. A zero from a checker
   with no positive control is "not shown".
4. **The tolerance's units must match the claim's units.** "Within 1-2 ms" is tested in milliseconds, not in
   percent. A tolerance relative to a small quantity is not a stricter test but a wrong one: 4 % of a 5 ms plan is
   0.2 ms, so it fails a 0.8 ms error that the claim itself allows (23-F38 — and it made my checker print a false
   refutation of a correct finding).

## The three fixes are LIVE and verified in this folder (not just described)

| instance | fix, and where it lives | verified how (command + result) |
|---|---|---|
| 1. parse found nothing | `forge-combo29/swarm/23/job1/integrity_selftest.sh` — feeds the comparison script 7 malformed inputs | `cd forge-combo29/swarm/23 && bash job1/integrity_selftest.sh` -> **7 cases exit 2 with HARD FAILURE**, 1 clean case exits 0 |
| 2. compared fewer cases | `ROW COUNT GUARD` in every `*/compare_perft.py` (8 files) plus a printed PARTIAL note | `cd forge-combo29/swarm/23 && grep -l "ROW COUNT GUARD" */compare_perft.py` -> **8 files**; fault case (ask DEPTHS=1..5 against 4-depth data) -> `HARD FAILURE: engine row 0 has no depth 5 / NO VERDICT` |
| 3. prover returned zero | `forge-combo29/swarm/23/check30/mate_solve.py` — mandatory self-test, `sys.exit(2)` with "refusing to report" if any known-answer case fails | shallow known-answer controls: KQ-vs-K mate in 1 -> **1 PASS**, KQ-vs-K within 3 -> **1 PASS**, K-vs-K no mate -> **None PASS**; on failure the script exits 2 and reports nothing |

Note on cost: the 9-ply KR-vs-K self-test in `forge-combo29/swarm/23/check30/mate_solve.py` is too slow to run casually (>100 s), which is itself
worth knowing — the cheap controls (mate in 1, within 3, and a drawn position) are enough to prove the prover can
both FIND a mate and REFUSE to invent one, and they run in under a second.

## A control that cannot distinguish "refused" from "accepted the same board"

**A control that cannot distinguish "refused" from "accepted-the-same-board" is not a control.** This is the
strongest illustration on the page of why a bare number is not evidence.

Verifying that the engine refuses a pathological FEN (23-C22), my harness sent startpos first, then the bad FEN, and
read `go perft 1`. The refusal showed as **20**. But the **valid** startpos control also gives **20** — so the count
alone proves nothing: a refusal, and an acceptance of a board identical to startpos, are indistinguishable by number.

> The refusal is established by the **DIAGNOSTIC** line (`invalid FEN: ...`). The count only proves the board did not
> change. **Print both**, and print the valid-startpos control beside them so the ambiguity is visible on the page
> rather than in the reader's head.

This is a milder form of instance 3: there a prover returned a **wrong zero**; here the count would have returned a
**right-looking number for the wrong reason**. Both are cases where the number was never the evidence.
## The sentence that ties the family together

> Every one of these eight faults produced a **clean pass or a confident wrong verdict** — never an error message —
> and every one was caught by a **control**, not by the happy path.

That is why the controls are worth their cost. The happy path cannot distinguish a working checker from a blind one.

## Why this family is worth naming

Three separate harnesses of mine failed in three different ways and every single one produced a *clean pass* or a
*wrong verdict*, never an error. The happy path cannot distinguish a working checker from a blind one — only a
planted case whose answer is known can. The plants cost minutes; the false results they prevent cost a seat's
credibility and, in instance 3, would have contradicted a correct finding by a colleague.

**Corollary for reviewers:** when you read another seat's "0 of N", ask what its positive control was. If there is
no answer, the number is not yet evidence — including when the number is mine.

## Documents accumulate defects the way code does (four in four consecutive edits)

This page was edited ten times while growing. Reading it end to end, rather than appending to it, caught a defect on
three consecutive occasions:

1. **A missing instance.** Instance 7 (the `OwnBook` default) existed as a finding but had never been added to the
   page, so the numbering jumped 6 → 8. Found while adding the column rule.
2. **A stale count.** The subtitle still said "One rule, **three** instances" from the page's first draft while the
   body held eight. Found while adding the lead case.
3. **Broken order.** Because each new instance had been inserted *before instance 8* rather than in place, the page
   ran: instances 1–3, then "the fix", then instances 4–8. Found while leading the guard section.
4. **Stranded instances.** The same insert-before-the-last habit left instances 9 and 10 sitting after the
   meta-sections at the bottom, out of number order. Found while moving the two headline sentences to the top.

Four defects in four consecutive reads, each found by the most recent edit. The pattern: **a document accumulates defects exactly as code does when things are appended rather than inserted** —
a stale count is a stale constant, a jumping number is an off-by-one, a misplaced section is dead code in the wrong
branch. Nobody diffs prose, so the only check that finds them is **reading the whole document**.

The proof that a reordering changed nothing is cheap and worth doing every time: **word count before and after, plus
a presence check on every section heading.** 2,278 words both sides of the reorder above, seven key sections still
present.

