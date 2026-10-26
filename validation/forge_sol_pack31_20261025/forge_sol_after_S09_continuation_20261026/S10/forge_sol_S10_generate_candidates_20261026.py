"""Generate four independent, originally implemented search experiments.

No native processes or original source writes. Reruns require fresh output paths.
"""
from pathlib import Path
import difflib
import hashlib
import json
import shutil

INPUT=Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')
L=INPUT/'01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src'
OUT=Path('/workspace/forge-pack24-20261026/S10')
VIEWS=Path('/tmp/forge_sol_S10_candidate_views_20261026')
FEATURES=[
 ('singular_siblings','SingularSiblingLmr','After a TT move proves singular, reduce its later non-checking quiet siblings by one additional ply at non-PV nodes. This does not alter the singularity test itself.'),
 ('quiet_check_survival','QuietCheckLmpSurvival','When late-quiet pruning has activated, retain legal quiet checks while dropping other quiets. The existing futility check exemption cannot recover moves already skipped by the picker.'),
 ('improving_razor','ImprovingRazorGuard','Do not razor a non-PV node whose static evaluation is improving. Preserve the existing razor margin and qsearch fallback for other nodes.'),
 ('capture_history_lmp','CaptureHistoryLmp','At shallow non-PV nodes, prune late captures only when their capture history is negative, SEE is losing, and the move neither checks nor promotes. Reuse the existing history-prune depth and LMP count thresholds.'),
]

def replace(text,old,new):
 if text.count(old)!=1:raise ValueError('unique source anchor required: '+old[:100])
 return text.replace(old,new)

def guarded(macro,text):return '#ifdef '+macro+'\n'+text+'#endif\n'

