// Regenerates the v3 "random" net exactly as tools/nnue_v3_tool.cpp write_random() does,
// in memory, and searches a seed range for a target FNV-1a of the file payload.
// usage: gennet <hidden> <kb> <ob> <mirror 0|1> <seed_lo> <seed_hi> <target_hex|-> [out_path]
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <string>
#include <vector>

namespace {

constexpr int HeaderBytes = 192;
constexpr int QA = 255;
constexpr int QB = 64;

std::uint64_t fnv1a64(const std::uint8_t* data, std::size_t size, std::uint64_t hash = 14695981039346656037ULL) {
    for (std::size_t i = 0; i < size; ++i) {
        hash ^= static_cast<std::uint64_t>(data[i]);
        hash *= 1099511628211ULL;
    }
    return hash;
}

void put_u32(std::vector<std::uint8_t>& out, std::uint32_t v) {
    for (int i = 0; i < 4; ++i) out.push_back(static_cast<std::uint8_t>((v >> (8 * i)) & 0xFFU));
}
void put_i16(std::vector<std::uint8_t>& out, std::int16_t v) {
    const auto u = static_cast<std::uint16_t>(v);
    out.push_back(static_cast<std::uint8_t>(u & 0xFFU));
    out.push_back(static_cast<std::uint8_t>((u >> 8U) & 0xFFU));
}

std::vector<std::uint8_t> build(int hidden, int king_buckets, int output_buckets, bool mirror, std::uint32_t seed) {
    std::vector<std::uint8_t> out;
    out.reserve(6400000);
    const char magic[8] = {'F', 'O', 'R', 'G', 'E', 'N', 'N', '3'};
    out.insert(out.end(), magic, magic + 8);
    put_u32(out, 3);
    put_u32(out, static_cast<std::uint32_t>(HeaderBytes));
    put_u32(out, 768);
    put_u32(out, static_cast<std::uint32_t>(hidden));
    put_u32(out, static_cast<std::uint32_t>(king_buckets));
    put_u32(out, static_cast<std::uint32_t>(output_buckets));
    put_u32(out, mirror ? 2U : 0U);
    put_u32(out, static_cast<std::uint32_t>(QA));
    put_u32(out, static_cast<std::uint32_t>(QB));
    put_u32(out, 400);
    for (int sq = 0; sq < 64; ++sq) out.push_back(static_cast<std::uint8_t>((sq >> 3) * king_buckets / 8));
    for (int p = 0; p <= 32; ++p) {
        out.push_back(static_cast<std::uint8_t>(std::min(output_buckets - 1, std::max(p - 2, 0) * output_buckets / 32)));
    }
    while (out.size() < static_cast<std::size_t>(HeaderBytes)) out.push_back(0);
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
    const std::uint64_t hash = fnv1a64(out.data(), out.size());
    for (int i = 0; i < 8; ++i) out.push_back(static_cast<std::uint8_t>((hash >> (8 * i)) & 0xFFU));
    return out;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 8) {
        std::fprintf(stderr, "usage: gennet <hidden> <kb> <ob> <mirror> <seed_lo> <seed_hi> <target_hex|-> [out]\n");
        return 2;
    }
    const int hidden = std::atoi(argv[1]);
    const int kb = std::atoi(argv[2]);
    const int ob = std::atoi(argv[3]);
    const bool mirror = std::atoi(argv[4]) != 0;
    const std::uint64_t lo = std::strtoull(argv[5], nullptr, 10);
    const std::uint64_t hi = std::strtoull(argv[6], nullptr, 10);
    const std::string target = argv[7];
    const char* out_path = argc > 8 ? argv[8] : nullptr;

    for (std::uint64_t seed = lo; seed <= hi; ++seed) {
        const std::vector<std::uint8_t> bytes = build(hidden, kb, ob, mirror, static_cast<std::uint32_t>(seed));
        const std::uint64_t stored = fnv1a64(bytes.data(), bytes.size() - 8);
        char hex[32];
        std::snprintf(hex, sizeof(hex), "%016llx", static_cast<unsigned long long>(stored));
        if (target != "-" && target == hex) {
            std::printf("MATCH seed %llu size %zu fnv %s\n", static_cast<unsigned long long>(seed), bytes.size(), hex);
            if (out_path != nullptr) {
                std::FILE* f = std::fopen(out_path, "wb");
                if (f == nullptr) return 1;
                std::fwrite(bytes.data(), 1, bytes.size(), f);
                std::fclose(f);
                std::printf("wrote %s\n", out_path);
            }
            return 0;
        }
        if (target == "-" && (seed == lo || seed % 1000 == 0)) {
            std::printf("seed %llu size %zu fnv %s\n", static_cast<unsigned long long>(seed), bytes.size(), hex);
        }
    }
    std::printf("NO MATCH in [%llu, %llu]\n", static_cast<unsigned long long>(lo), static_cast<unsigned long long>(hi));
    return 1;
}
