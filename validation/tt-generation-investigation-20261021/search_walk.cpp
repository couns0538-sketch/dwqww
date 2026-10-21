#include "forge/search.hpp"
#include "forge/nnue.hpp"
#include <iostream>
#include <stdexcept>
using namespace forge;
int main(){if(!nnue::available()||!nnue::enabled)throw std::runtime_error("frozen embedded NNUE required");Searcher s(16,1);Board b;SearchLimits limits;limits.depth=8;
 const char* moves[]={"e2e4","e7e5","g1f3","b8c6","f1b5","a7a6","b5a4","g8f6","e1g1","f8e7"};
 auto run=[&](int i){const auto fen=b.fen();auto r=s.search(b,limits,false,Searcher::TTAccess::Exclusive);std::cout<<"WALK root="<<i<<" fen="<<fen<<" depth="<<r.depth<<" seldepth="<<r.seldepth<<" score="<<r.score<<" nodes="<<r.nodes<<" best="<<Board::move_to_uci(r.best_move)<<" pv=";for(auto m:r.pv)std::cout<<Board::move_to_uci(m)<<',';std::cout<<'\n'<<std::flush;};
 run(0);run(1);int i=2;for(auto text:moves){auto m=b.parse_uci(text);if(!m)throw std::runtime_error("walk move illegal");Undo u;if(!b.make_move(*m,u))throw std::runtime_error("walk move rejected");run(i++);}
}
