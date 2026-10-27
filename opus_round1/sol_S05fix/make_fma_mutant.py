#!/usr/bin/env python3
"""Planted bug for the S05-1 check: in a COPY of the source tree, make the LMR reduction-table setup in
src/search.cpp use std::fma (one line; the pattern must occur exactly once). Built with an FMA-capable -march,
this puts fused multiply-adds into forge::(anonymous)::ReductionTable::refresh(), i.e. outside forge::nnue::.
The v3 checker (forge::nnue:: scope only) passes such a binary; v4 must fail it with a nonzero whole-.text count.
Never run on a real source tree: the copy is a mutant for the checker test only.
usage: make_fma_mutant.py <copied_src_root>"""
from pathlib import Path
import sys

root = Path(sys.argv[1])
path = root / 'src' / 'search.cpp'
text = path.read_text(encoding='utf-8')
old = 'std::max(0.0, tune::LmrQuietBase / 100.0 + product / (tune::LmrQuietDivisor / 100.0)));'
new = 'std::max(0.0, std::fma(product, 100.0 / tune::LmrQuietDivisor, tune::LmrQuietBase / 100.0)));'
if text.count(old) != 1:
    raise SystemExit(f'mutant pattern found {text.count(old)} times, expected 1')
if '#include <cmath>' not in text:
    text = text.replace('#include <algorithm>', '#include <algorithm>\n#include <cmath>', 1)
path.write_text(text.replace(old, new), encoding='utf-8')
print(f'mutant written: {path} (std::fma in ReductionTable::refresh)')
