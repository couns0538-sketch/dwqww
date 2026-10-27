#!/usr/bin/env python3
"""make_s47_fixtures.py (S47, opus 2026-10-27): deterministic synthetic fixtures for Part A and Part B.
Part A: a lock tree and candidate trees (net-only, CRLF-only edits, src change, extra file, identical) + an AUTOLOCK-style
dir + a CAP-LATE Z re-gate record. Part B: an old AUTOLOCK_1 and a new AUTOLOCK_2 dir as autopromote.ps1 writes them
(LOCK.json, SOURCES.sha256, exe + .sha256, nnue_weights.inc + .md5, BENCH_REF.txt, PERFT.txt, UCI_OPTIONS.txt, PINS.md,
pins/ with one allow-listed reviewed diff), gate + confirm RESULT.md / RUN_INFO.json / manifest records, pin allow-list.
The tests copy these to scratch before planting a defect. Writes only into --out (default fixtures/ next to this file)."""
import argparse
import hashlib
import json
import os

LF = '\n'


def w(path, data, crlf=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    b = data.encode('utf-8') if isinstance(data, str) else data
    if crlf:
        b = b.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    with open(path, 'wb') as f:
        f.write(b)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def md5(b):
    return hashlib.md5(b).hexdigest()


HPP = '#pragma once\nnamespace forge { int answer(); }\n'
CPP = '#include "forge/a.hpp"\nint forge::answer() { return 42; }\nint main() { return forge::answer() == 42 ? 0 : 1; }\n'
NET_OLD = '// FORGE_NNUE H256 fixture net OLD\nstatic const short w[4] = {1, 2, 3, 4};\n'
NET_NEW = '// FORGE_NNUE H256 fixture net NEW (f030-like)\nstatic const short w[4] = {5, 6, 7, 8};\n'
PINS_TXT = 'bench_pin d11 312866\nbench_pin d13 862329\n'
UCI = 'option name Hash type spin default 32 min 1 max 2048\noption name Threads type spin default 1 min 1 max 256\noption name UseNNUE type check default true\n'
OLD_BENCH = [312866, 862329, 3024920, 12389307, 34048354]
NEW_BENCH = [445320, 1123540, 4197338, 14179708, 28577307]
PIN_DIFF = ('--- a/tests/pins.txt\n+++ b/tests/pins.txt\n@@ -1,2 +1,2 @@\n-bench_pin d11 312866\n+bench_pin d11 445320\n'
            ' bench_pin d13 862329\n# PROPOSED pin re-record, reviewed; attached to the lock, never applied by the lock tooling\n')


def tree(root, net, crlf=False, extra=None, cpp=CPP, tests=False):
    w(os.path.join(root, 'include', 'forge', 'a.hpp'), HPP, crlf)
    w(os.path.join(root, 'src', 'main.cpp'), cpp, crlf)
    w(os.path.join(root, 'src', 'nnue_weights.inc'), net)
    if extra:
        w(os.path.join(root, 'src', 'extra.cpp'), extra)
    if tests:
        w(os.path.join(root, 'tests', 'pins.txt'), PINS_TXT)


def sources_sha(root):
    lines = []
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            p = os.path.join(dp, f)
            with open(p, 'rb') as fh:
                lines.append(f'{sha(fh.read())}  {os.path.relpath(p, root).replace(os.sep, "/")}')
    return '\n'.join(sorted(lines, key=lambda s: s.split('  ', 1)[1])) + '\n'


def bench_ref(b):
    s = '/'.join(map(str, b))
    return f'bench d11/13/16/20/22 (Threads 1 Hash 16 OwnBook false): {s}\nrepeat: {s}\n'


def lock_dir(d, n, tag, exe_name, exe_bytes, net, bench, parent, pins=None):
    tree(os.path.join(d, 'source'), net, tests=True)
    w(os.path.join(d, 'SOURCES.sha256'), sources_sha(os.path.join(d, 'source')))
    w(os.path.join(d, exe_name), exe_bytes)
    w(os.path.join(d, exe_name + '.sha256'), f'{sha(exe_bytes)} *{exe_name}\n')
    w(os.path.join(d, 'nnue_weights.inc'), net)
    w(os.path.join(d, 'nnue_weights.inc.md5'), f'{md5(net.encode())} *nnue_weights.inc\n')
    w(os.path.join(d, 'BENCH_REF.txt'), bench_ref(bench))
    w(os.path.join(d, 'PERFT.txt'), 'perft 5 startpos: 4865609 (want 4865609)\nperft 5 kiwipete: 193690690 (want 193690690)\nFMA instructions (objdump -Cd): 0\n')
    w(os.path.join(d, 'UCI_OPTIONS.txt'), UCI)
    w(os.path.join(d, 'PINS.md'), 'fixture lock pins note\n' if not pins else 'staged pin diffs attached in pins/ (reviewed, not applied)\n')
    if pins:
        for name, body in pins.items():
            w(os.path.join(d, 'pins', name), body)
    lj = {'n': n, 'tag': tag, 'kind': 'net', 'exe': exe_name, 'sha256': sha(exe_bytes).upper(), 'net_md5': md5(net.encode()).upper(), 'parent': parent}
    w(os.path.join(d, 'LOCK.json'), json.dumps(lj, indent=1) + LF)
    return lj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures'))
    a = ap.parse_args()
    o = a.out
    A = os.path.join(o, 'partA')
    tree(os.path.join(A, 'lock'), NET_OLD)
    tree(os.path.join(A, 'cand_net'), NET_NEW)
    tree(os.path.join(A, 'cand_crlf'), NET_NEW, crlf=True)
    tree(os.path.join(A, 'cand_src'), NET_NEW, cpp=CPP.replace('42', '43'))
    tree(os.path.join(A, 'cand_extra'), NET_NEW, extra='int extra() { return 1; }\n')
    tree(os.path.join(A, 'cand_same'), NET_OLD)
    tree(os.path.join(A, 'AUTOLOCK_1_fx', 'source'), NET_OLD)
    w(os.path.join(A, 'AUTOLOCK_1_fx', 'LOCK.json'), json.dumps({'n': 1, 'tag': 'AUTOLOCK_1_fx', 'kind': 'net', 'net_md5': md5(NET_OLD.encode()).upper()}, indent=1) + LF)
    w(os.path.join(A, 'gate_regate.json'), json.dumps({'tag': 'gate104_e48f006_rebase_vs_AL1', 'ag_rebase_of': 'gate104_e48f006_vs_h256e12', 'ag_rebase_exempt24': True}, indent=1) + LF)
    w(os.path.join(A, 'expected_net_md5.txt'), md5(NET_NEW.encode()) + LF)

    B = os.path.join(o, 'partB')
    old_exe, new_exe = b'MZ fixture old lock exe\n', b'MZ fixture new lock exe (gated)\n'
    oj = lock_dir(os.path.join(B, 'locks', 'AUTOLOCK_1_gate120_fx'), 1, 'AUTOLOCK_1_gate120_fx', 'forge_fx_old.exe', old_exe, NET_OLD, OLD_BENCH,
                  {'n': 0, 'tag': 'h256_e12', 'sha256': '456743D9C065D2DEC2D9A52EF23992F36908EFC1243B6916EDAB9A8AB3C7FDFA'})
    lock_dir(os.path.join(B, 'locks', 'AUTOLOCK_2_gate130_fx'), 2, 'AUTOLOCK_2_gate130_fx', 'forge_fx_new.exe', new_exe, NET_NEW, NEW_BENCH, oj,
             pins={'e48f006_pin_rerecord_PROPOSED.diff': PIN_DIFF})
    for lab, srand, start in (('gate', 344808634, 321001), ('confirm', 1983003762, 348001)):
        w(os.path.join(B, lab, 'RESULT.md'), f'# gate130_fx{"_confirm" if lab == "confirm" else ""} RESULT\n- Settings: 10+0.1, srand {srand}, 8moves_v3.pgn start={start}\n'
                                             f'**Verdict: H1 accepted (SPRT [0,10] normalized)**\n')
        w(os.path.join(B, lab, 'RUN_INFO.json'), json.dumps({'srand': srand, 'openings_start': start, 'attempt': 1, 'fresh_srand': False,
                                                             'candidate': {'sha256': sha(new_exe).upper()}, 'base': {'sha256': oj['sha256']}}, indent=1) + LF)
        w(os.path.join(B, lab, 'record.json'), json.dumps({'tag': 'gate130_fx' + ('_confirm' if lab == 'confirm' else ''), 'srand': srand, 'openings_start': start,
                                                          'prebench': {'cand_off': NEW_BENCH}}, indent=1) + LF)
    w(os.path.join(B, 'pin_allow.json'), json.dumps([{'name': 'e48f006_pin_rerecord_PROPOSED.diff', 'md5_prefix': md5(PIN_DIFF.encode())[:8],
                                                      'net_md5': md5(NET_NEW.encode())}], indent=1) + LF)
    w(os.path.join(B, 'net_md5.txt'), md5(NET_NEW.encode()) + LF)
    os.makedirs(os.path.join(B, 'cr'), exist_ok=True)
    w(os.path.join(B, 'cr', 'CR_PASS_AUTOLOCK_1.txt'), 'PASS AUTOLOCK_1_gate120_fx (fixture CR record)\n')
    print('fixtures written to', o)


if __name__ == '__main__':
    main()
