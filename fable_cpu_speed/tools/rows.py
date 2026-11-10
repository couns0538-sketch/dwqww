# rows.py - fixed-limit search rows of one exe over a slice of the frozen position file, and their comparison.
# A row is: position index, depth, score, nodes, best move.
#   run: python -I -B rows.py run --exe X --out F.tsv --mask 0x2 [--first 1] [--count 2000] [--limit "depth 13"]
#                    [--policy cold|warm|reset] [--net on|off] [--hash 16] [--threads 1] [--label T]
#        cold  = ucinewgame + isready before every position
#        warm  = one ucinewgame at the start, then no reset
#        reset = every position searched twice with ucinewgame between; second rows go to F.second.tsv
#   cmp: python -I -B rows.py cmp --a A.tsv --b B.tsv --planned N --log L [--label T]
# A run that times out, loses the engine or ends with a non-zero exit code is marked INCOMPLETE in its trailer,
# and cmp refuses to call such a file complete.
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402


def run(a):
    U.require_lane()
    U.disk_guard()
    mask = U.parse_mask(a.mask)
    fens = U.read_fens(a.first, a.count)
    planned = len(fens)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    out2 = a.out[:-4] + '.second.tsv' if a.policy == 'reset' else None
    head = U.header('ROWS %s' % a.label, [os.path.abspath(__file__), U.__file__], [a.exe], [
        'corpus %s sha256 %s; positions %d..%d' % (os.path.basename(U.CORPUS), U.hashes(U.CORPUS)[1], a.first, a.first + planned - 1),
        'settings: go %s; policy %s; net %s; Hash %d; Threads %d; requested mask 0x%X' % (a.limit, a.policy, a.net, a.hash, a.threads, mask),
        'planned %d' % planned])
    files = [open(a.out, 'w', encoding='ascii', newline='\n')]
    if out2:
        files.append(open(out2, 'w', encoding='ascii', newline='\n'))
    for f in files:
        f.write(''.join('# ' + x + '\n' for x in head))
    done = 0
    status, code, err = 'INCOMPLETE', None, ''
    eng = None
    try:
        eng = U.Engine(a.exe, mask, errfile=a.out + '.stderr.txt')
        for f in files:
            f.write('# child mask read back 0x%X\n' % eng.child_mask)
        eng.uci()
        eng.setoption('Threads', a.threads)
        eng.setoption('Hash', a.hash)
        eng.setoption('UseNNUE', 'true' if a.net == 'on' else 'false')
        eng.isready()
        if a.policy == 'warm':
            eng.send('ucinewgame')
            eng.isready()
        for i, fen in enumerate(fens):
            idx = a.first + i
            for k, f in enumerate(files):
                if a.policy in ('cold', 'reset'):
                    eng.send('ucinewgame')
                    eng.isready()
                eng.send('position fen ' + fen)
                d, s, n, b = eng.go(a.limit, a.timeout)
                f.write('%d\t%d\t%s\t%d\t%s\n' % (idx, d, s, n, b))
            done += 1
            if done % 200 == 0:
                for f in files:
                    f.flush()
        code = eng.quit()
        status = 'COMPLETE' if code == 0 else 'INCOMPLETE'
    except Exception as e:  # noqa
        err = str(e)
        if eng is not None:
            eng.kill()
    for f in files:
        if err:
            f.write('# ERROR %s\n' % err)
        f.write('# completed %d of planned %d; engine exit code %s; status %s; end %s\n' % (done, planned, code, status, U.vienna_now()))
        f.close()
    print('%s: completed %d of %d, exit %s, %s %s' % (os.path.basename(a.out), done, planned, code, status, err))
    return 0 if status == 'COMPLETE' and done == planned else 2


def load(path):
    rows, head, trailer = {}, [], ''
    with open(path, 'r', encoding='ascii', errors='replace') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('#'):
                if line.startswith('# completed '):
                    trailer = line
                else:
                    head.append(line)
                continue
            p = line.split('\t')
            if len(p) == 5:
                rows[int(p[0])] = tuple(p[1:])
    return rows, head, trailer


def cmp(a):
    ra, ha, ta = load(a.a)
    rb, hb, tb = load(a.b)
    L = U.header('ROWCMP %s' % a.label, [os.path.abspath(__file__), U.__file__], [], ['planned %d comparisons' % a.planned])
    for name, path, head, tr in (('A', a.a, ha, ta), ('B', a.b, hb, tb)):
        L.append('%s file %s sha256 %s' % (name, path, U.hashes(path)[1]))
        L.extend('%s %s' % (name, h) for h in head if ('exe ' in h or 'settings' in h or 'corpus' in h or 'child mask' in h or 'ROWS' in h or 'ERROR' in h))
        L.append('%s trailer: %s' % (name, tr or '(none: file is cut off)'))
    complete = all(('status COMPLETE' in t and ('completed %d of planned %d;' % (a.planned, a.planned)) in t) for t in (ta, tb))
    keys = sorted(set(ra) | set(rb))
    compared = mism = 0
    examples = []
    for k in keys:
        if k in ra and k in rb:
            compared += 1
            if ra[k] != rb[k]:
                mism += 1
                if len(examples) < 10:
                    examples.append('  position %d: A %s | B %s' % (k, ' '.join(ra[k]), ' '.join(rb[k])))
    L.append('planned %d completed %d mismatches %d (rows only in one file: %d)' % (a.planned, compared, mism, len(keys) - compared))
    L.extend(examples)
    if mism:
        verdict = 'FAIL'
    elif complete and compared == a.planned:
        verdict = 'PASS'
    else:
        verdict = 'INCOMPLETE'
    L.append('VERDICT ROWCMP %s; end %s' % (verdict, U.vienna_now()))
    U.write_log(a.log, L)
    print('\n'.join(L[-(4 + len(examples)):]))
    return {'PASS': 0, 'FAIL': 1, 'INCOMPLETE': 2}[verdict]


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('--exe', required=True)
    r.add_argument('--out', required=True)
    r.add_argument('--mask', required=True)
    r.add_argument('--first', type=int, default=1)
    r.add_argument('--count', type=int, default=2000)
    r.add_argument('--limit', default='depth 13')
    r.add_argument('--policy', choices=['cold', 'warm', 'reset'], default='cold')
    r.add_argument('--net', choices=['on', 'off'], default='on')
    r.add_argument('--hash', type=int, default=16)
    r.add_argument('--threads', type=int, default=1)
    r.add_argument('--timeout', type=float, default=600.0)
    r.add_argument('--label', default='')
    c = sub.add_parser('cmp')
    c.add_argument('--a', required=True)
    c.add_argument('--b', required=True)
    c.add_argument('--planned', type=int, required=True)
    c.add_argument('--log', required=True)
    c.add_argument('--label', default='')
    a = ap.parse_args()
    return run(a) if a.cmd == 'run' else cmp(a)


if __name__ == '__main__':
    sys.exit(main())
