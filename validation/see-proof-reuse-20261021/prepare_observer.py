from pathlib import Path
import json,hashlib,shutil,difflib,subprocess
ROOT=Path('/workspace/dwqww'); E=ROOT/'validation/see-proof-reuse-20261021'; S=Path('/workspace/.cloud-setup/see-proof-reuse23-source'); BASE=Path('/workspace/.cloud-setup/tt-refresh-native-source'); B=Path('/workspace/.cloud-setup/tt-refresh-native-release')
assert not S.exists(); S.mkdir()
gate=json.loads((ROOT/'validation/tt-refresh-20261021/ROOT-FROZEN23-SOURCE-GATES.json').read_text())
assert gate['source_commit']=='1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for rel,sha in gate['inputs'].items():
 src=BASE/rel; assert hashfile(src)==sha,(rel,hashfile(src),sha)
 out=S/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,out)
(E/'frozen-source-map.json').write_text(json.dumps(gate['inputs'],indent=2)+'\n')
(E/'originals').mkdir(exist_ok=False)
for rel in ['forge','libforge_core.a','compile_commands.json','CMakeCache.txt','CMakeFiles/forge.dir/link.txt','CMakeFiles/forge_core.dir/flags.make']:
 src=B/rel;out=E/'originals'/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,out);assert hashfile(src)==hashfile(out)
(E/'baseline-originals.json').write_text(json.dumps({str(B/rel):hashfile(B/rel) for rel in ['forge','libforge_core.a','compile_commands.json','CMakeCache.txt','CMakeFiles/forge.dir/link.txt','CMakeFiles/forge_core.dir/flags.make']},indent=2)+'\n')
header=r'''#pragma once
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
'''
(S/'include/forge/see_observer.hpp').write_text(header)
# Instrument existing calls without changing their values or branch order.
p=S/'src/search.cpp';old=p.read_text();s=old.replace('#include "forge/search.hpp"','#include "forge/search.hpp"\n#include "forge/see_observer.hpp"',1)
a=s.index('    [[nodiscard]] Move next(bool skip_quiets) {');b=s.index('\nprivate:\n    enum Stage',a)
part=s[a:b]
part=part.replace('    [[nodiscard]] Move next(bool skip_quiets) {','    [[nodiscard]] Move next(bool skip_quiets) {\n        ++seeobs::stats.next_calls;\n        diagnostic_good_ = false;\n        diagnostic_move_ = Move::none();')
part=part.replace('board_.see_ge(move, -move_score_threshold(move))','seeobs::query(board_, move, -move_score_threshold(move), seeobs::Good)')
part=part.replace('                    return move;\n                }\n                stage_ = Killer1;','                    diagnostic_good_ = true;\n                    return move;\n                }\n                stage_ = Killer1;',1)
import re
part=re.sub(r'return (tt_move_|move|killers_\[[01]\]|counter_|bad_captures_\[bad_index_\+\+\]|Move::none\(\));',r'return diagnostic_return(\1);',part)
s=s[:a]+part+s[b:]
helper='''    [[nodiscard]] bool diagnostic_proof(Move move) const {
        const bool stage_proof = stage_ == GoodCaptures;
        if (stage_proof != diagnostic_good_) ++seeobs::stats.stage_faults;
        const bool identity = move == diagnostic_move_ && diagnostic_key_ == board_.key();
        if (stage_proof && !identity) ++seeobs::stats.scope_faults;
        return stage_proof && diagnostic_good_ && identity;
    }

'''
pos=s.index('\nprivate:\n    enum Stage',a);s=s[:pos]+'\n'+helper+s[pos:]
pos=s.index('    // Quiet/evasion generation are mutually exclusive')
s=s[:pos]+'''    bool diagnostic_good_ = false;
    Move diagnostic_move_{};
    std::uint64_t diagnostic_key_ = 0;
    Move diagnostic_return(Move move) {
        if (move.is_none()) ++seeobs::stats.none_returns;
        else ++seeobs::stats.returned[static_cast<std::size_t>(stage_)];
        const bool stage_proof = stage_ == GoodCaptures && !move.is_none();
        if (stage_proof != diagnostic_good_) ++seeobs::stats.stage_faults;
        if (stage_proof) ++seeobs::stats.good_returns;
        diagnostic_move_ = move;
        diagnostic_key_ = board_.key();
        return move;
    }

'''+s[pos:]
assert s.count('board.see_ge(move, -tune::SeeNoisyMultiplier * depth)')==1
s=s.replace('board.see_ge(move, -tune::SeeNoisyMultiplier * depth)','seeobs::query(board, move, -tune::SeeNoisyMultiplier * depth, seeobs::Noisy, picker.diagnostic_proof(move), depth)')
assert s.count('board.see_ge(move, 0)')==1
s=s.replace('board.see_ge(move, 0)','seeobs::query(board, move, 0, seeobs::Extension, picker.diagnostic_proof(move), depth)')
p.write_text(s);(E/'observer-search.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='frozen23/src/search.cpp',tofile='observer/src/search.cpp')))
p=S/'src/board.cpp';old=p.read_text();s=old.replace('#include "forge/board.hpp"','#include "forge/board.hpp"\n#include "forge/see_observer.hpp"',1)
s=s.replace('    while (depth + 1 < gain.size()) {','    while (depth + 1 < gain.size()) {\n        seeobs::promotion_iter();',1)
s=s.replace('            while (!checked && pinners != 0) {','            while (!checked && pinners != 0) {\n                seeobs::pinner();')
s=s.replace('bool Board::see_ge(const Move& move, int threshold) const {','bool Board::see_ge(const Move& move, int threshold) const {\n    seeobs::enter();')
s=s.replace('    if (move.is_castle()) return 0 >= threshold;','    if (move.is_castle()) { ++seeobs::count().castle; return 0 >= threshold; }',1)
s=s.replace('            return promotion_recapture_exchange(*this, move, captured_square) >= threshold;','            ++seeobs::count().promotion;\n            return promotion_recapture_exchange(*this, move, captured_square) >= threshold;',1)
s=s.replace('    if (swap < 0) return false;','    if (swap < 0) { ++seeobs::count().fast_false; return false; }',1)
s=s.replace('    if (swap <= 0) return true;','    if (swap <= 0) { ++seeobs::count().fast_true; return true; }',1)
a=s.index('bool Board::see_ge(');b=s.index('\nint Board::static_exchange',a);part=s[a:b];part=part.replace('    while (true) {','    seeobs::exchange();\n    while (true) {\n        seeobs::iter();',1);s=s[:a]+part+s[b:]
p.write_text(s);(E/'observer-board.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='frozen23/src/board.cpp',tofile='observer/src/board.cpp')))
(E/'see_observer.hpp').write_text(header)
# Every other exact source input is preserved; generated instrumentation is explicit.
changed=[]
for rel,sha in gate['inputs'].items():
 if hashfile(S/rel)!=sha:changed.append(rel)
assert changed==['src/board.cpp','src/search.cpp'],changed
(E/'PREPARED.json').write_text(json.dumps({'status':'SOURCE_ONLY_PREPARED','source_commit':gate['source_commit'],'source_files':len(gate['inputs']),'source_export':str(S),'changed_frozen_inputs':changed,'new_observer_header_sha256':hashfile(S/'include/forge/see_observer.hpp'),'baseline_engine_sha256':hashfile(B/'forge'),'baseline_core_sha256':hashfile(B/'libforge_core.a'),'observer_no_skipped_calls':True,'no_performance_or_elo_claim':True},indent=2)+'\n')
print('PREPARED frozen files',len(gate['inputs']),'changed',changed)
