# RULE: A CHECKER THAT HAS NEVER BEEN ASKED A QUESTION WITH A KNOWN ANSWER IS NOT EVIDENCE

**One rule, three instances from this seat (23), and the fix. For any seat measuring anything.**

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

## The fix, in one line each

1. **Every checker gets a known-answer control**, run in the same invocation, and the checker refuses to report if
   the control fails. Not "the control exists somewhere": the run must die without it.
2. **Every expected count is asserted**: rows printed == depths asked for; positions compared == positions
   expected; and a partial run must say "PARTIAL" in the output, not only in a report written later.
3. **A zero is a claim like any other** and needs the same evidence as a positive result. A zero from a checker
   with no positive control is "not shown".

## Why this family is worth naming

Three separate harnesses of mine failed in three different ways and every single one produced a *clean pass* or a
*wrong verdict*, never an error. The happy path cannot distinguish a working checker from a blind one — only a
planted case whose answer is known can. The plants cost minutes; the false results they prevent cost a seat's
credibility and, in instance 3, would have contradicted a correct finding by a colleague.

**Corollary for reviewers:** when you read another seat's "0 of N", ask what its positive control was. If there is
no answer, the number is not yet evidence — including when the number is mine.

## The three fixes are LIVE and verified in this folder (not just described)

| instance | fix, and where it lives | verified how (command + result) |
|---|---|---|
| 1. parse found nothing | `job1/integrity_selftest.sh` — feeds the comparison script 7 malformed inputs | `bash job1/integrity_selftest.sh` -> **7 cases exit 2 with HARD FAILURE**, 1 clean case exits 0 |
| 2. compared fewer cases | `ROW COUNT GUARD` in every `*/compare_perft.py` (8 files) plus a printed PARTIAL note | `grep -l "ROW COUNT GUARD" */compare_perft.py \| wc -l` -> **8**; fault case (ask DEPTHS=1..5 against 4-depth data) -> `HARD FAILURE: engine row 0 has no depth 5 / NO VERDICT` |
| 3. prover returned zero | `check30/mate_solve.py` — mandatory self-test, `sys.exit(2)` with "refusing to report" if any known-answer case fails | shallow known-answer controls: KQ-vs-K mate in 1 -> **1 PASS**, KQ-vs-K within 3 -> **1 PASS**, K-vs-K no mate -> **None PASS**; on failure the script exits 2 and reports nothing |

Note on cost: the 9-ply KR-vs-K self-test in `mate_solve.py` is too slow to run casually (>100 s), which is itself
worth knowing — the cheap controls (mate in 1, within 3, and a drawn position) are enough to prove the prover can
both FIND a mate and REFUSE to invent one, and they run in under a second.
