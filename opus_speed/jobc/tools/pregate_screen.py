#!/usr/bin/env python3
"""pregate_screen.py - cheap screens that reject a broken Forge candidate BEFORE any gate game (Job C).

usage: python -I -B pregate_screen.py --exe CAND.exe [--pins d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354]
         [--perft-pins startpos=4865609,kiwipete=193690690] [--opt Name=Value ...] [--ref-exe LOCK.exe]
         [--require Threads Hash OwnBook UseNNUE] [--wac FILE.epd --wac-n 60 --wac-nodes 100000 --wac-min K]
         [--positions 20] [--movetime 200] [--budget-s 300] [--json OUT.json] [--log OUT.uci.log]

Checks, in order (each PASS / FAIL, the whole run stops at the first FAIL that makes the rest meaningless):
  1 file     the exe exists and is a PE image (MZ header)
  2 uci      'uci' answers 'uciok' within 10 s; the option list is captured (the 'id author' line is dropped)
  3 options  every --require option and every --opt name is advertised; with --ref-exe the shared options must
             have the same type / default / min / max as the reference (a changed default silently changes the gate),
             additions are listed
  4 ready    'isready' -> 'readyok'
  5 bench    'bench D' at pure UCI defaults (no setoption at all) for every depth of --pins: nodes must equal the pin
             (the lock's OFF pins; a candidate's option is OFF by default). 'bench D' with no pin is only recorded.
  6 perft    'go perft 5' on startpos and kiwipete at defaults: nodes must equal --perft-pins
  7 smoke    setoption Threads=1 Hash=16 OwnBook=false (+ --opt), then on --positions EPD positions (first lines of
             --wac, else built-in): ucinewgame / isready / position / go movetime M: a bestmove must arrive within
             M + 3000 ms, be legal in the position (python-chess) and not '0000'
  8 wac      the next --wac-n positions of the EPD at 'go nodes N' (deterministic at Threads=1): solved = bestmove in
             bm and not in am; FAIL only below --wac-min (default 0 = report only); compare with the lock's count
  9 quit     'quit' ends the process within 5 s
Exit codes: 0 PASS, 1 FAIL, 3 PASS but over --budget-s (SLOW), 2 usage / IO. The engine is the only process
started; it inherits the caller's CPU mask and priority (run it on CPUs 0-1 at Idle); a hung engine is killed
(it is this tool's own child). Never run two screens at once.
"""
import argparse
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time

KIWI = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
BUILTIN_FENS = [
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', KIWI,
    '8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1', 'r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1',
    'rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8', 'r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10',
    '2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1', '8/7p/5k2/5p2/p1p2P2/Pr1pPK2/1P1R3P/8 b - - 0 1',
    '5rk1/1ppb3p/p1pb4/6q1/3P1p1r/2P1R2P/PP1BQ1P1/5RKN w - - 0 1', 'r1bq2rk/pp3pbp/2p1p1pQ/7P/3P4/2PB1N2/PP3PPR/2KR4 w - - 0 1',
    '5k2/6pp/p1qN4/1p1p4/3P4/2PKP2Q/PP3r2/3R4 b - - 0 1', '7k/p7/1R5K/6r1/6p1/6P1/8/8 w - - 0 1',
    '8/8/8/8/8/4k3/4P3/4K3 w - - 0 1', '8/8/1p6/8/8/8/8/k6K w - - 0 1', '4k3/8/8/8/8/8/8/4K2R w K - 0 1',
    'r3k3/8/8/8/8/8/8/4K3 b q - 0 1', '8/P7/8/8/8/8/8/k6K w - - 0 1', '8/8/8/3pP3/8/8/8/k6K w - d6 0 1',
    '6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1', 'rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3',
]


BAD_RX = re.compile(r'invalid FEN|invalid fen|illegal move|unknown command|error', re.IGNORECASE)


def full_fen(fen):
    """A FEN must carry all six fields (placement, side, castling, ep, halfmove, fullmove): the lock rejects a
    placement-only FEN with 'info string invalid FEN' and silently keeps its old position."""
    f = fen.split()
    if len(f) != 6:
        raise ValueError(f'not a six-field FEN: {fen!r}')
    return fen


