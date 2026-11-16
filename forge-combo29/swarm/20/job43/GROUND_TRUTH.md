# seat 20 — job 43: the regime ground-truth triple, and the trap in applying PC20 to the base build

Any seat can tell which settings regime it is actually in by running `go depth 12` on startpos at `Threads 1` with a
fresh process and comparing against this table. Measured by me, two runs per cell, every cell identical:

| regime | build | bestmove | score | nodes |
|---|---|---|---|---|
| **defaults** (no setoption at all) | base 6b98f217 | `e2e4` | `cp 30` | **56,720** |
| **defaults** | PC r15 | `e2e4` | `cp 30` | **56,720** |
| **S14** (14 options, Threads 1, Hash 16) | base 6b98f217 | `d2d4` | `cp 24` | **22,459** |
| **S14** | PC r15 | `d2d4` | `cp 24` | **22,459** |
| **PC20** (S14 + 6) | PC r15 | `d2d4` | `cp 25` | **21,600** |

## The trap — and it is the reason this table matters
**The base build does NOT have the five PC20 option names.** Verified on the base exe, each one answers:
```
info string unknown option CuckooRep
info string unknown option HistRework
info string unknown option TtPruneV2
info string unknown option CorrHistV2
info string unknown option MateAlphaGuard
```
(and on the PC build `HistRework` requires a NUMBER — `value true` answers `invalid value for option HistRework`;
the correct form is `value 2`.)

So a harness that sends "PC20" to the **base** build is really running **S14 with five silently ignored options** —
which is exactly why my sweep shows base+PC20 = `d2d4 / cp 24 / 22,459`, identical to base+S14, while the PC build
gives `cp 25 / 21,600`. The numbers look plausible and mean something different. **Anyone who reports "PC20 on the
base tree" is reporting an S14 run.**

## One command to check your own regime
```
printf 'uci\nsetoption name OwnBook value false\nisready\nucinewgame\nisready\nposition startpos\ngo depth 12\nquit\n' | ./forge | grep -E 'info depth 12|bestmove'
```
- `e2e4` / `cp 30` / nodes **56720** → you are at **defaults** (your S14 setoptions did not take).
- `d2d4` / `cp 24` / nodes **22459** on either build → **S14** is in force.
- `d2d4` / `cp 25` / nodes **21600** → **PC20** on the PC build.

This table is a *measurement*, so it is the ground truth for this build pair only; the PC's own trained net will
change the numbers (file 5: the net is not shared), and then this table must be re-measured, not trusted.

## Why the table catches the mistake S-C23 found
Seat 27's S-F8 quoted `cp 30 / 56,720` as an "S14" figure — by this table that is the **defaults** row. The check
above takes one command and would have caught it before publication.
