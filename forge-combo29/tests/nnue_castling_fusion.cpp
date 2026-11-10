// Standalone bit-exact regression. Include the implementation to test the real
// updater against its generic sequential algorithm using the shipped weights.
// g++-14 -std=c++20 -O3 -ffp-contract=off -fno-fast-math \
//   -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_NNUE_CASTLE_FUSE=1 -Iinclude \
//   tests/nnue_castling_fusion.cpp src/board.cpp src/bitboard.cpp -o nnue-castle-test
// Repeat with the switch omitted (default 0). Do not also link src/nnue.cpp.
#include "../src/nnue.cpp"

#include <bit>
#include <cstdlib>
#include <iostream>
#include <random>

namespace {
using namespace forge;
using namespace forge::nnue;
std::size_t cases = 0;

void require(bool condition, const char* message) {
    if (!condition) {
        std::cerr << message << '\n';
        std::exit(1);
    }
}

void check(const Accumulator& parent, const DirtyPieces& dirty) {
    Accumulator expected = parent;
    const auto& w = forge::nnue::weights();
    for (const Color perspective : {White, Black}) {
        auto& acc = expected.values[static_cast<std::size_t>(perspective)];
        for (int i = 0; i < dirty.count; ++i) {
            const auto& change = dirty.changes[static_cast<std::size_t>(i)];
            const float* column = w.w1.get() + static_cast<std::size_t>(
                feature_index(perspective, change.piece, change.square)) * HiddenSize;
            for (int h = 0; h < HiddenSize; ++h) {
                if (change.add) acc[static_cast<std::size_t>(h)] += column[h];
                else acc[static_cast<std::size_t>(h)] -= column[h];
            }
        }
    }
    Accumulator actual;
    update(parent, actual, dirty);
    Accumulator aliased = parent;
    update(aliased, aliased, dirty);
    require(actual.valid && aliased.valid, "Updater did not set valid");
    for (std::size_t p = 0; p < 2; ++p) {
        for (std::size_t h = 0; h < HiddenSize; ++h) {
            const auto bits = std::bit_cast<std::uint32_t>(expected.values[p][h]);
            require(std::bit_cast<std::uint32_t>(actual.values[p][h]) == bits,
                    "Distinct-source accumulator bits differ");
            require(std::bit_cast<std::uint32_t>(aliased.values[p][h]) == bits,
                    "In-place accumulator bits differ");
        }
    }
    ++cases;
}
} // namespace

int main() {
    using namespace forge;
    using namespace forge::nnue;
    require(available(), "Test requires the shipped network");
    std::mt19937 rng(0xCA571E);
    const char* positions[] = {
        "r3k2r/8/8/8/8/8/8/R3K2R",
        "r3k2r/ppp2ppp/2n1bn2/3qp3/3PP3/2N1BN2/PPP2PPP/R2QK2R",
        "r3k2r/pppbbppp/2np1n2/1B2p3/4P3/2NP1N2/PPP2PPP/R3K2R"
    };
    for (const char* placement : positions) {
        for (Color us : {White, Black}) {
            Board board;
            require(board.set_fen(std::string(placement) +
                    (us == White ? " w KQkq - 0 1" : " b KQkq - 0 1")), "Invalid fixture FEN");
            for (bool king_side : {false, true}) {
                const int from = us == White ? 4 : 60;
                const Move move{static_cast<std::uint8_t>(from),
                    static_cast<std::uint8_t>(from + (king_side ? 2 : -2)), 0,
                    static_cast<std::uint8_t>(king_side ? KingCastle : QueenCastle)};
                require(board.is_legal(move), "Fixture castling move is not legal");
                const DirtyPieces dirty = dirty_pieces(board, move);
                require(dirty.count == 4 && !dirty.changes[0].add && dirty.changes[1].add &&
                        !dirty.changes[2].add && dirty.changes[3].add, "Unexpected castle order");
                Accumulator parent;
                refresh(board, parent);
                check(parent, dirty);
                // Arbitrary finite IEEE-754 floats include subnormals, large
                // exponents, cancellation-sensitive values, and both signs.
                for (int trial = 0; trial < 1000; ++trial) {
                    for (auto& perspective : parent.values) {
                        for (float& lane : perspective) {
                            std::uint32_t bits = rng();
                            if ((bits & 0x7F800000U) == 0x7F800000U) bits ^= 0x00800000U;
                            lane = std::bit_cast<float>(bits);
                        }
                    }
                    check(parent, dirty);
                }
                // Exercise every four-change sign pattern (only -+-+ fuses),
                // shorter fallback paths, and signed-zero inputs.
                for (auto& perspective : parent.values)
                    for (std::size_t h = 0; h < HiddenSize; ++h)
                        perspective[h] = h % 2 == 0 ? 0.0F : -0.0F;
                for (int mask = 0; mask < 16; ++mask) {
                    DirtyPieces other = dirty;
                    for (int i = 0; i < 4; ++i)
                        other.changes[static_cast<std::size_t>(i)].add = (mask & (1 << i)) != 0;
                    for (int count = 0; count <= 4; ++count) {
                        other.count = count;
                        check(parent, other);
                    }
                }
            }
        }
    }
    std::cout << "PASS: " << cases << " cases; both perspectives, every float bit, "
              << "distinct and aliased accumulators; FORGE_SPD_NNUE_CASTLE_FUSE="
              << FORGE_SPD_NNUE_CASTLE_FUSE << '\n';
}
