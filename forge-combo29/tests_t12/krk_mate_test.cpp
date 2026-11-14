// Two-thread KRK mate probe. Builds legal king-and-rook vs king positions whose
// Threads 1 depth-14 search returns a mate score, then searches each one
// repeatedly with more than one thread and a fresh hash. A run is a miss when
// the score is not a mate or the move does not force mate.
#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <cstdlib>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

namespace {

int chebyshev(int a, int b) {
    const int df = std::abs((a & 7) - (b & 7));
    const int dr = std::abs((a >> 3) - (b >> 3));
    return std::max(df, dr);
}

std::string krk_fen(int white_king, int black_king, int white_rook) {
    std::array<char, 64> squares{};
    squares[static_cast<std::size_t>(white_king)] = 'K';
    squares[static_cast<std::size_t>(black_king)] = 'k';
    squares[static_cast<std::size_t>(white_rook)] = 'R';
    std::string fen;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const char piece = squares[static_cast<std::size_t>(rank * 8 + file)];
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
    fen += " w - - 0 1";
    return fen;
}

bool rook_attacks(int rook, int target, int white_king) {
    if ((rook & 7) != (target & 7) && (rook >> 3) != (target >> 3)) return false;
    const int step = (rook & 7) == (target & 7)
                         ? ((target > rook) ? 8 : -8)
                         : ((target > rook) ? 1 : -1);
    for (int square = rook + step; square != target; square += step) {
        if (square == white_king) return false;
    }
    return true;
}

std::vector<std::string> candidate_positions() {
    std::vector<std::string> fens;
    // Kings one square apart from the edge, rook not yet delivering mate. These
    // still mate inside depth 14, but the proof is long enough to use the table.
    for (int black_king = 0; black_king < 64; ++black_king) {
        const int bfile = black_king & 7;
        const int brank = black_king >> 3;
        if (bfile == 0 || bfile == 7 || brank == 0 || brank == 7) continue;
        if (bfile > 3 || brank > 3) continue;
        for (int white_king = 0; white_king < 64; ++white_king) {
            const int kings = chebyshev(white_king, black_king);
            if (kings < 2 || kings > 3) continue;
            for (int rook = 0; rook < 64; ++rook) {
                if (rook == white_king || rook == black_king) continue;
                if (chebyshev(rook, white_king) < 1) continue;
                if (chebyshev(rook, black_king) == 1 && chebyshev(rook, white_king) != 1) continue;
                if (rook_attacks(rook, black_king, white_king)) continue;
                if (chebyshev(white_king, black_king) == 1) continue;
                fens.push_back(krk_fen(white_king, black_king, rook));
            }
        }
    }
    return fens;
}

struct Outcome {
    bool ok = false;
    int score = 0;
    std::string move;
};

std::string score_text(int score) {
    if (forge::is_mate_score(score)) {
        const int distance = forge::MateValue - std::abs(score);
        const int mate = (distance + 1) / 2;
        return "mate " + std::to_string(score > 0 ? mate : -mate);
    }
    return "cp " + std::to_string(score);
}

Outcome search_fen(forge::Searcher& searcher, const std::string& fen, int depth) {
    Outcome outcome;
    forge::Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) {
        std::cout << "invalid fen " << fen << " " << error << "\n";
        return outcome;
    }
    forge::SearchLimits limits;
    limits.depth = depth;
    const forge::SearchInfo info = searcher.search(board, limits, false);
    outcome.ok = true;
    outcome.score = info.score;
    outcome.move = forge::Board::move_to_uci(info.best_move);
    return outcome;
}

bool positive_mate(const Outcome& outcome) {
    return outcome.ok && forge::is_mate_score(outcome.score) && outcome.score > 0 && !outcome.move.empty() &&
           outcome.move != "0000";
}

