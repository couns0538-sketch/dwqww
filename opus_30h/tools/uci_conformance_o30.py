#!/usr/bin/env python3
"""uci_conformance_o30.py - Opus 30-h job: does an exe (with a v2 net or tuned options) behave like a UCI engine in the
ways a GUI / the gate runner uses it? Own code (python-chess for legality only).

usage: python -I -B uci_conformance_o30.py <exe> [--opt "Name=Value"]... [--expect-info "text"] [--threads 2]
                                           [--mask 0x3] [--json out.json]
Runs one engine process (Idle, CPU mask) through: uci / uciok with the options advertised, setoption + isready,
`info string` echo of a v2 net load (with --expect-info), ucinewgame, go depth / movetime / wtime+btime / nodes /
infinite + stop, a mate-in-1, a position with one legal move, a checkmated and a stalemated side to move, Threads N,
a second ucinewgame, quit - all with OwnBook false (as the crew's gates; with the book on, book positions answer at
once). Every bestmove must be legal in its position (or 0000 / (none) when there is no legal move), every search must
end inside its limit + a margin, `go infinite` must not print bestmove before `stop` and must answer `stop` within 1 s,
quit must end the process within 3 s, stderr must stay empty. Prints one line per check and CONFORMANCE PASS / FAIL;
exit 0 only on PASS. Observations (not counted): `go infinite` with OwnBook at its default (true) in a book position.
"""
import argparse
import ctypes
import json
import queue
import subprocess
import sys
import threading
import time

import chess


class Engine:
    def __init__(self, exe, mask):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, bufsize=1)
        k32 = ctypes.WinDLL('kernel32', use_last_error=True)
        k32.OpenProcess.restype = ctypes.c_void_p
        h = ctypes.c_void_p(k32.OpenProcess(0x0200 | 0x0400, False, self.p.pid))   # SET_INFORMATION | QUERY
        if not h.value or not k32.SetPriorityClass(h, 0x40) or not k32.SetProcessAffinityMask(h, ctypes.c_size_t(mask)):
            self.p.stdin.close()
            raise SystemExit('cannot set Idle / CPU mask on the engine (fail closed)')
        k32.CloseHandle(h)
        self.q = queue.Queue()
        self.err = []
        threading.Thread(target=self._read, args=(self.p.stdout, self.q), daemon=True).start()
        threading.Thread(target=self._read_err, daemon=True).start()

    @staticmethod
    def _read(stream, q):
        for line in stream:
            q.put(line.rstrip('\r\n'))
        q.put(None)

    def _read_err(self):
        for line in self.p.stderr:
            self.err.append(line.rstrip('\r\n'))

    def send(self, cmd):
        self.p.stdin.write(cmd + '\n')
        self.p.stdin.flush()

    def until(self, pred, timeout):
        """Lines up to and including the first one for which pred(line) holds; (lines, seconds) or (lines, None)."""
        t0 = time.monotonic()
        lines = []
        while True:
            left = timeout - (time.monotonic() - t0)
            if left <= 0:
                return lines, None
            try:
                line = self.q.get(timeout=left)
            except queue.Empty:
                return lines, None
            if line is None:
                return lines, None
            lines.append(line)
            if pred(line):
                return lines, time.monotonic() - t0


