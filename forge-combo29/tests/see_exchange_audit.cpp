// Diagnostic, not a pass/fail proof that minimax target exchanges equal LVA SEE.
// Uses legal move generation for king safety, but independent exchange recursion.
#include "forge/board.hpp"
#include <algorithm>
#include <array>
#include <cstdlib>
#include <iostream>
#include <random>
using namespace forge;
static constexpr std::array<int,7> value{0,100,300,300,500,900,0};
static std::uint64_t oracle_nodes=0;
static int gain(const Board& board, Move move) {
    return value[piece_type(board.captured_piece(move))] +
        (move.is_promotion() ? value[move.promotion]-value[Pawn] : 0);
}
static int best_reply(Board& board, int target) {
    ++oracle_nodes;
    int best=0; // Like conventional SEE, either side may decline the exchange.
    for (Move move : board.legal_moves(true)) {
        if (move.to != target || !move.is_capture()) continue;
        const int immediate = gain(board,move);
        Undo undo; (void)board.make_move(move,undo);
        const int score = immediate - best_reply(board,target);
        board.unmake_move(move,undo);
        best=std::max(best,score);
    }
    return best;
}
static int oracle(Board& board, Move move) {
    const int immediate = gain(board,move);
    Undo undo; (void)board.make_move(move,undo);
    const int score = immediate-best_reply(board,move.to);
    board.unmake_move(move,undo);
    return score;
}
int main(int argc, char**) {
    Board board; std::mt19937 rng(20261112);
    std::uint64_t tested=0, mismatches=0;
    auto check=[&](Move move) {
        if(move.is_castle())return;
        ++tested;
        const int exact=oracle(board,move), see=board.static_exchange(move);
        if(see!=exact) {
            ++mismatches;
            if(mismatches<=30) std::cout<<"DIFFERENCE fen="<<board.fen()<<" move="<<Board::move_to_uci(move)
                                      <<" LVA_SEE="<<see<<" legal_target_minimax="<<exact<<'\n';
        }
        // Binary static_exchange is meaningful only for a monotone threshold predicate.
        bool previous=true;
        for(int threshold=-2000;threshold<=2000;threshold+=25) {
            const bool current=board.see_ge(move,threshold);
            if((current && !previous) || current!=(see>=threshold)) {
                std::cerr<<"FAIL threshold consistency "<<board.fen()<<" "<<Board::move_to_uci(move)<<" threshold="<<threshold<<'\n';
                std::exit(2);
            }
            previous=current;
        }
        if(!board.see_ge(move,see) || (see<2000 && board.see_ge(move,see+1))) std::abort();
    };
    const char* corners[]={
        "8/3k4/8/2B5/3p4/8/3KP3/3n4 w - - 0 1",
        "8/4k3/8/3rN3/3Q4/8/2bK4/8 w - - 0 1",
        "1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
        "4k3/P7/8/8/8/8/7p/4K1R1 b - - 0 1",
        "4k3/8/8/3pP3/4K3/8/8/8 w - d6 0 1",
        "8/8/8/r4pPK/8/8/8/4k3 w - f6 0 1",
        "4r2k/8/8/8/1b6/8/8/4K3 w - - 0 1"};
    for(auto fen:corners){if(!board.set_fen(fen))return 3;for(auto move:board.legal_moves())check(move);}
    for(int game=0;game<30;++game){
        (void)board.set_fen(Board::StandardStartFen);
        for(int ply=0;ply<160;++ply){
            auto legal=board.legal_moves();if(legal.empty())break;
            if (argc > 1) {
                for (auto move:legal) check(move);
            } else {
                check(legal[rng()%legal.size()]);
                auto captures=board.legal_moves(true);if(!captures.empty())check(captures[rng()%captures.size()]);
            }
            Undo undo;(void)board.make_move(legal[rng()%legal.size()],undo);
        }
    }
    std::cout<<"PASS threshold_consistency tested="<<tested<<" oracle_differences="<<mismatches<<" oracle_nodes="<<oracle_nodes<<" seed=20261112\n";
    return 0;
}
