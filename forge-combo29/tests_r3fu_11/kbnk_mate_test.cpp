#include "forge/eval.hpp"
#include "forge/search.hpp"

#include <array>
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

int file_of_sq(int square) { return square & 7; }
int rank_of_sq(int square) { return square >> 3; }

bool knight_attacks(int from, int to) {
    const int df = file_of_sq(from) - file_of_sq(to);
    const int dr = rank_of_sq(from) - rank_of_sq(to);
    const int adf = df < 0 ? -df : df;
    const int adr = dr < 0 ? -dr : dr;
    return (adf == 1 && adr == 2) || (adf == 2 && adr == 1);
}

std::string fen_from_squares(int strong_king, int lone_king, int bishop, int knight, bool strong_white) {
    std::array<char, 64> board{};
    board.fill(0);
    if (strong_white) {
        board[static_cast<std::size_t>(strong_king)] = 'K';
        board[static_cast<std::size_t>(lone_king)] = 'k';
        board[static_cast<std::size_t>(bishop)] = 'B';
        board[static_cast<std::size_t>(knight)] = 'N';
    } else {
        board[static_cast<std::size_t>(strong_king)] = 'k';
        board[static_cast<std::size_t>(lone_king)] = 'K';
        board[static_cast<std::size_t>(bishop)] = 'b';
        board[static_cast<std::size_t>(knight)] = 'n';
    }
    std::string fen;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const char piece = board[static_cast<std::size_t>(rank * 8 + file)];
            if (piece == 0) {
                ++empty;
                continue;
            }
            if (empty != 0) {
                fen += static_cast<char>('0' + empty);
                empty = 0;
            }
            fen += piece;
        }
        if (empty != 0) fen += static_cast<char>('0' + empty);
        if (rank != 0) fen += '/';
    }
    fen += strong_white ? " w - - 0 1" : " b - - 0 1";
    return fen;
}

bool piece_safe(int lone_king, int piece) {
    if (forge::square_distance(lone_king, piece) <= 1) return false;
    return !knight_attacks(lone_king, piece);
}

std::vector<std::string> make_positions() {
    std::vector<std::string> fens;
    std::uint64_t rng = 0x4B424E4BULL;
    auto next = [&]() {
        rng = rng * 6364136223846793005ULL + 1442695040888963407ULL;
        return rng;
    };
    while (fens.size() < 20) {
        const int strong_king = static_cast<int>(next() % 64U);
        const int lone_king = static_cast<int>(next() % 64U);
        const int bishop = static_cast<int>(next() % 64U);
        const int knight = static_cast<int>(next() % 64U);
        if (strong_king == lone_king || strong_king == bishop || strong_king == knight ||
            lone_king == bishop || lone_king == knight || bishop == knight) {
            continue;
        }
        if (forge::square_distance(strong_king, lone_king) < 2) continue;
        if (!piece_safe(lone_king, bishop) || !piece_safe(lone_king, knight)) continue;
        const bool strong_white = (fens.size() % 2U) == 0U;
        const std::string fen = fen_from_squares(strong_king, lone_king, bishop, knight, strong_white);
        forge::Board board;
        if (!board.set_fen(fen)) continue;
        if (board.in_check()) continue;
        if (board.legal_moves().empty()) continue;
        bool repeat = false;
        for (const std::string& earlier : fens) {
            if (earlier == fen) repeat = true;
        }
        if (repeat) continue;
        fens.push_back(fen);
    }
    return fens;
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

int main(int argc, char** argv) {
    forge::dead_material_enabled = true;
    const int game_limit = argc > 1 ? std::atoi(argv[1]) : 40;
    const std::vector<std::string> base = make_positions();
    if (base.size() != 20) {
        fail("expected 20 positions");
        return 1;
    }
    int index = 0;
    for (const std::string& fen : base) {
        if (index >= game_limit) break;
        mate_within_50(fen, index++);
        if (index >= game_limit) break;
        const std::string flipped = swap_colors(fen);
        if (flipped == fen) fail("color swap did nothing");
        mate_within_50(flipped, index++);
    }
    if (game_limit >= 40 && index != 40) fail("did not run both sides");
    std::cout << "kbnk mate failures " << g_failures << " games " << index << '\n';
    return g_failures == 0 ? 0 : 1;
}
