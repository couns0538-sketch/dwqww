#include "forge/board.hpp"
#include "forge/search.hpp"
#include <array>
#include <iostream>
#include <stdexcept>
#include <string_view>
int main() {
    constexpr std::array<std::string_view, 8> fens{
        forge::Board::StandardStartFen,
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    };
    forge::Searcher searcher(16);
    searcher.set_threads(1);
    std::uint64_t total = 0;
    std::cout << "case\tdepth\tnodes\tscore\tbestmove\tpv\n";
    for (std::size_t i = 0; i < fens.size(); ++i) {
        forge::Board board;
        if (!board.set_fen(fens[i])) throw std::runtime_error("bad bench FEN");
        forge::SearchLimits limits;
        limits.depth = 11;
        searcher.clear();
        const auto result = searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
        total += result.nodes;
        std::cout << i << '\t' << result.depth << '\t' << result.nodes << '\t' << result.score
                  << '\t' << forge::Board::move_to_uci(result.best_move) << '\t';
        bool first = true;
        for (const auto move : result.pv) {
            if (!board.is_pseudo_legal(move) || !board.is_legal(move)) throw std::runtime_error("illegal PV");
            if (!first) std::cout << ',';
            first = false;
            std::cout << forge::Board::move_to_uci(move);
            forge::Undo undo;
            if (!board.make_move(move, undo)) throw std::runtime_error("PV make failed");
        }
        std::cout << '\n';
    }
    std::cout << "total_nodes\t" << total << '\n';
}
