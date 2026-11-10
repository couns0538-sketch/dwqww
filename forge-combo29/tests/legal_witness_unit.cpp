#include "forge/board.hpp"
#include <cstdlib>
#include <iostream>
#include <random>
using namespace forge;
static void require(bool ok,const char*message){if(!ok){std::cerr<<"FAIL "<<message<<'\n';std::exit(1);}}
static Board position(const char*fen){Board b;require(b.set_fen(fen),fen);return b;}
static Move first(const Board&b,int from,Bitboard destinations){destinations&=~b.occupied(b.side_to_move())&~b.pieces(opposite(b.side_to_move()),King);if(!destinations)return Move::none();int to=lsb(destinations);return Move{static_cast<std::uint8_t>(from),static_cast<std::uint8_t>(to),0,static_cast<std::uint8_t>(b.piece_at(to)==Empty?Quiet:Capture)};}
static bool pawn_witness(const Board&b){auto p=pawn_push(b.side_to_move(),b.pieces(b.side_to_move(),Pawn))&~b.occupied()&~(Rank1BB|Rank8BB);if(!p)return false;int to=lsb(p);Move m{static_cast<std::uint8_t>(to-pawn_push_delta(b.side_to_move())),static_cast<std::uint8_t>(to),0,Quiet};require(b.is_pseudo_legal(m),"pawn witness pseudo");return b.is_legal(m);}
static Move knight_witness(const Board&b){auto n=b.pieces(b.side_to_move(),Knight);return n?first(b,lsb(n),attacks::knight(lsb(n))):Move::none();}
static Move king_witness(const Board&b){int k=b.king_square(b.side_to_move());return first(b,k,attacks::king(k));}
int main(){
    auto pinned=position("7k/8/8/7b/8/8/4P3/1N1K4 w - - 0 1");
    require(!pawn_witness(pinned),"pinned pawn unexpectedly legal");auto n=knight_witness(pinned);require(Board::move_to_uci(n)=="b1d2"&&pinned.is_legal(n)&&pinned.has_legal_move(),"knight after pinned pawn");
    auto later=position("7k/8/8/8/8/6b1/8/r1NK2N1 w - - 0 1");
    require(!later.is_legal(knight_witness(later))&&!later.is_legal(king_witness(later)),"first witnesses should fail");
    require(later.parse_uci("g1e2").has_value()&&later.has_legal_move(),"later knight fallback");
    auto capture=position("7k/8/8/8/8/8/8/3rK3 w - - 0 1");auto k=king_witness(capture);
    require(Board::move_to_uci(k)=="e1d1"&&k.is_capture()&&capture.is_legal(k)&&capture.has_legal_move(),"king capture witness");
    auto xray=position("7k/8/8/8/8/8/8/r2rK3 w - - 0 1");require(!xray.is_legal(king_witness(xray))&&xray.has_legal_move(),"king capture xray fallback");
    for(auto fen:{"7k/6Q1/6K1/8/8/8/8/8 b - - 0 1","7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"})require(!position(fen).has_legal_move(),"terminal fixture");
    std::uint64_t positions=0,pawn_hits=0,knight_hits=0,king_hits=0,fallback=0,capture_hits=0;
    auto check=[&](const Board&b){++positions;const auto before=b.fen();const auto key=b.key();bool expected=!b.legal_moves().empty();require(b.has_legal_move()==expected,"existence mismatch");require(b.fen()==before&&b.key()==key,"witness changed position");
        auto n=knight_witness(b),k=king_witness(b);for(auto m:{n,k})if(!m.is_none())require(b.is_pseudo_legal(m),"extension witness not pseudo legal");
        if(pawn_witness(b))++pawn_hits;else if(!n.is_none()&&b.is_legal(n)){++knight_hits;capture_hits+=n.is_capture();}else if(!k.is_none()&&b.is_legal(k)){++king_hits;capture_hits+=k.is_capture();}else ++fallback;};
    for(auto b:{pinned,later,capture,xray,position("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"),position("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),position("4r2k/8/8/8/1b6/8/8/4K3 w - - 0 1"),position("8/4k3/8/3pP3/8/8/8/K3R3 w - d6 0 1"),position("5b1k/4P3/3K4/8/8/8/8/8 w - - 0 1")}){check(b);for(auto m:b.legal_moves()){Undo u;(void)b.make_move(m,u);check(b);b.unmake_move(m,u);}}
    std::mt19937 rng(20261114);for(int game=0;game<100;++game){Board b;for(int ply=0;ply<180;++ply){check(b);auto legal=b.legal_moves();if(legal.empty())break;Undo u;(void)b.make_move(legal[rng()%legal.size()],u);}}
    require(knight_hits&&king_hits&&fallback&&capture_hits,"missing branch coverage");
    std::cout<<"PASS positions="<<positions<<" pawn_hits="<<pawn_hits<<" knight_hits="<<knight_hits<<" king_hits="<<king_hits<<" fallback="<<fallback<<" capture_hits="<<capture_hits<<" seed=20261114\n";
}
