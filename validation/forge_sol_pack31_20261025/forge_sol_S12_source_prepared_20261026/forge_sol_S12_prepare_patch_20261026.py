#!/usr/bin/env python3
"""Create a source-only, exact-input-bound S12 patch; never edit supplied trees."""
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACK = Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')
BASES = {
    'L': PACK / '01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src',
    'LP': PACK / '01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src',
    'B': PACK / '01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src',
}
FILES = ['CMakeLists.txt', 'include/forge/search.hpp', 'src/search.cpp', 'src/uci.cpp', 'README.md', 'IDEA_SOURCE.md']


def replace(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f'exact unique anchor expected, found {text.count(old)}: {old[:100]!r}')
    return text.replace(old, new)


def changed(name, text):
    if name == 'CMakeLists.txt':
        text = replace(text, 'option(FORGE_NATIVE ', 'option(FORGE_NNUE_LAZY_ACC "Enable experimental NnueLazyAcc UCI option (default OFF)" OFF)\noption(FORGE_NATIVE ')
        return replace(text, 'target_compile_features(forge_core PUBLIC cxx_std_20)\n', '''target_compile_features(forge_core PUBLIC cxx_std_20)
if(FORGE_NNUE_LAZY_ACC)
    target_compile_definitions(forge_core PUBLIC FORGE_NNUE_LAZY_ACC=1)
endif()
''')
    if name == 'include/forge/search.hpp':
        text = replace(text, 'namespace forge {\n', '''#ifndef FORGE_NNUE_LAZY_ACC
#define FORGE_NNUE_LAZY_ACC 0
#endif

namespace forge {

#if FORGE_NNUE_LAZY_ACC
namespace lazy_acc {
// UCI joins all search workers before changing this pending configuration.
extern std::atomic<bool> requested;
}
struct LazyAccStats {
    std::uint64_t refreshes = 0;
    std::uint64_t updates = 0;
    std::uint64_t zero_dirty_edges = 0;
    std::uint64_t copies_avoided = 0;
    std::uint64_t alias_hits = 0;
    std::uint64_t evaluations = 0;
};
#endif
''')
        text = replace(text, '    bool restricted_root_empty = false;\n', '''    bool restricted_root_empty = false;
#if FORGE_NNUE_LAZY_ACC
    LazyAccStats lazy_acc_stats{};
#endif
''')
        text = replace(text, '    nnue::DirtyPieces dirty{};\n', '''    nnue::DirtyPieces dirty{};
#if FORGE_NNUE_LAZY_ACC
    // Null edges may borrow a physical valid ancestor. Never a descendant or
    // another alias: valid remains false here until a real update materializes.
    SearchStack* accumulator_owner = nullptr;
#endif
''')
        text = replace(text, '    std::atomic<bool> stop{false};\n', '''    std::atomic<bool> stop{false};
#if FORGE_NNUE_LAZY_ACC
    // Immutable from before worker creation until every helper has joined.
    bool lazy_acc_enabled = false;
#endif
''')
        text = replace(text, '    [[nodiscard]] bool is_main() const { return id_ == 0; }\n', '''    [[nodiscard]] bool is_main() const { return id_ == 0; }
#if FORGE_NNUE_LAZY_ACC
    [[nodiscard]] LazyAccStats lazy_acc_stats() const { return lazy_acc_stats_; }
#endif
''')
        text = replace(text, '    SharedSearchState& shared_;\n', '''#if FORGE_NNUE_LAZY_ACC
    LazyAccStats lazy_acc_stats_{};
    [[nodiscard]] int static_evaluate_lazy(const Board& board, SearchStack* ss);
#endif
    SharedSearchState& shared_;
''')
        return text
    if name == 'src/search.cpp':
        text = replace(text, 'namespace forge {\n', '''namespace forge {

#if FORGE_NNUE_LAZY_ACC
namespace lazy_acc {
std::atomic<bool> requested{false};
}
namespace {
std::atomic<bool> lazy_acc_active_announced{false};
// Only static_evaluate_lazy creates aliases; every target is physical and valid.
SearchStack* computed_owner(SearchStack* frame) {
    if (frame->accumulator.valid) return frame;
    SearchStack* owner = frame->accumulator_owner;
    return owner != nullptr && owner < frame && owner->accumulator.valid
        && owner->accumulator_owner == nullptr ? owner : nullptr;
}
}
#endif
''')
        text = replace(text, 'int Worker::static_evaluate(const Board& board, SearchStack* ss) {\n', '''#if FORGE_NNUE_LAZY_ACC
int Worker::static_evaluate_lazy(const Board& board, SearchStack* ss) {
    const bool residual = nnue::residual();
    SearchStack* owner = computed_owner(ss);
    if (owner != nullptr) {
        if (owner != ss) ++lazy_acc_stats_.alias_hits;
    } else {
        int back = 0;
        while (back < ss->ply && computed_owner(ss - back - 1) == nullptr) ++back;
        if (back >= ss->ply && computed_owner(ss - back - 1) == nullptr) {
            nnue::refresh(board, ss->accumulator);
            ss->accumulator_owner = nullptr;
            ++lazy_acc_stats_.refreshes;
            if (residual) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
            owner = ss;
        } else {
            owner = computed_owner(ss - back - 1);
            for (int i = back; i >= 0; --i) {
                SearchStack* child = ss - i;
                assert(owner != nullptr && owner < child && owner->accumulator.valid);
                if (child->dirty.count == 0) {
                    // A null move changes only the output perspective, not the
                    // piece features or white-oriented PSQT/phase. Borrow both.
                    child->accumulator_owner = owner;
                    ++lazy_acc_stats_.zero_dirty_edges;
                    ++lazy_acc_stats_.copies_avoided;
                } else {
                    nnue::update(owner->accumulator, child->accumulator, child->dirty);
                    ++lazy_acc_stats_.updates;
                    if (residual) Evaluator::update_runtime_psqt(owner->runtime_psqt, child->runtime_psqt, child->dirty);
                    child->accumulator_owner = nullptr;
                    owner = child;
                }
            }
        }
    }
    assert(owner != nullptr && owner->accumulator.valid);
    const int network = nnue::evaluate(board, owner->accumulator);
    if (!residual) return network;
    if (!owner->runtime_psqt.valid) owner->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
    return std::clamp(evaluator_.evaluate_runtime(board, owner->runtime_psqt) + network, -MateInMaxPly + 1, MateInMaxPly - 1);
}
#endif

int Worker::static_evaluate(const Board& board, SearchStack* ss) {
''')
        text = replace(text, '    if (!nnue::enabled || !nnue::available()) return evaluator_.evaluate(board);\n', '''    if (!nnue::enabled || !nnue::available()) return evaluator_.evaluate(board);
#if FORGE_NNUE_LAZY_ACC
    ++lazy_acc_stats_.evaluations;
    if (shared_.lazy_acc_enabled) return static_evaluate_lazy(board, ss);
#endif
''')
        text = replace(text, '            nnue::refresh(board, ss->accumulator);\n            if (residual)', '''            nnue::refresh(board, ss->accumulator);
#if FORGE_NNUE_LAZY_ACC
            ++lazy_acc_stats_.refreshes;
#endif
            if (residual)''')
        text = replace(text, '                nnue::update((ss - i - 1)->accumulator, (ss - i)->accumulator, (ss - i)->dirty);\n', '''                nnue::update((ss - i - 1)->accumulator, (ss - i)->accumulator, (ss - i)->dirty);
#if FORGE_NNUE_LAZY_ACC
                ++lazy_acc_stats_.updates;
                if ((ss - i)->dirty.count == 0) ++lazy_acc_stats_.zero_dirty_edges;
#endif
''')
        # Both invalidation sites must clear aliases, including when the child
        # frame is reused for a different sibling after it borrowed an ancestor.
        anchor = '    (ss + 1)->runtime_psqt.valid = false;\n'
        if text.count(anchor) != 2:
            raise ValueError('exactly two child invalidation sites expected')
        text = text.replace(anchor, anchor + '''#if FORGE_NNUE_LAZY_ACC
    (ss + 1)->accumulator_owner = nullptr;
#endif
''')
        text = replace(text, '    local_nodes_ = 0;\n', '''#if FORGE_NNUE_LAZY_ACC
    lazy_acc_stats_ = {};
#endif
    local_nodes_ = 0;
''')
        text = replace(text, '        entry.runtime_psqt.valid = false;\n', '''        entry.runtime_psqt.valid = false;
#if FORGE_NNUE_LAZY_ACC
        entry.accumulator_owner = nullptr;
#endif
''')
        text = replace(text, '        nnue::refresh(board, ss->accumulator);\n        if (nnue::residual())', '''        nnue::refresh(board, ss->accumulator);
#if FORGE_NNUE_LAZY_ACC
        ++lazy_acc_stats_.refreshes;
#endif
        if (nnue::residual())''')
        text = replace(text, '    // Age the table once per search, before any worker can probe it.\n', '''#if FORGE_NNUE_LAZY_ACC
    shared_.lazy_acc_enabled = lazy_acc::requested.load(std::memory_order_relaxed)
        && nnue::enabled && nnue::available();
#endif
    // Age the table once per search, before any worker can probe it.
''')
        text = replace(text, '    shared_.stop.store(external_stop, std::memory_order_relaxed);\n    return result;\n', '''    shared_.stop.store(external_stop, std::memory_order_relaxed);
#if FORGE_NNUE_LAZY_ACC
    for (const auto& worker : workers_) {
        const auto stats = worker->lazy_acc_stats();
        result.lazy_acc_stats.refreshes += stats.refreshes;
        result.lazy_acc_stats.updates += stats.updates;
        result.lazy_acc_stats.zero_dirty_edges += stats.zero_dirty_edges;
        result.lazy_acc_stats.copies_avoided += stats.copies_avoided;
        result.lazy_acc_stats.alias_hits += stats.alias_hits;
        result.lazy_acc_stats.evaluations += stats.evaluations;
    }
    if (shared_.lazy_acc_enabled && result.lazy_acc_stats.evaluations != 0) {
        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
        if (!lazy_acc_active_announced.exchange(true, std::memory_order_relaxed))
            std::cout << "info string NnueLazyAcc active\\n";
        const auto& stats = result.lazy_acc_stats;
        std::cout << "info string NnueLazyAcc stats refreshes " << stats.refreshes
                  << " updates " << stats.updates << " zero_dirty_edges " << stats.zero_dirty_edges
                  << " copies_avoided " << stats.copies_avoided << " alias_hits " << stats.alias_hits
                  << " evaluations " << stats.evaluations << std::endl;
    }
#endif
    return result;
''')
        return text
    if name == 'src/uci.cpp':
        text = replace(text, '            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\\n";\n', '''            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\\n";
#if FORGE_NNUE_LAZY_ACC
            if (forge::nnue::available()) std::cout << "option name NnueLazyAcc type check default false\\n";
#endif
''')
        return replace(text, '            } else if (name == "UseNNUE") {\n', '''#if FORGE_NNUE_LAZY_ACC
            } else if (name == "NnueLazyAcc") {
                if (value_text == "true") forge::lazy_acc::requested.store(true, std::memory_order_relaxed);
                else if (value_text == "false") forge::lazy_acc::requested.store(false, std::memory_order_relaxed);
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option NnueLazyAcc" << std::endl;
                }
                searcher.clear_hash();
#endif
            } else if (name == "UseNNUE") {
''')
    if name in ['README.md', 'IDEA_SOURCE.md']:
        title, rest = text.split('\n', 1)
        note = '''
## S12 source-only candidate, 2026-10-26

Idea source: Forge's own nearest-ancestor lazy accumulator implementation and
the task's zero-dirty/null-edge copy-elision hypothesis. Original implementation;
no code or tuned values from another engine. FORGE_NNUE_LAZY_ACC defaults OFF;
an enabled build exposes NnueLazyAcc, also OFF. It aliases only physical valid
ancestors across zero-dirty edges and preserves nonempty update arithmetic.
Native correctness, speed, Windows, and strength are UNVERIFIED at preparation.
This addendum does not supersede the historical lock/provenance notes below.

'''
        return title + '\n' + note + rest
    raise ValueError(name)


