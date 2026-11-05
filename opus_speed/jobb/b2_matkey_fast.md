STATE: IN PROGRESS

# b2_matkey_fast: FORGE_SPD_MATKEY_FAST (spec S3 variant (a): closed-form 14-bit material index)

Worker b2mg (fable), job B part 2, branch opus-speed-20261105. Source edits 09:22-09:25 PC clock; unit test 09:29 (`date`).
Patch: `F:/ospd/wt/opus_speed/patches/b2_matkey_fast.patch` (90 lines; file search.cpp only; applies with `patch -p1` to a fresh
lock copy and reproduces `F:/ospd/src/b2_matkey_fast`: apply test in `F:/ospd/src/b2_applytest_matkey_fast`). One switch line
`#define FORGE_SPD_MATKEY_FAST 0` in search.cpp. Verify variant (not for stacking): `F:/ospd/src/b2_matkey_fast_verify`;
planted mutant: `F:/ospd/src/b2_matkey_fast_mutant` (drops the White-pawn term).

## Design (own words)
The lock's `material_key` (search.cpp:588-596) is Horner over the ten counts c_j (White then Black, Pawn..Queen):
key = sum_j (c_j + 1) * P^(9-j), then * G, mod 2^64 (P = 1099511628211, G = 0x9E3779B97F4A7C15). Unsigned arithmetic
mod 2^64 is a ring, so key = K0 + sum_j c_j * K_j with K_j = G * P^(9-j) mod 2^64 and K0 = sum_j K_j. Both users
(corrected_eval :642, update_correction :655) mask the key with CorrectionSize - 1 = 0x3fff, and the low 14 bits of a sum or
a product depend only on the low 14 bits of the operands, so the switch keeps K_j and K0 mod 2^14 (a constexpr table
derived at compile time from the two lock literals, no typed numbers), computes `MatKeyBase + sum_j popcount_j * K14_j` in
32 bits (ten independent popcount + multiply terms, no serial chain; the 32-bit wrap is harmless because 2^14 divides
2^32) and masks. `material_index(board)` replaces `material_key(board) & (CorrectionSize - 1U)` at the two use sites; the
`MaterialCorrectionWeight > 0` guards stay. static_asserts: CorrectionSize == 1 << 14 and K14[9] == G mod 2^14 (= 0x3c15,
the lock exe's `imul $0x3c15`, card T05B-02). Variant (b) (incremental Board key) is not built (task: variant (a) only).

## Lines touched (lock numbering)
- src/search.cpp :586-597: switch block before the anonymous namespace; inside it `#if FORGE_SPD_MATKEY_FAST` constants,
  table, static_asserts and `material_index` / `#else` the lock's `material_key` verbatim / `#endif` (no unused function at 1);
  :641-643 corrected_eval and :655 update_correction: the index expression under `#if` / lock line under `#else`.
- Switch 0: `g++ -E -P` of src/search.cpp is byte-identical to the lock's (`F:/ospd/jobb/b2/matkey_fast/pp/`).

## Why node-identical
Same 14-bit index at every use (algebra above, the unit test and the in-engine verify build), so the same
material-correction entry is read and written at every node: same corrected evals, same tree.

## Checks
(c1) unit test `F:/ospd/jobb/b2/tools/b2_matkey_unit.cpp` -> `F:/ospd/jobb/b2/matkey_fast/b2_matkey_unit.log`: the lock Horner form
     (restated on count vectors) vs the switch's table code (verbatim copy): all count pairs 0..10 in every two positions (12,100
     vectors), 10^6 random vectors with counts 0..10, 10^5 with counts 0..64: "checked 1112100 count vectors, 0 mismatches: PASS".
     Printed table: K0 = 0x1f14; K_j = 0x238f 0x10b5 0x1ff7 0x1ead 0x2e1f 0x33e5 0x3807 0x3e5d 0x17af 0x3c15 = exactly the
     values the spec derived independently (SPEC_SPEED.md S3, matkey_check.py).
(a), (b), (c2) verify build over bench d13 + 12k FENs, (c3) mutant, codegen: PENDING (chain B, after chain A).

## Risks
- The gain is a few cycles of dependent latency per corrected_eval / update_correction call (spec: +0 to +1.5 %, UNPROVEN,
  likely below the +1 % keep threshold alone; the spec times it inside a stack).
- If CorrectionSize ever changes, the static_assert stops the build (the derivation is for 14 bits only).
