No source blocker found in the isolated nearest-pawn prototype. Execution and
performance remain pending. All76 files exactly match EXPECTED-SOURCE-76.json;
only CMakeLists.txt, bitboard.hpp and eval.cpp differ from frozen20, plus the new
test. Version metadata genuinely remains20. Hashes/delta are preserved alongside.

Geometry and bounds: bitboard.hpp:105-113 builds inclusive Chebyshev radius0..6
masks; radius7 implicitly covers every square. For two-or-more targets, lines121-123
select [0,3] or [4,7] through mask3; mask1/mask5 narrows to [0,1]/[2,3]/[4,5]/[6,7];
mask0/2/4/6 chooses the exact smaller answer. Every accessed radius is0..6:
first3, then1or5, then0/2/4/6. The resulting distance is0..7. No occupancy,
color, pin or king-path restriction belongs in Chebyshev distance. Equal-square
input correctly returns0. Empty input takes the existing7 convention; a nonzero
singleton uses the old square_distance and never passes zero to countr_zero.
Unsigned more_than_one(0) subtraction is defined. The helper requires square0..63,
matching existing square/mask APIs; Board::set_fen enforces exactly one king per
side (board.cpp:259), and production passes board.king_square through EvalInfo.
No arbitrary invalid-square API guarantee is added by this review.

Old-loop equivalence: eval.cpp:269-271 retains the own_pawns!=0 guard and exactly
one KingPawnDistance add in its original order. For any valid king square and
pawn bitboard it computes the old min(7, all Chebyshev distances), without changing
packed score arithmetic, taper/scaling, cache keys or feature coefficients. This
same templated call serves public/cache/runtime and traced evaluation. Trace=true
still receives the identical integer feature multiplicity. The constexpr table
is immutable geometry, nominal3584bytes, with no new mutable cache/invalidation.
NNUE, weights, Board, search, dirty-piece updates and runtime-PSQT sources/headers
are byte-identical to20. Header inclusion does not establish compiled NNUE-object
identity; that still needs the ordinary binary/object checks.

Oracle review: the production table generator uses existing square_distance.
The scalar test independently calculates abs(file difference),abs(rank difference)
using arithmetic, not the table/helper/production square_distance. The king-flood
oracle independently expands an accumulated reachable set with vertical shifts,
then file-masked horizontal shifts; these eight-neighbor steps generate exactly
Chebyshev balls without a FileA/H wrap. It does not call attack tables or the new
mask generator. Both return7 for an empty set, matching the explicit old convention.
They provide independent algorithms, not independent compilers or runtime proof.
Six constexpr assertions exercise empty, singleton, overlap,distant/near and dense
cases. Loop arithmetic implies395840 target sets and791680 oracle comparisons:
64*(1empty+64singletons+2016pairs+2048ranksubsets+2048random+8dense).
These are planned counts, not observed PASS counts. All-square pairs/rank subsets
cover every king location, edge, distance and both implicit color orientations;
the larger random/dense sets add multi-target coverage. No malformed-position or
chess-legality inference follows from geometry fixtures.

CMake registers the new forge_nearest_pawn_tests as the fifth test, linked to the
actual forge_core; existing tests remain in place. New compiler constexpr work
and all13 runtime suites remain to be checked by the authorized build owner.
Next gate: actual frozen-source Release/tests, full public cached/runtime/uncached
and trace parity versus20, exact1T cold/warm search parity and unchanged-state/
NNUE evidence. Only a separately calibrated frozen workload can establish speed;
this review provides no NPS, playing-strength or Elo result.

Method: read-only source and SHA inspection, no compilation, engine, timing,
helper/model execution or Git operation. Only this independent-review directory
was written; production tree, isolated prototype and source manifest untouched.
