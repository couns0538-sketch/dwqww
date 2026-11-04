#!/usr/bin/env python3
"""test_patch_atomic.py - Opus 30-h job: the multi-file patch scripts must change all their files or none
(Code Review 2026-11-04, CR_O30_V2INT16_20261104: o30_v2int16.py wrote the header before checking the loader anchor).
For o30_v2int16.py (2 files) and o30_v2stats.py (3 files), on copies of the v2port tree's files:
  A planted anchor mismatch in the LAST file  -> exit != 0 and every file byte-identical (sha256) to before;
  B a clean tree                              -> exit 0 and every file changed;
  C a re-run on B's result                    -> exit != 0 and every file unchanged from B;
  D a half-edited tree (only the first file)  -> exit != 0 (refused) and unchanged.
Prints PASS / FAIL per case and PATCH ATOMIC PASS / FAIL; exit 0 only on PASS. Own code."""
import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path(r'D:\o30\repos\v2port')
FILES = {'o30_v2int16.py': ['include/forge/nnue_v2.hpp', 'src/nnue.cpp'],
         'o30_v2stats.py': ['include/forge/nnue_v2.hpp', 'src/nnue.cpp', 'src/search.cpp']}
# a line of the last file that one of the script's anchors contains (breaking it plants a mismatch)
BREAK = {'o30_v2int16.py': ('src/nnue.cpp', 'static_cast<float>(read_i16(bytes, offset)) / WeightScale;'),
         'o30_v2stats.py': ('src/search.cpp', '    const bool residual = net.residual;')}


def tree(root, rels):
    for rel in rels:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SRC / rel, root / rel)


def hashes(root, rels):
    return {rel: hashlib.sha256((root / rel).read_bytes()).hexdigest() for rel in rels}


def run(script, root):
    return subprocess.run([sys.executable, '-I', '-B', str(HERE / script), str(root)], capture_output=True, text=True).returncode


def main():
    base = Path(r'D:\o30\tmp') / f'atomic_{time.strftime("%H%M%S")}'
    fails = 0

    def check(name, ok):
        nonlocal fails
        fails += not ok
        print(f"{'PASS' if ok else 'FAIL'} {name}")
    for script, rels in FILES.items():
        # A: planted mismatch in the last file
        a = base / script / 'A'
        tree(a, rels)
        rel, needle = BREAK[script]
        text = (a / rel).read_bytes()
        assert needle.encode() in text, f'{script}: the needle is not in {rel}'
        broken = needle.replace(' ', '  ', 1)   # INSIDE the anchor text (appending after it would still match)
        (a / rel).write_bytes(text.replace(needle.encode(), broken.encode(), 1))
        before = hashes(a, rels)
        rc = run(script, a)
        check(f'{script} A: planted mismatch in {rel} -> refused ({rc}), no file changed', rc != 0 and hashes(a, rels) == before)
        # B: clean tree, C: re-run
        b = base / script / 'B'
        tree(b, rels)
        before = hashes(b, rels)
        rc = run(script, b)
        after = hashes(b, rels)
        check(f'{script} B: clean tree -> exit 0, all {len(rels)} files changed', rc == 0 and all(after[r] != before[r] for r in rels))
        rc = run(script, b)
        check(f'{script} C: re-run -> refused ({rc}), unchanged', rc != 0 and hashes(b, rels) == after)
        # D: half-edited tree = B's first file + the original others
        d = base / script / 'D'
        tree(d, rels)
        shutil.copyfile(b / rels[0], d / rels[0])
        before = hashes(d, rels)
        rc = run(script, d)
        check(f'{script} D: half-edited tree -> refused ({rc}), unchanged', rc != 0 and hashes(d, rels) == before)
    print(f"PATCH ATOMIC {'PASS' if fails == 0 else 'FAIL'}: {fails} failing case(s) (trees under {base})")
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
