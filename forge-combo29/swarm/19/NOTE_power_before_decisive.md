# NOTE_power_before_decisive.md — compute the power of a separator before calling it decisive

**The rule, one line:**
> **A discriminator is a hypothesis test. Its power must be computed BEFORE it is announced as decisive.**

This is trap 16 in `HARNESS_TRAPS.md`. It is written separately because it is a short *procedure*, not just a
cautionary story, and because the procedure is what I got wrong.

## The procedure, four steps, in this order
1. **State the two hypotheses as rates.** Not as "different" — as numbers. (Mine: 41.4 % vs 63.6 %.)
2. **Compute how many DECIDED cells are needed** to separate those two rates at ~80 % power by whatever test you
   intend (here the two-sided sign test). For 41 % vs 64 % the answer is **≈ 48 decided cells**.
3. **Check whether the sample you are about to run yields that many DECIDED cells — not rows.** If it yields 14,
   the answer is 14.
4. **If step 3 fails, say "this cannot settle it"** — do not announce it as the separator.

Step 3 is where I failed, and it fails silently: nothing about a 200-position run *looks* like a 14-cell
experiment.

## The tell: the tie rate sets the effective n
| what I quoted | what it was |
|---|---|
| 103 same-move quiet cells | **14 decided** — 89 ties contributing nothing |
| "n = 29" for the pooled claim | same error at smaller scale; power **0.15** |

**A high tie rate means the rows are not the sample.** Quote the decided count, or quote the power, or both —
never the row count alone as though it were the sample size.

## The second half: stratify on the lever that governs power
I stratified on **material balance**, because it was the variable where the two position sets differed most
(43.5 % vs 22.0 % sharp, z = 5.91). That was the wrong lever for this purpose: **material balance does not
control the tie rate.** What sets the decided count at a fixed node budget is how many positions sit **near the
depth boundary**, where one extra iteration is available to one engine and not the other.

**"The variable that differs most" and "the variable that governs power" are different questions.** It is tempting
to stratify on the first because the difference is visible and testable; that is precisely why it is a trap.

## Where this sits next to trap 12b
| | what cannot discriminate | how the failure looks |
|---|---|---|
| **trap 12b** | the **metric** — a uniform zero across all arms | `0 of 8` everywhere; looks like four nulls |
| **trap 16** | the **sample** — an interval containing both hypotheses | `7 of 14`; looks like a result |

**Both produce a null that reads as information and carries none.** Neither failure is visible in the result, so
the check has to happen on the instrument before the run. That is the general habit: **before asking "what does
this number say", ask "could this number have said anything".**

## What a properly-powered version would look like here
- **≈ 48 decided quiet cells** → at my observed tie rate that is **≈ 600–700 quiet positions**.
- Which is why the other seat, holding 600 positions, could settle it and I could not.
- **A cheaper route than more positions: pick positions near the depth boundary**, which raises the decided
  fraction instead of the row count. That is the fix I would use next time.
