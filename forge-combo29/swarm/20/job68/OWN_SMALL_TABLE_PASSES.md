# seat 20 — job 68: the own-small-table variant PASSES the acceptance test — and my job-67 "fail" used the wrong baseline

Job 67 concluded that *sharing* the table failed the line-quality half. Job 67's follow-up (an 8 MB **own**-table
variant) also appeared to fail — **because I compared it against the collapsed Hash-2048 build's lines.** That
baseline was wrong: the collapsed build publishes almost nothing meaningful. **The correct baseline is the HEALTHY
build** (same positions, Hash 16, where the engine works). Against that baseline the candidate passes.

## The measurement (Hash 2048, MultiPV 3, `go wtime 5000`, Threads 1, 5 G-set positions)

Candidate: the repaired tree with the alternate line keeping **its own table, capped at 8 MB**
(`alt_mb = min(hash_mb, 8)`). Reference: the same repaired build at **Hash 16** (healthy, uncollapsed).

| pos | reference lines at Hash 16 | **candidate lines at Hash 2048** | max diff |
|---|---|---|---|
| 1 | −292 / −293 / −316 | −292 / −293 / −316 | **0 cp** |
| 2 | −251 / −349 / −359 | −251 / −349 / −359 | **0 cp** |
| 3 | 312 / 220 / 218 | 312 / 220 / 218 | **0 cp** |
| 4 | −660 / −733 / −743 | −660 / −733 / −743 | **0 cp** |
| 5 | −605 / −1152 / −1264 | −605 / −1199 / −1268 | **47 cp** |

Main-line depth at Hash 2048: **1 → 13–15 plies.**

**Both halves of the acceptance test pass:** depth restored (13–15 against the healthy 14), and alternate lines
reproduce the healthy build to within **47 cp worst case and 0 cp on four of five positions** — against the
775–988 cp that the two rejected variants moved them.

## My error, stated plainly
In job 67 I compared the candidate against the **collapsed** build and read a 988 cp difference as a failure. That was
a wrong reference point: when the baseline itself publishes garbage (depth 1, no usable lines), any working candidate
"differs" from it enormously. **The failure I reported was the baseline's, not the candidate's.**

Same error class as S-C20: a comparison whose reference I had not checked. The lesson generalises —
**before calling a candidate worse, check that the reference is working.**

## What this means for the requirement
S-F56's requirement — *restore main-line depth at large Hash without moving the alternate lines' scores* — is
**satisfiable**, and the direction that works is: **the alternate line keeps its OWN table (independent bounds
preserved) but that table is sized small**, because only the extra PV lines use it. Sharing fails (the alternate line
inherits bounds computed for a different root restriction); keeping it own-and-small passes.

## Still not a proposal to adopt
- **5 positions, one clock, MultiPV 3, Threads 1, built-in net.** The 47 cp outlier on position 5 shows the invariance
  is not exact.
- **The tolerance is an owner decision:** 47 cp is fine for "the lines still say the same thing" and not fine if the
  requirement is bit-identical.
- I did not test MultiPV 2 or 8, deeper clocks, or whether the 8 MB table can **saturate** on long games.
- The right next step is not another variant — it is **a wider position sample at a stated tolerance**, plus a check
  that 8 MB never fills.
