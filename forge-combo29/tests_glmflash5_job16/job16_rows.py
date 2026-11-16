import subprocess, sys, threading, queue

# Job 16 step 1: depth-12 node counts for the PC's 14 search settings (S14),
# S13 (without LmpBase), and the pv1/de0 additions, on B6.
# Driver reads every line up to readyok after the options; stops on refusals.

DEF_STYLE = [("Threads", "1"), ("Hash", "16")]

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]
S13 = [o for o in S14 if o[0] != "LmpBase"]
PV1 = [("SoundPvArm", "1"), ("SoundStepMask", "1")]
DE0 = [("DoubleExtLimit", "-1")]

class Refusal(Exception):
    pass

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
            self.send("isready")
            self.until("readyok")
        if self.refusals:
            raise Refusal(self.refusals)
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
                raise Refusal(self.refusals)
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
    ("none",      []),
    ("S14",       S14),
    ("S14+pv1",   S14 + PV1),
    ("S14+de0",   S14 + DE0),
    ("S13",       S13),
    ("S13+pv1",   S13 + PV1),
]

n = int(sys.argv[2])
fens = [l.strip() for l in open(sys.argv[1])][:n]
out_rows = []
summary = []
for tag, opts in SETS:
    try:
        e = Eng("/tmp/forgebuild_b6/forge", opts)
    except Refusal as r:
        summary.append(f"{tag}: DRIVER STOPPED on refusal: {r.args[0]}")
        continue
    nodes = []
    for i, f in enumerate(fens, 1):
        v = e.search(f)
        nodes.append(int(v))
        out_rows.append(f"{tag}|{i}|{v}")
    e.p.kill()
    summary.append(f"{tag}: first3={nodes[:3]} sum_all{n}={sum(nodes)}")
print("\n".join(summary))
with open(sys.argv[3], "w") as f:
    f.write("\n".join(out_rows) + "\n")
with open(sys.argv[4], "w") as f:
    f.write("\n".join(summary) + "\n")
