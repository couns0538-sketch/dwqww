#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdint>
#include <iostream>

namespace {

constexpr int kSearches = 200;
constexpr int kDepth = 10;

std::uint64_t draw(std::uint64_t& state) {
    state += 0x5A17ULL;
    state = (state << 13) | (state >> 51);
    state ^= 0x3C6EF372ULL;
    return state;
}

bool listed(const forge::Board& board, forge::Move move) {
    if (move.is_none()) return false;
    const forge::MoveList legal = board.legal_moves();
    for (std::size_t i = 0; i < legal.size(); ++i) {
        if (legal[i] == move) return true;
    }
    return false;
}

int search_one(forge::Searcher& searcher, const forge::Board& board, const char* label) {
    const forge::MoveList legal = board.legal_moves();
    forge::SearchLimits limits;
    limits.depth = kDepth;
    searcher.clear();
    const forge::SearchInfo info = searcher.search(board, limits, false);
    if (legal.empty()) {
        if (!info.best_move.is_none()) {
            std::cerr << label << " terminal returned " << forge::Board::move_to_uci(info.best_move) << "\n";
            return 1;
        }
        return 0;
    }
    if (!listed(board, info.best_move)) {
        std::cerr << label << " illegal fen " << board.fen()
                  << " move " << forge::Board::move_to_uci(info.best_move) << "\n";
        return 1;
    }
    return 0;
}

forge::Board reach(int index) {
    forge::Board board;
    if (!board.set_fen(forge::Board::StandardStartFen)) return board;
    std::uint64_t state = 0xC0FFEEULL + static_cast<std::uint64_t>(index) * 17ULL;
    const int plies = index % 16;
    for (int ply = 0; ply < plies; ++ply) {
        const forge::MoveList legal = board.legal_moves();
        if (legal.empty()) break;
        const std::size_t pick = static_cast<std::size_t>(draw(state) % legal.size());
        forge::Undo undo;
        if (!board.make_move(legal[pick], undo)) break;
    }
    return board;
}

}  // namespace

int main() {
    if (forge::tune::AspCappedReopen) {
        std::cerr << "AspCappedReopen must default off\n";
        return 1;
    }
    forge::tune::AspCappedReopen = true;

    forge::Searcher searcher(16);
    int legal_moves = 0;
    int terminals = 0;
    for (int index = 0; index < kSearches; ++index) {
        const forge::Board board = reach(index);
        const bool terminal = board.legal_moves().empty();
        if (search_one(searcher, board, "walk") != 0) return 1;
        if (terminal) ++terminals;
        else ++legal_moves;
    }

    // Roots the random walk does not build: check with an escape, a promoting
    // pawn, checkmate, and stalemate. Same depth, same option.
    const char* edges[] = {
        "4r2k/8/8/8/8/8/8/4K3 w - - 0 1",
        "8/P7/8/8/8/8/8/4K2k w - - 0 1",
        "7k/7Q/6K1/8/8/8/8/8 b - - 0 1",
        "k7/2Q5/K7/8/8/8/8/8 b - - 0 1",
    };
    for (const char* fen : edges) {
        forge::Board board;
        if (!board.set_fen(fen)) {
            std::cerr << "rejected fen " << fen << "\n";
            return 1;
        }
        if (search_one(searcher, board, fen) != 0) return 1;
    }

    if (legal_moves + terminals != kSearches) {
        std::cerr << "count mismatch\n";
        return 1;
    }
    std::cout << "asp_legal ok searches " << kSearches << " legal " << legal_moves
              << " terminals " << terminals << " edges 4 depth " << kDepth << "\n";
    return 0;
}
