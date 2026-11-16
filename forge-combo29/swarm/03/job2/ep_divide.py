#!/usr/bin/env python3
"""ep_divide.py EXE SET_TSV OUT : for every class-B position, ask the engine for `go perft 1` and record whether
it generated the raw en-passant capture at all. Raw transcripts beside the OUT file."""
import os, subprocess, sys

EXE, SET, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT + ".raw", exist_ok=True)
rows = [l.rstrip("\n").split("\t") for l in open(SET) if l.strip()]
rows = [r for r in rows if r[0] == "B"]
lines_out = []
for i, r in enumerate(rows):
    fen = r[2]
    # the raw ep capture square, from the ep field of the FEN
    parts = fen.split()
    ep = parts[3]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    inp = f"uci\nisready\nucinewgame\nisready\nposition fen {fen}\nisready\ngo perft 1\nquit\n"
    out, _ = p.communicate(inp, timeout=120)
    rawp = f"{OUT}.raw/b{i:03d}.txt"
    open(rawp, "w").write(">>> " + inp.replace("\n", "\n>>> ") + "\n" + out)
    div = [l for l in out.splitlines() if ":" in l and not l.startswith(("info", "option", "id"))]
    total = [l for l in out.splitlines() if l.startswith("nodes ")]
    ep_moves = [l for l in div if l.strip().endswith(": 0") or l.split(":")[0].endswith(ep)]
    hit = [l for l in div if l.split(":")[0][2:4] == ep]
    lines_out.append(f"{i}\t{fen}\tperft1={total[0].split()[1] if total else 'NONE'}"
                     f"\tdivide_lines={len(div)}\tep_target_moves={len(hit)}\t{hit[:3]}")
with open(OUT, "w") as f:
    f.write("\n".join(lines_out) + "\n")
print(f"{len(rows)} class-B positions, "
      f"{sum(1 for l in lines_out if 'ep_target_moves=0' in l)} with NO move to the ep square")
print("\n".join(lines_out[:5]))
