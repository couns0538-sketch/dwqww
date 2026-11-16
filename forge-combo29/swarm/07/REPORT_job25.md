# REPORT — seat 07, job 25: 07-F2 WITHDRAWN — the repository already documented this option

## What was asked / the answer / how sure

**Asked:** search the repository for any record of `LmrSignedCorrection` having been tuned, and
report it: evidence of tuning means quote it in FINDINGS; absence means say the absence supports the
reading that the option was added and never activated.

**Answer:** **there is a record, and it refutes my own finding 07-F2.** `forge-combo29/REPORT_r3_03.md`
is a full report on this option; it states the very arithmetic I got wrong, records the divisor being
deliberately changed from `/8` to `/64` in a follow-up, and explains why the option does not move the
depth-13 bench tree. The repository also ships a unit test for the function. **07-F2 is withdrawn in
full (07-R2).**

**How sure:** very high — the refutation is a quoted document in the tree plus a unit test with
`{3, 64, 2, "64cp better subtracts one ply"}` among its cases, and I re-derived the bound by hand and
in code.

## Where my proof was wrong

07-F2 enumerated **one** correction table:

    per-table cap: 32 cp

and concluded `correction_cp ∈ [-32, 32]`, so `correction_cp / 64 == 0` always. But
`corrected_eval` (`src/search.cpp:1217-1226`) builds `correction` as a **sum**:

    std::int32_t correction = pawn_table[...];
    if (MaterialCorrectionWeight > 0) correction += material_table[...] * weight / 100;
    if (NonPawnCorrection)            correction += (np_w + np_b) / 2;
    return std::clamp(raw_eval + correction / CorrectionGrain, ...);

So the reachable bound is the sum, not one table:

    default tables summed (pawn + material): 64 cp
    with NonPawnCorrection (pawn + material + avg of 2 nonpawn): 96 cp
    reachable (reduction, correction_cp) pairs where the reduction CHANGES: 2013 of 5983

At ±64 cp the step is exactly one ply, so the option is **live** — just rarely. That is precisely what
the existing report says.

## The record, quoted

From `forge-combo29/REPORT_r3_03.md`:

- line 78: *"The previous adjustment subtracted `correction_cp / 8` with no cap, so a large
  correction moved the reduction by several plies. The follow-up rule subtracts `correction_cp / 64`,
  rounded toward zero, then limits that adjustment to -1..+1."*
- line 79: *"A correction inside -63..+63 centipawns changes nothing."*
- line 87: *"bench 13 with `LmrSignedCorrection` on: 862329. The same count as option off. A one-ply
  step needs 64 centipawns, and each correction table caps at 32, so the step happens only when the
  pawn and material corrections are both saturated on the same side. That did not change the
  depth-13 bench tree."*
- line 49 (an earlier build, divisor /8): *"bench 13: 1244366 nodes ... The count differs from 862329,
  so the option is live."*
- line 10: *"It was not tuned for strength, and this report does not claim a strength result."*

And the unit test `forge-combo29/tests_r3_03/lmr_signed_correction_test.cpp` asserts the intended
behaviour directly, including `{3, 64, 2, "64cp better subtracts one ply"}` and
`{3, 1000, 2, "a large positive correction is limited to one ply"}`.

## What I checked at the end to be sure

Re-ran the exact command the report used, on my build:

    bench 13 with LmrSignedCorrection ON : nodes 862329
    bench 13 with LmrSignedCorrection OFF: nodes 862329

Identical — matching the report's own line 87. So the observation was right; my *explanation* of it
(dead code) was wrong.

## Answer to the question the owner actually asked

**Whether to delete the option or repair the divisor:** neither, on this evidence. The divisor was
already repaired once (from `/8` to `/64`, documented in the same file), the current constant was
chosen deliberately with its consequence stated, and the option can act when the correction tables
saturate together. **The option should be left alone**, and `REPORT_r3_03.md` is the document to read
before touching it.

## Findings

**07-R2** in FINDINGS.md, and the 07-F2 row is rewritten to say WITHDRAWN in its first words so a
reader scanning the table cannot pick up the dead conclusion.

## Suspicions, not proven

- Whether the option ever fires in real games on this build. Its inertness on bench 13 is documented;
  its frequency elsewhere is not, and no strength result was claimed by the original report either.

## What I did NOT do

- Did not re-run the original screening matches (`screen_r3fu_03/`); the report itself says they are
  screening, not a strength claim.

## What I am NOT sure about

- Nothing that affects this withdrawal: the record, the code and my re-run all agree.

## Times

See job25/stamps.txt.
