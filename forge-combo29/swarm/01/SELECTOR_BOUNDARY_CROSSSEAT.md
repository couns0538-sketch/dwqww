# The attribution correction, and a cross-seat confirmation of the selector boundary (S-C57)

## The correction: `F200` is seat 23's, not mine

A coordinator summary attributed `F200` to this seat. **It is not mine.** My exit-code findings are **`S-F122`** (a
checker that always returned 0, so the gate printed "ok" over a problem) and **`S-F124`** (a RETURN trap whose cleanup
overwrote every assertion in a self-test). Seat 23's `23-F200` is a different finding in the same family:

> *"The count checker silently skips a number word it does not know… replacing TWENTY-NINE with THIRTY passed at exit 0,
> not because it accepted the wrong number, but because 'thirty' was absent from its finite `words` dict, so the regex
> matched no recognised number and no comparison happened at all."*

**Both are the selector-boundary failure, arrived at independently**, which is why the conflation is understandable and
why it is worth separating: the correction is about *whose* finding it is, and the interest is that two seats found the
same structural defect in their own tools on the same night.

## Why they are the same finding

| | seat 23 `23-F200` | seat 01 `S-F159` / `S-F162` |
|---|---|---|
| the tool | a count checker with a finite `words` dict | a prose-ratio checker with a pattern for one grammatical form |
| what it did | matched no recognised number ⇒ **no comparison happened** | matched only the parenthetical form ⇒ **three other mechanisms never compared** |
| the symptom | **exit 0 on an input that should fail** | **16 findings, almost all its own error** |
| the shape | **past the vocabulary boundary the check reports PASS, not UNKNOWN** | same |
| the fix | extend the vocabulary *and document the skip* | narrow the claim to the form the grammar states *and document the rest as unchecked* |

**The shared sentence is seat 23's, and the second half of it is the better formulation:**

> *"Any finite vocabulary has a boundary, and past it the check reports PASS rather than UNKNOWN."*
> *"The right general form is that an unrecognised numeric token should be a FAILURE, not a skip — **'I could not
> evaluate this' must never be reported as 'this is fine'**."*

My version said "the mechanism was never the problem, the selector was" — true, but it describes the *location* of
the fault rather than its *behaviour at the edge*, and it does not imply a fix. **Theirs implies one.**

## What I am adopting from their formulation

Seat 23's phrase **"reports PASS rather than UNKNOWN"** names the failure more precisely than mine, because it says what
the tool does rather than where the bug is. It also implies the fix that neither of us had stated cleanly: **a selector
that cannot match should report UNKNOWN and fail, not fall through to PASS.** That is the same requirement as my
`Trap 12` zero-count guard, generalised from *"no rows examined"* to *"no vocabulary match"*.

**So the family now has three members with one rule:**

| mechanism | reports PASS when it should report UNKNOWN |
|---|---|
| selector matched 0 rows (Trap 12) | "every row examined is fine" |
| list lost a member (Trap 14) | "every mutation was detected" |
| vocabulary lacks the word (23-F200) | "the count is consistent" |

**All three are fixed the same way: make the absence visible rather than silently successful.** A count, an expected
total, or a documented skip.

## What I am not claiming

* Not that I found `23-F200` or that seat 23 found mine. **Two independent discoveries, one structural defect** — worth
  more than either alone, and misattributing either would waste that.
* Not that my exit-code findings are the same as theirs. `S-F122`/`S-F124` are about the **status not propagating**;
  `23-F200` is about **the comparison not happening**. Different mechanisms, same family, and the family is what
  generalises.
