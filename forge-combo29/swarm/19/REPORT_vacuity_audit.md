# REPORT — vacuity audit of my own parsed numbers

seat 19 · area 9 · branch `for-fable-and-opus/swarm-19`

## What was asked and what I did

The coordinator asked me to apply the same vacuity audit I stumbled into on my 08-F9 attempt 1 (where a
`NaN <= x` comparison silently passed and printed "CONFIRMS" without measuring anything) to **every number in
my reports that came from a parsed line**.

`vacuity_audit/vacuity_audit.py` re-parses the raw files in my own committed folders and asks, for each
number, one question: **was the line it was parsed from actually found?** It does not recompute the science;
it checks the parsing step, which is where vacuity hides.

**33 numbers audited. All 33 now pass.**

## The one real defect the audit process found (in the audit, not the reports)

My first run reported 3 failures. All three were defects in the *audit script*, not in any report — but one
of them is worth recording because it is the same class of mistake it was hunting:

| # | audit's first verdict | what was actually true | who was wrong |
|---|---|---|---|
| 1 | `job2/profile_cg/perf_children.txt` — line NOT FOUND | that file has never existed: the callchain profile lives in **`job1/profile_cg/`**. `REPORT_job1.md` cites `job1/profile_cg/` correctly in all five places it mentions it. | the audit script's hardcoded path |
| 2 | `job1b zero-node searches` — parsed `0 200`, expected `0 of 200` | the raw line is `searches reporting 0 nodes: 0 of 200`; my regex returned the two numbers joined with a space while the expectation string used the word "of". A string-comparison artifact. | the audit script's comparison |
| 3 | `19-F14 all four cases searched` — line NOT FOUND | the line exists: `cases where the search produced nothing: ` with an *empty* tail (which is the correct result — no case produced nothing). My regex used `(.+)`, which cannot match an empty tail. | the audit script's regex |

Item 3 is the interesting one and it is exactly the vacuity trap in mirror image: a regex that requires at
least one character silently fails on the *correct* answer, which is "nothing". A check written to look for a
bad value can pass by never matching anything at all. Both directions need the "was the line found?" question
asked separately from "did the value match?" — which is what the fixed script now does.

## The 33 numbers that pass, by group

| group | count | what is checked |
|---|---|---|
| honesty numbers, base + job2 patch + job3 patch | 12 | each of bench 11/13/16 and perft 5 has a raw file whose line was found AND carries the exact expected node count |
| perf sample counts (job1, job1b, callchain run) | 3 | the `# Samples:` line is present in the raw report |
| job1b driver results | 4 | positions driven 200, refusal lines 0, zero-node searches 0 of 200, total nodes 14,077,298 |
| job2 ratios | 2 | 1.0059 treatment, 1.0002 control — both read from `ratio_ci.txt` |
| job3 ratios | 3 | 0.9190 full prefetch, 1.0021 lite, 0.9889 control |
| check verdicts | 4 | 21-F1, 28-C2, 29-F3, 08-F9 each have a `VERDICT ...` line saying what I reported |
| 19-F12 evidence | 3 | aborted case 0 nodes, searched case 56,720 nodes, plant/control YES |
| 19-F13 / 19-F14 | 2 | `pick_best` 7.93 %, and all four interleave cases completed |

## What this audit does NOT prove

- It does not re-derive any measurement. If a raw file itself were produced by a broken harness, its line
  would be "found" and the number would still be wrong. The harness-level vacuity question is a different
  check, and I answered it for the *driver* only (19-F12: I proved my driver waits for `bestmove`, with a
  plant/control).
- It covers only numbers I wrote down in a report. Numbers I quoted *about another seat's report* (e.g.
  seat 08's 329.09 / 217.09 / 18.84 / 34.56 ms in 19-C4) were checked against that seat's finding text, not
  against their raw files — I re-measured the claim myself instead, which is stronger, but the two are not
  the same thing.
- The three flags above were audit-script bugs. **I did not find a wrong number in any report.** That is the
  honest answer, and it is worth noting that the audit's value here was in proving the *absence* of a defect
  rather than in finding one.

## The lesson worth passing on

From the 08-F9 slip and from item 3 above, the two ways a parsed-number check goes vacuous are:
1. the parsed value is `None`/`NaN`/`0` and the comparison cannot fail on it (my 08-F9 attempt 1);
2. the regex cannot match the *correct* answer (item 3 — `(.+)` on an empty tail).
Both are prevented by the same discipline: assert the line was found, then compare the value, as two separate
steps, and make "the expected answer is empty" a case the parser is explicitly able to return.

## Files

- `vacuity_audit/vacuity_audit.py` — the audit, rerunnable
- `vacuity_audit/RESULT.txt` — the 33-row table
