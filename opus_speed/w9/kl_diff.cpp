// kl_diff.cpp - differential test of FORGE_SPD_KING_LINES (own code, speed job W9).
// Links against w9dev/src/board.cpp built with FORGE_SPD_KING_LINES=1 and compares Board::is_legal and
// Board::gives_check with reference versions that restate the lock's rules through the public accessors.
// For every FEN: every pseudo-legal move of the parent; every pseudo-legal move of every child (after make_move);
// the parent again after unmake (cache restore); the same around a null move. Exit 0 = no mismatch.
#include "forge/board.hpp"

#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

using namespace forge;

namespace {

bool attacked_ref(const Board& b, int square, Color by, Bitboard occupancy, Bitboard removed) {
    const Bitboard available = ~removed;
    if ((attacks::pawn(opposite(by), square) & b.pieces(by, Pawn) & available) != 0) return true;
    if ((attacks::knight(square) & b.pieces(by, Knight) & available) != 0) return true;
    if ((attacks::king(square) & b.pieces(by, King) & available) != 0) return true;
    const Bitboard queens = b.pieces(by, Queen) & available;
    if ((attacks::bishop(square, occupancy) & ((b.pieces(by, Bishop) & available) | queens)) != 0) return true;
    return (attacks::rook(square, occupancy) & ((b.pieces(by, Rook) & available) | queens)) != 0;
}

bool ref_is_legal(const Board& b, const Move& move) {
    const Color us = b.side_to_move();
    const Piece moving = b.piece_at(move.from);
    Bitboard occupancy = b.occupied() & ~square_bb(move.from);
    int captured_square = move.to;
    if ((move.flags & EnPassant) != 0U) captured_square = move.to - pawn_push_delta(us);
    Bitboard removed = 0;
    if (move.is_capture()) {
        removed = square_bb(captured_square);
        occupancy &= ~removed;
    }
    occupancy |= square_bb(move.to);
    if (move.is_castle()) {
        const bool king_side = (move.flags & KingCastle) != 0U;
        const int rook_from = us == White ? (king_side ? 7 : 0) : (king_side ? 63 : 56);
        const int rook_to = us == White ? (king_side ? 5 : 3) : (king_side ? 61 : 59);
        occupancy &= ~square_bb(rook_from);
        occupancy |= square_bb(rook_to);
    }
    const int king = piece_type(moving) == King ? static_cast<int>(move.to) : b.king_square(us);
    return !attacked_ref(b, king, opposite(us), occupancy, removed);
}

bool ref_gives_check(const Board& b, const Move& move) {
    const Color us = b.side_to_move();
    const Color them = opposite(us);
    const int ksq = b.king_square(them);
    const Bitboard king_bit = square_bb(ksq);
    Bitboard occ = (b.occupied() ^ square_bb(move.from)) | square_bb(move.to);
    if ((move.flags & EnPassant) != 0U) occ &= ~square_bb(move.to - pawn_push_delta(us));
    if (move.is_castle()) {
        const bool king_side = (move.flags & KingCastle) != 0U;
        const int rook_from = us == White ? (king_side ? 7 : 0) : (king_side ? 63 : 56);
        const int rook_to = us == White ? (king_side ? 5 : 3) : (king_side ? 61 : 59);
        occ = (occ & ~square_bb(rook_from)) | square_bb(rook_to);
        if ((attacks::rook(rook_to, occ) & king_bit) != 0) return true;
    }
    const int type = move.is_promotion() ? move.promotion : piece_type(b.piece_at(move.from));
    Bitboard direct = 0;
    switch (type) {
    case Pawn: direct = attacks::pawn(us, move.to); break;
    case Knight: direct = attacks::knight(move.to); break;
    case Bishop: direct = attacks::bishop(move.to, occ); break;
    case Rook: direct = attacks::rook(move.to, occ); break;
    case Queen: direct = attacks::queen(move.to, occ); break;
    default: break;
    }
    if ((direct & king_bit) != 0) return true;
    const Bitboard moved = square_bb(move.from);
    const Bitboard diagonals = (b.pieces(us, Bishop) | b.pieces(us, Queen)) & ~moved;
    const Bitboard lines = (b.pieces(us, Rook) | b.pieces(us, Queen)) & ~moved;
    if (diagonals != 0 && (attacks::bishop(ksq, occ) & diagonals) != 0) return true;
    return lines != 0 && (attacks::rook(ksq, occ) & lines) != 0;
}

struct Stats {
    long positions = 0;
    long moves = 0;
    long legal = 0;
    long checks = 0;
    long mismatch_legal = 0;
    long mismatch_check = 0;
    long shown = 0;
};

// Compares both functions for every pseudo-legal move of the current position.
void compare_position(Board& b, const std::string& label, Stats& st) {
    ++st.positions;
    const MoveList moves = b.pseudo_legal_moves(false);
    for (const Move m : moves) {
        ++st.moves;
        const bool l_new = b.is_legal(m);
        const bool l_ref = ref_is_legal(b, m);
        if (l_new != l_ref) {
            ++st.mismatch_legal;
            if (st.shown++ < 20) std::printf("LEGAL MISMATCH %s move %s new=%d ref=%d fen %s\n", label.c_str(),
                                             Board::move_to_uci(m).c_str(), l_new, l_ref, b.fen().c_str());
        }
        if (!l_ref) continue;
        ++st.legal;
        const bool c_new = b.gives_check(m);
        const bool c_ref = ref_gives_check(b, m);
        if (c_ref) ++st.checks;
        if (c_new != c_ref) {
            ++st.mismatch_check;
            if (st.shown++ < 20) std::printf("CHECK MISMATCH %s move %s new=%d ref=%d fen %s\n", label.c_str(),
                                             Board::move_to_uci(m).c_str(), c_new, c_ref, b.fen().c_str());
        }
    }
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::printf("usage: kl_diff <fen file> [max positions]\n");
        return 2;
    }
    std::ifstream in(argv[1]);
    if (!in) {
        std::printf("cannot open %s\n", argv[1]);
        return 2;
    }
    const long limit = argc > 2 ? std::atol(argv[2]) : 0;
    Board board;
    Stats st;
    long fens = 0;
    long rejected = 0;
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty() || line[0] == '#') continue;
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
        std::string error;
        if (!board.set_fen(line, &error)) {
            ++rejected;
            continue;
        }
        ++fens;
        if (limit > 0 && fens > limit) break;
        compare_position(board, "parent", st);
        // Every child, then the parent again (the Undo restore of the cache).
        const MoveList moves = board.pseudo_legal_moves(false);
        for (const Move m : moves) {
            if (!ref_is_legal(board, m)) continue;
            Undo undo;
            (void)board.make_move(m, undo);
            compare_position(board, "child", st);
            // Grandchild of the first legal reply exercises a second make / unmake level.
            const MoveList replies = board.pseudo_legal_moves(false);
            for (const Move r : replies) {
                if (!ref_is_legal(board, r)) continue;
                Undo undo2;
                (void)board.make_move(r, undo2);
                compare_position(board, "grandchild", st);
                board.unmake_move(r, undo2);
                break;
            }
            compare_position(board, "child-after-unmake", st);
            board.unmake_move(m, undo);
        }
        compare_position(board, "parent-after-unmake", st);
        if (!board.in_check()) {
            NullUndo nu;
            board.make_null_move(nu);
            compare_position(board, "null-child", st);
            board.unmake_null_move(nu);
            compare_position(board, "parent-after-null", st);
        }
    }
    std::printf("fens %ld rejected %ld positions %ld moves %ld legal %ld checks %ld mismatch_legal %ld mismatch_check %ld\n",
                fens, rejected, st.positions, st.moves, st.legal, st.checks, st.mismatch_legal, st.mismatch_check);
    return (st.mismatch_legal == 0 && st.mismatch_check == 0 && fens > 0) ? 0 : 1;
}
