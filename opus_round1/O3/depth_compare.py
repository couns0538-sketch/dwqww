#!/usr/bin/env python3
"""Fixed-depth identity run: for each position (fresh ucinewgame, Threads 1, Hash 16,
OwnBook false) record bestmove, final-depth node count and score.
usage: depth_compare.py <forge_exe> <positions.fen> <depth> <out.tsv>
positions.fen: one '<FEN 6 fields> ; <id>' per line.  Compare two outputs with diff."""
import re, subprocess, sys, time
exe, positions, depth, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
def send(s): p.stdin.write(s + "\n"); p.stdin.flush()
def wait(pat):
    rx = re.compile(pat); seen = []
    for line in p.stdout:
        seen.append(line)
        if rx.search(line): return line, seen
    raise SystemExit("engine exited before " + pat)
send("uci"); wait(r"^uciok")
for o in ("Threads value 1", "Hash value 16", "OwnBook value false"): send("setoption name " + o)
send("isready"); wait(r"^readyok")
rows = []
for n, line in enumerate(open(positions, encoding="utf-8")):
    fen, ident = [x.strip() for x in line.split(";", 1)]
    send("ucinewgame"); send("isready"); wait(r"^readyok")
    send("position fen " + fen); send(f"go depth {depth}")
    t0 = time.time(); best, seen = wait(r"^bestmove")
    infos = [l for l in seen if l.startswith("info depth ")]
    last = infos[-1] if infos else ""
    nodes = re.search(r" nodes (\d+)", last); score = re.search(r" score (cp -?\d+|mate -?\d+)", last)
    d = re.search(r"^info depth (\d+)", last)
    rows.append(f"{n}\t{ident}\t{best.split()[1]}\t{nodes.group(1) if nodes else '?'}\t{d.group(1) if d else '?'}\t{score.group(1) if score else '?'}\t{fen}")
    print(rows[-1].split('\t')[:6], f"{time.time()-t0:.1f}s", flush=True)
send("quit"); p.wait(timeout=60)
with open(out, "w", newline="\n") as fh: fh.write("idx\tid\tbestmove\tnodes\tdepth\tscore\tfen\n" + "\n".join(rows) + "\n")
