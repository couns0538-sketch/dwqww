// Original actual-Forge-API exactness check. No external engine implementation.
#include "forge/board.hpp"
#include "forge/nnue.hpp"
#include <array>
#include <bit>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <random>
#include <stdexcept>
#include <unordered_set>
#include <string>
#include "nnue_weights.inc"
using namespace forge;
using A=nnue::Accumulator;
constexpr std::size_t H=nnue::HiddenSize;
void need(bool yes,const char* why){if(!yes)throw std::runtime_error(why);}
// Disable auto-vectorization for the independent scalar integer oracle.
#if defined(__GNUC__) && !defined(__clang__)
__attribute__((optimize("no-tree-vectorize"),noinline))
#endif
std::array<std::array<std::int64_t,H>,2> scalar(const Board& b){
 std::array<std::array<std::int64_t,H>,2> a{};
 for(int p=0;p<2;++p){
  for(std::size_t h=0;h<H;++h)a[p][h]=NnueB1[h];
  for(int s=0;s<64;++s){const Piece pc=b.piece_at(s);if(pc==Empty)continue;
   const int relative=color_of(pc)==static_cast<Color>(p)?0:1;
   const int f=(relative*6+piece_type(pc)-1)*64+(p?s^56:s);
   for(std::size_t h=0;h<H;++h)a[p][h]+=NnueW1[static_cast<std::size_t>(f)*H+h];
  }
 }
 return a;
}
void equal(const Board& b,const A& f,const A& q){
 need(f.valid&&q.valid&&q.exact_int32,"actual backend tags");
 for(int p=0;p<2;++p)for(std::size_t h=0;h<H;++h)
  need(std::bit_cast<std::uint32_t>(f.values[p][h])==std::bit_cast<std::uint32_t>(static_cast<float>(q.exact_values[p][h])/4096.0F),"float/int32 lane bit mismatch");
 need(nnue::evaluate(b,f)==nnue::evaluate(b,q),"unchanged float output mismatch");
}
int main(int argc,char**argv){try{
 const std::uint64_t target=argc>1?std::stoull(argv[1]):1000000;need(target>=1,"position target");need(nnue::exact_int32_available(),"compiled actual AVX2 backend missing");
 std::mt19937_64 random(20261025);std::unordered_set<std::uint64_t> seen;seen.reserve(static_cast<std::size_t>(target*2));
 std::uint64_t checked=0,transitions=0,castles=0,ep=0,promotions=0,nulls=0,hash=14695981039346656037ULL;std::int64_t lo=INT64_MAX,hi=INT64_MIN;
 const std::array<const char*,7> fixtures={Board::StandardStartFen.data(),"r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1","4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1","4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1","1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 1","4k3/7P/8/8/8/8/p7/1R2K3 b - - 0 1","r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"};
 Board b;A f,q;int ply=0;std::uint64_t resets=0;
 auto start=[&](){need(b.set_fen(fixtures[resets<fixtures.size()?resets:0]),"fixture rejected");++resets;ply=0;nnue::set_exact_int32(false);nnue::refresh(b,f);nnue::set_exact_int32(true);nnue::refresh(b,q);};start();
 auto check=[&](){
  equal(b,f,q);A ff,qq;nnue::set_exact_int32(false);nnue::refresh(b,ff);nnue::set_exact_int32(true);nnue::refresh(b,qq);equal(b,ff,qq);
  need(std::memcmp(ff.values.data(),f.values.data(),sizeof(f.values))==0,"float incremental/fresh");
  need(std::memcmp(qq.exact_values.data(),q.exact_values.data(),sizeof(q.exact_values))==0,"int32 incremental/fresh");
  const auto s=scalar(b);for(int p=0;p<2;++p)for(std::size_t h=0;h<H;++h){need(s[p][h]==q.exact_values[p][h],"scalar int64/AVX2 int32 mismatch");lo=std::min(lo,s[p][h]);hi=std::max(hi,s[p][h]);}
 };
 // Enumerate every first move of sparse special fixtures, ensuring EP/promotions/castles.
 for(const char*fen:fixtures){need(b.set_fen(fen),"special FEN");nnue::set_exact_int32(false);nnue::refresh(b,f);nnue::set_exact_int32(true);nnue::refresh(b,q);A sf=f,sq=q;
  for(Move m:b.legal_moves()){auto dirty=nnue::dirty_pieces(b,m);Undo u;need(b.make_move(m,u),"special legal make");nnue::update(sf,f,dirty);nnue::update(sq,q,dirty);check();++transitions;castles+=m.is_castle();ep+=(m.flags&EnPassant)!=0;promotions+=m.is_promotion();b.unmake_move(m,u);} }
 start();
 while(checked<target){
  if(seen.insert(b.key()).second){check();++checked;for(unsigned char c:b.fen())hash=(hash^c)*1099511628211ULL;
   if(checked%4096==0&&!b.in_check()){NullUndo u;b.make_null_move(u);check();b.unmake_null_move(u);++nulls;}
  }
  auto moves=b.legal_moves();if(moves.empty()||ply>=180){start();continue;}Move m=moves[static_cast<std::size_t>(random()%moves.size())];const auto dirty=nnue::dirty_pieces(b,m);A nf,nq;nnue::update(f,nf,dirty);nnue::update(q,nq,dirty);
  if(transitions%37==0){A alias=q;nnue::update(alias,alias,dirty);need(std::memcmp(alias.exact_values.data(),nq.exact_values.data(),sizeof(nq.exact_values))==0,"in-place update mismatch");}
  Undo u;need(b.make_move(m,u),"legal move rejected");f=nf;q=nq;++ply;++transitions;castles+=m.is_castle();ep+=(m.flags&EnPassant)!=0;promotions+=m.is_promotion();
 }
 need(castles&&ep&&promotions,"special coverage missing");
 std::cout<<"{\"status\":\"PASS\",\"unique_positions\":"<<checked<<",\"incremental_fresh_mismatches\":0,\"scalar_avx2_mismatches\":0,\"float_output_mismatches\":0,\"transitions\":"<<transitions<<",\"castles\":"<<castles<<",\"en_passant\":"<<ep<<",\"promotions\":"<<promotions<<",\"nulls\":"<<nulls<<",\"q_min\":"<<lo<<",\"q_max\":"<<hi<<",\"corpus_fnv64\":"<<hash<<"}\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
