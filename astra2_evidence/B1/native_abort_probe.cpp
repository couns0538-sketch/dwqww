#include "forge/search.hpp"
#include <iostream>
#include <map>
using namespace forge;
int main() {
  const char* fens[] = {
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"
  };
  for(const char* fen: fens) {
    Board b; if(!b.set_fen(fen))return 2;
    std::map<int,SearchInfo> complete;
    for(int cap: {1000,2000,3000,4000,5000,6000,7000,8000,10000,12000,16000,20000,24000,32000,48000,64000}) {
      Searcher s(16,1); SearchLimits l;l.nodes=cap;l.nodes_specified=true;
      auto r=s.search(b,l,false);
      if(r.depth<=0)continue;
      if(!complete.contains(r.depth)) {Searcher d(16,1); SearchLimits q;q.depth=r.depth;complete[r.depth]=d.search(b,q,false);}
      auto& c=complete[r.depth];
      if(r.best_move!=c.best_move || r.score!=c.score) {
        std::cout<<"MISMATCH fen="<<fen<<" cap="<<cap<<" completeddepth="<<r.depth<<" returned="<<Board::move_to_uci(r.best_move)<<":"<<r.score<<" completed="<<Board::move_to_uci(c.best_move)<<":"<<c.score<<" nodes="<<r.nodes<<'\n';
        return 1;
      }
    }
  }
  std::cout<<"NO_MISMATCH\n";
}
