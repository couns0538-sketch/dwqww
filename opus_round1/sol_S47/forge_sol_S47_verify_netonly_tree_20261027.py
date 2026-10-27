#!/usr/bin/env python3
"""forge_sol_S47_verify_netonly_tree_20261027.py: S47 Part A, net-only tree check (opus, 2026-10-27).

verify_netonly_tree: compares a lock tree with a candidate tree and exits 0 ONLY if the single difference is
src/nnue_weights.inc and that file has the expected md5. Every file under the scope (default include/ and src/) is
hashed after CRLF->LF, so CRLF-only edits are ignored (and listed). Prints a JSON verdict with the diff list.
  --lock DIR   a lock source tree (include/, src/) or ANY AUTOLOCK dir (its tree is DIR/source; LOCK.json is read)
  --cand DIR   the candidate tree (or an AUTOLOCK dir)
  --net-md5    expected md5 of the candidate's src/nnue_weights.inc (raw bytes; an LF-normalised match is reported too)
  --gate-json  optional manifest gate record: a CAP-LATE Z re-gate (ag_rebase_of set) whose tree is not net-only vs
               the lock gives a FAIL with a Z-1 message
Read-only. Exit 0 PASS, 1 FAIL, 2 usage error.
"""
import argparse
import hashlib
import json
import os
import sys

VERSION = 'S47 verify_netonly_tree 2026-10-27 v1'
NET = 'src/nnue_weights.inc'


def tree_root(d):
    if os.path.isdir(os.path.join(d, 'source', 'src')):
        return os.path.join(d, 'source'), True
    return d, False


def lock_json(d):
    p = os.path.join(d, 'LOCK.json')
    if not os.path.isfile(p):
        return None
    try:
        with open(p, encoding='utf-8-sig') as f:
            j = json.load(f)
        return {k: j.get(k) for k in ('n', 'tag', 'kind', 'net_md5', 'sha256', 'exe')}
    except (OSError, ValueError) as ex:
        return {'unreadable': str(ex)}


def walk(root, scope):
    out = {}
    for top in scope:
        base = os.path.join(root, top)
        for dp, dn, fn in os.walk(base):
            dn.sort()
            for f in sorted(fn):
                full = os.path.join(dp, f)
                with open(full, 'rb') as fh:
                    b = fh.read()
                out[os.path.relpath(full, root).replace(os.sep, '/')] = (hashlib.sha256(b).hexdigest(), hashlib.sha256(b.replace(b'\r\n', b'\n')).hexdigest())
    return out


def md5s(path):
    with open(path, 'rb') as f:
        b = f.read()
    return hashlib.md5(b).hexdigest(), hashlib.md5(b.replace(b'\r\n', b'\n')).hexdigest()


def verify(lock, cand, net_md5, scope=('include', 'src'), gate=None):
    lroot, lal = tree_root(lock)
    croot, cal = tree_root(cand)
    reasons = []
    for nm, root in (('lock', lroot), ('cand', croot)):
        if not os.path.isdir(os.path.join(root, 'src')):
            reasons.append(f'{nm} tree has no src/ under {root}')
    L = walk(lroot, scope) if not reasons else {}
    C = walk(croot, scope) if not reasons else {}
    only_l, only_c = sorted(set(L) - set(C)), sorted(set(C) - set(L))
    both = set(L) & set(C)
    differ = sorted(k for k in both if L[k][1] != C[k][1])
    crlf_only = sorted(k for k in both if L[k][0] != C[k][0] and L[k][1] == C[k][1])
    non_net = [d for d in differ if d != NET] + [f'only in lock: {x}' for x in only_l] + [f'only in candidate: {x}' for x in only_c]
    net = {'path': NET, 'expected_md5': (net_md5 or '').lower(), 'md5_raw': None, 'md5_lf': None, 'match': None}
    if C and NET in C:
        net['md5_raw'], net['md5_lf'] = md5s(os.path.join(croot, NET))
        net['match'] = 'raw' if net['md5_raw'] == net['expected_md5'] else 'lf' if net['md5_lf'] == net['expected_md5'] else None
    if not reasons:
        if non_net:
            reasons.append('tree differs outside src/nnue_weights.inc: ' + ', '.join(non_net))
        if NET not in differ:
            reasons.append('src/nnue_weights.inc is identical to the lock (no new net)' if NET in both else 'src/nnue_weights.inc missing')
        if not net['match']:
            reasons.append(f"src/nnue_weights.inc md5 {net['md5_raw']} != expected {net['expected_md5']}")
    z1 = None
    if gate is not None:
        rb = gate.get('ag_rebase_of')
        z1 = {'gate': gate.get('tag'), 'ag_rebase_of': rb, 'net_only': not non_net and NET in differ}
        if rb and non_net:
            reasons.append(f"Z-1 (CAP-LATE Z): {gate.get('tag')} is a re-gate of {rb}, but its tree is not net-only vs the lock "
                           f"({', '.join(non_net)}); it must never be promoted as an AUTO-LOCK")
    lj = lock_json(lock)
    if lj and lj.get('net_md5') and os.path.isfile(os.path.join(lroot, NET)):
        lm = md5s(os.path.join(lroot, NET))[0]
        if lm != str(lj['net_md5']).lower():
            reasons.append(f"lock LOCK.json net_md5 {lj['net_md5']} != md5 of its own tree net {lm}")
    return {'tool': VERSION, 'lock': {'path': lock, 'tree': lroot, 'autolock_dir': lal, 'lock_json': lj}, 'candidate': {'path': cand, 'tree': croot, 'autolock_dir': cal},
            'scope': list(scope), 'files': {'lock': len(L), 'candidate': len(C)}, 'differ': differ, 'only_in_lock': only_l, 'only_in_candidate': only_c,
            'crlf_only_ignored': crlf_only, 'net': net, 'z1': z1, 'verdict': 'FAIL' if reasons else 'PASS', 'reasons': reasons}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--lock', required=True)
    ap.add_argument('--cand', required=True)
    ap.add_argument('--net-md5', required=True)
    ap.add_argument('--scope', default='include,src')
    ap.add_argument('--gate-json')
    ap.add_argument('--out')
    a = ap.parse_args(argv)
    for p in (a.lock, a.cand):
        if not os.path.isdir(p):
            print(f'S47 Part A: not a directory: {p}', file=sys.stderr)
            return 2
    gate = None
    if a.gate_json:
        with open(a.gate_json, encoding='utf-8-sig') as f:
            gate = json.load(f)
    res = verify(a.lock, a.cand, a.net_md5, tuple(x for x in a.scope.split(',') if x), gate)
    txt = json.dumps(res, indent=1, sort_keys=True) + '\n'
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(txt)
    sys.stdout.write(txt)
    return 0 if res['verdict'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
