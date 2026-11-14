// Preparation only: executable requires --run-ten. Never called by the build helper.
// The original test body, exact KRK oracle, and predicates are retained unchanged.
#define main unchanged_t12_krk_main
#include "original-krk-mate-test.cpp"
#undef main
#include <iomanip>
int main(int argc,char**argv){
 if(argc!=2||std::string(argv[1])!="--run-ten"){std::cerr<<"Usage: repeat-one --run-ten (ten actual Threads=2 depth=14 searches)\n";return 2;}
 const std::string fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1";
 const KrkTablebase tb;
 forge::Board root;if(!root.set_fen(fen))return 3;
 const int exact_dtm=tb.dtm(root.king_square(forge::White),forge::lsb(root.pieces(forge::White,forge::Rook)),root.king_square(forge::Black),0);
 if(exact_dtm!=13){std::cerr<<"Unexpected original-oracle root DTM "<<exact_dtm<<'\n';return 4;}
 forge::SearchLimits limits;limits.depth=14;
 // As in the original main loop: one reused 16-MB, two-worker Searcher.
 forge::Searcher mt_searcher(16,2);
 std::cout<<"CONFIG {\"fen\":"<<std::quoted(fen)<<",\"runs\":10,\"threads\":2,\"hash_mb\":16,\"depth\":14,\"clear_all\":true,\"fresh_state\":\"new Board and Searcher::clear before each search; reused Searcher\",\"emit_info\":false,\"tt_access\":\"Shared default\",\"use_nnue\":"<<(forge::nnue::enabled?"true":"false")<<",\"MateAlphaGuard\":"<<(forge::tune::MateAlphaGuard?"true":"false")<<",\"HindsightDepth\":"<<(forge::tune::HindsightDepth?"true":"false")<<",\"SoundMatePruning\":"<<(forge::tune::SoundMatePruning?"true":"false")<<",\"exact_dtm\":"<<exact_dtm<<",\"nodes\":"<<limits.nodes<<",\"nodes_specified\":"<<(limits.nodes_specified?"true":"false")<<",\"soft_nodes\":"<<(limits.soft_nodes?"true":"false")<<",\"movetime_ms\":"<<limits.movetime_ms<<",\"time_ms\":"<<limits.time_ms<<",\"mate_moves\":"<<limits.mate_moves<<",\"multipv\":"<<limits.multipv<<"}"<<std::endl;
 int misses=0,no_mate_score_count=0,non_mating_move_count=0;
 for(int run=0;run<10;run++){
  forge::Board board;if(!board.set_fen(fen))return 5;mt_searcher.clear();
  std::cout<<"BEGIN {\"run\":"<<run<<",\"fen\":"<<std::quoted(fen)<<"}"<<std::endl;
  const forge::SearchInfo info=mt_searcher.search(board,limits,false);
  const bool has_mate_score=info.score>=forge::MateInMaxPly;
  const int move_plies=tb.move_mate_plies(board,info.best_move);
  const int claimed_plies=has_mate_score?(forge::MateValue-info.score):-1;
  const bool is_mating_move=move_plies>0&&(has_mate_score?(move_plies<=claimed_plies):(move_plies<=limits.depth));
  const bool miss=!has_mate_score||!is_mating_move;misses+=miss;no_mate_score_count+=!has_mate_score;non_mating_move_count+=!is_mating_move;
  std::cout<<"ROW {\"run\":"<<run<<",\"fen\":"<<std::quoted(fen)<<",\"score\":"<<info.score<<",\"score_text\":"<<std::quoted(format_score(info.score))<<",\"bestmove\":"<<std::quoted(forge::Board::move_to_uci(info.best_move))<<",\"depth\":"<<info.depth<<",\"seldepth\":"<<info.seldepth<<",\"nodes\":"<<info.nodes<<",\"elapsed_ms\":"<<info.elapsed_ms<<",\"exact_dtm\":"<<exact_dtm<<",\"move_dtm\":"<<move_plies<<",\"claimed_plies\":"<<claimed_plies<<",\"has_mate_score\":"<<(has_mate_score?"true":"false")<<",\"is_mating_move\":"<<(is_mating_move?"true":"false")<<",\"miss\":"<<(miss?"true":"false")<<",\"pv\":[";
  for(std::size_t i=0;i<info.pv.size();i++){if(i)std::cout<<',';std::cout<<std::quoted(forge::Board::move_to_uci(info.pv[i]));}std::cout<<"]}"<<std::endl;
 }
 std::cout<<"SUMMARY {\"runs\":10,\"misses\":"<<misses<<",\"no_mate_score\":"<<no_mate_score_count<<",\"non_mating_move\":"<<non_mating_move_count<<"}"<<std::endl;return misses?1:0;
}
