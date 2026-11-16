#!/usr/bin/env python3
"""Variant E: relativise the COLOUR-ABSOLUTE piece index of the continuation / piece-to-history tables.

`PieceToHistory` and `ContinuationHistory` (include/forge/search.hpp:384-385) are 13-slot arrays indexed by
`static_cast<std::size_t>(piece)` where `Piece` is colour-absolute (include/forge/board.hpp:35-40):
WP=1, WN=2, WB=3, WR=4, WQ=5, WK=6, BP=7, ... BK=12. So in a colour-mirrored pair the mover's knight
writes slot 2 on one side and slot 8 on the other - two different history tables. `ButterflyHistory`
by contrast is indexed by `[side_to_move()]`, a relative 2-slot index, and does map under a mirror.

This variant maps the piece through the mover's own frame before indexing, everywhere those tables
are touched, and changes nothing else. The mapping keeps 13 slots (0 unused, 1..6 our pieces, 7..12
their pieces) so the array sizes and every other type stay identical:

    rel_piece(piece, us) = colour_of(piece)==us ? piece_type(piece) : 6 + piece_type(piece)

usage: make_variant_e.py BASE_SEARCH_CPP OUT
"""
import sys

src, out = sys.argv[1:3]
text = open(src).read()

HELPER = """namespace {

// Symmetry experiment (swarm seat 06): the piece-to-history and continuation tables are indexed by
// Piece, which is COLOUR-ABSOLUTE (WP=1..BK=12), so the same piece of the other colour lands in a
// different slot and a colour-mirrored search reads different history. Map the piece into the
// mover's own frame first: our pieces 1..6, their pieces 7..12, 0 unused. Slot count is unchanged.
[[nodiscard]] inline std::size_t rel_piece(const Piece piece, const Color us) {
    const int type = piece_type(piece);
    return static_cast<std::size_t>(color_of(piece) == us ? type : 6 + type);
}

} // namespace
"""

ANCHOR = "namespace forge {"
assert ANCHOR in text
text = text.replace(ANCHOR, ANCHOR + "\n\n" + HELPER, 1)

# --- reads in quiet_history (the non-SPEED2 branch) ---
OLD_R1 = """        if ((ss - 1)->continuation != nullptr) score += (*(ss - 1)->continuation)[static_cast<std::size_t>(piece)][move.to];
        if ((ss - 2)->continuation != nullptr) score += (*(ss - 2)->continuation)[static_cast<std::size_t>(piece)][move.to];"""
NEW_R1 = """        const std::size_t rel = rel_piece(piece, board.side_to_move());
        if ((ss - 1)->continuation != nullptr) score += (*(ss - 1)->continuation)[rel][move.to];
        if ((ss - 2)->continuation != nullptr) score += (*(ss - 2)->continuation)[rel][move.to];"""
if OLD_R1 in text:
    text = text.replace(OLD_R1, NEW_R1, 1)

OLD_R2 = """            score += (*(ss - 4)->continuation)[static_cast<std::size_t>(piece)][move.to] / 2;"""
NEW_R2 = """            score += (*(ss - 4)->continuation)[rel][move.to] / 2;"""
if OLD_R2 in text:
    text = text.replace(OLD_R2, NEW_R2, 1)

# --- the write in update_continuation ---
OLD_W = """        apply_history((*previous->continuation)[static_cast<std::size_t>(piece)][static_cast<std::size_t>(to)],
                      back == 4 ? bonus / 2 : bonus);"""
NEW_W = """        apply_history((*previous->continuation)[rel_piece(piece, us)][static_cast<std::size_t>(to)],
                      back == 4 ? bonus / 2 : bonus);"""
assert OLD_W in text
text = text.replace(OLD_W, NEW_W, 1)

# update_continuation needs `us`; add it from the stack frame
OLD_UPD = """void Worker::update_continuation(SearchStack* ss, Piece piece, int to, int bonus) {"""
NEW_UPD = """void Worker::update_continuation(SearchStack* ss, Piece piece, int to, int bonus) {
    const Color us = color_of(piece);"""
assert OLD_UPD in text
text = text.replace(OLD_UPD, NEW_UPD, 1)

# --- the pointer write that selects which table a child will read ---
OLD_P = """        ss->continuation = &(*continuation_history_)[static_cast<std::size_t>(ss->moved_piece)][move.to];"""
NEW_P = """        ss->continuation = &(*continuation_history_)[rel_piece(ss->moved_piece, board.side_to_move())][move.to];"""
assert OLD_P in text
text = text.replace(OLD_P, NEW_P, 1)

open(out, "w").write(text)
print("wrote", out)
