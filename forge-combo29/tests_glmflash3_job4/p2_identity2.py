#!/usr/bin/env python3
# P2: identity proof. For one engine binary: for each of the first 2000 FENs of
# UHO_Lichess_4852_v1.epd, fresh process not required per job (ucinewgame before each):
# ucinewgame, position fen <FEN>, go depth 9; record one answer line
#   bestmove <bm> score <cp|mate N> nodes <n>
# per position. Print sha256 over all answer lines and the smallest node count.
import hashlib
import subprocess
import sys

def answers(exe, fens_path, out_path):
    fens = [l.strip() for l in open(fens_path) if l.strip()][:2000]
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True)
    lines = []
    min_nodes = None

    def send(s):
        p.stdin.write(s + '\n')
        p.stdin.flush()

    def until_bestmove():
        best = None
        score = None
        nodes = None
        while True:
            line = p.stdout.readline()
            if not line:
                raise RuntimeError('engine closed output')
            t = line.strip()
            if t.startswith('bestmove'):
                best = t.split()[1]
                break
            if 'score cp' in t:
                score = t.split('score cp')[1].split()[0]
            elif 'score mate' in t:
                score = 'mate' + t.split('score mate')[1].split()[0]
            if ' nodes ' in t:
                try:
                    nodes = int(t.split(' nodes ')[1].split()[0])
                except (ValueError, IndexError):
                    pass
        return best, score, nodes

    send('uci')
    # wait for uciok
    while True:
        line = p.stdout.readline()
        if line.startswith('uciok'):
            break
    extra = sys.argv[4] if len(sys.argv) > 4 else ''
    if extra:
        send(extra)
    send('isready')
    while True:
        if p.stdout.readline().startswith('readyok'):
            break
    for fen in fens:
        send('ucinewgame')
        send('isready')
        while True:
            if p.stdout.readline().startswith('readyok'):
                break
        send('position fen ' + fen)
        send('go depth 9')
        best, score, nodes = until_bestmove()
        if nodes is not None and (min_nodes is None or nodes < min_nodes):
            min_nodes = nodes
        lines.append(f'bestmove {best} score {score} nodes {nodes}')
    send('quit')
    p.wait(timeout=30)
    text = '\n'.join(lines) + '\n'
    with open(out_path, 'w') as f:
        f.write(text)
    digest = hashlib.sha256(text.encode()).hexdigest()
    print(f'{exe}: positions={len(lines)} sha256={digest} min_nodes={min_nodes}')
    return digest

if __name__ == '__main__':
    answers(sys.argv[1], sys.argv[2], sys.argv[3])
