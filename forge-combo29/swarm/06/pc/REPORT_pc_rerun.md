# REPORT — re-running seat 06's own findings on the PC r15 build under PC20

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
