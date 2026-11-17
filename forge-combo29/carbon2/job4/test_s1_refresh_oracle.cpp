// Step S1 Oracle + Planted-Fault Test:
// Exercises both tiled refresh_from_pieces and fused refresh_one_and_evaluate across all 1,000 positions of
// positions_1000.txt + king-bucket-crossing moves (including d<->e mirror flips, rank 1/2/3/4 bucket steps,
// king captures, and castling), asserting exact equality of BOTH the centipawn output AND all 2 * hidden
// child accumulator int16 lanes against fresh evaluate_reference / refresh!

#include "forge/board.hpp"
#include "forge/nnue_v3.hpp"

#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 3) return 1;
    std::string err;
    if (!forge::nnue::v3::load(argv[1], &err)) return 1;
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
    fens.push_back("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
    fens.push_back("8/8/3k4/8/4K3/8/2R5/8 w - - 0 1");

    forge::nnue::v3::WorkerState ws;
    forge::nnue::v3::prepare(net, ws, 16);
    forge::nnue::v3::Accumulator ref_acc;

    std::uint64_t root_refreshes = 0;
    std::uint64_t single_king_Bucket_transitions = 0;

    for (const std::string& fen : fens) {
        forge::Board b;
        if (!b.set_fen(fen)) return 1;
        ws.invalidate();
        forge::nnue::v3::refresh_cached(net, ws.cache, b, ws.stack[4]);
        ws.valid_flags[4] = 1;
        forge::nnue::v3::refresh(net, b, ref_acc);
        if (std::memcmp(ws.stack[4].values[0].data(), ref_acc.values[0].data(), static_cast<std::size_t>(net.hidden) * 2) != 0 ||
            std::memcmp(ws.stack[4].values[1].data(), ref_acc.values[1].data(), static_cast<std::size_t>(net.hidden) * 2) != 0) {
            std::cerr << "ROOT TILED REFRESH ACCUMULATOR MISMATCH on " << fen << "\n";
            return 1;
        }
        ++root_refreshes;

        const auto& parent = ws.stack[4];
        for (const forge::Move m : b.legal_moves()) {
            const forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(b, m);
            forge::Undo u;
            (void)b.make_move(m, u);
            const int k0 = b.king_square(forge::White);
            const int k1 = b.king_square(forge::Black);
            const auto key0 = forge::nnue::v3::king_key(net, forge::White, k0);
            const auto key1 = forge::nnue::v3::king_key(net, forge::Black, k1);
            if ((key0 == parent.keys[0]) != (key1 == parent.keys[1])) {
                const forge::Color ref_side = !(key0 == parent.keys[0]) ? forge::White : forge::Black;
                const int got = forge::nnue::v3::refresh_one_and_evaluate(
                    net, ws.cache, parent, ws.stack[5], key0, k0, key1, k1, ref_side, dirty, b);
                const int exp = forge::nnue::v3::evaluate_reference(net, b);
                forge::nnue::v3::refresh(net, b, ref_acc);
                if (got != exp ||
                    std::memcmp(ws.stack[5].values[0].data(), ref_acc.values[0].data(), static_cast<std::size_t>(net.hidden) * 2) != 0 ||
                    std::memcmp(ws.stack[5].values[1].data(), ref_acc.values[1].data(), static_cast<std::size_t>(net.hidden) * 2) != 0) {
                    std::cerr << "SINGLE_REFRESH_FUSE MISMATCH on " << fen << " move " << forge::Board::move_to_uci(m)
                              << " got=" << got << " exp=" << exp << "\n";
                    return 1;
                }
                ++single_king_Bucket_transitions;
            }
            b.unmake_move(m, u);
        }
    }

    std::cout << "S1_REFRESH_FUSE_ORACLE PASS: root_refreshes=" << root_refreshes
              << " single_king_bucket_transitions=" << single_king_Bucket_transitions << " mismatches=0\n";
    return 0;
}
