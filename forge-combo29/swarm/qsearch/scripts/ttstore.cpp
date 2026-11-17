#include <optional>
// Property 4, precise question: when qsearch stores into a position that already
// holds a DEEP main-search entry, which fields does it overwrite?
// Prints the entry before and after.
#include "forge/board.hpp"
#include "forge/search.hpp"
#include <cstdio>
#include <cstdlib>
#include <string>
#include <iostream>
namespace forge {
struct SearcherTestProbe {
    static int qsearch(Worker& w, Board& b, SearchStack* ss, int a, int bb){ return w.qsearch(b,ss,a,bb); }
    static SearchStack* stack_base(Worker& w){ return &w.stack_[0]; }
    static void prepare(Worker& w){
        for(SearchStack& s:w.stack_){ s.pv_length=0;s.current_move=Move::none();s.excluded_move=Move::none();
            s.moved_piece=Empty;s.static_eval=ValueNone;s.raw_eval=ValueNone;s.continuation=nullptr;
            s.double_extensions=0;s.withheld_plies=0;s.null_move_allowed=true;s.arrival_index=0;s.killers={};
            s.accumulator.valid=false;s.runtime_psqt.valid=false;s.diff_known=false;s.entered_null=false;s.dirty.count=0; }
        for(int i=0;i<MaxPly+8;++i) w.stack_[static_cast<std::size_t>(i)].ply=i-4; }
    static void set_root_history(Worker& w,std::size_t i){ w.root_history_index_=i; }
    static void plant(Worker& w, Board& b, int score, Move mv, int depth, Bound bd, bool pv){
        TTProbe p=w.shared_.tt.probe(b.key());
        w.shared_.tt.store(p,b.key(),score,ValueNone,mv,depth,bd,pv,(std::uint16_t)b.halfmove_clock()); }
    static TTEntry peek(Worker& w, Board& b){ return w.shared_.tt.probe(b.key()).entry; }
};
}
using namespace forge;
static std::string desc(const TTEntry& e){
  if(!e.occupied()) return "EMPTY";
  char buf[200];
  std::snprintf(buf,sizeof buf,"depth=%d score=%d move=%s bound=%d pv=%d gen=%d",
    (int)e.depth,(int)e.score, Board::move_to_uci(e.move).c_str(), (int)e.bound(), (int)e.pv(), (int)e.generation());
  return buf;
}
int main(int argc,char**argv){
  const std::string fen=argv[1];
  const std::string deepMove=argc>2?argv[2]:"e2a6";
  const int deepScore=argc>3?atoi(argv[3]):-140;
  const int deepDepth=argc>4?atoi(argv[4]):20;
  Board b; std::string e;
  if(!b.set_fen(fen,&e)){ std::cout<<"REFUSED "<<e<<"\n"; return 3; }
  Searcher s(32,1); Worker& w=s.main_worker();
  const std::optional<Move> dm=b.parse_uci(deepMove);
  if(!dm){ std::cout<<"BAD MOVE\n"; return 4; }
  // Plant a deep main-search entry, as depth-20 search would have left it.
  SearcherTestProbe::plant(w,b,deepScore,*dm,deepDepth,BoundUpper,false);
  const TTEntry before=SearcherTestProbe::peek(w,b);
  // Now run qsearch at the same position.
  SearcherTestProbe::prepare(w);
  SearcherTestProbe::set_root_history(w,b.history_size());
  SearchStack* ss=SearcherTestProbe::stack_base(w)+4; ss->ply=0;
  (void)SearcherTestProbe::qsearch(w,b,ss,-32001,32001);
  const TTEntry after=SearcherTestProbe::peek(w,b);
  std::cout<<"before: "<<desc(before)<<"\n";
  std::cout<<"after : "<<desc(after)<<"\n";
  const bool depthKept = after.depth==before.depth;
  const bool moveChanged = !(after.move==before.move);
  const bool scoreChanged = after.score!=before.score;
  std::cout<<"depth_kept="<<depthKept<<" move_changed="<<moveChanged<<" score_changed="<<scoreChanged<<"\n";
  if(depthKept && (moveChanged||scoreChanged))
    std::cout<<"*** DEEP ENTRY PARTIALLY OVERWRITTEN BY A DEPTH-0 QSEARCH STORE\n";
  return 0;
}
