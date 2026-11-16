#!/usr/bin/env python3
"""perft_cmp.py -- the engine's move generator against python-chess.
Usage: perft_cmp.py ENGINE SETFILE PERFT_DEPTH [LIMIT]
One engine process per position (the rows form). Compares per position; writes the table."""
import subprocess
import sys
import time

exe, setfile, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
limit = int(sys.argv[4]) if len(sys.argv) > 4 else None
import chess

def engine_perft(exe, fen, d):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    out = []
    def rd():
        try:
            for l in p.stdout:
                out.append(l)
        except Exception:
            pass
    import threading
    threading.Thread(target=rd, daemon=True).start()
    p.stdin.write(f"uci\nisready\nposition fen {fen}\ngo perft {d}\nquit\n")
    p.stdin.flush()
    p.wait(timeout=300)
    best = None
    for l in reversed(out):
        l = l.strip()
        if l.startswith("bestmove"):
            continue
        if " nodes " in l or l.startswith("nodes ") or "perft" in l.lower():
            t = l.split()
            for k, tok in enumerate(t):
                if tok in ("nodes", "perft") and k + 1 < len(t) and t[k+1].isdigit():
                    best = int(t[k+1])
        if l.startswith("info string") and "nodes" in l:
            t = l.split()
            try:
                best = int(t[t.index("nodes") + 1])
            except Exception:
                pass
    return best, "\n".join(out)

fens = [l.strip() for l in open(setfile, encoding="utf-8", errors="replace") if l.strip()]
if limit:
    fens = fens[:limit]
eq = diff = 0
diff_rows = []
for i, fen in enumerate(fens):
    ecount, raw = engine_perft(exe, fen, depth)
    b = chess.Board(fen)
    pcount = b.perft(depth)
    if ecount == pcount:
        eq += 1
    else:
        diff += 1
        diff_rows.append((i, fen, ecount, pcount, raw))
print(f"equal {eq}, differ {diff}, total {eq + diff} (perft {depth})")
for i, fen, e, p_, raw in diff_rows[:20]:
    print(f"DIFF pos {i}: engine {e} python-chess {p_} fen {fen}")
for i, fen, e, p_, raw in diff_rows:
    if len(diff_rows) <= 20:
        break
if diff_rows and len(diff_rows) > 20:
    print(f"... {len(diff_rows) - 20} more differing rows in the full table file")
import json
open("/tmp/perft_diffs.json", "w").write(json.dumps(
    [{"pos": i, "fen": f, "engine": e, "python": p_} for i, f, e, p_, _ in diff_rows]))
