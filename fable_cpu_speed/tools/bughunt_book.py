# bughunt_book.py - bug hunt, second battery: the "Book File" option fed with files that are not opening books,
# and move lists in odd notations. Same flags and the same run logic as bughunt.py.
#   python -I -B bughunt_book.py --log L --exes release=PATH,asan=PATH [--masks 0x2,0x8]
import argparse
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402
import san as S  # noqa: E402
import bughunt as B  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', required=True)
    ap.add_argument('--exes', required=True)
    ap.add_argument('--masks', default='0x2,0x8')
    a = ap.parse_args()
    U.require_lane()
    exes = [x.split('=', 1) for x in a.exes.split(',')]
    masks = [U.parse_mask(m) for m in a.masks.split(',')]
    work = os.path.join(U.JOB, 'out', 'bughunt', 'book')
    os.makedirs(os.path.join(work, 'dir with spaces'), exist_ok=True)
    fx = {}

    def make(name, data):
        p = os.path.join(work, name)
        if not os.path.exists(p):
            with open(p, 'wb') as f:
                f.write(data)
        fx[name] = p

    make('empty.bin', b'')
    make('seven_bytes.bin', b'\x01\x02\x03\x04\x05\x06\x07')
    make('sixteen_zero_bytes.bin', b'\x00' * 16)
    make('ff_4096.bin', b'\xff' * 4096)
    make('odd_size_100001.bin', bytes((i * 131 + 7) % 256 for i in range(100001)))
    make(os.path.join('dir with spaces', 'zeros 160.bin'), b'\x00' * 160)
    fx['an exe file'] = U.LOCK_EXE
    fx['a folder'] = work
    cs = []
    for name, path in fx.items():
        cs.append(('Book File = %s' % name, B.P0,
                   ['setoption name OwnBook value true', 'setoption name Book File value ' + path, 'isready', ('wait', 'readyok', 60),
                    B.P0, 'go movetime 30', B.BEST, 'setoption name Book File value <empty>', 'isready', ('wait', 'readyok', 60),
                    B.P0, 'go movetime 30', B.BEST]))
    for tag, moves in (('uppercase promotion letter', 'e2e4 d7d5 e4d5 c7c6 d5c6 b8a6 c6b7 a6b8 b7a8Q'),
                       ('king-takes-rook castling notation', 'e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 e1h1'),
                       ('null move 0000 in the list', 'e2e4 0000 d2d4'),
                       ('move with trailing garbage', 'e2e4x e7e5'),
                       ('five-character non-promotion', 'e2e4q e7e5'),
                       ('promotion to king', 'e2e4 d7d5 e4d5 c7c6 d5c6 b8a6 c6b7 a6b8 b7a8k'),
                       ('castling through notation e1g1 when illegal', 'e1g1')):
        cs.append(('moves: %s' % tag, B.P0, ['position startpos moves ' + moves, 'go depth 3', B.BEST]))
    legal = {}
    ref = U.Engine(U.LOCK_EXE, masks[0])
    ref.uci()
    ref.send(B.P0)
    _, ls = ref.perft(1, 60)
    legal[B.P0] = {l.split(':')[0] for l in ls if ':' in l}
    ref.quit()
    results = {}

    def lane(i, name, exe):
        env = S.env() if name != 'release' else None
        for k, (cname, pos, steps) in enumerate(cs):
            r = B.run_case(exe, masks[i % len(masks)], env, steps, os.path.join(work, '%s_%03d.stderr.txt' % (name, k)))
            # book moves are legal moves of the start position; a refused move list leaves the start position
            for b in r['best']:
                if b in ('0000', '(none)'):
                    r['flags'].append('NULLMOVE')
            results[(name, k)] = r

    ts = [threading.Thread(target=lane, args=(i, n, e)) for i, (n, e) in enumerate(exes)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    L = U.header('BUG HUNT 2: Book File with non-book files, odd move notations', [os.path.abspath(__file__), B.__file__, U.__file__], [e for _, e in exes], [
        'flags: CRASH, HANG, NO-ANSWER, NULLMOVE, SANITIZER; a best move is not checked for legality here because the move list may have been accepted in part',
        'planned %d cases x %d exes = %d runs' % (len(cs), len(exes), len(cs) * len(exes))])
    flagged = 0
    for k, (cname, pos, steps) in enumerate(cs):
        parts, anyflag = [], False
        for name, _ in exes:
            r = results.get((name, k))
            anyflag = anyflag or (r is None) or bool(r['flags'])
            parts.append('%s: exit %s best %s%s | %s' % (name, r['code'], ','.join(r['best']) or '-', (' FLAGS ' + ' '.join(r['flags'])) if r['flags'] else '',
                                                    ' ; '.join(r['info'])[:160]) if r else '%s: NOT RUN' % name)
        flagged += 1 if anyflag else 0
        L.append('%s %-46s | %s' % ('!!' if anyflag else 'ok', cname[:46], ' || '.join(parts)))
        if anyflag:
            for name, _ in exes:
                r = results.get((name, k))
                if r and r['flags']:
                    for e in (r['rep'] or r['err'][:6]):
                        L.append('      %s stderr: %s' % (name, e.strip()[:260]))
    L.append('planned %d runs completed %d; cases with at least one flag: %d' % (len(cs) * len(exes), len(results), flagged))
    L.append('VERDICT BUGHUNT2 DONE; end %s' % U.vienna_now())
    U.write_log(a.log, L)
    print('\n'.join(L[-(len(cs) + 12):]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
