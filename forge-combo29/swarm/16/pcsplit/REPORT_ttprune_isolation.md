# REPORT_ttprune_isolation — TtPruneV2 named as the lever (area 6, closes S-F15)

**What was asked:** S-F15 showed TtPruneV2 alone moved the depth-10 mismatch count 102 → 113 while full PC20
gave 120. Re-run it with TtPruneV2 ON and the other four options EXPLICITLY OFF, on the full 353 pairs, and
report the count — so the attribution does not rest on "the others were off by default".

**The answer: 113 of 353, exactly, and the explicit-off run is identical to the default-off run on all 353
positions. TtPruneV2 is the cause of the extra asymmetry, and it is a lever the owner can flip.**

```
| cell                                         | n   | bm_equal | bm_MISMATCH |
|----------------------------------------------|-----|----------|-------------|
| base + S14                                   | 353 |      252 |         101 |
| PC + S14 (all four options off)              | 353 |      251 |         102 |
| PC + TtPruneV2 ONLY, others EXPLICITLY off   | 353 |      240 |         113 |
| PC + TtPruneV2 only, others at their default | 353 |      240 |         113 |
| PC + PC20 (all four on)                      | 353 |      233 |         120 |
```

- **The explicit-off and default-off runs agree on 353 of 353 positions** (identical bestmove AND score), so
  "off by default" was not a hidden assumption — it is measured.
- **TtPruneV2 alone accounts for 11 of the 19 extra mismatches** (102 → 113 against PC20's 120). The remaining 7
  come from the options interacting (CuckooRep, HistRework and CorrHistV2 individually move the count by -4 to
  +2, which does not add up to 7 without interaction).
- **109 of 353 positions change their match/mismatch verdict** when TtPruneV2 is switched on. So it is not a
  small perturbation of the same pairs — it re-shapes which pairs mirror.

**How sure:** high. This is a direct A/B on the same build, same settings, same positions, with the difference
between the two cells reduced to one option and verified (353/353 identical against the default-off run).

**What the owner can do with it:** turning `TtPruneV2` off restores the asymmetry to the base-tree level
(113 → 102, i.e. to within one position of base + S14's 101). It is off by default, so this only applies when
PC20 is in use. I am NOT claiming the asymmetry is a defect — file 3 settled that it is order dependence, and
file 6 settled that draws and multi-thread variation are not defects. This is a lever and an attribution.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge   PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings: S14 + the options named in each cell, Threads 1, Hash 16, depth 10, fresh process + ucinewgame
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| TtPruneV2 ONLY, other four explicitly off, 353 pairs | done | `raw_D_ttprune_explicit.tsv`, `raw_D.meta` | 113/353 mismatch |
| same cell with the others at default | done | `raw_B_ttprune.tsv` | 113/353 — identical |
| the two runs compared position by position | done | analysis in this report | 353/353 identical bestmove and score |
| all-four-off reference | done | `raw_A_pc_s14.tsv` | 102/353 |
| PC20 reference | done | `../pcsym10/raw_G353.tsv` | 120/353 |
| explain the remaining 7 | NOT done | — | interaction; would need pairwise option runs |

## Findings

`S-F20 | 6 | TtPruneV2 is NAMED as the lever for the extra colour asymmetry on the PC build: with TtPruneV2 on and CuckooRep/HistRework/CorrHistV2/MateAlphaGuard explicitly off, the depth-10 bestmove-mismatch count is 113 of 353 (all four off: 102; full PC20: 120), and 109 of 353 positions change their match verdict when the option is switched on; the explicit-off run is identical to the default-off run on 353/353 positions, so the attribution does not rest on defaults | pcsplit/raw_D_ttprune_explicit.tsv pcsplit/raw_B_ttprune.tsv pcsplit/raw_A_pc_s14.tsv | NEW |`

## Suspicions, not proven

- That the remaining 7 mismatches are TtPruneV2 × CorrHistV2 interaction. Both touch the transposition table's
  use, so it is the natural pair, but I did not run the pairwise cell.

## What I did NOT do

- Did not run pairwise option combinations to decompose the last 7.
- Did not test whether TtPruneV2 changes anything on the BASE tree (the option does not exist there).

## Times

`pcsplit/stamps.txt`, every line a `date -u`.
