// Does a qsearch-stored entry (depth 0) ever satisfy a DEEP main-search cutoff?
// Probe: solve a position with qsearch, then measure whether a depth-N search of the
// same position returns the qsearch answer with ~0 extra nodes.
#include "forge/board.hpp"
#include "forge/search.hpp"
#include <cstdio>
#include <cstdlib>
#include <string>
#include <iostream>
namespace forge {
struct SearcherTestProbe {
    static int qsearch(Worker& w, Board& b, SearchStack* ss, int a, int bb) { return w.qsearch(b, ss, a, bb); }
    static SearchStack* stack_base(Worker& w) { return &w.stack_[0]; }
    static void prepare(Worker& w) {
        for (SearchStack& ss : w.stack_) {
            ss.pv_length=0; ss.current_move=Move::none(); ss.excluded_move=Move::none();
            ss.moved_piece=Empty; ss.static_eval=ValueNone; ss.raw_eval=ValueNone;
            ss.continuation=nullptr; ss.double_extensions=0; ss.withheld_plies=0;
            ss.null_move_allowed=true; ss.arrival_index=0; ss.killers={};
            ss.accumulator.valid=false; ss.runtime_psqt.valid=false;
            ss.diff_known=false; ss.entered_null=false; ss.dirty.count=0; }
        for (int i=0;i<MaxPly+8;++i) w.stack_[static_cast<std::size_t>(i)].ply=i-4;
    }
    static void set_root_history(Worker& w, std::size_t i){ w.root_history_index_=i; }
};
}
using namespace forge;
int main(int argc,char**argv){
  const std::string fen=argv[1]; const int depth=atoi(argv[2]);
  const bool use_qs = argc>3 && std::string(argv[3])=="qswarm";
  Board b; std::string e;
  if(!b.set_fen(fen,&e)){ std::cout<<"REFUSED\n"; return 3; }
  Searcher s(32,1); Worker& w=s.main_worker();
  if(use_qs){
    SearcherTestProbe::prepare(w);
    SearcherTestProbe::set_root_history(w,b.history_size());
    SearchStack* ss=SearcherTestProbe::stack_base(w)+4;
    ss->ply=0;
    (void)SearcherTestProbe::qsearch(w,b,ss,-32001,32001);
  } else {
    w.clear();
  }
  SearchLimits lim; lim.depth=depth;
  const SearchInfo r=s.search(b,lim,false);
  std::cout<<"{\"fen\":\""<<fen<<"\",\"depth\":"<<depth<<",\"qswarm\":"<<(use_qs?1:0)
           <<",\"score\":"<<r.score<<",\"nodes\":"<<r.nodes<<",\"best\":\""
           <<Board::move_to_uci(r.best_move)<<"\"}\n";
  return 0;
}
