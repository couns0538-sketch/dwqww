#!/usr/bin/env python3
"""Check of seat 27 finding 27-F2, with my own interactive runner.

27-F2 claims: `go nodes N` below one root iteration (N < 26 at startpos) answers the first legal
move in generation order (a2a3) with NO info line at all; N = 26 answers d2m4.

My runner NEVER closes stdin while a command is running (after the 19-F12 warning), reads until
`bestmove`, and records every info line it saw. For each N it records:
  N, number of info lines, deepest depth reported, nodes on the last info line, the bestmove.

Controls I add beyond the finding:
  * the boundary is searched both ways (N = 24,25,26,27) to check "< 26" as stated;
  * the SAME N is run twice, once in a fresh process and once after a completed search in the same
    process, so a state effect cannot be mistaken for a budget effect;
  * a large N (100000) must produce many info lines -- if it does not, the runner is broken and the
    whole check is void.

Usage: check_27f2.py EXE OUTDIR
"""
import hashlib
import os
import re
import subprocess
import sys

EXE = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

NS = [0, 1, 10, 24, 25, 26, 27, 30, 100, 100000]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


class Engine:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.sent = []
        self.send("uci")
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died during uci handshake")
            if l.strip() == "uciok":
                break
        self.send("isready")
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died during first isready")
            if l.strip() == "readyok":
                break

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()
        self.sent.append(s)

    def search(self, go_cmd):
        """Send go_cmd and read until bestmove. Returns (info_lines, bestmove)."""
        self.send(go_cmd)
        infos = []
        while True:
            line = self.p.stdout.readline()
            if line == "":
                raise SystemExit("FAIL: engine died / EOF while searching after %r" % go_cmd)
            line = line.rstrip("\n")
            if line.startswith("bestmove"):
                return infos, line
            if "info" in line:
                infos.append(line)

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def deepest(infos):
    best = None
    nodes = None
    for l in infos:
        m = re.search(r"\bdepth (\d+)", l)
        if m:
            best = max(best or 0, int(m.group(1)))
        m = re.search(r"\bnodes (\d+)", l)
        if m:
            nodes = int(m.group(1))
    return best, nodes


rows = []
# fresh process per N
for n in NS:
    e = Engine()
    e.send("position startpos")
    e.send("isready")
    while e.p.stdout.readline().strip() != "readyok":
        pass
    infos, bm = e.search("go nodes %d" % n)
    e.close()
    d, nd = deepest(infos)
    rows.append(("fresh", n, len(infos), d, nd, bm))
    with open(os.path.join(OUT, "fresh_nodes_%d.txt" % n), "w") as f:
        f.write("exe %s\nsha256 %s\n" % (os.path.abspath(EXE), sha256(EXE)))
        f.write("lines sent:\n" + "\n".join("  > " + s for s in e.sent) + "\n")
        f.write("info lines (%d):\n" % len(infos) + "\n".join("  " + l for l in infos) + "\n")
        f.write("bestmove: %s\n" % bm)

# same N after a completed search in ONE process
e = Engine()
e.send("position startpos")
e.send("isready")
while e.p.stdout.readline().strip() != "readyok":
    pass
warm_infos, warm_bm = e.search("go depth 10")
for n in [25, 26, 27]:
    e.send("ucinewgame")
    e.send("position startpos")
    e.send("isready")
    while e.p.stdout.readline().strip() != "readyok":
        pass
    infos, bm = e.search("go nodes %d" % n)
    d, nd = deepest(infos)
    rows.append(("warm", n, len(infos), d, nd, bm))
    with open(os.path.join(OUT, "warm_nodes_%d.txt" % n), "w") as f:
        f.write("after a completed go depth 10 (%d info lines, %s)\n" % (len(warm_infos), warm_bm))
        f.write("info lines for this search (%d):\n" % len(infos)
                + "\n".join("  " + l for l in infos) + "\nbestmove: %s\n" % bm)
e.close()

rep = []
rep.append("# check of 27-F2: `go nodes N` below one root iteration\n")
rep.append("exe %s  sha256 %s\n" % (os.path.abspath(EXE), sha256(EXE)))
rep.append("| run | N | info lines | deepest depth | nodes (last info) | bestmove |")
rep.append("|---|---|---|---|---|---|")
for kind, n, ni, d, nd, bm in rows:
    rep.append("| %s | %d | %d | %s | %s | `%s` |" % (kind, n, ni, d, nd, bm))

fresh = {n: (ni, d, nd, bm) for kind, n, ni, d, nd, bm in rows if kind == "fresh"}
warm = {n: (ni, d, nd, bm) for kind, n, ni, d, nd, bm in rows if kind == "warm"}
rep.append("")

# assertions
big = fresh[100000]
runner_ok = big[0] > 5 and big[2] is not None
rep.append("**Runner sanity control (N = 100000):** %d info lines, %s nodes -> %s"
           % (big[0], big[2], "OK, the runner does see info lines" if runner_ok else
              "BROKEN - the runner reports no info lines even for a big search, check void"))

below = {n: v for n, v in fresh.items() if n < 26}
above = {n: v for n, v in fresh.items() if n >= 26}
quiet_below = all(v[0] == 0 for v in below.values())
a2a3_below = all(v[3] == "bestmove a2a3" for v in below.values())
rep.append("")
rep.append("**27-F2 first half (N < 26: no info line at all):** %s"
           % ("HOLDS - every N below 26 produced 0 info lines" if quiet_below else
              "DOES NOT HOLD - some N below 26 produced info lines"))
rep.append("**27-F2 first half (N < 26: bestmove is a2a3):** %s"
           % ("HOLDS - every N below 26 answered bestmove a2a3" if a2a3_below else
              "DOES NOT HOLD - " + ", ".join("N=%d -> %s" % (n, v[3]) for n, v in sorted(below.items()))))
rep.append("**27-F2 second half (N = 26 answers d2d4?):** %s (actual: `%s`)"
           % ("HOLDS" if fresh[26][3] == "bestmove d2d4" else "DOES NOT HOLD", fresh[26][3]))
rep.append("")
rep.append("**Boundary, both ways:** " + ", ".join(
    "N=%d %s" % (n, "quiet" if fresh[n][0] == 0 else "%d info lines, depth %s, %s" % (fresh[n][0], fresh[n][2], fresh[n][3]))
    for n in (24, 25, 26, 27, 30)))
rep.append("")
rep.append("**State effect (same N after a completed search, same process):** " + ", ".join(
    "N=%d %s" % (n, "quiet" if warm[n][0] == 0 else "%d info lines, %s" % (warm[n][0], warm[n][3]))
    for n in (25, 26, 27)))
same = all(fresh[n][3] == warm[n][3] and (fresh[n][0] == 0) == (warm[n][0] == 0) for n in (25, 26, 27))
rep.append("state makes no difference to these answers: %s" % ("YES" if same else "NO - investigate"))

text = "\n".join(rep)
open(os.path.join(OUT, "VERDICT.md"), "w").write(text)
print(text)
