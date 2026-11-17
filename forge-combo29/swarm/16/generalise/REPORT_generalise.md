# REPORT_generalise — does S-F35 GENERALISE? 60 positions × 2 depths = 120 cases

**Why this job exists:** S-F35 concluded the colour asymmetry is *completely* explained by move-generation order on
the evidence of **15 cases** (5 positions × 3 depths). My own STANDING CAUTION, habit 3, says a small sample is not
a property — and "completely" is precisely the kind of word that needs a larger N before it stands. This tests it.

**The answer: it generalises completely. 120 of 120 cases equal on the canonical build, against 34 of 120 on the
base build, with zero residue and zero cases the fix broke.**

```
depth | base equal | canonical equal
    1 |   25 / 60  |     60 / 60
    2 |    9 / 60  |     60 / 60
  ALL |   34 / 120 |    120 / 120

cases the fix BROKE (equal before, unequal after): 0
canonical RESIDUE cases:                           0
```

**P1 confirmed** (my bar was ≥115 of 120; measured 120). **P2 confirmed** (base 34 of 120, well under my 40 bar, so
the comparison is meaningful rather than both-sides-equal-by-accident). **P3 confirmed** (zero broken cases — the
fix never damages a pair that was already fine). **P4 REFUTED, in the good direction:** I predicted depth 1 would
be equal more often than depth 2 *if a residue existed*; with no residue at all, both depths are perfectly equal,
so the prediction's premise never arose. Recording it as refuted rather than quietly dropping it.

**What this changes:** S-F35's word "completely" now rests on **120 cases rather than 15**, across two depths, with
a base-build baseline showing how much asymmetry is being removed (34 → 120 of 120 equal). The finding can be
stated without the caveat I would otherwise have owed: *the colour-mirror search asymmetry of this engine is
entirely move-generation order.*

**What it still does not change:** it remains a DIAGNOSTIC. The canonical order discards the tuned ordering that
gives the engine its strength, and my S-F36 attempt at a cheap strength-preserving variant failed (7 of 15) with a
source-verified explanation. Nothing in this job suggests the owner should adopt the ordering.

**How sure:** high. 480 searches (60 positions × 2 depths × 2 mirror searches × 2 builds), PC20, Threads 1,
Hash 16, cold, mirrors computed with python-chess rather than typed.

## Honesty numbers

```
base      /home/ubuntu/builds/bld-pc/forge      none 312866 / S14 242796 / PC20 278024  (all match file 5)
canonical /home/ubuntu/builds/bld-mirord3/forge = PC r15 + EXPERIMENT_mirror_order.patch.txt, switch ON
          EXPERIMENT build: bench pins not claimed (the order changes the tree by design)
settings  PC20 + Threads 1 + Hash 16, cold per search, depths 1 and 2, 60 G positions + colour mirrors
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 60 positions × 2 depths × 2 builds | done | `raw/generalise.txt`, `run.log` | 120/120 canonical vs 34/120 base |
| per-depth breakdown | done | same | depth 1: 25→60 of 60; depth 2: 9→60 of 60 |
| did the fix break any case? | done | same | 0 broken |
| residue inspection | done | same | 0 residue cases to inspect |
| depths 3+ at this scale | NOT done | — | depth 1 and 2 answer the generality question |

## Findings

`S-F37 | 6 | S-F35 GENERALISES: on 60 G positions at depths 1 and 2 (120 cases) the fully canonicalised build is equal on mirror node counts in 120 of 120 cases against 34 of 120 on the base PC r15 build — depth 1 25/60 → 60/60, depth 2 9/60 → 60/60 — with ZERO residue and ZERO cases the fix broke. So "the colour-mirror asymmetry is entirely move-generation order" now rests on 120 cases rather than 15, and the S-F35 caveat about sample size can be withdrawn | generalise/raw/generalise.txt generalise/run.log (again: `python3 generalise/generalise.py ~/builds/bld-pc/forge ~/builds/bld-mirord3/forge /tmp/o`) | NEW |`

## Suspicions, not proven

- That the same holds for every position. 120 cases across two depths is strong but not exhaustive; the mechanism
  (order correspondence at every generation site) is what makes me confident beyond the sample, and the sample is
  what tests the mechanism.

## What I did NOT do

- Did not test depths 3-6 at this scale (cost; the two depths answer the generality question and the mechanism is
  depth-independent by construction).
- Did not test the R position set, only G.

## Times

`generalise/stamps.txt`, every line a `date -u`.
