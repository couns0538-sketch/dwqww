#include "forge/board.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <charconv>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

// Exact retrograde tablebase for White King + White Rook vs Black King.
// State index: ((wk * 64 + wr) * 64 + bk) * 2 + stm, where stm = 0 (White), 1 (Black).
class KrkTablebase {
public:
    static constexpr std::size_t TotalStates = 64U * 64U * 64U * 2U;

    KrkTablebase() : dtm_(TotalStates, -1), legal_(TotalStates, 0) {
        forge::attacks::init();
        build();
    }

    [[nodiscard]] int dtm(int wk, int wr, int bk, int stm) const {
        return dtm_[index(wk, wr, bk, stm)];
    }

    [[nodiscard]] bool is_legal_state(int wk, int wr, int bk, int stm) const {
        return legal_[index(wk, wr, bk, stm)] != 0;
    }

    // Evaluates a White-to-move KRK move from (wk, wr, bk).
    // Returns exact distance-to-mate in plies from the root (>= 1) if the move
    // forces mate, or -1 if the move allows a draw (stalemate or rook loss).
    [[nodiscard]] int move_mate_plies(const forge::Board& root, const forge::Move& move) const {
        if (move.is_none() || !root.is_legal(move)) return -1;
        forge::Board next = root;
        forge::Undo undo;
        if (!next.make_move(move, undo)) return -1;
        if (!next.has_legal_move()) {
            return next.in_check() ? 1 : -1;
        }
        if (next.is_insufficient_material()) return -1;
        const forge::Bitboard wr_bb = next.pieces(forge::White, forge::Rook);
        if (wr_bb == 0) return -1;
        const int wk = next.king_square(forge::White);
        const int bk = next.king_square(forge::Black);
        const int wr = forge::lsb(wr_bb);
        const int child_dtm = dtm(wk, wr, bk, 1);
        if (child_dtm < 0) return -1;
        return 1 + child_dtm;
    }

private:
    std::vector<std::int16_t> dtm_;
    std::vector<std::uint8_t> legal_;

    [[nodiscard]] static constexpr std::size_t index(int wk, int wr, int bk, int stm) {
        return ((static_cast<std::size_t>(wk) * 64U + static_cast<std::size_t>(wr)) * 64U +
                static_cast<std::size_t>(bk)) * 2U + static_cast<std::size_t>(stm);
    }

    [[nodiscard]] static bool rook_attacks_bk(int wk, int wr, int bk) {
        return (forge::attacks::rook(wr, forge::square_bb(wk)) & forge::square_bb(bk)) != 0;
    }

