#include "forge/search.hpp"
#include "forge/uci_output.hpp"

#include <algorithm>
#include <bit>
#include <cmath>
#include <iostream>
#include <limits>

namespace forge {
namespace {

constexpr int Infinity = 32000;
constexpr int MateScore = 30000;
constexpr std::array<int, 7> PieceValue{0, 100, 320, 330, 500, 900, 0};
constexpr std::array<int, 7> MgValue{0, 82, 337, 365, 477, 1025, 0};
constexpr std::array<int, 7> EgValue{0, 94, 281, 297, 512, 936, 0};
constexpr std::array<int, 7> PhaseWeight{0, 0, 1, 1, 2, 4, 0};
constexpr std::array<int, 8> PassedMg{0, 5, 10, 20, 35, 60, 100, 0};
constexpr std::array<int, 8> PassedEg{0, 10, 20, 35, 60, 100, 160, 0};
constexpr int MaxPhase = 24;
constexpr int abs_int(int value) { return value < 0 ? -value : value; }

int normalized_score_for_tt(int score, int ply) {
    if (score > MateScore - 128) return score + ply;
    if (score < -MateScore + 128) return score - ply;
    return score;
}

int score_from_tt(int score, int ply) {
    if (score > MateScore - 128) return score - ply;
    if (score < -MateScore + 128) return score + ply;
    return score;
}

bool same_move(const Move& a, const Move& b) {
    return a.from == b.from && a.to == b.to && a.promotion == b.promotion;
}

bool has_non_pawn_material(const Board& board, Color color) {
    if (color == White) return (board.pieces(WN) | board.pieces(WB) | board.pieces(WR) | board.pieces(WQ)) != 0;
    return (board.pieces(BN) | board.pieces(BB) | board.pieces(BR) | board.pieces(BQ)) != 0;
}

constexpr std::array<std::uint64_t, 64> make_knight_attacks() {
    std::array<std::uint64_t, 64> attacks{};
    constexpr std::array<int, 8> offsets{17, 15, 10, 6, -6, -10, -15, -17};
    for (int square = 0; square < 64; ++square) {
        const int file = square & 7;
        for (const int offset : offsets) {
            const int target = square + offset;
            if (target < 0 || target >= 64 || abs_int((target & 7) - file) > 2) continue;
            attacks[static_cast<std::size_t>(square)] |= 1ULL << target;
        }
    }
    return attacks;
}

constexpr auto KnightAttacks = make_knight_attacks();

constexpr std::array<int, 8> RayDirections{9, 7, -7, -9, 8, -8, 1, -1};

constexpr std::array<std::array<std::uint64_t, 8>, 64> make_ray_attacks() {
    std::array<std::array<std::uint64_t, 8>, 64> attacks{};
    for (int square = 0; square < 64; ++square) {
        for (std::size_t direction = 0; direction < RayDirections.size(); ++direction) {
            int from = square;
            while (true) {
                const int target = from + RayDirections[direction];
                if (target < 0 || target >= 64 || abs_int((target & 7) - (from & 7)) > 1) break;
                attacks[static_cast<std::size_t>(square)][direction] |= 1ULL << target;
                from = target;
            }
        }
    }
    return attacks;
}

constexpr auto RayAttacks = make_ray_attacks();

} // namespace

Searcher::Searcher(std::size_t hash_mb) {
    resize_hash(hash_mb);
    eval_cache_.resize(EvalCacheSize);
    pawn_cache_.resize(PawnCacheSize);
}

void Searcher::resize_hash(std::size_t hash_mb) {
    const std::size_t bytes = std::max<std::size_t>(1, hash_mb) * 1024U * 1024U;
    table_.assign(std::max<std::size_t>(1, bytes / sizeof(TTEntry)), TTEntry{});
    tt_mask_ = std::has_single_bit(table_.size()) ? table_.size() - 1U : 0U;
}

void Searcher::clear() {
    clear_hash();
    history_ = {};
    killers_ = {};
    countermoves_ = {};
}

void Searcher::clear_hash() {
    std::fill(table_.begin(), table_.end(), TTEntry{});
    std::fill(eval_cache_.begin(), eval_cache_.end(), EvalEntry{});
    std::fill(pawn_cache_.begin(), pawn_cache_.end(), PawnEntry{});
}

int Searcher::hashfull_permille() const {
    const std::size_t sample = std::min<std::size_t>(1000, table_.size());
    if (sample == 0) return 0;
    const auto occupied = std::count_if(table_.begin(), table_.begin() + static_cast<std::ptrdiff_t>(sample),
                                        [](const TTEntry& entry) { return tt_depth(entry) >= 0; });
    return static_cast<int>(occupied * 1000 / static_cast<std::ptrdiff_t>(sample));
}

Searcher::PawnEntry Searcher::analyze_pawns(const Board& board) {
    PawnEntry result;
    result.key = board.pawn_key();
    result.valid = true;
    result.white_min_rank.fill(8);
    result.black_max_rank.fill(-1);
    auto add = [&](Color color, int mg, int eg) {
        const int sign = color == White ? 1 : -1;
        result.mg += sign * mg;
        result.eg += sign * eg;
    };

    std::uint64_t pawns = board.pieces(WP) | board.pieces(BP);
    while (pawns != 0) {
        const int square = static_cast<int>(std::countr_zero(pawns));
        pawns &= pawns - 1;
        const Piece piece = board.piece_at(square);
        const Color color = piece == WP ? White : Black;
        const int file = square & 7;
        const int rank = square >> 3;
        const int relative_rank = color == White ? rank : 7 - rank;
        const int center = 14 - (std::abs(file * 2 - 7) + std::abs(rank * 2 - 7));
        add(color, MgValue[1] + relative_rank * 6 + center, EgValue[1] + relative_rank * 10);
        ++result.by_file[static_cast<std::size_t>(color)][static_cast<std::size_t>(file)];
        if (color == White) result.white_min_rank[static_cast<std::size_t>(file)] =
            std::min(result.white_min_rank[static_cast<std::size_t>(file)], rank);
        else result.black_max_rank[static_cast<std::size_t>(file)] =
            std::max(result.black_max_rank[static_cast<std::size_t>(file)], rank);
    }
    for (int color_index = 0; color_index < 2; ++color_index) {
        const Color color = static_cast<Color>(color_index);
        for (int file = 0; file < 8; ++file) {
            const int count = result.by_file[static_cast<std::size_t>(color)][static_cast<std::size_t>(file)];
            if (count > 1) add(color, -14 * (count - 1), -20 * (count - 1));
        }
    }
    pawns = board.pieces(WP) | board.pieces(BP);
    while (pawns != 0) {
        const int square = static_cast<int>(std::countr_zero(pawns));
        pawns &= pawns - 1;
        const Color color = board.piece_at(square) == WP ? White : Black;
        const int file = square & 7;
        const int rank = square >> 3;
        const int relative_rank = color == White ? rank : 7 - rank;
        const auto& own_files = result.by_file[static_cast<std::size_t>(color)];
        const bool left_empty = file == 0 || own_files[static_cast<std::size_t>(file - 1)] == 0;
        const bool right_empty = file == 7 || own_files[static_cast<std::size_t>(file + 1)] == 0;
        if (left_empty && right_empty) add(color, -12, -16);
        bool passed = true;
        for (int adjacent = std::max(0, file - 1); adjacent <= std::min(7, file + 1); ++adjacent) {
            if (color == White && result.black_max_rank[static_cast<std::size_t>(adjacent)] > rank) passed = false;
            if (color == Black && result.white_min_rank[static_cast<std::size_t>(adjacent)] < rank) passed = false;
        }
        if (passed) add(color, PassedMg[static_cast<std::size_t>(relative_rank)],
                        PassedEg[static_cast<std::size_t>(relative_rank)]);
    }
    return result;
}

int Searcher::evaluate(const Board& board) {
    return evaluate_with_pawns(board, analyze_pawns(board));
}

int Searcher::evaluate_with_pawns(const Board& board, const PawnEntry& pawns) {
    const auto& pawns_by_file = pawns.by_file;
    std::array<int, 2> bishops{};
    std::array<int, 2> king_square{-1, -1};
    int mg_score = pawns.mg;
    int eg_score = pawns.eg;
    int phase = 0;

    auto add = [&](Color color, int mg, int eg) {
        const int sign = color == White ? 1 : -1;
        mg_score += sign * mg;
        eg_score += sign * eg;
    };
    const std::uint64_t white_occupied = board.occupied(White);
    const std::uint64_t black_occupied = board.occupied(Black);
    auto mobility = [&](int square, Color color, int type) {
        const std::uint64_t own = color == White ? white_occupied : black_occupied;
        if (type == 2) {
            return std::popcount(KnightAttacks[static_cast<std::size_t>(square)] & ~own);
        }
        const std::uint64_t all_occupied = white_occupied | black_occupied;
        int count = 0;
        const int begin = type == 3 ? 0 : (type == 4 ? 4 : 0);
        const int end = type == 3 ? 4 : 8;
        for (int index = begin; index < end; ++index) {
            std::uint64_t ray = RayAttacks[static_cast<std::size_t>(square)]
                                         [static_cast<std::size_t>(index)];
            const std::uint64_t blockers = ray & all_occupied;
            if (blockers != 0) {
                const int blocker_square = RayDirections[static_cast<std::size_t>(index)] > 0
                    ? static_cast<int>(std::countr_zero(blockers))
                    : 63 - static_cast<int>(std::countl_zero(blockers));
                ray &= ~RayAttacks[static_cast<std::size_t>(blocker_square)]
                                  [static_cast<std::size_t>(index)];
            }
            count += std::popcount(ray & ~own);
        }
        return count;
    };

    for (int color_index = 0; color_index < 2; ++color_index) {
        const Color color = static_cast<Color>(color_index);
        for (int type = 2; type <= 6; ++type) {
            const Piece piece = static_cast<Piece>((color == White ? 0 : 6) + type);
            std::uint64_t remaining = board.pieces(piece);
            while (remaining != 0) {
                const int square = static_cast<int>(std::countr_zero(remaining));
                remaining &= remaining - 1;
                const int file = square & 7;
                const int rank = square >> 3;
                const int relative_rank = color == White ? rank : 7 - rank;
                const int center = 14 - (std::abs(file * 2 - 7) + std::abs(rank * 2 - 7));
                int mg = MgValue[static_cast<std::size_t>(type)];
                int eg = EgValue[static_cast<std::size_t>(type)];
                if (type == 2) {
                    mg += center * 4;
                    eg += center * 3;
                } else if (type == 3) {
                    mg += center * 3;
                    eg += center * 2;
                    ++bishops[static_cast<std::size_t>(color)];
                } else if (type == 4) {
                    mg += relative_rank * 2;
                    eg += center;
                } else if (type == 5) {
                    mg += center;
                    eg += center * 2;
                } else {
                    mg -= center * 5;
                    eg += center * 5;
                    king_square[static_cast<std::size_t>(color)] = square;
                }
                phase += PhaseWeight[static_cast<std::size_t>(type)];
                add(color, mg, eg);

                if (type <= 5) {
                    const int moves = mobility(square, color, type);
                    const int mg_weight = type == 2 ? 4 : (type == 3 ? 5 : (type == 4 ? 2 : 1));
                    const int eg_weight = type == 2 ? 3 : (type == 3 ? 4 : (type == 4 ? 3 : 2));
                    add(color, moves * mg_weight, moves * eg_weight);
                    if (type == 4 && pawns_by_file[static_cast<std::size_t>(color)][static_cast<std::size_t>(file)] == 0) {
                        const Color enemy = opposite(color);
                        const bool open = pawns_by_file[static_cast<std::size_t>(enemy)][static_cast<std::size_t>(file)] == 0;
                        add(color, open ? 20 : 10, open ? 12 : 6);
                    }
                }
            }
        }
    }

    for (int color_index = 0; color_index < 2; ++color_index) {
        const Color color = static_cast<Color>(color_index);
        if (bishops[static_cast<std::size_t>(color)] >= 2) add(color, 30, 45);

        const int king = king_square[static_cast<std::size_t>(color)];
        if (king >= 0) {
            const int king_file = king & 7;
            const int king_rank = king >> 3;
            const int direction = color == White ? 1 : -1;
            int shelter = 0;
            for (int file = std::max(0, king_file - 1); file <= std::min(7, king_file + 1); ++file) {
                for (int step = 1; step <= 2; ++step) {
                    const int rank = king_rank + direction * step;
                    if (rank < 0 || rank >= 8) continue;
                    const Piece expected = color == White ? WP : BP;
                    if (board.piece_at(rank * 8 + file) == expected) {
                        shelter += step == 1 ? 12 : 6;
                        break;
                    }
                }
            }
            add(color, shelter, 0);
        }
    }

    phase = std::min(phase, MaxPhase);
    int score = (mg_score * phase + eg_score * (MaxPhase - phase)) / MaxPhase;
    score += board.side_to_move() == White ? 10 : -10;
    return board.side_to_move() == White ? score : -score;
}

int Searcher::evaluate_cached(const Board& board) {
    EvalEntry& entry = eval_cache_[eval_index(board.key())];
    if (entry.valid && entry.key == board.key()) return entry.score;
    PawnEntry& pawn_entry = pawn_cache_[pawn_index(board.pawn_key())];
    if (!pawn_entry.valid || pawn_entry.key != board.pawn_key()) pawn_entry = analyze_pawns(board);
    const int score = evaluate_with_pawns(board, pawn_entry);
    entry.key = board.key();
    entry.score = static_cast<std::int16_t>(score);
    entry.valid = true;
    return score;
}

bool Searcher::should_stop() {
    if (stop_.load(std::memory_order_relaxed)) return true;
    if (node_limit_specified_ && nodes_ >= node_limit_) return true;
    if (time_limit_ms_ != 0 && (nodes_ & time_check_mask_) == 0U) {
        auto budget_start = start_;
        if (pondering_) {
            const std::int64_t hit_ns = ponder_hit_ns_.load(std::memory_order_relaxed);
            if (hit_ns == 0) return false; // Opponent's clock is still running.
            budget_start = std::chrono::steady_clock::time_point(
                std::chrono::duration_cast<std::chrono::steady_clock::duration>(
                    std::chrono::nanoseconds(hit_ns)));
        }
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - budget_start).count();
        if (elapsed >= static_cast<long long>(time_limit_ms_)) return true;
    }
    return false;
}

