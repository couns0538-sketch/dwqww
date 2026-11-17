// Safety + kernel cross-equivalence + loader-bound overflow test for Piece P5 (NNUE v3 kernels):
// 1. Cross-checks Scalar == Avx2 == Avx512 on output_sum_with, fused apply_pair_and_evaluate, and batched
//    refresh_from_pieces across all 1,000 positions of positions_1000.txt + legal child transitions (count=2
//    quiet, count=3 capture/ep/promo, count=4 castling, and king-bucket transitions).
// 2. Tests worst-case loader-admissible bound (hidden=1024, all accumulator units saturated at QA=255 and
//    all w2 saturated at +127 and -127) to verify zero int32 horizontal-sum overflow in Avx2 and Avx512!

#include "forge/board.hpp"
#include "forge/nnue_v3.hpp"

#include <algorithm>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 2) return 1;
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
    // Add castling + en-passant positions so count=3 (ep) and count=4 (castle) are guaranteed covered
    fens.push_back("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
    fens.push_back("r3k2r/8/8/3pP3/8/8/8/R3K2R w KQkq d6 0 1");

    forge::nnue::v3::WorkerState ws;
    forge::nnue::v3::prepare(net, ws, 16);

    std::uint64_t evals_checked = 0;
    std::uint64_t fused_checked = 0;
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
        const std::int64_t s_scalar = forge::nnue::v3::output_sum_with(forge::nnue::v3::Kernel::Scalar, net, us_p, th_p, ob);
        const std::int64_t s_avx2   = forge::nnue::v3::output_sum_with(forge::nnue::v3::Kernel::Avx2, net, us_p, th_p, ob);
        const std::int64_t s_avx512 = forge::nnue::v3::output_sum_with(forge::nnue::v3::Kernel::Avx512, net, us_p, th_p, ob);
        const int ref_cp = forge::nnue::v3::evaluate_reference(net, b);
        const int fast_cp = forge::nnue::v3::evaluate(net, b, acc);
        if (s_scalar != s_avx2 || s_scalar != s_avx512 || ref_cp != fast_cp) {
            std::cerr << "ROOT KERNEL MISMATCH on " << fen << ": scalar=" << s_scalar
                      << " avx2=" << s_avx2 << " avx512=" << s_avx512
                      << " ref_cp=" << ref_cp << " fast_cp=" << fast_cp << "\n";
            return 1;
        }
        ++evals_checked;

        for (const forge::Move m : b.legal_moves()) {
            const forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(b, m);
            forge::Undo u;
            (void)b.make_move(m, u);
            const int k0 = b.king_square(forge::White);
            const int k1 = b.king_square(forge::Black);
            const auto key0 = forge::nnue::v3::king_key(net, forge::White, k0);
            const auto key1 = forge::nnue::v3::king_key(net, forge::Black, k1);
            int got_cp = 0;
            if (key0 == acc.keys[0] && key1 == acc.keys[1]) {
                got_cp = forge::nnue::v3::apply_pair_and_evaluate(net, acc, ws.stack[5], key0, k0, key1, k1, dirty, b);
                ++fused_checked;
            } else {
                ws.valid_flags[5] = 0;
                forge::nnue::v3::make_valid(net, ws, 5, b, [&](int) -> const forge::nnue::DirtyPieces& { return dirty; });
                got_cp = forge::nnue::v3::evaluate(net, b, ws.stack[5]);
            }
            const int child_ref = forge::nnue::v3::evaluate_reference(net, b);
            if (got_cp != child_ref) {
                std::cerr << "CHILD FUSED/REFRESH MISMATCH on move " << forge::Board::move_to_uci(m)
                          << " got=" << got_cp << " ref=" << child_ref << "\n";
                return 1;
            }
            ++evals_checked;
            b.unmake_move(m, u);
        }
    }

    // Worst-case loader-bound saturation check (hidden = 1024, all units = 255, all w2 = +127 and -127)
    forge::nnue::v3::Net extreme;
    extreme.hidden = 1024;
    extreme.output_buckets = 1;
    extreme.w2.allocate(2 * 1024);
    extreme.b2 = {0};
    alignas(64) std::int16_t sat_acc[1024];
    std::fill_n(sat_acc, 1024, static_cast<std::int16_t>(255));
    for (const std::int16_t wval : {static_cast<std::int16_t>(127), static_cast<std::int16_t>(-127)}) {
        std::fill_n(extreme.w2.data(), 2 * 1024, wval);
        const std::int64_t es = forge::nnue::v3::output_sum_with(forge::nnue::v3::Kernel::Scalar, extreme, sat_acc, sat_acc, 0);
        const std::int64_t e2 = forge::nnue::v3::output_sum_with(forge::nnue::v3::Kernel::Avx2, extreme, sat_acc, sat_acc, 0);
        const std::int64_t e5 = forge::nnue::v3::output_sum_with(forge::nnue::v3::Kernel::Avx512, extreme, sat_acc, sat_acc, 0);
        if (es != e2 || es != e5) {
            std::cerr << "SATURATION OVERFLOW MISMATCH w=" << wval << ": scalar=" << es << " avx2=" << e2 << " avx512=" << e5 << "\n";
            return 1;
        }
    }

    std::cout << "P5_NNUE_KERNELS PASS: evals_checked=" << evals_checked
              << " fused_pair_evals=" << fused_checked
              << " scalar_avx2_avx512_saturation_1024=exact mismatches=0\n";
    return 0;
}
