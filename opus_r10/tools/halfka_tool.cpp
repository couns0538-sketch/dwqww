// R10 test tool for the HalfKA (K32H3^) path, linked with the engine core (not part of the engine).
//   halfka_tool eval <net.nnue> <fens.txt> <out.txt>   raw output (the trainer's integer output value) and cp per FEN;
//                                                     every position is evaluated with the SIMD and the scalar kernels
//   halfka_tool walk <net.nnue> <seed> <games> <plies> random legal game lines: at every ply the incrementally updated
//                                                     accumulators (parent + this ply's changes, and from 2..4 plies
//                                                     back as the search's lazy walk does) must equal a full refresh
// FEN file: one FEN per line (anything after " | " is ignored).
#include "forge/board.hpp"
#include "forge/nnue_halfka.hpp"

#include <array>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>

using namespace forge;

namespace {

int eval_mode(const std::string& fens, const std::string& out_path) {
    std::ifstream in(fens);
    std::ofstream out(out_path, std::ios::binary);
    std::string line;
    long long n = 0, simd_mismatch = 0, bad = 0;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        const std::size_t bar = line.find(" | ");
        const std::string fen = bar == std::string::npos ? line : line.substr(0, bar);
        if (fen.empty()) continue;
        Board b;
        if (!b.set_fen(fen)) {
            ++bad;
            out << "BADFEN\n";
            continue;
        }
        halfka::set_force_scalar(false);
        const std::int64_t v = halfka::evaluate_fresh_raw(b);
        halfka::set_force_scalar(true);
        const std::int64_t s = halfka::evaluate_fresh_raw(b);
        halfka::set_force_scalar(false);
        if (v != s) ++simd_mismatch;
        out << v << ' ' << v / 16 << '\n';
        ++n;
    }
    std::printf("eval: %lld positions, %lld bad FENs, SIMD (%s) vs scalar mismatches %lld, net %s\n", n, bad,
                halfka::simd_compiled() ? "AVX2" : "none", simd_mismatch, halfka::description().c_str());
    return simd_mismatch == 0 && bad == 0 ? 0 : 1;
}

int walk_mode(unsigned seed, int games, int plies) {
    const int l1 = halfka::l1();
    std::mt19937 rng(seed);
    long long checks = 0, mismatches = 0, refreshes = 0, incrementals = 0, multi = 0;
    for (int g = 0; g < games; ++g) {
        Board b;
        (void)b.set_fen(Board::StandardStartFen);
        // per ply: accumulators, king squares, buckets, and the changes that led to the ply
        std::vector<std::array<std::vector<std::int16_t>, 2>> acc;
        std::vector<std::array<int, 2>> kings, buckets;
        std::vector<nnue::DirtyPieces> dirty(1);
        auto fresh = [&](Color c) {
            std::vector<std::int16_t> v(static_cast<std::size_t>(l1));
            halfka::refresh(b, c, v.data());
            return v;
        };
        acc.push_back({fresh(White), fresh(Black)});
        kings.push_back({b.king_square(White), b.king_square(Black)});
        buckets.push_back({halfka::feature_bucket(b, White), halfka::feature_bucket(b, Black)});
        for (int p = 0; p < plies; ++p) {
            const MoveList legal = b.legal_moves();
            if (legal.size() == 0) break;
            const Move m = legal[static_cast<std::size_t>(rng() % legal.size())];
            dirty.push_back(nnue::dirty_pieces(b, m));
            Undo u;
            (void)b.make_move(m, u);
            std::array<std::vector<std::int16_t>, 2> now;
            for (const Color c : {White, Black}) {
                const int king = b.king_square(c), bucket = halfka::feature_bucket(b, c);
                const std::vector<std::int16_t> ref = fresh(c);
                // 1) from the parent, 2) from an ancestor 2..4 plies back (when the orientation is the same there)
                const int k = static_cast<int>(acc.size());  // index of this ply
                for (int back = 1; back <= 4 && back <= k; ++back) {
                    const int from = k - back;
                    if (kings[static_cast<std::size_t>(from)][c] != king || buckets[static_cast<std::size_t>(from)][c] != bucket) continue;
                    std::vector<std::int16_t> v(static_cast<std::size_t>(l1));
                    halfka::apply(acc[static_cast<std::size_t>(from)][c].data(), v.data(), c, king, bucket,
                                  dirty[static_cast<std::size_t>(from + 1)]);
                    for (int e = from + 2; e <= k; ++e) halfka::apply(v.data(), v.data(), c, king, bucket, dirty[static_cast<std::size_t>(e)]);
                    ++checks;
                    if (back == 1) ++incrementals;
                    else ++multi;
                    if (std::memcmp(v.data(), ref.data(), sizeof(std::int16_t) * static_cast<std::size_t>(l1)) != 0) ++mismatches;
                }
                if (kings[static_cast<std::size_t>(k - 1)][c] != king || buckets[static_cast<std::size_t>(k - 1)][c] != bucket) ++refreshes;
                now[c] = ref;
            }
            acc.push_back(now);
            kings.push_back({b.king_square(White), b.king_square(Black)});
            buckets.push_back({halfka::feature_bucket(b, White), halfka::feature_bucket(b, Black)});
        }
    }
    std::printf("walk: %d games x up to %d plies: %lld incremental checks (%lld from the parent, %lld from 2-4 plies back), "
                "%lld mismatches vs full refresh, %lld orientation/state changes (refresh needed)\n",
                games, plies, checks, incrementals, multi, mismatches, refreshes);
    return mismatches == 0 ? 0 : 1;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::fprintf(stderr, "usage: halfka_tool eval <net> <fens> <out> | walk <net> <seed> <games> <plies>\n");
        return 2;
    }
    std::string error;
    if (!halfka::load(argv[2], error)) {
        std::fprintf(stderr, "load failed: %s\n", error.c_str());
        return 2;
    }
    const std::string mode = argv[1];
    if (mode == "eval" && argc >= 5) return eval_mode(argv[3], argv[4]);
    if (mode == "walk" && argc >= 6)
        return walk_mode(static_cast<unsigned>(std::stoul(argv[3])), std::stoi(argv[4]), std::stoi(argv[5]));
    std::fprintf(stderr, "bad arguments\n");
    return 2;
}