// The move forces mate when it is immediate checkmate, or when a fresh
// single-thread search of the reply proves a mating score for the defender.
bool move_forces_mate(const std::string& fen, const std::string& uci, int claimed_score) {
    if (!forge::is_mate_score(claimed_score) || claimed_score <= 0) return false;
    forge::Board board;
    if (!board.set_fen(fen)) return false;
    const std::optional<forge::Move> parsed = board.parse_uci(uci);
    if (!parsed.has_value()) return false;
    bool legal = false;
    const forge::MoveList moves = board.legal_moves();
    for (const forge::Move& move : moves) {
        if (move == *parsed) legal = true;
    }
    if (!legal) return false;
    forge::Undo undo;
    (void)board.make_move(*parsed, undo);
    if (!board.has_legal_move()) return board.in_check();
    // Reductions hide a mate that is still inside the depth-14 proof, so the
    // reply is searched past that limit before the move is called non-mating.
    forge::Searcher checker(16, 1);
    checker.clear();
    forge::SearchLimits limits;
    limits.depth = 18;
    const forge::SearchInfo info = checker.search(board, limits, false);
    return forge::is_mate_score(info.score) && info.score < 0;
}

} // namespace

int main(int argc, char** argv) {
    const int threads = argc > 1 ? std::max(2, std::atoi(argv[1])) : 2;
    const int hash_mb = argc > 2 ? std::max(1, std::atoi(argv[2])) : 16;
    const int runs = argc > 3 ? std::max(1, std::atoi(argv[3])) : 10;
    const int target = argc > 4 ? std::max(40, std::atoi(argv[4])) : 40;
    const int depth = 14;

    std::cout << "settings threads " << threads << " hash_mb " << hash_mb << " runs " << runs
              << " target " << target << " depth " << depth << "\n";

    const std::vector<std::string> candidates = candidate_positions();
    std::cout << "candidates " << candidates.size() << "\n";

    forge::Searcher one(hash_mb, 1);
    std::vector<std::string> mates;
    mates.reserve(static_cast<std::size_t>(target));
    int examined = 0;
    for (const std::string& fen : candidates) {
        if (static_cast<int>(mates.size()) >= target) break;
        ++examined;
        if (examined % 25 == 0) {
            std::cout << "progress examined " << examined << " mates " << mates.size() << "\n" << std::flush;
        }
        one.clear();
        const Outcome result = search_fen(one, fen, depth);
        if (!positive_mate(result)) continue;
        if (!move_forces_mate(fen, result.move, result.score)) continue;
        mates.push_back(fen);
        std::cout << "t1 " << fen << " " << score_text(result.score) << " " << result.move << "\n";
    }
    std::cout << "examined " << examined << "\n";
    std::cout << "t1_mates " << mates.size() << "\n";
    if (static_cast<int>(mates.size()) < target) {
        std::cout << "not enough mate positions\n";
        return 2;
    }

    forge::Searcher many(static_cast<std::size_t>(hash_mb), threads);
    int misses = 0;
    int runs_done = 0;
    int score_misses = 0;
    int move_misses = 0;
    for (const std::string& fen : mates) {
        for (int run = 0; run < runs; ++run) {
            many.clear_hash();
            const Outcome result = search_fen(many, fen, depth);
            ++runs_done;
            bool miss = !positive_mate(result);
            bool move_miss = false;
            if (!miss) {
                move_miss = !move_forces_mate(fen, result.move, result.score);
                miss = move_miss;
            }
            if (!miss) continue;
            ++misses;
            if (move_miss) ++move_misses;
            else ++score_misses;
            if (misses <= 12) {
                std::cout << "miss " << fen << " run " << run << " " << score_text(result.score) << " " << result.move
                          << (move_miss ? " non-mating-move" : " no-mate-score") << "\n";
            }
        }
    }
    std::cout << "runs " << runs_done << "\n";
    std::cout << "misses " << misses << "\n";
    std::cout << "score_misses " << score_misses << "\n";
    std::cout << "move_misses " << move_misses << "\n";
    return 0;
}
