// int8_evaldiff.cpp - NnueInt8Vnni proof harness (own code, 2026-11-06; steps 2b / 2c / 2d).
// Build: all src/*.cpp of the GATE tree (FORGE_NNUE_INT8_VNNI=1; uci.cpp with -Dmain=forge_uci_main_unused) + this file.
// usage: int8_evaldiff <fen file> <max fens> <walk plies per fen> <seed>
// For startpos and the first <max fens> lines of the file:
//   float network term (lock path) vs int8 network term (refresh) -> |diff| statistics, sign flips of the total
//   static eval (hand-crafted + network, as Worker::static_evaluate adds them), largest |A| of the int16 accumulator;
//   then a random legal walk of <walk plies>: int8 incremental update == int8 refresh (bytes), the kernel sum
//   int8_l1_sum == the scalar reference int8_l1_sum_scalar, and the same eval statistics at every walk position.
// Exit 0 = no incremental/refresh and no kernel/scalar mismatch; 1 = a mismatch; 2 = usage / input error.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <random>
#include <string>
#include <vector>

#if !FORGE_NNUE_INT8_VNNI
#error "build the harness from the gate tree (FORGE_NNUE_INT8_VNNI=1)"
#endif

using namespace forge;

namespace {

struct Stats {
    long long n = 0, sign_flips = 0, ge5 = 0, ge10 = 0, ge20 = 0, ge50 = 0;
    double sum_abs_net = 0.0, sum_abs_tot = 0.0, sum_signed = 0.0;
    int max_abs_net = 0, max_abs_tot = 0;
    int max_acc = 0;
    long long incr_mismatch = 0, kernel_mismatch = 0, walk_positions = 0;
};

int max_abs_acc(const nnue::Accumulator& a) {
    int m = 0;
    for (const auto& side : a.ivalues)
        for (const std::int16_t v : side) m = std::max(m, std::abs(static_cast<int>(v)));
    return m;
}

void sample(const Board& board, Evaluator& ev, Stats& s) {
    nnue::int8_vnni = false;
    nnue::Accumulator af;
    nnue::refresh(board, af);
    const int nf = nnue::evaluate(board, af);
    nnue::int8_vnni = true;
    nnue::Accumulator aq;
    nnue::refresh(board, aq);
    const int nq = nnue::evaluate(board, aq);
    if (nnue::int8_l1_sum(board, aq) != nnue::int8_l1_sum_scalar(board, aq)) ++s.kernel_mismatch;
    if (nq != nnue::evaluate_int8_scalar(board, aq)) ++s.kernel_mismatch;
    s.max_acc = std::max(s.max_acc, max_abs_acc(aq));
    // the public hand-crafted eval (evaluate_runtime is private to Worker); the same value enters both totals
    const int hce = ev.evaluate(board);
    const int tf = hce + nf, tq = hce + nq;
    const int dn = std::abs(nq - nf), dt = std::abs(tq - tf);
    ++s.n;
    s.sum_abs_net += dn;
    s.sum_abs_tot += dt;
    s.sum_signed += nq - nf;
    s.max_abs_net = std::max(s.max_abs_net, dn);
    s.max_abs_tot = std::max(s.max_abs_tot, dt);
    if (dn >= 5) ++s.ge5;
    if (dn >= 10) ++s.ge10;
    if (dn >= 20) ++s.ge20;
    if (dn >= 50) ++s.ge50;
    if ((tf > 0 && tq < 0) || (tf < 0 && tq > 0)) ++s.sign_flips;
}

void walk(Board board, int plies, std::mt19937& rng, Evaluator& ev, Stats& s) {
    nnue::int8_vnni = true;
    nnue::Accumulator acc;
    nnue::refresh(board, acc);
    for (int p = 0; p < plies; ++p) {
        const MoveList moves = board.legal_moves();
        if (moves.empty()) return;
        const Move move = moves[std::uniform_int_distribution<std::size_t>(0, moves.size() - 1)(rng)];
        const nnue::DirtyPieces dirty = nnue::dirty_pieces(board, move);
        Undo undo;
        if (!board.make_move(move, undo)) return;
        nnue::int8_vnni = true;
        nnue::Accumulator child;
        nnue::update(acc, child, dirty);
        nnue::Accumulator fresh;
        nnue::refresh(board, fresh);
        if (std::memcmp(child.ivalues.data(), fresh.ivalues.data(), sizeof(child.ivalues)) != 0) ++s.incr_mismatch;
        if (nnue::int8_l1_sum(board, child) != nnue::int8_l1_sum_scalar(board, child)) ++s.kernel_mismatch;
        acc = child;
        ++s.walk_positions;
        sample(board, ev, s);
    }
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 5) {
        std::fprintf(stderr, "usage: int8_evaldiff <fen file> <max fens> <walk plies> <seed>\n");
        return 2;
    }
    std::ifstream in(argv[1]);
    if (!in) {
        std::fprintf(stderr, "cannot open %s\n", argv[1]);
        return 2;
    }
    const int max_fens = std::atoi(argv[2]), plies = std::atoi(argv[3]);
    std::mt19937 rng(static_cast<std::uint32_t>(std::strtoul(argv[4], nullptr, 10)));
    std::vector<std::string> fens = {"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"};
    std::string line;
    while (static_cast<int>(fens.size()) < max_fens + 1 && std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (!line.empty() && line[0] != '#') fens.push_back(line);
    }
    Evaluator ev;
    Stats root, all;
    long long bad_fen = 0;
    for (const std::string& fen : fens) {
        Board board;
        if (!board.set_fen(fen)) {
            ++bad_fen;
            continue;
        }
        sample(board, ev, root);
        sample(board, ev, all);
        walk(board, plies, rng, ev, all);
    }
    auto print = [](const char* name, const Stats& s) {
        std::printf("%s: n %lld  net |diff| cp: max %d mean %.3f, mean signed %+.3f; >=5 %lld >=10 %lld >=20 %lld >=50 %lld;"
                    " total |diff| max %d mean %.3f; total sign flips %lld; max |A| %d\n",
                    name, s.n, s.max_abs_net, s.n ? s.sum_abs_net / static_cast<double>(s.n) : 0.0,
                    s.n ? s.sum_signed / static_cast<double>(s.n) : 0.0, s.ge5, s.ge10, s.ge20, s.ge50, s.max_abs_tot,
                    s.n ? s.sum_abs_tot / static_cast<double>(s.n) : 0.0, s.sign_flips, s.max_acc);
    };
    std::printf("fens %zu (bad %lld), walk %d plies per fen, seed %s\n", fens.size(), bad_fen, plies, argv[4]);
    print("roots", root);
    print("roots+walk", all);
    std::printf("walk positions %lld: incremental != refresh %lld; kernel != scalar %lld\n", all.walk_positions,
                all.incr_mismatch, all.kernel_mismatch + root.kernel_mismatch);
    return (all.incr_mismatch == 0 && all.kernel_mismatch == 0 && root.kernel_mismatch == 0) ? 0 : 1;
}