    void build() {
        for (int wk = 0; wk < 64; ++wk) {
            for (int wr = 0; wr < 64; ++wr) {
                if (wr == wk) continue;
                for (int bk = 0; bk < 64; ++bk) {
                    if (bk == wk || bk == wr) continue;
                    if (forge::square_distance(wk, bk) <= 1) continue;
                    const bool bk_checked = rook_attacks_bk(wk, wr, bk);
                    if (!bk_checked) {
                        legal_[index(wk, wr, bk, 0)] = 1;
                    }
                    legal_[index(wk, wr, bk, 1)] = 1;
                }
            }
        }

        // Terminal checkmates (stm == 1, in check, no legal king move or rook capture).
        for (int wk = 0; wk < 64; ++wk) {
            for (int wr = 0; wr < 64; ++wr) {
                for (int bk = 0; bk < 64; ++bk) {
                    const std::size_t idx = index(wk, wr, bk, 1);
                    if (!legal_[idx]) continue;
                    if (!rook_attacks_bk(wk, wr, bk)) continue;
                    bool has_escape = false;
                    forge::Bitboard moves = forge::attacks::king(bk);
                    while (moves != 0) {
                        const int nbk = forge::pop_lsb(moves);
                        if (forge::square_distance(wk, nbk) <= 1) continue;
                        if (nbk == wr) {
                            has_escape = true;
                            break;
                        }
                        if (!rook_attacks_bk(wk, wr, nbk)) {
                            has_escape = true;
                            break;
                        }
                    }
                    if (!has_escape) dtm_[idx] = 0;
                }
            }
        }

        for (int ply = 1; ply <= 64; ++ply) {
            bool changed = false;
            if ((ply & 1) == 1) {
                // White to move: wins in `ply` if any legal move reaches a Black state with dtm == ply - 1.
                for (int wk = 0; wk < 64; ++wk) {
                    for (int wr = 0; wr < 64; ++wr) {
                        for (int bk = 0; bk < 64; ++bk) {
                            const std::size_t idx = index(wk, wr, bk, 0);
                            if (!legal_[idx] || dtm_[idx] >= 0) continue;
                            bool found = false;
                            forge::Bitboard kmoves = forge::attacks::king(wk);
                            while (kmoves != 0) {
                                const int nwk = forge::pop_lsb(kmoves);
                                if (nwk == wr || forge::square_distance(nwk, bk) <= 1) continue;
                                if (dtm_[index(nwk, wr, bk, 1)] == ply - 1) {
                                    found = true;
                                    break;
                                }
                            }
                            if (!found) {
                                const forge::Bitboard occ = forge::square_bb(wk) | forge::square_bb(bk);
                                forge::Bitboard rmoves = forge::attacks::rook(wr, occ);
                                while (rmoves != 0) {
                                    const int nwr = forge::pop_lsb(rmoves);
                                    if (nwr == wk || nwr == bk) continue;
                                    if (dtm_[index(wk, nwr, bk, 1)] == ply - 1) {
                                        found = true;
                                        break;
                                    }
                                }
                            }
                            if (found) {
                                dtm_[idx] = static_cast<std::int16_t>(ply);
                                changed = true;
                            }
                        }
                    }
                }
            } else {
                // Black to move: loses in `ply` iff >= 1 legal move, cannot capture undefended rook,
                // and every legal move leads to a solved White state (max dtm == ply - 1).
                for (int wk = 0; wk < 64; ++wk) {
                    for (int wr = 0; wr < 64; ++wr) {
                        for (int bk = 0; bk < 64; ++bk) {
                            const std::size_t idx = index(wk, wr, bk, 1);
                            if (!legal_[idx] || dtm_[idx] >= 0) continue;
                            int legal_count = 0;
                            int worst = -1;
                            bool can_draw = false;
                            forge::Bitboard kmoves = forge::attacks::king(bk);
                            while (kmoves != 0) {
                                const int nbk = forge::pop_lsb(kmoves);
                                if (forge::square_distance(wk, nbk) <= 1) continue;
                                if (nbk == wr) {
                                    can_draw = true;
                                    break;
                                }
                                if (rook_attacks_bk(wk, wr, nbk)) continue;
                                ++legal_count;
                                const int child = dtm_[index(wk, wr, nbk, 0)];
                                if (child < 0) {
                                    can_draw = true;
                                    break;
                                }
                                worst = std::max(worst, child);
                            }
                            if (!can_draw && legal_count > 0 && worst == ply - 1) {
                                dtm_[idx] = static_cast<std::int16_t>(ply);
                                changed = true;
                            }
                        }
                    }
                }
            }
            if (!changed) break;
        }
    }
};

std::string make_krk_fen(int wk, int wr, int bk) {
    std::ostringstream out;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const int sq = rank * 8 + file;
            char piece = 0;
            if (sq == wk) piece = 'K';
            else if (sq == wr) piece = 'R';
            else if (sq == bk) piece = 'k';
            if (piece == 0) {
                ++empty;
            } else {
                if (empty > 0) {
                    out << empty;
                    empty = 0;
                }
                out << piece;
            }
        }
        if (empty > 0) out << empty;
        if (rank > 0) out << '/';
    }
    out << " w - - 0 1";
    return out.str();
}

std::string format_score(int score) {
    if (forge::is_mate_score(score)) {
        const int distance = forge::MateValue - std::abs(score);
        const int mate = (distance + 1) / 2;
        return "mate " + std::to_string(score > 0 ? mate : -mate);
    }
    return "cp " + std::to_string(score);
}

struct SelectedPosition {
    std::string fen;
    int wk = 0;
    int wr = 0;
    int bk = 0;
    int exact_dtm = 0;
    int t1_score = 0;
    forge::Move t1_move{};
};

