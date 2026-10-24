// Original output-layer boundary check for the user's locked H256 weights.
// Synthetic accumulators are not FEN-parity positions or playing evidence.
#include "forge/nnue.hpp"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include "../src/nnue_weights.inc"

int main() {
    using namespace forge;
    Board board;
    if (!board.set_fen(Board::StandardStartFen) || !nnue::set_int16(true)) return 2;
    bool passed = true;
    for (const bool positive : {true, false}) {
        nnue::Accumulator integer, floating;
        integer.valid = floating.valid = true;
        integer.integer = true;
        std::int64_t total = 0;
        for (int side = 0; side < 2; ++side) {
            for (int h = 0; h < nnue::HiddenSize; ++h) {
                const auto weight = NnueW2[side * nnue::HiddenSize + h];
                const bool selected = positive ? weight > 0 : weight < 0;
                integer.integer_values[static_cast<std::size_t>(side)][static_cast<std::size_t>(h)] = selected ? 4096 : 0;
                floating.values[static_cast<std::size_t>(side)][static_cast<std::size_t>(h)] = selected ? 1.0F : 0.0F;
                if (selected) total += static_cast<std::int64_t>(weight) * 8192;
            }
        }
        const double exact = (static_cast<double>(total) / 33554432.0 + static_cast<double>(NnueB2) / 4096.0) * 400.0 / 2.25;
        const int expected = static_cast<int>(std::clamp(exact, -30000.0, 30000.0));
        const int actual = nnue::evaluate(board, integer);
        const int reference = nnue::evaluate(board, floating);
        const bool exceeds = total > std::numeric_limits<std::int32_t>::max() || total < std::numeric_limits<std::int32_t>::min();
        const bool ok = exceeds && actual == expected && std::abs(actual - reference) <= 2;
        passed = passed && ok;
        std::cout << "{\"case\":\"" << (positive ? "positive" : "negative")
                  << "\",\"total_i64\":" << total << ",\"exceeds_int32\":" << (exceeds ? "true" : "false")
                  << ",\"integer_cp\":" << actual << ",\"oracle_cp\":" << expected
                  << ",\"float_cp\":" << reference << ",\"result\":\"" << (ok ? "PASS" : "FAIL") << "\"}\n";
    }
    return passed ? 0 : 1;
}
