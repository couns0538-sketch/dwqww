#include "forge/search.hpp"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <string>
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    std::ifstream in(argv[1]);
    if (!in) return 3;
    forge::tune::MateAlphaGuard = true;
    forge::Searcher searcher(16, 1);
    int count=0, excluded=0, faults=0, record=0;
    std::string fen;
    while (count<200 && std::getline(in,fen)) {
        ++record;
        forge::Board board;
        if (!board.set_fen(fen)) { std::cout << "INVALID " << record << ' ' << fen << '\n'; return 4; }
        const auto moves=board.legal_moves();
        if (moves.empty() || board.is_insufficient_material() || board.halfmove_clock()>=100) { ++excluded; continue; }
        std::cout << "INPUT record=" << record << " fen=" << fen << std::endl;
        searcher.clear(); forge::SearchLimits limits; limits.depth=10;
        const auto result=searcher.search(board,limits,false,forge::Searcher::TTAccess::Exclusive);
        const bool legal=std::find(moves.begin(),moves.end(),result.best_move)!=moves.end();
        const bool score=result.score>=-forge::MateValue && result.score<=forge::MateValue;
        const bool depth=result.depth==10 || forge::is_mate_score(result.score);
        faults+=!legal || !score || !depth;
        ++count;
        std::cout << "RESULT " << count << " legal=" << legal << " score=" << result.score << " depth=" << result.depth << " nodes=" << result.nodes << " move=" << forge::Board::move_to_uci(result.best_move) << std::endl;
    }
    std::cout << "SUMMARY searches=" << count << " exclusions=" << excluded << " faults=" << faults << std::endl;
    return count==200 && faults==0 ? 0 : 1;
}
