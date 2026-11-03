#!/usr/bin/env python3
"""smoke2m.py - Opus R15 timed self-play smoke for a Forge candidate line (standard library only).

usage: python -I -B smoke2m.py ENGINE [--line "N1=V1;N2=V2"] [--seconds 120] [--threads 2] [--hash 16]
         [--tc 2000+20] [--max-plies 160] [--random-plies 4] [--seed 15] [--mask 0x3] [--idle] [--out PREFIX]

One engine process plays both sides (ON vs ON) for --seconds of wall time at a real clock (go wtime/btime/winc/binc,
the gate path), Threads / Hash as in the crew's gates, OwnBook false, the line's options set once. Games start from a
fixed position (startpos, kiwipete, two middlegames, one endgame) plus --random-plies random legal plies (seeded per
game), so no two games are alike. Before every search the engine's own `go perft 1` list is read: a bestmove not in
it is an ILLEGAL move (every one is counted; the game ends there). An engine exit is a CRASH (the engine is restarted
and the smoke goes on), no bestmove within the side's remaining clock + 10 s is a HANG. A move that used more than
the side's remaining clock + --timemargin (1000 ms, as fastchess in the crew's gates) is a TIME LOSS; less than that
over the clock is an OVERRUN (reported only: pipe and scheduling latency of an Idle process on a busy core). After
either the clock is reset and the game goes on. Every option must be acknowledged without an
"info string invalid/unknown/error" line. stderr of the engine is kept in PREFIX.stderr.txt; any stderr text counts.

Exit 0 = PASS: >= 1 finished game, 0 illegal, 0 crashes, 0 hangs, 0 time losses, 0 option errors, empty stderr.
1 = FAIL. 2 = usage.
--mask/--idle set this process's CPU mask / Idle class first (Windows), so the engine inherits both (fail closed).
An ENGINE ending in .py is run with this interpreter (used by the self-test's stub engines).
"""
import argparse
import json
import os
import queue
import random
import subprocess
import sys
import threading
import time

STARTS = [
    'startpos',
    'fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',
    'fen r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 3 9',
    'fen r2q1rk1/pb1nbppp/1p2pn2/2pp4/2PP4/1PN1PN2/PB2BPPP/R2Q1RK1 w - - 0 10',
    'fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1',
]


def set_low(mask, idle):
    if os.name != 'nt' or (not mask and not idle):
        return
    import ctypes
    k32 = ctypes.windll.kernel32
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    h = k32.GetCurrentProcess()
    if idle and not k32.SetPriorityClass(ctypes.c_void_p(h), 0x40):
        sys.exit('smoke2m: SetPriorityClass(Idle) failed - not running unprotected')
    if mask and not k32.SetProcessAffinityMask(ctypes.c_void_p(h), ctypes.c_size_t(int(mask, 16))):
        sys.exit(f'smoke2m: SetProcessAffinityMask({mask}) failed - not running unprotected')


