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
