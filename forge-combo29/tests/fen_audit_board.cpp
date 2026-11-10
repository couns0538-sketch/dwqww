#include "forge/board.hpp"
#include <cstdlib>
#include <iostream>
#include <random>
#include <vector>
using namespace forge;
static void require(bool value,const char* text){if(!value){std::cerr<<"FAIL "<<text<<'\n';std::exit(1);}}
static bool same(const Board&a,const Board&b){
    if(a.fen()!=b.fen()||a.key()!=b.key()||a.pawn_key()!=b.pawn_key()||a.checkers()!=b.checkers()||a.key_history()!=b.key_history())return false;
    for(int s=0;s<64;++s)if(a.piece_at(s)!=b.piece_at(s))return false;
    for(auto c:{White,Black})if(a.occupied(c)!=b.occupied(c)||a.king_square(c)!=b.king_square(c))return false;
    auto am=a.legal_moves(),bm=b.legal_moves();if(am.size()!=bm.size())return false;
    for(size_t i=0;i<am.size();++i)if(!(am[i]==bm[i]))return false;
    return true;
}
int main(){
    Board original;for(auto text:{"g1f3","g8f6","f3g1","f6g8"}){auto m=original.parse_uci(text);require(m.has_value(),"seed move");Undo u;(void)original.make_move(*m,u);}
    const std::string base="4k3/8/8/8/8/8/8/4K3 w - - 0 1";
    const std::vector<std::string> bad={"", "8/8/8/8/8/8/8/8 w - - 0 1", base+" trailing",
        "4k3/8/8/8/8/8/8/4K3 w - - 0", "4k3/8/8/8/8/8/8/4K3 w - - -1 1",
        "4k3/8/8/8/8/8/8/4K3 w - - 0 0", "4k3/8/8/8/8/8/8/4K3 w - - 9223372036854775808 1",
        "4k3/8/8/8/8/8/8/4K3 x - - 0 1", "4k3/8/8/8/8/8/8/4K3 w K - 0 1",
        "4k3/8/8/8/8/8/8/4K3 w KK - 0 1", "4k3/8/8/8/8/8/8/4K3 w - d6 0 1",
        "4k3/8/8/3p4/8/8/8/4K3 b - d6 0 1", "4k3/8/8/8/8/8/8/4K3 w - z9 0 1",
        "4k3/8/8/8/8/8/4K3/4K3 w - - 0 1", "8/8/8/8/8/8/4k3/4K3 w - - 0 1",
        "P3k3/8/8/8/8/8/8/4K3 w - - 0 1", "4k3/8/8/8/8/P7/PPPPPPPP/4K3 w - - 0 1",
        "4k3/8/8/8/8/8/8/3xK3 w - - 0 1", "4k3/8/8/8/8/8/8/44K w - - 0 1",
        "4k3/8/8/8/8/8/8/4K3/8 w - - 0 1", "4k3/8/8/8/8/8/4K3 w - - 0 1",
        "4k3/8/8/8/8/8/8/K3R3 w - - 0 1", // late side-just-moved check rejection
        std::string(10000,'8')+" w - - 0 1"};
    for(const auto& fen:bad){Board b=original;std::string error;require(!b.set_fen(fen,&error),"explicit malformed FEN accepted");require(!error.empty(),"missing parse error");require(same(b,original),"rejection changed board");}
    std::vector<std::string> valid{std::string(Board::StandardStartFen),base,
        "4k3/8/8/3p4/8/8/8/4K3 w - d6 0 1",
        "4k3/8/8/8/8/8/8/4K3 w - - +0000 +0001",
        "4k3/8/8/8/8/8/8/4K3 w - - 9223372036854775807 9223372036854775807",
        "r3k2r/8/8/8/8/8/8/R3K2R w qkQK - 0 1",
        "4k3/11111111/8/8/8/8/8/4K3 w - - 0 1"};
    std::mt19937 rng(20261113);Board walk;
    for(int i=0;i<3000;++i){valid.push_back(walk.fen());auto moves=walk.legal_moves();if(moves.empty()||i%160==159){(void)walk.set_fen(Board::StandardStartFen);continue;}Undo u;(void)walk.make_move(moves[rng()%moves.size()],u);}
    auto roundtrip=[&](const std::string& fen){Board b=original;require(b.set_fen(fen),"valid FEN rejected");Board c;require(c.set_fen(b.fen()),"canonical FEN rejected");require(same(b,c),"roundtrip changed board");require(b.history_size()==1,"FEN retained old repetition history");};
    for(auto& fen:valid)roundtrip(fen);
    size_t accepted=0,rejected=0;
    const std::string chars="PNBRQKpnbrqk/1234567890 +-wKbqabcdefxyz\t\r\n";
    for(int i=0;i<20000;++i){auto fen=valid[rng()%valid.size()];int edits=1+rng()%4;while(edits--){size_t p=rng()%(fen.size()+1);switch(rng()%4){case 0:fen.insert(p,1,chars[rng()%chars.size()]);break;case 1:if(p<fen.size())fen.erase(p,1);break;case 2:if(p<fen.size())fen[p]=static_cast<char>(rng()%256);break;default:fen.resize(p);break;}}
        Board b=original;bool ok=b.set_fen(fen);if(ok){++accepted;roundtrip(fen);}else{++rejected;require(same(b,original),"mutated rejection changed board");}}
    std::cout<<"PASS explicit_rejections="<<bad.size()<<" valid_roundtrips="<<valid.size()<<" mutations_accepted="<<accepted<<" mutations_rejected="<<rejected<<" seed=20261113\n";
}
