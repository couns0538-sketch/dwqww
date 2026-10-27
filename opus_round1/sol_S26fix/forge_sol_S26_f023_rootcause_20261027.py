"""S26-v4-2: root cause of f023's PIN_MISMATCH (documented 661 vs actual 620), from committed evidence only.

usage: python -I -B forge_sol_S26_f023_rootcause_20261027.py <job_dir> <B tests.cpp> > logs/f023_pin_rootcause.json
Reads: closed_nets/<net>/ (Sol's v3 records + CI summaries), evidence/ci/<run>/ (CI receipts) and the base-B
tests.cpp (sha256 55334ba9..., rebuilt by ci/make_base_B.sh). Expectations are not edited anywhere.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

NETS = ('B_lock', 'f019', 'f020', 'f021', 'f022', 'f023')
PIN = re.compile(r'^PIN_MISMATCH: WAC 001 documented (\S+)/(\d+)/d(\d+)/PV=\S+, observed (\S+)/(-?\d+)/d(\d+)/PV=(\S+);', re.M)


def main():
    job, tests = Path(sys.argv[1]), Path(sys.argv[2])
    src = tests.read_text(encoding='utf-8')
    lines = src.splitlines()
    start = next(i for i, l in enumerate(lines) if 'constexpr std::string_view documented_wac_move' in l)
    end = next(i for i in range(start, len(lines)) if 're-record Job C pins' in lines[i])
    obs = {}
    for net in NETS:
        folder = job / 'closed_nets' / net
        native = json.loads(next(folder.glob('forge_sol_S26_%s_native_result_*.json' % net)).read_text(encoding='utf-8'))
        row = ((native.get('nets') or []) + (native.get('failed_nets') or []))[0]
        w = {c['case']: c for c in row['pin_observations']['cases']}['WAC001']
        rec = {'v3_uci_Hash8': '%s %s %s' % (w['bestmove'], w['score_kind'], w['score']), 'v3_status': row['status'],
               'v3_failure': row.get('failure')}
        for kind in ('v4', 'v5'):
            p = folder / ('ci_%s_summary.json' % kind)
            if p.is_file():
                s = json.loads(p.read_text(encoding='utf-8'))
                rec['ci_%s_uci_Hash8' % kind] = s.get('uci_WAC001_d12_Hash8')
                rec['ci_%s_pin_lines' % kind] = [l for l in (s.get('forge_tests_diagnostics') or []) if l.startswith('PIN_MISMATCH')]
                rec['ci_%s_failure' % kind] = s.get('row_failure')
        obs[net] = rec
    asan = {}
    for run in sorted(p.name for p in (job / 'evidence' / 'ci').iterdir() if p.is_dir()):
        log = job / 'evidence' / 'ci' / run / 's26fix-asan-f023' / 'ctest_asan.log'
        xml = job / 'evidence' / 'ci' / run / 's26fix-asan-f023' / 'ctest_asan.xml'
        text = (log.read_text(encoding='utf-8', errors='replace') if log.is_file() else '') + \
               (xml.read_text(encoding='utf-8', errors='replace') if xml.is_file() else '')
        m = PIN.search(text.replace('&gt;', '>'))
        if m:
            asan[run] = {'documented': '%s/%s/d%s' % m.group(1, 2, 3), 'observed': '%s/%s/d%s' % m.group(4, 5, 6)}
    f023 = obs['f023']
    result = {
        'schema': 'opus_sol_S26fix_f023_pin_rootcause_v1',
        'tests_cpp_sha256': hashlib.sha256(tests.read_bytes()).hexdigest(),
        'pin_source_lines': '%d-%d' % (start + 1, end + 1),
        'pin_source': lines[start:end + 1],
        'documented_value_origin': 'h256_e12 lock net (74c4009d...) WAC 001 at d12 = f6h5 661 (B_lock row below; '
                                   'lock archive 4_tests/FORGE_KNOWN_TEST_FAILURES.md row fc_nnue_h256_e12_ep12_ep10base: '
                                   '"WAC 001 x2 with score 661")',
        'observations': obs,
        'asan_forge_tests_pin_lines': asan,
        'conclusion': [
            'The documented WAC 001 outcome f6h5/661/d12 is the h256_e12 lock net\'s own observation (B_lock: f6h5 cp 661).',
            'tests.cpp accepts the 6.4.24 expectation (g3g6 mate) or exactly the documented horizon outcome; any other '
            'failing outcome prints PIN_MISMATCH and keeps the two ordinary FAIL lines.',
            'f019-f022 find the mate at d12 (g3g6 mate 2), so the pin is never consulted for them.',
            'f023 is the only candidate that, like the lock, plays the horizon move f6h5 at d12, but with its own '
            'evaluation: 620 cp in every run (v3, CI v4 x2, CI v5, ASan build, UCI Hash 8).',
            'Root cause: a net-specific pin applied to a different net. Not a tool, engine or flakiness defect. '
            'Remedy (proposal only, not applied): a REVIEWED per-net pin entry for f023 (allowlist pins with exact_lines) '
            'or re-recorded pins if f023 ever became the lock; v4/v5 already wrote the UNREVIEWED 661 -> 620 proposal.'],
        'consistent': all(v == 'f6h5 cp 620' for k, v in f023.items() if k.endswith('Hash8')) and
                      all(a['observed'] == 'f6h5/620/d12' for a in asan.values()),
    }
    print(json.dumps(result, indent=1, sort_keys=True))
    return 0 if result['consistent'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
