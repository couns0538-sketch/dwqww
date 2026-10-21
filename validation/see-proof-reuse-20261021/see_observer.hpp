#pragma once
#include "forge/board.hpp"
#include <array>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>
namespace forge::seeobs {
enum Site { Other, Good, Noisy, Extension, SiteCount };
struct Count { std::uint64_t calls=0, proof_calls=0, false_results=0, proof_false=0, castle=0, promotion=0, fast_false=0, fast_true=0, exchange_calls=0, exchange_iters=0, pinner_iters=0, promotion_iters=0, proof_exchange_calls=0, proof_exchange_iters=0, proof_pinner_iters=0, proof_promotion_iters=0; };
struct Context { Site site=Other; bool proof=false; };
inline thread_local Context context;
struct Stats { std::array<Count,SiteCount> site{}; std::array<std::uint64_t,15> returned{}; std::uint64_t next_calls=0,none_returns=0,good_returns=0,stage_faults=0,scope_faults=0,proof_positive_threshold=0; std::vector<std::string> witnesses; };
inline Stats stats;
inline Count& count(){return stats.site[context.site];}
inline void enter(){++count().calls;if(context.proof)++count().proof_calls;}
inline void exchange(){++count().exchange_calls;if(context.proof)++count().proof_exchange_calls;}
inline void iter(){++count().exchange_iters;if(context.proof)++count().proof_exchange_iters;}
inline void pinner(){++count().pinner_iters;if(context.proof)++count().proof_pinner_iters;}
inline void promotion_iter(){++count().promotion_iters;if(context.proof)++count().proof_promotion_iters;}
inline bool query(const Board& board,Move move,int threshold,Site site,bool proof=false,int depth=0){
 const Context old=context;context={site,proof};
 const bool result=board.see_ge(move,threshold);
 Count& c=count();if(!result)++c.false_results;if(proof&&!result)++c.proof_false;if(proof&&threshold>0)++stats.proof_positive_threshold;
 if(proof&&stats.witnesses.size()<32){stats.witnesses.push_back(std::to_string(static_cast<int>(site))+"\t"+Board::move_to_uci(move)+"\t"+std::to_string(move.flags)+"\t"+std::to_string(move.promotion)+"\t"+std::to_string(depth)+"\t"+std::to_string(threshold)+"\t"+std::to_string(result)+"\t"+std::to_string(board.key())+"\t"+board.fen());}
 context=old;return result;
}
struct Dump { ~Dump(){const char* p=std::getenv("FORGE_SEE_OBSERVER");if(!p)return;std::ofstream f(p);f<<"{\n\"next_calls\":"<<stats.next_calls<<",\"none_returns\":"<<stats.none_returns<<",\"good_returns\":"<<stats.good_returns<<",\"stage_faults\":"<<stats.stage_faults<<",\"scope_faults\":"<<stats.scope_faults<<",\"proof_positive_threshold\":"<<stats.proof_positive_threshold<<",\n\"returned_stages\":[";for(std::size_t i=0;i<stats.returned.size();++i){if(i)f<<',';f<<stats.returned[i];}f<<"],\n\"sites\":[\n";for(int i=0;i<SiteCount;++i){const Count& c=stats.site[static_cast<std::size_t>(i)];if(i)f<<",\n";f<<"{\"site\":"<<i;
#define FIELD(x) f<<",\"" #x "\":"<<c.x
FIELD(calls);FIELD(proof_calls);FIELD(false_results);FIELD(proof_false);FIELD(castle);FIELD(promotion);FIELD(fast_false);FIELD(fast_true);FIELD(exchange_calls);FIELD(exchange_iters);FIELD(pinner_iters);FIELD(promotion_iters);FIELD(proof_exchange_calls);FIELD(proof_exchange_iters);FIELD(proof_pinner_iters);FIELD(proof_promotion_iters);
#undef FIELD
f<<'}';}f<<"\n]}\n";std::ofstream w(std::string(p)+".witnesses.tsv");w<<"site\tmove\tflags\tpromotion\tdepth\tthreshold\tresult\tkey\tfen\n";for(const auto& x:stats.witnesses)w<<x<<'\n';} };
inline Dump dump;
}
