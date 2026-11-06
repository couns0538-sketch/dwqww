"""box_run.py - counter-build box test of one port, option OFF vs ON (own code, 2026-11-06, leftover checks).

usage: python -I -B box_run.py --port cnl|tcn|ntc --exe <counter build exe> --on "A=1,B=2" --out <new dir> [--mask 0xC]
- Own process: Idle class + the CPU mask (children inherit), both read back; fail closed.
- bench 16 OFF and ON at the defaults (+ ON options): nodes must equal the gate exe's pins (counters must not change search).
- Spec box FENs F1-F5 at go depth 16 and sanity FENs S1-S5 at depth 12, OFF and ON, ONE PROCESS PER FEN (Hash 16,
  Threads 1, OwnBook false, ucinewgame): depth / score / nodes / bestmove of the last info line + the exit-time
  'info string spec_counters ...' line. Bestmove legality by python-chess. Report = table + flags, no verdict.
"""
import argparse, ctypes, json, subprocess, sys, time
from pathlib import Path
import chess

FENS = [
    ('F1', 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', 16),
    ('F2', 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1', 16),
    ('F3', '8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1', 16),
    ('F4', '2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1', 16),
    ('F5', 'r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9', 16),
    ('S1', '6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1', 12),
    ('S2', '7k/5Q2/6K1/8/8/8/8/8 b - - 0 1', 12),
    ('S3', '7k/8/4Q2K/8/8/8/8/8 w - - 0 1', 12),
    ('S4', '8/8/8/4k3/8/8/8/3QK3 w - - 99 200', 12),
    ('S5', '7k/8/6K1/8/8/8/8/R7 w - - 99 150', 12),
]
BENCH_ON_D16 = {'cnl': 2738962, 'tcn': 3049356, 'ntc': 3034926}   # gate exe pin_check -Full ON (BENCH.md)
BENCH_OFF_D16 = 3024920                                              # lock / trial_w6 pin


def place(mask: int) -> None:
    k = ctypes.windll.kernel32
    # explicit types: without them ctypes truncates the 64-bit pseudo-handle to a C int and every call fails
    k.GetCurrentProcess.restype = ctypes.c_void_p
    k.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    k.GetPriorityClass.argtypes = [ctypes.c_void_p]
    k.GetPriorityClass.restype = ctypes.c_uint32
    k.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    k.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
    h = k.GetCurrentProcess()
    if not k.SetPriorityClass(h, 0x40) or k.GetPriorityClass(h) != 0x40:
        sys.exit('placement: Idle class not applied')
    if not k.SetProcessAffinityMask(h, ctypes.c_size_t(mask)):
        sys.exit('placement: affinity not applied')
    pm, sm = ctypes.c_size_t(), ctypes.c_size_t()
    k.GetProcessAffinityMask(h, ctypes.byref(pm), ctypes.byref(sm))
    if pm.value != mask:
        sys.exit(f'placement: affinity read back 0x{pm.value:X}')


def run(exe, opts, cmds, stop_pat, log):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines = []

    def send(s):
        p.stdin.write(s + '\n'); p.stdin.flush(); lines.append('> ' + s)

    def until(pat):
        while True:
            l = p.stdout.readline()
            if not l:
                raise RuntimeError(f'engine closed before {pat!r}')
            l = l.rstrip('\n'); lines.append(l)
            if l.startswith(pat):
                return l
    send('uci'); until('uciok')
    for kv in opts:
        n, v = kv.split('=', 1); send(f'setoption name {n} value {v}')
    send('isready'); until('readyok')
    for c in cmds:
        send(c)
    stop = until(stop_pat)
    send('quit')
    rest = p.stdout.read().splitlines(); lines += rest
    p.wait(timeout=60)
    log.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    cnt = [l for l in lines if l.startswith('info string spec_counters')]
    return lines, stop, (cnt[-1] if cnt else '')


def parse_counters(line):
    t = line.split()[3:]
    out, i, prefix = {}, 0, ''
    while i < len(t):
        if i + 1 < len(t) and t[i + 1].lstrip('-').isdigit():
            out[prefix + t[i]] = int(t[i + 1]); i += 2
        else:
            prefix = t[i] + '_'; i += 1
    return out


def fires(port, c):
    if port == 'cnl':
        return c.get('applied', 0)
    if port == 'tcn':
        return sum(v for k, v in c.items() if 'refused' in k)
    return c.get('blocked', 0)


def odd(port, c, on):
    """Rule-shape checks that must hold for every search (empty list = nothing odd)."""
    bad = []
    if port == 'cnl' and on and c.get('applied') != c.get('lmr_cut_nott'):
        bad.append('applied != lmr_cut_nott')
    if port == 'tcn':
        if c.get('d7+_refused_high_noncut', 0) or c.get('d7+_refused_low_cut', 0):
            bad.append('refused at depth 7+')
        if on and sum(v for k, v in c.items() if 'refused_low_cut' in k):
            bad.append('fail-low refused under form 1')
    if port == 'ntc' and on and any(c.get(f'blocked_v{t}', 0) for t in (1, 2, 3)):
        bad.append('blocked a victim below type 4')
    if not on and fires(port, c):
        bad.append('rule fired with the option OFF')
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', required=True, choices=['cnl', 'tcn', 'ntc'])
    ap.add_argument('--exe', required=True)
    ap.add_argument('--on', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--mask', default='0xC')
    a = ap.parse_args()
    place(int(a.mask, 16))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    on_opts = [x for x in a.on.split(',') if x]
    summ, flags, rows = [], [], []
    summ.append(f'box_run {time.strftime("%Y-%m-%d %H:%M:%S")}: port {a.port} exe {a.exe} ON {",".join(on_opts)} mask {a.mask}')
    for side in (0, 1):
        opts = on_opts if side else []
        _, stop, cl = run(a.exe, opts, ['bench 16'], 'info string bench depth 16', out / f'bench16_on{side}.log')
        n = int(stop.split(' nodes ')[1].split()[0])
        want = BENCH_ON_D16[a.port] if side else BENCH_OFF_D16
        ok = n == want
        if not ok:
            flags.append(f'bench 16 side {side}: {n} != gate {want}')
        summ.append(f'bench 16 {"ON " if side else "OFF"}: nodes {n} (gate exe {want}) {"OK" if ok else "DIFF"}; counters {cl[26:]}')
    res = {}
    for fid, fen, d in FENS:
        for side in (0, 1):
            opts = ['OwnBook=false', 'Hash=16', 'Threads=1'] + (on_opts if side else [])
            lines, stop, cl = run(a.exe, opts, ['ucinewgame', 'isready', f'position fen {fen}', f'go depth {d}'],
                                  'bestmove', out / f'{fid}_on{side}.log')
            info = [l for l in lines if l.startswith('info depth ')]
            last = info[-1].split() if info else []
            g = lambda k: last[last.index(k) + 1] if k in last else ''
            score = (g('score') + ' ' + last[last.index('score') + 2]) if 'score' in last else ''
            best = stop.split()[1]
            b = chess.Board(fen)
            legal = (best == '0000' and not any(b.legal_moves)) or (best != '0000' and chess.Move.from_uci(best) in b.legal_moves)
            c = parse_counters(cl) if cl else {}
            res[(fid, side)] = dict(depth=g('depth'), score=score, nodes=int(g('nodes') or 0), best=best, legal=legal, c=c)
            rows.append(json.dumps(dict(fen=fid, side=side, **res[(fid, side)])))
            if not legal:
                flags.append(f'{fid} side {side}: illegal bestmove {best}')
            if not cl:
                flags.append(f'{fid} side {side}: no counters line')
            for x in odd(a.port, c, side == 1):
                flags.append(f'{fid} side {side}: {x}')
    (out / 'box_rows.jsonl').write_text('\n'.join(rows) + '\n', encoding='utf-8', newline='\n')
    tot = {0: {}, 1: {}}
    tn = {0: 0, 1: 0}
    for fid, fen, d in FENS:
        r0, r1 = res[(fid, 0)], res[(fid, 1)]
        ratio = r1['nodes'] / r0['nodes'] if r0['nodes'] else 0.0
        if fid.startswith('F') and not 0.5 <= ratio <= 2.0:
            flags.append(f'{fid}: ON/OFF node ratio {ratio:.2f} outside 0.5-2x')
        summ.append(f'{fid} d{d}: OFF {r0["score"]:<9} {r0["best"]:<5} n {r0["nodes"]:>9} | ON {r1["score"]:<9} {r1["best"]:<5} '
                    f'n {r1["nodes"]:>9} | ratio {ratio:.3f} | fires OFF {fires(a.port, r0["c"])} ON {fires(a.port, r1["c"])}')
        if fid.startswith('F'):
            for s in (0, 1):
                tn[s] += res[(fid, s)]['nodes']
                for k, v in res[(fid, s)]['c'].items():
                    tot[s][k] = tot[s].get(k, 0) + v
    summ.append(f'F1-F5 nodes OFF {tn[0]} ON {tn[1]} (ON/OFF {tn[1] / tn[0]:.3f}); counters per 1M nodes, OFF -> ON:')
    for k in tot[0]:
        summ.append(f'  {k:<28} {tot[0][k] * 1e6 / tn[0]:>10.1f} -> {tot[1].get(k, 0) * 1e6 / tn[1]:>10.1f}')
    s3 = res[('S3', 0)]['best'], res[('S3', 1)]['best']
    if any(m not in ('e6e8', 'e6c8') for m in s3):
        flags.append(f'S3 bestmove {s3} not e6e8 / e6c8')
    f3 = res[('F3', 0)], res[('F3', 1)]
    if f3[0]['score'].split()[0] != f3[1]['score'].split()[0] or f3[0]['best'] != f3[1]['best']:
        summ.append(f'note: F3 score class / move OFF {f3[0]["score"]} {f3[0]["best"]} vs ON {f3[1]["score"]} {f3[1]["best"]}')
    summ.append('FLAGS: ' + ('none' if not flags else '; '.join(flags)))
    (out / 'SUMMARY.txt').write_text('\n'.join(summ) + '\n', encoding='utf-8', newline='\n')
    print('\n'.join(summ))
    return 0 if not flags else 3


if __name__ == '__main__':
    sys.exit(main())
