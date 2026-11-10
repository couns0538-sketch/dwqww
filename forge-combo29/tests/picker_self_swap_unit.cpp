#include "forge/search.hpp"
#include "forge/uci_output.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <exception>
#include <iostream>
#include <limits>
#include <optional>
// The implementation-local picker is exposed only in this test translation
// unit. Preload production dependencies so their access control is unchanged.
#define private public
#include "search.cpp"
#undef private
#include <bit>
#include <cstdlib>
#include <random>

using namespace forge;
using Scored = MovePicker::Scored;
static_assert(sizeof(Move) == 4 && sizeof(Scored) == 8);
std::uint64_t fixtures = 0, calls = 0;
void require(bool condition, const char* message) {
    if (!condition) { std::cerr << "FAIL: " << message << " fixture=" << fixtures << " call=" << calls << '\n'; std::exit(1); }
}
void check(const Board& board, const Worker& worker, const std::vector<int>& scores,
           std::size_t prefix, std::size_t consumed = 0, bool already_sorted = false) {
    MovePicker picker(board, worker, nullptr, Move::none(), MovePicker::Mode::Main);
    std::array<Scored, 256> expected;
    for (std::size_t i = 0; i < expected.size(); ++i) {
        expected[i] = {std::bit_cast<Move>(static_cast<std::uint32_t>(0xA53C0000U + i)),
                       static_cast<int>(1000000 + i)};
    }
    for (std::size_t i = 0; i < scores.size(); ++i) expected[prefix + i].score = scores[i];
    picker.moves_ = expected;
    picker.index_ = prefix + consumed;
    picker.count_ = prefix + scores.size();
    picker.list_start_ = prefix;
    picker.sorted_ = already_sorted;
    auto index = picker.index_;
    bool sorted = already_sorted;
    while (index < picker.count_) {
        // Verbatim locked ordering policy: strict >, first four selections,
        // unconditional swap, same std::sort comparator for the remainder.
        if (!sorted) {
            if (index - prefix < 4) {
                std::size_t best = index;
                for (std::size_t i = index + 1; i < picker.count_; ++i)
                    if (expected[i].score > expected[best].score) best = i;
                std::swap(expected[index], expected[best]);
            } else {
                std::sort(expected.begin() + static_cast<std::ptrdiff_t>(index),
                          expected.begin() + static_cast<std::ptrdiff_t>(picker.count_),
                          [](const Scored& a, const Scored& b) { return a.score > b.score; });
                sorted = true;
            }
        }
        const Move want = expected[index++].move;
        const Move actual = picker.pick_best();
        ++calls;
        require(std::bit_cast<std::uint32_t>(actual) == std::bit_cast<std::uint32_t>(want), "Returned move/order changed");
        require(picker.index_ == index && picker.sorted_ == sorted, "Picker state changed");
        // Includes every score/move byte plus untouched prefix and suffix.
        require(std::memcmp(picker.moves_.data(), expected.data(), sizeof(expected)) == 0, "Scored data/prefix/suffix differs");
    }
    ++fixtures;
}
int main() {
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    Board board;
    for (std::size_t n = 1; n <= 8; ++n) {
        std::size_t cases = 1;
        for (std::size_t i = 0; i < n; ++i) cases *= 3;
        for (std::size_t code = 0; code < cases; ++code) {
            std::size_t digits = code;
            std::vector<int> scores(n);
            for (int& score : scores) { score = static_cast<int>(digits % 3) - 1; digits /= 3; }
            for (std::size_t prefix : {0U, 7U, 128U}) check(board, *worker, scores, prefix);
        }
    }
    // Explicit array-boundary fixtures, independent of random coverage.
    for (std::size_t n : {1U, 4U, 5U, 255U, 256U}) {
        std::vector<int> scores(n, 0);
        check(board, *worker, scores, 0);
        for (std::size_t i = 0; i < n; ++i) scores[i] = static_cast<int>(i);
        check(board, *worker, scores, 0);
        for (std::size_t i = 0; i < n; ++i) scores[i] = -static_cast<int>(i);
        check(board, *worker, scores, 0);
    }
    check(board, *worker, std::vector<int>{0}, 255);
    constexpr std::uint32_t Seed = 20261110;
    std::mt19937 rng(Seed);
    for (int trial = 0; trial < 1000; ++trial) {
        const std::size_t prefix = rng() % 32;
        const std::size_t n = 1 + rng() % (256 - prefix);
        std::vector<int> scores(n);
        for (std::size_t i = 0; i < n; ++i) {
            switch (trial % 6) {
            case 0: scores[i] = 0; break;
            case 1: scores[i] = static_cast<int>(i); break;
            case 2: scores[i] = -static_cast<int>(i); break;
            case 3: scores[i] = (i % 2) ? std::numeric_limits<int>::min() : std::numeric_limits<int>::max(); break;
            case 4: scores[i] = static_cast<int>(rng() % 7) - 3; break;
            default: scores[i] = std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(rng())); break;
            }
        }
        check(board, *worker, scores, prefix);
        for (std::size_t consumed = 1; consumed <= 5 && consumed < n; ++consumed)
            check(board, *worker, scores, prefix, consumed);
        check(board, *worker, scores, prefix, 0, true);
    }
    std::cout << "{\"passed\":true,\"seed\":" << Seed << ",\"fixtures\":" << fixtures
              << ",\"pick_calls\":" << calls << ",\"guard\":" << FORGE_SPD_PICKER_SELF_SWAP_GUARD
              << ",\"speed2\":" << FORGE_SEARCH_SPEED2 << ",\"badcap_prefix\":" << FORGE_SDK_BADCAP_PREFIX
              << ",\"no_zero_lists\":" << FORGE_SPD_NO_ZERO_MOVELISTS << "}\n";
}
