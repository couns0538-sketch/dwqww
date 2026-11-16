#!/usr/bin/env python3
"""fuzzuci78.py -- replay every (position, go) pair from long 56's 2,000 sequences, each pair
in a FRESH engine process, and judge the bestmove with python-chess on the position the
engine kept (file 19's rule: read all lines after `position`; a refused FEN keeps the
previous position -- here the start position; a refused move keeps the board up to the last
legal move). One row per pair in out/records.tsv.
Usage: fuzzuci78.py <exe> <outdir> <first> <last> <tag>"""
import chess
import subprocess
import sys
import threading
import time

exe, outdir, first, last, tag = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
import shlex
ARGV = shlex.split(exe)
GRACE_STOP = 1.0
GRACE_BANANA = 0.6

seqs, cur = [], None
for line in open("/tmp/uci56_seqs.txt"):
    line = line.rstrip("\n")
    if line.startswith("### seq "):
        cur = [line]; seqs.append(cur)
    elif cur is not None:
        cur.append(line)

pairs = []
for si, lines in enumerate(seqs):
    pos = None
    for l in lines[1:]:
        if l.startswith("position"):
            pos = l
        elif l.startswith("go") and l.strip() != "go":
            pairs.append((si, pos if pos is not None else "position startpos", l))

def kept_board(posline):
    """python-chess board the engine keeps after `posline`, with the refusal text."""
    toks = posline.split()
    refusal = ""
    try:
        if len(toks) >= 2 and toks[1] == "fen":
            fen = " ".join(toks[2:])
            if " moves " in posline:
                fen = " ".join(toks[2:toks.index("moves")])
            bd = chess.Board(fen)
        elif len(toks) >= 2 and toks[1] == "startpos":
            bd = chess.Board()
        else:
            bd = chess.Board()
    except ValueError:
        return chess.Board(), "refused-fen"
    if " moves " in posline:
        mv = toks[toks.index("moves") + 1:]
        for u in mv:
            try:
                m = chess.Move.from_uci(u)
            except ValueError:
                refusal = "refused-move:" + u
                break
            if not bd.is_legal(m):
                refusal = "refused-move:" + u
                break
            bd.push(m)
    return bd, refusal

def run_pair(i):
    si, pos, go = pairs[i]
    p = subprocess.Popen(ARGV, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    out = []
    def rdo():
        try:
            for l in p.stdout:
                out.append(l)
        except Exception:
            pass
    threading.Thread(target=rdo, daemon=True).start()
    try:
        p.stdin.write("uci\n" + "isready\n"); p.stdin.flush()
        t0 = time.monotonic()
        while time.monotonic() - t0 < 10:
            if any("readyok" in x for x in out[-50:]): break
            time.sleep(0.01)
        p.stdin.write(pos + "\n"); p.stdin.flush()
        time.sleep(0.02)
        refuse = [l.strip() for l in out if "invalid FEN" in l or "illegal move" in l]
        p.stdin.write(go + "\n"); p.stdin.flush()
        t = go.split()
        wait = 20.0
        if "movetime" in t: wait = float(t[t.index("movetime") + 1]) / 1000.0 + 0.4
        if "infinite" in t or "ponder" in t: wait = GRACE_STOP
        if t[1] not in ("depth", "nodes", "movetime", "infinite", "ponder"): wait = GRACE_BANANA
        t0 = time.monotonic(); best = None
        while time.monotonic() - t0 < wait:
            for l in out[::-1]:
                if l.startswith("bestmove"):
                    best = l.split()[1] if len(l.split()) > 1 else "(none)"
                    break
            if best: break
            time.sleep(0.01)
        if not best:
            p.stdin.write("stop\n"); p.stdin.flush()
            t0 = time.monotonic()
            while time.monotonic() - t0 < 5:
                for l in out[::-1]:
                    if l.startswith("bestmove"):
                        best = l.split()[1] if len(l.split()) > 1 else "(none)"
                        break
                if best: break
                time.sleep(0.01)
        p.stdin.write("quit\n"); p.stdin.flush()
    except Exception:
        pass
    p.terminate()
    bd, refusal = kept_board(pos)
    legal = ""
    if best in (None, "(none)"):
        legal = "none"
    elif bd.occupied_co[bd.turn] == 0 or bd.is_game_over():
        legal = "n/a" if best == "0000" or best == "(none)" else "no-legal-moves"
    else:
        try:
            m = chess.Move.from_uci(best)
            legal = "yes" if bd.is_legal(m) else "no"
        except ValueError:
            legal = "unparseable"
    kind = go.split()[1] if len(go.split()) > 1 else "?"
    real = kind in ("depth", "nodes", "movetime")
    return (i, si, pos, go, best if best else "(none)", legal, refusal,
            " ; ".join(refuse[:2]), "real" if real else "other")

if __name__ == "__main__":
    rows = []
    for i in range(first, min(last, len(pairs))):
        r = run_pair(i)
        rows.append(r)
        if r[5] == "no":
            sys.stderr.write(f"ILLEGAL pair {i}: {r}\n")
        if (i - first) % 25 == 0:
            sys.stderr.write(f"[{tag}] {i - first}/{last - first}\n")
    with open(f"{outdir}/records_{tag}.tsv", "w") as f:
        f.write("pair\tseq\tposition\tgo\tbestmove\tlegal\trefusal\tengine_refusal_lines\tclass\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    print(f"{tag}: {len(rows)} rows")
