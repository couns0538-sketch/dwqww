#include "forge/eval.hpp"
#include "forge/search.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

namespace {

int g_failures = 0;

void fail(const std::string& message) {
    std::cerr << "fail: " << message << '\n';
    ++g_failures;
}

std::vector<std::string> make_positions() {
    return {
        "8/1k6/8/8/5K2/7B/6N1/8 w - - 0 1",
        "8/8/B4K2/8/8/8/1k4N1/8 w - - 0 1",
        "8/8/8/8/8/8/k6N/4KB2 w - - 0 1",
        "1k6/8/4N3/2K5/8/8/8/B7 w - - 0 1",
        "1N6/5K1B/8/8/8/2k5/8/8 w - - 0 1",
        "8/8/7B/8/7k/8/5N2/5K2 w - - 0 1",
        "8/5K2/8/k7/8/N7/8/5B2 w - - 0 1",
        "7K/8/3k4/6B1/7N/8/8/8 w - - 0 1",
        "4K3/3B4/8/8/8/8/1k6/5N2 w - - 0 1",
        "1k6/8/8/1N6/B7/3K4/8/8 w - - 0 1",
        "2K2k2/8/8/8/8/8/8/N4B2 w - - 0 1",
        "8/8/8/1B6/6k1/2N5/5K2/8 w - - 0 1",
        "7N/8/3k4/B7/8/6K1/8/8 w - - 0 1",
        "8/B7/5k2/8/8/8/3N4/5K2 w - - 0 1",
        "1B1k4/8/8/8/7N/8/K7/8 w - - 0 1",
        "8/4N3/3B4/8/8/5K2/8/7k w - - 0 1",
        "7K/8/8/8/1k2B3/4N3/8/8 w - - 0 1",
        "2N3K1/8/8/8/8/k7/8/7B w - - 0 1",
        "8/1N6/6K1/5B2/8/2k5/8/8 w - - 0 1",
        "8/8/2N5/4K3/7k/2B5/8/8 w - - 0 1",
    };
}

std::string swap_colors(std::string fen) {
    const auto white = fen.find(" w ");
    const auto black = fen.find(" b ");
    const auto cut = white != std::string::npos ? white : black;
    if (cut == std::string::npos) return fen;
    for (std::size_t i = 0; i < cut; ++i) {
        char& ch = fen[i];
        if (ch >= 'a' && ch <= 'z') ch = static_cast<char>(ch - 'a' + 'A');
        else if (ch >= 'A' && ch <= 'Z') ch = static_cast<char>(ch - 'A' + 'a');
    }
    if (white != std::string::npos) fen.replace(white, 3, " b ");
    else fen.replace(black, 3, " w ");
    return fen;
}

bool is_kbnk(const forge::Board& board, forge::Color& strong) {
    const int wn = forge::popcount(board.pieces(forge::White, forge::Knight));
    const int bn = forge::popcount(board.pieces(forge::Black, forge::Knight));
    const int wb = forge::popcount(board.pieces(forge::White, forge::Bishop));
    const int bb = forge::popcount(board.pieces(forge::Black, forge::Bishop));
    if ((board.pieces(forge::Pawn) | board.pieces(forge::Rook) | board.pieces(forge::Queen)) != 0) return false;
    if (wn == 1 && wb == 1 && bn == 0 && bb == 0) {
        strong = forge::White;
        return true;
    }
    if (bn == 1 && bb == 1 && wn == 0 && wb == 0) {
        strong = forge::Black;
        return true;
    }
    return false;
}

bool mate_within_50(const std::string& fen, int index) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        fail("position " + std::to_string(index) + " fen rejected " + fen);
        return false;
    }
    forge::Color strong = forge::White;
    if (!is_kbnk(board, strong)) {
        fail("position " + std::to_string(index) + " is not KBNK " + fen);
        return false;
    }
    int score = 0;
    if (!forge::dead_material_score(board, score) || score == 0) {
        fail("position " + std::to_string(index) + " missing KBN score");
        return false;
    }
    if ((board.side_to_move() == strong && score < 588) || (board.side_to_move() != strong && score > -588)) {
        fail("position " + std::to_string(index) + " score " + std::to_string(score) + " below bishop+knight");
        return false;
    }
    const bool verbose = std::getenv("KBNK_VERBOSE") != nullptr;
    std::cout << "start " << index << " " << fen << std::endl;
    forge::Searcher searcher(16);
    std::string played;
    for (int ply = 0; ply <= 100; ++ply) {
        const forge::MoveList legal = board.legal_moves();
        if (legal.empty()) {
            if (board.in_check() && board.side_to_move() != strong) {
                std::cout << "mate " << index << " plies " << ply << " " << fen << '\n';
                return true;
            }
            fail("position " + std::to_string(index) + " ended without mating the lone king " + played);
            return false;
        }
        if (ply == 100) {
            fail("position " + std::to_string(index) + " no mate within 50 moves " + board.fen() + " " + played);
            return false;
        }
        forge::Color now_strong = forge::White;
        if (!is_kbnk(board, now_strong) || now_strong != strong) {
            fail("position " + std::to_string(index) + " lost KBN material");
            return false;
        }
        forge::SearchLimits limits;
        limits.nodes = 200000;
        limits.nodes_specified = true;
        limits.depth = 64;
        searcher.clear();
        const forge::SearchInfo info = searcher.search(board, limits, false);
        if (info.best_move.is_none()) {
            fail("position " + std::to_string(index) + " empty move");
            return false;
        }
        bool found = false;
        for (const forge::Move move : legal) {
            if (move == info.best_move) found = true;
        }
        if (!found) {
            fail("position " + std::to_string(index) + " illegal " + forge::Board::move_to_uci(info.best_move));
            return false;
        }
        forge::Undo undo;
        if (!board.make_move(info.best_move, undo)) {
            fail("position " + std::to_string(index) + " make failed");
            return false;
        }
        if (!played.empty()) played += ' ';
        played += forge::Board::move_to_uci(info.best_move);
        if (verbose) std::cout << "  " << ply << " " << forge::Board::move_to_uci(info.best_move) << " " << board.fen() << std::endl;
    }
    fail("position " + std::to_string(index) + " loop ended");
    return false;
}

}  // namespace

int main() {
    forge::dead_material_enabled = true;
    const std::vector<std::string> base = make_positions();
    if (base.size() != 20) {
        fail("expected 20 positions");
        return 1;
    }
    int index = 0;
    for (const std::string& fen : base) {
        mate_within_50(fen, index++);
        const std::string flipped = swap_colors(fen);
        if (flipped == fen) fail("color swap did nothing");
        mate_within_50(flipped, index++);
    }
    if (index != 40) fail("did not run both sides");
    std::cout << "kbnk mate failures " << g_failures << " games " << index << '\n';
    return g_failures == 0 ? 0 : 1;
}
