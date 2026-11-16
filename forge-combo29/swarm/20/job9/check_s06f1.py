#!/usr/bin/env python3
"""check_s06f1.py — seat 20, area 10 job 9: my OWN check of seat 06's S-F1.

Claim (seat 06, S-F1): "`eval` is exactly colour-symmetric: 0 differences in hce/nnue/total over 8,103
position-pairs across 4 eval configurations".

I do not use their positions. I use:
  * 40 positions of my own making (a fixed walk of legal positions by my own seed), plus
  * the O opening set from the kimi5 branch if present (it is a shared input on the branch, not seat 06's set).
For each: the engine's `eval` line on the position and on python-chess's `board.mirror()` (colour flip).
Colour symmetry means total(mirror) = -total(original), hce(mirror) = -hce(original), same for nnue.
A control: the position against ITSELF must give difference 0 in the value sense (equal, not negated) - this
proves the harness can tell equal from negated.

usage: check_s06f1.py <exe> <outdir> [fenfile]
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
FENFILE = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(OUT, exist_ok=True)


def eval_of(lines_pre, timeout=20.0):
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
    for line in lines_pre:
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


def parse_eval(line):
    if not line:
        return None
    h = re.search(r"hce (-?\d+)", line)
    n = re.search(r"nnue (-?\d+)", line)
    t = re.search(r"total (-?\d+)", line)
    if not (h and n and t):
        return None
    return {"hce": int(h.group(1)), "nnue": int(n.group(1)), "total": int(t.group(1)),
            "incheck": "incheck 1" in line}


def ev(exe, fen, opts=()):
    pre = ["uci", "setoption name OwnBook value false"] + list(opts) + ["isready", f"position fen {fen}", "eval"]
    return parse_eval(eval_of(pre))


SEED = 2001
rng_seed = SEED


def my_positions(n=40):
    """a fixed walk of legal positions by my own seed: play pseudo-random legal plies and sample."""
    import random
    r = random.Random(SEED)
    out = []
    b = chess.Board()
    while len(out) < n:
        moves = list(b.legal_moves)
        if not moves or b.is_game_over():
            b = chess.Board()
            continue
        b.push(r.choice(moves))
        if b.ply() % 7 == 0:
            out.append(b.fen())
    return out


fens = my_positions(40)
source = "my own 40 (seed 2001, one every 7 plies)"
if FENFILE and os.path.exists(FENFILE):
    extra = [l.strip() for l in open(FENFILE, encoding="utf-8", errors="replace") if l.strip()][:40]
    # keep only the FEN part of an EPD line
    extra = [" ".join(l.split()[:6]) for l in extra if len(l.split()) >= 4]
    good = []
    for f in extra:
        try:
            chess.Board(f)
            good.append(f)
        except ValueError:
            pass
    fens += good
    source += f" + first {len(good)} of {os.path.basename(FENFILE)}"

CONFIGS = [
    ("default", ()),
    ("nnue_off", ("setoption name UseNNUE value false",)),
    ("deadmaterial_on", ("setoption name DeadMaterial value true",)),
]

print(f"exe {EXE}")
print(f"positions: {len(fens)} ({source})")
print()
print(f"{'config':18s} {'pairs':>6s} {'sym':>5s} {'asym':>5s} {'mirror_invalid':>14s} "
      f"{'max |d_total|':>14s} {'control_diffs':>14s}")
res = {"exe": EXE, "source": source, "configs": {}, "diffs": []}

for cname, opts in CONFIGS:
    sym = asym = bad = 0
    maxd = 0
    diffs = []
    control_diffs = 0
    for fen in fens:
        b = chess.Board(fen)
        m = b.mirror()           # python-chess colour flip
        a = ev(EXE, fen, opts)
        c = ev(EXE, m.fen(), opts)
        if a is None or c is None:
            bad += 1
            continue
        d = {"total": a["total"] + c["total"], "hce": a["hce"] + c["hce"], "nnue": a["nnue"] + c["nnue"]}
        if a["total"] == -c["total"] and a["hce"] == -c["hce"] and a["nnue"] == -c["nnue"]:
            sym += 1
        else:
            asym += 1
            maxd = max(maxd, abs(d["total"]))
            diffs.append({"fen": fen, "mirror": m.fen(), "self": a, "mirror_eval": c, "sums": d})
        # control: the position against itself (equal, not negated)
        a2 = ev(EXE, fen, opts)
        if a2 is None or a2["total"] != a["total"] or a2["hce"] != a["hce"]:
            control_diffs += 1
    print(f"{cname:18s} {len(fens):6d} {sym:5d} {asym:5d} {bad:14d} {maxd:14d} {control_diffs:14d}")
    res["configs"][cname] = {"sym": sym, "asym": asym, "invalid": bad, "max_abs_d_total": maxd,
                            "control_diffs": control_diffs}
    res["diffs"] += [dict(d, config=cname) for d in diffs]

with open(os.path.join(OUT, "check_s06f1.json"), "w") as f:
    json.dump(res, f, indent=1)
print()
print(f"asymmetric pairs found: {len(res['diffs'])}")
for d in res["diffs"][:6]:
    print(f"  {d['config']}: {d['fen']}")
    print(f"    self   {d['self']}")
    print(f"    mirror {d['mirror_eval']}  sums {d['sums']}")
print(f"\nwrote check_s06f1.json")
