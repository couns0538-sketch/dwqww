#!/usr/bin/env python3
"""make_draft.py <out.md> "<now from date>" <name>=<RESULT.json>=<control.nnue2> ... - checks of the GPU-trained v2 nets
(2026-11-04): assembles D:/o30/tmp/forge_checks_draft.md from the outputs in D:/o30/checks_gpu/<name>/ (smoke_300s.json
+ .stderr.txt + step log, uci_conformance.json + step log, depth_probe*.json + step logs): per net and check the result,
the numbers, log paths with md5, and one line "works in Forge: yes/no (why)". The engine's `id author` text is never
copied (only check names and pass/fail; details only for failed checks, without id lines). Read-only on the inputs;
writes the one markdown file (LF). Standard library."""
import glob
import hashlib
import json
import math
import os
import re
import statistics
import sys

BASE = 'D:/o30/checks_gpu'
EXE = 'D:/o30/w/v2p4_pc1/src_copy/forge_ltopgo_v2p4_pc1.exe'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def loadj(p):
    try:
        with open(p, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def readt(p):
    try:
        with open(p, encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        return ''


def fnv(s):
    m = re.search(r'fnv1a ([0-9a-f]{16})', s or '')
    return m.group(1) if m else ''


def log_facts(p):
    """clock lines, CPU busy lines, sharers and exit code of a step log"""
    t = readt(p)
    out = []
    for l in t.splitlines():
        if (l.startswith(('step.sh start', '--- run start', '--- run end', 'window open', 'waiting', 'step.sh:'))
                or l.startswith('cpu') or l.startswith('sharer:') or 'forge-v2-bullet' in l and 'on_cpu0=True' in l):
            out.append(l.strip())
    return out


def fileline(p):
    return f'`{p}` md5 {md5(p)}' if os.path.isfile(p) else f'`{p}` (missing)'


def main():
    out_md, now = sys.argv[1], sys.argv[2]
    nets = [a.split('=', 2) for a in sys.argv[3:]]
    L = []
    L.append('# Forge checks of the GPU-trained v2 nets - draft')
    L.append('')
    L.append(f'Written {now} (PC clock = Vienna, from `date`). Exe (gate exe) `{EXE}` sha256 '
             f'{hashlib.sha256(open(EXE, "rb").read()).hexdigest()}.')
    L.append('All runs at Idle on CPU 0 only (mask 0x1 through `D:/a14/tools/opus_lowrun.py`; every tool pins itself to the same '
             'mask), one at a time, between 13:05 and 14:05; no process of anybody else was touched. Scripts: '
             '`D:/o30/checks_gpu/scripts/` (step.sh, chain.sh, depth_probe_ab.py, bullet_cpu0.ps1, cpu_busy.ps1, net_ready.py, '
             'make_draft.py).')
    L.append('')
    L.append('Checks per net: 1. smoke (`tools/smoke2m.py`, 300 s self-play at a real clock 2000+20 ms, Threads 2, Hash 16, '
             'OwnBook false, EvalFileV2 = the net - as `a/net_final_checks.sh` step 1, but both engine threads on the one CPU 0); '
             '2. UCI conformance with the net loaded (`tools/uci_conformance_o30.py`, Threads 2); 3. game-position speed '
             '(`scripts/depth_probe_ab.py` = `a/depth_probe_o30.py` plus `--opt-a` and a load check): the net (B) vs its control '
             '(A, the lock function as v2 replicas with the same bucket layout) on the same exe, 200 positions from the match PGN '
             '`D:/o30/control/lockkb4_v2p4/lockkb4_v2p4.pgn`, `go movetime 200`, Threads 1, Hash 16, 2 rounds A-B / B-A; the '
             'nodes-per-second ratio B / A is the geometric mean over positions with its 95 % CI; the depth difference is depth '
             'at equal time (not a strength claim). No Elo claim anywhere: these are play / conformance / speed checks only.')
    L.append('')
    verdicts = []
    for name, rj, control in nets:
        d = f'{BASE}/{name}'
        r = loadj(rj) or {}
        net = r.get('net', '').replace('\\', '/')
        exp_fnv = fnv(r.get('info', ''))
        L.append(f'## {name}')
        L.append('')
        L.append(f'- net `{net}` sha256 {r.get("sha256", "n/a")} md5 {r.get("md5", "n/a")}, fnv1a {exp_fnv or "n/a"}, '
                 f'package RESULT.json all_checks_passed = {r.get("all_checks_passed")!r}; control `{control}` md5 '
                 f'{md5(control) if os.path.isfile(control) else "n/a"}')
        why = []
        # 1. smoke
        sj = loadj(f'{d}/smoke_300s.json')
        serr = readt(f'{d}/smoke_300s.stderr.txt').strip()
        if sj:
            smoke_ok = sj.get('verdict') == 'PASS'
            L.append(f'- **1. smoke 300 s: {sj.get("verdict")}** - games {sj.get("games")} (finished {sj.get("finished_games")}), '
                     f'plies {sj.get("plies")}, illegal {sj.get("illegal")}, crashes {sj.get("crashes")}, hangs {sj.get("hangs")}, '
                     f'time losses {sj.get("time_losses")}, overruns {sj.get("overruns")} (within the 1000 ms margin, reported only), '
                     f'option errors {sj.get("option_errors")}, stderr {"empty" if not serr else "NOT empty: " + serr.splitlines()[0][:120]}; '
                     f'Threads {sj.get("threads")}, Hash {sj.get("hash")}, tc {sj.get("tc")}, mask {sj.get("mask")}, idle {sj.get("idle")}')
            if not smoke_ok:
                why.append('smoke FAIL')
            for ev in (sj.get('events') or [])[:5]:
                L.append(f'  - event: {json.dumps(ev)[:300]}')
        else:
            smoke_ok = False
            why.append('smoke not run / no result')
            L.append('- **1. smoke 300 s: NOT RUN / no result**')
        for l in log_facts(f'{d}/smoke_300s.txt'):
            L.append(f'  - {l}')
        L.append(f'  - files: {fileline(f"{d}/smoke_300s.txt")}; {fileline(f"{d}/smoke_300s.json")}; '
                 f'{fileline(f"{d}/smoke_300s.stderr.txt")}')
        # 2. conformance
        cj = loadj(f'{d}/uci_conformance.json')
        if cj:
            checks = cj.get('checks', [])
            n_ok = sum(1 for c in checks if c.get('ok'))
            conf_ok = bool(cj.get('pass')) and n_ok == len(checks)
            load_detail = ''
            for c in checks:
                if c.get('check', '').startswith('info string contains'):
                    load_detail = c.get('detail', '')
            L.append(f'- **2. UCI conformance with the net loaded: {"PASS" if conf_ok else "FAIL"}** - {n_ok} / {len(checks)} checks; '
                     f'net load line fnv1a {fnv(load_detail) or "n/a"} ' +
                     ('(= the package)' if exp_fnv and fnv(load_detail) == exp_fnv else '(DIFFERENT from the package!)'))
            if exp_fnv and fnv(load_detail) != exp_fnv:
                why.append('conformance loaded a different net')
            for c in checks:
                if not c.get('ok'):
                    det = ' '.join(l for l in c.get('detail', '').split(';') if 'id author' not in l)[:200]
                    L.append(f'  - FAIL: {c.get("check")}: {det}')
                    why.append(f'conformance check failed: {c.get("check")}')
            obs = cj.get('observations') or []
            for o in obs:
                L.append(f'  - observation (not counted): {o.get("observation")}: {"conform" if o.get("uci_conform") else "NOT conform"}')
        else:
            conf_ok = False
            why.append('conformance not run / no result')
            L.append('- **2. UCI conformance: NOT RUN / no result**')
        for l in log_facts(f'{d}/uci_conformance.txt'):
            L.append(f'  - {l}')
        L.append(f'  - files: {fileline(f"{d}/uci_conformance.txt")}; {fileline(f"{d}/uci_conformance.json")}')
        # 3. probe(s)
        probes = sorted(p.replace('\\', '/') for p in glob.glob(f'{d}/depth_probe*.json'))
        probe_ok = False
        runs = []
        if probes:
            for pj in probes:
                p = loadj(pj) or {}
                tag = os.path.basename(pj)[len('depth_probe'):-len('.json')].strip('_') or 'main'
                runs.append((tag, p))
                la = [x for r_ in p.get('loads', {}).get('A', []) for x in r_.get('load', [])]
                lb = [x for r_ in p.get('loads', {}).get('B', []) for x in r_.get('load', [])]
                fa = {fnv(x) for x in la}
                fb = {fnv(x) for x in lb}
                ci = p.get('nps_ratio_ci95', [0, 0])
                b_ok = bool(fb) and fb == {exp_fnv} if exp_fnv else bool(fb)
                a_path_ok = bool(la) and all(control.lower() in x.lower() for x in la)
                b_path_ok = bool(lb) and all(net.lower() in x.lower() for x in lb)
                if tag == 'main':
                    probe_ok = b_ok and a_path_ok and b_path_ok
                L.append(f'- **3. game-position speed ({tag}): nps B / A = {p.get("nps_ratio_b_over_a", 0):.4f} '
                         f'(95 % CI {ci[0]:.4f} .. {ci[1]:.4f})** over {p.get("n")} positions x {p.get("rounds")} rounds, movetime '
                         f'{p.get("movetime")} ms; geometric mean nps A {p.get("geo_mean_nps_a", 0):.0f}, B {p.get("geo_mean_nps_b", 0):.0f}; '
                         f'depth at equal time A {p.get("mean_depth_a", 0):.3f}, B {p.get("mean_depth_b", 0):.3f}, B - A '
                         f'{p.get("depth_b_minus_a", 0):+.3f} (SE {p.get("depth_se", 0):.3f}); {p.get("seconds")} s; '
                         f'loads: A (control) fnv1a {", ".join(sorted(fa)) or "n/a"} x{len(la)} '
                         + ('(the control file)' if a_path_ok else '(NOT the control file!)')
                         + f', B (net) fnv1a {", ".join(sorted(fb)) or "n/a"} x{len(lb)} '
                         + ('(= the package)' if b_ok and b_path_ok else '(NOT the packaged net!)'))
                log = pj[:-len('.json')] + '.txt'
                for l in log_facts(log):
                    L.append(f'  - {l}')
                L.append(f'  - files: {fileline(log)}; {fileline(pj)}')
            # pooled over the runs with the same movetime: the same positions each run, paired per position and run
            groups = {}
            for tag, p in runs:
                pp = p.get('per_position', {})
                if pp.get('log_nps_a') and pp.get('log_nps_b'):
                    lr = [y - x for x, y in zip(pp['log_nps_a'], pp['log_nps_b'])]
                    groups.setdefault(p.get('movetime'), []).append((tag, lr, p.get('nps_ratio_b_over_a', 0)))
            for mt, g in sorted(groups.items(), key=lambda kv: (kv[0] is None, kv[0] or 0)):
                if len(g) < 2:
                    continue
                allv = [v for _, lr, _ in g for v in lr]
                m = statistics.mean(allv)
                se = statistics.stdev(allv) / len(allv) ** 0.5
                ratios = [r for _, _, r in g]
                L.append(f'- **pooled speed at movetime {mt} ms over {len(g)} runs ({", ".join(t for t, _, _ in g)}): nps B / A = '
                         f'{math.exp(m):.4f} (95 % CI {math.exp(m - 1.96 * se):.4f} .. {math.exp(m + 1.96 * se):.4f}; '
                         f'{len(allv)} paired position-runs, the same positions in every run); single-run ratios '
                         f'{min(ratios):.4f} .. {max(ratios):.4f}**')
            if not probe_ok:
                why.append('speed probe: main run missing or the net was not the packaged one')
        else:
            L.append('- **3. game-position speed: NOT RUN / no result**')
            why.append('speed probe not run / no result')
            for l in log_facts(f'{d}/depth_probe.txt'):
                L.append(f'  - {l}')
        dry = f'{d}/probe_dryrun.txt'
        if os.path.isfile(dry):
            L.append(f'  - probe dry run (positions parsed): {fileline(dry)}')
        works = smoke_ok and conf_ok and probe_ok
        missing = [w for w in why if 'not run' in w or 'missing' in w]
        reason = ('smoke PASS, UCI conformance PASS with the packaged net loaded, speed probe ran with the packaged net loaded'
                  if works else ('not shown: ' if missing and len(missing) == len(why) else '') + '; '.join(why))
        L.append(f'- **works in Forge: {"yes" if works else "no"} ({reason})**')
        L.append('')
        verdicts.append((name, works, reason))
    L.append('## Summary')
    L.append('')
    for name, works, reason in verdicts:
        L.append(f'- {name}: works in Forge: {"yes" if works else "no"} ({reason})')
    L.append('')
    with open(out_md, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    print(f'wrote {out_md} md5 {md5(out_md)}')


if __name__ == '__main__':
    main()
