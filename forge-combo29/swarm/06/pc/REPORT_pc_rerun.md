# REPORT — re-running seat 06's own findings on the PC r15 build under PC20

## HEADLINE

**The search asymmetry is present in the engine the owner actually plays, at a rate indistinguishable
from the base tree.** On the same 353 G positions at depth 10, Threads 1: the PC r15 build gives **120 of 353
(34.0%)** mismatched bestmoves and **331 of 353 (93.8%)** differing scores; the base tree gives **101 of 353
(28.6%)** and **334 of 353 (94.6%)**. The Wilson intervals overlap (PC 29.2–39.1%, base 24.1–33.5%), so **the
effect is not a base-tree artefact** — it survives every search repair and every new switch the PC build carries.
That joint statement, not either single number, is the finding: the owner's engine has this property too.

**And it predates the PC's new search code.** With the four new switches OFF (S14 only) the PC build already
gives **102 of 353 (28.9%)**, i.e. the base tree's rate within a point; switching them all ON (PC20) gives 34.0%.
A paired McNemar test on the same 353 positions gives p = 0.098 for bestmoves and p = 0.815 for scores — not
significant. So the cause is **not** in CuckooRep / HistRework / TtPruneV2 / CorrHistV2 / MateAlphaGuard; it is
older than them, and an owner deciding where to spend time should look at the shared search core, not the new
switches.

Build: FABLE_TO_swarm_5's r15 patch on a fresh export of 6b98f217, `patch -p1` (11 files, no fuzz),
g++-13.3.0 Release `-DFORGE_MARCH=x86-64-v4 -DFORGE_MATE_ALPHA_GUARD=1`.
Pin check: all seven numbers FABLE 5 pins reproduced exactly (see `HONESTY_pc.txt`).
Settings: **PC20** (Threads 1, Hash 16, the 14 S14 settings, CuckooRep true, HistRework 2, TtPruneV2 true,
CorrHistV2 true, MateAlphaGuard true, OwnBook false). **Threads 1 everywhere** (owner's rule of 2026-11-16).

## Verdict per finding

| finding | base build, S14 | PC r15 build, PC20 | verdict |
|---|---|---|---|
| S-F1 the `eval` command is exactly colour-symmetric | 0 differences in 8,103 pairs | **0 differences in 353 pairs** | **HOLDS on the PC build** |
| S-F6 the depth-10 search is not colour-symmetric | 101/353 bestmoves, 334/353 scores | **120/353 (34.0%) bestmoves, 331/353 (93.8%) scores** | **NOT repaired — persists, slightly worse** |
| S-F2 an unreachable ep square is refused | refused | refused (same board parser, unchanged by the patch) | holds |
| S-F19/S-F22 (state probes, totals are not a symmetry test) | — | not re-run; they are harness properties, not build properties | unaffected |

## The two measurement tables (pasted output of the committed scripts)

`table_pc_eval.txt` (S-F1 on the PC build):

```
pairs compared: 353
pairs with ANY hce/nnue/total difference: 0
```

`table_pc_search_counts.txt` (S-F6 on the PC build, next to the base-build numbers for the same 353 positions):

```
PC r15 build, PC20, Threads 1, depth 10, 353 G positions:
  bestmove differs after mirroring : 120 of 353 (34.0%)
  score differs                    : 331 of 353 (93.8%)

BASE build, S14, Threads 1, depth 10, same 353 positions (from job 3):
  bestmove differs after mirroring : 101 of 353 (28.6%)
  score differs                    : 334 of 353 (94.6%)
```

## What this means

- **The evaluation symmetry is a property of the evaluation, and survives the PC's search changes.**
- **The search asymmetry is NOT one of the defects the PC patch repairs.** The patch fixes the drawn root, the
  `go` parse, isready pending, abort publish, the hard-limit emergency, bare-king LMR and bare-king one-thread —
  none of which is this. On the PC build the rate is 34.0% versus 28.6% on the base build; the two Wilson
  intervals (PC 29.2–39.1%, base 24.1–33.5%) overlap, so I do **not** claim the PC build is worse — I claim only
  that the asymmetry is still there and is not repaired.
- Consequence for the PC: its scores are not exactly mirror-invariant either. That does not make them wrong —
  S-F22 already says a differing search is not a defect — but it does mean any PC-side test that assumes mirror
  symmetry of *search* will fail, while a test of `eval` symmetry will pass.

## What I did NOT do

- Did not re-run S-F19's three state-probe modes on the PC build (they measure harness behaviour, and they cost
  706 processes; the conclusion would not change).
- Did not measure the PC build at Threads > 1 for any of this: the owner's rule forbids reporting such a score.
- Did not test the four new search switches individually (CuckooRep / HistRework / TtPruneV2 / CorrHistV2) to see
  which, if any, changes the asymmetry. That is a clean follow-up and the harness already takes an option list.

## The switch test: does the new search code cause it? No.

Same 353 G pairs, depth 10, Threads 1, on the PC r15 build. The only difference between the two rows is the six
PC20 options. Pasted output of `table_switches.txt`:

```
| settings | bestmoves mismatched | rate | Wilson 95% CI | scores differed | rate |
|---|---|---|---|---|---|
| PC r15, S14 only (four switches OFF) | 102/353 | 28.9% | 24.4 - 33.8% | 333/353 | 94.3% |
| PC r15, PC20 (four switches ON + MateAlphaGuard) | 120/353 | 34.0% | 29.2 - 39.1% | 331/353 | 93.8% |
```

Paired comparison on the identical positions (`table_switches_stats.txt`):

```
bestmove mismatch: discordant pairs 106 (only-S14 44, only-PC20 62); concordant 247; McNemar exact p = 0.098
score difference:  discordant pairs 18 (only-S14 10, only-PC20 8);   concordant 335; McNemar exact p = 0.815
```

Reading, stated carefully because the bestmove p is 0.098 and not 0.5:

- **The switches do not create the asymmetry.** With them all off the rate is 28.9%, statistically the base
  tree's 28.6%. There is nothing to attribute to the new code.
- **The +5.1 pp move when they are on is not significant** (p = 0.098, one test, and the two intervals overlap
  heavily). I do not claim the switches make it worse; I claim only that they do not make it better and are not
  the origin.
- **The score measure is flat** across the two regimes (94.3% vs 93.8%, p = 0.815), so the score asymmetry is
  entirely independent of the new code.
- **Consequence for the owner**: the asymmetry predates the r15 switches. Time spent on CuckooRep, HistRework,
  TtPruneV2, CorrHistV2 or MateAlphaGuard will not remove it; the shared search core is where it lives.
