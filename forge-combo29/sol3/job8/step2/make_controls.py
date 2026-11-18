import difflib
from pathlib import Path
import sys

root, tree, out = map(Path, sys.argv[1:])
name = Path('src/nnue_v3.cpp')
source = (tree / name).read_text(encoding='ascii')
controls = {
    'C1': (
        '        for (; a < n_add; ++a) {\n'
        '            v_ref = _mm512_add_epi16(v_ref, _mm512_load_si512(reinterpret_cast<const __m512i*>(adds[a] + h)));',
        '        for (; a < n_add; ++a) {\n'
        '            v_ref = _mm512_sub_epi16(v_ref, _mm512_load_si512(reinterpret_cast<const __m512i*>(adds[a] + h)));',
    ),
    'C2': (
        '            v_inc = ia0 ? _mm512_add_epi16(v_inc, col) : _mm512_sub_epi16(v_inc, col);',
        '            v_inc = ia0 ? _mm512_sub_epi16(v_inc, col) : _mm512_add_epi16(v_inc, col);',
    ),
    'C3': (
        '        for (; a + 4 <= n_add; a += 4) {\n'
        '            v = _mm512_add_epi16(v, _mm512_load_si512(reinterpret_cast<const __m512i*>(adds[a] + h)));',
        '        for (; a + 4 <= n_add; a += 4) {\n'
        '            v = _mm512_sub_epi16(v, _mm512_load_si512(reinterpret_cast<const __m512i*>(adds[a] + h)));',
    ),
}
for control, (before, after) in controls.items():
    if source.count(before) != 1:
        raise ValueError(f'{control}: exact source context was not unique')
    changed = source.replace(before, after)
    diff = list(difflib.unified_diff(source.splitlines(keepends=True), changed.splitlines(keepends=True),
                                      f'a/{name}', f'b/{name}'))
    if sum(line.startswith('+') for line in diff) != 2 or sum(line.startswith('-') for line in diff) != 2:
        raise ValueError(f'{control}: expected exactly one changed source line')
    (out / f'{control}.patch.txt').write_text(''.join(diff), encoding='ascii')
