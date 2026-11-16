# seat 20 — job 64: the tt.clear repair at the SAFE Hash sizes — it costs nothing and gains +2.5 to +3 plies

S-C35 confirmed seat 30's repair at Hash 256/512, where the shipped build collapses. But the owner's realistic
MultiPV settings are the **safe** ones (Hash 16/64/128 at MultiPV 3), where the shipped build already works. The
question that decides whether the patch is worth taking *for analysis* was: does it cost anything there?

**It does not. It gains.** Shipped vs repaired, 10 G-set positions, `go wtime 5000`, MultiPV 3, Threads 1:

| Hash | shipped depths | median | repaired depths | median | diff |
|---|---|---|---|---|---|
| **16** | 14,12,12,14,13,15,14,12,12,15 | 13.5 | 14,15,13,14,14,17,14,13,14,17 | **14.0** | **+0.5 (neutral)** |
| **64** | 13,11,11,12,11,14,14,11,11,15 | 11.5 | 14,15,13,14,13,16,14,13,14,17 | **14.0** | **+2.5** |
| **128** | 12,9,10,11,11,12,14,10,8,14 | 11.0 | 14,14,12,13,13,15,14,12,14,16 | **14.0** | **+3.0** |

Pre-stated rule was: "if the repaired median depth is LOWER at any safe Hash by more than 1 ply, the patch has a cost
to declare." **No Hash shows a cost.**

## The two things this establishes
1. **No cost to declare at the safe sizes.** The worst case is +0.5 plies at Hash 16 (neutral); the patch never loses
   depth where the shipped build was working.
2. **The repaired build is FLAT at ~14 plies from Hash 16 to 128**, whereas the shipped build decays 13.5 → 11.5 → 11.0
   as the table grows. That is exactly what removing a per-line full-table clear should do: the table size stops
   costing depth. So the "multi-PV gradient" I reported in S-C33 (13.5 → 11.5 → 11.0) is **mostly the clear, not the
   table**.

## What it means for the owner
- Taking the patch would **not degrade** analysis at any safe setting, and would **improve** the larger-table ones by
  two to three plies.
- It does **not** change the advice "MultiPV 1 at any Hash" — that is still the least-lossy way to analyse.
- Still the owner's/Opus's decision; what I add is that the *analysis* side shows no cost, which was the missing number
  when I wrote the page's "strength effect unmeasured" caveat. **Strength in play is still unmeasured** — this is depth
  at a fixed clock, not a match result.

## Limits
- 10 positions, one run each per cell, one clock (5 s), MultiPV 3 only, built-in net, Threads 1.
- One run per cell is thin for a +0.5 result (Hash 16); the +2.5/+3.0 differences are far larger than that noise and
  are consistent with the flat-median pattern.

## PREDICTION TEST that PARTLY FAILED — the gradient is MOSTLY the clear, not entirely

My S-C40 explanation was "the multi-ply gradient is mostly the per-line `clear()`, not the table size". I tested it
with a falsifiable prediction: **if the gradient is the clear, the repaired build's depth should be FLAT in Hash.**

Repaired build, MultiPV 3, `go wtime 5000`, Threads 1, 10 G-set positions, Hash 16 → 512:

| Hash | repaired depths | median |
|---|---|---|
| 16 | 14,15,13,14,14,17,14,13,14,17 | **14.0** |
| 64 | 14,15,12,14,13,16,14,13,14,17 | **14.0** |
| 128 | 14,15,12,14,13,15,14,12,14,16 | **14.0** |
| **256** | 13,12,12,12,11,14,14,10,9,16 | **12.0** |
| **512** | 12,11,6,11,8,7,12,9,7,14 | **10.0** |

**Flat to 128, then declining.** So the prediction is **partly refuted**:

- **The clear explains most of it**: 13.5 → 11.5 → 11.0 (shipped, 16→128) becomes a flat **14.0** — a 3-ply recovery at
  Hash 128, which is the bulk of the gradient.
- **A residual table-size cost remains**: even repaired, Hash 256 loses 2 plies and Hash 512 loses 4 against Hash 16.
  A 2 GB table has real costs that are not the `clear()` (allocation, cache/TLB pressure on a 4-core box), and the
  repair does not remove them.

**Corrected statement:** the multi-PV gradient is **mostly** the per-line `clear()` — about 3 of the 4–5 plies at
Hash 128 — with a further ~2 plies per doubling at 256+ coming from table size itself. My S-C40 wording "mostly the
clear, not the table size" was right in direction and too absolute; this table is the qualifier.
