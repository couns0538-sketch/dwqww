// Stage-order contract of the staged move picker (src/search/movepicker.hpp).
// The picker output is compared with an independent reference built from the
// move generator, SEE and the history tables, over fixed positions with
// seeded random history contents, TT moves, killers and counter moves:
//   Main:       TT, good captures (SEE >= 0) by score, killer 1, killer 2,
//               counter, quiets by score, bad captures by score.
//   Quiescence: TT (captures/promotions only), captures by score.
//   Evasions:   TT, then every move by evasion score.
// Within a scored stage, equal scores may come in any order, so a stage is
// checked as a multiset with non-increasing scores.
#include "forge/search.hpp"
#include "search/movepicker.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace forge {
// The picker reads the worker's tables through Worker friendship; the test
// fills them through the usual test probe.
struct SearcherTestProbe {
    static HistoryTables& histories(Worker& worker) { return worker.histories_; }
};
} // namespace forge

using namespace forge;

namespace {

int failures = 0;
int checks = 0;

void check(bool okay, const std::string& name) {
    ++checks;
    if (!okay) {
        ++failures;
        if (failures <= 50) std::cout << "FAIL " << name << '\n';
    }
}

struct Rng {
    std::uint64_t state;
    std::uint64_t next() {
        state ^= state << 13U;
        state ^= state >> 7U;
        state ^= state << 17U;
        return state;
    }
    int range(int lo, int hi) { return lo + static_cast<int>(next() % static_cast<std::uint64_t>(hi - lo + 1)); }
};

Board position(const std::string& fen) {
    Board board;
    if (!board.set_fen(fen)) throw std::runtime_error("invalid fixture FEN: " + fen);
    return board;
}

std::string name_of(Move move) { return Board::move_to_uci(move); }

// Reference scores (the documented ordering keys).
int capture_score(const Board& board, const HistoryTables& h, Move move) {
    const int captured = piece_type(board.captured_piece(move));
    int value = SeePieceValue[static_cast<std::size_t>(captured)];
    if (move.is_promotion()) value += SeePieceValue[move.promotion] - SeePieceValue[Pawn];
    int score = 10 * value + (*h.capture_history)[static_cast<std::size_t>(board.moved_piece(move))][move.to][static_cast<std::size_t>(captured)];
    if (move.is_promotion()) score += move.promotion == Queen ? 20000 : -5000;
    return score;
}

bool direct_check(const Board& board, Move move) {
    const Color them = opposite(board.side_to_move());
    const int king = board.king_square(them);
    const Bitboard occupancy = board.occupied();
    Bitboard targets = 0;
    switch (piece_type(board.moved_piece(move))) {
    case Pawn: targets = attacks::pawn(them, king); break;
    case Knight: targets = attacks::knight(king); break;
    case Bishop: targets = attacks::bishop(king, occupancy); break;
    case Rook: targets = attacks::rook(king, occupancy); break;
    case Queen: targets = attacks::bishop(king, occupancy) | attacks::rook(king, occupancy); break;
    default: break;
    }
    return (targets & square_bb(move.to)) != 0;
}

int quiet_score(const Board& board, const HistoryTables& h, const SearchStack* ss, Move move) {
    const Piece piece = board.moved_piece(move);
    int score = (*h.main_history)[static_cast<std::size_t>(board.side_to_move())][move.from][move.to];
    if ((ss - 1)->continuation != nullptr) score += (*(ss - 1)->continuation)[static_cast<std::size_t>(piece)][move.to];
    if ((ss - 2)->continuation != nullptr) score += (*(ss - 2)->continuation)[static_cast<std::size_t>(piece)][move.to];
    return score + (direct_check(board, move) ? 12000 : 0);
}

int evasion_score(const Board& board, const HistoryTables& h, const SearchStack* ss, Move move) {
    if (move.is_capture() || move.is_promotion()) {
        int value = SeePieceValue[static_cast<std::size_t>(piece_type(board.captured_piece(move)))];
        if (move.is_promotion()) value += SeePieceValue[move.promotion] - SeePieceValue[Pawn];
        return 1'000'000 + 10 * value - SeePieceValue[static_cast<std::size_t>(piece_type(board.moved_piece(move)))] / 10;
    }
    return quiet_score(board, h, ss, move);
}

std::vector<Move> generate(const Board& board, bool captures_only) {
    MoveList list;
    board.generate_pseudo_legal(list, captures_only);
    return {list.begin(), list.end()};
}

struct Stage {
    std::string name;
    bool scored = false;          // multiset + non-increasing score, else exact order
    bool see_nonnegative = false; // expected last_move_see_nonnegative() for its moves
    std::vector<Move> moves;
    std::map<std::uint32_t, int> scores;
};

std::uint32_t key(Move move) {
    return static_cast<std::uint32_t>(move.from) | static_cast<std::uint32_t>(move.to) << 8U |
           static_cast<std::uint32_t>(move.promotion) << 16U | static_cast<std::uint32_t>(move.flags) << 24U;
}

struct Pick {
    Move move;
    bool see_nonnegative;
};

std::vector<Pick> run_picker(const Board& board, const Worker& worker, const SearchStack* ss, Move tt,
                             MovePicker::Mode mode, int skip_after) {
    MovePicker picker(board, worker, ss, tt, mode);
    std::vector<Pick> out;
    for (int i = 0; i < 600; ++i) {
        const Move move = picker.next(skip_after >= 0 && i >= skip_after);
        if (move.is_none()) return out;
        out.push_back({move, picker.last_move_see_nonnegative()});
    }
    throw std::runtime_error("move picker did not terminate");
}

void compare(const std::vector<Pick>& actual, const std::vector<Stage>& stages, const std::string& label) {
    std::size_t at = 0;
    for (const Stage& stage : stages) {
        if (stage.moves.empty()) continue;
        const std::string where = label + " stage " + stage.name;
        if (at + stage.moves.size() > actual.size()) {
            check(false, where + ": picker returned too few moves");
            return;
        }
        std::vector<std::uint32_t> got;
        std::vector<std::uint32_t> want;
        for (std::size_t i = 0; i < stage.moves.size(); ++i) {
            const Pick& pick = actual[at + i];
            got.push_back(key(pick.move));
            want.push_back(key(stage.moves[i]));
            check(pick.see_nonnegative == stage.see_nonnegative, where + ": see flag of " + name_of(pick.move));
        }
        if (stage.scored) {
            for (std::size_t i = 1; i < stage.moves.size(); ++i) {
                const auto prev = stage.scores.find(got[i - 1]);
                const auto curr = stage.scores.find(got[i]);
                if (prev != stage.scores.end() && curr != stage.scores.end()) {
                    check(prev->second >= curr->second, where + ": scores non-increasing at " + std::to_string(i));
                }
            }
            std::sort(got.begin(), got.end());
            std::sort(want.begin(), want.end());
        }
        check(got == want, where + ": move set/order");
        at += stage.moves.size();
    }
    check(at == actual.size(), label + ": no extra moves (" + std::to_string(actual.size()) + " vs " + std::to_string(at) + ")");
}

std::vector<Stage> expected_main(const Board& board, const HistoryTables& h, const SearchStack* ss, Move tt,
                                 bool skip_quiets) {
    if (!tt.is_none() && !board.is_pseudo_legal(tt)) tt = Move::none();
    Stage tt_stage{"tt", false, false, {}, {}};
    if (!tt.is_none()) tt_stage.moves.push_back(tt);

    std::vector<std::pair<int, Move>> captures;
    for (const Move move : generate(board, true)) {
        if (move == tt) continue;
        captures.emplace_back(capture_score(board, h, move), move);
    }
    std::stable_sort(captures.begin(), captures.end(), [](const auto& a, const auto& b) { return a.first > b.first; });
    Stage good{"good-captures", true, true, {}, {}};
    Stage bad{"bad-captures", true, false, {}, {}};
    for (const auto& [score, move] : captures) {
        Stage& target = board.see_ge(move, 0) ? good : bad;
        target.moves.push_back(move);
        target.scores[key(move)] = score;
    }

    const std::array<Move, 2> killers = ss->killers;
    Move counter = Move::none();
    const SearchStack* previous = ss - 1;
    if (!previous->current_move.is_none() && previous->moved_piece != Empty) {
        counter = (*h.counter_moves)[static_cast<std::size_t>(previous->moved_piece)][previous->current_move.to];
    }
    auto valid_quiet = [&](Move move) {
        return !move.is_none() && move != tt && !move.is_capture() && !move.is_promotion() && board.is_pseudo_legal(move);
    };
    Stage specials{"killers-counter", false, false, {}, {}};
    Stage quiets{"quiets", true, false, {}, {}};
    if (!skip_quiets) {
        if (valid_quiet(killers[0])) specials.moves.push_back(killers[0]);
        if (valid_quiet(killers[1]) && killers[1] != killers[0]) specials.moves.push_back(killers[1]);
        if (valid_quiet(counter) && counter != killers[0] && counter != killers[1]) specials.moves.push_back(counter);
        for (const Move move : generate(board, false)) {
            if (move.is_capture() || move.is_promotion()) continue;
            if (move == tt || move == killers[0] || move == killers[1] || move == counter) continue;
            quiets.moves.push_back(move);
            quiets.scores[key(move)] = quiet_score(board, h, ss, move);
        }
    }
    return {tt_stage, good, specials, quiets, bad};
}

std::vector<Stage> expected_qsearch(const Board& board, const HistoryTables& h, Move tt) {
    if (!tt.is_none() && !board.is_pseudo_legal(tt)) tt = Move::none();
    if (!tt.is_none() && !tt.is_capture() && !tt.is_promotion()) tt = Move::none();
    Stage tt_stage{"qs-tt", false, false, {}, {}};
    if (!tt.is_none()) tt_stage.moves.push_back(tt);
    Stage captures{"qs-captures", true, false, {}, {}};
    for (const Move move : generate(board, true)) {
        if (move == tt) continue;
        captures.moves.push_back(move);
        captures.scores[key(move)] = capture_score(board, h, move);
    }
    return {tt_stage, captures};
}

std::vector<Stage> expected_evasions(const Board& board, const HistoryTables& h, const SearchStack* ss, Move tt) {
    if (!tt.is_none() && !board.is_pseudo_legal(tt)) tt = Move::none();
    Stage tt_stage{"evasion-tt", false, false, {}, {}};
    if (!tt.is_none()) tt_stage.moves.push_back(tt);
    Stage moves{"evasions", true, false, {}, {}};
    for (const Move move : generate(board, false)) {
        if (move == tt) continue;
        moves.moves.push_back(move);
        moves.scores[key(move)] = evasion_score(board, h, ss, move);
    }
    return {tt_stage, moves};
}

Move random_move(Rng& rng, const std::vector<Move>& pool) {
    const int pick = rng.range(0, 9);
    if (pick == 0 || pool.empty()) {
        // Garbage that is (almost always) not pseudo-legal here.
        Move move{};
        move.from = static_cast<std::uint8_t>(rng.range(0, 63));
        move.to = static_cast<std::uint8_t>(rng.range(0, 63));
        move.flags = static_cast<std::uint8_t>(rng.range(0, 1));
        return move;
    }
    if (pick == 1) return Move::none();
    return pool[static_cast<std::size_t>(rng.range(0, static_cast<int>(pool.size()) - 1))];
}

void randomize(Rng& rng, HistoryTables& h, bool zero) {
    h.clear();
    if (zero) return;
    for (auto& side : *h.main_history)
        for (auto& from : side)
            for (auto& entry : from) entry = static_cast<std::int16_t>(rng.range(-HistoryMax, HistoryMax));
    for (auto& piece : *h.capture_history)
        for (auto& to : piece)
            for (auto& entry : to) entry = static_cast<std::int16_t>(rng.range(-HistoryMax, HistoryMax));
}

void randomize_continuation(Rng& rng, PieceToHistory& table) {
    for (auto& piece : table)
        for (auto& entry : piece) entry = static_cast<std::int16_t>(rng.range(-HistoryMax, HistoryMax));
}

} // namespace

