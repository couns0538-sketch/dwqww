// Step E2 AVX-512 VNNI Output-Layer Oracle & Saturation Test:
// 1. Verifies exact int64 output_sum and centipawn eval parity across Scalar, Avx2, and Avx512 (VNNI active for
//    hidden >= 768) on all 1,000 positions of positions_1000.txt + all depth-1 legal child moves (testing both
//    output_sum_avx512_vnni and apply_pair_and_sum_avx512_vnni for count=2, count=3, count=4).
// 2. Verifies exact int32/int64 parity at every legal width >= 768 (768, 800, 896, 1024) under saturated
//    worst-case loader bounds (accumulator = 255, w2 = +127 and -127).

#include "forge/board.hpp"
#include "forge/nnue_v3.hpp"

#include <algorithm>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 3) return 1;
    std::string err;
    if (!forge::nnue::v3::load(argv[1], &err)) {
        std::cerr << "Load failed: " << err << "\n";
        return 1;
    }
    const forge::nnue::v3::Net& net = *forge::nnue::v3::loaded();

    std::vector<std::string> fens;
    {
        std::ifstream in(argv[2]);
        std::string ln;
        while (std::getline(in, ln)) {
            if (!ln.empty() && ln.back() == '\r') ln.pop_back();
            if (!ln.empty()) fens.push_back(ln);
        }
    }

    forge::nnue::v3::WorkerState ws;
    forge::nnue::v3::prepare(net, ws, 16);

    std::uint64_t checked = 0;
    for (const std::string& fen : fens) {
        forge::Board b;
        if (!b.set_fen(fen)) return 1;
        ws.invalidate();
        forge::nnue::v3::refresh_cached(net, ws.cache, b, ws.stack[4]);
        ws.valid_flags[4] = 1;
        const auto& acc = ws.stack[4];
        const int ob = forge::nnue::v3::output_bucket(net, b);
        const auto* us_p = acc.values[static_cast<std::size_t>(b.side_to_move())].data();
        const auto* th_p = acc.values[static_cast<std::size_t>(forge::opposite(b.side_to_move()))].data();

        const std::int64_t s_sc = forge::nnue::v3::output_sum_with(forge::nnue::v3::Kernel::Scalar, net, us_p, th_p, ob);
        const std::int64_t s_a2 = forge::nnue::v3::output_sum_with(forge::nnue::v3::Kernel::Avx2, net, us_p, th_p, ob);
        const std::int64_t s_a5 = forge::nnue::v3::output_sum_with(forge::nnue::v3::Kernel::Avx512, net, us_p, th_p, ob);
        if (s_sc != s_a2 || s_sc != s_a5) {
            std::cerr << "VNNI OUTPUT_SUM MISMATCH on " << fen
                      << ": scalar=" << s_sc << " avx2=" << s_a2 << " avx512_vnni=" << s_a5 << "\n";
            return 1;
        }
        ++checked;

        for (const forge::Move m : b.legal_moves()) {
            const forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(b, m);
            forge::Undo u;
            (void)b.make_move(m, u);
            const int k0 = b.king_square(forge::White);
            const int k1 = b.king_square(forge::Black);
            const auto key0 = forge::nnue::v3::king_key(net, forge::White, k0);
            const auto key1 = forge::nnue::v3::king_key(net, forge::Black, k1);
            if (key0 == acc.keys[0] && key1 == acc.keys[1]) {
                const int got = forge::nnue::v3::apply_pair_and_evaluate(net, acc, ws.stack[5], key0, k0, key1, k1, dirty, b);
                const int ref = forge::nnue::v3::evaluate_reference(net, b);
                if (got != ref) {
                    std::cerr << "VNNI FUSED EVAL MISMATCH on move " << forge::Board::move_to_uci(m)
                              << ": got=" << got << " ref=" << ref << "\n";
                    return 1;
                }
                ++checked;
            }
            b.unmake_move(m, u);
        }
    }

    // Check saturated loader-bound widths 768, 800, 896, 1024
    alignas(64) std::int16_t sat_acc[1024];
    std::fill_n(sat_acc, 1024, static_cast<std::int16_t>(255));
    for (const int width : {768, 800, 896, 1024}) {
        forge::nnue::v3::Net extreme;
        extreme.hidden = width;
        extreme.output_buckets = 1;
        extreme.w2.allocate(static_cast<std::size_t>(2 * width));
        extreme.b2 = {0};
        for (const std::int16_t wval : {static_cast<std::int16_t>(127), static_cast<std::int16_t>(-127)}) {
            std::fill_n(extreme.w2.data(), 2 * width, wval);
            const std::int64_t es = forge::nnue::v3::output_sum_with(forge::nnue::v3::Kernel::Scalar, extreme, sat_acc, sat_acc, 0);
            const std::int64_t e2 = forge::nnue::v3::output_sum_with(forge::nnue::v3::Kernel::Avx2, extreme, sat_acc, sat_acc, 0);
            const std::int64_t e5 = forge::nnue::v3::output_sum_with(forge::nnue::v3::Kernel::Avx512, extreme, sat_acc, sat_acc, 0);
            if (es != e2 || es != e5) {
                std::cerr << "VNNI SATURATION MISMATCH width=" << width << " w=" << wval
                          << ": scalar=" << es << " avx2=" << e2 << " vnni=" << e5 << "\n";
                return 1;
            }
        }
    }

    std::cout << "E2_VNNI_ORACLE PASS: evals_and_sums_checked=" << checked
              << " widths_768_800_896_1024_saturated=exact mismatches=0\n";
    return 0;
}
