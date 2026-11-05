#!/usr/bin/env python3
"""make_poison.py - poison copy of a stacked source tree (speed job follow-up, own code; patch review QA test 5).

usage: python -I -B make_poison.py <src tree> <dst tree>

Copies <src> (its include/ and src/ folders; e.g. F:/ospd/packs/<stack>/src_kit, switches already ON) to <dst>, which
must not exist, and inserts the poison blocks of the authors' own verify build (F:/ospd/src/b2_no_zero_movelists_verify,
POISON part only, same text) for FORGE_SPD_NO_ZERO_MOVELISTS:
  - board.hpp, before `namespace forge {`: macro FORGE_SPD_NO_ZERO_MOVELISTS_POISON (default 0) and <cstring>;
  - board.hpp, MoveList: a constructor that fills data_ with 0xA5 bytes;
  - search.cpp, MovePicker constructor body: moves_, bad_captures_, check_squares_ filled with 0xA5;
  - search.cpp, after the declarations of quiets_tried / captures_tried (the switch-ON branch): both filled with 0xA5.
Every anchor must occur exactly once and the switch must be ON (`#define FORGE_SPD_NO_ZERO_MOVELISTS 1|2`), else exit 2
and nothing is written. Line endings follow each file (CRLF or LF). Build the copy with
-Define FORGE_SPD_NO_ZERO_MOVELISTS_POISON=1: every array that lost its zero fill then starts as 0xA5 garbage, so any
read before a write changes nodes. A verify build only, never a candidate. Writes only <dst>.
"""
import hashlib
import pathlib
import re
import shutil
import sys

MACRO = ('// Verify build only (never in the patch): fill every array that lost its zero\n'
         '// fill with 0xA5 bytes at construction; the node counts must stay the lock\'s.\n'
         '#ifndef FORGE_SPD_NO_ZERO_MOVELISTS_POISON\n'
         '#define FORGE_SPD_NO_ZERO_MOVELISTS_POISON 0\n'
         '#endif\n'
         '#if FORGE_SPD_NO_ZERO_MOVELISTS_POISON\n'
         '#include <cstring>\n'
         '#endif\n'
         '\n')
EDITS = [
    # (file, anchor, text, 'before' | 'after')
    ('include/forge/board.hpp', 'namespace forge {\n', MACRO, 'before'),
    ('include/forge/board.hpp', '    using const_iterator = std::array<Move, Capacity>::const_iterator;\n',
     '#if FORGE_SPD_NO_ZERO_MOVELISTS_POISON\n'
     '    MoveList() { std::memset(&data_, 0xA5, sizeof(data_)); }\n'
     '#endif\n', 'after'),
    ('src/search.cpp', 'tt_move_(tt_move) {\n',
     '#if FORGE_SPD_NO_ZERO_MOVELISTS_POISON\n'
     '        std::memset(&moves_, 0xA5, sizeof(moves_));\n'
     '        std::memset(&bad_captures_, 0xA5, sizeof(bad_captures_));\n'
     '        std::memset(&check_squares_, 0xA5, sizeof(check_squares_));\n'
     '#endif\n', 'after'),
    ('src/search.cpp', '    std::array<Move, 128> quiets_tried;\n    std::array<Move, 64> captures_tried;\n',
     '#if FORGE_SPD_NO_ZERO_MOVELISTS_POISON\n'
     '    std::memset(&quiets_tried, 0xA5, sizeof(quiets_tried));\n'
     '    std::memset(&captures_tried, 0xA5, sizeof(captures_tried));\n'
     '#endif\n', 'after'),
]
SWITCH = re.compile(rb'^#define FORGE_SPD_NO_ZERO_MOVELISTS [12]\r?$', re.M)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    if dst.exists():
        print(f'refusing: {dst} exists')
        return 2
    for sub in ('include', 'src'):
        if not (src / sub).is_dir():
            print(f'refusing: {src / sub} missing')
            return 2
    texts = {}
    for rel in sorted({e[0] for e in EDITS}):
        texts[rel] = (src / rel).read_bytes()
    if not SWITCH.search(texts['include/forge/board.hpp']):
        print('refusing: FORGE_SPD_NO_ZERO_MOVELISTS is not ON in board.hpp (the poison would be dead code)')
        return 2
    new = dict(texts)
    for rel, anchor, text, where in EDITS:
        data = new[rel]
        crlf = b'\r\n' in data
        conv = (lambda s: s.replace('\n', '\r\n').encode()) if crlf else (lambda s: s.encode())
        a, t = conv(anchor), conv(text)
        n = data.count(a)
        if n != 1:
            print(f'refusing: anchor {anchor!r} found {n} times in {rel}')
            return 2
        new[rel] = data.replace(a, t + a if where == 'before' else a + t)
    shutil.copytree(src / 'include', dst / 'include')
    shutil.copytree(src / 'src', dst / 'src')
    for rel, data in new.items():
        (dst / rel).write_bytes(data)
    for rel in sorted(new):
        added = new[rel].count(b'FORGE_SPD_NO_ZERO_MOVELISTS_POISON')
        print(f'{rel}: {sha(texts[rel])[:12]} -> {sha(new[rel])[:12]} ({added} poison macro uses)')
    print(f'poison copy written: {dst}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