def bestmove_of(lines):
    for line in reversed(lines):
        if line.startswith('bestmove'):
            parts = line.split()
            return parts[1] if len(parts) > 1 else ''
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe')
    ap.add_argument('--opt', action='append', default=[])
    ap.add_argument('--expect-info', default='')
    ap.add_argument('--threads', type=int, default=2)
    ap.add_argument('--mask', default='0x3')
    ap.add_argument('--json', default='')
    a = ap.parse_args()
    results = []

    def check(name, ok, detail=''):
        results.append({'check': name, 'ok': bool(ok), 'detail': detail})
        print(f"{'ok  ' if ok else 'FAIL'} {name}{': ' + detail if detail else ''}", flush=True)

    e = Engine(a.exe, int(a.mask, 16))
    e.send('uci')
    lines, secs = e.until(lambda l: l == 'uciok', 10)
    names = {l.split(' name ', 1)[1].split(' type ')[0] for l in lines if l.startswith('option name ')}
    check('uci -> uciok', secs is not None, f'{len(names)} options, id: ' + '; '.join(l for l in lines if l.startswith('id ')))
    for kv in a.opt:
        n = kv.split('=', 1)[0]
        check(f'option advertised: {n}', n in names)
    for kv in a.opt:
        n, v = kv.split('=', 1)
        e.send(f'setoption name {n} value {v}')
    if 'OwnBook' in names:
        e.send('setoption name OwnBook value false')   # as the crew's gates: every go below must really search
    e.send('isready')
    lines, secs = e.until(lambda l: l == 'readyok', 30)
    check('setoption + isready -> readyok', secs is not None, f'{secs:.2f} s' if secs is not None else 'no readyok')
    errs = [l for l in lines if 'ERROR' in l.upper()]
    check('no ERROR info line after setoption', not errs, '; '.join(errs)[:200])
    if a.expect_info:
        hit = [l for l in lines if l.startswith('info string') and a.expect_info in l]
        check(f'info string contains "{a.expect_info}"', bool(hit), (hit[0] if hit else '')[:200])

    def search(name, fen, moves, go, limit_s, margin_s=1.5, expect_none=False):
        board = chess.Board(fen) if fen else chess.Board()
        for m in moves:
            board.push_uci(m)
        pos = (f'position fen {fen}' if fen else 'position startpos') + (' moves ' + ' '.join(moves) if moves else '')
        e.send(pos)
        e.send(go)
        lines, secs = e.until(lambda l: l.startswith('bestmove'), limit_s + margin_s + 10)
        bm = bestmove_of(lines)
        if secs is None or bm is None:
            check(name, False, f'no bestmove within {limit_s + margin_s + 10:.1f} s')
            return lines, None
        if expect_none:
            check(name, bm in ('0000', '(none)', ''), f'bestmove {bm!r} with no legal move, {secs:.2f} s')
            return lines, bm
        legal = False
        try:
            legal = chess.Move.from_uci(bm) in board.legal_moves
        except ValueError:
            pass
        check(name, legal and secs <= limit_s + margin_s, f'bestmove {bm} legal={legal}, {secs:.2f} s (limit {limit_s} + {margin_s})')
        return lines, bm

    e.send('ucinewgame')
    e.send('isready')
    e.until(lambda l: l == 'readyok', 30)
    search('go depth 10 (startpos)', None, [], 'go depth 10', 20)
    search('go movetime 500 (after 1.e4 e5)', None, ['e2e4', 'e7e5'], 'go movetime 500', 0.5, 0.5)
    search('go wtime 2000 btime 2000 winc 20 binc 20', None, ['d2d4', 'g8f6', 'c2c4'],
           'go wtime 2000 btime 2000 winc 20 binc 20', 2.0, 0.2)
    search('go nodes 20000', 'r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3', [], 'go nodes 20000', 10)
    # go infinite + stop: no bestmove before stop (UCI), then one within 1 s
    def infinite(name, record):
        e.send('position startpos moves g1f3 d7d5')
        e.send('go infinite')
        early, t_early = e.until(lambda l: l.startswith('bestmove'), 0.8)
        e.send('stop')
        lines, secs = e.until(lambda l: l.startswith('bestmove'), 5) if t_early is None else (early, 0.0)
        bm = bestmove_of(lines)
        b = chess.Board()
        b.push_uci('g1f3'); b.push_uci('d7d5')
        legal = bm is not None and chess.Move.from_uci(bm) in b.legal_moves
        if t_early is not None:
            e.send('isready')   # the stop above was sent after the search had ended: resync
            e.until(lambda l: l == 'readyok', 10)
        record(name, t_early is None and secs is not None and secs <= 1.0 and legal,
               f'bestmove {bm} ' + (f'BEFORE stop ({t_early:.3f} s after go)' if t_early is not None
                                    else f'{secs:.3f} s after stop'))
    infinite('go infinite + stop: no bestmove before stop, then within 1 s (OwnBook false)', check)
    lines, bm = search('mate in 1 found (depth 6)', '6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1', [], 'go depth 6', 10)
    mate = [l for l in lines if ' score mate 1 ' in l + ' ']
    check('mate in 1: bestmove d1d8 and score mate 1', bm == 'd1d8' and bool(mate), f'bestmove {bm}')
    search('one legal move (depth 8)', 'k7/8/2K5/8/8/8/8/1R6 b - - 0 1', [], 'go depth 8', 10)
    search('checkmated side to move -> no move', 'k7/1Q6/1K6/8/8/8/8/8 b - - 0 1', [], 'go depth 3', 3, expect_none=True)
    search('stalemated side to move -> no move', 'k7/2Q5/1K6/8/8/8/8/8 b - - 0 1', [], 'go depth 3', 3, expect_none=True)
    e.send(f'setoption name Threads value {a.threads}')
    e.send('isready')
    e.until(lambda l: l == 'readyok', 30)
    search(f'Threads {a.threads}: go depth 12', 'r2q1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R2Q1RK1 w - - 0 10', [],
           'go depth 12', 30)
    e.send('ucinewgame')
    e.send('isready')
    lines, secs = e.until(lambda l: l == 'readyok', 30)
    check('second ucinewgame + isready', secs is not None)
    search('after ucinewgame: go movetime 300', None, ['c2c4'], 'go movetime 300', 0.3, 0.5)
    observations = []   # behaviour of the engine's defaults that the gates do not use: reported, not counted
    if 'OwnBook' in names:
        e.send('setoption name OwnBook value true')
        e.send('isready')
        e.until(lambda l: l == 'readyok', 30)

        def note(name, ok, detail):
            observations.append({'observation': name, 'uci_conform': bool(ok), 'detail': detail})
            print(f"note {name}: {'conform' if ok else 'NOT conform'} - {detail}", flush=True)
        infinite('OwnBook true (the default) + go infinite in a book position', note)
    e.send('quit')
    try:
        e.p.wait(timeout=3)
        check('quit -> process exits within 3 s', True, f'exit code {e.p.returncode}')
    except subprocess.TimeoutExpired:
        check('quit -> process exits within 3 s', False, 'still running (left alone, never killed)')
    time.sleep(0.2)
    check('stderr empty', not e.err, '; '.join(e.err)[:200])
    ok = all(r['ok'] for r in results)
    print(f"CONFORMANCE {'PASS' if ok else 'FAIL'}: {sum(r['ok'] for r in results)} / {len(results)} checks, exe {a.exe}, "
          f"options {a.opt}")
    if a.json:
        with open(a.json, 'x', encoding='utf-8', newline='\n') as f:
            json.dump({'exe': a.exe, 'options': a.opt, 'checks': results, 'observations': observations, 'pass': ok}, f,
                      indent=1)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
