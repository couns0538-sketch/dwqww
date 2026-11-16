# seat 20 — job 29: `MateAlphaGuard` is what fixes the mate distance (PC r15)

## The isolation (PC r15 build, `Threads 1`, `Hash 16`, depth 12, S-F19 board, fresh process each)

| settings | bestmove | score | nodes | pv |
|---|---|---|---|---|
| defaults, nothing set | c2b1 | **mate −7** (14 plies) | 28,084 | 14 |
| **`MateAlphaGuard true` ONLY** | c2b1 | **mate −4 (8 plies)** | 29,801 | 8 |
| `MateAlphaGuard false` explicit | c2b1 | mate −7 | 28,084 | 14 |
| S14 without it | c2b1 | mate −9 | 37,664 | 14 |
| S14 + `MateAlphaGuard true` | c2b1 | **mate −4** | 31,996 | 8 |
| the five non-MateAlphaGuard PC20 extras only | c2b1 | cp −3122 | 15,444 | 16 |
| those five + `MateAlphaGuard true` | c2b1 | cp −3122 | 15,444 | 16 |

The true forced distance is **8 plies**, proved independently by exhaustive search in job16 (`mate -4`).

## What this says, precisely

1. **`MateAlphaGuard true` is necessary and sufficient for the correct distance here.** Set alone on an otherwise
   default PC build it turns `mate -7` into `mate -4`; set to `false` explicitly it does nothing. This is the single
   most useful fact of the job: the fix is a named switch, and it is the switch whose whole purpose is to stop a
   mate score being cut off by an alpha bound.
2. **The PC20 bundle as a whole also gives `mate -4`**, so a PC20 test cannot tell you *why*. Any seat reporting
   "PC20 fixes mate distances" is reporting the bundle; the mechanism is `MateAlphaGuard`.
3. **The other five PC20 extras make this position WORSE**: CuckooRep/HistRework 2/TtPruneV2/CorrHistV2/OwnBook
   alone give `cp −3122` — the mate score is lost entirely, which is the same failure mode as `LmpBase=8` on the
   base tree (my S-F19). Adding `MateAlphaGuard` to them does **not** rescue it. So on this position the PC20
   bundle is a fight between one switch that finds the mate and four that lose it, and the bundle happens to land
   on the right answer.
4. **`MateAlphaGuard` does not exist on the base tree.** The base build's `uci` answer has no such option, so this
   cannot be tested there and no base-tree finding of mine can be attributed to it.

## Consequence: my S-F34 needs a qualifier, and gets one
S-F34 said "the mate-distance defect is FIXED on the PC build" from a PC20 measurement. That was too broad: on the
same PC build with DEFAULT settings the answer is still `mate -7`. The accurate statement, which supersedes it:

> On the PC r15 build the mate distance is correct **only when `MateAlphaGuard true` is set** (PC20 includes it);
> with default settings the PC build reports the same wrong `mate -7` as the base tree.

## What I did NOT do
- I did not test `MateAlphaGuard` on other mate positions, so "sufficient" is established for one board.
- I did not find whether the four search extras lose the mate *because* they change move ordering or because they
  interact with the guard (the last two rows show the guard cannot rescue them, which suggests ordering).
- Only `Threads 1`; no score above one thread is used anywhere here.

## Rule-1 note
The zero in this job is "`MateAlphaGuard false` changes nothing (28,084 nodes, identical to defaults)" — shown by
the `true` row being different on the same harness, so the switch is proven able to fire.