def inventory(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob('*')) if p.is_file()}


def main():
    patchpath = HERE / 'forge_sol_S12_lazyacc_h256e12_20261026.patch'
    if patchpath.exists():
        raise FileExistsError('sealed output already exists; use a new named revision')
    originals = {key: inventory(path) for key, path in BASES.items()}
    views = {}
    patch = []
    for name in FILES:
        before = (BASES['L'] / name).read_text()
        after = changed(name, before)
        destination = HERE / 'sourceview_L' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(after)
        views[name] = hashlib.sha256(after.encode()).hexdigest()
        patch.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                     fromfile='a/' + name, tofile='b/' + name, n=3))
    patchpath.write_text(''.join(patch))
    after_originals = {key: inventory(path) for key, path in BASES.items()}
    if after_originals != originals:
        raise RuntimeError('an original source tree changed during source-only preparation')
    (HERE / 'forge_sol_S12_source_binding_20261026.json').write_text(json.dumps({
        'scope': 'source-only; no compiler or native engine executed',
        'bases': {key: str(path) for key, path in BASES.items()},
        'original_full_inventories': originals, 'originals_unchanged': True,
        'candidate_view_files_sha256': views,
        'patch_sha256': hashlib.sha256(patchpath.read_bytes()).hexdigest(),
        'native_status': 'UNVERIFIED',
    }, indent=2, sort_keys=True) + '\n')
    print(patchpath)
    print(hashlib.sha256(patchpath.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
