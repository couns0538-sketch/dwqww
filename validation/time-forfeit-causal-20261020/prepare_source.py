#!/usr/bin/env python3
"""Create a diagnostic-only source export from trusted frozen Git, no engine run."""
from pathlib import Path
import difflib, hashlib, io, json, subprocess, tarfile
REPO=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
REV='c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e'
DEST=Path('/workspace/.cloud-setup/forge-forfeit-causal-source-v2')
assert not DEST.exists(), 'Refuse to overwrite existing diagnostic export'
archive=subprocess.check_output(['git','archive',REV,'CMakeLists.txt','LICENSE','src','include','tests','bench','tools'],cwd=REPO)
(HERE/'baseline-source.tar').write_bytes(archive)
DEST.mkdir()
with tarfile.open(fileobj=io.BytesIO(archive)) as tar: tar.extractall(DEST,filter='data')
def sha(b): return hashlib.sha256(b).hexdigest()
before={str(p.relative_to(DEST)):sha(p.read_bytes()) for p in sorted(DEST.rglob('*')) if p.is_file()}
(DEST/'include/forge/time_diagnostic.hpp').write_bytes((HERE/'time_diagnostic.hpp').read_bytes())
changes=[]
def edit(rel, operations):
    p=DEST/rel;original=p.read_text();text=original
    for old,new,count in operations:
        assert text.count(old)==count,(rel,old[:70],text.count(old),count)
        text=text.replace(old,new)
    p.write_text(text)
    changes.extend(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
ns='forge::time_diagnostic::'
edit('src/uci.cpp',[
    ('#include "forge/search.hpp"','#include "forge/search.hpp"\n#include "forge/time_diagnostic.hpp"',1),
    ('        } else if (command == "go") {','        } else if (command == "go") {\n            const auto diagnostic_sequence = '+ns+'begin_go(\n                std::chrono::duration_cast<std::chrono::nanoseconds>(command_start.time_since_epoch()).count());',1),
    ('&ponder_hit_received, search_board, limits, ponder_enabled]() mutable {','&ponder_hit_received, search_board, limits, ponder_enabled, diagnostic_sequence]() mutable {\n                    '+ns+'enter_search(diagnostic_sequence);\n                    '+ns+'event("worker_dispatch_begin");',1),
    ('                    const forge::SearchInfo result = searcher.search(search_board, limits, true);','                    const forge::SearchInfo result = searcher.search(search_board, limits, true);\n                    '+ns+'event("uci_search_return", result.nodes, 0, 0, static_cast<long long>(result.elapsed_ms));',1),
    ('                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n                    std::cout << "bestmove " << best << prediction << std::endl;',
     '                    '+ns+'event("bestmove_pre_lock", result.nodes);\n                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n                    '+ns+'event("bestmove_pre_output", result.nodes);\n                    std::cout << "bestmove " << best << prediction << std::endl;\n                    '+ns+'event("bestmove_post_flush", result.nodes);',1)
])
p=DEST/'src/search.cpp';original=p.read_text();text=original.replace('#include "forge/search.hpp"','#include "forge/search.hpp"\n#include "forge/time_diagnostic.hpp"',1)
begin=text.index('bool Worker::should_stop() {');end=text.index('bool Worker::is_draw(',begin)
old=text[begin:end];new=old.replace('bool Worker::should_stop() {','''bool Worker::should_stop() {
    const bool diagnostic_poll = time_diagnostic::poll_enabled();
    const auto diagnostic_origin = std::chrono::duration_cast<std::chrono::nanoseconds>(start_.time_since_epoch()).count();
    if (diagnostic_poll) time_diagnostic::event("timer_poll_begin", local_nodes_, diagnostic_origin, hard_limit_ms_);
    const auto diagnostic_return = [&](bool decision, int reason) {
        if (diagnostic_poll) time_diagnostic::event("timer_poll_end", local_nodes_, diagnostic_origin, hard_limit_ms_, reason);
        return decision;
    };''',1)
for a,b in [
 ('if (shared_.stop.load(std::memory_order_relaxed)) return true;','if (shared_.stop.load(std::memory_order_relaxed)) return diagnostic_return(true, 1);'),
 ('if (!is_main()) return false;','if (!is_main()) return diagnostic_return(false, 2);'),
 ('if (node_limit_specified_ && total_nodes() >= node_limit_) return true;','if (node_limit_specified_ && total_nodes() >= node_limit_) return diagnostic_return(true, 3);'),
 ('if (pondering_ && shared_.ponder_hit_ns.load(std::memory_order_relaxed) == 0) return false;','if (pondering_ && shared_.ponder_hit_ns.load(std::memory_order_relaxed) == 0) return diagnostic_return(false, 4);'),
 ('if (elapsed_ms() >= hard_limit_ms_) return true;','if (elapsed_ms() >= hard_limit_ms_) return diagnostic_return(true, 5);'),
 ('    return false;','    return diagnostic_return(false, 0);')]:
 assert new.count(a)==1,a;new=new.replace(a,b,1)
text=text[:begin]+new+text[end:]
begin=text.index('SearchInfo Worker::search(');end=text.index('// Searcher facade',begin)
part=text[begin:end]
part=part.replace('    start_ = limits.request_start', '    time_diagnostic::event("worker_search_begin");\n    start_ = limits.request_start',1)
part=part.replace('    local_nodes_ = 0;', '    time_diagnostic::event("worker_origin", 0,\n        std::chrono::duration_cast<std::chrono::nanoseconds>(start_.time_since_epoch()).count());\n    local_nodes_ = 0;',1)
part=part.replace('    SearchInfo result;', '    time_diagnostic::event("budget_ready", 0,\n        std::chrono::duration_cast<std::chrono::nanoseconds>(start_.time_since_epoch()).count(),\n        hard_limit_ms_, soft_limit_ms_);\n    SearchInfo result;',1)
nps_line='        const std::uint64_t nps = elapsed > 0 ? nodes * 1000U / static_cast<std::uint64_t>(elapsed) : 0;\n'
info_lock='        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());'
assert part.count(nps_line+info_lock)==1, 'Locate the actual completed-iteration emit block'
part=part.replace(nps_line+info_lock,nps_line+'''        time_diagnostic::event("info_pre_lock", nodes,
            std::chrono::duration_cast<std::chrono::nanoseconds>(start_.time_since_epoch()).count(), depth, elapsed);
        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
        time_diagnostic::event("info_pre_output", nodes, 0, depth, elapsed);''',1)
part=part.replace('        std::cout << std::endl;', '''        time_diagnostic::event("info_pre_flush", nodes, 0, depth, elapsed);
        std::cout << std::endl;
        time_diagnostic::event("info_post_flush", nodes, 0, depth, elapsed);''',1)
part=part.replace('            iteration_score = search(board, ss, depth, alpha, beta, false);', '\n'.join([
    '            time_diagnostic::event("iteration_search_enter", local_nodes_,',
    '                std::chrono::duration_cast<std::chrono::nanoseconds>(start_.time_since_epoch()).count(), depth);',
    '            iteration_score = search(board, ss, depth, alpha, beta, false);',
    '            time_diagnostic::event("iteration_search_return", local_nodes_,',
    '                std::chrono::duration_cast<std::chrono::nanoseconds>(start_.time_since_epoch()).count(), depth, aborted_ ? 1 : 0);']),1)
part=part.replace('            if (elapsed_ms() >= static_cast<std::int64_t>(static_cast<double>(soft_limit_ms_) * factor)) break;', '\n'.join([
    '            if (elapsed_ms() >= static_cast<std::int64_t>(static_cast<double>(soft_limit_ms_) * factor)) {',
    '                time_diagnostic::event("soft_budget_stop", local_nodes_,',
    '                    std::chrono::duration_cast<std::chrono::nanoseconds>(start_.time_since_epoch()).count(),',
    '                    soft_limit_ms_, static_cast<std::int64_t>(static_cast<double>(soft_limit_ms_) * factor));',
    '                break;',
    '            }']),1)
part=part.replace('return result;', '''time_diagnostic::event("worker_result", result.nodes,
            std::chrono::duration_cast<std::chrono::nanoseconds>(start_.time_since_epoch()).count(),
            hard_limit_ms_, static_cast<long long>(result.elapsed_ms));
        return result;''')
text=text[:begin]+part+text[end:]
text=text.replace('SearchInfo Searcher::search(Board board, const SearchLimits& limits, bool emit_info) {','SearchInfo Searcher::search(Board board, const SearchLimits& limits, bool emit_info) {\n    time_diagnostic::event("facade_enter");',1)
text=text.replace('    shared_.stop.store(external_stop, std::memory_order_relaxed);\n    return result;', '    shared_.stop.store(external_stop, std::memory_order_relaxed);\n    time_diagnostic::event("facade_result", result.nodes, 0, 0, static_cast<long long>(result.elapsed_ms));\n    return result;',1)
p.write_text(text)
changes.extend(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='a/src/search.cpp',tofile='b/src/search.cpp'))
(HERE/'instrumentation.patch').write_text(''.join(changes))
after={str(p.relative_to(DEST)):sha(p.read_bytes()) for p in sorted(DEST.rglob('*')) if p.is_file()}
changed=[name for name in sorted(after) if before.get(name)!=after[name]]
assert changed==['include/forge/time_diagnostic.hpp','src/search.cpp','src/uci.cpp'],changed
(HERE/'SOURCE.json').write_text(json.dumps({'baseline_sha':REV,'source_export':str(DEST),'baseline_archive_sha256':sha(archive),'changed_files':changed,'baseline_sha256':before,'instrumented_sha256':after,'timing_execution':False},indent=2)+'\n')
print('Prepared diagnostic source only:',', '.join(changed))
