#include "forge/search.hpp"
#include "forge/uci_output.hpp"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>

namespace forge {
namespace {

constexpr int HistoryMax = 16384;

[[nodiscard]] int score_to_tt(int score, int ply) {
    if (score >= MateInMaxPly) return score + ply;
    if (score <= -MateInMaxPly) return score - ply;
    return score;
}

[[nodiscard]] int score_from_tt(int score, int ply) {
    if (score == ValueNone) return ValueNone;
    if (score >= MateInMaxPly) return score - ply;
    if (score <= -MateInMaxPly) return score + ply;
    return score;
}

[[nodiscard]] int mated_in(int ply) { return -MateValue + ply; }
[[nodiscard]] int mate_in(int ply) { return MateValue - ply; }

struct ReductionTable {
    std::array<std::array<std::uint8_t, 64>, 64> quiet{};
    std::array<std::array<std::uint8_t, 64>, 64> noisy{};
    ReductionTable() {
        for (int depth = 1; depth < 64; ++depth) {
            for (int moves = 1; moves < 64; ++moves) {
                const double product = std::log(static_cast<double>(depth)) * std::log(static_cast<double>(moves));
                quiet[static_cast<std::size_t>(depth)][static_cast<std::size_t>(moves)] =
                    static_cast<std::uint8_t>(std::max(0.0, 0.85 + product / 2.20));
                noisy[static_cast<std::size_t>(depth)][static_cast<std::size_t>(moves)] =
                    static_cast<std::uint8_t>(std::max(0.0, 0.10 + product / 3.40));
            }
        }
    }
};
const ReductionTable Reductions;

[[nodiscard]] int reduction(bool quiet, int depth, int moves) {
    const std::size_t d = static_cast<std::size_t>(std::min(depth, 63));
    const std::size_t m = static_cast<std::size_t>(std::min(moves, 63));
    return quiet ? Reductions.quiet[d][m] : Reductions.noisy[d][m];
}

[[nodiscard]] int lmp_threshold(int depth, bool improving) {
    return improving ? 3 + depth * depth : (3 + depth * depth) / 2;
}

[[nodiscard]] int history_bonus(int depth) { return std::min(1536, 16 * depth * depth + 48 * depth - 32); }

void apply_history(std::int16_t& entry, int bonus) {
    const int clamped = std::clamp(bonus, -HistoryMax, HistoryMax);
    entry = static_cast<std::int16_t>(entry + clamped - entry * std::abs(clamped) / HistoryMax);
}

[[nodiscard]] int capture_value(const Board& board, Move move) {
    int value = SeePieceValue[static_cast<std::size_t>(piece_type(board.captured_piece(move)))];
    if (move.is_promotion()) value += SeePieceValue[move.promotion] - SeePieceValue[Pawn];
    return value;
}

std::string format_score(int score) {
    if (is_mate_score(score)) {
        const int distance = MateValue - std::abs(score);
        const int mate = (distance + 1) / 2;
        return "mate " + std::to_string(score > 0 ? mate : -mate);
    }
    return "cp " + std::to_string(score);
}

} // namespace

// ---------------------------------------------------------------------------
// Transposition table

void TranspositionTable::resize(std::size_t mb) {
    const std::size_t bytes = std::max<std::size_t>(1, mb) * 1024U * 1024U;
    cluster_count_ = std::max<std::size_t>(1, bytes / sizeof(TTCluster));
    clusters_ = std::make_unique<TTCluster[]>(cluster_count_);
    generation_ = 0;
}

void TranspositionTable::clear() {
    for (std::size_t i = 0; i < cluster_count_; ++i) clusters_[i] = TTCluster{};
    generation_ = 0;
}

TTEntry* TranspositionTable::probe(std::uint64_t key, bool& hit) {
    TTCluster& cluster = cluster_for(key);
    const std::uint32_t key32 = static_cast<std::uint32_t>(key >> 32U);
    for (TTEntry& entry : cluster.entries) {
        if (entry.key32 == key32 && entry.occupied()) {
            hit = true;
            return &entry;
        }
    }
    hit = false;
    TTEntry* replace = &cluster.entries[0];
    auto relative_age = [this](const TTEntry& entry) {
        return static_cast<int>((32 + generation_ - entry.generation()) & 31U);
    };
    for (TTEntry& entry : cluster.entries) {
        if (!entry.occupied()) return &entry;
        if (entry.depth - 4 * relative_age(entry) < replace->depth - 4 * relative_age(*replace)) replace = &entry;
    }
    return replace;
}

void TranspositionTable::store(TTEntry* entry, std::uint64_t key, int score, int eval, Move move, int depth,
                               Bound bound, bool pv) {
    const std::uint32_t key32 = static_cast<std::uint32_t>(key >> 32U);
    const bool same_position = entry->key32 == key32 && entry->occupied();
    if (!move.is_none() || !same_position) entry->move = move;
    if (bound == BoundExact || !same_position || depth + 4 > entry->depth || entry->generation() != generation_) {
        entry->key32 = key32;
        entry->score = static_cast<std::int16_t>(std::clamp(score, -32767, 32767));
        entry->eval = static_cast<std::int16_t>(std::clamp(eval, -32767, 32767));
        entry->depth = static_cast<std::uint8_t>(std::clamp(depth, 0, 255));
        entry->gen_bound = static_cast<std::uint8_t>((static_cast<unsigned>(generation_) << 3U) | (pv ? 4U : 0U) | static_cast<unsigned>(bound));
    }
}

int TranspositionTable::hashfull() const {
    int count = 0;
    const std::size_t sample = std::min<std::size_t>(1000, cluster_count_);
    for (std::size_t i = 0; i < sample; ++i) {
        for (const TTEntry& entry : clusters_[i].entries) {
            if (entry.occupied() && entry.generation() == generation_) ++count;
        }
    }
    return sample == 0 ? 0 : count * 1000 / (4 * static_cast<int>(sample));
}

// ---------------------------------------------------------------------------
// Move picker

class MovePicker {
public:
    enum class Mode { Main, Quiescence };

