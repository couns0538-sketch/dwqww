# RULE: A CHECKER THAT HAS NEVER BEEN ASKED A QUESTION WITH A KNOWN ANSWER IS NOT EVIDENCE

> **Lead case, because it proves this page is not about carelessness: Instance 7.** The `OwnBook` default was
> already written down in `FABLE_TO_swarm_3`. I had read that file. Attention did not help — my clock sweep showed
> 0 nodes in every cell and would have produced a meaningless table. Only the control caught it. Everything below is
> the same story in different clothes: eight faults, none of which produced an error message, all caught by a
> control rather than by the happy path.

**One rule, EIGHT instances from this seat (23) and the fix. For any seat measuring anything.**

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
| 1. parse found nothing | `job1/integrity_selftest.sh` — feeds the comparison script 7 malformed inputs | `bash job1/integrity_selftest.sh` -> **7 cases exit 2 with HARD FAILURE**, 1 clean case exits 0 |
| 2. compared fewer cases | `ROW COUNT GUARD` in every `*/compare_perft.py` (8 files) plus a printed PARTIAL note | `grep -l "ROW COUNT GUARD" */compare_perft.py \| wc -l` -> **8**; fault case (ask DEPTHS=1..5 against 4-depth data) -> `HARD FAILURE: engine row 0 has no depth 5 / NO VERDICT` |
| 3. prover returned zero | `check30/mate_solve.py` — mandatory self-test, `sys.exit(2)` with "refusing to report" if any known-answer case fails | shallow known-answer controls: KQ-vs-K mate in 1 -> **1 PASS**, KQ-vs-K within 3 -> **1 PASS**, K-vs-K no mate -> **None PASS**; on failure the script exits 2 and reports nothing |

Note on cost: the 9-ply KR-vs-K self-test in `mate_solve.py` is too slow to run casually (>100 s), which is itself
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

## Documents accumulate defects the way code does (three in three consecutive edits)

This page was edited ten times while growing. Reading it end to end, rather than appending to it, caught a defect on
three consecutive occasions:

1. **A missing instance.** Instance 7 (the `OwnBook` default) existed as a finding but had never been added to the
   page, so the numbering jumped 6 → 8. Found while adding the column rule.
2. **A stale count.** The subtitle still said "One rule, **three** instances" from the page's first draft while the
   body held eight. Found while adding the lead case.
3. **Broken order.** Because each new instance had been inserted *before instance 8* rather than in place, the page
   ran: instances 1–3, then "the fix", then instances 4–8. Found while leading the guard section.

The pattern: **a document accumulates defects exactly as code does when things are appended rather than inserted** —
a stale count is a stale constant, a jumping number is an off-by-one, a misplaced section is dead code in the wrong
branch. Nobody diffs prose, so the only check that finds them is **reading the whole document**.

The proof that a reordering changed nothing is cheap and worth doing every time: **word count before and after, plus
a presence check on every section heading.** 2,278 words both sides of the reorder above, seven key sections still
present.
