# bughunt.py - a battery of UCI edge cases, each in a new process, on a release exe and on instrumented builds.
# It looks for: a crash (exit code not 0), a hang (no answer or no exit in time), a search that gives no best
# move, a best move that is not legal, "bestmove 0000" although legal moves exist, and sanitizer reports.
# Findings are candidates for a human to judge; nothing is fixed here.
#   python -I -B bughunt.py --log L --exes release=PATH,asan=PATH,ubsan=PATH [--masks 0x2,0x8,0x40]
import argparse
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402
import san as S  # noqa: E402

P0 = 'position startpos'
KIWI = 'position fen ' + U.KIWIPETE
ENDG = 'position fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1'
MATE = 'position fen R6k/6pp/8/8/8/8/8/7K b - - 0 1'
STALE = 'position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1'
SHUFFLE = 'g1f3 g8f6 f3g1 f6g8 '
BEST = ('wait', 'bestmove', 30)


def cases():
    c = []

    def add(name, legal, *steps):
        c.append((name, legal, list(steps)))

    for tag, pos in (('start', P0), ('kiwi', KIWI), ('endg', ENDG)):
        for lim in ('nodes 0', 'nodes 1', 'depth 1', 'movetime 0', 'movetime 1', 'wtime 0 btime 0', 'wtime 1 btime 1',
                    'wtime 30 btime 30 winc 0 binc 0 movestogo 1', 'mate 1', 'depth 0', 'depth -5', 'depth 9999 nodes 20000',
                    'nodes 18446744073709551615 depth 3', 'nodes abc depth 3', 'searchmoves zzzz depth 3', 'depth',
                    'wtime -100 btime -100', 'movestogo 0 wtime 1000 btime 1000', 'winc 100000 binc 100000 wtime 1 btime 1 depth 4',
                    'nodes 5000 searchmoves'):
            add('%s: go %s' % (tag, lim), pos, pos, 'go ' + lim, BEST)
    add('start: go searchmoves e2e4 depth 3', P0, P0, 'go searchmoves e2e4 depth 3', BEST)
    add('go infinite then stop', P0, P0, 'go infinite', ('sleep', 0.3), 'stop', BEST)
    add('go without limits then stop', P0, P0, 'go', ('sleep', 0.3), 'stop', BEST)
    add('go ponder, ponderhit, stop', P0, P0, 'go ponder', ('sleep', 0.2), 'ponderhit', ('sleep', 0.2), 'stop', BEST)
    add('go ponder with clock, ponderhit', P0, P0, 'go ponder wtime 1000 btime 1000', ('sleep', 0.2), 'ponderhit', BEST)
    add('go ponder then stop', P0, P0, 'go ponder', ('sleep', 0.2), 'stop', BEST)
    add('ponderhit and stop with no search', None, 'ponderhit', 'stop', 'isready', ('wait', 'readyok', 10))
    add('two go commands in a row', P0, P0, 'go depth 14', 'go depth 1', BEST, BEST)
    add('isready during search', P0, P0, 'go infinite', ('sleep', 0.2), 'isready', ('wait', 'readyok', 10), 'stop', BEST)
    add('ucinewgame during search', None, P0, 'go infinite', ('sleep', 0.2), 'ucinewgame', 'isready', ('wait', 'readyok', 10))
    add('Hash change during search', None, P0, 'go infinite', ('sleep', 0.2), 'setoption name Hash value 64', 'isready', ('wait', 'readyok', 30))
    add('Threads change during search, then search', P0, P0, 'go infinite', ('sleep', 0.2), 'setoption name Threads value 4', 'isready',
        ('wait', 'readyok', 30), 'go depth 6', BEST, BEST)
    add('bench during search', None, P0, 'go infinite', ('sleep', 0.2), 'bench 6', ('wait', 'info string bench', 60))
    add('quit during search', None, P0, 'go infinite', ('sleep', 0.2))
    add('stdin closed during search', None, P0, 'go infinite', ('sleep', 0.2), ('close',))
    add('stdin closed at once', None, ('close',))
    add('checkmated root', MATE, MATE, 'go depth 5', BEST)
    add('stalemated root', STALE, STALE, 'go depth 5', BEST)
    add('checkmated root, clock', MATE, MATE, 'go wtime 1000 btime 1000', BEST)
    bad = ['8/8/8/8/8/8/8/8 w - - 0 1', '4k3/8/8/8/8/8/8/4RK2 w - - 0 1', 'kK6/8/8/8/8/8/8/8 w - - 0 1',
           'P7/8/8/8/8/8/8/k6K w - - 0 1', '4k3/8/8/8/8/8/8/4K3 w KQkq - 0 1',
           'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 1',
           'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - -5 0',
           'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 999999999',
           'rnbqkbnr/pppppppp/9/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
           'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR x KQkq - 0 1',
           'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 250 1',
           'k7/8/2QQQQQ1/2QQQQQ1/2QQQQQ1/2QQQQQ1/2QQQQQ1/7K w - - 0 1',
           '1k6/8/QQQQQQQQ/QQQQQQQQ/QQQQQQQQ/QQQQQQQQ/8/K7 b - - 0 1',
           'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR', 'w - - 0 1', '']
    for i, f in enumerate(bad):
        # whatever the engine makes of the FEN, the search afterwards must end with a move or a clean refusal
        add('odd FEN %02d [%s]' % (i + 1, f), 'position fen ' + f, 'position fen ' + f, 'go depth 4', BEST)
    add('1,600-ply shuffle game', None, 'position startpos moves ' + SHUFFLE * 400, 'go depth 6', BEST)
    add('8,000-ply shuffle game', None, 'position startpos moves ' + SHUFFLE * 2000, 'go depth 6', BEST)
    add('illegal move in the list', P0, 'position startpos moves e2e4 e7e5 e1e2 zzzz', 'go depth 3', BEST)
    add('position without arguments', P0, 'position', 'position fen', 'position startpos moves', 'go depth 3', BEST)
    for v in ('0', '1', '2048', '99999', '-1', 'abc', ''):
        add('Hash value [%s]' % v, P0, 'setoption name Hash value ' + v, 'isready', ('wait', 'readyok', 120), P0, 'go depth 4', BEST)
    for v in ('0', '-3', '2', '8', 'abc'):
        add('Threads value [%s]' % v, P0, 'setoption name Threads value ' + v, 'isready', ('wait', 'readyok', 60), P0, 'go depth 4', BEST)
    add('Move Overhead 99999 with a clock', P0, 'setoption name Move Overhead value 99999', P0, 'go wtime 1000 btime 1000', BEST)
    add('UseNNUE value maybe', P0, 'setoption name UseNNUE value maybe', P0, 'go depth 4', BEST)
    add('Book File that does not exist', P0, 'setoption name Book File value C:\\nonexistent\\x.bin', P0, 'go movetime 50', BEST)
    add('OwnBook and Ponder on, clock search at the start position', P0, 'setoption name OwnBook value true', 'setoption name Ponder value true', P0, 'go movetime 50', BEST)
    add('setoption fragments', P0, 'setoption', 'setoption name', 'setoption name Hash', 'setoption name Clear Hash', 'setoption value 3', P0, 'go depth 3', BEST)
    add('unknown command, empty lines, 100 KB line', P0, 'xyzzy', '', '   ', 'a' * 100000, P0, 'go depth 3', BEST)
    for v in ('0', '1', 'abc', '11', '-1', ''):
        add('go perft [%s]' % v, None, P0, 'go perft ' + v, 'isready', ('wait', 'readyok', 60))
    add('perft 2 on a checkmated root', None, MATE, 'go perft 2', 'isready', ('wait', 'readyok', 60))
    for v in ('0', '-3', 'abc', '1'):
        add('bench [%s]' % v, None, 'bench ' + v, ('wait', 'info string bench', 300))
    add('go depth 64 with a node limit on a small endgame', ENDG, ENDG, 'go depth 64 nodes 300000', ('wait', 'bestmove', 300))
    add('go depth 64 on bare kings', None, 'position fen 8/8/8/4k3/8/8/8/4K3 w - - 0 1', 'go depth 64', ('wait', 'bestmove', 60))
    return c


