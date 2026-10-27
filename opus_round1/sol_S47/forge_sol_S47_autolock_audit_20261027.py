#!/usr/bin/env python3
"""forge_sol_S47_autolock_audit_20261027.py: S47 Part B, AUTO-LOCK audit verifier (opus, 2026-10-27).

Reads (read-only) the old lock dir, the new AUTOLOCK_<n>_<tag> dir, the gate + confirm RESULT.md / RUN_INFO.json,
optional manifest gate records and the bench / perft / uci outputs, and writes ONE markdown packet for Code Review plus a
JSON twin. Every check is PASS, FAIL or MISSING; a missing input is flagged MISSING, never guessed. The tool never
writes CR_PASS_AUTOLOCK_<n>.txt and its verdict is evidence for CR, not a CR approval.

Checks
  A1 new lock is a NEW dir named AUTOLOCK_<n>_<tag>, n above the old lock, LOCK.json n/tag/parent consistent, no orphan
     lower-n AUTOLOCK dir next to it
  A2 old lock files unchanged: every file of the old lock's own hash list (recorded before the promote) re-hashed;
     the old exe sha256 equal to its recorded value
  A3 net md5 = the gated pack's net (and = nnue_weights.inc.md5 and LOCK.json net_md5)
  A4 exe sha256 = the gated exe (RUN_INFO candidate sha of gate AND confirm; = .sha256 file and LOCK.json)
  A5 bench d11-d22: two runs identical and node-exact to the gate's prebench.cand_off (or --expected-bench); differs
     from the old lock's own bench reference (net applied); the old reference is read from the old lock, never
     hard-coded
  A6 perft5 4865609 / kiwipete5 193690690 / FMA 0 (--perft-expect overrides the two perft numbers)
  A7 uci option list equal to the old lock's
  A8 confirm srand AND openings start differ from the gate's
  A9 gate and confirm verdicts are H1 accepted and not VOID
  A10 pins: attached pin files are unchanged or allow-listed reviewed diffs (attached, not applied); tests/ trees,
      when present in both lock trees, identical after CRLF->LF
  A11 INFO only: whether CR_PASS_AUTOLOCK_<n>.txt exists (this tool never grants it)
Overall: FAIL if any FAIL, else INCOMPLETE if any MISSING, else ALL_CHECKS_PASS. Exit 1 / 3 / 0 (2 = usage).
"""
import argparse
import hashlib
import json
import os
import re
import sys

VERSION = 'S47 autolock_audit 2026-10-27 v1'
NAME_RX = re.compile(r'^AUTOLOCK_(\d+)_(.+)$')
PERFT_DEFAULT = (4865609, 193690690)


def h(path, algo='sha256'):
    d = hashlib.new(algo)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            d.update(chunk)
    return d.hexdigest()


def lf_sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read().replace(b'\r\n', b'\n')).hexdigest()


def text(path):
    with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
        return f.read()


def jload(path):
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def opt(path):
    return path if path and os.path.isfile(path) else None


def hash_list(path):
    out = {}
    for line in text(path).splitlines():
        m = re.match(r'^([0-9a-fA-F]{32,64})\s+\*?(.+?)\s*$', line)
        if m:
            out[m.group(2).replace('\\', '/')] = m.group(1).lower()
    return out


def parse_bench(t):
    runs = []
    for line in t.splitlines():
        m = re.search(r'(\d+)/(\d+)/(\d+)/(\d+)/(\d+)\s*$', line.strip())
        if m and ('bench' in line.lower() or line.lower().lstrip().startswith('repeat')):
            runs.append([int(x) for x in m.groups()])
    if runs:
        return runs
    raw = [int(x) for x in re.findall(r'bench depth \d+ nodes (\d+)', t)]
    return [raw[i:i + 5] for i in range(0, len(raw) - len(raw) % 5, 5)]


def parse_prebench(t, side):
    vals = re.findall(rf'(?m)^{side} d\d+ (\d+)', t)
    return [int(v) for v in vals] if len(vals) == 5 else None


def parse_perft(t):
    p = re.search(r'perft 5 startpos:\s*(\d+)', t)
    k = re.search(r'perft 5 kiwipete:\s*(\d+)', t)
    f = re.search(r'FMA[^:\n]*:\s*(\d+)', t)
    return (int(p.group(1)) if p else None, int(k.group(1)) if k else None, int(f.group(1)) if f else None)


