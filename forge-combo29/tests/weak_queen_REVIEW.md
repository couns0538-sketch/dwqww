# WeakQueen mask experiment

This experiment is confined to the queen's existing WeakQueen predicate. It
does not change evaluation parameters, features, trace coefficients, ray
occupancy, or the network. Native speed and Elo gates remain **UNPROVEN**.

## Exact identity and precondition

Let D and S be the bishop and rook rays from the evaluated queen, both computed
with the original full board occupancy. Let B, R, and Q be the enemy bishop,
rook, and queen bitboards. The original mask is

```
((D & (B | Q)) | (S & (R | Q))) & ~Q
```

Distributing the final mask gives

```
(D & B & ~Q) | (D & Q & ~Q) |
(S & R & ~Q) | (S & Q & ~Q)
```

The Q terms vanish. Valid Board piece bitboards are disjoint, so B & ~Q = B
and R & ~Q = R. Therefore the result is exactly

```
(D & B) | (S & R)
```

This is equality of the full bitboard, not merely its zero/nonzero predicate.
An enemy queen still blocks both rays through `occupied`; excluding it from
the attacker mask must not turn this into an X-ray test. Own pieces, kings,
and non-slider enemies remain blockers too. Multiple promoted queens do not
invalidate disjointness. An inconsistent manually corrupted Board with
overlapping piece types is outside the precondition.

## Compiler check

The previously preserved GCC14 optimized-tree excerpt in
`hce_profile_lines_queen_ir.txt` shows that repeated bishop/rook rays are already
reused. No missing ray-reuse optimization is claimed. It also shows the two
OR-with-enemy-queen operations and final complement/mask still present.
Fresh strict-FP/O3/x86-64-v4 GCC14 compilation of frozen source
`9b67829c86c0ddadcb8334fe92147ffa4a895ced`, differing only in
`FORGE_SPD_WEAK_QUEEN_MASK=0/1`, changes actual object code:

- `size` text total: 28,835 to 28,643 bytes, a reduction of 192 bytes.
- Non-traced evaluation function: 11,029 to 10,984 bytes, minus 45 bytes.
- Traced evaluation function: 11,715 to 11,600 bytes, minus 115 bytes.

The whole-object total also includes alignment and supporting sections; do not
interpret its difference as an instruction-count reduction. Both color paths
and traced/non-traced optimized IR remove the OR-with-queen terms and final
queen exclusion. `weak_queen_codegen.txt` preserves the exact symbol sizes,
object hashes, and four before/after IR blocks. The compiler's local counts
and branch probabilities are estimates, not sampled runtime data.

## Test contract

`weak_queen_unit.cpp` exhausts all 16 valid single-bit assignments and 100,000
deterministic full-width assignments, with an invalid-overlap counterexample.
It checks 528 adversarial color/direction/attacker/blocker configurations,
the saved 128 search-screen positions, and three deterministic 4,096-ply legal
walks including make/unmake. Every tested board is checked for disjoint piece
bitboards and exact occupancy union. Cached, cache-hit, uncached and complete
trace results are compared against the unchanged default evaluation compiled
under separate test-only symbols by `weak_queen_oracle.cpp`.

`weak_queen_check.py SOURCE_COMMIT OUTPUT_DIRECTORY` archives only src/include,
builds isolated strict-FP default/off variants, checks the immutable default
binary SHA-256, runs both full official pin suites and UCI smoke checks, then
the existing depth-7/256-comparison screen and ASan/UBSan tests in both modes.
LeakSanitizer is disabled for this container; this is not a leak-check claim.
Only the WeakQueen experiment is enabled in its opt-in engine; other review
experiments retain their defaults.

## Test-first sensitivity

Before editing production source, the original and temporary simplified
evaluators both passed all 37,412 board checks, covering 33,320 queen visits
and 3,793 weak-queen detections. Removing the original final enemy-queen
exclusion deliberately failed against the independent oracle with exit 1:

```
rnN3n1/1kp4r/pP5p/3ppP1P/1bB1PPp1/3q1Q2/1P1P3R/1RB1K1N1 w - - 1 20
```

The mutation was never applied to production. Initial adversarial fixture
construction placed the side-that-moved king in check; Board rejected those
fixtures. The harness was corrected to choose a far valid king square before
the completed runs. Original failed attempts remain in the local precheck
logs; no engine defect was inferred from them.

A second temporary mutation removed enemy queens from the opt-in ray
occupancy. It failed on the adversarial queen-blocks-bishop fixture
`k7/8/8/8/3Q4/2q5/1b6/K7 w - - 0 1`, confirming that the test rejects an
accidental X-ray change. The actual candidate continues to use full occupancy.

The guarded production candidate was then compiled and passed the same
37,412-board comparison before the source-only commit was frozen.

## Frozen validation results

All following checks passed for source commit
`9b67829c86c0ddadcb8334fe92147ffa4a895ced` using GCC 14.2.0 and the strict-FP
review flags. No other opt-in review experiment was enabled.

- Default-off executable SHA-256 is exactly the immutable lock rebuild:
  `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`.
- Isolated enabled executable SHA-256:
  `c5a6021d39ebb267ed3e1c0046d6ee430b9c5f959a50102434c372c3f267292c`.
- Both modes passed all ten official NNUE-on/off bench pins and startpos
  perft 5 = 4,865,609, using the project's `scripts/check_pins.sh`.
- Both modes passed the existing UCI smoke script.
- All 256 depth-7 comparisons passed across the 128 saved positions with
  NNUE both on and off. Scores, depths, nodes, PVs and bestmoves matched.
- Both release modes and both ASan/UBSan modes passed the same 37,412 board
  checks, 100,016 algebra cases, and complete HCE value/trace comparisons.
  These counts include repeated cache hits and make/unmake board visits, not
  37,412 unique positions. No sanitizer diagnostic was emitted.

The complete commands, compiler, test hashes and artifact hashes are in
`weak_queen_receipt.json`; full search records in `weak_queen_equivalence.json`;
UCI output in `weak_queen_uci.json`; pin/unit/sanitizer and initial harness
history in `weak_queen_validation.log`; mutation commands and hashes in
`weak_queen_mutations.json`. Local raw source/build evidence remains under
`/workspace/shared/forge-build/weak-queen-mask/`.

Reproduce with:

```
python3 forge-combo29/tests/weak_queen_check.py \
  9b67829c86c0ddadcb8334fe92147ffa4a895ced /tmp/forge-weak-queen
```

Correctness confidence is high for valid Board states: the bitwise identity
is exact and both full trace comparisons and search gates passed. This is a
small verified code-generation simplification, **not a measured speedup**.
Native Windows/clang PGO speed and Elo gates remain **UNPROVEN**. The switch
remains default off and the original disabled path is intact.