bool Searcher::abort_if_stopped() {
    if (!should_stop()) return false;
    aborted_ = true;
    return true;
}

int Searcher::move_score(const Board& board, const Move& move, const Move& tt_move,
                         const Move& counter_move, int ply) const {
    if (same_move(move, tt_move)) return 2'000'000;
    if ((move.flags & Promotion) != 0U) {
        const int victim = move.is_capture()
            ? ((move.flags & EnPassant) != 0U ? 1 : piece_type(board.piece_at(move.to)))
            : 0;
        return 1'100'000 + PieceValue[move.promotion] + victim * 16;
    }
    if (move.is_capture()) {
        const int victim = (move.flags & EnPassant) != 0U ? 1 : piece_type(board.piece_at(move.to));
        const int attacker = piece_type(board.piece_at(move.from));
        return 1'000'000 + victim * 16 - attacker;
    }
    const std::size_t index = static_cast<std::size_t>(std::min(ply, 127));
    if (same_move(move, killers_[index][0])) return 800'000;
    if (same_move(move, killers_[index][1])) return 700'000;
    if (same_move(move, counter_move)) return 600'000;
    return history_[move.from][move.to];
}

void Searcher::order_moves(const Board& board, MoveList& moves, const Move& tt_move,
                           const Move& counter_move, int ply) const {
    std::array<int, 256> scores;
    if (moves.size() > scores.size()) return;
    for (std::size_t i = 0; i < moves.size(); ++i) {
        scores[i] = move_score(board, moves[i], tt_move, counter_move, ply);
    }
    for (std::size_t i = 1; i < moves.size(); ++i) {
        const Move move = moves[i];
        const int score = scores[i];
        std::size_t j = i;
        while (j > 0 && scores[j - 1] < score) {
            moves[j] = moves[j - 1];
            scores[j] = scores[j - 1];
            --j;
        }
        moves[j] = move;
        scores[j] = score;
    }
}

