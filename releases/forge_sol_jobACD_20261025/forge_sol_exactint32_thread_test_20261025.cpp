// Original concurrent config/actual-core regression; all boards/accumulators private.
#include "forge/nnue.hpp"
#include <atomic>
#include <iostream>
#include <thread>
#include <vector>
#include <random>
int main(){using namespace forge;std::atomic<int> failures{0};std::vector<std::thread> threads;
 if(!nnue::exact_int32_available())return 2;
 // Match actual UCI lifecycle: construct Board on controller before workers.
 Board controller_bootstrap;
 for(int t=0;t<4;++t)threads.emplace_back([&,t]{std::mt19937 rng(20261025U+static_cast<unsigned>(t));Board b;
  for(int n=0;n<2000;++n){if(n%80==0||!b.has_legal_move())(void)b.set_fen(Board::StandardStartFen);
   nnue::set_exact_int32((n+t)%2==0);nnue::Accumulator parent,child,fresh;nnue::refresh(b,parent);auto ms=b.legal_moves();if(ms.empty())continue;auto m=ms[rng()%ms.size()];auto dirty=nnue::dirty_pieces(b,m);nnue::update(parent,child,dirty);Undo u;if(!b.make_move(m,u)){++failures;continue;}nnue::refresh(b,fresh);if(nnue::evaluate(b,child)!=nnue::evaluate(b,fresh))++failures;
  }});
 for(auto&thread:threads)thread.join();std::cout<<"threads4 transitions8000 failures "<<failures.load()<<'\n';return failures.load()!=0;}
