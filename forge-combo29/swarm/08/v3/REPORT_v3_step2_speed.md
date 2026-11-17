# Step 2 — the v3 count-dispatch patch: identity EXACT, and a real +1.2 % speed win — seat 08

## The patch
`v3/v3_pair_count_dispatch.patch.txt` — a unified diff against **file 5's tree** (6b98f217 + `pc_r15.patch`),
67 lines, **applies with `patch -p1 --fuzz=0`, no rejects**.

`apply_changes_pair_avx512` re-tested `i < c.count` **inside** the 32-lane `h` loop, for both perspectives. The patch
dispatches **once on `c.count`** (1/2/3/4, the ceiling `collect_changes` already enforces) into unrolled
specialisations, so each slot's liveness is decided outside the `h` loop. Arithmetic per element, slot order and lanes
are unchanged — by construction the results are bit-identical, and the identity check tests exactly that.

## Identity: EXACT on a build made from a CLEAN tree
Applied the patch to a fresh 6b98f217 worktree, re-applied file 5's patch, then mine, built with
`-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`, g++ 13.3.0:

| check | required | verified build |
|---|---|---|
| bench 11 / 13, no setoption | 312866 / 862329 | **312866 / 862329** |
| bench 11 / 13, PC20 | 278024 / 587276 | **278024 / 587276** |
| bench 11 / 13, test net | 965454 / 4151906 | **965454 / 4151906** |
| bench 11 / 13, PC20 + net | 625258 / 3652372 | **625258 / 3652372** |
| eval 968 / 1176 / 31 | exact | **968 / 1176 / 31** |
| **200-opening node sum** | **27,944,084** | **27,944,084** |

**Every identity row reproduces.** Per file 7 Step 2, that makes this a legitimate speed patch.

## Speed: a REAL effect, and my first verdict was wrong
**Bench arm** (`bench 13`, PC20 + net, alternating base/patch, 10 runs each): base median **2126 ms**, patch median
**2092 ms**, ratio **0.9838** (**+1.6 %**), **node counts identical in every pair**.

**Real-position arm** — the one the coordinator required. Fixed `go nodes 200000`, **ABBA** (base, patch, patch, base)
per position, **n = 120**, PC20 + test net:

| quantity | value |
|---|---|
| positions with a full quartet | **120** |
| **median ratio patch/base** | **0.9878** (**+1.2 % faster**) |
| 2.5th / 97.5th percentile | 0.961 / 1.026 |
| per-position spread (max/min) | **1.58x** |
| **positions where the patch is faster** | **107 of 120** |
| **two-sided sign test** | **p = 1.5e-19** |
| node counts matched | **120 of 120** |

## MY FIRST VERDICT WAS WRONG, and the error is the interesting part
My first version of the verdict said **"NOT MEASURABLE — the per-position spread (1.30x) is much larger than the
median effect (1.2 %), so the change cannot be separated from position variation."** That is **wrong reasoning**:

- **The per-position spread describes how much positions differ from EACH OTHER.**
- **A paired ABBA design cancels exactly that** — each position is its own control, and the comparison is
  within-position.
- So the correct question is **"does the patch win within positions?"**, i.e. a **sign test on the paired outcomes**
  — not "is the median effect bigger than the between-position spread".

On those 120 pairs the patch wins **107 times**, p = 1.5e-19. **Spread is context, not the test.** I had written a
rule that would have thrown away a real, well-supported result — and it would have done so in the safe-sounding
direction ("we are being conservative"), which is the kind of error that survives review.

This is the **seventh** label-or-reasoning failure in this seat and the first one that would have *discarded* a true
finding rather than overstating one. Recorded as **08-W7**.

## So the recommendation, within the rules
**The patch is measurably faster: +1.2 % (paired median) and +1.6 % (bench), with identical node counts, 107 of 120
positions favouring it at p = 1.5e-19.** It is small, and the honest caveats are:
- my compiler is **g++ 13.3.0, no `-march`**; the PC uses **clang + `-march=znver5` + PGO**, and a different compiler
  can turn an explicit unroll into nothing (or into more);
- the net is the **shared-shape test net**, not the PC's trained one;
- **the PC should time it itself**, two builds per variant, exactly as file 7 Step 3 requires — this arm is evidence
  that the patch is worth that measurement, not a substitute for it.

## What this does NOT claim
- No strength claim: node counts are identical by construction, so any strength difference would be noise.
- Not a claim about the PC's build. It is a claim about **this** build, stated with its compiler.

## Show it again
    cd /tmp/pcbase_clean/forge-combo29 && patch -p1 --fuzz=0 < <repo>/forge-combo29/swarm/08/v3/v3_pair_count_dispatch.patch.txt
    cd <repo>/forge-combo29/swarm/08/v3 && python3 speed_step2.py /tmp/speed.txt   # both arms
