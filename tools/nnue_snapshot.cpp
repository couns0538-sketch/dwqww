// Deterministic baseline/candidate NNUE output and accumulator byte comparison.
// Link the same driver separately against each core; compare stdout with cmp.
#include "forge/nnue.hpp"

#include <array>
#include <bit>
#include <cstdint>
#include <iostream>
#include <stdexcept>

namespace {
std::uint64_t state = 0x243f6a8885a308d3ULL;
std::uint64_t random_word() {
    state = state * 6364136223846793005ULL + 1442695040888963407ULL;
    return state;
}
void emit(std::uint32_t word) {
    // Explicit little-endian serialization, without struct padding.
    for (int shift = 0; shift < 32; shift += 8) std::cout.put(static_cast<char>((word >> shift) & 255U));
}
void snapshot(const forge::Board& board, const forge::nnue::Accumulator& acc) {
    for (const auto& perspective : acc.values)
        for (float value : perspective) emit(std::bit_cast<std::uint32_t>(value));
    emit(static_cast<std::uint32_t>(forge::nnue::evaluate(board, acc)));
}
}

int main() {
    if (!forge::nnue::available()) throw std::runtime_error("NNUE weights are required");
    constexpr std::array<const char*, 6> starts{
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
        "4k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
    };
    forge::Board board;
    for (const char* fen : starts) {
        for (int game = 0; game < 12; ++game) {
            if (!board.set_fen(fen)) throw std::runtime_error("invalid fixture");
            forge::nnue::Accumulator acc;
            forge::nnue::refresh(board, acc);
            snapshot(board, acc);
            // Exercise every legal first move, covering both castles, en
            // passant, all promotions and captures without relying on chance.
            for (const auto move : board.legal_moves()) {
                const auto dirty = forge::nnue::dirty_pieces(board, move);
                forge::Undo undo;
                if (!board.make_move(move, undo)) throw std::runtime_error("legal move rejected");
                forge::nnue::Accumulator child, fresh;
                forge::nnue::update(acc, child, dirty);
                forge::nnue::refresh(board, fresh);
                snapshot(board, child);
                snapshot(board, fresh);
                board.unmake_move(move, undo);
            }
            for (int ply = 0; ply < 120; ++ply) {
                const auto moves = board.legal_moves();
                if (moves.empty()) break;
                const auto move = moves[static_cast<std::size_t>(random_word() % moves.size())];
                const auto dirty = forge::nnue::dirty_pieces(board, move);
                forge::Undo undo;
                if (!board.make_move(move, undo)) throw std::runtime_error("legal move rejected");
                forge::nnue::Accumulator child, fresh;
                forge::nnue::update(acc, child, dirty);
                forge::nnue::refresh(board, fresh);
                snapshot(board, child);
                snapshot(board, fresh);
                acc = child;
            }
        }
    }
    // Finite synthetic activations probe negative/zero/saturated SCReLU
    // values and values adjacent to clamp boundaries, for both perspectives.
    constexpr std::array<float, 8> edges{
        -2.0F, -0.0F, 0.0F, 0x1p-149F,
        0x1.fffffep-1F, 1.0F, 0x1.000002p0F, 2.0F
    };
    for (int sample = 0; sample < 100000; ++sample) {
        forge::nnue::Accumulator acc;
        for (auto& perspective : acc.values) {
            for (float& value : perspective) {
                const auto word = random_word();
                value = sample < 1000 ? edges[static_cast<std::size_t>((word >> 32U) % edges.size())]
                    : static_cast<float>(static_cast<int>((word >> 32U) % 16385U) - 8192) / 4096.0F;
            }
        }
        if (!board.set_fen(sample % 2 == 0 ? starts[0] : "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"))
            throw std::runtime_error("invalid side fixture");
        emit(static_cast<std::uint32_t>(forge::nnue::evaluate(board, acc)));
    }
    if (!std::cout) throw std::runtime_error("output failed");
}
