"""Create the bounded S13 source patch; never alters the reference tree."""
from pathlib import Path
import difflib
import json

ROOT = Path(__file__).resolve().parent
SOURCE = Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files/01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src')
VIEW = Path('/tmp/forge_sol_S13_private_views_20261026/L_skeleton')
FLAG = 'FORGE_S13_TT_CHILD_PREFETCH'
OPTION = 'TtChildPrefetch'
NAMES = ['CMakeLists.txt', 'include/forge/search.hpp', 'src/search.cpp', 'src/uci.cpp', 'README.md', 'IDEA_SOURCE.md']


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('anchor not unique: ' + old[:90])
    return text.replace(old, new, 1)


def guard(text):
    return '#ifdef ' + FLAG + '\n' + text + '#endif\n'


def transform(name, text):
    if name == 'CMakeLists.txt':
        anchor = 'target_compile_features(forge_core PUBLIC cxx_std_20)\n'
        return replace_once(text, anchor, anchor + f'\noption({FLAG} "Build the opt-in {OPTION} experiment" OFF)\nif({FLAG})\n    target_compile_definitions(forge_core PUBLIC {FLAG}=1)\nendif()\n')
    if name == 'include/forge/search.hpp':
        text = replace_once(text, 'struct SearchLimits {\n', 'struct SearchLimits {\n' + guard('    bool s13_tt_child_prefetch = false;\n'))
        text = replace_once(text, '    TranspositionTable tt;\n', '    TranspositionTable tt;\n' + guard('    std::atomic<bool> s13_tt_child_prefetch{false};\n    std::atomic<bool> s13_tt_child_prefetch_announced{false};\n'))
        text = replace_once(text, '    bool pondering_ = false;\n', guard('    bool s13_tt_child_prefetch_ = false;\n') + '    bool pondering_ = false;\n')
        text = replace_once(text, '    void set_threads(int threads);\n', '    void set_threads(int threads);\n' + guard('    void set_s13_tt_child_prefetch(bool enabled) { shared_.s13_tt_child_prefetch.store(enabled, std::memory_order_relaxed); }\n    [[nodiscard]] bool s13_tt_child_prefetch_enabled() const { return shared_.s13_tt_child_prefetch.load(std::memory_order_relaxed); }\n'))
        return text
    if name == 'src/search.cpp':
        text = replace_once(text, '            board.make_null_move(undo);\n', '            board.make_null_move(undo);\n' + guard('            if (s13_tt_child_prefetch_) shared_.tt.prefetch(board.key());\n'))
        text = replace_once(text, '                (void)board.make_move(move, undo);\n', '                (void)board.make_move(move, undo);\n' + guard('                if (s13_tt_child_prefetch_) shared_.tt.prefetch(board.key());\n'))
        anchor = 'SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_info, const std::vector<Worker*>& all) {\n'
        text = replace_once(text, anchor, anchor + guard('    s13_tt_child_prefetch_ = limits.s13_tt_child_prefetch;\n'))
        anchor = '    SearchLimits worker_limits = limits;\n'
        text = replace_once(text, anchor, anchor + guard('    // Snapshot once before helper launch; recursive workers use their own copy.\n    worker_limits.s13_tt_child_prefetch = shared_.s13_tt_child_prefetch.load(std::memory_order_relaxed);\n    if (worker_limits.s13_tt_child_prefetch && !shared_.s13_tt_child_prefetch_announced.exchange(true, std::memory_order_relaxed)) {\n        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());\n        std::cout << "info string TtChildPrefetch active" << std::endl;\n    }\n'))
        return text
    if name == 'src/uci.cpp':
        anchor = '            std::cout << "option name Clear Hash type button\\n"\n'
        text = replace_once(text, anchor, guard('            std::cout << "option name TtChildPrefetch type check default false\\n";\n') + anchor)
        anchor = '            } else if (name == "Clear Hash") {\n'
        text = replace_once(text, anchor, guard('            } else if (name == "TtChildPrefetch") {\n                if (value_text == "true" || value_text == "false") {\n                    searcher.set_s13_tt_child_prefetch(value_text == "true");\n                } else {\n                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n                    std::cout << "info string invalid value for option TtChildPrefetch" << std::endl;\n                }\n') + anchor)
        anchor = '            forge::Searcher bench_searcher(16);\n'
        return replace_once(text, anchor, anchor + guard('            bench_searcher.set_s13_tt_child_prefetch(searcher.s13_tt_child_prefetch_enabled());\n'))
    heading, remainder = text.split('\n\n', 1)
    if name == 'README.md':
        addition = '## S13 opt-in child TT prefetch — 2026-10-26\n\nThe isolated `FORGE_S13_TT_CHILD_PREFETCH` build switch and `TtChildPrefetch` UCI option both default OFF. ON adds prefetch after null-move and ProbCut make, while retaining the original qsearch/main prefetches and existing 64-byte TT-cluster assertion. It snapshots the requested atomic option before helper launch and announces `info string TtChildPrefetch active` once. Set the option before searching. No TT layout, move order, evaluation value or network changes. Native node parity, sanitizer checks and speed remain UNVERIFIED until the separate qualification completes; no strength claim.\n\n'
    else:
        addition = '## S13 child TT prefetch idea sources — 2026-10-26\n\n- The crew S13 handoff asks to cover child-key changes with TT prefetch and verify a 64-byte bucket.\n- Forge itself already prefetches after qsearch/main make and already asserts `sizeof(TTCluster) == 64`; inspecting its null-move and ProbCut recursion identified the two remaining child entry paths.\n- Own C++ implementation; the atomic requested-option/worker-snapshot pattern follows our own earlier Forge experiment plumbing. No code, tuned constants or parameter values from another engine.\n\n'
    return heading + '\n\n' + addition + remainder


def main():
    if VIEW.exists():
        raise FileExistsError('source view already exists; preserve previous attempt')
    patch = []
    for name in NAMES:
        old = (SOURCE / name).read_bytes().decode('utf-8')
        new = transform(name, old)
        target = VIEW / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('x', encoding='utf-8', newline='') as f:
            f.write(new)
        patch.extend(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True), 'a/' + name, 'b/' + name, n=3))
    out = ROOT / 'forge_sol_S13_ttprefetch_20261026.patch'
    with out.open('x', encoding='utf-8', newline='') as f:
        f.writelines(patch)
    print(json.dumps({'status': 'SOURCE_CREATED_NATIVE_UNVERIFIED', 'patch': str(out), 'private_skeleton': str(VIEW), 'files': NAMES}))


if __name__ == '__main__':
    main()
