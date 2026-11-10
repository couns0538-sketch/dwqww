# Bounded legal-witness experiment

Status: UNPROVEN optimization, default off. No speed, strength or acceptance claim.
Production source commit: 4d9815a1e1a0807a8891be624a1c865af32299a3.
Switch: FORGE_SPD_LEGAL_WITNESSES (default 0, src/board.cpp).

## Scope and exactness argument

After the existing lowest quiet pawn-push witness fails, test at most two additional moves: the lowest target from the lowest knight, then the lowest king target. This deliberately does not scan every knight, every destination, promotions or castles. The complete existing move-generation fallback is unchanged.

For each added witness, knight/king attack geometry establishes its movement pattern. Own occupied squares and the opposing king are excluded. A nonempty target is therefore an enemy capture and gets Capture, otherwise Quiet. Promotion and other special flags remain zero. These are pseudo-legal moves, satisfying is_legal's documented precondition even with KING_LINES enabled. An added true return therefore proves existence of a legal move. If both probes fail, the original full-list answer still determines the result. No game state, hashes or search constants change; only the existing lazy king-lines cache may be populated earlier.

Cost is bounded by two extra legality checks after a failed pawn witness; most positions that succeed on the old pawn probe do no extra work. Whether the added checks cost less than saved fallback generation is an empirical question, not established by this implementation.

## Sanitized differential existence tests

Run tests/legal_witness_check.sh. Executed with g++-14, C++20, -O1, ASan and UBSan, leak detection disabled. Both witness modes crossed with both KING_LINES modes passed with identical output:

`PASS positions=17755 pawn_hits=15575 knight_hits=862 king_hits=789 fallback=529 capture_hits=146 seed=20261114`

Counts describe a modeled witness path over the test corpus, not instrumented engine hotspots or a timing profile. Every tested witness is separately checked with is_pseudo_legal. Actual has_legal_move is compared to complete legal_moves existence, while FEN/key stability is checked. The corpus includes 100 seeded games up to 180 plies plus focused fixtures and their legal children.

Required focused cases:
- `7k/8/8/7b/8/8/4P3/1N1K4 w - - 0 1`: lowest pawn e2e3 is diagonally pinned; Nb1d2 is a legal knight witness.
- `7k/8/8/8/8/6b1/8/r1NK2N1 w - - 0 1`: first knight Nc1a2 exposes Ra1 and first king target e1 is attacked by Bg3; the full fallback finds later Ng1e2.
- `7k/8/8/8/8/8/8/3rK3 w - - 0 1`: king witness Ke1xd1 captures the checking rook.
- `7k/8/8/8/8/8/8/r2rK3 w - - 0 1`: the same capture is illegal because Ra1 attacks d1, but later king escapes exist.
- Explicit checkmate and stalemate, double check, EP and pinned-promotion positions remain consistent with the complete legal list.

## Isolated full-engine validation

Run tests/legal_witness_engine_check.sh with an output directory. It builds off/on binaries using the combo29 x86-64-v4 review flags, changing only FORGE_SPD_LEGAL_WITNESSES; runs all 10 prescribed NNUE-on/off bench pins and startpos perft5; and compares 128 FENs at depth7 with NNUE on/off (256 comparisons of nodes, score, PV and bestmove). Completion evidence is recorded separately after that run finishes. This is not a strength or timing test.
