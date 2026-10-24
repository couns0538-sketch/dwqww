// Original actual-API phase probe. API kernel costs are not a search-time split.
#include "forge/nnue.hpp"

#include <array>
#include <bit>
#include <charconv>
#include <chrono>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

#if defined(__FAST_MATH__) || (defined(__FINITE_MATH_ONLY__) && __FINITE_MATH_ONLY__ != 0)
#error "NNUE phase probe requires strict floating-point compilation"
#endif

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
std::uint64_t unsigned_argument(std::string_view value) {
    std::uint64_t result = 0;
    const auto parsed = std::from_chars(value.data(), value.data() + value.size(), result);
    require(!value.empty() && parsed.ec == std::errc{} && parsed.ptr == value.data() + value.size(),
            "invalid unsigned decimal argument");
    return result;
}
void wait_for_start() {
    std::string line;
    require(static_cast<bool>(std::getline(std::cin, line)), "start command required on stdin");
    if (!line.empty() && line.back() == '\r') line.pop_back();
    require(line == "start", "expected start command on stdin");
}
template<class Function>
std::int64_t elapsed_ns(std::uint64_t iterations, Function function) {
    const auto begin = std::chrono::steady_clock::now();
    for (std::uint64_t i = 0; i < iterations; ++i) function(static_cast<std::size_t>(i % 64U));
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now() - begin).count();
}
} // namespace

int main(int argc, char** argv) {
    try {
        std::uint64_t iterations = 200000U;
        bool wait_start = false, iterations_seen = false;
        for (int i = 1; i < argc; ++i) {
            const std::string_view option(argv[i]);
            if (option == "--iterations") {
                require(!iterations_seen && i + 1 < argc, "invalid or duplicate iterations option");
                iterations_seen = true;
                iterations = unsigned_argument(argv[++i]);
            } else if (option == "--wait-start") {
                require(!wait_start, "duplicate wait-start option");
                wait_start = true;
            } else {
                throw std::runtime_error("usage: nnue_phase_benchmark [--iterations N] [--wait-start]");
            }
        }
        require(iterations > 0U && iterations <= 4294967295ULL,
                "iterations must be in [1, 4294967295]");
        std::ios::sync_with_stdio(false);
        if (wait_start) wait_for_start();
        require(forge::nnue::available(), "NNUE network required");
        constexpr std::array<const char*, 4> starts{
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
            "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
        };
        std::array<forge::Board, 64> boards;
        std::array<forge::nnue::Accumulator, 64> parents, refresh_outputs, update_outputs;
        std::array<forge::nnue::DirtyPieces, 64> dirty;
        std::uint64_t random = 0x504841534550524fULL;
        auto random_word = [&] {
            random = random * 6364136223846793005ULL + 1442695040888963407ULL;
            return random;
        };
        for (std::size_t i = 0; i < boards.size(); ++i) {
            require(boards[i].set_fen(starts[i % starts.size()]), "invalid fixture");
            for (std::size_t ply = 0; ply < i % 24U; ++ply) {
                const auto moves = boards[i].legal_moves();
                if (moves.empty()) break;
                forge::Undo undo;
                require(boards[i].make_move(moves[static_cast<std::size_t>(random_word() % moves.size())], undo),
                        "legal fixture move rejected");
            }
            forge::nnue::refresh(boards[i], parents[i]);
            const auto moves = boards[i].legal_moves();
            if (!moves.empty()) {
                const auto move = moves[static_cast<std::size_t>(random_word() % moves.size())];
                dirty[i] = forge::nnue::dirty_pieces(boards[i], move);
            }
        }
        std::uint64_t checksum = 0;
        auto refresh = [&](std::size_t i) { forge::nnue::refresh(boards[i], refresh_outputs[i]); };
        auto update = [&](std::size_t i) { forge::nnue::update(parents[i], update_outputs[i], dirty[i]); };
        auto evaluate = [&](std::size_t i) {
            checksum += static_cast<std::uint64_t>(forge::nnue::evaluate(boards[i], parents[i]));
        };
        for (std::size_t i = 0; i < 2048U; ++i) {
            refresh(i % boards.size()); update(i % boards.size()); evaluate(i % boards.size());
        }
        const auto refresh_ns = elapsed_ns(iterations, refresh);
        const auto update_ns = elapsed_ns(iterations, update);
        const auto evaluate_ns = elapsed_ns(iterations, evaluate);
        for (std::size_t i = 0; i < boards.size(); ++i) {
            require(refresh_outputs[i].valid && update_outputs[i].valid, "invalid actual accumulator");
            checksum += std::bit_cast<std::uint32_t>(refresh_outputs[i].values[0][0]);
            checksum += std::bit_cast<std::uint32_t>(update_outputs[i].values[0][0]);
        }
        std::cout << std::setprecision(12)
                  << "{\"kind\":\"nnue_phase_benchmark\",\"iterations\":" << iterations
                  << ",\"hidden_size\":" << forge::nnue::HiddenSize
                  << ",\"refresh_ns_per_call\":" << static_cast<double>(refresh_ns) / static_cast<double>(iterations)
                  << ",\"update_ns_per_call\":" << static_cast<double>(update_ns) / static_cast<double>(iterations)
                  << ",\"evaluate_ns_per_call\":" << static_cast<double>(evaluate_ns) / static_cast<double>(iterations)
                  << ",\"refresh_elapsed_ns\":" << refresh_ns << ",\"update_elapsed_ns\":" << update_ns
                  << ",\"evaluate_elapsed_ns\":" << evaluate_ns << ",\"checksum\":" << checksum
                  << ",\"api_phase_only\":true}\n";
        require(static_cast<bool>(std::cout), "phase probe output failed");
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "nnue_phase_benchmark: " << error.what() << '\n';
        return 1;
    }
}
