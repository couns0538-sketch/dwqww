"""Per-net ASan/UBSan verdict for run_pernet_asan.sh (S26-v4-3).

PASS requires: no non-empty sanitizer log file and no sanitizer text in the ctest log/junit or bench stderr;
a ctest summary line; every test in the junit ran; failing tests are a subset of {forge_tests}; the forge_tests
FAIL/KNOWN_FAILURE/PIN_MISMATCH lines equal Sol's Release (v3) lines for this net; bench d11 equals the frozen
reference. The function check() is importable for the unit tests.
"""
import argparse
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

SANITIZER = re.compile(r'(runtime error:|ERROR: AddressSanitizer|ERROR: LeakSanitizer|SUMMARY: (?:Address|Undefined|Leak)Sanitizer)')
DIAG = re.compile(r'^(?:FAIL:|KNOWN_FAILURE:|PIN_MISMATCH:).*$', re.M)
BENCH = re.compile(r'^info string bench depth (\d+) nodes (\d+) ', re.M)


def check(out, expected):
    problems = []
    logdir = os.path.join(out, 'sanitizer_logs')
    reports = sorted(n for n in os.listdir(logdir) if os.path.getsize(os.path.join(logdir, n)) > 0) if os.path.isdir(logdir) else []
    if reports:
        problems.append('sanitizer report files: ' + ', '.join(reports))
    texts = {}
    for name in ('ctest_asan.log', 'ctest_asan.xml', 'bench11_asan.stderr'):
        p = os.path.join(out, name)
        texts[name] = open(p, encoding='utf-8', errors='replace').read() if os.path.isfile(p) else None
        if texts[name] is not None and SANITIZER.search(texts[name]):
            problems.append('sanitizer text in ' + name)
    log = texts['ctest_asan.log'] or ''
    summary = re.search(r'^.*tests passed.*$', log, re.M)
    if not summary:
        problems.append('no ctest summary line')
    cases, failing, lines = [], [], None
    if texts['ctest_asan.xml']:
        root = ET.fromstring(texts['ctest_asan.xml'])
        for case in root.iter('testcase'):
            name = case.attrib.get('name')
            cases.append(name)
            # CTest JUnit: status="run" (passed), "fail" (ran and failed); anything else did not run.
            if case.attrib.get('status', 'run') not in ('run', 'fail'):
                problems.append('test not run: %s' % name)
            if case.find('failure') is not None or case.find('error') is not None:
                failing.append(name)
            if name == 'forge_tests':
                text = '\n'.join(''.join(i.itertext()) for i in case if i.tag in ('failure', 'error', 'system-out', 'system-err'))
                lines = sorted(set(html.unescape(m.group(0).strip()) for m in DIAG.finditer(text)))
    else:
        problems.append('no junit')
    if not cases:
        problems.append('no test cases')
    if any(n != 'forge_tests' for n in failing):
        problems.append('unexpected failing tests: ' + ', '.join(n for n in failing if n != 'forge_tests'))
    if lines is None:
        problems.append('forge_tests missing from junit')
    elif lines != expected['forge_tests_diagnostics']:
        problems.append('forge_tests diagnostics differ from the Release v3 lines for this net')
    bench_text = ''
    p = os.path.join(out, 'bench11_asan.txt')
    if os.path.isfile(p):
        bench_text = open(p, encoding='utf-8', errors='replace').read()
    m = BENCH.search(bench_text)
    d11 = int(m.group(2)) if m and m.group(1) == '11' else None
    if d11 != expected['bench_ref']['11']:
        problems.append('bench d11 %s != frozen ref %s' % (d11, expected['bench_ref']['11']))
    return {'status': 'PASS' if not problems else 'FAIL', 'problems': problems,
            'ctest_summary': summary.group(0).strip() if summary else None, 'tests': len(cases),
            'failing_tests': failing, 'forge_tests_diagnostics': lines,
            'expected_forge_tests_diagnostics': expected['forge_tests_diagnostics'],
            'bench_d11_asan': d11, 'bench_d11_ref': expected['bench_ref']['11'], 'sanitizer_report_files': reports}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--net', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--expected', required=True)
    a = p.parse_args(argv)
    expected = json.load(open(a.expected, encoding='utf-8'))['nets'][a.net]
    result = dict(check(a.out, expected), net=a.net, net_sha256=expected['net_sha256'])
    print(json.dumps(result, indent=1, sort_keys=True))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