    MovePicker(const Board& board, const Searcher& searcher, const SearchStack* ss, Move tt_move, Mode mode)
        : board_(board), searcher_(searcher), ss_(ss), tt_move_(tt_move) {
        const bool in_check = board.in_check();
        if (!tt_move_.is_none() && !board_.is_pseudo_legal(tt_move_)) tt_move_ = Move::none();
        if (mode == Mode::Quiescence && !in_check && !tt_move_.is_none() && !tt_move_.is_capture() &&
            !tt_move_.is_promotion()) {
            tt_move_ = Move::none();
        }
        if (in_check) stage_ = tt_move_.is_none() ? EvasionGenerate : EvasionTT;
        else if (mode == Mode::Quiescence) stage_ = tt_move_.is_none() ? QsGenerate : QsTT;
        else stage_ = tt_move_.is_none() ? GenerateCaptures : MainTT;
        if (ss != nullptr) {
            killers_ = ss->killers;
            const SearchStack* previous = ss - 1;
            if (!previous->current_move.is_none() && previous->moved_piece != Empty) {
                counter_ = (*searcher_.counter_moves_)[static_cast<std::size_t>(previous->moved_piece)][previous->current_move.to];
            }
        }
        // Squares from which each piece type would give direct check.
        const Color them = opposite(board.side_to_move());
        const int enemy_king = board.king_square(them);
        const Bitboard occupancy = board.occupied();
        check_squares_[Pawn] = attacks::pawn(them, enemy_king);
        check_squares_[Knight] = attacks::knight(enemy_king);
        check_squares_[Bishop] = attacks::bishop(enemy_king, occupancy);
        check_squares_[Rook] = attacks::rook(enemy_king, occupancy);
        check_squares_[Queen] = check_squares_[Bishop] | check_squares_[Rook];
        check_squares_[King] = 0;
    }

    [[nodiscard]] Move next(bool skip_quiets) {
        while (true) {
            switch (stage_) {
            case MainTT:
            case QsTT:
            case EvasionTT:
                stage_ = static_cast<Stage>(stage_ + 1);
                return tt_move_;

            case GenerateCaptures:
                generate_captures();
                stage_ = GoodCaptures;
                [[fallthrough]];
            case GoodCaptures:
                while (index_ < count_) {
                    const Move move = pick_best();
                    if (move == tt_move_) continue;
                    if (!board_.see_ge(move, -move_score_threshold(move))) {
                        bad_captures_[bad_count_++] = move;
                        continue;
                    }
                    return move;
                }
                stage_ = Killer1;
                [[fallthrough]];
            case Killer1:
                stage_ = Killer2;
                if (!skip_quiets && is_valid_quiet(killers_[0])) return killers_[0];
                [[fallthrough]];
            case Killer2:
                stage_ = CounterMove;
                if (!skip_quiets && is_valid_quiet(killers_[1]) && killers_[1] != killers_[0]) return killers_[1];
                [[fallthrough]];
            case CounterMove:
                stage_ = GenerateQuiets;
                if (!skip_quiets && is_valid_quiet(counter_) && counter_ != killers_[0] && counter_ != killers_[1]) {
                    return counter_;
                }
                [[fallthrough]];
            case GenerateQuiets:
                if (!skip_quiets) generate_quiets();
                stage_ = QuietMoves;
                [[fallthrough]];
            case QuietMoves:
                if (!skip_quiets) {
                    while (index_ < count_) {
                        const Move move = pick_best();
                        if (move == tt_move_ || move == killers_[0] || move == killers_[1] || move == counter_) continue;
                        return move;
                    }
                }
                stage_ = BadCaptures;
                bad_index_ = 0;
                [[fallthrough]];
            case BadCaptures:
                if (bad_index_ < bad_count_) return bad_captures_[bad_index_++];
                return Move::none();

            case QsGenerate:
                generate_captures();
                stage_ = QsCaptures;
                [[fallthrough]];
            case QsCaptures:
                while (index_ < count_) {
                    const Move move = pick_best();
                    if (move == tt_move_) continue;
                    return move;
                }
                return Move::none();

            case EvasionGenerate:
                generate_evasions();
                stage_ = Evasions;
                [[fallthrough]];
            case Evasions:
                while (index_ < count_) {
                    const Move move = pick_best();
                    if (move == tt_move_) continue;
                    return move;
                }
                return Move::none();
            }
        }
    }

private:
    enum Stage : int {
        MainTT, GenerateCaptures, GoodCaptures, Killer1, Killer2, CounterMove, GenerateQuiets, QuietMoves, BadCaptures,
        QsTT, QsGenerate, QsCaptures,
        EvasionTT, EvasionGenerate, Evasions
    };
    struct Scored {
        Move move;
        int score;
    };

    const Board& board_;
    const Searcher& searcher_;
    const SearchStack* ss_;
    Move tt_move_;
    std::array<Move, 2> killers_{};
    Move counter_{};
    Stage stage_;
    std::array<Scored, 256> moves_{};
    std::size_t index_ = 0;
    std::size_t count_ = 0;
    std::array<Move, 64> bad_captures_{};
    std::size_t bad_count_ = 0;
    std::size_t bad_index_ = 0;
    MoveList buffer_;
    std::array<Bitboard, 7> check_squares_{};

    [[nodiscard]] bool direct_check(Move move) const {
        const int type = piece_type(board_.moved_piece(move));
        return (check_squares_[static_cast<std::size_t>(type)] & square_bb(move.to)) != 0;
    }

    [[nodiscard]] static int move_score_threshold(Move) { return 0; }

    [[nodiscard]] bool is_valid_quiet(Move move) const {
        return !move.is_none() && move != tt_move_ && !move.is_capture() && !move.is_promotion() &&
               board_.is_pseudo_legal(move);
    }