int main() {
    const std::vector<std::string> fens{
        std::string(Board::StandardStartFen),
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1",
        "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N w - - 0 1",
        "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",
        "rnbqkbnr/ppp2ppp/8/1B1pp3/4P3/8/PPPP1PPP/RNBQK1NR b KQkq - 1 3",
        "4k3/8/8/8/8/8/4r3/4K3 w - - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    };
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    const Worker& w = *worker;
    HistoryTables& h = SearcherTestProbe::histories(*worker);
    std::array<SearchStack, 8> stack{};
    SearchStack* ss = &stack[4];
    Rng rng{0x9E3779B97F4A7C15ULL};
    int evasion_positions = 0;
    int main_runs = 0;
    int qs_runs = 0;
    int evasion_runs = 0;

    for (const std::string& fen : fens) {
        const Board board = position(fen);
        const std::vector<Move> all = generate(board, false);
        const std::vector<Move> captures = generate(board, true);
        std::vector<Move> pool = all;
        pool.insert(pool.end(), captures.begin(), captures.end());
        if (board.in_check()) ++evasion_positions;
        for (int trial = 0; trial < 60; ++trial) {
            const std::string label = fen + " trial " + std::to_string(trial);
            randomize(rng, h, trial % 4 == 0);
            for (SearchStack& entry : stack) entry = SearchStack{};
            // Continuation tables of the two previous plies (sometimes absent).
            if (trial % 3 != 0) {
                ss[-1].continuation = &(*h.continuation_history)[WN][static_cast<std::size_t>(rng.range(0, 63))];
                ss[-2].continuation = &(*h.continuation_history)[BQ][static_cast<std::size_t>(rng.range(0, 63))];
                randomize_continuation(rng, *ss[-1].continuation);
                randomize_continuation(rng, *ss[-2].continuation);
            }
            ss->killers = {random_move(rng, pool), random_move(rng, pool)};
            if (trial % 5 == 1) ss->killers[1] = ss->killers[0];
            // Previous move for the counter-move slot, and a counter move in it.
            if (trial % 2 == 0) {
                ss[-1].current_move = random_move(rng, pool);
                ss[-1].moved_piece = static_cast<Piece>(rng.range(1, 12));
                if (!ss[-1].current_move.is_none()) {
                    (*h.counter_moves)[static_cast<std::size_t>(ss[-1].moved_piece)][ss[-1].current_move.to] = random_move(rng, pool);
                }
            }
            const Move tt = trial % 7 == 3 ? Move::none() : random_move(rng, pool);

            if (board.in_check()) {
                compare(run_picker(board, w, ss, tt, MovePicker::Mode::Main, -1), expected_evasions(board, h, ss, tt),
                        label + " evasions/main");
                compare(run_picker(board, w, ss, tt, MovePicker::Mode::Quiescence, -1), expected_evasions(board, h, ss, tt),
                        label + " evasions/qs");
                evasion_runs += 2;
                continue;
            }
            compare(run_picker(board, w, ss, tt, MovePicker::Mode::Main, -1), expected_main(board, h, ss, tt, false),
                    label + " main");
            compare(run_picker(board, w, ss, tt, MovePicker::Mode::Main, 0), expected_main(board, h, ss, tt, true),
                    label + " main skip_quiets");
            compare(run_picker(board, w, ss, tt, MovePicker::Mode::Quiescence, -1), expected_qsearch(board, h, tt),
                    label + " qsearch");
            main_runs += 2;
            ++qs_runs;
        }
    }

    // A quiet TT move is dropped in quiescence; a non pseudo-legal TT move is dropped everywhere.
    {
        Board board = position(std::string(Board::StandardStartFen));
        for (SearchStack& entry : stack) entry = SearchStack{};
        h.clear();
        const Move quiet = *board.parse_uci("g1f3");
        MovePicker qs(board, w, ss, quiet, MovePicker::Mode::Quiescence);
        check(qs.next(false).is_none(), "quiet TT move is not searched in quiescence at the start position");
        Move bogus{};
        bogus.from = 0;  // a1 rook to a5 through its own pawn
        bogus.to = 32;
        MovePicker main(board, w, ss, bogus, MovePicker::Mode::Main);
        bool returned = false;
        for (Move move; !(move = main.next(false)).is_none();) returned |= move == bogus;
        check(!returned, "non pseudo-legal TT move is never returned");
    }
    // Mid-stage skip: quiets generated, then skipped -> only bad captures remain.
    {
        const Board board = position("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
        for (SearchStack& entry : stack) entry = SearchStack{};
        randomize(rng, h, false);
        const std::vector<Stage> stages = expected_main(board, h, ss, Move::none(), false);
        const std::size_t first_quiet = stages[0].moves.size() + stages[1].moves.size() + stages[2].moves.size() + 1;
        const std::vector<Pick> picks = run_picker(board, w, ss, Move::none(), MovePicker::Mode::Main,
                                                   static_cast<int>(first_quiet));
        check(picks.size() == first_quiet + stages[4].moves.size(), "skip during quiet stage jumps to bad captures");
    }

    check(evasion_positions >= 2, "fixture set contains evasion positions");
    std::cout << "movepicker contract: positions=" << fens.size() << " main_runs=" << main_runs << " qs_runs=" << qs_runs
              << " evasion_runs=" << evasion_runs << " checks=" << checks << " failures=" << failures << '\n';
    std::cout << (failures == 0 ? "PASS" : "FAIL") << " movepicker_tests\n";
    return failures == 0 ? 0 : 1;
}
