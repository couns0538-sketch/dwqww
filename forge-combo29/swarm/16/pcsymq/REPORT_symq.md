# REPORT_symq — does symmetrising the PSQT table remove the colour SCORE gap on the PC build?

**What was asked (my own last open question in area 6):** S-C3 showed on the BASE tree that symmetrising the
tuned PSQT table takes LEFT-RIGHT hce differences to 0/334. Does the same change remove the COLOUR-mirror search
score gap I measured on the PC build (S-F22/S-F23)?

**The answer: NO. Symmetrising the PSQT table does not remove the colour score gap — if anything the median gap
grows slightly, which is noise.**

```
build            n   score_equal   median |gap|   p90   move_mismatch
PC base PSQT    60        3            11 cp       85        22
PC symm PSQT    60        2            19 cp       69        18
```

**This is a clean negative that closes the loop.** It means the two asymmetries are DIFFERENT phenomena:

- **Left-right (S-C3, base tree):** entirely the PSQT table. Symmetrising it took hce differences 328/334 → 0/334.
- **Colour-mirror search scores (this job, PC build):** NOT the PSQT table. Symmetrising it moves the median gap
  11 → 19 cp (with ~60 pairs the approximate SE is 6–10 cp, so the two are indistinguishable) and the move
  mismatch 22 → 18.

So the colour score gap is a property of the SEARCH (order dependence, per S-F11/S-F12/S-F21 and S-F23's
"does not shrink with depth"), not of the evaluation. That is consistent with every other result I have in this
area, and it rules out the one fix that worked for the other asymmetry.

**How sure:** high on the direction (no improvement), medium on the magnitude (60 positions, overlapping
intervals). The important claim — "symmetrising PSQT does not fix it" — rests on the fact that the gap did not
fall below the base build's, when a real fix would take it near zero as it did for left-right hce.

## Honesty numbers

```
PC base  /home/ubuntu/builds/bld-pc/forge    sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
         none 312866 / S14 242796 / PC20 278024   (all match file 5)
PC symm  /home/ubuntu/builds/bld-pcsymq/forge  = PC r15 with src/eval_params_table.inc symmetrised by
         check_S-F3/symmetrise_psqt.py (368 lines rewritten, the same script used for S-C3)
         EXPERIMENT build: its bench numbers are not expected to match file 5 and none are claimed.
settings PC20 + Threads 1 + Hash 16, depth 10, 60 no-castling G positions, cold per search
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| hce colour-mirror check on both builds (control) | done | run output above | 0/20 differs on BOTH — colour hce was already symmetric, as S-F1/S-C2 found |
| depth-10 score gap, 60 positions, both builds | done | `run.log` | base 11 cp median; symmetrised 19 cp — no improvement |
| move mismatch, both builds | done | `run.log` | 22 vs 18 |
| left-right hce (the thing PSQT DOES fix) | done earlier | `../check_S-F3/raw/G_sympsqt.tsv` | 328/334 → 0/334 |

## Findings

`S-F25 | 6 | symmetrising the tuned PSQT table does NOT remove the colour-mirror search SCORE gap on the PC build: with PC20 at Threads 1 depth 10 over 60 positions the median mirror score gap is 11 cp on the shipped build and 19 cp on the symmetrised build (intervals overlap; no improvement), move mismatch 22 vs 18 — so the colour score gap is a SEARCH property (order dependence, and per S-F23 it does not shrink with depth), not an evaluation property, and it is a different phenomenon from the left-right asymmetry, which the same table change fixes completely (S-C3: 328/334 -> 0/334) | pcsymq/run.log pcsymq/symq_scoregap.py | NEW |`

## Suspicions, not proven

- That no evaluation change could remove the colour gap, only a search-level determinism change. The one search
  change I tried (full-window root, S-F8) made it worse, which points that way.

## What I did NOT do

- Did not test the symmetrised build on the full 353 pairs (60 positions was enough to see no improvement).
- Did not test other evaluation changes (net, corrections); out of reach without the PC's trained net.

## Times

`pcsymq/stamps.txt`, every line a `date -u`.
