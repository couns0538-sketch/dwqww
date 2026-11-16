# Which PC20 option removes the mate fault? `MateAlphaGuard` alone.

`isolate_pc.txt`, script `matecheck/isolate.py`. Each row is **S14 plus the named option**, on the
PC build, **Threads 1**, fresh process per search. Two positions, each judged against its
solver-proven truth:

- `8/8/1p6/8/p3p3/8/2Kpk3/8 w` at depth 12 — truth `mate -4` (8 plies)
- `k7/6R1/5N2/p4K1P/P7/8/8/8 b` at depth 14 — truth `mate -3` (6 plies)

## Results

```
S14 only (baseline)            STILL WRONG (mate -9)  | STILL WRONG (mate -9)
+ CuckooRep=true               STILL WRONG (mate -13) | FIXED (score and PV length right)
+ HistRework=2                 STILL WRONG (mate -7)  | STILL WRONG (mate -5)
+ TtPruneV2=true               STILL WRONG (mate -7)  | STILL WRONG (mate -6)
+ CorrHistV2=true              STILL WRONG (mate -8)  | STILL WRONG (cp -2214)
+ MateAlphaGuard=true          FIXED (score and PV length right) | FIXED (score and PV length right)
+ OwnBook=false                STILL WRONG (mate -9)  | STILL WRONG (mate -9)
full PC20                      FIXED (score and PV length right) | FIXED (score and PV length right)
```

## What this settles

**`MateAlphaGuard=true` is the option, on its own, that fixes both mate-distance faults.** It is the
only single option that fixes both; `CuckooRep` fixes the second position but makes the first worse
(`mate -13` instead of `-12`), which is a useful warning that these options interact and that a
single case is not enough to judge one.

This agrees with the other seat's report that MateAlphaGuard alone fixes one case, and extends it to
a second position with a different mate distance and a different side to move. It also means my
earlier caution in 15-F19 is now resolved: the attribution is established by isolating each option,
not inferred from the full PC20 set.

## What it does NOT establish

- **Why** MateAlphaGuard fixes it — it is a guard on the mate score versus the alpha window, so the
  natural reading is that a mate score is being clamped or replaced by a bound at a node where the
  alpha window is narrow, and the guard prevents that. That is a plausible mechanism, not a measured
  one; I did not read the patch's implementation for this option.
- Whether `MateAlphaGuard` has a cost (nodes, strength) elsewhere. It moved the two positions to the
  right answer at 30,502 and 32,727 nodes; I did not measure the aggregate.
- Whether it fixes the whole class or just these two positions. The G-set evidence (15-F18: 12 mate
  scores, 0 violations under full PC20) suggests it does, but that run had all five options on, so it
  is consistent evidence, not isolated evidence.

## Note on a baseline row

`S14 only` here reads `mate -9` on the first position at depth 12, whereas my earlier job-1 run of the
**base tree** recorded `mate -12`. Different builds (PC r15 vs base 6b98f217) and, in job 1, a
different protocol (many positions per process rather than one per process). Both are "wrong by
several moves"; the exact wrong value is not stable across builds, which is itself consistent with
the fault being a search-window artefact rather than a fixed offset.