def run_case(exe, mask, env, steps, errfile):
    p = U.spawn([exe], mask, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=open(errfile, 'wb'), env=env, cwd=os.path.dirname(exe))
    lines, lock = [], threading.Lock()

    def rd():
        for raw in p.stdout:
            with lock:
                lines.append(raw.decode('ascii', 'replace').rstrip('\r\n'))

    t = threading.Thread(target=rd, daemon=True)
    t.start()
    flags, closed, seen = [], False, 0

    def send(s):
        try:
            p.stdin.write((s + '\n').encode('ascii'))
            p.stdin.flush()
        except OSError:
            flags.append('PIPE-CLOSED')

    send('uci')
    for st in steps:
        if isinstance(st, str):
            send(st)
        elif st[0] == 'sleep':
            time.sleep(st[1])
        elif st[0] == 'close':
            try:
                p.stdin.close()
            except OSError:
                pass
            closed = True
        elif st[0] == 'wait':
            end = time.monotonic() + st[2]
            hit = False
            while time.monotonic() < end and not hit:
                with lock:
                    for i in range(seen, len(lines)):
                        if lines[i].startswith(st[1]):
                            seen = i + 1
                            hit = True
                            break
                if not hit:
                    if p.poll() is not None:
                        time.sleep(0.2)
                        with lock:
                            hit = any(l.startswith(st[1]) for l in lines[seen:])
                        break
                    time.sleep(0.01)
            if not hit:
                flags.append('NO-ANSWER(%s)' % st[1])
    if not closed:
        send('quit')
        try:
            p.stdin.close()
        except OSError:
            pass
    try:
        code = p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
        code = 'HANG'
        flags.append('HANG')
    t.join(timeout=5)
    if code not in (0, 'HANG'):
        flags.append('CRASH(exit %s)' % code)
    err = open(errfile, 'r', encoding='utf-8', errors='replace').read()
    rep = S.report_lines(err)
    if rep:
        flags.append('SANITIZER(%d lines)' % len(rep))
    with lock:
        out = list(lines)
    return {'code': code, 'flags': flags, 'best': [l.split()[1] if len(l.split()) > 1 else '?' for l in out if l.startswith('bestmove')],
            'info': [l for l in out if l.startswith('info string') and 'bench' not in l][:3], 'tail': out[-4:], 'err': err.splitlines()[:25], 'rep': rep[:6]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', required=True)
    ap.add_argument('--exes', required=True)
    ap.add_argument('--masks', default='0x2,0x8,0x40')
    a = ap.parse_args()
    U.require_lane()
    exes = [x.split('=', 1) for x in a.exes.split(',')]
    masks = [U.parse_mask(m) for m in a.masks.split(',')]
    work = os.path.join(U.JOB, 'out', 'bughunt')
    os.makedirs(work, exist_ok=True)
    cs = cases()
    # legal move lists from the lock exe
    legal = {}
    ref = U.Engine(U.LOCK_EXE, masks[0])
    ref.uci()
    for _, pos, _ in cs:
        if pos and pos not in legal:
            ref.send('position startpos')          # an invalid FEN leaves this position in place, as in the cases
            ref.send(pos)
            _, ls = ref.perft(1, 60)
            legal[pos] = {l.split(':')[0] for l in ls if ':' in l}
    ref.quit()
    results = {}

    def lane(i, name, exe):
        env = S.env() if name != 'release' else None
        for k, (cname, pos, steps) in enumerate(cs):
            r = run_case(exe, masks[i % len(masks)], env, steps, os.path.join(work, '%s_%03d.stderr.txt' % (name, k)))
            if pos is not None:
                lg = legal[pos]
                for b in r['best']:
                    if b in ('0000', '(none)'):
                        if lg:
                            r['flags'].append('NULLMOVE(%d legal moves exist)' % len(lg))
                    elif b not in lg:
                        r['flags'].append('ILLEGAL(%s)' % b)
            results[(name, k)] = r

    ts = [threading.Thread(target=lane, args=(i, n, e)) for i, (n, e) in enumerate(exes)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    L = U.header('BUG HUNT: UCI edge-case battery', [os.path.abspath(__file__), U.__file__, S.__file__], [e for _, e in exes], [
        'each case runs in a new process on every exe; legal move lists come from the lock exe (go perft 1)',
        'flags: CRASH, HANG, NO-ANSWER, NULLMOVE (bestmove 0000 although legal moves exist), ILLEGAL, SANITIZER',
        'planned %d cases x %d exes = %d runs' % (len(cs), len(exes), len(cs) * len(exes))])
    flagged = 0
    for k, (cname, pos, steps) in enumerate(cs):
        parts, anyflag = [], False
        for name, _ in exes:
            r = results.get((name, k))
            if r is None:
                parts.append('%s: NOT RUN' % name)
                anyflag = True
                continue
            anyflag = anyflag or bool(r['flags'])
            parts.append('%s: exit %s best %s%s' % (name, r['code'], ','.join(r['best']) or '-', (' FLAGS ' + ' '.join(r['flags'])) if r['flags'] else ''))
        L.append('%s %-58s | %s' % ('!!' if anyflag else 'ok', cname[:58], ' | '.join(parts)))
        if anyflag:
            flagged += 1
            for name, _ in exes:
                r = results.get((name, k))
                if r and r['flags']:
                    L.append('      %s info: %s' % (name, ' ; '.join(r['info'])[:300]))
                    L.append('      %s last output: %s' % (name, ' ; '.join(r['tail'])[:400]))
                    for e in (r['rep'] or r['err'][:6]):
                        L.append('      %s stderr: %s' % (name, e.strip()[:260]))
    L.append('planned %d runs completed %d; cases with at least one flag: %d' % (len(cs) * len(exes), len(results), flagged))
    L.append('VERDICT BUGHUNT DONE (flags are candidates to judge, see README.md); end %s' % U.vienna_now())
    U.write_log(a.log, L)
    print('\n'.join(l for l in L if l.startswith(('!!', '      ', 'planned', 'VERDICT'))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
