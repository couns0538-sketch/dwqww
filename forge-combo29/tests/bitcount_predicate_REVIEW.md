# Evaluation bitcount predicates

`FORGE_SPD_EVAL_BITCOUNT_PREDICATES` is default **0**. The original disabled
code remains verbatim. The candidate replaces only pawn double-support and
white/black BishopPair boolean count comparisons with `more_than_one`.
Exactly-one bishops, count-valued uses, WeakQueen, parameters and networks
are unchanged. Native speed and Elo remain **UNPROVEN**.

## Identity

For every unsigned 64-bit bitboard `b`, `b & (b - 1)` clears its least
significant set bit. The result is nonzero precisely when at least two bits
were set. For zero, unsigned subtraction wraps and the AND is still zero.
Thus `more_than_one(b)` equals both `popcount(b) > 1` and `popcount(b) >= 2`
for every bitboard, including empty, singleton, pair, full-width and promoted
piece masks. This identity has no piece-disjointness or maximum-count
precondition. It does not depend on pawn support having at most two bits.

## Compiler-guided scope

Before editing production, GCC 14.2.0 was examined with the same strict-FP,
O3, x86-64-v4 review flags. The pre-experiment source is frozen at
`920bf1183d770c993d4c9cd0bbe184e9a2571810`. Source-only archived reproduction:

```
python3 forge-combo29/tests/bitcount_predicate_codegen.py \
  920bf1183d770c993d4c9cd0bbe184e9a2571810 /tmp/forge-bitcount-codegen
```

The exact-one bishop predicates already lower to arithmetic/XOR comparisons
without population counts. Their temporary explicit nonzero/not-many rewrite
introduces extra zero branches. It is smaller in the scale-factor function
(526 to 502 bytes), but is not an unambiguous instruction-path improvement.
It was rejected conservatively, not established slower or globally optimal.

The three accepted source predicates still had standalone, unreused
population counts. Both color instantiations and both trace modes were
inspected. The candidate changes:

- Pawn support: `popcnt; cmp; cmovg` becomes `blsr; cmovne` in normal HCE.
  The trace path's `popcnt; cmp; jle` becomes `blsr; je`.
- Bishop pairs: false-dependency clearing, memory `popcnt`, and comparison
  become memory `blsr` with direct flag use. The old counts are not reused.
- There are eight fewer static `popcntq` sites across the object: 123 to 115.
  Pawn-only and bishop-only prototypes each remove four. These are static
  instruction sites, not measured dynamic instruction or cycle counts.
- Whole-object `size` text remains 28,835 bytes. Non-traced evaluation changes
  from 11,029 to 11,013 bytes, while traced evaluation changes from 11,715 to
  11,731 bytes. Alignment and surrounding code layout can offset local
  instruction savings. No whole-object size reduction is claimed.

`bitcount_predicate_codegen.json` records every compiler command, variant
source/object/IR/assembly hash and symbol size. `bitcount_predicate_codegen.txt`
preserves the accepted predicate assembly and complete before/prototype
scale-factor assembly. The frozen final off/on objects have exactly the same `.text` bytes as the
respective before/both prototypes, recorded in
`bitcount_predicate_codegen_identity.json`.

## Tests and sensitivity

`bitcount_predicate_unit.cpp` checks 102,146 boolean cases: zero, full mask,
all 64 singletons and their complements, all 2,016 bit pairs, and 100,000
fixed-seed full-width masks. It checks both at-least-two and exactly-one
identities, although the production exactly-one sites were not changed.

Engine tests compare uncached, cached, repeated-cache-hit and complete traced
HCE against the original default evaluator under separate test-only symbols.
Trace comparisons include all coefficients, phase, scale, side and value.

- 256 bishop fixtures include no bishops, singletons, same-/opposite-square-
  color pairs and promoted triples for both sides and both turns.
- 1,120 pawn fixtures cover no/left/right/double support, board-edge files,
  optional same-rank phalanxes, both colors and both turns.
- BishopPair and PawnDoubleSupport coefficients have independent literal
  expectations in the constructed fixtures.
- The saved 128 search fixtures plus three fixed-seed 4,096-ply legal walks
  include make/unmake/replay and cache resets. There are 38,260 total board
  visits per run, including repeats; this is not a unique-position count.

Before changing production, this characterization suite passed on the
original evaluator. Three temporary deliberately wrong evaluators failed:
single pawn support counted as double, a singleton bishop awarded a pair,
and exactly-two bishops excluding a promoted triple. This is a semantics-
preserving optimization, so the original passing is expected. The mutation
failures establish test sensitivity rather than pretending the original
behavior was defective. Mutations never touched production.

The initial harness attempted to call private runtime-PSQT helpers and did
not compile. That unsupported test access was removed before any completed
run. No production access modifier was changed. Runtime search remains
covered by the official pins and depth-7 comparison gate.

## Frozen source and validation

Production and oracle-test source were frozen first at
`5f0a6e95ebdd49b45061cc942473f32e442869a6`. The validation command is:

```
python3 forge-combo29/tests/bitcount_predicate_check.py \
  5f0a6e95ebdd49b45061cc942473f32e442869a6 /tmp/forge-bitcount-validation
```

It archives only `forge-combo29/src` and `forge-combo29/include`, never the
repository's executables or bundles. Only this experiment is enabled in the
candidate; all other review switches retain their defaults.

Validation results are recorded separately from the source freeze in the
receipt, equivalence JSON, UCI JSON, mutation JSON and validation log bearing
the `bitcount_predicate_` prefix. The receipt identifies compiler, commands,
test hashes, source hashes and artifact hashes. The default-off executable
matches the immutable lock byte-for-byte:

- Off: `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`.
- On: `4d75c1ce1b1aef2a61246564fff1d9aead8ea66124ecd4a5dd5e3782763f64d4`.

Both full official pin suites match all ten NNUE-on/off bench totals and
startpos perft 5 = 4,865,609. Both UCI smoke checks pass. All 256 depth-7
comparisons match depth, nodes, score, PV and bestmove across 128 positions
with NNUE both enabled and disabled.

Both release and both ASan/UBSan runs pass all 38,260 board visits and
102,146 algebra cases without a sanitizer diagnostic. All three final
opt-in mutations fail as expected. LeakSanitizer is disabled in this
environment, so there is no leak-check claim.

Correctness rests on the exact identity plus the oracle/trace/search gates.
The static code-generation simplification is not a measured speedup. Any
separately recorded shared-cloud timing remains exploratory and does not
replace the native Windows/clang-PGO speed or native SPRT Elo gates.


## Diagnostic outcome

The separately preregistered four-block depth-18 cloud run completed without
errors or changed nodes/hashes. Median candidate/baseline CPU duration was
1.00321 with NNUE and 1.01824 with HCE; wall ratios were 1.00335 and 1.01766.
This is not a positive performance screen. Block variability and shared-host
limitations prevent a native regression claim. See
`bitcount_predicate_profile_REVIEW.md` for all block ratios and the fixed
protocol. Keep this correctness-verified experiment default off. Do not
infer speed or Elo gain from its smaller local predicate sequences.
