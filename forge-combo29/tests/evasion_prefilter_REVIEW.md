# Checked-position evasion prefilter: source-only feasibility review

Baseline: `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Scope: only `tests/evasion_prefilter_*`; no production edit, engine build change, match, timing, native speed or strength claim.

## Proposed placement and correctness

The existing `FORGE_SPD_KING_LINES` branch in `Board::is_legal` accepts/rejects ordinary nonking moves through the pinned-piece test only when `checkers_ == 0`. Checked positions instead reconstruct occupancy and call `square_attacked_with_occupancy`. Add a default-off experiment immediately after that existing fast path, before occupancy reconstruction, or inside its checked-position alternative. Do not alter MovePicker generation or sorting.

For a pseudo-legal nonking, non-en-passant move when `checkers_ != 0`:

1. If `checkers_ & (checkers_ - 1)` is nonzero, reject.
2. Otherwise take the sole checker with `lsb(checkers_)`. Reject if `square_bb(move.to)` is disjoint from `checkers_ | attacks::between(king_square(us), checker)`.
3. A surviving move still uses the original complete attack test. The prefilter is necessary, not sufficient.

Proof: the stationary king's existing checker must be captured at its square, or a slider's ray must be blocked at an intermediate square. A normal move adds occupancy only at its destination; vacating its origin cannot block an existing attack. A pawn/knight/adjacent king checker has no intervening ray squares. Two checking slider rays have no intersection except the king square; an existing non-slider checker cannot sit between an attacking slider and king because it would already block that slider. Consequently a single ordinary nonking move cannot neutralize two current checkers. Promotion does not change this occupancy argument.

En passant must bypass conservatively: it removes a checker from a square different from its destination and changes three occupied squares. King moves bypass because they change the square whose safety is tested. A pinned move that interposes against one checker can expose another slider, so the survivor fallback is essential.

## Contracts and state

- `board.hpp` explicitly documents pseudo-legality as a prerequisite of the king-lines fast path. MovePicker validates its TT move with `is_pseudo_legal`; generated moves and legal-existence witnesses supply pseudo-legal geometry. This proposal does not make `is_legal` a general malformed-move validator.
- `checkers_` is set by FEN initialization, recomputed after make, saved/restored by undo, and set to zero during legal null-move processing. No additional cache or Undo field is needed. Null moves made while in check remain outside the legal-search contract.
- `attacks::between` already indexes initialized `BetweenTable`; endpoints are excluded. Do not call `lsb(0)`.
- MovePicker's evasion path scores/sorts the full pseudo list and only the caller filters legality. Removing rejected moves before sorting may alter ties. An equivalent predicate at `is_legal` preserves that list and its ordering.
- Source already has short-circuit pawn/knight/king then bishop/rook attack tests. Avoided full attacks are not all equally expensive. There is no explicit cached-checker evasion geometry in the current checked path. Compiler disassembly has not yet been inspected, so no claim is made that all proposed machine-code work is absent from optimization.

## Bounded probe

`evasion_prefilter_run.py` is default-off. It reads only the immutable baseline's headers, `src/board.cpp`, `src/bitboard.cpp`, through git, plus the explicitly preserved and hashed `evasion_prefilter_positions.fen` fixture copy; no whole-tree archive or bundled Windows executable is copied. It builds only the standalone board probe. Each fixture explores at most 300 positions and two descendant plies, with deterministic traversal. Counts describe this fixture traversal, not search-weighted frequency or a measured cycle saving.

The probe checks all pseudo moves at each visited position against baseline legality, including descendants of baseline-legal moves; rejects must never be baseline legal. It independently reconstructs cached checkers and verifies FEN/checker restoration after undo. Special roots cover double check, ordinary irrelevant nonking moves, legal EP capture of a checking pawn, a pinned interposition survivor, and promotion capture of a checker. It records checked moves, eligible moves, eliminated occupancy checks, bypassed EP/king moves, and remaining illegal survivors. It does not modify baseline sources and does not assert production integration equivalence.

Execution was authorized after the coordinator released the CPU window. Reproduce only after release:

`python3 tests/evasion_prefilter_run.py --run --output tests/evasion_prefilter_results.json`

Future acceptance gates: actual default-off in-function patch in a separate frozen source snapshot, differential legality/perft and fixed-node traces including TT/witness/null paths, assembly inspection, then coordinated native timing. Any count of avoidable full checks is opportunity only; extra branches/bit scans/table loads and cache effects may outweigh it.

## Adversarial parser-accepted positions

FEN validation checks one king each, nonadjacent kings, pawn ranks, piece inventories, castling/EP consistency, and that the side that just moved did not leave its king attacked. It does not establish retrograde reachability or cap the number of checking attackers. The occupancy proof above does not assume legal history and covers more than two checkers by the same rejection. An adjacent enemy king cannot be a parser-accepted checker; if encountered outside that contract, the bypass/fallback does not validate the board. Knight checker squares are nonaligned with the king and therefore have an empty BetweenTable entry; pawn checks are adjacent diagonals with no intermediate squares. Piece-level mutators are private. Arbitrary malformed Move flags, invalid from/to indices, made-illegal positions, and incorrectly paired undo objects remain outside the API's pseudo-legal move/state contract.

## Actual-call instrumentation plan

`evasion_prefilter_calls.py` is also default-off. It snapshots only immutable-lock `src`/`include` source extensions, then builds plain and instrumented engines for KING_LINES=0 and 1. Each executes fresh single-threaded bench16 processes with NNUE on and off. Expected node pins are 3,024,920 and 2,448,617 respectively, enforced for all eight runs. Instrumentation never changes the original return value and counts rejected-but-legal disagreements. The KING_LINES=1 no-check fast-path logic is untouched; an entry counter counts all calls and counters before the common fallback account for residual predicate overhead opportunities. This is counts instrumentation, not a production candidate or a valid timing comparison. Raw engine-reported times are retained only as part of unmodified transcripts and must not be interpreted.

The common fallback still needs a checkers test on no-check king and EP calls; KING_LINES=0 incurs that test for all calls. Eligible surviving checked moves additionally pay a bit-count predicate, bit scan and BetweenTable load before the unchanged attack reconstruction. Counts will quantify the call subsets, not this net machine-code cost.

## Executed bounded results

Fixture receipt: `evasion_prefilter_results.json`. 133 roots, 32,412 visited positions, 1,002,306 pseudo-move comparisons, zero changed legality results. There were 1,711 checked positions, including a double check, one legal EP bypass, 39,520 rejected ordinary moves, and 22 surviving-but-illegal ordinary moves. This is coverage, not the search distribution.

Actual-call receipt: `evasion_prefilter_calls_results.json`. All eight plain/instrumented KING_LINES=0/1 and NNUE on/off bench16 runs preserved the expected 3,024,920/2,448,617 node pins. Both KING_LINES settings had identical call classifications and zero would-reject-but-legal disagreements. The instrumented function always returned the baseline result.

With KING_LINES=1 (existing default):

- NNUE on: 8,634,127 total legality calls; 2,602,512 original full fallbacks; 1,971,410 checked calls. Prefilter rejects 1,553,164 calls, including 12,101 double-check cases: 17.99% of all calls, 59.68% of full fallbacks, 78.78% of checked calls.
- NNUE off: 7,645,530 total legality calls; 2,540,664 original full fallbacks; 2,229,607 checked calls. Prefilter rejects 1,843,476 calls, including 7,945 double-check cases: 24.11% of all calls, 72.56% of full fallbacks, 82.68% of checked calls.
- 631,102/311,057 no-check fallback calls would still pay the new checked-condition test. The 6,031,615/5,104,866 existing no-check pinned-fast-path calls can remain completely unchanged in a production candidate.
- 108,583/110,175 eligible checked moves survive the mask and require full validation. Of these, 813/769 are illegal. Checked king bypasses are 309,269/275,835; checked EP bypasses are 394/121.

With KING_LINES=0 every call already enters the full fallback, so the same 1,553,164/1,843,476 rejects represent 17.99%/24.11% of original full fallbacks; all calls pay the new condition. There is count-based headroom worth a separately authorized, default-off snapshot candidate, but no measured speed gain. Full-attack short-circuit cost, added branches and table traffic must be measured separately. Compiler assembly inspection and actual candidate integration gates remain outstanding.

## Default-off candidate and completed correctness gates

The headroom phase above preceded implementation. Production experiment is now frozen at `8c447f4e676f86ee034f82b33cd0856b00eed230`, after proof commit `86e6d46`. `FORGE_SPD_CHECK_EVASION_PREFILTER` defaults to zero, guards both legality variants, preserves the original king-lines no-check fast path, and changes no move sorting.

Executed gates in `evasion_prefilter_validation.json` and companion logs:

- Full default-off engine is byte-identical to immutable lock: SHA256 `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`.
- Enabled engine preserves all ten NNUE-on/off depth11/13/16/20/22 node pins and start-position perft5 = 4,865,609.
- 256 fixed-depth comparisons against immutable lock pass: exact depth, nodes, score, PV and bestmove, with NNUE both modes.
- Four ASan+UBSan matrix entries (KING_LINES=0/1 × prefilter=0/1) pass with identical results. Every generated pseudo move is compared against make-move plus direct own-king attack recomputation, independently of the candidate's prefilter. Explicit cases cover slider interposition, knight and pawn checker captures, double check, EP checker capture, a pinned illegal survivor, promotion checker capture, and king escape.
- Four unsafe mutations are rejected: omit checker capture, omit interposition, omit EP bypass, and accept mask survivors without full validation. All fail explicit evasion fixtures.
- Compiled default baseline `is_legal` contains no BetweenTable reference, BLSR or TZCNT. Enabled assembly contains one each: compiler did not already synthesize this cached-checker predicate. Both symbol dumps are saved. Source-level fast-path preservation does not imply identical register allocation or instruction addresses when the candidate is enabled.

The fixed four-cycle depth18 CPU/wall diagnostic protocol is in `evasion_prefilter_profile_REVIEW.md`. It is separately frozen before execution. Correctness passes and eliminated-call counts do not establish native speed or strength.
