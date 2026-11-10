#include "forge/board.hpp"
#include <cstdlib>
#include <iostream>
#include <random>
using namespace forge;
#if !FORGE_SPD_PREFETCH_EARLY
#error "This test requires FORGE_SPD_PREFETCH_EARLY=1"
#endif
int main() {
    Board board;
    std::mt19937 rng(20261111);
    std::uint64_t positions=0, checked=0, accepted=0, rejected=0;
    std::uint64_t promotions=0, castles=0, doubles=0, ep=0, rejected_ep=0;
    auto check = [&] {
        ++positions;
        for (auto move : board.legal_moves()) {
            ++checked;
            std::uint64_t predicted = 0;
            const bool fast = board.key_after(move, predicted);
            const auto fen = board.fen();
            const auto old_key = board.key();
            Undo undo;
            (void)board.make_move(move, undo);
            if (fast && predicted != board.key()) {
                std::cerr << "FAIL key_after " << fen << " " << Board::move_to_uci(move)
                          << " predicted=" << predicted << " actual=" << board.key() << '\n';
                std::exit(1);
            }
            board.unmake_move(move, undo);
            if (board.key()!=old_key || board.fen()!=fen) std::abort();
            if (fast) {
                ++accepted;
                promotions += move.is_promotion();
                castles += move.is_castle();
                doubles += (move.flags & DoublePush) != 0;
                ep += (move.flags & EnPassant) != 0;
            } else {
                ++rejected;
                rejected_ep += (move.flags & EnPassant) != 0;
            }
        }
    };
    const char* fens[]={
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
        "1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
        "4k3/P7/8/8/8/8/7p/4K1R1 b - - 0 1",
        "4k3/8/8/3pP3/4K3/8/8/8 w - d6 0 1",
        "8/8/8/r4pPK/8/8/8/4k3 w - f6 0 1",
        "4k3/8/8/8/3p4/8/4P3/4K3 w - - 0 1",
        "4k3/3p4/8/4P3/8/8/8/4K3 b - - 0 1",
        "4k3/8/8/3p4/8/8/8/4K3 w - d6 0 1",
        "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"};
    for (auto fen:fens) { std::string error; if(!board.set_fen(fen,&error)){std::cerr<<error<<" "<<fen;return 2;} check(); }
    for (int game=0;game<100;++game) {
        (void)board.set_fen(Board::StandardStartFen);
        for(int ply=0;ply<180;++ply) {
            check(); auto legal=board.legal_moves(); if(legal.empty()) break;
            Undo undo; (void)board.make_move(legal[rng()%legal.size()],undo);
        }
    }
    if(!accepted || !rejected || !promotions || !castles || !doubles || !rejected_ep || ep) return 3;
    std::cout<<"PASS positions="<<positions<<" moves="<<checked<<" fast="<<accepted<<" fallback="<<rejected
             <<" fast_promotions="<<promotions<<" fast_castles="<<castles<<" fast_double_pushes="<<doubles
             <<" fast_ep="<<ep<<" fallback_ep="<<rejected_ep<<" seed=20261111\n";
}
