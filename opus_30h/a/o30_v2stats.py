#!/usr/bin/env python3
"""o30_v2stats.py <v2port scratch repo> - Opus 30-h job, TEST BUILDS ONLY: counters for the speed hunt (own code).
With -DFORGE_NNUE_V2_STATS=1 the exe counts, per path (v1 = the compiled-in net, v2 = EvalFileV2): evaluations, lazy
walk-backs and the plies they replay, incremental updates (and the columns they apply), full refreshes, cached
refreshes (and their columns), and prints them to stderr at exit. Without the define every counter compiles away.
Anchored edits; refused if an anchor is missing / not unique or the tree already has the counters."""
import sys
from pathlib import Path

STATS_DECL = '''namespace forge::nnue::v2 {
#if defined(FORGE_NNUE_V2_STATS) && FORGE_NNUE_V2_STATS
struct Stats {
    unsigned long long v1_evals = 0, v1_walks = 0, v1_walk_plies = 0, v1_updates = 0, v1_refreshes = 0;
    unsigned long long v2_evals = 0, v2_walks = 0, v2_walk_plies = 0, v2_updates = 0, v2_update_cols = 0;
    unsigned long long v2_cached = 0, v2_cached_cols = 0, v2_full = 0, v2_noancestor = 0;
};
inline Stats stats;
#define FORGE_V2_STAT(field, n) (::forge::nnue::v2::stats.field += static_cast<unsigned long long>(n))
#else
#define FORGE_V2_STAT(field, n) ((void)0)
#endif
'''
EDITS_HPP = [
    ('namespace forge::nnue::v2 {\n', STATS_DECL),
    ('inline void refresh(const Net& net, const Board& board, Color perspective, float* values) {\n',
     'inline void refresh(const Net& net, const Board& board, Color perspective, float* values) {\n    FORGE_V2_STAT(v2_full, 1);\n'),
    ('''    constexpr int Chunk = 64;
    static_assert(HiddenSize % Chunk == 0, "HiddenSize must be a multiple of the refresh chunk");''',
     '''    FORGE_V2_STAT(v2_cached, 1);
    FORGE_V2_STAT(v2_cached_cols, subs + adds);
    constexpr int Chunk = 64;
    static_assert(HiddenSize % Chunk == 0, "HiddenSize must be a multiple of the refresh chunk");'''),
    ('''    if (subs == 1 && adds == 1) apply_columns<1, 1>(parent, child, sub.data(), add.data());''',
     '''    FORGE_V2_STAT(v2_updates, 1);
    FORGE_V2_STAT(v2_update_cols, subs + adds);
    if (subs == 1 && adds == 1) apply_columns<1, 1>(parent, child, sub.data(), add.data());'''),
]
EDITS_CPP = [
    ('void refresh(const Board& board, Accumulator& accumulator) {\n',
     'void refresh(const Board& board, Accumulator& accumulator) {\n    FORGE_V2_STAT(v1_refreshes, 1);\n'),
    ('void update(const Accumulator& parent, Accumulator& child, const DirtyPieces& dirty) {\n',
     'void update(const Accumulator& parent, Accumulator& child, const DirtyPieces& dirty) {\n    FORGE_V2_STAT(v1_updates, 1);\n'),
    ('} // namespace forge::nnue::v2\n',
     '''#if defined(FORGE_NNUE_V2_STATS) && FORGE_NNUE_V2_STATS
namespace {
struct StatsPrinter {
    ~StatsPrinter() {
        const Stats& s = stats;
        std::fprintf(stderr, "v2stats v1: evals %llu walks %llu walk_plies %llu updates %llu refreshes %llu\\n",
                     s.v1_evals, s.v1_walks, s.v1_walk_plies, s.v1_updates, s.v1_refreshes);
        std::fprintf(stderr, "v2stats v2: evals %llu walks %llu walk_plies %llu updates %llu update_cols %llu cached %llu "
                     "cached_cols %llu full %llu noancestor %llu\\n", s.v2_evals, s.v2_walks, s.v2_walk_plies,
                     s.v2_updates, s.v2_update_cols, s.v2_cached, s.v2_cached_cols, s.v2_full, s.v2_noancestor);
    }
} stats_printer;
}  // namespace
#endif
} // namespace forge::nnue::v2
'''),
]
EDITS_SEARCH = [
    ('''        while (back < ss->ply && !(ss - back - 1)->accumulator.valid) ++back;
        if (back >= ss->ply && !(ss - back - 1)->accumulator.valid) {
            nnue::v2::RefreshCache& cache = nnue::v2::cache(net, id_);''',
     '''        while (back < ss->ply && !(ss - back - 1)->accumulator.valid) ++back;
        FORGE_V2_STAT(v2_walks, 1);
        FORGE_V2_STAT(v2_walk_plies, back + 1);
        if (back >= ss->ply && !(ss - back - 1)->accumulator.valid) {
            FORGE_V2_STAT(v2_noancestor, 1);
            nnue::v2::RefreshCache& cache = nnue::v2::cache(net, id_);'''),
    ('''    const nnue::v2::Net& net = *active;
    const bool residual = net.residual;''',
     '''    const nnue::v2::Net& net = *active;
    const bool residual = net.residual;
    FORGE_V2_STAT(v2_evals, 1);'''),
    ('''    const bool residual = nnue::residual();
    if (!ss->accumulator.valid) {
        // Walk back to the nearest valid accumulator, then replay the moves.
        int back = 0;
        while (back < ss->ply && !(ss - back - 1)->accumulator.valid) ++back;''',
     '''    const bool residual = nnue::residual();
    FORGE_V2_STAT(v1_evals, 1);
    if (!ss->accumulator.valid) {
        // Walk back to the nearest valid accumulator, then replay the moves.
        int back = 0;
        while (back < ss->ply && !(ss - back - 1)->accumulator.valid) ++back;
        FORGE_V2_STAT(v1_walks, 1);
        FORGE_V2_STAT(v1_walk_plies, back + 1);'''),
]


