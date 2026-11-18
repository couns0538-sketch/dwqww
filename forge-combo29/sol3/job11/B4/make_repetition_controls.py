import difflib
from pathlib import Path
import sys

tree, target = map(Path, sys.argv[1:])
source = (tree / 'src/board.cpp').read_text(encoding='ascii')
push = '        pv.push_back(pv.back() ^ (undo.key ^ key_ ^ Z.side));'
previous = 'opp_prefix_[(key_history_.size() - 1U) & 1U]'
controls = {
    'C1': ('bool Board::make_move(', push, '        pv.push_back(pv.back() + 1ULL);'),
    'C2': ('bool Board::upcoming_repetition_unchecked(', '            if (check_candidate(r - 7 + hi_lane)) return true;',
           '            if (check_candidate(r - 7 + (hi_lane ^ 1))) return true;'),
    'C3': ('bool Board::upcoming_repetition_unchecked(', '        if (pdata[r] == target && check_candidate(r)) return true;',
           '        if (pdata[r] == (target ^ 1ULL) && check_candidate(r)) return true;'),
    'C4': ('void Board::unmake_move(', f'    {previous}.pop_back();',
           f'    {previous}.erase({previous}.end() - 2);'),
    'C5': ('void Board::make_null_move(', push, '        pv.push_back(pv.back() ^ (undo.key ^ key_ ^ Z.side) ^ 1ULL);'),
}
for arm, (function, old, new) in controls.items():
    start = source.index(function)
    end = source.index('\n}\n', start)
    section = source[start:end]
    if section.count(old) != 1:
        raise ValueError(f'{arm}: expected one matching source line')
    changed = source[:start] + section.replace(old, new) + source[end:]
    diff = difflib.unified_diff(source.splitlines(keepends=True), changed.splitlines(keepends=True),
                                'a/src/board.cpp', 'b/src/board.cpp')
    (target / f'{arm}.patch.txt').write_text(''.join(diff), encoding='ascii')