def uci_lines(t):
    return [' '.join(line.split()) for line in t.splitlines() if line.strip().startswith('option name')]


def verdict_of(t):
    if re.search(r'RESULT: \*\*VOID\*\*', t):
        return 'VOID'
    m = re.search(r'\*\*Verdict: ([^\r\n*]*)\*\*', t)
    return m.group(1).strip() if m else None


def tree_of(d):
    return os.path.join(d, 'source') if os.path.isdir(os.path.join(d, 'source')) else d


def lock_exe(d, lj):
    if lj and lj.get('exe') and os.path.isfile(os.path.join(d, os.path.basename(str(lj['exe'])))):
        return os.path.join(d, os.path.basename(str(lj['exe'])))
    exes = sorted(f for f in os.listdir(d) if f.lower().endswith('.exe'))
    return os.path.join(d, exes[0]) if len(exes) == 1 else None


class Audit:
    def __init__(self, a):
        self.a, self.rows, self.inputs = a, [], {}

    def row(self, cid, title, status, evidence):
        self.rows.append({'id': cid, 'check': title, 'status': status, 'evidence': evidence})

    def note_input(self, label, path):
        if path and os.path.isfile(path):
            self.inputs[label] = {'path': path, 'sha256': h(path), 'bytes': os.path.getsize(path)}
        elif path:
            self.inputs[label] = {'path': path, 'missing': True}

    def run(self):
        a = self.a
        old, new = a.old_lock, a.new_lock
        oj = jload(os.path.join(old, 'LOCK.json')) if opt(os.path.join(old, 'LOCK.json')) else None
        nj = jload(os.path.join(new, 'LOCK.json')) if opt(os.path.join(new, 'LOCK.json')) else None
        old_tag = (oj or {}).get('tag') or a.old_tag
        old_n = int((oj or {}).get('n', 0) or 0)
        gate_ri = jload(a.gate_run_info) if opt(a.gate_run_info) else None
        conf_ri = jload(a.confirm_run_info) if opt(a.confirm_run_info) else None
        gate_rec = jload(a.gate_record) if opt(a.gate_record) else None
        conf_rec = jload(a.confirm_record) if opt(a.confirm_record) else None
        for lab, p in (('old LOCK.json', os.path.join(old, 'LOCK.json')), ('new LOCK.json', os.path.join(new, 'LOCK.json')),
                       ('gate RESULT.md', a.gate_result), ('gate RUN_INFO.json', a.gate_run_info), ('confirm RESULT.md', a.confirm_result),
                       ('confirm RUN_INFO.json', a.confirm_run_info), ('gate record', a.gate_record), ('confirm record', a.confirm_record),
                       ('old hash list', a.old_hashes), ('old bench reference', a.old_ref), ('pin allow-list', a.pin_allow)):
            if p:
                self.note_input(lab, p)

        # A1 new dir
        name = os.path.basename(os.path.normpath(new))
        m = NAME_RX.match(name)
        ev, bad = [], []
        if os.path.realpath(new) == os.path.realpath(old):
            bad.append('new lock dir is the old lock dir')
        if not m:
            bad.append(f"dir name '{name}' is not AUTOLOCK_<n>_<tag>")
        else:
            n = int(m.group(1))
            ev.append(f'name n={n}, old lock {old_tag} n={old_n}')
            if n <= old_n:
                bad.append(f'n {n} not above the old lock n {old_n}')
            if nj is None:
                bad.append('new LOCK.json missing')
            else:
                if int(nj.get('n', -1)) != n or nj.get('tag') != name:
                    bad.append(f"LOCK.json n/tag {nj.get('n')}/{nj.get('tag')} != dir name")
                ptag = (nj.get('parent') or {}).get('tag')
                if old_tag and ptag != old_tag:
                    bad.append(f'LOCK.json parent.tag {ptag} != old lock {old_tag}')
                ev.append(f"LOCK.json n {nj.get('n')} tag {nj.get('tag')} parent {ptag} kind {nj.get('kind')}")
            chain, p = set(), (nj or {}).get('parent')
            while isinstance(p, dict):
                chain.add(p.get('tag'))
                p = p.get('parent')
            sib = [d for d in os.listdir(os.path.dirname(os.path.abspath(new))) if NAME_RX.match(d) and os.path.isdir(os.path.join(os.path.dirname(os.path.abspath(new)), d))]
            orphans = sorted(d for d in sib if int(NAME_RX.match(d).group(1)) < n and d not in chain)
            if orphans:
                bad.append('orphan lower-n AUTOLOCK dir(s): ' + ', '.join(orphans))
            ev.append(f'sibling AUTOLOCK dirs: {sorted(sib)}')
        self.row('A1', 'new lock in a NEW dir AUTOLOCK_<n>_<tag>, consistent LOCK.json, no orphan lower-n dir', 'FAIL' if bad else 'PASS', '; '.join(bad + ev))

        # A2 old lock unchanged
        if not opt(a.old_hashes):
            self.row('A2', 'old lock files unchanged (sha256 vs the hash list recorded before the promote)', 'MISSING', 'no --old-hashes list given / found')
        else:
            root = a.old_hashes_root or tree_of(old)
            lst = hash_list(a.old_hashes)
            changed, missing = [], []
            for rel, want in sorted(lst.items()):
                p = os.path.join(root, rel)
                if not os.path.isfile(p):
                    missing.append(rel)
                elif h(p, 'md5' if len(want) == 32 else 'sha256') != want:
                    changed.append(rel)
            exe_ev, exe_bad = 'old exe: no recorded sha256 given', False
            ox = lock_exe(old, oj)
            rec = (a.old_exe_sha or '').lower() or ((nj or {}).get('parent') or {}).get('sha256', '').lower()
            if ox and rec:
                got = h(ox)
                exe_bad = got != rec
                exe_ev = f'old exe {os.path.basename(ox)} {got} vs recorded {rec}'
            st = 'FAIL' if (changed or missing or exe_bad) else ('PASS' if lst else 'MISSING')
            self.row('A2', 'old lock files unchanged (sha256 vs the hash list recorded before the promote)', st,
                     f'{len(lst)} listed files re-hashed under {root}; changed {changed or "none"}; missing {missing or "none"}; {exe_ev}')

        # A3 net md5
        np_ = os.path.join(new, 'nnue_weights.inc')
        if not os.path.isfile(np_):
            self.row('A3', 'net md5 = the gated pack net', 'FAIL', 'new lock has no nnue_weights.inc')
        else:
            got = h(np_, 'md5')
            bad, ev = [], [f'nnue_weights.inc md5 {got}']
            if a.net_md5:
                ev.append(f'gated pack net {a.net_md5.lower()}')
                if got != a.net_md5.lower():
                    bad.append('differs from the gated pack net')
            mf = opt(os.path.join(new, 'nnue_weights.inc.md5'))
            if mf:
                rec = text(mf).split()[0].lower()
                if rec != got:
                    bad.append(f'nnue_weights.inc.md5 says {rec}')
            if nj and nj.get('net_md5') and str(nj['net_md5']).lower() != got:
                bad.append(f"LOCK.json net_md5 {nj['net_md5']}")
            self.row('A3', 'net md5 = the gated pack net', 'FAIL' if bad else ('PASS' if a.net_md5 else 'MISSING'),
                     '; '.join(ev + bad) + ('' if a.net_md5 else '; no --net-md5 (gated pack net) given'))

        # A4 exe sha
        nx = lock_exe(new, nj)
        if not nx:
            self.row('A4', 'exe sha256 = the gated exe (gate and confirm RUN_INFO)', 'FAIL', 'new lock has no single .exe')
        else:
            got = h(nx)
            bad, ev = [], [f'{os.path.basename(nx)} {got}']
            for lab, ri in (('gate', gate_ri), ('confirm', conf_ri)):
                if ri is None:
                    continue
                cs = str(((ri.get('candidate') or {}).get('sha256')) or '').lower()
                ev.append(f'{lab} RUN_INFO candidate {cs}')
                if cs != got:
                    bad.append(f'{lab} RUN_INFO candidate sha differs')
            sf = opt(nx + '.sha256')
            if sf and text(sf).split()[0].lower() != got:
                bad.append('.sha256 file differs')
            if nj and nj.get('sha256') and str(nj['sha256']).lower() != got:
                bad.append('LOCK.json sha256 differs')
            st = 'FAIL' if bad else ('PASS' if gate_ri and conf_ri else 'MISSING')
            self.row('A4', 'exe sha256 = the gated exe (gate and confirm RUN_INFO)', st, '; '.join(ev + bad) + ('' if gate_ri and conf_ri else '; gate or confirm RUN_INFO.json missing'))

        # A5 bench
        bf = a.bench or os.path.join(new, 'BENCH_REF.txt')
        runs = parse_bench(text(bf)) if opt(bf) else []
        exp = None
        if a.expected_bench:
            exp = [int(x) for x in a.expected_bench.split('/')]
        elif gate_rec and (gate_rec.get('prebench') or {}).get('cand_off'):
            exp = [int(x) for x in gate_rec['prebench']['cand_off']]
        oref = None
        orf = a.old_ref or os.path.join(old, 'BENCH_REF.txt')
        if opt(orf):
            t = text(orf)
            oref = (parse_bench(t) or [None])[0] or parse_prebench(t, 'base')
        bad, miss, ev = [], [], [f'runs {runs}']
        if len(runs) < 2:
            (miss if not runs else bad).append('bench needs two runs' if runs else f'no bench output ({bf})')
        elif any(r != runs[0] for r in runs[1:]):
            bad.append('the two runs differ (not deterministic)')
        if exp is None:
            miss.append('no expected bench (gate prebench.cand_off / --expected-bench)')
        elif runs and runs[0] != exp:
            bad.append(f'bench {runs[0]} != gated prebench {exp} (drift {[x - y for x, y in zip(runs[0], exp)]})')
        else:
            ev.append(f'= gated prebench {exp}')
        if oref is None:
            miss.append('old lock has no own bench reference (BENCH_REF.txt / --old-ref)')
        elif runs and runs[0] == oref:
            bad.append(f'bench equals the old lock bench {oref} (net not applied?)')
        else:
            ev.append(f'differs from old lock bench {oref}')
        self.row('A5', 'bench d11-d22 node-exact, run twice identical', 'FAIL' if bad else ('MISSING' if miss else 'PASS'), '; '.join(ev + bad + miss))

        # A6 perft
        pf = a.perft or os.path.join(new, 'PERFT.txt')
        want = tuple(int(x) for x in a.perft_expect.split(',')) if a.perft_expect else PERFT_DEFAULT
        if not opt(pf):
            self.row('A6', f'perft5 {want[0]} / kiwipete5 {want[1]} / FMA 0', 'MISSING', f'no perft output ({pf})')
        else:
            p5, k5, fma = parse_perft(text(pf))
            bad = [x for x in (f'perft5 {p5}' if p5 != want[0] else '', f'kiwipete5 {k5}' if k5 != want[1] else '', f'FMA {fma}' if fma != 0 else '') if x]
            self.row('A6', f'perft5 {want[0]} / kiwipete5 {want[1]} / FMA 0', 'FAIL' if bad else 'PASS', f'perft5 {p5} kiwipete5 {k5} FMA {fma}' + ('; ' + ', '.join(bad) if bad else ''))

        # A7 uci
        nu = a.uci or os.path.join(new, 'UCI_OPTIONS.txt')
        ou = a.old_uci or os.path.join(old, 'UCI_OPTIONS.txt')
        if not opt(nu) or not opt(ou):
            self.row('A7', 'uci option list equal to the old lock', 'MISSING', f"new list {'found' if opt(nu) else 'MISSING'} ({nu}); old list {'found' if opt(ou) else 'MISSING'} ({ou})")
        else:
            x, y = uci_lines(text(nu)), uci_lines(text(ou))
            diff = sorted(set(x) ^ set(y))
            self.row('A7', 'uci option list equal to the old lock', 'FAIL' if (diff or not x) else 'PASS', f'{len(x)} new / {len(y)} old option lines' + (f'; differ: {diff}' if diff else ''))

        # A8 srand / start
        def ss(ri, rec, res):
            s = (ri or {}).get('srand', (rec or {}).get('srand'))
            o = (ri or {}).get('openings_start', (rec or {}).get('openings_start'))
            if (s is None or o is None) and opt(res):
                t = text(res)
                ms, mo = re.search(r'srand (\d+)', t), re.search(r'start=(\d+)', t)
                s = s if s is not None else (int(ms.group(1)) if ms else None)
                o = o if o is not None else (int(mo.group(1)) if mo else None)
            return s, o
        gs, go = ss(gate_ri, gate_rec, a.gate_result)
        cs, co = ss(conf_ri, conf_rec, a.confirm_result)
        if None in (gs, go, cs, co):
            self.row('A8', 'confirm srand and openings start differ from the gate', 'MISSING', f'gate srand {gs} start {go}; confirm srand {cs} start {co}')
        else:
            bad = [x for x in ('confirm reuses the gate srand' if gs == cs else '', 'confirm reuses the gate openings start' if go == co else '') if x]
            self.row('A8', 'confirm srand and openings start differ from the gate', 'FAIL' if bad else 'PASS', f'gate srand {gs} start {go}; confirm srand {cs} start {co}' + ('; ' + '; '.join(bad) if bad else ''))

        # A9 verdicts
        vv = {lab: verdict_of(text(p)) if opt(p) else None for lab, p in (('gate', a.gate_result), ('confirm', a.confirm_result))}
        if None in vv.values():
            self.row('A9', 'gate and confirm verdicts H1 accepted, not VOID', 'MISSING', str(vv))
        else:
            bad = [f'{k} {v}' for k, v in vv.items() if v == 'VOID' or not v.startswith('H1 accepted')]
            self.row('A9', 'gate and confirm verdicts H1 accepted, not VOID', 'FAIL' if bad else 'PASS', str(vv))

        # A10 pins
        allow = jload(a.pin_allow) if opt(a.pin_allow) else []
        npins = os.path.join(new, 'pins')
        opins = os.path.join(old, 'pins')
        bad, ev = [], []
        if os.path.isdir(npins):
            for f in sorted(os.listdir(npins)):
                p = os.path.join(npins, f)
                if not os.path.isfile(p):
                    continue
                md = h(p, 'md5')
                same_old = os.path.isfile(os.path.join(opins, f)) and h(os.path.join(opins, f), 'md5') == md
                hit = [x for x in allow if x.get('name') == f and md.startswith(str(x.get('md5_prefix', '')).lower()) and x.get('md5_prefix')]
                if hit and hit[0].get('net_md5') and os.path.isfile(np_) and h(np_, 'md5') != str(hit[0]['net_md5']).lower():
                    bad.append(f'{f}: allow-listed for net {hit[0]["net_md5"]}, not for this lock net')
                elif same_old:
                    ev.append(f'{f} unchanged (md5 {md})')
                elif hit:
                    ev.append(f'{f} = allow-listed reviewed diff {hit[0]["md5_prefix"]}... (attached, not applied)')
                else:
                    bad.append(f'{f} md5 {md} is neither unchanged nor an allow-listed reviewed diff (edited pin?)')
        else:
            ev.append('no pins/ attachments in the new lock')
        if os.path.isdir(opins):
            for f in sorted(os.listdir(opins)):
                if os.path.isfile(os.path.join(opins, f)) and not os.path.isfile(os.path.join(npins, f)):
                    ev.append(f'old pin {f} not carried (lock-specific attachment)')
        ot, nt = os.path.join(tree_of(old), 'tests'), os.path.join(tree_of(new), 'tests')
        if os.path.isdir(ot) and os.path.isdir(nt):
            fo = {os.path.relpath(os.path.join(dp, f), ot): lf_sha(os.path.join(dp, f)) for dp, _, fs in os.walk(ot) for f in fs}
            fn = {os.path.relpath(os.path.join(dp, f), nt): lf_sha(os.path.join(dp, f)) for dp, _, fs in os.walk(nt) for f in fs}
            td = sorted(k for k in set(fo) | set(fn) if fo.get(k) != fn.get(k))
            if td:
                bad.append(f'tests/ pins differ between the old and new lock trees: {td}')
            else:
                ev.append(f'tests/ identical ({len(fo)} files)')
        else:
            ev.append('no tests/ tree in both lock dirs (pins live in the engine repo; nothing applied here)')
        self.row('A10', 'pins unchanged except allow-listed reviewed diffs (attached, not applied)', 'FAIL' if bad else 'PASS', '; '.join(bad + ev))

        # A11 CR (info)
        nn = int(m.group(1)) if m else None
        crf = os.path.join(a.cr_dir, f'CR_PASS_AUTOLOCK_{nn}.txt') if (a.cr_dir and nn is not None) else None
        self.row('A11', 'Code Review record (INFO only; this tool never writes or grants CR_PASS)', 'INFO',
                 (f'{os.path.basename(crf)} present (sha256 {h(crf)[:16]}...)' if crf and os.path.isfile(crf) else
                  f'CR_PASS_AUTOLOCK_{nn}.txt not found in {a.cr_dir}' if crf else 'no --cr-dir given') + '; CR decides, not this tool')
        st = [r['status'] for r in self.rows]
        overall = 'FAIL' if 'FAIL' in st else 'INCOMPLETE' if 'MISSING' in st else 'ALL_CHECKS_PASS'
        return overall

    def packet(self, overall):
        a = self.a
        L = [f'# AUTO-LOCK audit packet: {os.path.basename(os.path.normpath(a.new_lock))}', '',
             f'Tool: {VERSION}. Old lock: `{a.old_lock}`. New lock: `{a.new_lock}`.', '',
             f'**Overall: {overall}**. Evidence for Code Review only: this packet is NOT a CR approval and the tool never writes '
             f'CR_PASS_AUTOLOCK_<n>.txt. MISSING means the input was not supplied or not found; nothing is guessed.', '',
             '| id | check | status | evidence |', '|---|---|---|---|']
        for r in self.rows:
            L.append(f"| {r['id']} | {r['check']} | {r['status']} | {r['evidence'].replace('|', '/')} |")
        miss = [r for r in self.rows if r['status'] == 'MISSING']
        L += ['', '## Missing (flagged, not guessed)', ''] + ([f"- {r['id']}: {r['evidence']}" for r in miss] or ['- none'])
        L += ['', '## Inputs (read-only)', ''] + [f"- {k}: `{v['path']}`" + (f" sha256 {v['sha256']} ({v['bytes']} B)" if 'sha256' in v else ' MISSING') for k, v in sorted(self.inputs.items())]
        return '\n'.join(L) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--old-lock', required=True)
    ap.add_argument('--new-lock', required=True)
    ap.add_argument('--old-tag', help='old lock tag when it has no LOCK.json (e.g. h256_e12)')
    ap.add_argument('--old-hashes', help='hash list of the old lock files recorded before the promote')
    ap.add_argument('--old-hashes-root', help='root the hash-list paths are relative to (default: old/source or old)')
    ap.add_argument('--old-exe-sha', help='recorded sha256 of the old lock exe (default: new LOCK.json parent.sha256)')
    ap.add_argument('--old-ref', help="old lock's own bench reference (BENCH_REF.txt or PREBENCH 'base dNN' lines)")
    ap.add_argument('--old-uci')
    ap.add_argument('--gate-result')
    ap.add_argument('--gate-run-info')
    ap.add_argument('--confirm-result')
    ap.add_argument('--confirm-run-info')
    ap.add_argument('--gate-record', help='manifest gate record JSON (prebench.cand_off, srand, openings_start)')
    ap.add_argument('--confirm-record')
    ap.add_argument('--expected-bench', help='a/b/c/d/e override for the gated prebench')
    ap.add_argument('--net-md5', help='md5 of the gated pack net')
    ap.add_argument('--bench')
    ap.add_argument('--perft')
    ap.add_argument('--perft-expect', help='perft5,kiwipete5 (default 4865609,193690690)')
    ap.add_argument('--uci')
    ap.add_argument('--pin-allow', help='JSON list of {name, md5_prefix, net_md5?} reviewed pin diffs')
    ap.add_argument('--cr-dir')
    ap.add_argument('--out-md')
    ap.add_argument('--out-json')
    a = ap.parse_args(argv)
    for p in (a.old_lock, a.new_lock):
        if not os.path.isdir(p):
            print(f'S47 Part B: not a directory: {p}', file=sys.stderr)
            return 2
    au = Audit(a)
    overall = au.run()
    md = au.packet(overall)
    js = json.dumps({'tool': VERSION, 'overall': overall, 'checks': au.rows, 'inputs': au.inputs, 'grants_cr_approval': False}, indent=1, sort_keys=True) + '\n'
    if a.out_md:
        with open(a.out_md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(md)
    if a.out_json:
        with open(a.out_json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(js)
    sys.stdout.write(md)
    return {'FAIL': 1, 'INCOMPLETE': 3}.get(overall, 0)


if __name__ == '__main__':
    sys.exit(main())
