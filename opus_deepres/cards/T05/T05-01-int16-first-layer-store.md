# T05-01: int16 first-layer store (w1 as int16, exact float or int32 accumulators) for the v2 and lock paths
Status: COMPLETE - DOWNGRADED by review: (second vote) the cost it targets is not shown beyond noise (post-fix KB4 probe = its exe's OFF speed; bench ABBA CI 0.900-1.040 spans 1.0; D:/o30/FINAL_REPORT.md:508-509 "not needed"), the lock path (-1 to +1 %) is under the +1 % nps line, and no v2 net has a gate result yet - the next picks are KB8 nets whose whole speed cost is ~1 %, so this can recover at most ~1 % there; revisit for a KB16 / KB32 net. Size first (V2P4_GAP P2, fresh copies), build only for a KB8+ net headed to the gate. Kept as a full card, not a one-liner, because the exactness bounds below are the evidence any later build needs.

## Source
- Own: D:/o30/wt/opus_30h/a/o30_v2int16.py (anchored edit script, all-or-nothing after the Code Review, never built),
  D:/o30/wt/opus_30h/a/RESULTS.md ("New gate exe with the root fix": v2p4 probe OFF 0.933, KB1 0.980, KB4 replicas
  0.929; bench ABBA KB4 replicas vs KB1 0.968), D:/o30/FINAL_REPORT.md section 2 ("int16 first layer").
- Zen 5 cache facts: AMD Zen 5 deck via search summaries (notes/T05/sources.md no. 7): L2 1 MB per core, 16-way.
- No outside engine was found with a measured float -> int16 table number (MISSING; not searched further, stop rule).

## Licence
Own Forge code and records (no third-party code or constants). Zen 5 facts: vendor slides, facts only.

## Mechanism
Keep w1 as the file's int16 (2 B per weight, not 4) and keep the accumulators exact. Every lock / v2 value is an
integer k times 2^-12: weights |k| <= 14,227 (3.47), and the per-unit bound bias + 32 largest |w| is 342,331 (83.6)
for the lock net - below 2^24, so float32 sums are exact and order-free (the reviewers' rule); for ANY int16 file
(v2 nets included) |k| <= 33 x 32,768 < 2^24 holds too. Two exact designs:
(a) float accumulators that add float(w) * 2^-12, converted on the fly (the prepared script); (b) int32 accumulators
in units of 2^-12 (sign-extend + integer add), converted once per evaluation (int -> float, then x 2^-12, both exact).
The output layer (float, 16 ordered lanes) is unchanged, so evaluations and node counts are identical.
Not exact / not safe: int16 ACCUMULATORS (the simple bound exceeds 32,767 on all 256 units of the lock net - computed
here from the lock's weights), int8 weights (|k| up to 14,227 needs 15 bits).
Bytes per column read halve (1 KB -> 512 B). KB4 table 3.1 MB -> 1.57 MB, so the two perspectives' hot buckets
(2 x 393 KB) fit a Zen 5 core's 1 MB L2 again; KB32 25 MB -> 12.6 MB; the lock's 786 KB -> 393 KB.

## Forge fit
Lock: src/nnue.cpp:47 `std::unique_ptr<float[]> w1`, :59 converts NnueW1 / WeightScale to float at load; updates at
:99-157, refresh :84-97 (512-bit vaddps / vsubps in the lock exe, objdump). v2 (v2port.patch): include/forge/nnue_v2.hpp
`AlignedFloats w1` [KB][768][256], column(), apply_columns, refresh, refresh_cached, update; src/nnue.cpp loader.
`tools/forge_has.sh 'unique_ptr<float|/ WeightScale'` = 3 hits (nnue.cpp:47, :59, :61); no int16 NNUE arithmetic in the lock.
Change: apply o30_v2int16.py to the v2 path first (design a); design (b) for fewer uops per column.

## Expected gain
Source number (own, the cost this targets): lock net as KB4 replicas vs as KB1 on the SAME exe and tree, game
positions: 0.929 vs 0.980 (= 0.948; one probe run each, run-to-run noise ~+-3 %); bench ABBA 0.968 (CI 0.900-1.040,
median 0.991). The 30-h job dropped int16 when the lazy root explained the in-game loss; the post-fix probe still
shows ~5 % for KB4 vs KB1 (V2P4_GAP.md, part P2). No outside number (missing).
(verify note: RESULTS.md:216-219 reads the 0.968 ABBA as "cost little", :471-472 the post-fix probe as "runs at its own
exe's OFF speed" (OFF 0.933, KB4 0.929); 0.948 = ratio of two single runs of ~+-3 % each, bench CI includes 1.0 -> the
~5 % cost is not shown beyond noise; size it (V2P4_GAP P2 split, fresh copies) before building.)
Forge estimate: v2 KB4 / KB8 +1-4 % nps, KB16 / KB32 +2-5 %, lock path (KB1, 786 KB already in L2) -1 to +1 %
**UNPROVEN**: design (a) needs about 4 vector ops per 16 weights instead of 2 (sign-extend, convert, scale, add), so
where the table is not the bottleneck it can lose; design (b) (sign-extend + integer add) is the one to build if KB1 matters.

## Effort
Crew 2-4 h (script exists: apply, plain + kit builds pc1 = pc2, re-run the proofs). CPU ~2 h (parity x3 builds, walk
830k plies x 3 nets, verify build, nps ABBA). No GPU.

## Test plan
Pre-gate: OFF pins (bench d11-d22, perft) = lock; lock-as-v2 KB1 / KB4 = lock pins; trained nets' ON benches = their
packed counts (n2L 292397 / 836621 / 2200750); parity 10000/10000 on AVX2 / SSE / scalar; walk 0 mismatches; in-search
verify build clean. Gate route: node-identical speed change = nps ABBA only: depth_probe_ab.py game positions (200
positions, movetime 200, AB + BA), KB4 and KB8 nets plus the lock net (KB1 = the regression check), fresh copies per
slot and an identical-command A/A first (BH-8).

## OFF-by-default design
Build switch `FORGE_NNUE_W1_INT16` (default 0 = today's float tables, the lock's code byte for byte); 1 changes the
storage only. Node-identical by the exactness rule (pins equal), so no UCI option is needed. Default only if the ABBA shows no
KB1 regression; otherwise choose the storage per net at load (int16 for KB4+, float for KB1).
