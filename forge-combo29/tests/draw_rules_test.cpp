// Repetition, 50-move horizon, insufficient material, and TT clock checks.
// Build: cmake --build <build> --target draw_rules_test
#include "forge/search.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <string_view>

namespace {

int failures = 0;

void expect(bool condition, std::string_view name) {
    if (condition) return;
    std::cerr << "FAIL " << name << '\n';
    ++failures;
}

void play(forge::Board& board, std::string_view uci) {
    const auto move = board.parse_uci(uci);
    if (!move) {
        std::cerr << "illegal " << uci << " in " << board.fen() << '\n';
        std::exit(2);
    }
    forge::Undo undo;
    (void)board.make_move(*move, undo);
}

// Knight shuttle: start, then Nf3 Nf6 Ng1 Ng8, repeated `cycles` times.
void shuttle(forge::Board& board, int cycles) {
    for (int n = 0; n < cycles; ++n) {
        play(board, "g1f3");
        play(board, "g8f6");
        play(board, "f3g1");
        play(board, "f6g8");
    }
}

void test_repetition() {
    using forge::Board;
    Board game;
    const std::size_t root = game.history_size() - 1;
    shuttle(game, 1);
    expect(!game.is_repetition(), "twofold is not a game draw");
    expect(!game.is_repetition(root), "twofold of the root is not a search draw");
    shuttle(game, 1);
    expect(game.is_repetition(), "threefold is a game draw");
    expect(game.is_repetition(root), "threefold of the root is a search draw");

    Board inner;
    const std::size_t inner_root = inner.history_size() - 1;
    play(inner, "g1f3");
    play(inner, "b8c6");
    play(inner, "f3g1");
    play(inner, "c6b8");
    expect(!inner.is_repetition(inner_root), "returning only to the root is twofold");
    play(inner, "g1f3");
    expect(inner.is_repetition(inner_root), "repeating a position reached after the root is a draw");

    // Two occurrences of the start position are already on the board before
    // the root. The third visit, with no copy after the root, is a draw.
    Board before;
    shuttle(before, 1);
    play(before, "g1f3");
    const std::size_t before_root = before.history_size() - 1;
    play(before, "g8f6");
    play(before, "f3g1");
    play(before, "f6g8");
    expect(before.is_repetition(), "third visit is a game draw");
    expect(before.is_repetition(before_root), "third visit counts two copies at or before the root");

    Board reset;
    shuttle(reset, 1);
    play(reset, "e2e4");
    expect(reset.halfmove_clock() == 0, "pawn move resets the 50-move clock");
    expect(!reset.is_repetition(), "pawn move breaks the repetition window");
    expect(!reset.is_repetition(0), "search repetition does not cross the pawn move");
}

void test_null_move_clock() {
    forge::Board board;
    expect(board.set_fen("8/8/4k3/8/8/3K4/8/8 w - - 99 40"), "null-move fen");
    const int clock = board.halfmove_clock();
    const auto root = board.history_size() - 1;
    forge::NullUndo undo;
    board.make_null_move(undo);
    expect(board.halfmove_clock() == clock, "null move does not advance the 50-move clock");
    expect(board.side_to_move() == forge::Black, "null move passes the turn");
    expect(!board.is_repetition(root), "null move blocks repetition through plies_from_null");
    board.unmake_null_move(undo);
    expect(board.halfmove_clock() == clock, "unmake restores the 50-move clock");
    expect(board.side_to_move() == forge::White, "unmake restores the side to move");

    // The null move clears the span, so the twofold already on the board is not
    // visible. A later cycle that stays after the null is an ordinary search draw.
    forge::Board crossed;
    shuttle(crossed, 1);
    const auto crossed_root = crossed.history_size() - 1;
    forge::NullUndo crossed_undo;
    crossed.make_null_move(crossed_undo);
    expect(!crossed.is_repetition(crossed_root), "a null move clears the search repetition span");
    play(crossed, "g8f6");
    play(crossed, "g1f3");
    play(crossed, "f6g8");
    play(crossed, "f3g1");
    expect(crossed.is_repetition(crossed_root), "a cycle after the null is still a search draw");
}

void test_insufficient_material() {
    const struct {
        const char* fen;
        bool draw;
        const char* name;
    } cases[] = {
        {"8/8/4k3/8/8/3K4/8/8 w - - 0 1", true, "K vs K"},
        {"8/8/4k3/8/8/3KN3/8/8 w - - 0 1", true, "KN vs K"},
        {"8/8/4k3/8/8/3KB3/8/8 w - - 0 1", true, "KB vs K"},
        {"k4b2/8/8/8/8/8/8/2B4K w - - 0 1", true, "same-color bishops"},
        {"k1b5/8/8/8/8/8/8/2B4K w - - 0 1", false, "opposite-color bishops"},
        {"7k/8/8/8/8/8/4B1B1/4K3 w - - 0 1", true, "two bishops on one color"},
        {"7k/8/8/8/8/8/6B1/4K1B1 w - - 0 1", false, "two bishops on both colors"},
        {"8/8/4k3/8/8/2NNK3/8/8 w - - 0 1", false, "KNN vs K can mate"},
        {"8/8/4k3/8/8/2NBK3/8/8 w - - 0 1", false, "KBN vs K is a win"},
        {"8/8/4k3/8/8/3KN3/6b1/8 w - - 0 1", false, "KB vs KN"},
        {"8/8/4k3/8/8/3K1R2/8/8 w - - 99 80", false, "KR vs K has mating material"},
        {"8/8/4k3/8/4p3/3K4/8/8 w - - 0 1", false, "a pawn is mating material"},
    };
    for (const auto& item : cases) {
        forge::Board board;
        std::string error;
        expect(board.set_fen(item.fen, &error), item.name);
        expect(board.is_insufficient_material() == item.draw, item.name);
    }
}

void test_tt_horizon() {
    using forge::MateValue;
    using forge::ValueNone;
    using forge::score_from_tt;
    // Mate in 1 is one ply. It still wins on the move that makes the clock 100.
    expect(score_from_tt(MateValue - 1, 0, 99) == MateValue - 1, "mate in 1 at clock 99 stands");
    expect(score_from_tt(MateValue - 1, 3, 99) == MateValue - 1 - 3, "mate in 1 keeps its ply adjustment");
    expect(score_from_tt(MateValue - 1, 0, 100) == ValueNone, "mate in 1 at clock 100 is not playable");
    // Distance 20 fits in the 20 plies left at clock 80; distance 21 does not.
    expect(score_from_tt(MateValue - 20, 0, 80) == MateValue - 20, "mate on the horizon ply stands");
    expect(score_from_tt(MateValue - 21, 0, 80) == ValueNone, "mate past the horizon is refused");
    expect(score_from_tt(-MateValue + 21, 4, 80) == ValueNone, "loss past the horizon is refused");
    expect(score_from_tt(-MateValue, 4, 99) == -MateValue + 4, "checkmate already on the board stands");
    expect(score_from_tt(30, 2, 99) == 30, "a non-mate score is not a horizon decision");

    forge::TTEntry shallow;
    shallow.depth = 8;
    shallow.rule50_clock = 0;
    shallow.gen_bound = forge::BoundExact;
    expect(shallow.score_usable(50, 8), "both searches finish before the horizon");
    expect(shallow.score_usable(89, 8), "clock 89 depth 8 still finishes at 97");

    forge::TTEntry deep;
    deep.depth = 20;
    deep.rule50_clock = 0;
    deep.gen_bound = forge::BoundExact;
    expect(!deep.score_usable(89, 20), "clock 0 depth 20 must not answer clock 89 depth 20");
    expect(!deep.score_usable(89, 0), "a deep clock-0 score must not answer qsearch at clock 89");

    forge::TTEntry same;
    same.depth = 20;
    same.rule50_clock = 89;
    same.gen_bound = forge::BoundExact;
    expect(same.score_usable(89, 20), "the same clock can cross the horizon");
    expect(!same.score_usable(80, 20), "a different clock that also reaches the horizon cannot");

    forge::TTEntry blind;
    blind.depth = 5;
    blind.rule50_clock = 89;
    blind.gen_bound = forge::BoundLower;
    expect(!blind.score_usable(89, 20), "a short search at clock 89 must not answer a longer one");
}

} // namespace

int main() {
    test_repetition();
    test_null_move_clock();
    test_insufficient_material();
    test_tt_horizon();
    if (failures != 0) {
        std::cerr << failures << " failed\n";
        return 1;
    }
    std::cout << "draw_rules_test passed\n";
    return 0;
}
