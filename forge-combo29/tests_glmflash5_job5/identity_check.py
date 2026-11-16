import subprocess, sys, threading, queue

# Identity check: flag build (FORGE_MATE_ALPHA_GUARD=1, no option) vs default
# build, over the first N lines of openings_job5.epd, go nodes 20000 each,
# ucinewgame + isready before each. Compare (nodes, bestmove) per position.
# Control: default build with HindsightDepth=true vs default build plain.

def reader(proc, q):
    for line in proc.stdout:
        q.put(line.rstrip("\n"))
    q.put(None)

class Eng:
    def __init__(self, exe, options=()):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=reader, args=(self.p, self.q), daemon=True).start()
        for o in options:
            self.send(f"setoption name {o[0]} value {o[1]}")
        self.send("setoption name Threads value 1")
        self.send("setoption name Hash value 16")
        self.send("uci")
        self.until("uciok")

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def until(self, token):
        while True:
            line = self.q.get(timeout=60)
            if line is None:
                raise RuntimeError("engine died")
            if line.startswith(token):
                return line
            if line.startswith("info") and " nodes " in line:
                self.last_nodes = line

    def search(self, fen):
        self.send("ucinewgame")
        self.send("isready")
        self.until("readyok")
        self.send(f"position fen {fen}")
        self.send("isready")
        self.until("readyok")
        self.last_nodes = ""
        self.send("go nodes 20000")
        bm = self.until("bestmove")
        toks = self.last_nodes.split()
        nodes = toks[toks.index("nodes") + 1] if "nodes" in toks else "?"
        return nodes, bm.split()[1]

def run_pair(exeA, optA, exeB, optB, fens, out):
    a = Eng(exeA, optA)
    b = Eng(exeB, optB)
    same_nodes = same_bm = 0
    rows = []
    for i, fen in enumerate(fens, 1):
        na, ba = a.search(fen)
        nb, bb = b.search(fen)
        eq_n, eq_b = na == nb, ba == bb
        same_nodes += eq_n
        same_bm += eq_b
        rows.append(f"{i}|{fen}|{na}|{ba}|{nb}|{bb}|{int(eq_n)}|{int(eq_b)}")
    a.p.kill(); b.p.kill()
    with open(out, "w") as f:
        f.write("\n".join(rows) + "\n")
    return same_nodes, same_bm

fens = [l.strip() for l in open(sys.argv[1])][:int(sys.argv[2])]
DEF = "/tmp/forgebuild/forge"
FLAG = "/tmp/forgebuild_guard/forge"
n, b = run_pair(FLAG, (), DEF, (), fens, sys.argv[3])
print(f"identity flag-vs-default: equal nodes {n}/{len(fens)}, equal bestmove {b}/{len(fens)}")
n, b = run_pair(DEF, (("HindsightDepth", "true"),), DEF, (), fens, sys.argv[4])
print(f"control HD-on vs plain:    equal nodes {n}/{len(fens)}, equal bestmove {b}/{len(fens)} (must be < {len(fens)})")