    // Lists are sorted once when generated, so picking is sequential.
    [[nodiscard]] Move pick_best() { return moves_[index_++].move; }

    void sort_moves() {
        std::sort(moves_.begin(), moves_.begin() + static_cast<std::ptrdiff_t>(count_),
                  [](const Scored& a, const Scored& b) { return a.score > b.score; });
    }

    void generate_captures() {
        buffer_.clear();
        board_.generate_pseudo_legal(buffer_, true);
        index_ = 0;
        count_ = 0;
        for (const Move move : buffer_) {
            int score = 10 * capture_value(board_, move) + searcher_.capture_history_value(board_, move);
            if (move.is_promotion()) score += move.promotion == Queen ? 20000 : -5000;
            moves_[count_++] = Scored{move, score};
        }
        sort_moves();
    }

    void generate_quiets() {
        buffer_.clear();
        board_.generate_pseudo_legal(buffer_, false);
        index_ = 0;
        count_ = 0;
        for (const Move move : buffer_) {
            if (move.is_capture() || move.is_promotion()) continue;
            int score = searcher_.quiet_history(board_, ss_, move);
            if (direct_check(move)) score += 12000;
            moves_[count_++] = Scored{move, score};
        }
        sort_moves();
    }

    void generate_evasions() {
        buffer_.clear();
        board_.generate_pseudo_legal(buffer_, false);
        index_ = 0;
        count_ = 0;
        for (const Move move : buffer_) {
            int score;
            if (move.is_capture() || move.is_promotion()) {
                score = 1'000'000 + 10 * capture_value(board_, move) -
                        SeePieceValue[static_cast<std::size_t>(piece_type(board_.moved_piece(move)))] / 10;
            } else {
                score = searcher_.quiet_history(board_, ss_, move) + (direct_check(move) ? 12000 : 0);
            }
            moves_[count_++] = Scored{move, score};
        }
        sort_moves();
    }
};

// ---------------------------------------------------------------------------
// Searcher

Searcher::Searcher(std::size_t hash_mb)
    : tt_(hash_mb),
      main_history_(std::make_unique<ButterflyHistory>()),
      capture_history_(std::make_unique<CaptureHistory>()),
      continuation_history_(std::make_unique<ContinuationHistory>()),
      counter_moves_(std::make_unique<CounterMoveTable>()),
      correction_history_(std::make_unique<CorrectionHistory>()) {
    clear();
}

Searcher::~Searcher() = default;

void Searcher::resize_hash(std::size_t hash_mb) { tt_.resize(hash_mb); }

void Searcher::clear_hash() {
    tt_.clear();
    evaluator_.clear();
}

void Searcher::clear() {
    clear_hash();
    *main_history_ = ButterflyHistory{};
    *capture_history_ = CaptureHistory{};
    *continuation_history_ = ContinuationHistory{};
    *counter_moves_ = CounterMoveTable{};
    *correction_history_ = CorrectionHistory{};
    for (SearchStack& ss : stack_) ss = SearchStack{};
}

int Searcher::corrected_eval(const Board& board, int raw_eval) const {
    const std::int32_t correction =
        (*correction_history_)[static_cast<std::size_t>(board.side_to_move())][board.pawn_key() & (CorrectionSize - 1U)];
    return std::clamp(raw_eval + correction / CorrectionGrain, -MateInMaxPly + 1, MateInMaxPly - 1);
}

void Searcher::update_correction(const Board& board, int depth, int best_score, int static_eval) {
    std::int32_t& entry =
        (*correction_history_)[static_cast<std::size_t>(board.side_to_move())][board.pawn_key() & (CorrectionSize - 1U)];
    const int diff = std::clamp((best_score - static_eval) * CorrectionGrain, -CorrectionLimit / 4, CorrectionLimit / 4);
    const int weight = std::min(depth + 1, 16);
    entry = std::clamp((entry * (256 - weight) + diff * weight) / 256, -CorrectionLimit, CorrectionLimit);
}

std::int64_t Searcher::elapsed_ms() const {
    auto origin = start_;
    if (pondering_) {
        const std::int64_t hit_ns = ponder_hit_ns_.load(std::memory_order_relaxed);
        if (hit_ns == 0) return 0;
        origin = std::chrono::steady_clock::time_point(
            std::chrono::duration_cast<std::chrono::steady_clock::duration>(std::chrono::nanoseconds(hit_ns)));
    }
    return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - origin).count();
}

bool Searcher::should_stop() {
    if (stop_.load(std::memory_order_relaxed)) return true;
    if (node_limit_specified_ && nodes_ >= node_limit_) return true;
    if (hard_limit_ms_ > 0) {
        if (pondering_ && ponder_hit_ns_.load(std::memory_order_relaxed) == 0) return false;
        if (elapsed_ms() >= hard_limit_ms_) return true;
    }
    return false;
}

bool Searcher::is_draw(const Board& board, int ply) const {
    (void)ply;
    if (board.halfmove_clock() >= 100) {
        // Checkmate on the hundredth half-move still wins; everything else is a draw.
        return !board.in_check() || board.has_legal_move();
    }
    return board.is_repetition(root_history_index_) || board.is_insufficient_material();
}

int Searcher::quiet_history(const Board& board, const SearchStack* ss, Move move) const {
    const Piece piece = board.moved_piece(move);
    int score = (*main_history_)[static_cast<std::size_t>(board.side_to_move())][move.from][move.to];
    if (ss != nullptr) {
        if ((ss - 1)->continuation != nullptr) score += (*(ss - 1)->continuation)[static_cast<std::size_t>(piece)][move.to];
        if ((ss - 2)->continuation != nullptr) score += (*(ss - 2)->continuation)[static_cast<std::size_t>(piece)][move.to];
    }
    return score;
}

int Searcher::capture_history_value(const Board& board, Move move) const {
    const Piece piece = board.moved_piece(move);
    const int captured = piece_type(board.captured_piece(move));
    return (*capture_history_)[static_cast<std::size_t>(piece)][move.to][static_cast<std::size_t>(captured)];
}