class Engine:
    def __init__(self, exe, log):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.q = queue.Queue()
        self.log = log
        self.bad = []       # engine lines that mean a rejected input (e.g. 'info string invalid FEN': the engine keeps its OLD position)
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        for line in self.p.stdout:
            self.q.put(line.rstrip('\r\n'))
        self.q.put(None)

    def send(self, s):
        if self.log:
            self.log.write('> ' + s + '\n')
        try:
            self.p.stdin.write(s + '\n')
            self.p.stdin.flush()
        except (OSError, ValueError):
            pass

    def until(self, pred, timeout):
        """Lines until pred(line) is true; raises TimeoutError / EOFError. Never records 'id author' lines."""
        end = time.monotonic() + timeout
        seen = []
        while True:
            try:
                line = self.q.get(timeout=max(0.01, end - time.monotonic()))
            except queue.Empty:
                raise TimeoutError(f'no answer within {timeout:.1f} s (last: {seen[-1][:80] if seen else "-"})')
            if line is None:
                raise EOFError('engine closed its output')
            if line.startswith('id author'):
                continue
            if self.log:
                self.log.write(line + '\n')
            seen.append(line)
            if BAD_RX.search(line):
                self.bad.append(line[:120])
            if pred(line):
                return seen

    def kill(self):
        try:
            self.p.kill()
        except OSError:
            pass


def parse_options(lines):
    opts = {}
    rx = re.compile(r'^option name (.+?) type (\w+)(.*)$')
    for l in lines:
        m = rx.match(l)
        if not m:
            continue
        rest = m.group(3)
        d = {'type': m.group(2)}
        for k in ('default', 'min', 'max'):
            mm = re.search(rf'\b{k} (\S+)', rest)
            if mm:
                d[k] = mm.group(1)
        opts[m.group(1)] = d
    return opts


