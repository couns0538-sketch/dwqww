// Actual Worker/core regression through existing production friend. No copied search.
#include "forge/search.hpp"
#include "forge/nnue.hpp"
#include <chrono>
#include <cstdint>
#include <iostream>
#include <stdexcept>
extern "C" void forge_pv_diag_reset(std::uint64_t key);
extern "C" std::uint64_t forge_pv_diag_events();
extern "C" std::uint64_t forge_pv_diag_changed();
namespace forge {
struct SearcherTestProbe {
 static int run(Searcher& owner, Board board, bool seed, bool tt_pv, bool wide) {
  auto& w=owner.main_worker();w.clear();w.shared_.tt.clear();
  w.shared_.stop.store(false,std::memory_order_relaxed);
  w.shared_.ponder_hit_ns.store(0,std::memory_order_relaxed);
  w.all_workers_=nullptr;w.aborted_=false;w.local_nodes_=0;
  w.nodes_.store(0,std::memory_order_relaxed);w.node_limit_=0;
  w.node_limit_specified_=false;w.hard_limit_ms_=w.soft_limit_ms_=0;
  w.time_managed_=w.pondering_=false;w.start_=std::chrono::steady_clock::now();
  w.seldepth_=0;w.root_history_index_=board.history_size()-1;
  auto* ss=&w.stack_[5];ss->ply=1;ss->null_move_allowed=false;
  nnue::refresh(board,ss->accumulator);
  if(seed){auto move=board.parse_uci("d1e1");if(!move)throw std::runtime_error("seed move illegal");
   auto slot=w.shared_.tt.probe(board.key());
   w.shared_.tt.store(slot,board.key(),0,0,*move,7,BoundLower,tt_pv,board.halfmove_clock());}
  forge_pv_diag_reset(board.key());
  return w.search(board,ss,7,wide?-10000:-1,wide?10000:0,false);
 }
};
}
int main(){
 forge::Board b;if(!b.set_fen("6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1"))return 3;
 forge::Searcher owner(16,1);int failed=0;
 struct Case{const char* name;bool seed,pv,wide,required;};
 for(auto c:{Case{"PV_nonPVhit",true,false,true,true},Case{"PV_PVhit",true,true,true,false},
             Case{"PV_nohit",false,false,true,false},Case{"nullwindow_TTcut",true,false,false,false}}){
  const int score=forge::SearcherTestProbe::run(owner,b,c.seed,c.pv,c.wide);
  auto n=forge_pv_diag_events(),changed=forge_pv_diag_changed();
  // Require a real same-ply call for the targeted regression, not merely a final flag.
  if((c.required&&n==0)||changed!=0)++failed;
  std::cout<<"PV_CASE name="<<c.name<<" singular_calls="<<n<<" changed="<<changed<<" score="<<score<<'\n';
 }
 return failed?1:0;
}
