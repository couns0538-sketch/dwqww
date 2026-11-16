# ADDENDUM — deepseek6, long 8, the moved values I did not run the first time

Written before the first measuring command of this addendum. The original `PREDICTION.md` is NOT edited;
this is a new commit because the rule is "never edited", not "never added to".

## Why

The long-8 report (commit `deepseek6 long 8 report`) says plainly:

> "I did not run the moved value for EVERY option of `SoundArms` (three arms) or `NodeLiterals` (eight
> options); long 8 says 'each option moved once', and I moved one per SET rather than one per option. **This
> is a real shortfall against the wording**."

Long 8's own text is "with its options at their defaults AND with each option moved once". This addendum
finishes that: the remaining moved values, same builds, same harness, same protocol.

## The remaining moved values

`SoundArms` — already run: `SoundPvArm=1`. Remaining:

| option | moved to | why that value |
|---|---|---|
| `SoundInCheckArm` | 1 | long 4a measured it wired on O (9,473,683) |
| `SoundMateAlphaArm` | 1 | long 4a measured it SILENT on O but wired on G (18,688,400), so both sets are needed |

`SoundSteps` chain — already run: `SoundPvArm=1;SoundStepMask=0` (which is the identity case, an error I
recorded). Remaining, and each is a value long 4b measured as WIRED:

| option | moved to | long 4b evidence |
|---|---|---|
| `SoundStepMask` (with `SoundPvArm=1`) | 8 | bit 3 (quiet SEE) = 10,206,405, the largest single bit |
| `SoundStepMask` (with `SoundPvArm=1`) | 1 | bit 0 (LMP) = 9,476,627 |
| `SoundRegretCount` | true | not measured by me before; a check option, must be inert at the default and this turns it on |
| `SoundRegretProbe` | true | same |

`NodeLiterals` — already run: `NullStaticBase=360`. Remaining seven, each at a value long 5a measured as wired:

| option | moved to | long 5a O/S14 sum with it |
|---|---|---|
| `NullStaticSlope` | 48 | 9,612,192 |
| `NullEvalRedMax` | 0 | 9,518,441 |
| `NullVerifyDepth` | 1 | 9,627,015 |
| `ProbcutImproving` | 0 | 9,594,013 |
| `ProbcutReduction` | 6 | 9,653,016 |
| `ProbcutTtSlack` | 1 | 9,543,675 |
| `ProbcutStoreReduction` | 1 | 9,462,347 |

`IirNoRoot` — already run: `IirRootExclude=1` (inert without searchmoves, which long 6 explained). Nothing
remaining: it has one option.

That is 13 more settings x 553 positions = 7,189 more positions under the sanitizer.

## Predictions

| prediction | killed by |
|---|---|
| **0 sanitizer lines** on every one of the 13 settings | any sanitizer line |
| every position exits 0 | any nonzero exit |
| the DEFAULTS are unchanged from the original long-8 run (same rows, same sums), because nothing about the default build changed | any defaults-sum difference, which would mean my earlier table is wrong |
| `SoundRegretCount=true` and `SoundRegretProbe=true` change the tree (they are counters but the probe walks the board) — I predict DIFFER, and if they do not I will say the option is unmeasured-by-node-counts rather than unwired | exactly the defaults sum |
| `SoundMateAlphaArm=1` changes G but not O (long 4a's result) | differing from long 4a's direction |

I predict no node sum for the others: the point of this addendum is the sanitizer count, and long 3's lesson
says a band on a sum of steps is a guess.
