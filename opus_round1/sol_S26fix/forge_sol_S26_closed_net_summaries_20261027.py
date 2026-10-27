"""S26-1: one short SUMMARY_<net>.md per closed S26 first attempt, next to that net's native result JSON.

usage: python -I -B forge_sol_S26_closed_net_summaries_20261027.py build  <closed_nets dir>
       python -I -B forge_sol_S26_closed_net_summaries_20261027.py verify <closed_nets dir>
Each closed_nets/<net>/ holds forge_sol_S26_<net>_native_result_20261026.json (Sol's frozen-v3 record, byte copy;
for f019/f020 identical to his closed JSONs) and optional CI summaries (ci_v4_summary.json, ci_v5_summary.json,
ci_asan_check.json). The summary is rendered only from those files; verify() re-renders and compares bytes,
so a hand-edited number fails the check.
"""
import json
import sys
from pathlib import Path

NETS = ('B_lock', 'f019', 'f020', 'f021', 'f022', 'f023')
DEPTHS = ('11', '13', '16', '20', '22')


def _load(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else None


def _row(native):
    rows = (native.get('nets') or []) + (native.get('failed_nets') or [])
    if len(rows) != 1:
        raise ValueError('expected exactly one net row')
    return rows[0]


def verdict(row):
    """One-line verdict from the frozen-v3 record (never stronger than the record)."""
    if row.get('status') == 'PASS':
        return 'PASS (v3 qualification passed; no adoption, no Elo/speed claim)'
    return 'FAIL — ' + str(row.get('failure'))


def render(net, native_name, native, ci_v4=None, ci_v5=None, asan=None):
    r = _row(native)
    b = r.get('bench') or {}
    w = r.get('wac') or {}
    ct = r.get('ctest') or {}
    cases = ct.get('test_cases') or []
    passed = sum(1 for c in cases if not c.get('failed'))
    obs = {c['case']: c for c in (r.get('pin_observations') or {}).get('cases', [])}
    wac1 = obs.get('WAC001', {})
    fma = r.get('fma') or {}
    lines = [
        '# S26 closed net %s — %s' % (net, 'PASS' if r.get('status') == 'PASS' else 'FAIL'),
        '',
        'Source: `%s` (Sol frozen-v3 native first attempt, tool sha256 %s; byte copy). Advice only; no net adopted.'
        % (native_name, native.get('tool_sha256')),
        '',
        '| item | value |',
        '|---|---|',
        '| net | sha256 `%s`, md5 `%s` |' % (r.get('net_sha256'), r.get('net_md5')),
        '| verdict (v3) | %s |' % verdict(r),
        '| bench d11/13/16/20/22 | %s |' % ' / '.join(str(b.get(d)) for d in DEPTHS),
        '| frozen bench reference | %s |' % ('equal' if b and b == (r.get('bench_reference') or {}).get('bench') else 'DIFFERENT'),
        '| FMA (exe / NNUE object) | %s |' % ' / '.join(str(a.get('fma_count')) for a in fma.get('artifacts', [])),
        '| WAC300 @1000 ms (v3 box) | %s solved; documentary ref %s; %s |' % (w.get('solved'), w.get('reference_solved'), w.get('reference_status')),
        '| WAC001 d12 (UCI, Hash 8) | %s %s %s (documented pin %s/%s) |' % (wac1.get('bestmove'), wac1.get('score_kind'), wac1.get('score'),
                                                                           wac1.get('documented_move'), wac1.get('documented_score')),
        ('| CTest (v3) | %d/%d cases without failure; %s |' % (passed, len(cases), ct.get('status')) if cases else
         '| CTest (v3) | return code %s; check %s (no per-case list recorded; reason in the verdict line) |' % (
             ct.get('returncode'), ct.get('status'))),
    ]
    for label, s in (('CI re-run v4 (Linux)', ci_v4), ('CI re-run v5 (Linux)', ci_v5)):
        if s:
            lines.append('| %s | run %s: %s; bench %s; WAC %s solved (%s); WAC001 %s; forge_tests lines %s v3 |' % (
                label, s.get('ci_run_id'), s.get('row_status'), 'equal ref' if s.get('bench_equals_frozen_ref') else 'DIFFERENT',
                s.get('wac_solved'), s.get('wac_reference_status'), s.get('uci_WAC001_d12_Hash8'),
                'equal to' if s.get('forge_tests_diagnostics_equal_v3') else 'DIFFERENT from'))
            if s.get('row_status') != 'PASS':
                lines.append('| %s failure | %s |' % (label, s.get('row_failure')))
    if asan:
        lines.append('| ASan+UBSan (CI run %s) | %s; %s; sanitizer report files %d; bench d11 %s |' % (
            asan.get('ci_run_id'), asan.get('status'), asan.get('ctest_summary'), len(asan.get('sanitizer_report_files') or []),
            asan.get('bench_d11_asan')))
    lines += ['', 'WAC at fixed 1000 ms depends on the machine and its load; compare WAC only on one box. '
              'PIN_MISMATCH/KNOWN lines are net-specific (see ../../REPORT.md, S26-v4-2).', '']
    return '\n'.join(lines)


def _files(folder, net):
    natives = sorted(folder.glob('forge_sol_S26_%s_native_result_*.json' % net))
    if len(natives) != 1:
        raise ValueError('%s: expected one native result JSON, found %d' % (folder, len(natives)))
    return (natives[0], _load(natives[0]), _load(folder / 'ci_v4_summary.json'), _load(folder / 'ci_v5_summary.json'),
            _load(folder / 'ci_asan_check.json'))


def build(root):
    root = Path(root)
    for net in NETS:
        folder = root / net
        path, native, v4, v5, asan = _files(folder, net)
        (folder / ('SUMMARY_%s.md' % net)).write_text(render(net, path.name, native, v4, v5, asan), encoding='utf-8', newline='\n')


def verify(root):
    root = Path(root)
    problems = []
    for net in NETS:
        folder = root / net
        try:
            path, native, v4, v5, asan = _files(folder, net)
            want = render(net, path.name, native, v4, v5, asan)
            got = (folder / ('SUMMARY_%s.md' % net)).read_text(encoding='utf-8')
            if got != want:
                problems.append('%s: SUMMARY differs from its JSON sources' % net)
        except (OSError, ValueError, KeyError) as exc:
            problems.append('%s: %s' % (net, exc))
    return problems


if __name__ == '__main__':
    cmd, root = sys.argv[1], sys.argv[2]
    if cmd == 'build':
        build(root)
        print('built')
    p = verify(root)
    print('VERIFY', 'PASS' if not p else 'FAIL', p)
    raise SystemExit(0 if not p else 1)
