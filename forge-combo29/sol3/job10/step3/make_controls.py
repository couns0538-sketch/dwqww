import difflib
from pathlib import Path
import sys

tree, patches = map(Path, sys.argv[1:])
changes = {
    'C1': ('include/forge/search.hpp',
           '        const unsigned hit_m = static_cast<unsigned>(occ_m) & (static_cast<unsigned>(key_eq) << 3U);',
           '        const unsigned hit_m = static_cast<unsigned>(occ_m) & (static_cast<unsigned>(key_eq) << 2U);'),
    'C2': ('src/search.cpp',
           '    return replace_slot;',
           '    return static_cast<std::uint8_t>(replace_slot ^ 1U);'),
    'C3': ('src/search.cpp',
           '        entry = &cluster.entries[static_cast<unsigned>(__builtin_ctz(hit_m)) >> 2U];',
           '        entry = &cluster.entries[((static_cast<unsigned>(__builtin_ctz(hit_m)) >> 2U) + 1U) & 3U];'),
}
for arm, (filename, before, after) in changes.items():
    original = (tree / filename).read_text(encoding='ascii')
    lines = original.splitlines(keepends=True)
    if lines.count(before + '\n') != 1:
        raise ValueError(f'{arm}: expected one exact matching line')
    changed = lines.copy()
    changed[lines.index(before + '\n')] = after + '\n'
    text = ''.join(difflib.unified_diff(lines, changed, f'a/{filename}', f'b/{filename}'))
    (patches / f'{arm}.patch.txt').write_text(text, encoding='ascii')