void Searcher::update_continuation(SearchStack* ss, Piece piece, int to, int bonus) {
    for (const int back : {1, 2, 4}) {
        const SearchStack* previous = ss - back;
        if (previous->continuation == nullptr || previous->current_move.is_none()) continue;
        apply_history((*previous->continuation)[static_cast<std::size_t>(piece)][static_cast<std::size_t>(to)],
                      back == 4 ? bonus / 2 : bonus);
    }
}

void Searcher::update_quiet_stats(const Board& board, SearchStack* ss, Move move, int depth, const Move* quiets,
                                  int quiet_count) {
    const int bonus = history_bonus(depth);
    const Color us = board.side_to_move();
    if (ss->killers[0] != move) {
        ss->killers[1] = ss->killers[0];
        ss->killers[0] = move;
    }
    const SearchStack* previous = ss - 1;
    if (!previous->current_move.is_none() && previous->moved_piece != Empty) {
        (*counter_moves_)[static_cast<std::size_t>(previous->moved_piece)][previous->current_move.to] = move;
    }
    const Piece piece = board.moved_piece(move);
    apply_history((*main_history_)[static_cast<std::size_t>(us)][move.from][move.to], bonus);
    update_continuation(ss, piece, move.to, bonus);
    for (int i = 0; i < quiet_count; ++i) {
        const Move quiet = quiets[i];
        if (quiet == move) continue;
        apply_history((*main_history_)[static_cast<std::size_t>(us)][quiet.from][quiet.to], -bonus);
        update_continuation(ss, board.moved_piece(quiet), quiet.to, -bonus);
    }
}

void Searcher::update_capture_stats(const Board& board, Move best, int depth, const Move* captures, int capture_count) {
    const int bonus = history_bonus(depth);
    if (best.is_capture()) {
        const Piece piece = board.moved_piece(best);
        const int captured = piece_type(board.captured_piece(best));
        apply_history((*capture_history_)[static_cast<std::size_t>(piece)][best.to][static_cast<std::size_t>(captured)], bonus);
    }
    for (int i = 0; i < capture_count; ++i) {
        const Move capture = captures[i];
        if (capture == best) continue;
        const Piece piece = board.moved_piece(capture);
        const int captured = piece_type(board.captured_piece(capture));
        apply_history((*capture_history_)[static_cast<std::size_t>(piece)][capture.to][static_cast<std::size_t>(captured)], -bonus);
    }
}

// ---------------------------------------------------------------------------
// Quiescence search

int Searcher::qsearch(Board& board, SearchStack* ss, int alpha, int beta) {
    const bool pv_node = beta - alpha > 1;
    const int ply = ss->ply;
    if (((nodes_ & 1023U) == 0 || node_limit_specified_) && should_stop()) aborted_ = true;
    if (aborted_) return 0;
    ++nodes_;
    seldepth_ = std::max(seldepth_, ply);
    ss->pv_length = 0;

    if (is_draw(board, ply)) return 0;
    if (ply >= MaxPly) return board.in_check() ? 0 : evaluator_.evaluate(board);

    const bool in_check = board.in_check();
    ss->in_check = in_check;
    (ss + 1)->killers = {};

    bool tt_hit = false;
    TTEntry* tte = tt_.probe(board.key(), tt_hit);
    const Move tt_move = tt_hit ? tte->move : Move::none();
    const int tt_score = tt_hit ? score_from_tt(tte->score, ply) : ValueNone;
    const Bound tt_bound = tt_hit ? tte->bound() : BoundNone;
    const bool tt_pv = pv_node || (tt_hit && tte->pv());
    if (!pv_node && tt_hit && tt_score != ValueNone &&
        (tt_bound == BoundExact || (tt_bound == BoundLower && tt_score >= beta) ||
         (tt_bound == BoundUpper && tt_score <= alpha))) {
        return tt_score;
    }

    int best_score;
    int futility_base;
    if (in_check) {
        ss->static_eval = ValueNone;
        best_score = futility_base = -Infinite;
    } else {
        int eval;
        if (tt_hit && tte->eval != ValueNone) ss->raw_eval = tte->eval;
        else ss->raw_eval = evaluator_.evaluate(board);
        eval = ss->static_eval = corrected_eval(board, ss->raw_eval);
        if (tt_hit && tt_score != ValueNone &&
            ((tt_bound == BoundLower && tt_score > eval) || (tt_bound == BoundUpper && tt_score < eval) ||
             tt_bound == BoundExact)) {
            eval = tt_score;
        }
        best_score = eval;
        if (best_score >= beta) {
            if (!tt_hit) tt_.store(tte, board.key(), score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, false);
            return best_score;
        }
        if (best_score > alpha) alpha = best_score;
        futility_base = ss->static_eval + 160;
    }

    MovePicker picker(board, *this, ss, tt_move, MovePicker::Mode::Quiescence);
    Move best_move = Move::none();
    int move_count = 0;
    Move move;
    while (!(move = picker.next(false)).is_none()) {
        if (!board.is_legal(move)) continue;
        ++move_count;
        const bool gives_check = board.gives_check(move);
        if (!in_check && best_score > -MateInMaxPly) {
            // Futility: even winning the captured piece cannot raise alpha.
            if (!gives_check && !move.is_promotion() && futility_base + capture_value(board, move) <= alpha) {
                best_score = std::max(best_score, futility_base + capture_value(board, move));
                continue;
            }
            if (!board.see_ge(move, -40)) continue;
        }
        ss->current_move = move;
        ss->moved_piece = board.moved_piece(move);
        ss->continuation = &(*continuation_history_)[static_cast<std::size_t>(ss->moved_piece)][move.to];
        (ss + 1)->ply = ply + 1;
        Undo undo;
        (void)board.make_move(move, undo);
        tt_.prefetch(board.key());
        const int score = -qsearch(board, ss + 1, -beta, -alpha);
        board.unmake_move(move, undo);
        if (aborted_) return 0;
        if (score > best_score) {
            best_score = score;
            if (score > alpha) {
                best_move = move;
                if (pv_node) {
                    ss->pv[0] = move;
                    std::copy_n((ss + 1)->pv.begin(), (ss + 1)->pv_length, ss->pv.begin() + 1);
                    ss->pv_length = (ss + 1)->pv_length + 1;
                }
                if (score >= beta) break;
                alpha = score;
            }
        }
    }
    if (in_check && move_count == 0) return mated_in(ply);

    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
    tt_.store(tte, board.key(), score_to_tt(best_score, ply), in_check ? ValueNone : ss->raw_eval, best_move, 0, bound, tt_pv);
    return best_score;
}

