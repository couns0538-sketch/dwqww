# selftest_checkers.py - every checker must reject a deliberately bad fixture before its PASS is trusted.
# Cases: pins.py (control, wrong expected value, no output, timeout, fake engine control, fake engine with exit 3)
#        rows.py cmp (control, one altered row, file cut off, trailer says INCOMPLETE).
#   python -I -B selftest_checkers.py --log L --mask 0x10
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(os.path.dirname(HERE), 'tests')
WORK = U.JOB + r'\out\selftest'
PY = sys.executable


def run(args):
    p = U.spawn([PY, '-I', '-B'] + args, U.self_affinity(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.communicate()[0].decode('ascii', 'replace')
    verdict = [l for l in out.splitlines() if l.startswith('VERDICT')]
    return p.returncode, (verdict[-1] if verdict else '(no verdict line)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', required=True)
    ap.add_argument('--mask', default='0x10')
    a = ap.parse_args()
    U.require_lane()
    os.makedirs(WORK, exist_ok=True)
    m = a.mask
    pins = os.path.join(HERE, 'pins.py')
    rows = os.path.join(HERE, 'rows.py')
    cases = []

    def pin_case(name, want, exe, extra):
        cases.append((name, want, [pins, '--exe', exe, '--quick', '--masks', m, '--label', 'selftest_' + name,
                                   '--log', os.path.join(WORK, 'pins_%s.log' % name)] + extra))

    pin_case('pins_control_lock', 0, U.LOCK_EXE, [])
    pin_case('pins_wrong_expected_value', 1, U.LOCK_EXE, ['--override', 'bench_on_d11=312867'])
    pin_case('pins_no_output', 2, r'C:\Windows\System32\hostname.exe', [])
    pin_case('pins_timeout', 2, U.LOCK_EXE, ['--timeout-scale', '0.000001'])
    pin_case('pins_fake_engine_control', 0, os.path.join(TESTS, 'fake_ok.cmd'), [])
    pin_case('pins_fake_engine_exit3', 2, os.path.join(TESTS, 'fake_exit3.cmd'), [])

    src = U.JOB + r'\out\rows\det_cold_on_1.tsv'
    lines = open(src, 'r', encoding='ascii').read().split('\n')
    data_idx = [i for i, l in enumerate(lines) if l and not l.startswith('#')]
    good = os.path.join(WORK, 'rows_good_copy.tsv')
    open(good, 'w', encoding='ascii', newline='\n').write('\n'.join(lines))
    alt = list(lines)
    p = alt[data_idx[1000]].split('\t')
    p[3] = str(int(p[3]) + 1)                                   # one node count off by one
    alt[data_idx[1000]] = '\t'.join(p)
    f_alt = os.path.join(WORK, 'rows_one_altered.tsv')
    open(f_alt, 'w', encoding='ascii', newline='\n').write('\n'.join(alt))
    f_cut = os.path.join(WORK, 'rows_cut_off.tsv')
    open(f_cut, 'w', encoding='ascii', newline='\n').write('\n'.join(lines[:data_idx[1500]]) + '\n')
    f_inc = os.path.join(WORK, 'rows_trailer_incomplete.tsv')
    open(f_inc, 'w', encoding='ascii', newline='\n').write('\n'.join(
        l.replace('status COMPLETE', 'status INCOMPLETE') if l.startswith('# completed') else l for l in lines))
    for name, want, b in (('rowcmp_control', 0, good), ('rowcmp_one_altered_row', 1, f_alt),
                          ('rowcmp_file_cut_off', 2, f_cut), ('rowcmp_trailer_incomplete', 2, f_inc)):
        cases.append((name, want, [rows, 'cmp', '--a', src, '--b', b, '--planned', '2000', '--label', 'selftest_' + name,
                                   '--log', os.path.join(WORK, '%s.log' % name)]))

    L = U.header('SELFTEST of checkers (exit code 0 = PASS, 1 = FAIL, 2 = INCOMPLETE)',
                 [os.path.abspath(__file__), pins, rows, U.__file__], [U.LOCK_EXE], ['planned %d cases' % len(cases)])
    ok = 0
    for name, want, args in cases:
        code, verdict = run(args)
        good_case = (code == want)
        ok += 1 if good_case else 0
        L.append('%-32s expected exit %d got %d  %s  | %s' % (name, want, code, 'AS EXPECTED' if good_case else 'UNEXPECTED', verdict))
    L.append('planned %d completed %d as expected %d' % (len(cases), len(cases), ok))
    L.append('VERDICT SELFTEST %s; end %s' % ('PASS' if ok == len(cases) else 'FAIL', U.vienna_now()))
    U.write_log(a.log, L)
    print('\n'.join(L))
    return 0 if ok == len(cases) else 1


if __name__ == '__main__':
    sys.exit(main())
