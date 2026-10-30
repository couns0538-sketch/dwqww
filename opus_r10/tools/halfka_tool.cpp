// R10 test tool for the HalfKA (K32H3^) path, linked with the engine core (not part of the engine).
//   halfka_tool eval <net.nnue> <fens.txt> <out.txt>   raw output (the trainer's integer output value) and cp per FEN;
//                                                     every position is evaluated with the SIMD and the scalar kernels
//   halfka_tool walk <net.nnue> <seed> <games> <plies> random legal game lines: at every ply the incrementally updated
//                                                     accumulators (parent + this ply's changes, and from 2..4 plies
//                                                     back as the search's lazy walk does) must equal a full refresh
//   halfka_tool speed <net.nnue> <fens.txt> <reps>    ns per call of every eval stage (one random legal move per FEN):
//                                                     HalfKA refresh / apply / forward (AVX2 and scalar) and the lock's
//                                                     eval (FORGENN2 refresh / update / evaluate + the HCE part)
// FEN file: one FEN per line (anything after " | " is ignored).
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/nnue_halfka.hpp"

#include <array>
#include <chrono>
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

volatile long long g_sink = 0;  // keeps the timed calls from being optimised away

int speed_mode(const std::string& fens, int reps) {
    struct Pos {
        Board parent, child;
        nnue::DirtyPieces dirty;
    };
    std::vector<Pos> pos;
    std::mt19937 rng(20261030);
    {
        std::ifstream in(fens);
        std::string line;
        while (std::getline(in, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            const std::size_t bar = line.find(" | ");
            const std::string fen = bar == std::string::npos ? line : line.substr(0, bar);
            Board b;
            if (fen.empty() || !b.set_fen(fen)) continue;
            const MoveList legal = b.legal_moves();
            if (legal.size() == 0) continue;
            const Move m = legal[static_cast<std::size_t>(rng() % legal.size())];
            Pos p{b, b, nnue::dirty_pieces(b, m)};
            Undo u;
            (void)p.child.make_move(m, u);
            pos.push_back(p);
        }
    }
    const std::size_t n = pos.size(), L = static_cast<std::size_t>(halfka::l1());
    using clk = std::chrono::steady_clock;
    auto ns = [](clk::time_point a, clk::time_point b, double calls) {
        return std::chrono::duration<double, std::nano>(b - a).count() / calls;
    };
    // HalfKA rows of every parent and child; apply is timed where the orientation stays (the search refreshes otherwise)
    std::vector<std::int16_t> parent(n * 2 * L), child(n * 2 * L), scratch(L);
    std::vector<std::pair<std::size_t, Color>> same;
    for (std::size_t i = 0; i < n; ++i)
        for (const Color c : {White, Black}) {
            halfka::refresh(pos[i].parent, c, parent.data() + (i * 2 + c) * L);
            halfka::refresh(pos[i].child, c, child.data() + (i * 2 + c) * L);
            if (pos[i].parent.king_square(c) == pos[i].child.king_square(c) &&
                halfka::feature_bucket(pos[i].parent, c) == halfka::feature_bucket(pos[i].child, c))
                same.emplace_back(i, c);
        }
    auto t0 = clk::now();
    for (int r = 0; r < reps; ++r)
        for (std::size_t i = 0; i < n; ++i)
            for (const Color c : {White, Black}) {
                halfka::refresh(pos[i].child, c, scratch.data());
                g_sink = g_sink + scratch[0];
            }
    auto t1 = clk::now();
    const double h_refresh = ns(t0, t1, static_cast<double>(reps) * static_cast<double>(n) * 2);
    t0 = clk::now();
    for (int r = 0; r < reps; ++r)
        for (const auto& [i, c] : same) {
            const Board& b = pos[i].child;
            halfka::apply(parent.data() + (i * 2 + c) * L, scratch.data(), c, b.king_square(c), halfka::feature_bucket(b, c),
                          pos[i].dirty);
            g_sink = g_sink + scratch[0];
        }
    t1 = clk::now();
    const double h_apply = ns(t0, t1, static_cast<double>(reps) * static_cast<double>(same.size()));
    double h_eval[2] = {0, 0};
    for (const bool scalar : {false, true}) {
        halfka::set_force_scalar(scalar);
        t0 = clk::now();
        for (int r = 0; r < reps; ++r)
            for (std::size_t i = 0; i < n; ++i)
                g_sink = g_sink + halfka::evaluate_raw(pos[i].child, child.data() + (i * 2 + White) * L, child.data() + (i * 2 + Black) * L);
        t1 = clk::now();
        h_eval[scalar ? 1 : 0] = ns(t0, t1, static_cast<double>(reps) * static_cast<double>(n));
    }
    halfka::set_force_scalar(false);
    std::printf("speed: %zu positions x %d reps, net %s, SIMD %s\n", n, reps, halfka::description().c_str(),
                halfka::simd_compiled() ? "AVX2" : "none");
    std::printf("HalfKA   refresh, one perspective              %8.1f ns\n", h_refresh);
    std::printf("HalfKA   apply one ply from the parent, one persp. %8.1f ns  (%zu of %zu perspective-moves keep the orientation)\n",
                h_apply, same.size(), 2 * n);
    std::printf("HalfKA   forward (pairwise, l1, l2, output) AVX2  %8.1f ns, scalar %8.1f ns\n", h_eval[0], h_eval[1]);
    if (!nnue::available()) {
        std::printf("FORGENN2 not compiled into this tool\n");
        return 0;
    }
    // the lock's evaluation (option off): FORGENN2 accumulators (both perspectives per call) + the HCE part when residual
    std::vector<nnue::Accumulator> np(n), nc(n);
    for (std::size_t i = 0; i < n; ++i) {
        nnue::refresh(pos[i].parent, np[i]);
        nnue::refresh(pos[i].child, nc[i]);
    }
    nnue::Accumulator tmp;
    t0 = clk::now();
    for (int r = 0; r < reps; ++r)
        for (std::size_t i = 0; i < n; ++i) {
            nnue::refresh(pos[i].child, tmp);
            g_sink = g_sink + static_cast<long long>(tmp.values[0][0]);
        }
    t1 = clk::now();
    const double f_refresh = ns(t0, t1, static_cast<double>(reps) * static_cast<double>(n));
    t0 = clk::now();
    for (int r = 0; r < reps; ++r)
        for (std::size_t i = 0; i < n; ++i) {
            nnue::update(np[i], tmp, pos[i].dirty);
            g_sink = g_sink + static_cast<long long>(tmp.values[0][0]);
        }
    t1 = clk::now();
    const double f_update = ns(t0, t1, static_cast<double>(reps) * static_cast<double>(n));
    t0 = clk::now();
    for (int r = 0; r < reps; ++r)
        for (std::size_t i = 0; i < n; ++i) g_sink = g_sink + nnue::evaluate(pos[i].child, nc[i]);
    t1 = clk::now();
    const double f_eval = ns(t0, t1, static_cast<double>(reps) * static_cast<double>(n));
    Evaluator ev;
    t0 = clk::now();
    for (int r = 0; r < reps; ++r)
        for (std::size_t i = 0; i < n; ++i) g_sink = g_sink + ev.evaluate(pos[i].child);
    t1 = clk::now();
    const double f_hce = ns(t0, t1, static_cast<double>(reps) * static_cast<double>(n));
    std::printf("FORGENN2 refresh, both perspectives            %8.1f ns\n", f_refresh);
    std::printf("FORGENN2 update one ply, both perspectives     %8.1f ns\n", f_update);
    std::printf("FORGENN2 evaluate (SCReLU output)              %8.1f ns\n", f_eval);
    // the search adds the HCE through a private runtime path that reuses an incremental PSQT; the public evaluate()
    // recomputes it, so this is an upper bound of the HCE part
    std::printf("HCE      evaluate (public API, upper bound; residual net: %s) %8.1f ns\n", nnue::residual() ? "yes" : "no", f_hce);
    std::printf("per searched eval, accumulators updated from the parent: HalfKA 2 x apply + forward = %.1f ns; "
                "lock = update + evaluate%s = %.1f ns\n", 2 * h_apply + h_eval[0], nnue::residual() ? " + HCE" : "",
                f_update + f_eval + (nnue::residual() ? f_hce : 0.0));
    return 0;
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
    if (mode == "speed" && argc >= 5) return speed_mode(argv[3], std::stoi(argv[4]));
    std::fprintf(stderr, "bad arguments\n");
    return 2;
}
