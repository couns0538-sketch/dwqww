#!/usr/bin/env python3
"""long62.py -- the searchmoves subset runs. Phases:
  plain  <fens> <out> <lo> <hi>   : plain go depth 10 per position -> fen|best|nodes|score
  pairs  <plainfile> <dir>        : build the three pair files from the plain rows
  run    <pairsfile> <out> <lo> <hi> : the restricted runs over a pairs file
One process per position; the full answer log kept."""
import sys, subprocess, threading, queue, time

EXE = "/tmp/glmflash5_base/build/forge"
OPTS = "Threads=1;Hash=16;OwnBook=false"

def engine():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    q = queue.Queue()
    def rd():
        try:
            for l in p.stdout:
                q.put(l)
        except Exception:
            pass
        q.put(None)
    threading.Thread(target=rd, daemon=True).start()
    def send(s): p.stdin.write(s + "\n"); p.stdin.flush()
    def rl(t=2.0):
        try: return q.get(timeout=t)
        except queue.Empty: return ""
    send("uci")
    while True:
        l = rl()
        if not l or l.strip() == "uciok": break
    for o in OPTS.split(";"): send("setoption name " + o.replace("=", " value "))
    send("isready")
    while True:
        l = rl()
        if not l or l.strip() == "readyok": break
    return p, send, rl

def search(send, rl, fen, go_cmd):
    send("ucinewgame"); send("isready")
    while True:
        l = rl()
        if not l or l.strip() == "readyok": break
    send("position fen " + fen)
    send(go_cmd)
    best, nodes, score, lines = None, None, None, []
    t0 = time.time()
    while time.time() - t0 < 30:
        l = rl()
        if not l: continue
        lines.append(l.rstrip("\n"))
        if " nodes " in l and " nps " in l:
            t = l.split()
            for j, tok in enumerate(t):
                if tok == "nodes" and j + 1 < len(t):
                    try: nodes = int(t[j + 1])
                    except ValueError: pass
                if tok == "score" and j + 2 < len(t) and t[j + 1] == "cp":
                    try: score = int(t[j + 2])
                    except ValueError: pass
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
    return best, nodes, score, lines

def phase_plain(fens, out, lo, hi):
    res = []
    p, send, rl = engine()
    for i in range(lo, hi):
        fen = fens[i].strip()
        b, n, s, _ = search(send, rl, fen, "go depth 10")
        res.append(f"{fen} | {b} | {n} | {s}")
        sys.stderr.write(f"[{i}] {b} {n}\n")
    p.stdin.close(); p.terminate()
    with open(out, "w") as f:
        f.write("\n".join(res) + "\n")

def phase_pairs(plainfile, d):
    import chess
    rows = [l.split(" | ") for l in open(plainfile) if l.strip()]
    f1, f2, f3, f0 = [], [], [], []
    for fen, b, n, s in rows:
        b = b.strip()
        bd = chess.Board(fen)
        legal = list(bd.legal_moves)
        lmoves = [m.uci() for m in legal]
        assert b in lmoves, (fen, b)
        other = next((u for u in lmoves if u != b), None)
        frm = b[:2]
        own = [chess.square_name(sq) for sq in chess.scan_forward(bd.occupied_co[bd.turn])]
        tgt = None
        for cand in own:
            if cand != frm:
                tgt = frm + cand
                break
        assert tgt is not None
        f0.append(f"{fen} | {b} | {n} | {s}")
        f1.append(f"{fen} | {b}")
        f2.append(f"{fen} | {b} {other}" if other else f"{fen} | {b}   #single-reply")
        f3.append(f"{fen} | {b} {tgt}")
    open(d + "/pairs_sm1.txt", "w").write("\n".join(f1) + "\n")
    open(d + "/pairs_sm2.txt", "w").write("\n".join(f2) + "\n")
    open(d + "/pairs_sm3.txt", "w").write("\n".join(f3) + "\n")

def phase_run(pairsfile, out, lo, hi):
    res = []
    p, send, rl = engine()
    rows = [l.rstrip("\n") for l in open(pairsfile) if l.strip()]
    for i in range(lo, hi):
        line = rows[i]
        fen, _, mv = line.partition(" | ")
        go = f"go depth 10 searchmoves {mv.strip()}" if mv.strip() else "go depth 10"
        b, n, s, lines = search(send, rl, fen, go)
        keep = [l for l in lines if l.startswith(("bestmove", "info string")) or "illegal" in l.lower()]
        res.append(f"#{i} | {fen} | go=[{go}] | best={b} | nodes={n} | score={s} | lines={' ;; '.join(keep[:3])}")
        sys.stderr.write(f"[{i}] best={b}\n")
    p.stdin.close(); p.terminate()
    with open(out, "w") as f:
        f.write("\n".join(res) + "\n")

if __name__ == "__main__":
    ph = sys.argv[1]
    if ph == "plain":
        fens = open(sys.argv[2]).read().splitlines()
        phase_plain(fens, sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
    elif ph == "pairs":
        phase_pairs(sys.argv[2], sys.argv[3])
    elif ph == "run":
        rows = open(sys.argv[2]).read().splitlines()
        phase_run(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
