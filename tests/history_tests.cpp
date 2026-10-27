// History update math (forge/history.hpp) against independent reference
// formulas: bonus shape, gravity saturation, killer shift, counter moves,
// butterfly / continuation (plies 1, 2 and half at 4) / capture updates.
#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace forge {
// The history rules are Worker members (src/search/history.inc); reach them
// and the tables through the usual test probe.
struct SearcherTestProbe {
    static HistoryTables& histories(Worker& w) { return w.histories_; }
    static int quiet_history(Worker& w, const Board& b, const SearchStack* ss, Move m) { return w.quiet_history(b, ss, m); }
    static int capture_history_value(Worker& w, const Board& b, Move m) { return w.capture_history_value(b, m); }
    static void update_continuation(Worker& w, SearchStack* ss, Piece p, int to, int bonus) { w.update_continuation(ss, p, to, bonus); }
    static void update_quiet_stats(Worker& w, const Board& b, SearchStack* ss, Move m, int depth, const Move* q, int n) {
        w.update_quiet_stats(b, ss, m, depth, q, n);
    }
    static void update_capture_stats(Worker& w, const Board& b, Move best, int depth, const Move* c, int n) {
        w.update_capture_stats(b, best, depth, c, n);
    }
};
} // namespace forge

using namespace forge;
using Probe = SearcherTestProbe;

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

Board position(const std::string& fen) {
    Board board;
    if (!board.set_fen(fen)) throw std::runtime_error("invalid fixture FEN: " + fen);
    return board;
}

Move uci(Board& board, const std::string& text) {
    const auto move = board.parse_uci(text);
    if (!move) throw std::runtime_error("illegal fixture move " + text);
    return *move;
}

int reference_bonus(int depth) {
    return std::min(tune::HistoryBonusMax, tune::HistoryBonusQuadratic * depth * depth + tune::HistoryBonusLinear * depth - 32);
}

std::int16_t reference_gravity(int entry, int bonus) {
    const int clamped = bonus < -16384 ? -16384 : (bonus > 16384 ? 16384 : bonus);
    // C++ integer division truncates toward zero.
    return static_cast<std::int16_t>(entry + clamped - entry * (clamped < 0 ? -clamped : clamped) / 16384);
}

void test_bonus_and_gravity() {
    for (int depth = -2; depth <= 40; ++depth) {
        check(history_bonus(depth) == reference_bonus(depth), "history_bonus depth " + std::to_string(depth));
    }
    // The bonus shape follows the tunables.
    const int quadratic = tune::HistoryBonusQuadratic, linear = tune::HistoryBonusLinear, maximum = tune::HistoryBonusMax;
    tune::HistoryBonusQuadratic = 7;
    tune::HistoryBonusLinear = 100;
    tune::HistoryBonusMax = 900;
    for (int depth = 0; depth <= 20; ++depth) {
        check(history_bonus(depth) == std::min(900, 7 * depth * depth + 100 * depth - 32),
              "history_bonus with tuned shape depth " + std::to_string(depth));
    }
    tune::HistoryBonusQuadratic = quadratic;
    tune::HistoryBonusLinear = linear;
    tune::HistoryBonusMax = maximum;
    check(HistoryMax == 16384, "HistoryMax is 16384");

    const std::array<int, 15> bonuses{0, 1, -1, 31, -31, 400, -400, 2048, -2048, 16384, -16384, 16385, -16385, 50000, -50000};
    bool exact = true;
    bool bounded = true;
    for (int entry = -HistoryMax; entry <= HistoryMax; entry += 37) {
        for (const int bonus : bonuses) {
            std::int16_t value = static_cast<std::int16_t>(entry);
            apply_history(value, bonus);
            exact &= value == reference_gravity(entry, bonus);
            bounded &= value >= -HistoryMax && value <= HistoryMax;
        }
    }
    check(exact, "apply_history matches the gravity formula on a grid");
    check(bounded, "apply_history keeps entries inside +/-HistoryMax");

    // Repeated rewards converge monotonically and never overshoot.
    std::int16_t up = 0, down = 0;
    bool monotonic = true;
    for (int i = 0; i < 20000; ++i) {
        const std::int16_t before_up = up, before_down = down;
        apply_history(up, 2048);
        apply_history(down, -2048);
        monotonic &= up >= before_up && down <= before_down && up <= HistoryMax && down >= -HistoryMax;
    }
    check(monotonic, "repeated +/-2048 bonuses are monotonic and saturate inside the bound");
    check(up > 16000 && down < -16000, "saturation approaches +/-HistoryMax");
}

