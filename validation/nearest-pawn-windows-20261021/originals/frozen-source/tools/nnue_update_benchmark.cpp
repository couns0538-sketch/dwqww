// Public, out-of-line nnue::update microbenchmark. This is not NPS or Elo.
// Build driver and core without LTO; inspect the resulting update call site.
#include "forge/nnue.hpp"

#include <array>
#include <bit>
#include <charconv>
#include <chrono>
#include <cstdint>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <vector>
#include <cfenv>
#if defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64)
#include <xmmintrin.h>
#endif
#if defined(__FAST_MATH__) || (defined(__FINITE_MATH_ONLY__) && __FINITE_MATH_ONLY__ > 0)
#error "NNUE benchmark requires strict floating-point compilation"
#endif
#ifndef FORGE_NNUE_BENCH_FLAGS
#define FORGE_NNUE_BENCH_FLAGS "unspecified; record the external compile command"
#endif

namespace {
constexpr std::size_t CapacityPerCount = 64;
struct Sample {
    forge::nnue::Accumulator parent;
    forge::nnue::DirtyPieces dirty;
};
std::array<std::vector<Sample>, 5> corpus;
std::array<std::uint64_t, 5> seen{};
std::uint64_t random_state = 0x13198a2e03707344ULL;
std::uint64_t random_word() {
    random_state = random_state * 6364136223846793005ULL + 1442695040888963407ULL;
    return random_state;
}
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
void consider(const forge::nnue::Accumulator& parent, const forge::nnue::DirtyPieces& dirty) {
    require(dirty.count >= 0 && dirty.count <= 4, "invalid generated dirty count");
    const auto count = static_cast<std::size_t>(dirty.count);
    auto& samples = corpus[count];
    ++seen[count];
    if (samples.size() < CapacityPerCount) samples.push_back({parent, dirty});
    else {
        const auto slot = random_word() % seen[count];
        if (slot < CapacityPerCount) samples[static_cast<std::size_t>(slot)] = {parent, dirty};
    }
}
void make_corpus() {
    constexpr std::array<const char*, 10> starts{
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
        "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
        "4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1",
        "1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
        "4k3/7P/8/8/8/8/p7/1R2K3 b - - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
    };
    forge::Board board;
    for (const char* fen : starts) {
        require(board.set_fen(fen), "invalid corpus fixture");
        forge::nnue::Accumulator parent;
        forge::nnue::refresh(board, parent);
        for (const auto move : board.legal_moves()) {
            const auto dirty = forge::nnue::dirty_pieces(board, move);
            forge::Undo undo;
            require(board.make_move(move, undo), "legal corpus first move rejected");
            consider(parent, dirty);
            board.unmake_move(move, undo);
        }
        for (int ply = 0; ply < 96; ++ply) {
            forge::nnue::refresh(board, parent);
            if (ply % 8 == 0 && !board.in_check()) {
                forge::NullUndo undo;
                board.make_null_move(undo);
                consider(parent, forge::nnue::DirtyPieces{});
                board.unmake_null_move(undo);
            }
            const auto moves = board.legal_moves();
            if (moves.empty()) break;
            const auto move = moves[static_cast<std::size_t>(random_word() % moves.size())];
            const auto dirty = forge::nnue::dirty_pieces(board, move);
            forge::Undo undo;
            require(board.make_move(move, undo), "legal corpus walk move rejected");
            consider(parent, dirty);
        }
    }
    for (const std::size_t count : {0U, 2U, 3U, 4U})
        require(!corpus[count].empty(), "missing requested corpus category");
    for (const auto& sample : corpus[2])
        require(!sample.dirty.changes[0].add && sample.dirty.changes[1].add,
                "unexpected generated two-change flags");
}
void hash_word(std::uint64_t& hash, std::uint32_t word) {
    for (int shift = 0; shift < 32; shift += 8) {
        hash ^= (word >> shift) & 255U;
        hash *= 1099511628211ULL;
    }
}
void hash_accumulator(std::uint64_t& hash, const forge::nnue::Accumulator& accumulator) {
    for (const auto& side : accumulator.values)
        for (float value : side) hash_word(hash, std::bit_cast<std::uint32_t>(value));
    hash_word(hash, accumulator.valid ? 1U : 0U);
}
void json_string(std::string_view value) {
    std::cout << '"';
    for (char ch : value) {
        if (ch == '"' || ch == '\\') std::cout << '\\';
        if (ch == '\n') std::cout << "\\n";
        else if (ch == '\r') std::cout << "\\r";
        else if (ch == '\t') std::cout << "\\t";
        else std::cout << ch;
    }
    std::cout << '"';
}
} // namespace

