#pragma once

// Search module: staged move picker.
//   Main:       TT move, good captures (SEE >= 0, MVV + capture history),
//               killer 1, killer 2, counter move, quiets (history + direct
//               check bonus), bad captures.
//   Quiescence: TT move (captures/promotions only), captures.
//   Evasions:   TT move, then every move (captures first).
// The picker scores moves with the worker's history rules (Worker::quiet_history,
// Worker::capture_history_value) and reads its counter-move table, through its
// friendship with Worker (as in AL1 s198, which keeps the code generation).
// Included by src/search.cpp and by tests/movepicker_tests.cpp.

#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <cstddef>

namespace forge {

// Material gained by a capture or promotion, in SEE units.
[[nodiscard]] inline int capture_value(const Board& board, Move move) {
    int value = SeePieceValue[static_cast<std::size_t>(piece_type(board.captured_piece(move)))];
    if (move.is_promotion()) value += SeePieceValue[move.promotion] - SeePieceValue[Pawn];
    return value;
}

class MovePicker {
public:
    enum class Mode { Main, Quiescence };

    MovePicker(const Board& board, const Worker& searcher, const SearchStack* ss, Move tt_move, Mode mode)
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
                counter_ = (*searcher_.histories_.counter_moves)[static_cast<std::size_t>(previous->moved_piece)][previous->current_move.to];
            }
        }
    }

    // Emitted out of line as a COMDAT, which the PE linker places after every
    // object's .text: pin it to a 64-byte boundary (its AL1 s198 placement) so
    // its alignment does not depend on the size of other translation units.
    [[nodiscard, gnu::aligned(64)]] Move next(bool skip_quiets) {
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

    // Valid for the move just returned by next(), until the next next() call.
    // Only Main/GoodCaptures returns after a successful SEE >= 0 test.
    [[nodiscard]] bool last_move_see_nonnegative() const { return stage_ == GoodCaptures; }

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
    const Worker& searcher_;
    const SearchStack* ss_;
    Move tt_move_;
    std::array<Move, 2> killers_{};
    Move counter_{};
    Stage stage_;
#if FORGE_NOZERO_MOVE_BUFFERS
    UninitArray<Scored, 256> moves_;  // only [0, count_) is ever read
#else
    std::array<Scored, 256> moves_{};
#endif
    std::size_t index_ = 0;
    std::size_t count_ = 0;
#if FORGE_NOZERO_MOVE_BUFFERS
    UninitArray<Move, 64> bad_captures_;  // only [0, bad_count_) is ever read
#else
    std::array<Move, 64> bad_captures_{};
#endif
    std::size_t bad_count_ = 0;
    std::size_t bad_index_ = 0;
    MoveList buffer_;
    std::size_t list_start_ = 0;
    bool sorted_ = false;
    std::array<Bitboard, 7> check_squares_{};

    // Quiet/evasion generation are mutually exclusive stages, each reached at most once.
    void init_check_squares() {
        const Color them = opposite(board_.side_to_move());
        const int enemy_king = board_.king_square(them);
        const Bitboard occupancy = board_.occupied();
        check_squares_[Pawn] = attacks::pawn(them, enemy_king);
        check_squares_[Knight] = attacks::knight(enemy_king);
        check_squares_[Bishop] = attacks::bishop(enemy_king, occupancy);
        check_squares_[Rook] = attacks::rook(enemy_king, occupancy);
        check_squares_[Queen] = check_squares_[Bishop] | check_squares_[Rook];
        check_squares_[King] = 0;
    }

    [[nodiscard]] bool direct_check(Move move) const {
        const int type = piece_type(board_.moved_piece(move));
        return (check_squares_[static_cast<std::size_t>(type)] & square_bb(move.to)) != 0;
    }

    [[nodiscard]] static int move_score_threshold(Move) { return 0; }

    [[nodiscard]] bool is_valid_quiet(Move move) const {
        return !move.is_none() && move != tt_move_ && !move.is_capture() && !move.is_promotion() &&
               board_.is_pseudo_legal(move);
    }

    // Most nodes need only the first few moves: select those on demand and
    // sort the remainder once if the search gets that far.
    [[nodiscard]] Move pick_best() {
        if (!sorted_) {
            if (index_ - list_start_ < 4) {
                std::size_t best = index_;
                for (std::size_t i = index_ + 1; i < count_; ++i) {
                    if (moves_[i].score > moves_[best].score) best = i;
                }
                std::swap(moves_[index_], moves_[best]);
            } else {
                std::sort(moves_.begin() + static_cast<std::ptrdiff_t>(index_), moves_.begin() + static_cast<std::ptrdiff_t>(count_),
                          [](const Scored& a, const Scored& b) { return a.score > b.score; });
                sorted_ = true;
            }
        }
        return moves_[index_++].move;
    }

    void sort_moves() {
        list_start_ = index_;
        sorted_ = false;
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
        init_check_squares();
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
        init_check_squares();
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

} // namespace forge