int parse_arg(const char* text, int fallback) {
    int v = fallback;
    const std::string_view sv(text);
    const auto res = std::from_chars(sv.data(), sv.data() + sv.size(), v);
    return (res.ec == std::errc{} && res.ptr == sv.data() + sv.size()) ? v : fallback;
}

} // namespace

int main(int argc, char** argv) {
    const int target_positions = argc > 1 ? std::max(1, parse_arg(argv[1], 40)) : 40;
    const int runs_per_pos = argc > 2 ? std::max(1, parse_arg(argv[2], 10)) : 10;
    const int threads = argc > 3 ? std::clamp(parse_arg(argv[3], 2), 1, 64) : 2;
    const int hash_mb = argc > 4 ? std::clamp(parse_arg(argv[4], 16), 1, 1024) : 16;
    const int depth = argc > 5 ? std::clamp(parse_arg(argv[5], 14), 1, 64) : 14;
    const bool clear_all = argc > 6 ? (parse_arg(argv[6], 1) != 0) : true;

    const KrkTablebase tb;

    // Deterministically sample legal KRK positions across non-trivial mate distances
    // (preferring deeper forced mates within depth 14 so multi-threaded search does
    // real concurrent work, falling back to shorter mates if needed).
    struct Candidate {
        int wk;
        int wr;
        int bk;
        int dtm;
        std::uint64_t order_hash;
    };

    std::vector<SelectedPosition> positions;
    positions.reserve(static_cast<std::size_t>(target_positions));

    forge::Searcher single_searcher(static_cast<std::size_t>(hash_mb), 1);
    forge::SearchLimits limits;
    limits.depth = depth;

    // Target plies: 13 (mate in 7), 11 (mate in 6), 9 (mate in 5), 7 (mate in 4), 5 (mate in 3).
    const int target_dtms[] = {13, 11, 9, 7, 5};
    for (const int target_dtm : target_dtms) {
        if (static_cast<int>(positions.size()) >= target_positions) break;
        std::vector<Candidate> bucket;
        for (int wk = 0; wk < 64; ++wk) {
            for (int wr = 0; wr < 64; ++wr) {
                for (int bk = 0; bk < 64; ++bk) {
                    if (!tb.is_legal_state(wk, wr, bk, 0)) continue;
                    if (tb.dtm(wk, wr, bk, 0) != target_dtm) continue;
                    std::uint64_t h = static_cast<std::uint64_t>(wk * 4096 + wr * 64 + bk + 1);
                    h ^= h >> 30U;
                    h *= 0xbf58476d1ce4e5b9ULL;
                    h ^= h >> 27U;
                    h *= 0x94d049bb133111ebULL;
                    h ^= h >> 31U;
                    bucket.push_back(Candidate{wk, wr, bk, target_dtm, h});
                }
            }
        }
        std::sort(bucket.begin(), bucket.end(), [](const Candidate& a, const Candidate& b) {
            return a.order_hash < b.order_hash;
        });

        // Take a balanced slice per mate distance, verifying each with Threads 1 depth 14.
        const int quota = (target_dtm >= 7)
            ? std::max(10, target_positions / 4)
            : target_positions;
        int added_for_dtm = 0;
        for (const Candidate& cand : bucket) {
            if (static_cast<int>(positions.size()) >= target_positions) break;
            if (added_for_dtm >= quota) break;
            const std::string fen = make_krk_fen(cand.wk, cand.wr, cand.bk);
            forge::Board board;
            std::string err;
            if (!board.set_fen(fen, &err)) continue;

            single_searcher.clear();
            const forge::SearchInfo info = single_searcher.search(board, limits, false);
            if (info.score < forge::MateInMaxPly) continue;
            const int move_plies = tb.move_mate_plies(board, info.best_move);
            const int claimed_plies = forge::MateValue - info.score;
            if (move_plies < 0 || move_plies > claimed_plies) continue;

            positions.push_back(SelectedPosition{
                fen, cand.wk, cand.wr, cand.bk, cand.dtm, info.score, info.best_move
            });
            ++added_for_dtm;
        }
    }

    std::cout << "config positions=" << positions.size()
              << " runs_per_pos=" << runs_per_pos
              << " threads=" << threads
              << " hash_mb=" << hash_mb
              << " depth=" << depth
              << " use_nnue=" << (forge::nnue::enabled ? "true" : "false") << "\n";

    if (static_cast<int>(positions.size()) < target_positions) {
        std::cout << "ERROR: only found " << positions.size() << " positions with Threads 1 mate score\n";
        return 2;
    }

    // Verify Threads 1 stability across 100 runs (first 10 positions x 10 runs or all x 2+)
    // and run the main multi-threaded test (positions x runs_per_pos, fresh hash each time).
    int t1_misses = 0;
    const int t1_check_runs = 100;
    for (int r = 0; r < t1_check_runs; ++r) {
        const SelectedPosition& pos = positions[static_cast<std::size_t>(r) % positions.size()];
        forge::Board board;
        (void)board.set_fen(pos.fen);
        if (clear_all) single_searcher.clear();
        else single_searcher.clear_hash();
        const forge::SearchInfo info = single_searcher.search(board, limits, false);
        const bool mate_score = info.score >= forge::MateInMaxPly;
        const int move_plies = tb.move_mate_plies(board, info.best_move);
        const int claimed_plies = mate_score ? (forge::MateValue - info.score) : -1;
        const bool mating_move = move_plies > 0 && (!mate_score || move_plies <= std::max(pos.exact_dtm + 2, claimed_plies)) && move_plies <= depth * 2;
        if (!mate_score || !mating_move) ++t1_misses;
    }
    std::cout << "threads_1_check: " << t1_misses << " / " << t1_check_runs << " misses\n";

    forge::Searcher mt_searcher(static_cast<std::size_t>(hash_mb), threads);
    int total_runs = 0;
    int total_misses = 0;
    int no_mate_score_count = 0;
    int non_mating_move_count = 0;
    int logged_examples = 0;

    for (std::size_t idx = 0; idx < positions.size(); ++idx) {
        const SelectedPosition& pos = positions[idx];
        int pos_misses = 0;
        for (int run = 0; run < runs_per_pos; ++run) {
            forge::Board board;
            (void)board.set_fen(pos.fen);
            if (clear_all) mt_searcher.clear();
            else mt_searcher.clear_hash();
            const forge::SearchInfo info = mt_searcher.search(board, limits, false);
            ++total_runs;

            const bool has_mate_score = info.score >= forge::MateInMaxPly;
            const int move_plies = tb.move_mate_plies(board, info.best_move);
            const int claimed_plies = has_mate_score ? (forge::MateValue - info.score) : -1;
            // A move is non-mating if it is illegal/draws (move_plies < 0), or fails to force mate
            // within the claimed mate bound (when a mate score is reported) or within depth plies.
            const bool is_mating_move = move_plies > 0 &&
                (has_mate_score ? (move_plies <= claimed_plies) : (move_plies <= depth));

            if (!has_mate_score || !is_mating_move) {
                ++total_misses;
                ++pos_misses;
                if (!has_mate_score) ++no_mate_score_count;
                if (!is_mating_move) ++non_mating_move_count;
                if (logged_examples < 12) {
                    ++logged_examples;
                    std::cout << "  MISS pos=" << idx << " run=" << run
                              << " fen=\"" << pos.fen << "\""
                              << " exact_dtm=" << pos.exact_dtm
                              << " t1=" << format_score(pos.t1_score) << "/" << forge::Board::move_to_uci(pos.t1_move)
                              << " got=" << format_score(info.score) << "/" << forge::Board::move_to_uci(info.best_move)
                              << " move_dtm=" << move_plies << "\n";
                }
            }
        }
        if (pos_misses > 0) {
            std::cout << "pos " << idx << " (" << pos.fen << ", dtm=" << pos.exact_dtm << " plies): "
                      << pos_misses << "/" << runs_per_pos << " misses\n";
        }
    }

    std::cout << "SUMMARY: misses=" << total_misses << " / " << total_runs
              << " (no_mate_score=" << no_mate_score_count
              << ", non_mating_move=" << non_mating_move_count << ")\n";
    return total_misses == 0 ? 0 : 1;
}
