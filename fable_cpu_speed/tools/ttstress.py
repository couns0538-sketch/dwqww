# ttstress.py - transposition-table stress script of PREREG.md (Python standard library only).
# 60 steps; step i applies operation i mod 12 and then searches 4 positions with `go nodes 50000`:
#   0 Hash 1 | 1 Hash 2 | 2 Hash 16 | 3 Clear Hash | 4 Hash 64 | 5 ucinewgame | 6 Hash 256 | 7 Hash 1 |
#   8 Clear Hash + ucinewgame | 9 Hash 1024 (--max-hash caps it; ASan build: 256) | 10 Hash 3 |
#   11 UseNNUE false then true (skipped in a net-off run)
# Positions 2001-2240 of the frozen file, in order. Rows go to a file in the format of rows.py, so that two runs
# are compared with `rows.py cmp --planned 240`.
#   python -I -B ttstress.py --exe X --out F.tsv --mask 0x2 [--net on|off] [--max-hash 1024] [--san] [--label T]
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402

STEPS = 60
PER_STEP = 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--exe', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--mask', required=True)
    ap.add_argument('--net', choices=['on', 'off'], default='on')
    ap.add_argument('--max-hash', type=int, default=1024)
    ap.add_argument('--san', action='store_true', help='instrumented exe: sanitizer runtime on PATH, stderr scanned for reports')
    ap.add_argument('--label', default='')
    a = ap.parse_args()
    U.require_lane()
    U.disk_guard()
    mask = U.parse_mask(a.mask)
    fens = U.read_fens(2001, STEPS * PER_STEP)
    planned = len(fens)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    env = None
    if a.san:
        import san as S
        env = S.env()
    ops = ['Hash 1', 'Hash 2', 'Hash 16', 'Clear Hash', 'Hash 64', 'ucinewgame', 'Hash 256', 'Hash 1',
           'Clear Hash + ucinewgame', 'Hash %d' % min(1024, a.max_hash), 'Hash 3', 'UseNNUE false then true']
    head = U.header('TTSTRESS %s' % a.label, [os.path.abspath(__file__), U.__file__], [a.exe], [
        'corpus %s sha256 %s; positions 2001..2240' % (os.path.basename(U.CORPUS), U.hashes(U.CORPUS)[1]),
        'settings: go nodes 50000; net %s; Threads 1; start Hash default; requested mask 0x%X; operations: %s' % (a.net, mask, ' | '.join(ops)),
        'planned %d' % planned])
    f = open(a.out, 'w', encoding='ascii', newline='\n')
    f.write(''.join('# ' + x + '\n' for x in head))
    done = 0
    status, code, err = 'INCOMPLETE', None, ''
    eng = None
    ef = a.out + '.stderr.txt'
    try:
        eng = U.Engine(a.exe, mask, errfile=ef, env=env)
        f.write('# child mask read back 0x%X\n' % eng.child_mask)
        eng.uci(300)
        eng.setoption('Threads', 1)
        eng.setoption('UseNNUE', 'true' if a.net == 'on' else 'false')
        eng.isready(300)
        for step in range(STEPS):
            op = step % 12
            if op in (0, 1, 2, 4, 6, 7, 9, 10):
                eng.setoption('Hash', ops[op].split()[1])
            elif op == 3:
                eng.setoption('Clear Hash')
            elif op == 5:
                eng.send('ucinewgame')
            elif op == 8:
                eng.setoption('Clear Hash')
                eng.send('ucinewgame')
            elif op == 11 and a.net == 'on':
                eng.setoption('UseNNUE', 'false')
                eng.isready(300)
                eng.setoption('UseNNUE', 'true')
            eng.isready(600)
            for k in range(PER_STEP):
                idx = step * PER_STEP + k
                eng.send('position fen ' + fens[idx])
                d, s, n, b = eng.go('nodes 50000', 1800)
                f.write('%d\t%d\t%s\t%d\t%s\n' % (2001 + idx, d, s, n, b))
                done += 1
        code = eng.quit(600)
        status = 'COMPLETE' if code == 0 else 'INCOMPLETE'
    except Exception as e:  # noqa
        err = str(e)
        if eng is not None:
            eng.kill()
    reports = 0
    if a.san and os.path.exists(ef):
        import san as S
        reports = len(S.report_lines(open(ef, 'r', encoding='utf-8', errors='replace').read()))
        f.write('# sanitizer report lines in stderr: %d (%s)\n' % (reports, ef))
        if reports:
            status = 'INCOMPLETE'
    if err:
        f.write('# ERROR %s\n' % err)
    f.write('# completed %d of planned %d; engine exit code %s; status %s; end %s\n' % (done, planned, code, status, U.vienna_now()))
    f.close()
    print('%s: completed %d of %d, exit %s, sanitizer report lines %d, %s %s' % (os.path.basename(a.out), done, planned, code, reports, status, err))
    return 0 if status == 'COMPLETE' and done == planned else 2


if __name__ == '__main__':
    sys.exit(main())
