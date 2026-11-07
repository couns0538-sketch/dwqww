#!/usr/bin/env python3
"""apply_trc.py - make the TtReplaceCache source change on a trial_w6 copy (own code, 2026-11-06; anchored, fail closed).

usage: python -I -B apply_trc.py <tree>      (edits <tree>/include/forge/search.hpp, src/search.cpp, src/uci.cpp in place)
Every anchor must occur exactly once (search.cpp's replace loop: exactly twice = the TT_NOTLS and the plain probe);
LF files are kept LF. All new lines sit inside #if FORGE_SPD_TT_REPLACE_CACHE (default 0).
"""
import sys
from pathlib import Path

LOOP = """    for (const TTEntry& entry : cluster.entries) {
        if (!entry.occupied()) return snapshot(entry, false);
        if (entry.depth - 4 * relative_age(entry) < replace->depth - 4 * relative_age(*replace)) replace = &entry;
    }
"""
CACHED = """#if FORGE_SPD_TT_REPLACE_CACHE
    if (tt_replace_cache) {
        // TtReplaceCache=1: the current pick's metric is kept instead of recomputed per slot. Same slot order 0..3,
        // the first empty slot still returns at once, the same strict '<' (a tie keeps the earlier slot).
        int replace_value = replace->depth - 4 * relative_age(*replace);
        for (const TTEntry& entry : cluster.entries) {
            if (!entry.occupied()) return snapshot(entry, false);
            const int value = entry.depth - 4 * relative_age(entry);
            if (value < replace_value) {
                replace = &entry;
                replace_value = value;
            }
        }
        return snapshot(*replace, false);
    }
#endif
"""
EDITS = [
    ('include/forge/search.hpp', 1,
     '#define FORGE_SPD_TT_NOTLS 0\n#endif\n',
     '#define FORGE_SPD_TT_NOTLS 0\n#endif\n\n'
     '#ifndef FORGE_SPD_TT_REPLACE_CACHE\n'
     '// Build switch, default 0 (= the lock\'s code; nothing of it is compiled): 1 adds the UCI option TtReplaceCache\n'
     '// (default 0) that keeps the TT replace metric of the current pick instead of recomputing it per slot.\n'
     '#define FORGE_SPD_TT_REPLACE_CACHE 0\n#endif\n'),
    ('include/forge/search.hpp', 1,
     'namespace forge {\n',
     'namespace forge {\n#if FORGE_SPD_TT_REPLACE_CACHE\n'
     '// Runtime switch of the cached replace metric (UCI TtReplaceCache, false = the lock loop).\n'
     'extern bool tt_replace_cache;\n#endif\n'),
    ('src/search.cpp', 1,
     'namespace forge {\n',
     'namespace forge {\n#if FORGE_SPD_TT_REPLACE_CACHE\nbool tt_replace_cache = false;\n#endif\n'),
    ('src/search.cpp', 2, LOOP, CACHED + LOOP),
    ('src/uci.cpp', 1,
     '            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\\n";\n',
     '            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\\n";\n'
     '#if FORGE_SPD_TT_REPLACE_CACHE\n'
     '            std::cout << "option name TtReplaceCache type spin default 0 min 0 max 1\\n";\n#endif\n'),
    ('src/uci.cpp', 1,
     '                    std::cout << "info string invalid value for option UseNNUE" << std::endl;\n'
     '                }\n                searcher.clear_hash();\n',
     '                    std::cout << "info string invalid value for option UseNNUE" << std::endl;\n'
     '                }\n                searcher.clear_hash();\n'
     '#if FORGE_SPD_TT_REPLACE_CACHE\n'
     '            } else if (name == "TtReplaceCache") {\n'
     '                if (value_text == "0") forge::tt_replace_cache = false;\n'
     '                else if (value_text == "1") forge::tt_replace_cache = true;\n'
     '                else {\n'
     '                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n'
     '                    std::cout << "info string invalid value for option TtReplaceCache" << std::endl;\n'
     '                }\n#endif\n'),
]


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    tree = Path(sys.argv[1])
    texts = {}
    for rel, count, old, new in EDITS:
        p = tree / rel
        s = texts.get(rel) or p.read_bytes().decode('ascii')
        if '\r' in s:
            raise SystemExit('apply_trc: CR bytes in %s' % rel)
        n = s.count(old)
        if n != count:
            raise SystemExit('apply_trc: anchor found %d times (want %d) in %s: %r' % (n, count, rel, old[:60]))
        texts[rel] = s.replace(old, new)
    for rel, s in texts.items():
        (tree / rel).write_bytes(s.encode('ascii'))
        print('apply_trc: edited %s' % rel)


if __name__ == '__main__':
    main()
