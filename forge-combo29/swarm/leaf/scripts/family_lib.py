"""Shared UCI client for the family and band harnesses. No globals; import and call ask()/board_after().

Each family is a pair: the position that MUST be repaired and a near-miss that
MUST NOT behave as if it were. Verified with python-chess, never the engine's own score.
"""
import json, re, queue, subprocess, sys, threading, time
import chess

def ask(exe, posline, depth=12):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l.rstrip()) for l in p.stdout] or q.put(None), daemon=True).start()
    p.stdin.write(f"uci\nisready\nsetoption name Threads value 1\nsetoption name Hash value 16\n"
                  f"setoption name OwnBook value false\n{posline}\nisready\ngo depth {depth}\n")
    p.stdin.flush()
    lines, t0 = [], time.monotonic()
    while time.monotonic() - t0 < 120:
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
    n = re.search(r" nodes (\d+)", last); s = re.search(r"score (cp|mate) (-?\d+)", last)
    return {"nodes": int(n.group(1)) if n else None, "score": f"{s.group(1)} {s.group(2)}" if s else None,
            "bestmove": next((l.split()[1] for l in lines if l.startswith("bestmove")), None),
            "san": [l for l in lines if "AddressSanitizer" in l or "runtime error" in l]}

def board_after(posline):
    m = re.match(r"position fen (\S+ \S+ \S+ \S+ \S+ \S+)", posline)
    b = chess.Board(m.group(1))
    mv = re.search(r" moves (.+)$", posline)
    if mv:
        for x in mv.group(1).split(): b.push_uci(x)
    return b

OUT = []
def case(fam, name, posline, expect):
    r = ask(exe, posline)
    b = board_after(posline)
    mate_by_bm = None
    if r["bestmove"]:
        try:
            b.push_uci(r["bestmove"]); mate_by_bm = b.is_checkmate(); b.pop()
        except ValueError: mate_by_bm = "bad"
    # independent: does the side to move have a mate in one at all?
    has_m1 = any((b.push(m) or b.is_checkmate() or b.pop() is None) and b.is_checkmate() for m in list(b.legal_moves))
    b2 = board_after(posline); m1 = []
    for m in list(b2.legal_moves):
        b2.push(m)
        if b2.is_checkmate(): m1.append(m.uci())
        b2.pop()
    ok = expect(r, m1, mate_by_bm, r["nodes"])
    OUT.append({"family": fam, "case": name, "expect": expect.__doc__, "posline": posline,
                "result": r, "oracle_mate_in_1": m1, "bestmove_mates": mate_by_bm, "pass": ok})
    print(f"{'PASS' if ok else 'FAIL':4} {fam:22} {name:22} bm={str(r['bestmove']):6} score={str(r['score']):9} nodes={str(r['nodes']):>7} oracle_m1={m1}")
    return ok