def kv(s):
    return {k: int(v) for k, v in (x.split('=') for x in s.split(',') if x)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--exe', required=True)
    ap.add_argument('--pins', default='d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354')
    ap.add_argument('--perft-pins', default='startpos=4865609,kiwipete=193690690')
    ap.add_argument('--opt', action='append', default=[])
    ap.add_argument('--ref-exe')
    ap.add_argument('--require', nargs='*', default=['Threads', 'Hash', 'OwnBook', 'UseNNUE'])
    ap.add_argument('--wac')
    ap.add_argument('--wac-n', type=int, default=60)
    ap.add_argument('--wac-nodes', type=int, default=100000)
    ap.add_argument('--wac-min', type=int, default=0)
    ap.add_argument('--positions', type=int, default=20)
    ap.add_argument('--movetime', type=int, default=200)
    ap.add_argument('--budget-s', type=float, default=300)
    ap.add_argument('--json')
    ap.add_argument('--log')
    a = ap.parse_args()
    for p in (a.json, a.log):
        if p and os.path.exists(p):
            print(f'pregate_screen: {p} exists (never overwritten)', file=sys.stderr)
            return 2
    log = open(a.log, 'w', encoding='utf-8', newline='\n') if a.log else None
    t_start = time.monotonic()
    rep = {'exe': a.exe, 'opts': a.opt, 'checks': [], 'verdict': None, 'pc_clock': time.strftime('%Y-%m-%d %H:%M:%S')}
    failed = False

    def check(name, ok, detail):
        nonlocal failed
        rep['checks'].append({'check': name, 'result': 'PASS' if ok else 'FAIL', 'detail': detail, 't': round(time.monotonic() - t_start, 2)})
        print(f'[{rep["checks"][-1]["t"]:7.2f}s] {name:<8} {"PASS" if ok else "FAIL"}  {detail}', flush=True)
        failed |= not ok
        return ok

    # 1 file
    try:
        with open(a.exe, 'rb') as f:
            head = f.read(2)
        ok = head == b'MZ' and os.path.getsize(a.exe) > 0
        check('file', ok, f'{a.exe}: {os.path.getsize(a.exe)} bytes, {"PE image" if ok else "not a PE image"}')
    except OSError as e:
        check('file', False, f'{a.exe}: {e}')
    if failed:
        return finish(rep, a, log, t_start)
    # 2 uci
    eng = None
    try:
        eng = Engine(a.exe, log)
        eng.send('uci')
        lines = eng.until(lambda l: l == 'uciok', 10)
        opts = parse_options(lines)
        idname = next((l[8:] for l in lines if l.startswith('id name ')), '')
        check('uci', True, f'uciok after {len(lines)} lines; id name {idname!r}; {len(opts)} options')
    except (OSError, TimeoutError, EOFError) as e:
        check('uci', False, f'no uciok: {e}')
        opts = {}
    if failed:
        if eng:
            eng.kill()
        return finish(rep, a, log, t_start)
    rep['options'] = opts
    # 3 options
    missing = [o for o in a.require if o not in opts]
    optnames = [o.split('=', 1)[0] for o in a.opt]
    missing += [o for o in optnames if o not in opts]
    detail = f'required {a.require} + {optnames}: ' + ('all advertised' if not missing else f'MISSING {missing}')
    diffs, adds = [], []
    if a.ref_exe:
        try:
            ref = Engine(a.ref_exe, None)
            ref.send('uci')
            rl = ref.until(lambda l: l == 'uciok', 10)
            ref.send('quit')
            ref.p.wait(timeout=5)
            ropts = parse_options(rl)
            for k, v in opts.items():
                if k in ropts and ropts[k] != v:
                    diffs.append(f'{k}: ref {ropts[k]} cand {v}')
                elif k not in ropts:
                    adds.append(k)
            gone = [k for k in ropts if k not in opts]
            detail += f'; vs reference: {len(diffs)} changed, {len(adds)} added {adds[:8]}, {len(gone)} removed {gone[:8]}'
            if gone:
                diffs.append(f'removed options: {gone}')
            rep['option_diffs'] = diffs
            rep['option_additions'] = adds
        except (OSError, TimeoutError, EOFError, subprocess.TimeoutExpired) as e:
            detail += f'; reference exe unusable: {e}'
            diffs.append('reference exe unusable')
    check('options', not missing and not diffs, detail + (f'; CHANGED: {diffs[:5]}' if diffs else ''))
    # 4 ready
    try:
        eng.send('isready')
        eng.until(lambda l: l == 'readyok', 10)
        check('ready', True, 'readyok')
    except (TimeoutError, EOFError) as e:
        check('ready', False, str(e))
        eng.kill()
        return finish(rep, a, log, t_start)
    # 5 bench at pure defaults
    pins = kv(a.pins)
    bench = {}
    rx = re.compile(r'bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)')
    for d, want in sorted(pins.items(), key=lambda x: int(x[0][1:])):
        depth = int(d[1:])
        try:
            eng.send(f'bench {depth}')
            ls = eng.until(lambda l: rx.search(l) is not None, 240)
            m = rx.search(ls[-1])
            got = int(m.group(2))
            bench[d] = {'nodes': got, 'want': want, 'time_ms': int(m.group(3)), 'nps': int(m.group(4))}
            check(f'bench{depth}', got == want, f'nodes {got} want {want} ({m.group(3)} ms, nps {m.group(4)})')
        except (TimeoutError, EOFError) as e:
            check(f'bench{depth}', False, str(e))
            break
    rep['bench'] = bench
    if failed:
        eng.kill()
        return finish(rep, a, log, t_start)
    # 6 perft
    ppins = kv(a.perft_pins)
    perft = {}
    for name, want in ppins.items():
        pos = 'position startpos' if name == 'startpos' else 'position fen ' + KIWI
        try:
            eng.send(pos)
            eng.send('go perft 5')
            ls = eng.until(lambda l: l.startswith('nodes '), 120)
            got = int(ls[-1].split()[1])
            perft[name] = {'nodes': got, 'want': want}
            check(f'perft', got == want, f'{name} perft 5 nodes {got} want {want}')
        except (TimeoutError, EOFError, ValueError) as e:
            check('perft', False, f'{name}: {e}')
            break
    rep['perft'] = perft
    if failed:
        eng.kill()
        return finish(rep, a, log, t_start)
    # 7 smoke with options set
    import chess
    for o in ('Threads value 1', 'Hash value 16', 'OwnBook value false'):
        eng.send('setoption name ' + o)
    for o in a.opt:
        k, v = o.split('=', 1)
        eng.send(f'setoption name {k} value {v}')
    eng.send('isready')
    try:
        eng.until(lambda l: l == 'readyok', 10)
    except (TimeoutError, EOFError) as e:
        check('smoke', False, f'isready after setoption: {e}')
        eng.kill()
        return finish(rep, a, log, t_start)
    epd = []
    if a.wac and os.path.exists(a.wac):
        with open(a.wac, encoding='utf-8', errors='replace') as f:
            epd = [l.strip() for l in f if l.strip()]
    fens = []
    for l in epd[:a.positions]:
        try:
            b, ops = chess.Board.from_epd(l)
            fens.append(full_fen(b.fen()))
        except ValueError:
            continue
    if len(fens) < a.positions:
        fens += [full_fen(f) for f in BUILTIN_FENS[:a.positions - len(fens)]]
    bad, slow, maxt = [], [], 0.0
    for i, fen in enumerate(fens):
        b = chess.Board(fen)
        eng.send('ucinewgame')
        eng.send('isready')
        try:
            eng.until(lambda l: l == 'readyok', 10)
            nbad = len(eng.bad)
            eng.send('position fen ' + fen)
            eng.send(f'go movetime {a.movetime}')
            t0 = time.monotonic()
            ls = eng.until(lambda l: l.startswith('bestmove'), (a.movetime + 3000) / 1000.0)
            dt = time.monotonic() - t0
            maxt = max(maxt, dt)
            if len(eng.bad) > nbad:
                bad.append(f'pos {i + 1}: engine rejected the input: {eng.bad[-1]!r}')
                continue
            mv = ls[-1].split()[1] if len(ls[-1].split()) > 1 else ''
            legal = [m.uci() for m in b.legal_moves]
            if legal and mv not in legal:
                bad.append(f'pos {i + 1}: bestmove {mv!r} not legal')
            if not legal and mv not in ('0000', '(none)', 'none', ''):
                bad.append(f'pos {i + 1}: no legal move but bestmove {mv!r}')
            if dt > (a.movetime + 1000) / 1000.0:
                slow.append(f'pos {i + 1}: {dt:.2f} s')
        except (TimeoutError, EOFError) as e:
            bad.append(f'pos {i + 1}: {e}')
            break
    check('smoke', not bad, f'{len(fens)} six-field FENs at go movetime {a.movetime}: {len(bad)} bad {bad[:3]}, max {maxt:.2f} s, late {len(slow)} {slow[:3]}')
    if failed:
        eng.kill()
        return finish(rep, a, log, t_start)
    # 8 WAC at fixed nodes
    if epd:
        solved, total, errs, details = 0, 0, [], []
        for l in epd[a.positions:a.positions + a.wac_n]:
            try:
                b, ops = chess.Board.from_epd(l)
            except ValueError:
                continue
            eng.send('ucinewgame')
            eng.send('isready')
            try:
                eng.until(lambda l_: l_ == 'readyok', 10)
                nbad = len(eng.bad)
                eng.send('position fen ' + full_fen(b.fen()))
                eng.send(f'go nodes {a.wac_nodes}')
                ls = eng.until(lambda l_: l_.startswith('bestmove'), 60)
                if len(eng.bad) > nbad:
                    errs.append(f'{ops.get("id", "")}: engine rejected the input: {eng.bad[-1]!r}')
                    break
                mv = chess.Move.from_uci(ls[-1].split()[1])
                ok = (mv in ops.get('bm', []) if 'bm' in ops else True) and mv not in ops.get('am', [])
                total += 1
                solved += ok
                details.append({'id': ops.get('id', ''), 'solved': ok, 'move': b.san(mv)})
            except (TimeoutError, EOFError, ValueError) as e:
                errs.append(str(e))
                break
        rep['wac'] = {'file': a.wac, 'nodes': a.wac_nodes, 'solved': solved, 'total': total, 'details': details}
        check('wac', not errs and solved >= a.wac_min, f'{solved}/{total} solved at go nodes {a.wac_nodes} (floor {a.wac_min}){"; errors " + str(errs) if errs else ""}')
    # 8b any rejected input anywhere in the session (e.g. 'info string invalid FEN') is a FAIL on its own
    check('inputs', not eng.bad, 'no engine line reported a rejected input' if not eng.bad else f'{len(eng.bad)} rejected-input line(s): {eng.bad[:3]}')
    # 9 quit
    eng.send('quit')
    try:
        eng.p.wait(timeout=5)
        check('quit', True, f'exit code {eng.p.returncode}')
    except subprocess.TimeoutExpired:
        eng.kill()
        check('quit', False, 'engine did not exit within 5 s (killed)')
    return finish(rep, a, log, t_start)


def finish(rep, a, log, t_start):
    failed = any(c['result'] == 'FAIL' for c in rep['checks'])
    total = time.monotonic() - t_start
    rep['total_s'] = round(total, 1)
    rep['budget_s'] = a.budget_s
    rep['verdict'] = 'FAIL' if failed else ('SLOW' if total > a.budget_s else 'PASS')
    print(f'pregate_screen: {rep["verdict"]} in {total:.1f} s (budget {a.budget_s:.0f} s): ' +
          ', '.join(f"{c['check']} {c['result']}" for c in rep['checks']))
    if log:
        log.close()
    if a.json:
        with open(a.json, 'w', newline='\n') as f:
            json.dump(rep, f, indent=1)
            f.write('\n')
    return 1 if failed else (3 if total > a.budget_s else 0)


if __name__ == '__main__':
    sys.exit(main())
