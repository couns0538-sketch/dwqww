#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

// Two hundred fixed-depth searches with HindsightDepth on. Each best move, and
// every move of the returned principal variation, has to be a legal move in
// the position where it is played.

namespace {

std::uint64_t mix(std::uint64_t& state) {
    state = state * 6364136223846793005ULL + 1442695040888963407ULL;
    return state;
}

forge::Board position_for(int index) {
    forge::Board board;
    if (!board.set_fen(forge::Board::StandardStartFen)) {
        std::cerr << "start position was rejected\n";
        std::exit(1);
    }
    std::uint64_t state = 0xA5A5F00DULL ^ (static_cast<std::uint64_t>(index) * 0x9E3779B97F4A7C15ULL);
    const int steps = static_cast<int>(mix(state) % 28U);
    for (int step = 0; step < steps; ++step) {
        const forge::MoveList moves = board.legal_moves();
        if (moves.empty()) break;
        const forge::Move move = moves[static_cast<std::size_t>(mix(state) % moves.size())];
        forge::Undo undo;
        if (!board.make_move(move, undo)) break;
    }
    return board;
}

bool listed(const forge::MoveList& moves, forge::Move move) {
    for (const forge::Move candidate : moves) {
        if (candidate == move) return true;
    }
    return false;
}

bool line_is_legal(forge::Board board, const std::vector<forge::Move>& line) {
    for (const forge::Move move : line) {
        if (!listed(board.legal_moves(), move)) return false;
        forge::Undo undo;
        if (!board.make_move(move, undo)) return false;
    }
    return true;
}

} // namespace

int main() {
    if (forge::tune::HindsightDepth) {
        std::cerr << "HindsightDepth is on before the test sets it\n";
        return 1;
    }
    forge::tune::HindsightDepth = true;

    forge::Searcher searcher(16);
    constexpr int searches = 200;
    constexpr int depth = 10;
    for (int index = 0; index < searches; ++index) {
        const forge::Board board = position_for(index);
        const forge::MoveList legal = board.legal_moves();
        searcher.clear();
        forge::SearchLimits limits;
        limits.depth = depth;
        const forge::SearchInfo info = searcher.search(
            board, limits, false, forge::Searcher::TTAccess::Exclusive);
        const bool terminal = legal.empty();
        const bool best_ok = terminal ? info.best_move.is_none() : listed(legal, info.best_move);
        if (!best_ok || !line_is_legal(board, info.pv)) {
            std::cerr << "illegal result index " << index
                      << " move " << forge::Board::move_to_uci(info.best_move)
                      << " fen " << board.fen() << "\n";
            return 1;
        }
    }
    std::cout << "legal " << searches << " depth " << depth << " HindsightDepth on\n";
    return 0;
}