def main():
 VIEWS.mkdir(exist_ok=False)
 inventory=[]
 for key,option,hypothesis in FEATURES:
  macro='FORGE_S10_'+key.upper();field='s10_'+key
  paths=['CMakeLists.txt','include/forge/search.hpp','src/search.cpp','src/uci.cpp','IDEA_SOURCE.md','README.md']
  old={p:(L/p).read_text() for p in paths};new=dict(old)
  new['CMakeLists.txt']=replace(new['CMakeLists.txt'],
   'target_compile_features(forge_core PUBLIC cxx_std_20)\n',
   'target_compile_features(forge_core PUBLIC cxx_std_20)\n\noption('+macro+' "Build the opt-in '+option+' experiment" OFF)\nif('+macro+')\n    target_compile_definitions(forge_core PUBLIC '+macro+'=1)\nendif()\n')
  h=new['include/forge/search.hpp']
  h=replace(h,'struct SearchLimits {\n','struct SearchLimits {\n'+guarded(macro,'    bool '+field+' = false;\n'))
  h=replace(h,'    std::atomic<bool> stop{false};\n',guarded(macro,'    std::atomic<bool> '+field+'{false};\n    std::atomic<bool> '+field+'_announced{false};\n')+'    std::atomic<bool> stop{false};\n')
  h=replace(h,'    bool pondering_ = false;\n',guarded(macro,'    bool '+field+'_ = false;\n')+'    bool pondering_ = false;\n')
  h=replace(h,'    void set_threads(int threads);\n','    void set_threads(int threads);\n'+guarded(macro,'    void set_'+field+'(bool enabled) { shared_.'+field+'.store(enabled, std::memory_order_relaxed); }\n    [[nodiscard]] bool '+field+'_enabled() const { return shared_.'+field+'.load(std::memory_order_relaxed); }\n'))
  new['include/forge/search.hpp']=h
  s=new['src/search.cpp']
  s=replace(s,'SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_info, const std::vector<Worker*>& all) {\n',
   'SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_info, const std::vector<Worker*>& all) {\n'+guarded(macro,'    '+field+'_ = limits.'+field+';\n'))
  s=replace(s,'    SearchLimits worker_limits = limits;\n',
   '    SearchLimits worker_limits = limits;\n'+guarded(macro,
   '    // Snapshot once before helpers start; recursive search reads only worker-local state.\n'
   '    worker_limits.'+field+' = shared_.'+field+'.load(std::memory_order_relaxed);\n'
   '    if (worker_limits.'+field+' && !shared_.'+field+'_announced.exchange(true, std::memory_order_relaxed)) {\n'
   '        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());\n'
   '        std::cout << "info string '+option+' active" << std::endl;\n'
   '    }\n'))
  if key=='singular_siblings':
   s=replace(s,'    const bool has_material = board.has_non_pawn_material(board.side_to_move());\n',
    '    const bool has_material = board.has_non_pawn_material(board.side_to_move());\n'+guarded(macro,'    bool singular_sibling = false;\n'))
   s=replace(s,'            if (singular_score < singular_beta) {\n                extension = 1;\n',
    '            if (singular_score < singular_beta) {\n'+guarded(macro,'                if ('+field+'_) singular_sibling = true;\n')+'                extension = 1;\n')
   s=replace(s,'            int r = reduction(quiet, depth, move_count);\n',
    '            int r = reduction(quiet, depth, move_count);\n'+guarded(macro,
    '            if ('+field+'_ && singular_sibling && move != tt_move && quiet &&\n'
    '                !pv_node && !in_check && !gives_check) ++r;\n'))
  elif key=='quiet_check_survival':
   s=replace(s,'    while (!(move = picker.next(skip_quiets)).is_none()) {\n',
    '    while (!(move = picker.next(skip_quiets\n'+guarded(macro,'        && !'+field+'_\n')+'    )).is_none()) {\n')
   s=replace(s,'        if (!board.is_legal(move)) continue;\n        ++move_count;\n        ss->move_count = move_count;\n',
    '        if (!board.is_legal(move)) continue;\n'+guarded(macro,
    '        // The picker must still visit checks after ordinary quiets were pruned.\n'
    '        if ('+field+'_ && skip_quiets && !in_check && !move.is_capture() &&\n'
    '            !move.is_promotion() && !board.gives_check(move)) continue;\n')+'        ++move_count;\n        ss->move_count = move_count;\n')
  elif key=='improving_razor':
   s=replace(s,'        if (depth <= tune::RazorDepth && eval + tune::RazorBase + tune::RazorMultiplier * depth < alpha) {\n',
    '        if (depth <= tune::RazorDepth &&\n'+guarded(macro,'            (!'+field+'_ || !improving) &&\n')+'            eval + tune::RazorBase + tune::RazorMultiplier * depth < alpha) {\n')
  elif key=='capture_history_lmp':
   s=replace(s,'            const int lmr_depth = std::max(0, depth - reduction(quiet, depth, move_count));\n',
    '            const int lmr_depth = std::max(0, depth - reduction(quiet, depth, move_count));\n'+guarded(macro,
    '            if ('+field+'_ && !pv_node && !in_check && capture && !move.is_promotion() &&\n'
    '                !gives_check && depth <= tune::HistoryPruneDepth &&\n'
    '                move_count >= lmp_threshold(depth, improving) && history < 0 && !board.see_ge(move, 0)) {\n'
    '                continue;\n'
    '            }\n'))
  new['src/search.cpp']=s
  u=new['src/uci.cpp']
  u=replace(u,'            std::cout << "option name Clear Hash type button\\n"\n',
   guarded(macro,'            std::cout << "option name '+option+' type check default false\\n";\n')+'            std::cout << "option name Clear Hash type button\\n"\n')
  u=replace(u,'            } else if (name == "Clear Hash") {\n',
   guarded(macro,
   '            } else if (name == "'+option+'") {\n'
   '                if (value_text == "true" || value_text == "false") {\n'
   '                    searcher.set_'+field+'(value_text == "true");\n'
   '                } else {\n'
   '                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n'
   '                    std::cout << "info string invalid value for option '+option+'" << std::endl;\n'
   '                }\n')+'            } else if (name == "Clear Hash") {\n')
  u=replace(u,'            forge::Searcher bench_searcher(16);\n',
   '            forge::Searcher bench_searcher(16);\n'+guarded(macro,'            bench_searcher.set_'+field+'(searcher.'+field+'_enabled());\n'))
  new['src/uci.cpp']=u
  notes=(
   '\n## S10 '+option+' experiment — 2026-10-26\n\n'
   'UNPROVEN. '+hypothesis+'\n'
   'Build '+macro+'=ON, then set UCI '+option+'=true before search. Both defaults are OFF. '
   'The option is advertised only in an enabled build. One atomic request is snapshotted before worker launch; hot search reads a worker-local copy. '
   'The first active search of a searcher reports `info string '+option+' active`; the bench searcher explicitly inherits the option. '
   'No strength or speed conclusion is made. Qualification requires the full fixed OFF references, full correctness suite, all five ON depths, ON d11 differing from308972, and the specified WAC screen.\n')
  source=(
   '\n## S10 '+option+' idea source — 2026-10-26\n\n'
   'Idea sources only: the user-supplied S10 job and the supplied Forge idea-board audit. '
   'This independently implemented experiment follows a direct audit of Forge search.cpp and MovePicker. '
   +hypothesis+' No external engine code, tables or tuned values were used. Current Forge thresholds are reused where a threshold is needed. '
   'This differs from P22 singular-margin changes, P23 killer/counter LMR, P24 history-scaled futility, P27 qsearch evasions and the time-management packs.\n')
  for p,addition in [('README.md',notes),('IDEA_SOURCE.md',source)]:
   first,rest=new[p].split('\n',1);new[p]=first+'\n'+addition+'\n'+rest
  view=VIEWS/key;shutil.copytree(L,view)
  for p in paths:(view/p).write_text(new[p])
  patch=OUT/('forge_sol_S10_'+key+'_20261026.patch')
  if patch.exists():raise FileExistsError(patch)
  patch.write_text(''.join(''.join(difflib.unified_diff(old[p].splitlines(keepends=True),new[p].splitlines(keepends=True),fromfile='a/'+p,tofile='b/'+p,n=3)) for p in paths))
  inventory.append({'key':key,'option':option,'build_option':macro,'patch':str(patch),'patch_sha256':hashlib.sha256(patch.read_bytes()).hexdigest(),'bytes':patch.stat().st_size,'hypothesis':hypothesis,'view':str(view),'source_before':{p:hashlib.sha256(old[p].encode()).hexdigest() for p in paths},'source_after':{p:hashlib.sha256(new[p].encode()).hexdigest() for p in paths},'native_status':'UNVERIFIED_NOT_LAUNCHED'})
 (OUT/'forge_sol_S10_candidate_inventory_20261026.json').write_text(json.dumps(inventory,indent=2)+'\n')
 print(json.dumps(inventory,indent=2))

if __name__=='__main__':main()
