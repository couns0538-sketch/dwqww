#include "forge/board.hpp"
#include "forge/search.hpp"
#include <iostream>
namespace forge {
struct SearcherTestProbe { static int qs(Searcher& s, Board& b) { return s.quiescence(b,0,-32000,32000); } };
}
int main() {
    forge::Board board;
    if (!board.set_fen("1q2k3/4n3/8/3r4/8/8/8/K2QR3 w - - 0 1")) return 2;
    auto move=board.parse_uci("d1d5"); if (!move) return 3;
    forge::Searcher searcher(4);
    std::cout << "SEE=" << board.static_exchange(*move) << " stand_pat=" << forge::Searcher::evaluate(board)
              << " qscore=" << forge::SearcherTestProbe::qs(searcher,board) << '\n';
}
