# Bounded FEN and UCI position audit

2026-11-10 UTC. Production source unchanged. g++-14; C++20, -O1, ASan+UBSan, leak detection disabled. Run tests/fen_audit_check.sh from forge-combo29.

## Board parser and serialization

Observed sanitized result:

`PASS explicit_rejections=23 valid_roundtrips=3007 mutations_accepted=234 mutations_rejected=19766 seed=20261113`

The explicit rejected cases include missing/extra fields, empty/no-king board, extra/missing ranks, invalid squares/pieces, adjacent/extra kings, promotion-rank pawn, excess pawn inventory, invalid side/castling/EP, negative/zero/overflowing counters, and a late rejection because the side that just moved is in check. A 10,000-character malformed placement is included.

A rich existing board with repetition history is retained as the rejection baseline. After every rejected input, the harness compares FEN, keys, pawn key, checkers, history, squares, occupancies, king squares and ordered legal moves against that baseline. All rejected inputs preserved it.

3,000 positions from seeded legal play plus seven explicit accepted FENs are serialized, reparsed and compared. Accepted FENs replace the repetition history with one position. Another 20,000 deterministic byte/string mutations (including NUL/high-bit bytes, insertions, deletions and truncations) either reject atomically or successfully round-trip through canonical serialization. The 234 accepted mutations are not automatically defects: many are equivalent or represent another valid position.

Parser implementation relevant to the audit: src/board.cpp:219-227 reads exactly six fields; placement bounds are checked before indexing; set_fen constructs a scratch Board for late validation and commits only at the end.

## Accepted noncanonical inputs are not memory-safety findings

Explicit examples accepted and normalized:
- Leading plus signs and zero padding in numeric fields.
- Castling letters in a noncanonical order (serialization emits KQkq order).
- A rank encoded as eight adjacent `1` digits instead of `8`.
- EP target with no capturing pawn, provided the last-move geometry is consistent.
- Positive counters through signed 64-bit maximum, saturated to 65535 when stored.

These are documented parser choices or permissive forms. This audit does not require retrograde validation of every chess position, and does not label permissiveness as out-of-bounds access, UB or corruption.

## UCI transaction scope

The harness includes production src/uci.cpp with its main renamed, invoking the actual anonymous-namespace apply_position directly. It does not reimplement parsing, but it also does not exercise the outer line-reading/search-thread loop. src/uci.cpp:42-76 starts from a copy; malformed FEN or any illegal move returns before assignment. A successful position commits at lines 63 or 76.

The harness tests rejection after valid move prefixes, malformed/truncated FEN, unknown tokens, invalid suffixes and a long invalid move, against a board with existing history. It also checks successful startpos moves, an empty moves list, and FEN plus legal moves. The first build exposed a test-only helper-name collision with std::apply, corrected by renaming the helper. The complete script was then rebuilt and run successfully under ASan/UBSan, with no diagnostics:

`PASS actual_UCI_position_handler rejected_atomic=17 valid_commits=3`

No state corruption, out-of-bounds access or UB was reproduced in this bounded audit. This does not establish behavior for unbounded resource exhaustion or every malformed string.
