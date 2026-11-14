// 200 depth-10 searches. Every best move and every PV move must be legal.
// Build with -fsanitize=address,undefined. A sanitizer finding aborts the process.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

namespace {

constexpr int kSearches = 200;
constexpr int kDepth = 10;

bool contains(const forge::MoveList& moves, forge::Move move) {
    for (const forge::Move candidate : moves) {
        if (candidate == move) return true;
    }
    return false;
}

bool king_left_safe(const forge::Board& before, forge::Move move) {
    const forge::Color mover = before.side_to_move();
    int king = before.king_square(mover);
    // Castling and ordinary king moves store the king's destination in move.to.
    if (move.from == king) king = move.to;
    forge::Board after = before;
    forge::Undo undo;
    if (!after.make_move(move, undo)) return false;
    return !after.square_attacked(king, after.side_to_move());
}

bool line_legal(const forge::Board& root, const std::vector<forge::Move>& line, std::string& why) {
    forge::Board board = root;
    for (std::size_t i = 0; i < line.size(); ++i) {
        const forge::Move move = line[i];
        const forge::MoveList legal = board.legal_moves();
        const bool listed = contains(legal, move);
        const bool safe = king_left_safe(board, move);
        if (!listed || !safe) {
            why = "illegal pv[" + std::to_string(i) + "] " + forge::Board::move_to_uci(move) +
                  " listed=" + std::to_string(static_cast<int>(listed)) +
                  " safe=" + std::to_string(static_cast<int>(safe)) + " in " + board.fen();
            return false;
        }
        forge::Undo undo;
        if (!board.make_move(move, undo)) {
            why = "make_move rejected " + forge::Board::move_to_uci(move);
            return false;
        }
    }
    return true;
}

std::vector<std::string> sample_positions() {
    std::vector<std::string> fens;
    fens.reserve(static_cast<std::size_t>(kSearches));
    forge::Board walk;
    std::uint64_t rng = 0xC0FFEE5EEDULL;
    int ply = 0;
    while (static_cast<int>(fens.size()) < kSearches) {
        forge::MoveList legal = walk.legal_moves();
        if (legal.empty() || ply >= 12) {
            walk = forge::Board();
            ply = 0;
            legal = walk.legal_moves();
        }
        if (legal.empty()) return {};
        fens.push_back(walk.fen());
        rng = rng * 6364136223846793005ULL + 1ULL;
        const forge::Move move = legal[static_cast<std::size_t>(rng % legal.size())];
        forge::Undo undo;
        if (!walk.make_move(move, undo)) return {};
        ++ply;
    }
    return fens;
}

}  // namespace

int main() {
    const std::vector<std::string> fens = sample_positions();
    if (static_cast<int>(fens.size()) != kSearches) {
        std::cerr << "could not sample " << kSearches << " positions\n";
        return 1;
    }

    forge::Searcher searcher(16, 1);
    for (int index = 0; index < kSearches; ++index) {
        forge::Board board;
        if (!board.set_fen(fens[static_cast<std::size_t>(index)])) {
            std::cerr << "rejected fen " << fens[static_cast<std::size_t>(index)] << '\n';
            return 1;
        }
        const forge::MoveList legal = board.legal_moves();
        if (legal.empty()) {
            std::cerr << "sampled a terminal position\n";
            return 1;
        }
        forge::SearchLimits limits;
        limits.depth = kDepth;
        searcher.clear();
        const forge::SearchInfo info = searcher.search(board, limits, false);
        if (info.depth != kDepth) {
            std::cerr << "search " << index << " depth " << info.depth << " fen " << board.fen() << '\n';
            return 1;
        }
        if (info.best_move.is_none() || !contains(legal, info.best_move) || !king_left_safe(board, info.best_move)) {
            std::cerr << "search " << index << " illegal best " << forge::Board::move_to_uci(info.best_move)
                      << " fen " << board.fen() << '\n';
            return 1;
        }
        if (info.pv.empty() || !(info.pv.front() == info.best_move)) {
            std::cerr << "search " << index << " pv does not start with the best move\n";
            return 1;
        }
        std::string why;
        if (!line_legal(board, info.pv, why)) {
            std::cerr << "search " << index << " root " << board.fen() << " pv";
            for (const forge::Move move : info.pv) std::cerr << ' ' << forge::Board::move_to_uci(move);
            std::cerr << '\n' << why << '\n';
            return 1;
        }
        std::cout << "search " << (index + 1) << " depth " << info.depth << " move "
                  << forge::Board::move_to_uci(info.best_move) << " pv " << info.pv.size() << '\n';
        std::cout.flush();
    }
    std::cout << "PASS " << kSearches << " depth-" << kDepth << " searches, every move legal\n";
    return 0;
}