def plan(path, edits):
    """(path, original bytes, new bytes, edits) with every edit applied in memory, or an error text. Writes nothing."""
    original = path.read_bytes()
    raw = original.decode('utf-8')
    crlf = '\r\n' in raw
    text = raw.replace('\r\n', '\n')
    for old, new in edits:
        n = text.count(old)
        if n != 1:
            return None, f'{path}: anchor found {n} times: {old.splitlines()[0][:80]!r}'
        text = text.replace(old, new, 1)
    if path.name == 'nnue.cpp' and '#include <cstdio>' not in text:
        if text.count('#include <algorithm>\n') != 1:
            return None, f'{path}: no unique #include <algorithm> to add <cstdio> after'
        text = text.replace('#include <algorithm>\n', '#include <algorithm>\n#include <cstdio>\n', 1)
    return (path, original, (text.replace('\n', '\r\n') if crlf else text).encode('utf-8'), len(edits)), None


def apply_all(jobs):
    """All or nothing (the Code Review finding on o30_v2int16.py applies here too: three files, written one by one, could
    leave a half-instrumented tree): every anchor of every file first, then all writes; a failed write restores."""
    plans, errors = [], []
    for path, edits in jobs:
        p, err = plan(path, edits)
        if err:
            errors.append(err)
        else:
            plans.append(p)
    if errors:
        sys.exit('no file written:\n  ' + '\n  '.join(errors))
    written = []
    try:
        for path, original, new, _ in plans:
            path.write_bytes(new)
            written.append((path, original))
    except OSError as e:
        for path, original in written:
            path.write_bytes(original)
        sys.exit(f'write failed ({e}); the files written before it were restored - no file changed')
    for path, _, _, n in plans:
        print(f'{path}: {n} edits')


def main():
    repo = Path(sys.argv[1])
    files = [(repo / 'include' / 'forge' / 'nnue_v2.hpp', EDITS_HPP), (repo / 'src' / 'nnue.cpp', EDITS_CPP),
             (repo / 'src' / 'search.cpp', EDITS_SEARCH)]
    if any('FORGE_V2_STAT' in p.read_text(encoding='utf-8') for p, _ in files):
        sys.exit('refusing: the tree already has (part of) the counters')
    apply_all(files)


if __name__ == '__main__':
    main()
