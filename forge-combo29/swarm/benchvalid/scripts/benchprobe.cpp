// Instrumented replica of uci.cpp's `bench` branch.
// Same FEN list, same Searcher(16) (threads defaults to 1), same clear() per position,
// same limits.depth. The difference is that it prints one line PER POSITION,
// including bestmove / score / pv / depth / seldepth, which bench never prints.
//
// Build: see scripts/build_probe.sh. It is linked against the engine sources so it
// reads the real constant, not a copy.
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>

#include "forge/board.hpp"
#include "forge/search.hpp"

int main(int argc, char** argv) {
    int depth = 13;
    if (argc > 1) depth = std::stoi(argv[1]);

    // Deliberately duplicated from src/uci.cpp so the tool prints what bench uses.
    // scripts/check_fen_list.py asserts this list is byte-identical to the one in uci.cpp.
    static constexpr std::array<std::string_view, 8> fens{
        forge::Board::StandardStartFen,
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    };

    std::uint64_t total = 0;
    forge::Searcher bench_searcher(16);
    std::cout << "idx\tfen\tnodes\tbestmove\tscore\tdepth\tseldepth\tpvlen\tpv" << std::endl;
    for (std::size_t i = 0; i < fens.size(); ++i) {
        forge::Board board;
        if (!board.set_fen(fens[i])) {
            std::cout << "REFUSED " << i << " " << fens[i] << std::endl;
            continue;
        }
        forge::SearchLimits limits;
        limits.depth = depth;
        bench_searcher.clear();
        const forge::SearchInfo info =
            bench_searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
        total += info.nodes;
        std::string pv;
        for (std::size_t k = 0; k < info.pv.size(); ++k) {
            if (k) pv += ' ';
            pv += forge::Board::move_to_uci(info.pv[k]);
        }
        std::cout << i << '\t' << fens[i] << '\t' << info.nodes << '\t'
                  << (info.best_move.from == info.best_move.to ? "0000" : forge::Board::move_to_uci(info.best_move))
                  << '\t' << info.score << '\t' << info.depth << '\t' << info.seldepth << '\t'
                  << info.pv.size() << '\t' << pv << std::endl;
    }
    std::cout << "TOTAL\t" << total << std::endl;
    return 0;
}