std::vector<Move> Searcher::extract_pv(Board board, int depth) const {
    std::vector<Move> pv;
    pv.reserve(static_cast<std::size_t>(depth));
    std::vector<std::uint64_t> seen;
    seen.reserve(static_cast<std::size_t>(depth));
    for (int ply = 0; ply < depth; ++ply) {
        if (std::find(seen.begin(), seen.end(), board.key()) != seen.end()) break;
        seen.push_back(board.key());
        const std::uint64_t key = tt_key(board);
        const TTEntry& entry = table_[tt_index(key)];
        if (entry.key != key || entry.move.from == entry.move.to) break;
        const auto legal = board.legal_moves();
        const auto found = std::find_if(legal.begin(), legal.end(), [&](const Move& move) {
            return same_move(move, entry.move);
        });
        if (found == legal.end()) break;
        pv.push_back(*found);
        Undo undo;
        (void)board.make_move(*found, undo);
        if (board.is_repetition() || board.halfmove_clock() >= 100 || board.is_insufficient_material()) break;
    }
    return pv;
}

int Searcher::quiescence(Board& board, int ply, int alpha, int beta, bool null_branch) {
    if (abort_if_stopped()) return 0;
    if (ply >= 127) return evaluate_cached(board);
    seldepth_ = std::max(seldepth_, ply);
    ++nodes_;
    const bool checked = board.in_check(board.side_to_move());
    if (!null_branch && (board.is_repetition() || board.halfmove_clock() >= 100)) {
        if (!checked || board.has_legal_move()) return 0;
        return -MateScore + ply;
    }
    if (!null_branch && board.is_insufficient_material()) return 0;
    alpha = std::max(alpha, -MateScore + ply);
    beta = std::min(beta, MateScore - ply - 1);
    if (alpha >= beta) return alpha;
    const int original_alpha = alpha;
    const std::uint64_t qkey = tt_key(board, null_branch);
    TTEntry& qentry = table_[tt_index(qkey)];
    Move qtt_move{};
    const std::uint8_t qcontext = current_tt_context(board, null_branch);
    if (qentry.key == qkey) {
        qtt_move = qentry.move;
        if (tt_depth(qentry) == 0 && tt_context(qentry) == qcontext) {
            const int tt_score = score_from_tt(qentry.score, ply);
            const Bound bound = tt_bound(qentry);
            if (bound == Exact) return tt_score;
            if (bound == Lower && tt_score >= beta) return tt_score;
            if (bound == Upper && tt_score <= alpha) return tt_score;
        }
    }
    const int stand_pat = evaluate_cached(board);
    if (!checked) {
        if (stand_pat >= beta && beta <= 0) return beta;
    }

    auto moves = board.legal_moves(!checked);
    if (checked && moves.empty()) return -MateScore + ply;
    if (!checked) {
        if (stand_pat >= beta) {
            if (moves.empty() && !board.has_legal_move()) return 0;
            return beta;
        }
        alpha = std::max(alpha, stand_pat);
        if (moves.empty()) {
            // A favorable stalemate can raise alpha from stand-pat even though
            // its exact game-theoretic score is zero.  We only need the more
            // expensive quiet-legal-move probe when zero might change the
            // window result: either the window straddles zero, or stand-pat
            // improved alpha above the caller's original lower bound.
            if ((original_alpha < 0 || alpha > original_alpha) &&
                !board.has_legal_move()) {
                return 0;
            }
            return alpha;
        }
    }
    order_moves(board, moves, qtt_move, Move{}, ply);
    Move best_move{};
    for (const Move move : moves) {
        Undo undo;
        (void)board.make_move(move, undo);
        const int score = -quiescence(board, ply + 1, -beta, -alpha, null_branch);
        board.unmake_move(move, undo);
        if (aborted_) return 0;
        if (score >= beta) {
            if (tt_depth(qentry) <= 0) {
                qentry.key = qkey;
                qentry.move = move;
                qentry.score = static_cast<std::int16_t>(std::clamp(normalized_score_for_tt(beta, ply), -32767, 32767));
                set_tt_meta(qentry, 0, Lower, qcontext);
            }
            return beta;
        }
        if (score > alpha) { alpha = score; best_move = move; }
    }
    if (tt_depth(qentry) <= 0) {
        qentry.key = qkey;
        qentry.move = best_move;
        qentry.score = static_cast<std::int16_t>(std::clamp(normalized_score_for_tt(alpha, ply), -32767, 32767));
        set_tt_meta(qentry, 0, alpha <= original_alpha ? Upper : Exact, qcontext);
    }
    return alpha;
}

