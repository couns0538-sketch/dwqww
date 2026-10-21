// Actual-core frame-lifetime regression through existing SearcherTestProbe friendship.
#include "forge/search.hpp"
#include "forge/nnue.hpp"
#include <chrono>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
namespace forge {
struct SearcherTestProbe {
 struct Result { int score; bool tt_pv,aborted; std::uint64_t nodes; std::vector<Move> pv; };
 static Result run(Searcher& owner, Board& board, bool seed, bool seed_pv, bool wide, bool abort_verification) {
  auto& w=owner.main_worker();w.clear();w.shared_.tt.clear();
  w.shared_.stop.store(false,std::memory_order_relaxed);
  w.shared_.ponder_hit_ns.store(0,std::memory_order_relaxed);
  w.all_workers_=nullptr;w.aborted_=false;w.local_nodes_=0;
  w.nodes_.store(0,std::memory_order_relaxed);
  w.node_limit_=abort_verification?2:0;w.node_limit_specified_=abort_verification;
  w.hard_limit_ms_=w.soft_limit_ms_=0;w.time_managed_=w.pondering_=false;
  w.start_=std::chrono::steady_clock::now();w.seldepth_=0;
  w.root_history_index_=board.history_size()-1;
  auto* ss=&w.stack_[5];ss->ply=1;ss->null_move_allowed=false;
  nnue::refresh(board,ss->accumulator);
  if(seed){auto move=board.parse_uci("d1e1");
   if(!move)throw std::runtime_error("legal singular seed required");
   auto slot=w.shared_.tt.probe(board.key());
   w.shared_.tt.store(slot,board.key(),0,0,*move,7,BoundLower,seed_pv,board.halfmove_clock());}
  const int score=w.search(board,ss,7,wide?-10000:-1,wide?10000:0,false);
  Result result{score,ss->tt_pv,w.aborted_,w.local_nodes_,{}};
  if(ss->pv_length<0||ss->pv_length>MaxPly+1)throw std::runtime_error("invalid PV length");
  result.pv.assign(ss->pv.begin(),ss->pv.begin()+ss->pv_length);
  return result;
 }
};
}
int main(){
 using namespace forge;int assertions=0,failures=0;
 auto check=[&](bool okay,const std::string& label){++assertions;if(!okay){++failures;std::cerr<<"FAIL "<<label<<'\n';}};
 Board board;check(board.set_fen("6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1"),"fixture parses");
 const auto fen=board.fen();const auto key=board.key();const auto pawn=board.pawn_key();const auto history=board.history_size();const bool checked=board.in_check();
 Searcher owner(16,1);
 struct Case{const char* name;bool seed,pv,wide,abort;};
 for(auto c:{Case{"PV_nonPVhit",true,false,true,false},Case{"PV_PVhit",true,true,true,false},
             Case{"PV_nohit",false,false,true,false},Case{"nullwindow_TTcut",true,false,false,false},
             Case{"PV_abort_verification",true,false,true,true}}){
  const std::string label=c.name;const auto r=SearcherTestProbe::run(owner,board,c.seed,c.pv,c.wide,c.abort);
  check(r.tt_pv==c.wide,label+" preserves caller PV flag");
  check(r.aborted==c.abort,label+" expected abort state");
  check(r.nodes>0,label+" actual core visited nodes");
  check(r.score>=-Infinite&&r.score<=Infinite,label+" bounded search result");
  check(board.fen()==fen,label+" restores FEN");check(board.key()==key,label+" restores position key");
  check(board.pawn_key()==pawn,label+" restores pawn key");check(board.history_size()==history,label+" restores history");
  check(board.in_check()==checked,label+" restores check state");
  Board replay=board;bool legal=true;
  for(Move move:r.pv){if(!replay.is_legal(move)){legal=false;break;}Undo undo;if(!replay.make_move(move,undo)){legal=false;break;}}
  check(legal,label+" every reported PV move legal");
  if(c.wide&&!c.abort)check(!r.pv.empty(),label+" completed PV contains legal move");
  if(!c.wide)check(r.nodes==1&&r.pv.empty(),label+" immediate nonPV TT cutoff control");
  // At this seeded wide-PV node, the first move is TT d1e1 and meets SingularDepth7.
  // Its same-ply excluded verification is node2; the next entry observes the limit.
  // No diagnostic hook/extern symbol is needed to retain the abort-path regression.
  if(c.abort)check(r.nodes==2,label+" limit reached inside first singular verification");
  std::cout<<"PV_METADATA_CASE "<<label<<" nodes="<<r.nodes<<" aborted="<<r.aborted<<" flag="<<r.tt_pv<<" pv_moves="<<r.pv.size()<<'\n';
 }
 std::cout<<"PV metadata: assertions "<<assertions<<" failures "<<failures<<'\n';
 return failures?1:0;
}