struct Frames {
    std::array<SearchStack, 10> stack{};
    SearchStack* ss = &stack[6];
};

void test_quiet_stats() {
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    Worker& w = *worker;
    HistoryTables& h = Probe::histories(w);
    Board board = position("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4");
    const Move best = uci(board, "d2d3");
    const Move other1 = uci(board, "b1c3");
    const Move other2 = uci(board, "e1g1");
    const Move older_killer = uci(board, "a2a3");

    for (const int depth : {1, 4, 9, 13}) {
        h.clear();
        Frames f;
        SearchStack* ss = f.ss;
        ss->killers = {older_killer, Move::none()};
        // Previous moves: ply-1 knight to f6 (black), ply-2 a white move, ply-4 present, ply-3 absent.
        PieceToHistory& c1 = (*h.continuation_history)[BN][45];
        PieceToHistory& c2 = (*h.continuation_history)[WB][26];
        PieceToHistory& c3 = (*h.continuation_history)[BP][36];
        PieceToHistory& c4 = (*h.continuation_history)[WN][21];
        (ss - 1)->continuation = &c1; (ss - 1)->current_move = Move{62, 45, 0, 0}; (ss - 1)->moved_piece = BN;
        (ss - 2)->continuation = &c2; (ss - 2)->current_move = Move{5, 26, 0, 0}; (ss - 2)->moved_piece = WB;
        (ss - 3)->continuation = &c3; (ss - 3)->current_move = Move::none(); (ss - 3)->moved_piece = Empty;
        (ss - 4)->continuation = &c4; (ss - 4)->current_move = Move{6, 21, 0, 0}; (ss - 4)->moved_piece = WN;
        // Seed some existing values so gravity is exercised from non-zero entries.
        (*h.main_history)[White][best.from][best.to] = 1000;
        (*h.main_history)[White][other1.from][other1.to] = -700;
        c1[WP][best.to] = 3000;
        c4[WN][other1.to] = 5000;

        const int bonus = reference_bonus(depth);
        const auto main_best = (*h.main_history)[White][best.from][best.to];
        const auto main_o1 = (*h.main_history)[White][other1.from][other1.to];
        const auto main_o2 = (*h.main_history)[White][other2.from][other2.to];
        const auto c1_best = c1[WP][best.to], c2_best = c2[WP][best.to], c4_best = c4[WP][best.to];
        const auto c1_o1 = c1[WN][other1.to], c4_o1 = c4[WN][other1.to];
        const auto c3_snapshot = c3;
        const std::array<Move, 4> quiets{other1, best, other2, best}; // best appears twice: never penalised
        Probe::update_quiet_stats(w, board, ss, best, depth, quiets.data(), static_cast<int>(quiets.size()));

        const std::string d = " depth " + std::to_string(depth);
        check(ss->killers[0] == best && ss->killers[1] == older_killer, "killer shift" + d);
        check((*h.counter_moves)[BN][45] == best, "counter move stored under the previous piece/to" + d);
        check((*h.main_history)[White][best.from][best.to] == reference_gravity(main_best, bonus), "butterfly reward" + d);
        check((*h.main_history)[White][other1.from][other1.to] == reference_gravity(main_o1, -bonus), "butterfly penalty 1" + d);
        check((*h.main_history)[White][other2.from][other2.to] == reference_gravity(main_o2, -bonus), "butterfly penalty 2" + d);
        check(c1[WP][best.to] == reference_gravity(c1_best, bonus), "continuation ply-1 reward" + d);
        check(c2[WP][best.to] == reference_gravity(c2_best, bonus), "continuation ply-2 reward" + d);
        check(c4[WP][best.to] == reference_gravity(c4_best, bonus / 2), "continuation ply-4 half reward" + d);
        check(c1[WN][other1.to] == reference_gravity(c1_o1, -bonus), "continuation ply-1 penalty" + d);
        check(c4[WN][other1.to] == reference_gravity(c4_o1, -bonus / 2), "continuation ply-4 half penalty" + d);
        check(c3 == c3_snapshot, "ply-3 continuation untouched (and absent ply skipped)" + d);
    }

    // Same killer again: the killer pair is unchanged.
    {
        h.clear();
        Frames f;
        f.ss->killers = {best, older_killer};
        Probe::update_quiet_stats(w, board, f.ss, best, 5, nullptr, 0);
        check(f.ss->killers[0] == best && f.ss->killers[1] == older_killer, "repeated killer keeps the pair");
        // No previous move: no counter move is written anywhere.
        bool counters_empty = true;
        for (const auto& piece : *h.counter_moves)
            for (const Move move : piece) counters_empty &= move.is_none();
        check(counters_empty, "no counter move without a previous move");
    }
    // Null continuation pointers and missing previous moves are skipped safely.
    {
        h.clear();
        Frames f;
        PieceToHistory& c2 = (*h.continuation_history)[BQ][3];
        (f.ss - 2)->continuation = &c2;
        (f.ss - 2)->current_move = Move::none();
        Probe::update_continuation(w, f.ss, WP, best.to, 999);
        bool all_zero = true;
        for (const auto& piece : c2)
            for (const auto entry : piece) all_zero &= entry == 0;
        check(all_zero, "continuation of a ply without a move is not updated");
    }
}

