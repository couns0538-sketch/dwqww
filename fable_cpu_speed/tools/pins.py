# pins.py - the 13 lock pins on one exe: bench d11/13/16/20/22 with the net on and with the net off,
# perft startpos 5, kiwipete 4 and 5. PASS only when all planned pins ran and equal the expected values.
# A timeout, missing output or a non-zero exit is a failure, never "zero mismatches".
#   python -I -B pins.py --exe X --log L [--masks 0x10,0x1000,0x8] [--label T] [--flags "..."] [--quick]
#                        [--override name=value] [--timeout-scale F]
import argparse
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402

EXPECT = {
    'bench_on_d11': 312866, 'bench_on_d13': 862329, 'bench_on_d16': 3024920,
    'bench_on_d20': 12389307, 'bench_on_d22': 34048354,
    'bench_off_d11': 375354, 'bench_off_d13': 907205, 'bench_off_d16': 2448617,
    'bench_off_d20': 13573040, 'bench_off_d22': 24506465,
    'perft_startpos_5': 4865609, 'perft_kiwipete_4': 4085603, 'perft_kiwipete_5': 193690690,
}
ORDER = list(EXPECT.keys())


def lane(kind, exe, mask, names, scale, got, notes):
    eng = None
    try:
        eng = U.Engine(exe, mask)
        notes.append('lane %s: requested mask 0x%X, child mask read back 0x%X' % (kind, mask, eng.child_mask))
        eng.uci()
        if kind == 'off':
            eng.setoption('UseNNUE', 'false')
        eng.isready()
        for n in names:
            try:
                if n.startswith('bench'):
                    got[n] = eng.bench(int(n.rsplit('_d', 1)[1]), 1200 * scale)[0]
                else:
                    _, pos, d = n.split('_')
                    eng.send('position startpos' if pos == 'startpos' else 'position fen ' + U.KIWIPETE)
                    got[n] = eng.perft(int(d), 1800 * scale)[0]
            except U.EngineError as e:
                got[n] = 'ERROR ' + str(e)
                raise
        code = eng.quit()
        notes.append('lane %s: exit code %s' % (kind, code))
        if code != 0:
            for n in names:
                got[n] = 'ERROR exit code %s' % code
    except Exception as e:  # noqa
        notes.append('lane %s: FAILED: %s' % (kind, e))
        if eng is not None:
            eng.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--exe', required=True)
    ap.add_argument('--log', required=True)
    ap.add_argument('--masks', default='0x10,0x1000,0x8')
    ap.add_argument('--label', default='')
    ap.add_argument('--flags', default='')
    ap.add_argument('--quick', action='store_true', help='d11 net on, d11 net off, perft startpos 5 only (self-tests)')
    ap.add_argument('--override', action='append', default=[], help='name=value: replace one expected value (self-tests)')
    ap.add_argument('--timeout-scale', type=float, default=1.0)
    a = ap.parse_args()
    U.require_lane()
    masks = [U.parse_mask(x) for x in a.masks.split(',')]
    expect = dict(EXPECT)
    for o in a.override:
        k, v = o.split('=')
        expect[k] = int(v)
    names = ['bench_on_d11', 'bench_off_d11', 'perft_startpos_5'] if a.quick else ORDER
    groups = {'on': [n for n in names if n.startswith('bench_on')],
              'off': [n for n in names if n.startswith('bench_off')],
              'perft': [n for n in names if n.startswith('perft')]}
    L = U.header('PINS %s' % a.label, [os.path.abspath(__file__), U.__file__], [a.exe], [
        'build flags / candidate switch: %s' % (a.flags or '(lock recipe, no extra switch)'),
        'settings: built-in net; UseNNUE true for bench_on, false for bench_off; Threads default 1; bench uses its own 16 MB table',
        'expected values overridden (self-test): %s' % (a.override or 'none'),
        'planned %d' % len(names)])
    got, notes, ts = {}, [], []
    for i, kind in enumerate(('on', 'off', 'perft')):
        t = threading.Thread(target=lane, args=(kind, a.exe, masks[i % len(masks)], groups[kind], a.timeout_scale, got, notes))
        t.start()
        ts.append(t)
    for t in ts:
        t.join()
    L.extend(notes)
    done = mism = errs = 0
    for n in names:
        g = got.get(n, 'NOT RUN')
        if isinstance(g, int):
            done += 1
            ok = (g == expect[n])
            mism += 0 if ok else 1
            L.append('PIN %-18s expected %-10d got %-10d %s' % (n, expect[n], g, 'OK' if ok else 'DIFF'))
        else:
            errs += 1
            L.append('PIN %-18s expected %-10d got %s' % (n, expect[n], g))
    L.append('planned %d completed %d mismatches %d errors %d' % (len(names), done, mism, errs))
    verdict = 'PASS' if (done == len(names) and mism == 0 and errs == 0) else ('FAIL' if mism else 'INCOMPLETE')
    L.append('VERDICT PINS %s; end %s' % (verdict, U.vienna_now()))
    U.write_log(a.log, L)
    print('\n'.join(L))
    return 0 if verdict == 'PASS' else (1 if verdict == 'FAIL' else 2)


if __name__ == '__main__':
    sys.exit(main())
