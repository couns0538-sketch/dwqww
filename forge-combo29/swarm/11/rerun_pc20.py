#!/usr/bin/env python3
"""rerun_pc20.py EXE BUILDNAME — re-run seat 11's finds on a build under PC20.

Each block prints the find id, what it was on the base tree, and what happens now.
A "repaired on the PC" verdict requires the NEW behaviour to be positively observed, never
inferred from an absent line.
"""
import os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine
from pc20 import PC20_LINES, describe

EXE = sys.argv[1]
BUILD = sys.argv[2] if len(sys.argv) > 2 else "?"


class ME(Exception):
    pass


def probe(fen, go="go depth 5", opts=None):
    e = Engine(EXE, options=opts if opts is not None else [], timeout=300)
    e.start()
    try:
        ans, refused = e.position(fen=fen)
        if refused:
            return {"refused": refused[0] if refused else "REFUSED"}
        if go.startswith("go perft"):
            e.send(go)
            lines = e.read_until("nodes ")
            for l in lines:
                m = re.match(r"nodes (\d+)", l)
                if m:
                    return {"nodes": int(m.group(1))}
            raise ME(f"no nodes for {fen}")
        infos, bm, _ = e.go(go)
        if bm is None:
            raise ME("no bestmove")
        score = nodes = None
        for l in infos:
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                score = (m.group(1), int(m.group(2)))
            m2 = re.search(r"nodes (\d+)", l)
            if m2:
                nodes = int(m2.group(1))
        return {"bestmove": bm, "score": score, "nodes": nodes, "n_info": len(infos)}
    finally:
        e.quit()


print(f"build: {BUILD}   exe: {EXE}")
print(f"settings: {describe()}")
print("=" * 100)

# ---- S-F1: extra token silently dropped (reporting defect; board identical) -------------
print("\n[S-F1] `position fen ... zzz` is silently accepted; board should equal the 6-field form")
for label, fen in (("clean", "4k3/8/8/8/8/8/8/R3K3 w - - 0 1"),
                   ("junk appended", "4k3/8/8/8/8/8/8/R3K3 w - - 0 1 zzz")):
    try:
        r = probe(fen, go="go perft 1", opts=PC20_LINES)
    except ME as exc:
        print(f"  {label:16} MEASUREMENT FAILED: {exc}")
        continue
    print(f"  {label:16} -> {r}")

# ---- S-F8: setoption without the `value` word ------------------------------------------
print("\n[S-F8] `setoption name UseNNUE false` (no `value` word) was silently ignored")
for label, opts in (("with value", PC20_LINES + ["setoption name UseNNUE value false"]),
                    ("without value", PC20_LINES + ["setoption name UseNNUE false"])):
    e = Engine(EXE, options=[], timeout=180)
    e.start()
    try:
        for line in opts:
            e.send(line)
        e.send("isready")
        ans = e.read_until("readyok")
        e.send("eval")
        time.sleep(0.4)
        ev = []
        while True:
            try:
                l = e.q.get(timeout=0.6)
            except Exception:
                break
            if l is None:
                break
            if "info string eval" in l:
                ev.append(l)
                break
        bad = [l for l in ans if "invalid" in l or "unknown" in l]
        print(f"  {label:14} eval={ev[0] if ev else 'NONE'}  complaint_lines={bad}")
    finally:
        e.quit()

# ---- S-F10/S-F18: the halfmove-100 family ----------------------------------------------
print("\n[S-F10/S-F18] halfmove clock: is the drawn/mate-losing root adjudication still there?")
WHITE_MATE = "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - {h} 1"
KRK = "1K6/8/8/3R4/8/8/8/k7 w - - {h} 1"
for label, tpl, hs in (("mate in 1 on board", WHITE_MATE, (99, 100)),
                       ("KRvK (no mate available)", KRK, (99, 100))):
    for h in hs:
        try:
            r = probe(tpl.format(h=h), go="go depth 5", opts=PC20_LINES)
        except ME as exc:
            print(f"  {label:26} H={h:3} MEASUREMENT FAILED: {exc}")
            continue
        b = chess.Board(tpl.format(h=h))
        mate = False
        if "bestmove" in r:
            try:
                mv = chess.Move.from_uci(r["bestmove"])
                if mv in b.legal_moves:
                    b.push(mv)
                    mate = b.is_checkmate()
            except Exception:
                pass
        print(f"  {label:26} H={h:3} -> {r}  mate_delivered={mate}")

print("\n" + "=" * 100)
print("Nothing above is a verdict by itself; each line is raw behaviour on THIS build.")