void test_quiet_history_sum() {
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    Worker& w = *worker;
    HistoryTables& h = Probe::histories(w);
    Board board = position(std::string(Board::StandardStartFen));
    const Move move = uci(board, "g1f3");
    Frames f;
    (*h.main_history)[White][move.from][move.to] = 111;
    check(Probe::quiet_history(w, board, f.ss, move) == 111, "quiet history without continuations is the butterfly value");
    PieceToHistory& c1 = (*h.continuation_history)[BP][35];
    PieceToHistory& c2 = (*h.continuation_history)[WP][28];
    c1[WN][move.to] = -40;
    c2[WN][move.to] = 2500;
    (f.ss - 1)->continuation = &c1;
    check(Probe::quiet_history(w, board, f.ss, move) == 71, "butterfly + continuation(ply-1)");
    (f.ss - 2)->continuation = &c2;
    check(Probe::quiet_history(w, board, f.ss, move) == 2571, "butterfly + continuation(ply-1) + continuation(ply-2)");
    check(Probe::quiet_history(w, board, nullptr, move) == 111, "null stack uses only the butterfly value");
}

void test_capture_stats() {
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    Worker& w = *worker;
    HistoryTables& h = Probe::histories(w);
    Board board = position("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
    const Move best = uci(board, "e5f7");   // knight takes pawn
    const Move other = uci(board, "d5e6");  // pawn takes pawn
    const Move other2 = uci(board, "f3f6"); // queen takes knight
    for (const int depth : {2, 8}) {
        h.clear();
        (*h.capture_history)[WN][best.to][Pawn] = -3000;
        (*h.capture_history)[WQ][other2.to][Knight] = 9000;
        const int bonus = reference_bonus(depth);
        const std::array<Move, 3> tried{other, best, other2};
        Probe::update_capture_stats(w, board, best, depth, tried.data(), static_cast<int>(tried.size()));
        const std::string d = " depth " + std::to_string(depth);
        check((*h.capture_history)[WN][best.to][Pawn] == reference_gravity(-3000, bonus), "capture reward" + d);
        check((*h.capture_history)[WP][other.to][Pawn] == reference_gravity(0, -bonus), "capture penalty" + d);
        check((*h.capture_history)[WQ][other2.to][Knight] == reference_gravity(9000, -bonus), "capture penalty from seed" + d);
        check(Probe::capture_history_value(w, board, best) == (*h.capture_history)[WN][best.to][Pawn], "capture_history_value lookup" + d);
    }
    // A quiet best move only penalises the captures that were tried.
    h.clear();
    const Move quiet = uci(board, "a2a3");
    const std::array<Move, 1> tried{other};
    Probe::update_capture_stats(w, board, quiet, 6, tried.data(), 1);
    check((*h.capture_history)[WP][other.to][Pawn] == reference_gravity(0, -reference_bonus(6)), "quiet best: tried capture penalised");
    check((*h.capture_history)[WP][quiet.to][0] == 0, "quiet best: no capture reward");
}

} // namespace

int main() {
    test_bonus_and_gravity();
    test_quiet_stats();
    test_quiet_history_sum();
    test_capture_stats();
    std::cout << "history math: checks=" << checks << " failures=" << failures << '\n';
    std::cout << (failures == 0 ? "PASS" : "FAIL") << " history_tests\n";
    return failures == 0 ? 0 : 1;
}
