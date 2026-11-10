// Test-only inclusion exposes the internal scoring helpers without production hooks.
#include "../src/search.cpp"
#include <cstdlib>

int main() {
#if !FORGE_EXPERIMENT_CONTINUATION4
#error This test requires the opt-in experiment.
#endif
    using namespace forge;
    auto require = [](bool value) { if (!value) std::abort(); };
    PieceToHistory history{};
    SearchStack stack[5]{};
    SearchStack* ss = stack + 4;
    const Move move{12, 20};
    const Piece piece = WP;
    history[static_cast<std::size_t>(piece)][move.to] = -101;
    stack[0].continuation = &history;
    tune::Continuation4Weight = 100;
    require(continuation4_context(nullptr) == nullptr);
    require(continuation4_context(ss) == nullptr); // Sentinel/null predecessor.
    stack[0].current_move = move;
    require(continuation4_context(ss) == &history);
    require(continuation4_bonus(&history, piece, move) == -101);
    tune::Continuation4Weight = 50;
    require(continuation4_bonus(&history, piece, move) == -50);
    require(continuation4_bonus(nullptr, piece, move) == 0);
    tune::Continuation4Weight = 0;
    require(continuation4_context(ss) == nullptr);
    require(continuation4_bonus(&history, piece, move) == 0);
#if FORGE_SEARCH_SPEED2
    std::array<std::array<std::int16_t, 64>, 64> main{};
    main[move.from][move.to] = 9;
    tune::Continuation4Weight = 100;
    require(quiet_history_sum(main, &history, &history, piece, move, nullptr) == -193);
    require(quiet_history_sum(main, &history, &history, piece, move, &history) == -294);
#endif
    std::cout << "continuation4 helper tests PASS\n";
}
