# IDEA_SOURCE — S29 speed stack

- **The job**: Sol's S29 spec (`17aa0cae:validation/forge_sol_pack31_20261025/forge_sol_all_jobs_recovery_20261026/forge_sol_all_jobs_inventory_20261026.json`,
  id S29): rebase every node-exact S11-S14 piece into one stack behind one compile switch, so the speed work costs
  one [-3, 1] gate instead of four.
- **Piece S11 (material-key table)**: Sol's idea (`forge_sol_S11_material_history_key_20261026.patch`), first
  ported to AL1 on `opus-sol-S11` (`include/forge/material_key_table.hpp`, copied here with a new header comment).
  Idea class: replacing a polynomial evaluated by Horner's rule with a sum of precomputed per-term contributions
  (distributivity modulo 2^64).
- **Piece S13 (child TT prefetch)**: Sol's patch cc3efc96, ported verbatim on `opus-sol-S13`; here the same two
  prefetch statements without the runtime option. Idea class: software prefetch of the next hash-table bucket as
  soon as the child key is known (CPW "Transposition Table", prefetching).
- **Test**: adapted from `opus-sol-S11`'s `tests/material_key_tests.cpp`.
- No code was copied from any third-party engine.
