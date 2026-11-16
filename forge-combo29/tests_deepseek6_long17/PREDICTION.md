long 17 prediction (my own eleven node-step counters on the plain base) -- own commit before the first counted run

The counters' total relations (what my placements imply; all must hold on O and G under S14):
1. razor_ret <= razor_try <= gate; rfp_ret <= gate; null_try <= gate; null_ge_beta <= null_try;
   null_cut <= null_ge_beta (both cut returns sit inside the >= beta branch); null_verify <=
   null_ge_beta; probcut_cut <= probcut_enter; iir is OUTSIDE the gate block (its condition does
   not require it) so iir <= total search nodes, no relation to gate.
   Kill: any violated relation.
2. rfp_ret is the largest single counter on O (kimi5's job 8 measured reverse futility returning
   42 percent of the gated nodes on O defaults) -- I expect rfp_ret > null_try and
   rfp_ret > razor_try on both sets. Kill: otherwise.
3. iir fires: 0 < iir on both sets at depth 12 (the IirDepth 2 gate with a missing hash move
   happens from iteration 2 on). Kill: iir == 0.
4. The depth profile: gate's bucket 1 (depth 1) is the largest or second-largest bucket; the
   9+ bucket is the smallest of the eight nonzero buckets for gate on O. Kill: otherwise.
5. My counter copy's rows equal the plain build's rows on O and G under S14 on every position
   (the copy is observation-only). Kill: any differing row.
The held-back known answer: my eleven totals on O (summed over depth buckets) are what Opus
compares; a mismatch names where my placement sits differently, which the per-bucket lines then
localize.
