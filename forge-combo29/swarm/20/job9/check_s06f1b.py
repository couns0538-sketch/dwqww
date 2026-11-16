#!/usr/bin/env python3
"""check_s06f1b.py — seat 20, area 10 job 9, SECOND attempt: check of seat 06's S-F1 with the
sign convention ESTABLISHED by measurement first, not assumed.

ESTABLISHED CONVENTION (measured, see convention.txt):
  `eval` is relative to the SIDE TO MOVE. A board with four white queens next to a lone black king reads
  hce 4211 when WHITE is to move and hce -4182 when BLACK is to move; the colour-mirrored board with BLACK to
  move reads hce 4211 too. So the same advantage reads the same number whether it is White's or Black's.
  => Colour symmetry therefore means: eval(position) == eval(mirror(position)), NOT the negation.

usage: check_s06f1b.py <exe> <outdir> [fenfile]
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
import random

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
FENFILE = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(OUT, exist_ok=True)


def eval_line(fen, opts=(), timeout=25.0):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []
    lock = threading.Lock()

    def rd():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass
    threading.Thread(target=rd, daemon=True).start()
    for line in (["uci", "setoption name OwnBook value false"] + list(opts) +
                 ["isready", f"position fen {fen}", "eval"]):
        p.stdin.write(line + "\n")
        p.stdin.flush()
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        with lock:
            if any(x.startswith("info string eval") for x in out):
                break
        time.sleep(0.002)
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=10)
    except Exception:
        p.kill()
    with lock:
        for x in out:
            if x.startswith("info string eval"):
                return x
    return None


def nums(line):
    if not line:
        return None
    h = re.search(r"hce (-?\d+)", line)
    n = re.search(r"nnue (-?\d+)", line)
    t = re.search(r"total (-?\d+)", line)
    if not (h and n and t):
        return None
    return {"hce": int(h.group(1)), "nnue": int(n.group(1)), "total": int(t.group(1))}


SEED = 2001


def my_positions(n=60):
    r = random.Random(SEED)
    out, b = [], chess.Board()
    while len(out) < n:
        mv = list(b.legal_moves)
        if not mv or b.is_game_over():
            b = chess.Board()
            continue
        b.push(r.choice(mv))
        if b.ply() % 5 == 0:
            out.append(b.fen())
    return out


fens = my_positions(60)
src = "my own 60 (Random(2001), one every 5 plies)"
if FENFILE and os.path.exists(FENFILE):
    good = []
    for l in open(FENFILE, encoding="utf-8", errors="replace"):
        if not l.strip():
            continue
        f = " ".join(l.split()[:6])
        try:
            chess.Board(f)
            good.append(f)
        except ValueError:
            pass
        if len(good) >= 60:
            break
    fens += good
    src += f" + {len(good)} from {os.path.basename(FENFILE)}"

CONFIGS = [("default", ()),
           ("nnue_off", ("setoption name UseNNUE value false",)),
           ("deadmaterial_on", ("setoption name DeadMaterial value true",))]

print(f"exe {EXE}")
print(f"positions {len(fens)}  ({src})")
print(f"convention: eval is SIDE-TO-MOVE relative, so symmetry = mirror eval EQUALS the eval")
print()
print(f"{'config':18s} {'pairs':>6s} {'symmetric':>10s} {'asymmetric':>11s} {'max|hce diff|':>14s} "
      f"{'max|nnue diff|':>15s} {'max|total diff|':>16s}")
res = {"exe": EXE, "source": src, "convention": "side-to-move relative; symmetry means equal",
       "configs": {}, "diffs": []}
for cname, opts in CONFIGS:
    sym = asym = 0
    mx = {"hce": 0, "nnue": 0, "total": 0}
    diffs = []
    for fen in fens:
        m = chess.Board(fen).mirror().fen()
        a = nums(eval_line(fen, opts))
        b = nums(eval_line(m, opts))
        if a is None or b is None:
            continue
        d = {k: a[k] - b[k] for k in a}
        if d["hce"] == 0 and d["nnue"] == 0 and d["total"] == 0:
            sym += 1
        else:
            asym += 1
            for k in mx:
                mx[k] = max(mx[k], abs(d[k]))
            diffs.append({"fen": fen, "mirror": m, "self": a, "mirror_eval": b, "diffs": d})
    print(f"{cname:18s} {len(fens):6d} {sym:10d} {asym:11d} {mx['hce']:14d} {mx['nnue']:15d} {mx['total']:16d}")
    res["configs"][cname] = {"symmetric": sym, "asymmetric": asym, "max_diff": mx}
    res["diffs"] += [dict(x, config=cname) for x in diffs]

# CONTROLS: (1) same position twice -> diff 0; (2) a deliberately different position -> diff != 0
print()
print("controls:")
c1 = nums(eval_line(fens[0]))
c1b = nums(eval_line(fens[0]))
print(f"  same position twice: {c1} vs {c1b} -> "
      f"{'EQUAL' if c1 == c1b else 'DIFFERENT'}")
other = chess.Board(fens[0]).mirror()
other.push(random.Random(7).choice(list(other.legal_moves)))
c2 = nums(eval_line(other.fen()))
print(f"  a DIFFERENT position: self {c1['total']} vs other {c2['total']} -> "
      f"{'EQUAL (harness blind!)' if c1['total'] == c2['total'] else 'different (harness sees a change)'}")
res["controls"] = {"same_twice": [c1, c1b], "different_position": c2}

with open(os.path.join(OUT, "check_s06f1b.json"), "w") as f:
    json.dump(res, f, indent=1)
print()
print(f"asymmetric pairs: {len(res['diffs'])}")
for d in res["diffs"][:8]:
    print(f"  {d['config']}: {d['fen']}")
    print(f"     self {d['self']}  mirror {d['mirror_eval']}  diffs {d['diffs']}")
print("\nwrote check_s06f1b.json")
