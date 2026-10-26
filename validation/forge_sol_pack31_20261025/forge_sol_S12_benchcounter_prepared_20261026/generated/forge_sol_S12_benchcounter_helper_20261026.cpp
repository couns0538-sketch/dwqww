// Original diagnostic helper, source-bound to Forge's own canonical UCI bench.
// PREPARED ONLY: no C++ compile or native run accompanies this source packet.
#include "forge/board.hpp"
#include "forge/search.hpp"
#include <array>
#include <charconv>
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string_view>

#if !FORGE_NNUE_LAZY_ACC
#error "This helper must match an S12 feature-ON core and header ABI"
#endif

namespace {
constexpr std::array<std::string_view, 8> BenchFens{{
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
}};
constexpr std::string_view CanonicalUciSha256 = "13c7c87a377ec30616f9a733bc5d74072c697c6e48db9eb39d751409f3cc0f97";
constexpr std::string_view BenchBlockSha256 = "5c44f6b9cd21cb28c9bcc9564eee7552f15c9fce96707b4c16cc19638c4fdd30";
constexpr std::string_view SuiteSha256 = "16f158933265dc5dc05ffd00a181809d345b25d72d3de8e169804efed7b1a835";
constexpr std::string_view CandidateHeaderSha256 = "f1e61dcf7ec82339f6bef582fe5af0ff256171b3824e7964de3fd10c2b10b140";
constexpr std::string_view CandidatePatchSha256 = "66efe4c94225d95a42e8754e3b11ff363cfb4903a855e60c0bbdfdf8b5a6ee8d";

void add(std::uint64_t& destination, std::uint64_t value) {
    if (value > std::numeric_limits<std::uint64_t>::max() - destination)
        throw std::overflow_error("counter aggregation overflow");
    destination += value;
}

void accumulate(forge::LazyAccStats& sum, const forge::LazyAccStats& item) {
    add(sum.refreshes, item.refreshes);
    add(sum.updates, item.updates);
    add(sum.zero_dirty_edges, item.zero_dirty_edges);
    add(sum.copies_avoided, item.copies_avoided);
    add(sum.alias_hits, item.alias_hits);
    add(sum.evaluations, item.evaluations);
}

void stats(const forge::LazyAccStats& value) {
    std::cout << "{\"refreshes\":" << value.refreshes
              << ",\"updates\":" << value.updates
              << ",\"zero_dirty_edges\":" << value.zero_dirty_edges
              << ",\"copies_avoided\":" << value.copies_avoided
              << ",\"alias_hits\":" << value.alias_hits
              << ",\"evaluations\":" << value.evaluations << '}';
}

std::uint64_t reference(int depth) {
    switch (depth) {
        case 11: return 308972;
        case 13: return 745494;
        case 16: return 2460422;
        case 20: return 11901452;
        case 22: return 31111774;
        default: return 0;
    }
}
}

int main(int argc, char** argv) {
    try {
        if (argc != 3) {
            std::cerr << "usage: helper DEPTH OFF|ON (depth11/13/16/20/22)\n";
            return 2;
        }
        int depth = 0;
        const std::string_view depth_text(argv[1]);
        const auto parsed = std::from_chars(depth_text.data(), depth_text.data() + depth_text.size(), depth);
        const std::string_view mode(argv[2]);
        if (parsed.ec != std::errc{} || parsed.ptr != depth_text.data() + depth_text.size()
            || reference(depth) == 0 || (mode != "OFF" && mode != "ON")) return 2;
        if (!forge::nnue::available() || !forge::nnue::enabled) {
            std::cerr << "FAIL actual compiled NNUE must be available and enabled\n";
            return 2;
        }
        // The real UCI main and tools/search_benchmark.cpp construct a Board
        // before searching. Constructors perform Forge's existing initialization;
        // there is no fabricated alternate initialization function here.
        [[maybe_unused]] forge::Board initialization_board;
        forge::lazy_acc::requested.store(mode == "ON", std::memory_order_relaxed);
        std::cout << "{\"record\":\"binding\",\"mode\":\"" << mode
                  << "\",\"requested_depth\":" << depth
                  << ",\"suite_count\":8,\"hash_mib\":16,\"threads\":1"
                  << ",\"canonical_uci_sha256\":\"" << CanonicalUciSha256
                  << "\",\"bench_block_sha256\":\"" << BenchBlockSha256
                  << "\",\"suite_sha256\":\"" << SuiteSha256
                  << "\",\"candidate_header_sha256\":\"" << CandidateHeaderSha256
                  << "\",\"candidate_patch_sha256\":\"" << CandidatePatchSha256 << "\"}\n";

        // Same eight FENs, order, one Hash16 Searcher, clear before EVERY FEN,
        // default SearchLimits except fixed depth, no info PV, exclusive TT.
        forge::Searcher bench_searcher(16);
        if (bench_searcher.threads() != 1) throw std::runtime_error("expected exactly one worker");
        std::uint64_t total_nodes = 0;
        forge::LazyAccStats totals{};
        std::size_t index = 0;
        for (const std::string_view fen : BenchFens) {
            forge::Board bench_board;
            if (!bench_board.set_fen(fen)) throw std::runtime_error("invalid bound bench FEN");
            forge::SearchLimits limits;
            limits.depth = depth;
            bench_searcher.clear();
            const auto result = bench_searcher.search(
                bench_board, limits, false, forge::Searcher::TTAccess::Exclusive);
            add(total_nodes, result.nodes);
            accumulate(totals, result.lazy_acc_stats);
            // Bound FENs contain no JSON quote, backslash, or control byte;
            // the source producer validates that before emitting this program.
            std::cout << "{\"record\":\"per_fen\",\"mode\":\"" << mode
                      << "\",\"requested_depth\":" << depth << ",\"index\":" << index
                      << ",\"fen\":\"" << fen << "\",\"nodes\":" << result.nodes
                      << ",\"completed_depth\":" << result.depth << ",\"stats\":";
            stats(result.lazy_acc_stats);
            std::cout << "}\n";
            ++index;
        }
        const bool matched = total_nodes == reference(depth) && index == BenchFens.size();
        std::cout << "{\"record\":\"total\",\"mode\":\"" << mode
                  << "\",\"requested_depth\":" << depth << ",\"positions\":" << index
                  << ",\"nodes\":" << total_nodes << ",\"reference_nodes\":" << reference(depth)
                  << ",\"node_reference_match\":" << (matched ? "true" : "false")
                  << ",\"stats\":";
        stats(totals);
        std::cout << "}" << std::endl;
        if (!matched) return 1;
        if (mode == "OFF" && (totals.copies_avoided != 0 || totals.alias_hits != 0)) return 1;
        if (mode == "ON" && (totals.evaluations == 0 || totals.copies_avoided == 0)) return 1;
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL " << error.what() << '\n';
        return 1;
    }
}
