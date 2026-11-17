# The plan, computed — the reference table for this area

Twice tonight I wrote plan arithmetic from memory and got it wrong (once as "soft 72 / hard 360" for a 1600 ms
clock, once as "soft 8 / hard 40" for 200 ms — the true values are 117/585 and 53/114). Prose arithmetic is the
failure mode, so this file is the table, computed by `audit_plan_numbers.py` from `include/forge/clock_plan.hpp`'s
formula with the engine's own defaults (`Move Overhead 10`, `TmSoftDivisor 22`, `TmIncrementPercent 75`,
`TmHardPercent 60`, `TmHardSoftMultiple 5`).

**Any plan number in this area's files should be checked against this table, not against my prose.**

## Sudden-death clocks, no increment

| clock ms | soft | hard | reserve empty? |
|---|---|---|---|
| 0 | 0 | 0 | YES |
| 1 | 0 | 0 | YES |
| 10 | 0 | 0 | YES |
| 11 | 1 | 1 | no |
| 30 | 1 | 1 | no |
| 100 | 4 | 20 | no |
| 200 | 8 | 40 | no |
| 500 | 22 | 110 | no |
| 1000 | 45 | 225 | no |
| 1600 | 72 | 360 | no |
| 3000 | 135 | 675 | no |
| 6000 | 272 | 1360 | no |
| 10000 | 454 | 2270 | no |
| 30000 | 1363 | 6815 | no |

Note the row at **1600 ms: soft 72 / hard 360** — that is the NO-INCREMENT plan, and it is where my earlier mis-stated
"72 / 360" actually came from: I applied the sudden-death plan to an increment-60 context, where the true values are
**117 / 585**. Both numbers are correct for their own regime, which is precisely why the regime must be stated with
the number.

## The owner's control (increment 60) — the clocks this area actually uses

| clock ms | inc | soft | hard |
|---|---|---|---|
| 200 | 60 | **53** | **114** |
| 400 | 60 | **62** | **234** |
| 800 | 60 | **80** | **400** |
| 1200 | 60 | **99** | **495** |
| 1600 | 60 | **117** | **585** |
| 3000 | 60 | **180** | **900** |
| 6000 | 60 | **317** | **1585** |
| 10000 | 60 | **499** | **2495** |
| 30000 | 60 | **1408** | **7040** |

The bold rows that matter most: at the owner's 6 s control the plan is **soft 317 / hard 1585**; at 1600 ms it is
**117 / 585**. The **1585 ms** figure that recurs throughout this area's work is the **hard** limit at 6 s, which is
why the worst observed move lands there.

## `movestogo` at a 1000 ms clock, no increment (the job 3 controls)

| movestogo | soft | hard |
|---|---|---|
| 1 | 495 | 792 |
| 2 | 330 | 792 |
| 40 | 24 | 96 |
| 50 | 19 | 76 |

## The automated check
`audit_plan_numbers.py` also greps every `.md` file in this folder for the pattern `soft N / hard M` and reports any
pair that matches no computed plan. Last run: **1 claim found, 1 matched, 0 unmatched.** That is a narrow pattern —
it would not have caught my "72 / 360" prose because I wrote it as "soft 72 / hard 360 ms" inside a different
sentence shape — so the table above is the real protection and the grep is a backstop.

## Honest note on why this file exists at all
I stated plan arithmetic confidently three times tonight and was wrong twice. The computation is four lines of
integer arithmetic, so there is no reason to ever state it from memory: this table removes the temptation.
