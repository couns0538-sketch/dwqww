#include "forge/board.hpp"
#include <cstdlib>
#include <iostream>
using namespace forge;
static void require(bool ok, const char* message) { if (!ok) { std::cerr<<"FAIL "<<message<<'\n'; std::exit(1); } }
static Board position(const char* fen) { Board b; std::string error; require(b.set_fen(fen,&error),fen); return b; }
static void promotions(const char* fen, int pseudo_count, const char* legal_prefix) {
    auto b=position(fen); int pseudo=0,legal=0;
    for(auto m:b.pseudo_legal_moves())if(m.is_promotion())++pseudo;
    for(auto m:b.legal_moves())if(m.is_promotion()) {
        ++legal;
        require(Board::move_to_uci(m).substr(0,4)==legal_prefix,"promotion outside pin line");
        const auto before=b.fen(); const auto key=b.key();
        Undo u;(void)b.make_move(m,u);require(!b.in_check(opposite(b.side_to_move())),"promoted mover left in check");
        b.unmake_move(m,u);require(b.fen()==before && b.key()==key,"promotion undo");
    }
    require(pseudo==pseudo_count,"unexpected pseudo promotion count");
    require(legal==(*legal_prefix ? 4 : 0),"unexpected legal promotion count");
}
int main() {
    promotions("3nrn1k/4P3/8/8/8/8/8/4K3 w - - 0 1",8,"");
    promotions("4k3/8/8/8/8/8/4p3/3NRN1K b - - 0 1",8,"");
    promotions("5b1k/4P3/3K4/8/8/8/8/8 w - - 0 1",8,"e7f8");
    promotions("8/8/8/8/8/3k4/4p3/5B1K b - - 0 1",8,"e2f1");
    for(auto entry : {std::pair{"8/4k3/8/3pP3/8/8/8/K3R3 w - d6 0 1","e5d6"},
                     std::pair{"k3r3/8/8/8/3Pp3/8/4K3/8 b - d3 0 1","e4d3"}}) {
        auto b=position(entry.first);auto m=b.parse_uci(entry.second);require(m.has_value(),"missing EP double check");
        require(b.gives_check(*m),"EP gives_check"); const auto before=b.fen();const auto key=b.key();
        Undo u;(void)b.make_move(*m,u);require(popcount(b.checkers())==2,"EP did not produce two checkers");
        require(popcount(b.checkers() & b.pieces(Pawn))==1 && popcount(b.checkers() & b.pieces(Rook))==1,"wrong EP checkers");
        for(auto reply:b.legal_moves())require(piece_type(b.piece_at(reply.from))==King,"nonking reply to EP double check");
        b.unmake_move(*m,u);require(b.fen()==before && b.key()==key,"EP undo");
    }
    for(int side=0;side<2;++side) for(int flank=0;flank<2;++flank) {
        auto b=position(side==0 ? "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1" : "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1");
        const char* text=side==0 ? (flank==0 ? "a1a8":"h1h8") : (flank==0 ? "a8a1":"h8h1");
        auto m=b.parse_uci(text);require(m.has_value(),"missing rook capture");const auto before=b.fen();const auto key=b.key();
        Undo u;(void)b.make_move(*m,u);require(b.castling_rights()==(flank==0 ? 5:10),"rook capture did not clear both corner rights");
        Board fresh;require(fresh.set_fen(b.fen()) && fresh.key()==b.key(),"rights hash inconsistent");
        b.unmake_move(*m,u);require(b.castling_rights()==15 && b.fen()==before && b.key()==key,"castling rights undo");
    }
    std::cout<<"PASS 4 pinned-promotion fixtures, 2 EP double-check fixtures, 4 rook-capture rights fixtures\n";
}