// ---------------------------------------------------------------------------
// Main alpha-beta search

int Searcher::search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {
    const bool pv_node = beta - alpha > 1;
    const bool root_node = ss->ply == 0;
    const int ply = ss->ply;

    if (depth <= 0) return qsearch(board, ss, alpha, beta);
    if (((nodes_ & 1023U) == 0 || node_limit_specified_) && should_stop()) aborted_ = true;
    if (aborted_) return 0;
    ++nodes_;
    seldepth_ = std::max(seldepth_, ply);
    ss->pv_length = 0;
    ss->move_count = 0;

    if (!root_node) {
        if (is_draw(board, ply)) return 0;
        if (ply >= MaxPly) return board.in_check() ? 0 : evaluator_.evaluate(board);
        // Mate distance pruning.
        alpha = std::max(alpha, mated_in(ply));
        beta = std::min(beta, mate_in(ply + 1));
        if (alpha >= beta) return alpha;
    }

    const bool in_check = board.in_check();
    ss->in_check = in_check;
    const Move excluded = ss->excluded_move;
    (ss + 1)->killers = {};
    (ss + 1)->excluded_move = Move::none();
    (ss + 2)->killers = {};

    // Transposition table probe.
    bool tt_hit = false;
    TTEntry* tte = tt_.probe(board.key(), tt_hit);
    const Move tt_move = tt_hit ? tte->move : Move::none();
    const int tt_score = tt_hit ? score_from_tt(tte->score, ply) : ValueNone;
    const int tt_depth = tt_hit ? tte->depth : -1;
    const Bound tt_bound = tt_hit ? tte->bound() : BoundNone;
    const bool tt_capture = !tt_move.is_none() && tt_move.is_capture();
    ss->tt_pv = pv_node || (tt_hit && tte->pv());

    if (!pv_node && excluded.is_none() && tt_hit && tt_score != ValueNone && tt_depth >= depth &&
        board.halfmove_clock() < 90 &&
        (tt_bound == BoundExact || (tt_bound == BoundLower && tt_score >= beta) ||
         (tt_bound == BoundUpper && tt_score <= alpha))) {
        return tt_score;
    }

    // Static evaluation.
    int eval;
    if (in_check) {
        eval = ss->static_eval = ss->raw_eval = ValueNone;
    } else if (!excluded.is_none()) {
        eval = ss->static_eval;
    } else {
        if (tt_hit && tte->eval != ValueNone) ss->raw_eval = tte->eval;
        else ss->raw_eval = evaluator_.evaluate(board);
        eval = ss->static_eval = corrected_eval(board, ss->raw_eval);
        if (tt_hit && tt_score != ValueNone &&
            ((tt_bound == BoundLower && tt_score > eval) || (tt_bound == BoundUpper && tt_score < eval) ||
             tt_bound == BoundExact)) {
            eval = tt_score;
        }
    }

    bool improving = false;
    if (!in_check) {
        if ((ss - 2)->static_eval != ValueNone) improving = ss->static_eval > (ss - 2)->static_eval;
        else if ((ss - 4)->static_eval != ValueNone) improving = ss->static_eval > (ss - 4)->static_eval;
        else improving = true;
    }

    if (!pv_node && !in_check && excluded.is_none() && !is_mate_score(beta)) {
        // Razoring: hopeless positions fall back to quiescence.
        if (depth <= 2 && eval + 150 + 350 * depth < alpha) {
            const int razor = qsearch(board, ss, alpha - 1, alpha);
            if (aborted_) return 0;
            if (razor < alpha) return razor;
        }
        // Reverse futility pruning.
        if (depth <= 8 && eval - (72 * depth - 40 * improving) >= beta && eval < MateInMaxPly) return eval;
        // Null move pruning.
        if (depth >= 3 && eval >= beta && ss->static_eval >= beta - 24 * depth + 180 &&
            ss->null_move_allowed && !(ss - 1)->current_move.is_none() &&
            board.has_non_pawn_material(board.side_to_move()) &&
            !(tt_hit && tt_bound == BoundUpper && tt_score < beta)) {
            ++null_tries_;
            const int reduction = 3 + depth / 3 + std::min((eval - beta) / 200, 3);
            ss->current_move = Move::none();
            ss->moved_piece = Empty;
            ss->continuation = &(*continuation_history_)[Empty][0];
            (ss + 1)->ply = ply + 1;
            NullUndo undo;
            board.make_null_move(undo);
            int null_score = -search(board, ss + 1, depth - reduction, -beta, -beta + 1, !cut_node);
            board.unmake_null_move(undo);
            if (aborted_) return 0;
            if (null_score >= beta) {
                if (is_mate_score(null_score)) null_score = beta;
                if (depth < 14) {
                    ++null_cutoffs_;
                    return null_score;
                }
                // Verification search at high depth guards against zugzwang.
                ss->null_move_allowed = false;
                const int verification = search(board, ss, depth - reduction, beta - 1, beta, false);
                ss->null_move_allowed = true;
                if (aborted_) return 0;
                if (verification >= beta) {
                    ++null_cutoffs_;
                    return null_score;
                }
            }
        }
        // ProbCut: a good capture that beats beta by a margin at reduced depth.
        const int probcut_beta = beta + 180 - 50 * improving;
        if (depth >= 5 && !is_mate_score(beta) &&
            !(tt_hit && tt_depth >= depth - 3 && tt_score != ValueNone && tt_score < probcut_beta)) {
            MovePicker picker(board, *this, ss, tt_move, MovePicker::Mode::Quiescence);
            Move move;
            while (!(move = picker.next(false)).is_none()) {
                if (move == excluded || !board.is_legal(move)) continue;
                if (!board.see_ge(move, probcut_beta - ss->static_eval)) continue;
                ss->current_move = move;
                ss->moved_piece = board.moved_piece(move);
                ss->continuation = &(*continuation_history_)[static_cast<std::size_t>(ss->moved_piece)][move.to];
                (ss + 1)->ply = ply + 1;
                Undo undo;
                (void)board.make_move(move, undo);
                int value = -qsearch(board, ss + 1, -probcut_beta, -probcut_beta + 1);
                if (value >= probcut_beta && !aborted_) {
                    value = -search(board, ss + 1, depth - 4, -probcut_beta, -probcut_beta + 1, !cut_node);
                }
                board.unmake_move(move, undo);
                if (aborted_) return 0;
                if (value >= probcut_beta) {
                    tt_.store(tte, board.key(), score_to_tt(value, ply), ss->raw_eval, move, depth - 3, BoundLower, ss->tt_pv);
                    return value;
                }
            }
        }
    }

    // Internal iterative reduction: no hash move suggests a less important node.
    if (!in_check && depth >= 4 && tt_move.is_none() && (pv_node || cut_node)) --depth;

    MovePicker picker(board, *this, ss, tt_move, MovePicker::Mode::Main);
    std::array<Move, 128> quiets_tried{};
    std::array<Move, 64> captures_tried{};
    int quiet_count = 0;
    int capture_count = 0;
    int best_score = -Infinite;
    Move best_move = Move::none();
    int move_count = 0;
    bool skip_quiets = false;
    const bool has_material = board.has_non_pawn_material(board.side_to_move());

    Move move;
    while (!(move = picker.next(skip_quiets)).is_none()) {
        if (move == excluded) continue;
        if (root_node && root_restricted_ &&
            std::none_of(root_moves_.begin(), root_moves_.end(), [&](const Move& m) { return m == move; })) {
            continue;
        }
        if (!board.is_legal(move)) continue;
        ++move_count;
        ss->move_count = move_count;
        const bool capture = move.is_capture();
        const bool quiet = !capture && !move.is_promotion();
        const bool gives_check = board.gives_check(move);
        const Piece moved = board.moved_piece(move);
        const int history = quiet ? quiet_history(board, ss, move) : capture_history_value(board, move);

        // Shallow-depth pruning of unpromising moves.
        if (!root_node && best_score > -MateInMaxPly && has_material) {
            if (quiet && !skip_quiets && move_count >= lmp_threshold(depth, improving)) skip_quiets = true;
            const int lmr_depth = std::max(0, depth - reduction(quiet, depth, move_count));
            if (quiet && !gives_check) {
                if (!in_check && lmr_depth <= 7 && ss->static_eval + 100 + 110 * lmr_depth <= alpha) {
                    skip_quiets = true;
                    continue;
                }
                if (lmr_depth <= 3 && history < -2048 * depth) continue;
                if (!board.see_ge(move, -24 * lmr_depth * lmr_depth)) continue;
            } else if (!board.see_ge(move, -150 * depth)) {
                continue;
            }
        }

        // Extensions.
        int extension = 0;
        if (!root_node && depth >= 7 && move == tt_move && excluded.is_none() && tt_bound != BoundUpper &&
            tt_score != ValueNone && !is_mate_score(tt_score) && tt_depth >= depth - 3) {
            const int singular_beta = tt_score - 2 * depth;
            const int singular_depth = (depth - 1) / 2;
            ss->excluded_move = move;
            const int singular_score = search(board, ss, singular_depth, singular_beta - 1, singular_beta, cut_node);
            ss->excluded_move = Move::none();
            if (aborted_) return 0;
            if (singular_score < singular_beta) {
                extension = 1;
                if (!pv_node && singular_score < singular_beta - 24 && ss->double_extensions <= 6) {
                    extension = 2;
                    ss->double_extensions = (ss - 1)->double_extensions + 1;
                }
            } else if (singular_beta >= beta) {
                return singular_beta;
            } else if (tt_score >= beta) {
                extension = -2;
            } else if (cut_node) {
                extension = -1;
            }
        } else if (gives_check && depth >= 2 && !root_node && board.see_ge(move, 0)) {
            extension = 1;
        }
        if (extension <= 0) ss->double_extensions = (ss - 1)->double_extensions;
        const int new_depth = depth - 1 + extension;

        ss->current_move = move;
        ss->moved_piece = moved;
        ss->continuation = &(*continuation_history_)[static_cast<std::size_t>(moved)][move.to];
        (ss + 1)->ply = ply + 1;
        Undo undo;
        (void)board.make_move(move, undo);
        tt_.prefetch(board.key());
        const std::uint64_t nodes_before = nodes_;

        int score = -Infinite;
        bool full_depth_needed = !pv_node || move_count > 1;
        if (depth >= 2 && move_count > 1 + (root_node ? 1 : 0) && (quiet || !ss->tt_pv || move_count > 4)) {
            int r = reduction(quiet, depth, move_count);
            if (ss->tt_pv) r -= 1;
            if (!improving) r += 1;
            if (cut_node) r += 2;
            if (tt_capture && quiet) r += 1;
            if (gives_check) r -= 1;
            if (in_check) r -= 1;
            if (quiet) r -= std::clamp(history / 6000, -2, 2);
            const int reduced_depth = std::clamp(new_depth - r, 1, new_depth);
            score = -search(board, ss + 1, reduced_depth, -alpha - 1, -alpha, true);
            full_depth_needed = score > alpha && reduced_depth < new_depth;
            if (full_depth_needed) {
                score = -search(board, ss + 1, new_depth, -alpha - 1, -alpha, !cut_node);
                full_depth_needed = false;
            }
            if (!aborted_ && quiet && score > alpha) {
                // A late quiet move that beat expectations deserves a history boost.
                update_continuation(ss, moved, move.to, history_bonus(depth) / 2);
            }
        }
        if (full_depth_needed && !aborted_) {
            score = -search(board, ss + 1, new_depth, -alpha - 1, -alpha, !cut_node);
        }
        if (pv_node && !aborted_ && (move_count == 1 || score > alpha)) {
            score = -search(board, ss + 1, new_depth, -beta, -alpha, false);
        }
        board.unmake_move(move, undo);
        if (aborted_) return 0;
        if (root_node) root_move_nodes_[static_cast<std::size_t>(move_count - 1)] += nodes_ - nodes_before;

        if (score > best_score) {
            best_score = score;
            if (score > alpha) {
                best_move = move;
                if (pv_node) {
                    ss->pv[0] = move;
                    std::copy_n((ss + 1)->pv.begin(), (ss + 1)->pv_length, ss->pv.begin() + 1);
                    ss->pv_length = (ss + 1)->pv_length + 1;
                }
                if (root_node) root_best_index_ = move_count - 1;
                if (score >= beta) break;
                alpha = score;
            }
        }
        if (quiet && quiet_count < static_cast<int>(quiets_tried.size())) quiets_tried[static_cast<std::size_t>(quiet_count++)] = move;
        else if (!quiet && capture_count < static_cast<int>(captures_tried.size())) captures_tried[static_cast<std::size_t>(capture_count++)] = move;
    }

    if (move_count == 0) {
        if (!excluded.is_none()) return alpha;
        if (root_node && root_restricted_) return 0;
        return in_check ? mated_in(ply) : 0;
    }

    if (best_score >= beta) {
        if (!best_move.is_capture() && !best_move.is_promotion()) {
            update_quiet_stats(board, ss, best_move, depth + (best_score > beta + 100), quiets_tried.data(), quiet_count);
        }
        update_capture_stats(board, best_move, depth, captures_tried.data(), capture_count);
    } else if (!best_move.is_none() && (!best_move.is_capture() && !best_move.is_promotion())) {
        // Even without a cutoff, a new PV move earned its place.
        apply_history((*main_history_)[static_cast<std::size_t>(board.side_to_move())][best_move.from][best_move.to],
                      history_bonus(depth) / 4);
    }

    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
    if (excluded.is_none() && !(root_node && root_restricted_)) {
        tt_.store(tte, board.key(), score_to_tt(best_score, ply), ss->raw_eval, best_move, depth, bound, ss->tt_pv);
    }
    // Teach the static evaluation about this pawn structure when the search
    // result is a usable bound in the direction of the difference.
    if (!in_check && excluded.is_none() && !is_mate_score(best_score) &&
        (best_move.is_none() || !best_move.is_capture()) &&
        !(bound == BoundLower && best_score <= ss->static_eval) &&
        !(bound == BoundUpper && best_score >= ss->static_eval)) {
        update_correction(board, depth, best_score, ss->static_eval);
    }
    return best_score;
}

