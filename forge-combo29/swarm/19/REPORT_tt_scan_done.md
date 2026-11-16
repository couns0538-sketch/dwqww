# The TT scan's early exit: slot histogram, and why reordering can gain exactly nothing

seat 19 · area 9 · build **PC r15** (instrumented) · **Threads 1** · cold · `bench 16` = 3,021,035 probes.

## 1. The three lines

**What was asked.** The compiler beats explicit vectorisation (19-F40), so the only lever left on the scan is
the early exit itself: what fraction of hits land in slot 0/1/2/3 on the PC build, cold, at depth 16? If the real
workload differs from bench's 93 % slot-0, ordering compares by hit frequency is free and the compiler cannot
undo it. If it is the same, the scan is done.

**The answer.** **The scan is done. Reordering compares can gain exactly 0 %, and I can say that with
arithmetic rather than opinion.** Slot 0 holds **82.77 %** of hits at depth 16 (not bench-13's 93.05 %, so the
histogram *does* shift) — but slot 0 is **already scanned first**, so the hit path is already at its minimum.
And the decisive number: **66.9 % of all key compares come from empty-slot misses, which cannot be reordered at
all**, because the first empty slot is exactly where the scan must stop. The whole scan is **1.331 compares per
probe**.

**How sure.** High. These are counters, not timings: 3,021,035 probes, 1,082,705 hits, 1,938,330 misses, with
`empty_none = 0` confirming no probe path was missed. The arithmetic in §3 is arithmetic, not inference.

## 2. The histogram

**Hits by slot** (PC r15, depth 16, cold, `bench 16`):

| slot | hits | % of hits | % of all probes |
|---|---|---|---|
| **0** | 896,191 | **82.77 %** | 29.67 % |
| 1 | 152,998 | 14.13 % | 5.06 % |
| 2 | 28,308 | 2.61 % | 0.94 % |
| 3 | 5,208 | 0.48 % | 0.17 % |
| | **1,082,705** | 100 % | 35.8 % |

For comparison, base tree `bench 13` cold (from job 4): slot 0 **93.05 %**, slot 1 6.41 %, slot 2 0.50 %,
slot 3 0.04 %. **So the deeper search does spread the hits** — slot 0 drops 10 points and slots 1–2 quadruple —
which is exactly the hypothesis the question was testing.

**Misses by the slot where they stopped**, which the earlier work did not report separately:

| stopped at slot | misses | % of misses |
|---|---|---|
| 0 | 1,345,149 | 69.62 % |
| 1 | 443,856 | 22.97 % |
| 2 | 117,016 | 6.06 % |
| 3 | 26,135 | 1.35 % |

(`full`-table misses, which scan all four slots: only **6,174**.)

## 3. Why reordering cannot gain anything

Key compares come from three sources, and each is already minimal:

| source | compares | share |
|---|---|---|
| hits (stop at the matching slot) | 1,307,943 | **32.5 %** |
| empty-slot misses (stop at the first empty slot) | 2,688,449 | **66.9 %** |
| full-table misses (scan all four) | 24,696 | 0.6 % |
| **total** | **4,021,088** | 100 % = **1.331 per probe** |

- **Hits are already optimal.** Slot 0 is first in memory and first in the scan order, and it is the most
  frequent slot (82.77 %). Mean compares per hit = **1.208**, which is the minimum achievable for this
  distribution. **A frequency-ordered scan cannot beat "most frequent first" when the most frequent is already
  first.**
- **The 66.9 % from empty-slot misses cannot be reordered by definition.** The scan stops at the first
  unoccupied record because that record *is* the replacement destination (`src/search.cpp:505`). Any order that
  visits a later slot first would have to keep looking past an empty slot, which is both slower and wrong.
- **The full-table path is 0.6 %** and already negligible (19-F36).

So the addressable-by-ordering share is **zero**, and the answer to "if the real workload is different" is: it
*is* different (82.77 % vs 93.05 %), and it still does not matter, because the ordering was never the problem.

## 4. Finding

**19-F42 — the TT scan's compare order is already optimal; reordering by hit frequency can gain 0 %.**
Slot 0 holds 82.77 % of hits at depth 16 (vs 93.05 % at depth 13) and is already scanned first, giving 1.208
compares per hit. **66.9 % of all key compares are empty-slot misses that terminate the scan by design**, so
they are not reorderable either. Total: **1.331 compares per probe**, 4,021,088 across the run. Combined with
19-F40 (explicit vectorisation is scalarised away and measures 1.0001) and 19-F36 (probe count is 1.003/node,
replacement 0.204 %), **the `probe_body` scan has no remaining lever in any of the three directions tried:
vectorisation, ordering, or table size.** It is finished as an optimisation target.

### Suspicions, not proven

- That the remaining ~39 % of `probe_body` (19-F39) is therefore the **memory access** to the cluster line,
  since comparisons are now bounded at 1.33 and vectorisation is not available. This is consistent with
  everything measured, but 19-F40 showed my one attempt to isolate it was defeated by the compiler, so I am
  still not calling it proven.
- That 82.77 % vs 93.05 % would keep falling with depth, which would make the hit path *more* expensive per hit
  at very deep searches — but the compare count can only rise from 1.208 toward 4 in the limit, and even the
  worst case is bounded by the miss cost that dominates now.

## 5. What I did NOT do

- I did not implement a reordered scan, because the arithmetic above shows the gain is zero; implementing it to
  measure 0 % would be the kind of work the owner is paying me not to do.
- I did not measure the same histogram at depth 20+, so the "falls with depth" trend is tested at 13 and 16 only.
- I did not retry the load/comparison split; 19-F40 explains why my first attempt could not answer it.

## 6. Files

`pcspeed/ttdepth/counters.txt` (the raw counter lines, three depths), `job4/instrument_tt.py` (the counters),
this report.
