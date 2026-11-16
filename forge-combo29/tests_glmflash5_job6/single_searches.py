import subprocess, sys, threading, queue, time

# I0: PATCHED(no option) vs BASE(no option), go nodes 20000 -> 50/50 equal
# I1: PATCHED(TmSmoothStability=true) vs PATCHED(no option), go nodes 20000 -> 50/50 equal
# I2: PATCHED(HindsightDepth=true) vs PATCHED(no option) -> CONTROL, fewer than 50 equal
# I3: PATCHED clocked, go wtime 2000 btime 2000 winc 20 binc 20, three runs:
#     none, none again, TmSmoothStability=true; wall time go->bestmove per search.

DEF = "/tmp/forgebuild/forge"
PAT = "/tmp/forgebuild_patched/forge"

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
        for name, val in options:
            self.send(f"setoption name {name} value {val}")
        self.send("setoption name Threads value 1")
        self.send("setoption name Hash value 16")
        self.send("uci")
        self.until("uciok")

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def until(self, token):
        while True:
            line = self.q.get(timeout=120)
            if line is None:
                raise RuntimeError("engine died")
            if line.startswith(token):
                return line
            if line.startswith("info") and " nodes " in line:
                self.last_nodes = line

    def search(self, fen, go_line):
        self.send("ucinewgame")
        self.send("isready")
        self.until("readyok")
        self.send(f"position fen {fen}")
        self.send("isready")
        self.until("readyok")
        self.last_nodes = ""
        t0 = time.monotonic()
        self.send(go_line)
        bm = self.until("bestmove")
        wall_ms = (time.monotonic() - t0) * 1000.0
        toks = self.last_nodes.split()
        nodes = toks[toks.index("nodes") + 1] if "nodes" in toks else "?"
        return nodes, bm.split()[1], wall_ms

def fens(path, n):
    return [l.strip() for l in open(path)][:n]

def run_pair(tag, exeA, optA, exeB, optB, fens, go_line, out):
    a = Eng(exeA, optA)
    b = Eng(exeB, optB)
    en = eb = 0
    rows = []
    for i, fen in enumerate(fens, 1):
        na, ba, ta = a.search(fen, go_line)
        nb, bb, tb = b.search(fen, go_line)
        eqn, eqb = na == nb, ba == bb
        en += eqn; eb += eqb
        rows.append(f"{i}|{fen}|{na}|{ba}|{ta:.2f}|{nb}|{bb}|{tb:.2f}|{int(eqn)}|{int(eqb)}")
    a.p.kill(); b.p.kill()
    with open(out, "w") as f:
        f.write("\n".join(rows) + "\n")
    return en, eb

N = 50
fens50 = fens(sys.argv[1], N)
res = []
en, eb = run_pair("I0", PAT, (), DEF, (), fens50, "go nodes 20000", sys.argv[2])
res.append(f"I0 PATCHED-none vs BASE-none: equal nodes {en}/{N}, equal bestmove {eb}/{N}")
en, eb = run_pair("I1", PAT, (("TmSmoothStability", "true"),), PAT, (), fens50, "go nodes 20000", sys.argv[3])
res.append(f"I1 PATCHED-TSS vs PATCHED-none: equal nodes {en}/{N}, equal bestmove {eb}/{N}")
en, eb = run_pair("I2", PAT, (("HindsightDepth", "true"),), PAT, (), fens50, "go nodes 20000", sys.argv[4])
res.append(f"I2 PATCHED-HD vs PATCHED-none (CONTROL): equal nodes {en}/{N}, equal bestmove {eb}/{N} (must be < {N})")

# I3: three clocked runs on PATCHED, one process per run
def run_one(options, out):
    e = Eng(PAT, options)
    rows = []
    total = 0.0
    for i, fen in enumerate(fens50, 1):
        _, _, w = e.search(fen, "go wtime 2000 btime 2000 winc 20 binc 20")
        rows.append(f"{i}|{w:.2f}")
        total += w
    e.p.kill()
    with open(out, "w") as f:
        f.write("\n".join(rows) + "\n")
    return total

t1 = run_one((), sys.argv[5] + "run1_none.txt")
t2 = run_one((), sys.argv[5] + "run2_none_again.txt")
t3 = run_one((("TmSmoothStability", "true"),), sys.argv[5] + "run3_tss.txt")

def compare(fa, fb):
    wa = [float(l.split("|")[1]) for l in open(fa)]
    wb = [float(l.split("|")[1]) for l in open(fb)]
    diff20 = sum(abs(x - y) / max(x, y) > 0.20 for x, y in zip(wa, wb))
    ratio = sum(wb) / sum(wa)
    return sum(wa), sum(wb), ratio, diff20

s1, s2, r_nn, d_nn = compare(sys.argv[5] + "run1_none.txt", sys.argv[5] + "run2_none_again.txt")
s3, _, r_nt, d_nt = compare(sys.argv[5] + "run1_none.txt", sys.argv[5] + "run3_tss.txt")
res.append(f"I3 none run1 sum={s1:.1f} ms; none-again run2 sum={s2:.1f} ms; ratio(none2/none1)={r_nn:.3f}; positions >20% differ: {d_nn}/{N}")
res.append(f"I3 TmSmoothStability run3 sum={s3:.1f} ms; ratio(true/none1)={r_nt:.3f}; positions >20% differ: {d_nt}/{N}")
print("\n".join(res))
with open(sys.argv[6], "w") as f:
    f.write("\n".join(res) + "\n")