int main(int argc, char** argv) {
    try {
        std::uint64_t iterations = 2000000;
        std::string_view group = "quiet";
        for (int i = 1; i < argc; ++i) {
            const std::string_view option = argv[i];
            if (option == "--help") {
                std::cout << "nnue_update_benchmark [--iterations N] [--group quiet|capture|castle|null|all]\n";
                return 0;
            }
            require(i + 1 < argc, "missing option value");
            const std::string_view value = argv[++i];
            if (option == "--group") group = value;
            else if (option == "--iterations") {
                const auto parsed = std::from_chars(value.data(), value.data() + value.size(), iterations);
                require(parsed.ec == std::errc{} && parsed.ptr == value.data() + value.size() && iterations != 0,
                        "invalid iteration count");
            } else throw std::runtime_error("unknown option");
        }
        require(group == "quiet" || group == "capture" || group == "castle" || group == "null" || group == "all",
                "unknown corpus group");
        require(forge::nnue::available(), "NNUE weights are required");
        require(std::fegetround() == FE_TONEAREST, "round-to-nearest is required");
        std::uint32_t fp_control = 0xffffffffU;
#if defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64)
        fp_control = _mm_getcsr() & 0x0000ffc0U;
#endif
        make_corpus();
        std::vector<Sample> selected;
        for (std::size_t count = 0; count <= 4; ++count) {
            if (group == "all" || (group == "quiet" && count == 2) ||
                (group == "capture" && count == 3) || (group == "castle" && count == 4) ||
                (group == "null" && count == 0))
                selected.insert(selected.end(), corpus[count].begin(), corpus[count].end());
        }
        require(!selected.empty() && iterations >= selected.size(), "iterations must cover the selected corpus");
        std::vector<forge::nnue::Accumulator> outputs(selected.size());
        std::uint64_t input_hash = 14695981039346656037ULL;
        std::array<std::uint64_t, 5> actual_counts{};
        for (std::size_t slot = 0; slot < selected.size(); ++slot) {
            const auto& sample = selected[slot];
            hash_accumulator(input_hash, sample.parent);
            hash_word(input_hash, static_cast<std::uint32_t>(sample.dirty.count));
            for (int i = 0; i < sample.dirty.count; ++i) {
                const auto& change = sample.dirty.changes[static_cast<std::size_t>(i)];
                hash_word(input_hash, static_cast<std::uint32_t>(change.piece));
                hash_word(input_hash, change.square);
                hash_word(input_hash, change.add ? 1U : 0U);
            }
            actual_counts[static_cast<std::size_t>(sample.dirty.count)] +=
                iterations / selected.size() + (slot < iterations % selected.size() ? 1U : 0U);
        }
        const std::uint64_t warmup_calls = iterations < 16384U ? iterations : 16384U;
        std::size_t index = 0;
        for (std::uint64_t call = 0; call < warmup_calls; ++call) {
            forge::nnue::update(selected[index].parent, outputs[index], selected[index].dirty);
            if (++index == selected.size()) index = 0;
        }
        index = 0;
        const std::clock_t cpu_start = std::clock();
        const auto wall_start = std::chrono::steady_clock::now();
        for (std::uint64_t call = 0; call < iterations; ++call) {
            forge::nnue::update(selected[index].parent, outputs[index], selected[index].dirty);
            if (++index == selected.size()) index = 0;
        }
        const auto wall_end = std::chrono::steady_clock::now();
        const std::clock_t cpu_end = std::clock();
        require(cpu_start != static_cast<std::clock_t>(-1) && cpu_end != static_cast<std::clock_t>(-1) &&
                cpu_end >= cpu_start, "CPU clock unavailable or wrapped");
        std::uint64_t output_hash = 14695981039346656037ULL;
        for (const auto& output : outputs) {
            require(output.valid, "timed update left an invalid output");
            hash_accumulator(output_hash, output);
        }
        const auto wall_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(wall_end - wall_start).count();
        std::cout << "{\"benchmark\":\"public_nnue_update_microkernel\",\"group\":";
        json_string(group);
        std::cout << ",\"iterations\":" << iterations << ",\"warmup_calls\":" << warmup_calls
                  << ",\"corpus_size\":" << selected.size() << ",\"hidden_size\":" << forge::nnue::HiddenSize
                  << ",\"accumulator_bytes\":" << sizeof(forge::nnue::Accumulator)
                  << ",\"wall_ns\":" << wall_ns << ",\"cpu_ticks\":" << cpu_end - cpu_start
                  << ",\"clocks_per_sec\":" << CLOCKS_PER_SEC << ",\"fp_control\":" << fp_control
                  << ",\"actual_counts\":[";
        for (std::size_t count = 0; count <= 4; ++count) {
            if (count != 0) std::cout << ',';
            std::cout << actual_counts[count];
        }
        std::cout << "],\"corpus_seen\":[";
        for (std::size_t count = 0; count <= 4; ++count) {
            if (count != 0) std::cout << ',';
            std::cout << seen[count];
        }
        std::cout << "],\"input_hash_fnv1a64\":\"" << std::hex << std::setw(16) << std::setfill('0') << input_hash
                  << "\",\"output_hash_fnv1a64\":\"" << std::setw(16) << output_hash << std::dec
                  << "\",\"checksum_scope\":\"all_final_output_ring_lanes_and_validity_outside_timing\",\"compiler\":";
#if defined(__clang__)
        json_string("Clang " __clang_version__);
#elif defined(__GNUC__)
        json_string("GCC " __VERSION__);
#else
        json_string("other; record external compiler version");
#endif
        std::cout << ",\"flags_label\":";
        json_string(FORGE_NNUE_BENCH_FLAGS);
#if defined(__AVX2__)
        std::cout << ",\"driver_avx2\":true";
#else
        std::cout << ",\"driver_avx2\":false";
#endif
#if defined(__OPTIMIZE__)
        std::cout << ",\"driver_optimized\":true";
#else
        std::cout << ",\"driver_optimized\":false";
#endif
        std::cout << ",\"strict_math_preprocessor_check\":true,\"core_and_driver_lto\":\"must_be_disabled_and_verified_externally\"}\n";
        require(static_cast<bool>(std::cout), "benchmark output failed");
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "nnue_update_benchmark: " << error.what() << '\n';
        return 1;
    }
}