int Searcher::alpha_beta(Board& board, int depth, int ply, int alpha, int beta,
                         bool allow_null, bool null_branch, Move previous_move) {
    if (abort_if_stopped()) return 0;
    if (ply >= 127) return evaluate_cached(board);
    seldepth_ = std::max(seldepth_, ply);
    if (depth <= 0) return quiescence(board, ply, alpha, beta, null_branch);
    ++nodes_;
    if (!null_branch && (board.is_repetition() || board.halfmove_clock() >= 100)) {
        if (!board.in_check(board.side_to_move()) || board.has_legal_move()) return 0;
        return -MateScore + ply;
    }
    if (!null_branch && board.is_insufficient_material()) return 0;
    alpha = std::max(alpha, -MateScore + ply);
    beta = std::min(beta, MateScore - ply - 1);
    if (alpha >= beta) return alpha;
    const int original_alpha = alpha;
    const std::uint64_t key = tt_key(board, null_branch);
    TTEntry& entry = table_[tt_index(key)];
    Move tt_move{};
    const std::uint8_t context = current_tt_context(board, null_branch);
    if (entry.key == key) {
        tt_move = entry.move;
        if (ply > 0 && tt_depth(entry) >= depth && tt_context(entry) == context) {
            const int tt_score = score_from_tt(entry.score, ply);
            const Bound bound = tt_bound(entry);
            if (bound == Exact) return tt_score;
            if (bound == Lower && tt_score >= beta) return tt_score;
            if (bound == Upper && tt_score <= alpha) return tt_score;
        }
    }

    const bool checked = board.in_check(board.side_to_move());
    const bool zero_window = beta == alpha + 1;
    int static_eval = 0;
    if (zero_window && !checked && beta > -MateScore + 128 && beta < MateScore - 128) {
        static_eval = evaluate_cached(board);
    }

    auto moves = board.legal_moves();
    // Classify the actual chess position before restricting the root move set.
    if (moves.empty()) return checked ? -MateScore + ply : 0;
    if (ply == 0 && root_restricted_) {
        std::size_t write = 0;
        for (const Move move : moves) {
            const bool allowed = std::any_of(root_moves_.begin(), root_moves_.end(),
                                             [&](const Move& candidate) { return same_move(move, candidate); });
            if (allowed) moves[write++] = move;
        }
        moves.resize(write);
        // An empty searchmoves intersection is a command restriction, not mate.
        if (moves.empty()) return 0;
    }
    // Shallow null probes (depth 3-5) reduce directly to qsearch or one ply and
    // previously produced unverified false lower bounds. Restrict null pruning
    // to depths where Forge already performs a verification search.
    if (allow_null && ply > 0 && zero_window && depth >= 6 && !checked &&
        beta > -MateScore + 128 && beta < MateScore - 128 &&
        has_non_pawn_material(board, board.side_to_move()) && static_eval >= beta) {
        ++null_tries_;
        NullUndo null_undo;
        board.make_null_move(null_undo);
        const int reduction = 2 + depth / 4 + static_cast<int>(static_eval - beta >= 200);
        const int null_depth = std::max(0, depth - 1 - reduction);
        const int null_score = -alpha_beta(board, null_depth, ply + 1,
                                           -beta, -beta + 1, false, true, Move{});
        board.unmake_null_move(null_undo);
        if (aborted_) return 0;
        if (null_score >= beta) {
            const int verification = alpha_beta(board, depth - reduction, ply, alpha, beta,
                                                false, null_branch, previous_move);
            if (aborted_) return 0;
            if (verification >= beta) {
                ++null_cutoffs_;
                return beta;
            }
        }
    }
    const Move counter_move = previous_move.from == previous_move.to
        ? Move{} : countermoves_[previous_move.from][previous_move.to];
    order_moves(board, moves, tt_move, counter_move, ply);
    Move best_move{};
    std::array<Move, 256> quiets_searched;
    std::size_t quiet_count = 0;
    bool first_move = true;
    int moves_searched = 0;
    for (const Move move : moves) {
        Undo undo;
        (void)board.make_move(move, undo);
        const bool late_quiet = zero_window && depth <= 2 && !checked &&
                                moves_searched >= 8 + 4 * depth && !move.is_capture() &&
                                (move.flags & Promotion) == 0U && static_eval + 100 * depth <= alpha;
        if (late_quiet && !board.in_check(board.side_to_move())) {
            board.unmake_move(move, undo);
            ++moves_searched;
            continue;
        }
        int score;
        if (first_move) {
            score = -alpha_beta(board, depth - 1, ply + 1, -beta, -alpha, true, null_branch, move);
        } else {
            // LMR through nominal depth 9 can skip the only move that raises
            // alpha; keep those shallow nodes at full depth.
            const bool reduce = depth >= 10 && moves_searched >= 3 && !checked &&
                                !move.is_capture() && (move.flags & Promotion) == 0U;
            const bool reduce_more = reduce && depth >= 6 && moves_searched >= 12 &&
                                     history_[move.from][move.to] <= 0;
            const int reduced_depth = reduce ? depth - 2 - static_cast<int>(reduce_more) : depth - 1;
            score = -alpha_beta(board, reduced_depth, ply + 1, -alpha - 1, -alpha, true, null_branch, move);
            if (reduce && score > alpha) {
                score = -alpha_beta(board, depth - 1, ply + 1, -alpha - 1, -alpha, true, null_branch, move);
            }
            if (score > alpha && score < beta) {
                score = -alpha_beta(board, depth - 1, ply + 1, -beta, -alpha, true, null_branch, move);
            }
        }
        board.unmake_move(move, undo);
        if (aborted_) return 0;
        if (score > alpha) {
            alpha = score;
            best_move = move;
            if (alpha >= beta) {
                if (!move.is_capture()) {
                    const std::size_t index = static_cast<std::size_t>(ply);
                    if (!same_move(killers_[index][0], move)) {
                        killers_[index][1] = killers_[index][0];
                        killers_[index][0] = move;
                    }
                    int& history = history_[move.from][move.to];
                    const int bonus = depth * depth;
                    history += bonus - history * bonus / 16384;
                    for (std::size_t i = 0; i < quiet_count; ++i) {
                        const Move quiet = quiets_searched[i];
                        int& failed_history = history_[quiet.from][quiet.to];
                        failed_history -= bonus + failed_history * bonus / 16384;
                    }
                    if (previous_move.from != previous_move.to) {
                        countermoves_[previous_move.from][previous_move.to] = move;
                    }
                }
                break;
            }
        }
        if (!move.is_capture() && (move.flags & Promotion) == 0U && quiet_count < quiets_searched.size()) {
            quiets_searched[quiet_count++] = move;
        }
        first_move = false;
        ++moves_searched;
    }

    if (!aborted_ && ply == 0) root_best_move_ = best_move;
    if (!aborted_ && !(ply == 0 && root_restricted_)) {
        entry.key = key;
        entry.move = best_move;
        entry.score = static_cast<std::int16_t>(std::clamp(normalized_score_for_tt(alpha, ply), -32767, 32767));
        set_tt_meta(entry, depth, alpha <= original_alpha ? Upper : (alpha >= beta ? Lower : Exact), context);
    }
    return alpha;
}

