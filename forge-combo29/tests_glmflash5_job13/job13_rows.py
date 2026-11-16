import subprocess, sys, threading, queue

# Job 12 step 1: depth-12 node counts on kimi5's first200.fens for the
# SoundMatePruning case settings on B5 (base tree + kimi5's three job-5
# patches). One row per search: setting|position|nodes.

DEF_STYLE = [("Threads", "1"), ("Hash", "16")]

def reader(proc, q):
    for line in proc.stdout:
        q.put(line.rstrip("\n"))
    q.put(None)

class Eng:
    def __init__(self, exe, opts=()):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=reader, args=(self.p, self.q), daemon=True).start()
        self.refusals = []
        for n, v in list(opts) + DEF_STYLE:
            self.send(f"setoption name {n} value {v}")
        self.send("uci")
        self.until("uciok")

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def until(self, tok):
        while True:
            line = self.q.get(timeout=180)
            if line is None:
                raise RuntimeError("engine died")
            if "unknown option" in line or "invalid value" in line:
                self.refusals.append(line)
            if line.startswith(tok):
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
        self.send("go depth 12")
        self.until("bestmove")
        t = self.last_nodes.split()
        return t[t.index("nodes") + 1] if "nodes" in t else "?"

SETS = [
    ("none", []),
    ("hpm1024",[("HistoryPruneMultiplier","1024")]),
    ("hpm4096",[("HistoryPruneMultiplier","4096")]),
    ("histoff",[("HistoryPruneMultiplier","20000")]),
    ("futoff",[("FutilityBase","500"),("FutilityMultiplier","500")]),
    ("qseewide",[("SeeQuietMultiplier","200")]),
    
    
    
]

n = int(sys.argv[2])
fens = [l.strip() for l in open(sys.argv[1])][:n]
out_rows = []
summary = []
for tag, opts in SETS:
    e = Eng("/tmp/forgebuild_b5/forge", opts)
    nodes = []
    for i, f in enumerate(fens, 1):
        v = e.search(f)
        nodes.append(int(v))
        out_rows.append(f"{tag}|{i}|{v}")
    if e.refusals:
        summary.append(f"{tag}: REFUSALS: {e.refusals}")
    e.p.kill()
    summary.append(f"{tag}: first3={nodes[:3]} sum_all{n}={sum(nodes)}")
with open(sys.argv[3], "w") as f:
    f.write("\n".join(out_rows) + "\n")
print("\n".join(summary))
with open(sys.argv[4], "w") as f:
    f.write("\n".join(summary) + "\n")
