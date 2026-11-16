"""edit_material_cache.py : the change of job2/optimize_material_key.patch.txt, applied to a fresh copy.

Board gains material_key_ (the same value material_key() computed), set in set_fen, carried through
make_move/unmake_move exactly like pawn_key_, and recomputed only when the piece counts can change (a
capture or a promotion). corrected_eval and update_correction read it instead of re-deriving it.
"""

import re

# ---------------- board.hpp ----------------
p = "include/forge/board.hpp"
s = open(p).read()

s = s.replace("""    std::uint64_t key = 0;
    std::uint64_t pawn_key = 0;
    Bitboard checkers = 0;
    std::uint16_t plies_from_null = 0;""",
"""    std::uint64_t key = 0;
    std::uint64_t pawn_key = 0;
    std::uint64_t material_key = 0;
    Bitboard checkers = 0;
    std::uint16_t plies_from_null = 0;""", 1)

s = s.replace("""    [[nodiscard]] std::uint64_t pawn_key() const { return pawn_key_; }""",
"""    [[nodiscard]] std::uint64_t pawn_key() const { return pawn_key_; }
    // Hash of the piece counts of both sides. It changes only when a capture or a
    // promotion changes a count, so it is kept up to date instead of re-derived.
    [[nodiscard]] std::uint64_t material_key() const { return material_key_; }""", 1)

s = s.replace("""    std::uint64_t key_ = 0;
    std::uint64_t pawn_key_ = 0;
    Bitboard checkers_ = 0;""",
"""    std::uint64_t key_ = 0;
    std::uint64_t pawn_key_ = 0;
    std::uint64_t material_key_ = 0;
    Bitboard checkers_ = 0;""", 1)

s = s.replace("""    [[nodiscard]] std::uint64_t compute_pawn_key() const;""",
"""    [[nodiscard]] std::uint64_t compute_pawn_key() const;
    [[nodiscard]] std::uint64_t compute_material_key() const;""", 1)
open(p, "w").write(s)

# ---------------- board.cpp ----------------
p = "src/board.cpp"
s = open(p).read()

# 1. set_fen
s = s.replace("""    candidate.pawn_key_ = candidate.compute_pawn_key();""",
"""    candidate.pawn_key_ = candidate.compute_pawn_key();
    candidate.material_key_ = candidate.compute_material_key();""", 1)

# 2. make_move: save, then refresh when a count can have changed
s = s.replace("""    undo.key = key_;
    undo.pawn_key = pawn_key_;
    undo.checkers = checkers_;""",
"""    undo.key = key_;
    undo.pawn_key = pawn_key_;
    undo.material_key = material_key_;
    undo.checkers = checkers_;""", 1)

# after the promotion block and the castle block, material is settled; recompute once
s = s.replace("""    key_ ^= Z.castling[castling_];
    castling_ &= static_cast<std::uint8_t>(CastlingMasks[move.from] & CastlingMasks[move.to]);""",
"""    if (undo.captured != Empty || move.is_promotion()) material_key_ = compute_material_key();

    key_ ^= Z.castling[castling_];
    castling_ &= static_cast<std::uint8_t>(CastlingMasks[move.from] & CastlingMasks[move.to]);""", 1)

# 3. unmake_move
s = s.replace("""    key_ = undo.key;
    pawn_key_ = undo.pawn_key;
    checkers_ = undo.checkers;
    plies_from_null_ = undo.plies_from_null;
#if FORGE_SPD_KING_LINES
    king_lines_ = undo.king_lines;
#endif
}

void Board::make_null_move(NullUndo& undo) {""",
"""    key_ = undo.key;
    pawn_key_ = undo.pawn_key;
    material_key_ = undo.material_key;
    checkers_ = undo.checkers;
    plies_from_null_ = undo.plies_from_null;
#if FORGE_SPD_KING_LINES
    king_lines_ = undo.king_lines;
#endif
}

void Board::make_null_move(NullUndo& undo) {""", 1)

# 4. the function itself, moved out of search.cpp
old_fn = """// Hash of the piece counts of both sides, for material-indexed statistics.
[[nodiscard]] std::uint64_t material_key(const Board& board) {
    std::uint64_t key = 0;
    for (const Color color : {White, Black}) {
        for (int type = Pawn; type <= Queen; ++type) {
            key = key * 1099511628211ULL + static_cast<std::uint64_t>(popcount(board.pieces(color, static_cast<PieceType>(type))) + 1);
        }
    }
    return key * 0x9E3779B97F4A7C15ULL;
}

"""
assert old_fn in open("src/search.cpp").read()
q = open("src/search.cpp").read()
q = q.replace(old_fn, "", 1)
open("src/search.cpp", "w").write(q)

s = s.replace("""std::uint64_t Board::compute_pawn_key() const {""",
"""std::uint64_t Board::compute_material_key() const {
    std::uint64_t key = 0;
    for (const Color color : {White, Black}) {
        for (int type = Pawn; type <= Queen; ++type) {
            key = key * 1099511628211ULL + static_cast<std::uint64_t>(popcount(pieces(color, static_cast<PieceType>(type))) + 1);
        }
    }
    return key * 0x9E3779B97F4A7C15ULL;
}

std::uint64_t Board::compute_pawn_key() const {""", 1)
open(p, "w").write(s)

# ---------------- search.cpp: the two call sites ----------------
p = "src/search.cpp"
s = open(p).read()
s = s.replace("""correction += (*material_correction_)[side][material_key(board) & (CorrectionSize - 1U)] * tune::MaterialCorrectionWeight / 100;""",
"""correction += (*material_correction_)[side][board.material_key() & (CorrectionSize - 1U)] * tune::MaterialCorrectionWeight / 100;""", 1)
s = s.replace("""apply((*material_correction_)[side][material_key(board) & (CorrectionSize - 1U)]);""",
"""apply((*material_correction_)[side][board.material_key() & (CorrectionSize - 1U)]);""", 1)
assert "material_key(board)" not in s
open(p, "w").write(s)
print("edit_material_cache applied")
