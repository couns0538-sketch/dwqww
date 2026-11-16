#!/usr/bin/env python3
"""ep_divide2.py EXE SET_TSV OUT : class-B en-passant generation audit, WITHOUT pipelining.

Replaces ep_divide.py, which fed `position ... / go perft 1 / quit` as one stream. Seat 19's broadcast (19-F12)
shows that pipelining `quit` behind a running `go` makes this build answer a fabricated move at 0 nodes. perft is
answered inline in the UCI loop so the old numbers are almost certainly unaffected, but "almost certainly" is not
good enough for a finding: this version sends one command, reads stdout until its completion token, and only then
sends the next; `quit` is sent only after the last `nodes` line has been read.
"""
import os
import subprocess
import sys

EXE, SET, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT + ".raw", exist_ok=True)
rows = [l.rstrip("\n").split("\t") for l in open(SET) if l.strip()]
rows = [r for r in rows if r[0] == "B"]
lines_out = []
for i, r in enumerate(rows):
    fen = r[2]
    ep = fen.split()[3]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(f"{OUT}.raw/b{i:03d}.txt", "w")

    def send(c):
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def until(tok):
        while True:
            line = p.stdout.readline()
            if line == "":
                return None
            raw.write(line)
            raw.flush()
            if line.strip().startswith(tok):
                return line.strip()

    send("uci"); until("uciok")
    send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    send(f"position fen {fen}"); send("isready"); until("readyok")
    send("go perft 1")
    div = []
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        raw.write(line)
        raw.flush()
        s = line.strip()
        if s.startswith("nodes "):
            total = s
            break
        if ":" in s and not s.startswith(("info", "option", "id")):
            div.append(s)
    send("quit")            # only now, with the search finished and read
    try:
        p.wait(timeout=60)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.close()
    pawn_ep = [d for d in div if d.split(":")[0][2:4] == ep]
    lines_out.append(f"{i}\t{fen}\t{total}\tdivide_lines={len(div)}\tep_target_moves={len(pawn_ep)}\t{pawn_ep[:3]}")
with open(OUT, "w") as f:
    f.write("\n".join(lines_out) + "\n")
print(f"{len(rows)} class-B positions; "
      f"{sum(1 for l in lines_out if 'ep_target_moves=0' in l)} with NO move to the ep square")
print("\n".join(lines_out[:6]))
