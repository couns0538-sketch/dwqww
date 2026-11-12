// NNUE v3 command-line tool (job FB1).
//   forge_nnue_v3_tool info <net>
//   forge_nnue_v3_tool eval <net> <fen file>      one line per FEN: cp bucket kb_w flip_w kb_b flip_b
//   forge_nnue_v3_tool sum  <net> <fen file>      one line per FEN: raw int64 output sum (before b2/scaling)
//   forge_nnue_v3_tool random <out> <hidden> <king buckets> <output buckets> <mirror 0|1> <seed>
//                                                 writes a random v3 net (CI hooks without numpy)
// cp is the network output alone (side to move, centipawns) computed with the fast path (cache refresh +
// compiled kernel); every position is also evaluated with the scalar reference and a difference is reported
// on stderr as MISMATCH (the exit status is then 3). The residual flag is reported by `info`.
#include "forge/board.hpp"
#include "forge/nnue_v3.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <random>
#include <string>
#include <vector>

namespace {

int usage() {
    std::cerr << "usage: forge_nnue_v3_tool info <net> | eval <net> <fen file> | sum <net> <fen file>\n"
                 "       forge_nnue_v3_tool random <out> <hidden> <king buckets> <output buckets> <mirror 0|1> <seed>\n";
    return 2;
}

void put_u32(std::vector<std::uint8_t>& out, std::uint32_t v) {
    for (int i = 0; i < 4; ++i) out.push_back(static_cast<std::uint8_t>((v >> (8 * i)) & 0xFFU));
}

void put_i16(std::vector<std::uint8_t>& out, std::int16_t v) {
    const auto u = static_cast<std::uint16_t>(v);
    out.push_back(static_cast<std::uint8_t>(u & 0xFFU));
    out.push_back(static_cast<std::uint8_t>((u >> 8U) & 0xFFU));
}

// Random net in the loader's valid ranges (|w1| <= 40, |b1| <= 200, |w2| <= 127): rank-band king map, C5-style
// piece-count output map. Same recipe as tests/nnue_v3_tests.cpp.
int write_random(const std::string& path, int hidden, int king_buckets, int output_buckets, bool mirror, std::uint32_t seed) {
    if (hidden < forge::nnue::v3::MinHidden || hidden > forge::nnue::v3::MaxHidden || hidden % 32 != 0 ||
        king_buckets < 1 || king_buckets > forge::nnue::v3::MaxKingBuckets ||
        output_buckets < 1 || output_buckets > forge::nnue::v3::MaxOutputBuckets) {
        std::cerr << "random: bad shape\n";
        return 2;
    }
    std::vector<std::uint8_t> out;
    const char magic[8] = {'F', 'O', 'R', 'G', 'E', 'N', 'N', '3'};
    out.insert(out.end(), magic, magic + 8);
    put_u32(out, 3);
    put_u32(out, static_cast<std::uint32_t>(forge::nnue::v3::HeaderBytes));
    put_u32(out, 768);
    put_u32(out, static_cast<std::uint32_t>(hidden));
    put_u32(out, static_cast<std::uint32_t>(king_buckets));
    put_u32(out, static_cast<std::uint32_t>(output_buckets));
    put_u32(out, mirror ? forge::nnue::v3::FlagMirror : 0U);
    put_u32(out, static_cast<std::uint32_t>(forge::nnue::v3::QA));
    put_u32(out, static_cast<std::uint32_t>(forge::nnue::v3::QB));
    put_u32(out, 400);
    for (int sq = 0; sq < 64; ++sq) out.push_back(static_cast<std::uint8_t>((sq >> 3) * king_buckets / 8));
    for (int p = 0; p <= 32; ++p) out.push_back(static_cast<std::uint8_t>(std::min(output_buckets - 1, std::max(p - 2, 0) * output_buckets / 32)));
    while (out.size() < static_cast<std::size_t>(forge::nnue::v3::HeaderBytes)) out.push_back(0);
    std::mt19937 rng(seed);
    std::uniform_int_distribution<int> dw1(-40, 40);
    std::uniform_int_distribution<int> db1(-200, 200);
    std::uniform_int_distribution<int> dw2(-127, 127);
    std::uniform_int_distribution<int> db2(-5000, 5000);
    const std::size_t h = static_cast<std::size_t>(hidden);
    for (std::size_t i = 0; i < static_cast<std::size_t>(king_buckets) * 768 * h; ++i) put_i16(out, static_cast<std::int16_t>(dw1(rng)));
    for (std::size_t i = 0; i < h; ++i) put_i16(out, static_cast<std::int16_t>(db1(rng)));
    for (std::size_t i = 0; i < static_cast<std::size_t>(output_buckets) * 2 * h; ++i) put_i16(out, static_cast<std::int16_t>(dw2(rng)));
    for (int i = 0; i < output_buckets; ++i) put_u32(out, static_cast<std::uint32_t>(db2(rng)));
    const std::uint64_t hash = forge::nnue::v3::fnv1a64(out.data(), out.size());
    for (int i = 0; i < 8; ++i) out.push_back(static_cast<std::uint8_t>((hash >> (8 * i)) & 0xFFU));
    std::ofstream file(path, std::ios::binary);
    if (!file) {
        std::cerr << "cannot write " << path << '\n';
        return 1;
    }
    file.write(reinterpret_cast<const char*>(out.data()), static_cast<std::streamsize>(out.size()));
    std::cout << "wrote " << path << " hidden " << hidden << " kb " << king_buckets << " ob " << output_buckets
              << (mirror ? " mirrored" : "") << " bytes " << out.size() << '\n';
    return 0;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 3) return usage();
    const std::string command = argv[1];
    if (command == "random") {
        if (argc < 8) return usage();
        return write_random(argv[2], std::stoi(argv[3]), std::stoi(argv[4]), std::stoi(argv[5]), std::stoi(argv[6]) != 0,
                            static_cast<std::uint32_t>(std::stoul(argv[7])));
    }
    std::string error;
    if (!forge::nnue::v3::load(argv[2], &error)) {
        std::cerr << "ERROR NNUE v3: " << error << '\n';
        return 1;
    }
    const forge::nnue::v3::Net& net = *forge::nnue::v3::loaded();
    if (command == "info") {
        std::cout << forge::nnue::v3::describe(net) << '\n';
        return 0;
    }
    if ((command != "eval" && command != "sum") || argc < 4) return usage();
    std::ifstream in(argv[3]);
    if (!in) {
        std::cerr << "cannot open " << argv[3] << '\n';
        return 1;
    }
    auto state = std::make_unique<forge::nnue::v3::WorkerState>();
    forge::nnue::v3::prepare(net, *state, 8);
    std::string line;
    forge::Board board;
    int count = 0;
    int mismatches = 0;
    while (std::getline(in, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
        if (line.empty()) continue;
        if (!board.set_fen(line)) {
            std::cout << "BADFEN\n";
            continue;
        }
        const forge::nnue::v3::KingKey white = forge::nnue::v3::king_key(net, forge::White, board.king_square(forge::White));
        const forge::nnue::v3::KingKey black = forge::nnue::v3::king_key(net, forge::Black, board.king_square(forge::Black));
        const int bucket = forge::nnue::v3::output_bucket(net, board);
        forge::nnue::v3::Accumulator& accumulator = state->stack[4];
        forge::nnue::v3::refresh_cached(net, state->cache, board, accumulator);
        const forge::Color us = board.side_to_move();
        const std::int16_t* ours = accumulator.values[static_cast<std::size_t>(us)].data();
        const std::int16_t* theirs = accumulator.values[static_cast<std::size_t>(forge::opposite(us))].data();
        if (command == "eval") {
            const int fast = forge::nnue::v3::evaluate(net, board, accumulator);
            const int reference = forge::nnue::v3::evaluate_reference(net, board);
            if (fast != reference) {
                ++mismatches;
                std::cerr << "MISMATCH fast " << fast << " reference " << reference << " at " << line << '\n';
            }
            std::cout << fast << ' ' << bucket << ' '
                      << static_cast<int>(white.bucket) << ' ' << static_cast<int>(white.flip) << ' '
                      << static_cast<int>(black.bucket) << ' ' << static_cast<int>(black.flip) << '\n';
        } else {
            const std::int64_t fast = forge::nnue::v3::output_sum(net, ours, theirs, bucket);
            const std::int64_t reference = forge::nnue::v3::output_sum_scalar(net, ours, theirs, bucket);
            if (fast != reference) {
                ++mismatches;
                std::cerr << "MISMATCH sum fast " << fast << " reference " << reference << " at " << line << '\n';
            }
            std::cout << fast << '\n';
        }
        ++count;
    }
    std::cerr << count << " positions, kernel " << forge::nnue::v3::kernel_name() << ", fast-vs-reference mismatches " << mismatches
              << ", cache refreshes " << state->cache.refreshes << " columns " << state->cache.columns << '\n';
    return mismatches == 0 ? 0 : 3;
}
