#!/usr/bin/env python3
"""o30_v2rootfix.py <v2port scratch repo> - Opus 30-h job: refresh the ROOT accumulator of a v2 net at the start of each
search, as the compiled-in net does (own code; one anchored edit in src/search.cpp, refused if missing / not unique).

Found 2026-11-04 with the FORGE_NNUE_V2_STATS counters (o30_v2stats.py + stats_run_o30.py): on 100 game positions in
one long-lived process (hash kept, as in a game) the v2 path had the same evaluations as v1 (4.14M) but 777k of them
found NO valid ancestor up to the root (19 %): the port skipped the root refresh ("lazy"), and in games the root's
static evaluation usually comes from the hash table, so the root accumulator was never built and every subtree without
an evaluated ancestor was rebuilt from the refresh cache (1.55M cached refreshes, 2.3x the walk plies). The bench
clears the hash per position, so it never showed this. The fix evaluates the root once through static_evaluate_v2
(both perspectives refreshed exactly through the cache, the runtime PSQT for a residual net). Accumulators are exact
however they are built, so evaluations and node counts do not change; the default path gains one branch per search.
"""
import sys
from pathlib import Path

OLD = '''    // A v2 net (EvalFileV2) refreshes the root lazily in static_evaluate_v2.
    if (nnue::v2::active_net == nullptr && nnue::enabled && nnue::available()) {
        nnue::refresh(board, ss->accumulator);
        if (nnue::residual()) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
    }
'''
NEW = '''    if (nnue::v2::active_net == nullptr && nnue::enabled && nnue::available()) {
        nnue::refresh(board, ss->accumulator);
        if (nnue::residual()) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
    } else if (nnue::v2::active_net != nullptr && nnue::enabled) [[unlikely]] {
        // A v2 net: build the root accumulators now, as above. Left lazy, a root whose evaluation comes from the
        // hash table never gets them, and every subtree without an evaluated ancestor rebuilds from the cache.
        (void)static_evaluate_v2(board, ss);
    }
'''


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    p = Path(sys.argv[1]) / 'src' / 'search.cpp'
    raw = p.read_bytes().decode('utf-8')
    crlf = '\r\n' in raw
    text = raw.replace('\r\n', '\n')
    n = text.count(OLD)
    if n != 1:
        sys.exit(f'{p}: anchor found {n} times (need 1)')
    text = text.replace(OLD, NEW, 1)
    p.write_bytes((text.replace('\n', '\r\n') if crlf else text).encode('utf-8'))
    print(f'{p}: root refresh for v2 nets added ({"CRLF" if crlf else "LF"})')


if __name__ == '__main__':
    main()
