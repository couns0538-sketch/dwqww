"""Summarize one CI v4 re-run and compare it with Sol's frozen-v3 first attempt for the same net.

usage: summarize_v4.py <net_id> <out_dir containing v4_out/result.json> <expected_v3_diagnostics.json>
Prints one JSON object (also written to <out_dir>/summary.json by the caller via tee).
"""
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

DIAG = re.compile(r'^(?:FAIL:|KNOWN_FAILURE:|PIN_MISMATCH:).*$', re.M)


def forge_tests_lines(junit):
    root = ET.parse(junit).getroot()
    for case in root.iter('testcase'):
        if case.attrib.get('name') == 'forge_tests':
            text = '\n'.join(''.join(item.itertext()) for item in case
                             if item.tag in ('failure', 'error', 'system-out', 'system-err'))
            return sorted(set(html.unescape(m.group(0).strip()) for m in DIAG.finditer(text)))
    return None


def main():
    net_id, out, expected_path = sys.argv[1], sys.argv[2], sys.argv[3]
    expected = json.load(open(expected_path, encoding='utf-8'))['nets'][net_id]
    path = os.path.join(out, 'v4_out', 'result.json')
    summary = {'net': net_id, 'net_sha256_expected': expected['net_sha256'], 'v4_result_present': os.path.isfile(path)}
    if not summary['v4_result_present']:
        print(json.dumps(summary, indent=1, sort_keys=True))
        return 0
    d = json.load(open(path, encoding='utf-8'))
    rows = (d.get('nets') or []) + (d.get('failed_nets') or [])
    summary.update(v4_status=d.get('status'), v4_failure=d.get('failure'), tool_sha256=d.get('tool_sha256'),
                   evidence_kind=d.get('evidence_kind'), engine_execution=d.get('engine_execution'),
                   resource_lease=d.get('resource_lease'))
    if not rows:
        print(json.dumps(summary, indent=1, sort_keys=True))
        return 0
    r = rows[0]
    bench = r.get('bench')
    wac = r.get('wac') or {}
    obs = {c['case']: c for c in (r.get('pin_observations') or {}).get('cases', [])}
    w = obs.get('WAC001', {})
    job = os.path.join(out, 'v4_out', os.path.basename(r.get('job', '')))
    junit = os.path.join(job, 'ctest.xml')
    lines = forge_tests_lines(junit) if os.path.isfile(junit) else None
    summary.update(
        net_sha256=r.get('net_sha256'), net_md5=r.get('net_md5'), row_status=r.get('status'), row_failure=r.get('failure'),
        compiler=(r.get('compiler') or {}).get('version_stdout', '').strip(),
        translation_units=(r.get('recipe_before') or {}).get('translation_units'),
        engine_sha256=(r.get('binary_sha256_before') or {}),
        bench=bench, bench_equals_frozen_ref=(bench == {k: v for k, v in expected['bench_ref'].items()}) if bench else None,
        fma=(r.get('fma') or {}).get('fma_count'),
        wac_solved=wac.get('solved'), wac_reference=wac.get('reference_solved'), wac_reference_status=wac.get('reference_status'),
        uci_WAC001_d12_Hash8=('%s %s %s' % (w.get('bestmove'), w.get('score_kind'), w.get('score'))) if w else None,
        uci_WAC001_equals_v3=(('%s %s %s' % (w.get('bestmove'), w.get('score_kind'), w.get('score'))) == expected['uci_WAC001_d12_Hash8']) if w else None,
        ctest_status=(r.get('ctest') or {}).get('status'),
        forge_tests_diagnostics=lines,
        forge_tests_diagnostics_equal_v3=(lines == expected['forge_tests_diagnostics']) if lines is not None else None,
        v3_status=expected['v3_status'], v3_failure=expected['v3_failure'])
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
