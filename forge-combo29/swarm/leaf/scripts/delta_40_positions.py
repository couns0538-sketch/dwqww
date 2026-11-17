"""Node-count delta base vs fixed on 40 ordinary positions.

If the fix secretly searched one ply deeper everywhere, every position would move.
A leaf-rule fix that only fires at clock>=100 must leave all 40 node-identical
and score-identical, because none of them has a clock anywhere near 100.
"""
import json, re, subprocess, sys, threading, queue, time

import os
POS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "positions40.json")))
DEPTH = int(sys.argv[3]) if len(sys.argv) > 3 else 14

def ask(exe, posline, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l.rstrip()) for l in p.stdout] or q.put(None), daemon=True).start()
    p.stdin.write(f"uci\nisready\nsetoption name Threads value 1\nsetoption name Hash value 16\n"
                  f"setoption name OwnBook value false\n{posline}\nisready\ngo depth {depth}\n")
    p.stdin.flush()
    lines, t0 = [], time.monotonic()
    while time.monotonic() - t0 < 300:
        try: ln = q.get(timeout=0.5)
        except queue.Empty:
            if p.poll() is not None: break
            continue
        if ln is None: break
        lines.append(ln)
        if ln.startswith("bestmove"): break
    try: p.stdin.write("quit\n"); p.stdin.flush(); p.stdin.close()
    except OSError: pass
    try: p.wait(timeout=10)
    except subprocess.TimeoutExpired: p.kill()
    infos = [l for l in lines if l.startswith("info depth")]
    last = infos[-1] if infos else ""
    bm = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
    n = re.search(r" nodes (\d+)", last); s = re.search(r"score (cp|mate) (-?\d+)", last)
    return {"nodes": int(n.group(1)) if n else None,
            "score": f"{s.group(1)} {s.group(2)}" if s else None, "bestmove": bm}

base_exe, fix_exe = sys.argv[1], sys.argv[2]
rows, deltas = [], []
print(f"{'#':>2} {'kind':5} {'base_nodes':>10} {'fix_nodes':>10} {'d%':>7} {'base_score':>10} {'fix_score':>10} {'bm==':>4}")
for i, pos in enumerate(POS):
    b = ask(base_exe, pos["posline"], DEPTH)
    f = ask(fix_exe, pos["posline"], DEPTH)
    d = 0.0 if (b["nodes"] in (None, 0) or f["nodes"] in (None, 0)) else 100.0*(f["nodes"]-b["nodes"])/b["nodes"]
    deltas.append(d)
    rows.append({"i": i, "kind": pos["kind"], "posline": pos["posline"], "depth": DEPTH,
                 "base": b, "fixed": f, "delta_pct": d})
    print(f"{i:2} {pos['kind']:5} {str(b['nodes']):>10} {str(f['nodes']):>10} {d:7.3f} "
          f"{str(b['score']):>10} {str(f['score']):>10} {str(b['bestmove']==f['bestmove']):>4}")
ident = sum(1 for r in rows if r["base"]["nodes"] == r["fixed"]["nodes"] and r["base"]["score"] == r["fixed"]["score"])
print(f"\nnode+score identical: {ident}/40")
print(f"positions with any node delta: {sum(1 for d in deltas if abs(d) > 1e-9)}/40")
print(f"max |delta%|: {max(abs(d) for d in deltas):.4f}")
json.dump({"depth": DEPTH, "rows": rows, "identical": ident, "max_abs_delta_pct": max(abs(d) for d in deltas)},
          open(sys.argv[4], "w"), indent=1)