SearchInfo Searcher::search(Board board, const SearchLimits& limits, bool emit_info) {
    for (auto& row : history_) {
        for (int& value : row) value /= 2;
    }
    nodes_ = 0;
    seldepth_ = 0;
    pondering_ = limits.ponder;
    root_moves_ = limits.search_moves;
    root_restricted_ = limits.search_moves_specified;
    null_tries_ = 0;
    null_cutoffs_ = 0;
    reverse_futility_cutoffs_ = 0;
    node_limit_ = limits.nodes;
    node_limit_specified_ = limits.nodes_specified || limits.nodes != 0;
    const std::int64_t move_overhead_ms = std::max<std::int64_t>(0, limits.move_overhead_ms);
    if (limits.infinite) {
        time_limit_ms_ = 0;
    } else if (limits.movetime_ms >= 0) {
        const std::int64_t movetime_ms = limits.movetime_ms;
        time_limit_ms_ = static_cast<std::uint64_t>(
            std::max<std::int64_t>(1, movetime_ms - move_overhead_ms));
    } else if (limits.time_ms >= 0) {
        const std::int64_t time_ms = limits.time_ms;
        const std::int64_t moves_to_go = std::max<std::int64_t>(1, limits.moves_to_go);
        const std::int64_t increment_ms = std::max<std::int64_t>(0, limits.increment_ms);
        const std::int64_t share = time_ms / moves_to_go;
        const std::int64_t budget = std::min(time_ms / 2, share + increment_ms * 3 / 4);
        time_limit_ms_ = static_cast<std::uint64_t>(
            std::max<std::int64_t>(1, std::min(time_ms, budget) - move_overhead_ms));
    } else {
        time_limit_ms_ = 0;
    }
    time_check_mask_ = time_limit_ms_ <= 10 ? 0U : (time_limit_ms_ <= 100 ? 31U : 255U);
    start_ = std::chrono::steady_clock::now();
    SearchInfo result;
    if (root_restricted_) {
        const auto legal_root = board.legal_moves();
        result.restricted_root_empty = !legal_root.empty() &&
            std::none_of(legal_root.begin(), legal_root.end(), [&](const Move& legal) {
                return std::any_of(root_moves_.begin(), root_moves_.end(),
                                   [&](const Move& requested) { return same_move(legal, requested); });
            });
        if (result.restricted_root_empty && emit_info) {
            const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
            std::cout << "info string searchmoves restriction has no legal root moves" << std::endl;
        }
    }
    const int mate_moves = std::clamp(limits.mate_moves, 0, 32);
    const int mate_depth = mate_moves > 0 ? mate_moves * 2 - 1 : 64;
    const int max_depth = std::clamp(std::min(limits.depth, mate_depth), 1, 64);
    for (int depth = 1; depth <= max_depth; ++depth) {
        aborted_ = false;
        std::vector<Move> pv;
        int alpha = -Infinity;
        int beta = Infinity;
        if (depth >= 4 && result.depth > 0 && std::abs(result.score) < MateScore - 128) {
            constexpr int AspirationMargin = 35;
            alpha = std::max(-Infinity, result.score - AspirationMargin);
            beta = std::min(Infinity, result.score + AspirationMargin);
        }
        root_best_move_ = Move{};
        int score = alpha_beta(board, depth, 0, alpha, beta);
        if (score <= alpha || score >= beta) {
            if (should_stop()) {
                aborted_ = true;
            } else {
                root_best_move_ = Move{};
                score = alpha_beta(board, depth, 0, -Infinity, Infinity);
            }
        }
        if (aborted_) break;
        if (root_restricted_) {
            if (root_best_move_.from != root_best_move_.to) {
                const bool root_allowed = std::any_of(
                    root_moves_.begin(), root_moves_.end(),
                    [&](const Move& allowed) { return same_move(root_best_move_, allowed); });
                if (root_allowed) {
                    const auto legal = board.legal_moves();
                    const auto found = std::find_if(legal.begin(), legal.end(), [&](const Move& move) {
                        return same_move(move, root_best_move_);
                    });
                    if (found != legal.end()) {
                        pv.push_back(*found);
                        Board child = board;
                        Undo undo;
                        (void)child.make_move(*found, undo);
                        std::vector<Move> child_pv = extract_pv(child, depth - 1);
                        pv.insert(pv.end(), child_pv.begin(), child_pv.end());
                    }
                }
            }
        } else {
            const std::vector<Move> tt_pv = extract_pv(board, depth);
            if (!tt_pv.empty()) pv = tt_pv;
        }
        result.score = score;
        result.depth = depth;
        result.pv = pv;
        result.best_move = pv.empty() ? Move{} : pv.front();
        result.nodes = nodes_;
        result.seldepth = seldepth_;
        result.elapsed_ms = static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start_).count());
        if (emit_info) {
            const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
            std::cout << "info depth " << depth << " score ";
            if (std::abs(score) > MateScore - 128) {
                const int mate = (MateScore - std::abs(score) + 1) / 2;
                std::cout << "mate " << (score >= 0 ? mate : -mate);
            } else {
                std::cout << "cp " << score;
            }
            const std::uint64_t nps = result.elapsed_ms > 0 ? nodes_ * 1000U / result.elapsed_ms : 0;
            std::cout << " seldepth " << seldepth_ << " nodes " << nodes_ << " nps " << nps
                      << " hashfull " << hashfull_permille() << " time " << result.elapsed_ms << " pv";
            for (const Move move : pv) std::cout << ' ' << Board::move_to_uci(move);
            std::cout << std::endl;
        }
        if (limits.mate_moves > 0 && std::abs(score) > MateScore - 128 &&
            MateScore - std::abs(score) <= mate_depth) break;
        if (should_stop()) break;
    }
    result.nodes = nodes_;
    result.seldepth = seldepth_;
    result.elapsed_ms = static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - start_).count());
    if (result.best_move.from == result.best_move.to) {
        auto moves = board.legal_moves();
        if (root_restricted_) {
            std::size_t write = 0;
            for (const Move move : moves) {
                const bool allowed = std::any_of(
                    root_moves_.begin(), root_moves_.end(),
                    [&](const Move& candidate) { return same_move(move, candidate); });
                if (allowed) moves[write++] = move;
            }
            moves.resize(write);
        }
        if (!moves.empty()) result.best_move = moves.front();
    }
    return result;
}

} // namespace forge
