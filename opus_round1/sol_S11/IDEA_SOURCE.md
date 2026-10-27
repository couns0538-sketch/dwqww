# IDEA_SOURCE — S11 MaterialKeyTable (node-exact speed; UCI MaterialKeyTable, default off)

IDEA_SOURCE: Sol's S11 preparation on branch `forge/sol-pack31-20261025` (head 17aa0cae),
`validation/forge_sol_pack31_20261025/forge_sol_after_S09_continuation_20261026/S11/forge_sol_S11_material_history_key_20261026.patch`
(prepared 2026-10-26 for his dev bases L/L′/B, never built there in this form on the lock tree). Sol names the
idea "material_key table-sum", a reserve item in the S11 input `files/11_ideas_profile/profile_notes.md`
(read by Sol, sha256 f78b109d…; that file is not in this repository).

What the idea is: the material-correction key of `Worker::corrected_eval` / `update_correction` is Forge's own
Horner polynomial in the ten piece counts (multiplier 1099511628211, final mix 0x9E3779B97F4A7C15), computed
modulo 2^64. Because multiplication distributes over addition modulo 2^64, the polynomial is a constant plus
one independent term per (colour, piece type) slot; the terms are precomputed for every popcount 0..64 and the
key becomes ten table loads and additions instead of ten dependent multiply-adds and a final multiply. The two
constants are Forge's; the table only re-expresses Forge's own key (same 64-bit value for every board).

Technique background: precomputing per-term contributions of an additive hash is ordinary algebra (the same
reason Zobrist keys are sums/XORs of per-feature constants); no external engine code was read or copied, and
no tuned values are involved. Code written from scratch for the AL1 s198 lock tree (`include/forge/
material_key_table.hpp`, the guarded call in `src/search.cpp` `material_key`).

Not repeated (Sol's exclusions, still valid): piece_type table / conditional lowering and MovePicker history
hoists (earlier speedmp/mp2/speedstack packs), TT prefetch (S13), NNUE update and lazy accumulator work (S12).
