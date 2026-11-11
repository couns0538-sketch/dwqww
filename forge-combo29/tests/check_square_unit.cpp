#include "forge/search.hpp"
#include "forge/uci_output.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <exception>
#include <iostream>
#include <limits>
#include <optional>
#define private public
#include "search.cpp"
#undef private
#include <bit>
#include <cstdlib>
#include <fstream>
#include <random>
namespace forge {
struct SearcherTestProbe {
 static int quiet(const Worker& w,const Board& b,Move m) { return w.quiet_history(b,nullptr,m); }
 static int capture(const Worker& w,const Board& b,Move m) { return w.capture_history_value(b,m); }
 static void seed(Worker& w) {
  for (int c=0;c<2;++c) for(int f=0;f<64;++f) for(int t=0;t<64;++t)
   (*w.main_history_)[c][f][t]=static_cast<std::int16_t>((c*19+f*47+t*29)%1001-500);
 }
};
}
using namespace forge;
using Scored=MovePicker::Scored;
std::uint64_t boards=0, scores=0, selections=0, quiets=0, evasions=0, captures=0, promotions=0, castles=0, absent_b=0, absent_r=0, queens_only=0, pinned=0;
void require(bool ok,const char* message) { if(!ok){std::cerr<<"FAIL "<<message<<" board="<<boards<<'\n'; std::exit(1);} }
bool same(Move a,Move b){return std::bit_cast<std::uint32_t>(a)==std::bit_cast<std::uint32_t>(b);}
void check(const Board& b,const Worker& w) {
 ++boards;
 auto us=b.side_to_move();auto them=opposite(us);int k=b.king_square(them);auto occ=b.occupied();
 std::array<Bitboard,7> old{};
 old[Pawn]=attacks::pawn(them,k);old[Knight]=attacks::knight(k);old[Bishop]=attacks::bishop(k,occ);old[Rook]=attacks::rook(k,occ);old[Queen]=old[Bishop]|old[Rook];
 absent_b+=!(b.pieces(us,Bishop)|b.pieces(us,Queen)); absent_r+=!(b.pieces(us,Rook)|b.pieces(us,Queen));
 queens_only+=b.pieces(us,Queen)&&!b.pieces(us,Bishop)&&!b.pieces(us,Rook);
 MoveList all;b.generate_pseudo_legal(all,false);
 for(Move m:all) { promotions+=m.is_promotion();castles+=(m.flags&(KingCastle|QueenCastle))!=0; pinned+=piece_type(b.moved_piece(m))!=King&&!b.is_legal(m); }
 for(int mode=0;mode<3;++mode) {
  MovePicker p(b,w,nullptr,Move::none(),MovePicker::Mode::Main);
  // Poison dormant slots: safe candidate must write zeros, not just skip queries.
  p.check_squares_.fill(~Bitboard(0));
  std::vector<Scored> expected;
  MoveList list;b.generate_pseudo_legal(list,mode==2);
  for(Move m:list) {
   if(mode==0&&(m.is_capture()||m.is_promotion())) continue;
   int value;
   if(mode==2) {
    value=10*capture_value(b,m)+SearcherTestProbe::capture(w,b,m);
    if(m.is_promotion()) value+=m.promotion==Queen?20000:-5000;
   } else if(mode==1&&(m.is_capture()||m.is_promotion())) {
    value=1000000+10*capture_value(b,m)-SeePieceValue[piece_type(b.moved_piece(m))]/10;
   } else {
    value=SearcherTestProbe::quiet(w,b,m);
    if(old[piece_type(b.moved_piece(m))]&square_bb(m.to)) value+=12000;
   }
   expected.push_back({m,value});
  }
  if(mode==0){p.generate_quiets();++quiets;} else if(mode==1){p.generate_evasions();++evasions;} else{p.generate_captures();++captures;}
  require(p.count_==expected.size(),"generation size");
  for(std::size_t i=0;i<expected.size();++i){++scores;require(same(p.moves_[i].move,expected[i].move),"generation move");require(p.moves_[i].score==expected[i].score,"generation score");}
#if FORGE_SPD_CHECK_SQUARE_PRESENCE
  if(mode!=2) {
   require((b.pieces(us,Bishop)|b.pieces(us,Queen))||p.check_squares_[Bishop]==0,"absent bishop slot not zero");
   require((b.pieces(us,Rook)|b.pieces(us,Queen))||p.check_squares_[Rook]==0,"absent rook slot not zero");
  }
#endif
  for(std::size_t i=0;i<expected.size();++i) {
   if(i<4){std::size_t best=i;for(std::size_t j=i+1;j<expected.size();++j)if(expected[j].score>expected[best].score)best=j;std::swap(expected[i],expected[best]);}
   else if(i==4) std::sort(expected.begin()+i,expected.end(),[](const Scored&a,const Scored&b){return a.score>b.score;});
   require(same(p.pick_best(),expected[i].move),"selected move order");++selections;
  }
 }
}
int main(int argc,char**argv) {
 require(argc==2,"fixture path");SharedSearchState shared(1);auto worker=std::make_unique<Worker>(shared,0);SearcherTestProbe::seed(*worker);
 std::vector<std::string> fens={
 "7k/8/8/8/8/8/8/KQ6 w - - 0 1", "7k/8/8/8/8/8/8/KR6 w - - 0 1", "7k/8/8/8/8/8/8/KB6 w - - 0 1", "7k/8/8/8/8/8/8/KN6 w - - 0 1",
 "kq6/8/8/8/8/8/8/7K b - - 0 1", "kr6/8/8/8/8/8/8/7K b - - 0 1", "kb6/8/8/8/8/8/8/7K b - - 0 1",
 "4r2k/8/8/8/8/8/4B3/4K3 w - - 0 1", "4r2k/8/8/8/8/8/4R3/4K3 w - - 0 1", "4r2k/8/8/8/8/8/4Q3/4K3 w - - 0 1",
 "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
 "4r2k/3P4/8/8/8/8/8/4K3 w - - 0 1", "7k/P7/8/8/8/8/8/K7 w - - 0 1", "7k/8/8/3pP3/4K3/8/8/8 w - d6 0 1",
 "4r2k/8/8/8/1b6/8/PP6/4K1N1 w - - 0 1"};
 std::ifstream in(argv[1]);std::string line;while(std::getline(in,line))if(!line.empty())fens.push_back(line);
 std::mt19937 rng(20261111);
 for(const auto& fen:fens) {
  Board b;std::string error;require(b.set_fen(fen,&error),"fixture FEN");
  for(int ply=0;ply<24;++ply) {
   check(b,*worker);MoveList list;b.generate_pseudo_legal(list,false);std::vector<Move> legal;for(Move m:list)if(b.is_legal(m))legal.push_back(m);
   if(legal.empty())break;Undo undo;require(b.make_move(legal[rng()%legal.size()],undo),"legal move failed");
  }
 }
 require(promotions&&castles&&absent_b&&absent_r&&queens_only&&pinned,"coverage missing");
 std::cout<<"{\"passed\":true,\"boards\":"<<boards<<",\"scores\":"<<scores<<",\"selections\":"<<selections<<",\"promotions\":"<<promotions<<",\"castles\":"<<castles<<",\"absent_b\":"<<absent_b<<",\"absent_r\":"<<absent_r<<",\"queen_only\":"<<queens_only<<",\"nonking_illegal\":"<<pinned<<"}\n";
}
