"""Fresh read-only gate: any visible reference beneath a v1 root blocks that root.

This supplements the frozen proposal generator's exact-file reference check.
It performs no retirement. Proc denials remain explicit, never global absence.
"""
from pathlib import Path
import argparse
import collections
import datetime
import hashlib
import json
import os

S08 = Path('/workspace/forge-pack24-20261026/S08')
BUILDS = tuple(S08 / n / 'build' for n in (
    'forge_sol_S08_ASAN_window1_20261026',
    'forge_sol_S08_ON_build_window1_20261026',
    'forge_sol_S08_OFF_build_window1_20261026'))


def affected_build(target):
    target = target.removesuffix(' (deleted)')
    if not target.startswith('/'):
        return None
    p = Path(os.path.normpath(target))
    for root in BUILDS:
        if p == root or p.is_relative_to(root):
            return str(root)
    return None


def snapshot_proc(proc_root=Path('/proc')):
    references, denied = [], collections.Counter()
    checked = 0
    for p in Path(proc_root).iterdir():
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        checked += 1
        try:
            status = (p / 'status').read_text()
            cmd = (p / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
        except OSError:
            status, cmd = 'UNAVAILABLE', 'UNAVAILABLE'
            denied['status_or_cmdline'] += 1
        state = next((l for l in status.splitlines() if l.startswith('State:')), 'UNAVAILABLE')
        try:
            fds = list((p / 'fd').iterdir())
        except OSError:
            denied['fd_directories'] += 1
            fds = []
        for kind, link in [('cwd', p / 'cwd'), ('exe', p / 'exe'), *[('fd', f) for f in fds]]:
            try:
                target = os.readlink(link)
            except OSError:
                denied[kind + '_links'] += 1
                continue
            root = affected_build(target)
            if root:
                references.append({'pid': int(p.name), 'kind': kind, 'link': str(link),
                    'target': target, 'blocked_build_root': root, 'state': state, 'cmdline': cmd[:1000]})
        try:
            for line in (p / 'maps').read_text().splitlines():
                fields = line.split(maxsplit=5)
                if len(fields) == 6:
                    root = affected_build(fields[5])
                    if root:
                        references.append({'pid': int(p.name), 'kind': 'maps', 'target': fields[5],
                            'blocked_build_root': root, 'state': state, 'cmdline': cmd[:1000]})
        except OSError:
            denied['maps'] += 1
    return {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'allowed_build_roots': [str(b) for b in BUILDS], 'processes_inspected': checked,
        'references': references, 'blocked_build_roots': sorted({r['blocked_build_root'] for r in references}),
        'unreadable': dict(denied), 'no_visible_selected_root_references': not references,
        'qualification': 'Any visible cwd/exe/fd/map reference at or beneath an exact selected v1 root blocks ALL its cache groups, regardless of command name/text. Unreadable proc entries limit global absence; root must also affirm exact closed leases immediately before retirement.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    result = snapshot_proc()
    result['source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with args.out.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps(result, sort_keys=True))
    return 0 if result['no_visible_selected_root_references'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