// ---------------------------------------------------------------------------
// Iterative deepening driver

SearchInfo Searcher::search(Board board, const SearchLimits& limits, bool emit_info) {
    start_ = std::chrono::steady_clock::now();
    nodes_ = 0;
    seldepth_ = 0;
    aborted_ = false;
    pondering_ = limits.ponder;
    null_tries_ = 0;
    null_cutoffs_ = 0;
    root_moves_ = limits.search_moves;
    root_restricted_ = limits.search_moves_specified;
    root_history_index_ = board.history_size() - 1;
    node_limit_ = limits.nodes;
    node_limit_specified_ = limits.nodes_specified || limits.nodes != 0;
    tt_.new_search();

    // Time allocation.
    const std::int64_t overhead = std::max<std::int64_t>(0, limits.move_overhead_ms);
    soft_limit_ms_ = hard_limit_ms_ = 0;
    time_managed_ = false;
    if (limits.infinite) {
        soft_limit_ms_ = hard_limit_ms_ = 0;
    } else if (limits.movetime_ms >= 0) {
        hard_limit_ms_ = std::max<std::int64_t>(1, limits.movetime_ms - overhead);
        soft_limit_ms_ = hard_limit_ms_;
    } else if (limits.time_ms >= 0) {
        const std::int64_t time = limits.time_ms;
        const std::int64_t increment = std::max<std::int64_t>(0, limits.increment_ms);
        const std::int64_t available = std::max<std::int64_t>(1, time - overhead);
        std::int64_t soft;
        std::int64_t hard;
        if (limits.moves_to_go > 0) {
            const std::int64_t mtg = std::min<std::int64_t>(limits.moves_to_go, 50);
            soft = available / (mtg + 1) + increment * 3 / 4;
            hard = std::min(available * 4 / 5, soft * 4);
        } else {
            soft = available / 22 + increment * 3 / 4;
            hard = std::min(available * 3 / 5, soft * 5);
        }
        soft_limit_ms_ = std::max<std::int64_t>(1, std::min(soft, available));
        hard_limit_ms_ = std::max<std::int64_t>(1, std::min(hard, available));
        time_managed_ = true;
    }

    SearchInfo result;
    const MoveList legal = board.legal_moves();
    MoveList root_candidates;
    for (const Move move : legal) {
        if (!root_restricted_ ||
            std::any_of(root_moves_.begin(), root_moves_.end(), [&](const Move& m) { return m == move; })) {
            root_candidates.push_back(move);
        }
    }
    result.restricted_root_empty = root_restricted_ && !legal.empty() && root_candidates.empty();
    if (result.restricted_root_empty && emit_info) {
        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
        std::cout << "info string searchmoves restriction has no legal root moves" << std::endl;
    }

    const int mate_moves = std::clamp(limits.mate_moves, 0, 32);
    const int mate_depth = mate_moves > 0 ? mate_moves * 2 - 1 : 64;
    const int max_depth = std::clamp(std::min(limits.depth, mate_depth), 1, 64);

    auto emit = [&](int depth, int score, const std::vector<Move>& pv) {
        if (!emit_info) return;
        const std::int64_t elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start_).count();
        const std::uint64_t nps = elapsed > 0 ? nodes_ * 1000U / static_cast<std::uint64_t>(elapsed) : 0;
        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
        std::cout << "info depth " << depth << " seldepth " << std::max(seldepth_, depth) << " score " << format_score(score)
                  << " nodes " << nodes_ << " nps " << nps << " hashfull " << tt_.hashfull() << " time " << elapsed << " pv";
        for (const Move move : pv) std::cout << ' ' << Board::move_to_uci(move);
        std::cout << std::endl;
    };

    // Terminal or adjudicated roots: report without searching.
    const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                               board.is_insufficient_material());
    if (root_candidates.empty() || root_drawn) {
        int score = 0;
        if (legal.empty() && board.in_check()) score = -MateValue;
        for (int depth = 1; depth <= max_depth; ++depth) {
            result.depth = depth;
            result.score = score;
            emit(depth, score, {});
            if (should_stop()) break;
        }
        if (!root_candidates.empty()) result.best_move = root_candidates.front();
        result.nodes = nodes_;
        result.elapsed_ms = static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start_).count());
        return result;
    }

    // An explicit zero node budget is an immediate bounded answer.
    if (limits.nodes_specified && limits.nodes == 0) {
        result.best_move = root_candidates.front();
        result.depth = 0;
        return result;
    }

    for (SearchStack& ss : stack_) {
        ss.pv_length = 0;
        ss.current_move = Move::none();
        ss.excluded_move = Move::none();
        ss.moved_piece = Empty;
        ss.static_eval = ValueNone;
        ss.continuation = &(*continuation_history_)[Empty][0];
        ss.double_extensions = 0;
        ss.null_move_allowed = true;
        ss.killers = {};
    }
    SearchStack* ss = &stack_[4];
    for (int i = 0; i < MaxPly + 4; ++i) stack_[static_cast<std::size_t>(i)].ply = i - 4;

    Move previous_best = Move::none();
    int stable_iterations = 0;
    int score = 0;
    root_move_nodes_.fill(0);
    root_best_index_ = -1;
    for (int depth = 1; depth <= max_depth; ++depth) {
        root_depth_ = depth;
        int delta = 18;
        int alpha = -Infinite;
        int beta = Infinite;
        if (depth >= 4) {
            alpha = std::max(score - delta, -Infinite);
            beta = std::min(score + delta, Infinite);
        }
        int iteration_score = score;
        while (true) {
            ss->ply = 0;
            iteration_score = search(board, ss, depth, alpha, beta, false);
            if (aborted_) break;
            if (iteration_score <= alpha) {
                beta = (alpha + beta) / 2;
                alpha = std::max(iteration_score - delta, -Infinite);
            } else if (iteration_score >= beta) {
                beta = std::min(iteration_score + delta, Infinite);
            } else {
                break;
            }
            delta += delta / 2 + 4;
        }
        if (aborted_) {
            // A partially searched iteration that already raised alpha at the
            // root has found a move at least as good as the previous best.
            if (ss->pv_length > 0 && !(result.pv.size() > 0 && result.pv[0] == ss->pv[0])) {
                result.best_move = ss->pv[0];
                result.pv.assign(ss->pv.begin(), ss->pv.begin() + ss->pv_length);
                result.ponder_move = result.pv.size() > 1 ? result.pv[1] : Move::none();
                // Publish the revised line so GUIs see a PV consistent with the move.
                emit(depth, result.score, result.pv);
            }
            break;
        }
        score = iteration_score;
        result.score = score;
        result.depth = depth;
        result.seldepth = std::max(seldepth_, depth);
        result.pv.assign(ss->pv.begin(), ss->pv.begin() + ss->pv_length);
        if (!result.pv.empty()) result.best_move = result.pv.front();
        result.ponder_move = result.pv.size() > 1 ? result.pv[1] : Move::none();
        result.nodes = nodes_;
        emit(depth, score, result.pv);

        if (result.best_move == previous_best) ++stable_iterations;
        else stable_iterations = 0;
        previous_best = result.best_move;

        if (mate_moves > 0 && is_mate_score(score) && MateValue - std::abs(score) <= mate_depth) break;
        if (should_stop()) break;
        if (time_managed_ && !(pondering_ && ponder_hit_ns_.load(std::memory_order_relaxed) == 0)) {
            // Stop early when the best move has been stable; spend longer when it keeps changing.
            double factor = 1.0;
            if (stable_iterations >= 6) factor = 0.6;
            else if (stable_iterations >= 3) factor = 0.8;
            else if (stable_iterations == 0 && depth >= 6) factor = 1.4;
            // A best move that absorbed most of the effort is clearly best;
            // spend longer when the alternatives still draw attention.
            if (root_best_index_ >= 0 && nodes_ > 0 && depth >= 6) {
                const double effort = static_cast<double>(root_move_nodes_[static_cast<std::size_t>(root_best_index_)]) /
                                      static_cast<double>(nodes_);
                factor *= std::clamp(1.55 - effort, 0.6, 1.4);
            }
            if (elapsed_ms() >= static_cast<std::int64_t>(static_cast<double>(soft_limit_ms_) * factor)) break;
        }
    }

    result.nodes = nodes_;
    result.seldepth = std::max(result.seldepth, seldepth_);
    result.elapsed_ms = static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - start_).count());
    if (result.best_move.is_none()) result.best_move = root_candidates.front();
    return result;
}

} // namespace forge
