#include "forge/board.hpp"
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
using namespace forge;
static_assert(MoveList::Capacity==256,"Replay must use production capacity");
void require(bool ok,const char*m){if(!ok){std::cerr<<"FAIL "<<m<<'\n';std::exit(1);}}
std::string mirror(const Board&b){std::ostringstream out;constexpr char chars[]=" PNBRQKpnbrqk";for(int r=7;r>=0;--r){int empty=0;for(int f=0;f<8;++f){auto p=b.piece_at((r*8+f)^56);if(p==Empty)++empty;else{if(empty)out<<empty;empty=0;char c=chars[p];out<<static_cast<char>(is_white(p)?std::tolower(c):std::toupper(c));}}if(empty)out<<empty;if(r)out<<'/';}out<<" b - - 0 1";return out.str();}
int main(int argc,char**argv){require(argc==2,"fixture path");std::ifstream in(argv[1]);require(bool(in),"open fixtures");std::string row;size_t positions=0,maximum=0,promotions=0,captures=0,checked=0;while(std::getline(in,row)){std::istringstream line(row);size_t expected,legal_count;line>>expected>>legal_count;std::string fen;std::getline(line,fen);Board original;require(original.set_fen(fen),"accepted fixture became invalid");for(int side=0;side<2;++side){Board b=original;if(side)require(b.set_fen(mirror(original)),"mirrored fixture invalid");auto moves=b.pseudo_legal_moves();require(moves.size()==expected,"pseudo count changed");require(b.legal_moves().size()==legal_count,"legal count changed");require(b.has_legal_move()==(legal_count!=0),"existence changed");auto noisy=b.pseudo_legal_moves(true);require(noisy.size()<=moves.size(),"noisy count exceeds all");
#if FORGE_SPD_NO_ZERO_MOVELISTS >= 2
MoveList quiet;b.generate_pseudo_legal(quiet,Board::GenMode::Quiets);require(quiet.size()+noisy.size()==moves.size(),"quiets/noisy partition");
#endif
for(auto m:moves){require(b.is_pseudo_legal(m),"generated move not pseudo legal");promotions+=m.is_promotion();captures+=m.is_capture();}maximum=std::max(maximum,moves.size());checked+=b.in_check();++positions;}}
Board bad;for(auto fen:{"k7/8/8/8/8/P7/PPPPPPPP/4K3 w - - 0 1","k7/8/8/8/8/PPPPPPPP/QQ6/4K3 w - - 0 1","k7/8/8/8/8/NNNNNNNN/NNNNNNNN/4K3 w - - 0 1"})require(!bad.set_fen(fen),"impossible inventory accepted");
std::cout<<"PASS production_capacity="<<MoveList::Capacity<<" positions="<<positions<<" max_pseudo="<<maximum<<" headroom="<<MoveList::Capacity-maximum<<" promotions="<<promotions<<" captures="<<captures<<" in_check="<<checked<<" inventory_rejections=3\n";
}
