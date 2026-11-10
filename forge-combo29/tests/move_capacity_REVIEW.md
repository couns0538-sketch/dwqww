# Bounded MoveList capacity audit

Status: no overflow reproduced; finite search, not a proof that 256 always suffices.
2026-11-10 UTC. No production edits. Production MoveList::Capacity remains 256.

## Why legal-move counts are insufficient

The buffer is filled by pseudo-legal generation before king-safety filtering. The largest observed accepted FEN in this search has **209 pseudo-legal moves but only 3 legal moves**:

`krK1B2R/pp4Q1/3Q4/Q4Q2/2Q4Q/4Q3/1R4Q1/3Q4 w - - 0 1`

This leaves 47 slots below 256 in this corpus, not a universal headroom guarantee. At include/forge/board.hpp:108–112 the source still relies on a debug assert in MoveList::push_back; release writes are unchecked. This audit did not establish an accepted position that breaches that implicit capacity contract.

## Safe counting method

`tests/move_capacity_search.sh` copies board.hpp to an output-directory include override and changes ONLY that copy's Capacity from 256 to 1024. Both the harness and production board.cpp are compiled against that same test-only header. The production header is not changed. A static_assert ensures the search cannot accidentally run with capacity256.

The enlarged limit is comfortably above a loose geometry bound for accepted inventories: at most16 pieces per side, each with at most27 ordinary/promotion move outputs, plus at most2 castles, is below1024. This justifies the test buffer, not the production256 limit. These fixtures use no castling rights or EP field.

The search scores positions with a separate geometric counter: pawn single/double pushes, four promotion variants per promotion target, pawn captures, and popcounts of N/B/R/Q/K targets excluding own occupancy. Every newly observed global maximum and each per-configuration maximum is cross-checked against the actual production pseudo generator using the enlarged list. Legal counts are calculated separately. Checks do not constrain the side to move: set_fen acceptance is required, but the moving king may be in check, which matters for pseudo count.

## Deterministic bounded search

Seed20261115; 78 configurations, 6000 proposals each: 468000 proposals, 304602 parser-accepted proposals. Rejected/occupied-destination proposals are not counted as accepted. This is a constrained hillclimb with bounded temperature variation, not exhaustive placement enumeration.

Families:
- Full16-piece side-to-move inventories with 0..8 pawns and promotion-budget-valid extra queens/minors.
- Enemy king protected in a corner with two pawns and a rook, or additional eighth-rank rook capture targets to encourage promotion fanout. Enemy inventory is also parser-validated.
- Sparse variants remove one through six original minor/rook pieces, retaining the promotion budget, to test whether less self-blocking increases pseudo counts.
- White arrangements in the search, with color/rank-mirrored Black arrangements included in production replay.

The initial54-configuration pass observed208. Adding the bounded sparse family raised that to209, demonstrating why the smaller initial corpus was not treated as a proof. Full progress and per-configuration results are preserved in move_capacity_search_results.txt; replay fixtures with expected pseudo/legal counts are in move_capacity_maxima.txt.

Reproduce the search with `tests/move_capacity_search.sh /tmp/forge-move-capacity`. It uses g++-14, C++20, -O2. The optimization loop itself is not sanitizer-instrumented; safe enlarged counting precedes the sanitizer replay.

## Actual production256 replay

Run `tests/move_capacity_replay.sh`. It builds with real Capacity256, -O1, -DNDEBUG (release-style assertions disabled), ASan and UBSan, leak detection disabled. The matrix crosses LEGAL_WITNESSES0/1 with KING_LINES0/1 and NO_ZERO_MOVELISTS0/2: eight configurations cover both generator implementations and the separate quiet-generation path.

Every saved maximum and its color mirror must reproduce both pseudo/legal counts; has_legal_move must agree with legal-list existence; every generated move must pass is_pseudo_legal; quiet and noisy lists must partition the full list. Explicit excess-pawn, promotion-budget and total-piece inventory examples must be rejected.

The initial108-position replay passed all four configurations: max208, 2040 generated promotion variants, 1848 captures, 10 positions in check, and all3 impossible-inventory rejections. Final replay passed all eight configurations without ASan/UBSan diagnostics:

`PASS production_capacity=256 positions=156 max_pseudo=209 headroom=47 promotions=2176 captures=2192 in_check=14 inventory_rejections=3`

Counts describe each replay corpus, not performance measurements. No accepted overflow example was found; the production256 bound remains unproved by this finite audit.

## Limitations

This finite constrained search does not prove that a larger accepted position cannot exist. It does not cover all piece inventories, king locations, EP histories or castling rights. It does not prove historical reachability of accepted FENs, which was deliberately unnecessary for this API safety question. No production capacity reduction, strengthening claim, or speed claim follows from the results.

Static call-site check found the Board convenience wrappers using fresh MoveList objects and search MovePicker generation clearing its reused buffer before each fill (src/search.cpp generate_captures/generate_quiets/generate_evasions). No accidental accumulated-list overflow path was identified in those callers. This does not make the public append API intrinsically bounds-safe.
