# REPORT_pcrev — does the generation-order cause transfer to the PC build? (area 6)

**What was asked (my own follow-up to S-F12):** S-F11/S-F12 showed on the base tree that the generated move order
is not mirror-corresponding (40 of 41 positions) and that reversing it changes the search's node counts without
equalising the pair. Does the same hold on the PC build under PC20?

**The answer: yes, identically.** Same probe position, same experiment, PC20 on the PC build:

```
                        A nodes   mirror nodes   equal
depth 1  PC20 base          25          30        no
depth 1  PC20 reversed      34          42        no     <- counts changed
depth 2  PC20 base          66          60        no
depth 2  PC20 reversed      67          84        no     <- counts changed
```

These are the **same numbers the base tree gives** for the same probe and the same experiment — because the
mirror pair's node counts at this position do not depend on the four PC20 options (they are inert at depth ≤ 2,
which S-F13 measured independently). So the generation-order mechanism is not something the PC build introduces
or repairs: it is inherited unchanged.

**The conclusion of S-F12 therefore holds on the PC build:** the generation order causally influences the tree
(the counts move when the list is reversed) but is not sufficient to explain the mirror asymmetry (the pair is
still unequal, and the gap widens). My S-F15/S-F20 attribution is about a *different* layer — the extra
asymmetry that PC20's settings add on top of this inherited baseline.

**How sure:** medium-high. The numbers reproduce the base-tree values exactly, which is strong evidence the
mechanism is inherited, but it is one position and two depths. The deeper 353-pair evidence for the PC build is
in S-F14/S-F15/S-F20.

## Honesty numbers

```
PC build used for every other number in my folder:
  /home/ubuntu/builds/bld-pc/forge   PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
  none 312866 / S14 242796 / PC20 278024  (all match file 5)
EXPERIMENT build used ONLY here:
  /home/ubuntu/builds/bld-pcrev/forge  = PC r15 + the reverse switch (-DFORGE_EXPERIMENT_REVERSE_LIST=1)
  Its bench numbers are NOT expected to match file 5 (reversing the move order changes the tree by design)
  and I do not claim any. This is the same caveat as the base-tree experiment in S-F12.
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| reverse switch applied to the PC source | done | 2 `std::reverse` sites, switch default 0 | builds clean |
| depth 1 base vs reversed, PC20 | done | `run.txt` | 25/30 → 34/42, still unequal |
| depth 2 base vs reversed, PC20 | done | `run.txt` | 66/60 → 67/84, still unequal |
| the whole 353-pair sweep on the PC build | done previously | `../pcsym10/raw_G353.tsv` | 120/353 mismatch, 0/353 node-equal |

## Findings

`S-F21 | 6 | the generation-order mechanism transfers to the PC build under PC20 unchanged: on the S-F12 probe the PC build gives the SAME numbers as the base tree (depth 1: 25/30 base root, 34/42 with the list reversed; depth 2: 66/60 and 67/84), so reversing the order changes the counts but still does not equalise the mirror pair — S-F12's conclusion (order necessary, not sufficient) holds on the PC build | pcrev/run.txt | NEW |`

## Suspicions, not proven

- That the PC build's generator emits the same non-mirrored order as the base tree. The identical node counts
  imply it, but I did not dump and compare the two generators' orders on the PC build.

## What I did NOT do

- Did not run the reversed build across the 353 positions (that build is an experiment; the base PC build is the
  one that matters for the owner).
- Did not verify the PC build's generator order equals the base build's (seat 03 did something adjacent —
  move generation equality across 62,406 values — but for the base vs PC build, not for order).

## Times

`pcrev/stamps.txt`, every line a `date -u`.