class Engine:
    def __init__(self, cmd, errf):
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errf, text=True,
                                  bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        for line in self.p.stdout:
            self.q.put(line.rstrip('\r\n'))
        self.q.put(None)

    def send(self, line):
        try:
            self.p.stdin.write(line + '\n')
            self.p.stdin.flush()
            return True
        except (OSError, ValueError):
            return False

    def until(self, pred, timeout):
        """Lines until pred(line) is true. Returns (lines, status) with status 'ok', 'timeout' or 'exit'."""
        lines, end = [], time.monotonic() + timeout
        while True:
            left = end - time.monotonic()
            if left <= 0:
                return lines, 'timeout'
            try:
                line = self.q.get(timeout=min(left, 0.5))
            except queue.Empty:
                continue
            if line is None:
                return lines, 'exit'
            lines.append(line)
            if pred(line):
                return lines, 'ok'

    def alive(self):
        return self.p.poll() is None

    def close(self):
        if self.alive():
            self.send('quit')
            try:
                self.p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('engine')
    ap.add_argument('--line', default='')
    ap.add_argument('--seconds', type=float, default=120)
    ap.add_argument('--threads', type=int, default=2)
    ap.add_argument('--hash', type=int, default=16)
    ap.add_argument('--tc', default='2000+20')
    ap.add_argument('--max-plies', type=int, default=160)
    ap.add_argument('--random-plies', type=int, default=4)
    ap.add_argument('--seed', type=int, default=15)
    ap.add_argument('--timemargin', type=int, default=1000, help='ms over the clock before it is a time loss (gates: 1000)')
    ap.add_argument('--mask', default='')
    ap.add_argument('--idle', action='store_true')
    ap.add_argument('--out', default='smoke2m')
    a = ap.parse_args()
    if not os.path.isfile(a.engine):
        print(f'smoke2m: engine not found: {a.engine}', file=sys.stderr)
        return 2
    for suffix in ('.json', '.stderr.txt'):
        if os.path.exists(a.out + suffix):
            print(f'smoke2m: {a.out + suffix} exists (never overwritten)', file=sys.stderr)
            return 2
    try:
        base_ms, inc_ms = (int(x) for x in a.tc.split('+'))
    except ValueError:
        print(f'smoke2m: bad --tc {a.tc!r} (want 2000+20)', file=sys.stderr)
        return 2
    opts = []
    for part in [p for p in a.line.split(';') if p.strip()]:
        if '=' not in part:
            print(f'smoke2m: bad option {part!r}', file=sys.stderr)
            return 2
        n, v = part.split('=', 1)
        opts.append((n.strip(), v.strip()))
    set_low(a.mask, a.idle)
    cmd = [sys.executable, '-I', '-B', a.engine] if a.engine.endswith('.py') else [a.engine]
    errf = open(a.out + '.stderr.txt', 'w')
    st = dict(games=0, finished_games=0, plies=0, illegal=0, crashes=0, hangs=0, time_losses=0, overruns=0,
              option_errors=0,
              mates_or_stalemates=0, max_plies_games=0, restarts=0)
    events = []

    def start_engine():
        e = Engine(cmd, errf)
        e.send('uci')
        _, s = e.until(lambda l: l == 'uciok', 30)
        if s != 'ok':
            return None, f'no uciok ({s})'
        for n, v in [('Threads', a.threads), ('Hash', a.hash), ('OwnBook', 'false')] + opts:
            e.send(f'setoption name {n} value {v}')
        e.send('isready')
        lines, s = e.until(lambda l: l == 'readyok', 60)
        bad = [l for l in lines if l.startswith(('info string invalid', 'info string unknown', 'info string error'))]
        if bad:
            st['option_errors'] += len(bad)
            events.append({'event': 'option_error', 'lines': bad})
        return (e, None) if s == 'ok' else (None, f'no readyok ({s})')

    eng, why = start_engine()
    if eng is None:
        st['crashes'] += 1
        events.append({'event': 'start_failed', 'why': why})
    t_end = time.monotonic() + a.seconds
    game = 0
    while eng is not None and time.monotonic() < t_end:
        game += 1
        rng = random.Random(a.seed * 100003 + game)
        start = STARTS[(game - 1) % len(STARTS)]
        moves = []
        clock = [base_ms, base_ms]  # [side to move at the start, the other side]
        eng.send('ucinewgame')
        eng.send('isready')
        _, s = eng.until(lambda l: l == 'readyok', 30)
        if s != 'ok':
            st['crashes' if s == 'exit' else 'hangs'] += 1
            events.append({'event': 'newgame_' + s, 'game': game})
            break
        st['games'] += 1
        result = None
        ply = 0
        while time.monotonic() < t_end:
            pos = f'position {start}' + (' moves ' + ' '.join(moves) if moves else '')
            eng.send(pos)
            eng.send('go perft 1')
            lines, s = eng.until(lambda l: l.startswith('nodes '), 30)
            if s != 'ok':
                st['crashes' if s == 'exit' else 'hangs'] += 1
                events.append({'event': 'perft_' + s, 'game': game, 'ply': ply, 'position': pos})
                result = s
                break
            legal = {l.split(':')[0] for l in lines if ':' in l and not l.startswith('info')}
            if not legal:
                st['mates_or_stalemates'] += 1
                result = 'terminal'
                break
            if ply < a.random_plies:  # opening randomisation: random legal plies, no search
                moves.append(rng.choice(sorted(legal)))
                ply += 1
                continue
            if ply >= a.max_plies + a.random_plies:
                st['max_plies_games'] += 1
                result = 'max_plies'
                break
            side = (ply - a.random_plies) % 2
            white_to_move = (side == 0)  # clock[0] belongs to whoever moves first after the random plies
            wt, bt = (clock[0], clock[1]) if white_to_move else (clock[1], clock[0])
            t0 = time.monotonic()
            eng.send(f'go wtime {max(1, wt)} btime {max(1, bt)} winc {inc_ms} binc {inc_ms}')
            lines, s = eng.until(lambda l: l.startswith('bestmove'), clock[side] / 1000.0 + 10.0)
            used = int((time.monotonic() - t0) * 1000)
            if s != 'ok':
                st['crashes' if s == 'exit' else 'hangs'] += 1
                events.append({'event': 'search_' + s, 'game': game, 'ply': ply, 'position': pos,
                               'tail': lines[-3:]})
                if s == 'timeout':
                    eng.send('stop')
                    eng.until(lambda l: l.startswith('bestmove'), 5)
                result = s
                break
            parts = lines[-1].split()
            best = parts[1] if len(parts) > 1 else ''
            if best not in legal:
                st['illegal'] += 1
                events.append({'event': 'illegal', 'game': game, 'ply': ply, 'move': best, 'position': pos,
                               'legal_count': len(legal)})
                result = 'illegal'
                break
            clock[side] -= used
            if clock[side] < 0:
                # as in the crew's gates (fastchess timemargin): beyond the margin it is a time loss, within it an
                # overrun (pipe / scheduling latency of an Idle process on a busy core, no engine fault)
                lost = -clock[side] > a.timemargin
                st['time_losses' if lost else 'overruns'] += 1
                events.append({'event': 'time_loss' if lost else 'overrun', 'game': game, 'ply': ply,
                               'used_ms': used, 'left_ms': clock[side] + used})
                clock[side] = base_ms
            clock[side] += inc_ms
            moves.append(best)
            st['plies'] += 1
            ply += 1
        if result in ('terminal', 'max_plies'):
            st['finished_games'] += 1
        if result in ('exit', 'timeout') or not eng.alive():
            eng.close()
            if time.monotonic() >= t_end:
                eng = None
                break
            st['restarts'] += 1
            eng, why = start_engine()
            if eng is None:
                st['crashes'] += 1
                events.append({'event': 'restart_failed', 'why': why})
                break
    if eng is not None:
        eng.close()
    errf.close()
    stderr_text = open(a.out + '.stderr.txt', encoding='utf-8', errors='replace').read().strip()
    ok = (st['finished_games'] >= 1 and st['illegal'] == 0 and st['crashes'] == 0 and st['hangs'] == 0
          and st['time_losses'] == 0 and st['option_errors'] == 0 and not stderr_text)
    summary = dict(tool='smoke2m.py', verdict='PASS' if ok else 'FAIL', engine=os.path.abspath(a.engine),
                   line=a.line, seconds=a.seconds, threads=a.threads, hash=a.hash, tc=a.tc, timemargin=a.timemargin,
                   seed=a.seed, mask=a.mask, idle=a.idle,
                   stderr_first_line=stderr_text.splitlines()[0] if stderr_text else '', **st, events=events[:50])
    with open(a.out + '.json', 'w', newline='\n') as f:
        json.dump(summary, f, indent=1)
        f.write('\n')
    print(f"SMOKE2M {summary['verdict']} line [{a.line}] games {st['games']} finished {st['finished_games']} plies "
          f"{st['plies']} illegal {st['illegal']} crashes {st['crashes']} hangs {st['hangs']} time_losses "
          f"{st['time_losses']} overruns {st['overruns']} option_errors {st['option_errors']} stderr "
          f"{'yes' if stderr_text else 'no'} ({a.seconds:.0f} s, Threads {a.threads}, tc {a.tc}, margin {a.timemargin} ms)")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
