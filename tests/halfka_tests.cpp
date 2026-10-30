// R10: the HalfKA (K32H3^) evaluation path (src/nnue_halfka.cpp) with the small committed test net.
// usage: forge_halfka_tests <net.nnue> <expected.txt> <scratch dir>
// expected.txt: "<raw> <fen>" lines, the trainer's exact integer output for the net (nnue-pytorch, R10 parity run).
// Checks: the net loads; every expected position evaluates to exactly the trainer's value with the SIMD kernels and
// with the scalar ones; incremental accumulators (out of place and in place) equal a full refresh along random legal
// lines; a truncated copy of the net is rejected and leaves the loaded net in place; searches with 2 threads and the
// net loaded return legal moves (the sanitizer builds cover the kernels and the per-worker accumulators).
#include "forge/board.hpp"
#include "forge/nnue.hpp"
#include "forge/nnue_halfka.hpp"
#include "forge/search.hpp"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <random>
#include <string>
#include <vector>

using namespace forge;

namespace {

int failures = 0;

void check(bool ok, const std::string& what) {
    if (!ok) {
        ++failures;
        std::cout << "FAIL: " << what << '\n';
    }
}

std::vector<std::int16_t> fresh(const Board& b, Color c) {
    std::vector<std::int16_t> v(static_cast<std::size_t>(halfka::l1()));
    halfka::refresh(b, c, v.data());
    return v;
}

bool is_legal(const Board& b, const Move& m) {
    const MoveList legal = b.legal_moves();
    for (std::size_t i = 0; i < legal.size(); ++i)
        if (legal[i] == m) return true;
    return false;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 4) {
        std::cout << "usage: forge_halfka_tests <net.nnue> <expected.txt> <scratch dir>\n";
        return 2;
    }
    const std::string net = argv[1], scratch = argv[3];
    std::string error;
    check(halfka::load(net, error), "load " + net + ": " + error);
    if (!halfka::active()) {
        std::cout << "HALFKA TESTS FAILED (no net)\n";
        return 1;
    }

    // 1) exact values, SIMD and scalar
    std::ifstream in(argv[2]);
    std::string line, first_fen;
    long long first_raw = 0;
    int positions = 0;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty() || line[0] == '#') continue;
        const std::size_t sp = line.find(' ');
        const long long want = std::stoll(line.substr(0, sp));
        const std::string fen = line.substr(sp + 1);
        Board b;
        if (!b.set_fen(fen)) {
            check(false, "bad FEN " + fen);
            continue;
        }
        halfka::set_force_scalar(false);
        const long long simd = halfka::evaluate_fresh_raw(b);
        halfka::set_force_scalar(true);
        const long long scalar = halfka::evaluate_fresh_raw(b);
        halfka::set_force_scalar(false);
        check(simd == want, "SIMD raw " + std::to_string(simd) + " != " + std::to_string(want) + " for " + fen);
        check(scalar == want, "scalar raw " + std::to_string(scalar) + " != " + std::to_string(want) + " for " + fen);
        if (positions++ == 0) {
            first_fen = fen;
            first_raw = want;
        }
    }
    check(positions >= 100, "at least 100 expected positions (read " + std::to_string(positions) + ")");

    // 2) incremental == refresh along random legal lines
    std::mt19937 rng(20261030);
    long long checks = 0;
    for (int g = 0; g < 20; ++g) {
        Board b;
        (void)b.set_fen(Board::StandardStartFen);
        std::vector<std::int16_t> acc[2] = {fresh(b, White), fresh(b, Black)};
        for (int p = 0; p < 120; ++p) {
            const MoveList legal = b.legal_moves();
            if (legal.size() == 0) break;
            const Move m = legal[static_cast<std::size_t>(rng() % legal.size())];
            const nnue::DirtyPieces dirty = nnue::dirty_pieces(b, m);
            const int king_before[2] = {b.king_square(White), b.king_square(Black)};
            const int bucket_before[2] = {halfka::feature_bucket(b, White), halfka::feature_bucket(b, Black)};
            Undo u;
            (void)b.make_move(m, u);
            for (const Color c : {White, Black}) {
                const std::vector<std::int16_t> ref = fresh(b, c);
                const int king = b.king_square(c), bucket = halfka::feature_bucket(b, c);
                if (king == king_before[c] && bucket == bucket_before[c]) {
                    for (const bool scalar : {false, true}) {
                        halfka::set_force_scalar(scalar);
                        std::vector<std::int16_t> out(ref.size()), same = acc[c];
                        halfka::apply(acc[c].data(), out.data(), c, king, bucket, dirty);
                        halfka::apply(same.data(), same.data(), c, king, bucket, dirty);
                        check(out == ref, std::string("incremental (out of place") + (scalar ? ", scalar" : "") + ") != refresh at " + b.fen());
                        check(same == ref, std::string("incremental (in place") + (scalar ? ", scalar" : "") + ") != refresh at " + b.fen());
                        checks += 2;
                    }
                    halfka::set_force_scalar(false);
                }
                acc[c] = ref;
            }
        }
    }
    check(checks > 1000, "incremental checks " + std::to_string(checks));

    // 3) a truncated copy is rejected and the loaded net stays
    {
        std::ifstream f(net, std::ios::binary);
        const std::vector<char> bytes((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
        const std::string cut = scratch + "/halfka_truncated_test.nnue";
        std::ofstream(cut, std::ios::binary).write(bytes.data(), static_cast<std::streamsize>(bytes.size() / 2));
        const int l1_before = halfka::l1();
        std::string why;
        check(!halfka::load(cut, why), "a truncated net must not load");
        check(!why.empty(), "a failed load explains why");
        check(halfka::active() && halfka::l1() == l1_before, "a failed load keeps the loaded net");
        Board b;
        (void)b.set_fen(first_fen);
        check(halfka::evaluate_fresh_raw(b) == first_raw, "the loaded net is unchanged after a failed load");
    }

    // 4) searches with two threads and the net loaded
    {
        Searcher searcher(16, 2);
        for (const std::string& fen : {std::string(Board::StandardStartFen), first_fen,
                                      std::string("r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP2BPPP/R2QKB1R w KQ - 0 8")}) {
            Board b;
            (void)b.set_fen(fen);
            SearchLimits limits;
            limits.depth = 9;
            const SearchInfo info = searcher.search(b, limits);
            check(is_legal(b, info.best_move), "2-thread search returns a legal move for " + fen);
            check(info.nodes > 0, "2-thread search counts nodes for " + fen);
        }
    }

    halfka::unload();
    check(!halfka::active(), "unload turns the HalfKA eval off");
    std::cout << (failures == 0 ? "HALFKA TESTS OK" : "HALFKA TESTS FAILED") << " (" << positions << " positions, "
              << checks << " incremental checks, " << failures << " failures)\n";
    return failures == 0 ? 0 : 1;
}
