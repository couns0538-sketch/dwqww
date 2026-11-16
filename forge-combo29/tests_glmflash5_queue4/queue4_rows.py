import subprocess, sys, threading, queue

# Queue 3 step 0: depth-12 rows on the two bundle builds (O = 200 openings).
# B_VT: S14 / V / T1 / V+T1(plain, deepseek6 cross 9,331,413) / VT-F0 (mine)
# B_VP: S14 / P (9,476,627) / V+P (deepseek6 cross 8,650,468)

DEF_STYLE = [("Threads", "1"), ("Hash", "16")]
S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]
B_VT = "/tmp/forgebuild_bvt/forge"
B_VP = "/tmp/forgebuild_bvp/forge"
SETS = [
    ("VT/S14",      B_VT, S14, 9500069),
    ("VT/V",        B_VT, S14 + [("CheckExtensionDepth", "8"), ("LmrGiveCheck", "0"), ("LmrInCheck", "0")], 8565026),
    ("VT/T1",       B_VT, S14 + [("LmrFine", "1"), ("LmrFineHistory", "1")], 10170054),
    ("VT/V+T1plain", B_VT, S14 + [("CheckExtensionDepth", "8"), ("LmrGiveCheck", "0"), ("LmrInCheck", "0"), ("LmrFine", "1"), ("LmrFineHistory", "1")], 9331413),
    ("VT/VT-F0",    B_VT, S14 + [("CheckExtensionDepth", "8"), ("LmrGiveCheck", "0"), ("LmrInCheck", "0"), ("LmrFine", "1"), ("LmrFineHistory", "1"), ("LmrGiveCheckF", "0"), ("LmrInCheckF", "0")], None),
    ("VP/S14",      B_VP, S14, 9500069),
    ("VP/P",        B_VP, S14 + [("SoundPvArm", "1"), ("SoundStepMask", "1")], 9476627),
    ("VP/V+P",      B_VP, S14 + [("CheckExtensionDepth", "8"), ("LmrGiveCheck", "0"), ("LmrInCheck", "0"), ("SoundPvArm", "1"), ("SoundStepMask", "1")], 8650468),
]

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
                raise RuntimeError("died")
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

n = int(sys.argv[2])
fens = [l.strip() for l in open(sys.argv[1])][:n]
out = []
summary = []
for tag, exe, opts, known in SETS:
    try:
        e = Eng(exe, opts)
    except Refusal as r:
        summary.append(f"{tag}: DRIVER STOPPED on refusal: {r.args[0]}")
        continue
    nodes = []
    for i, f in enumerate(fens, 1):
        v = e.search(f)
        nodes.append(int(v))
        out.append(f"{tag}|{i}|{v}")
    e.p.kill()
    s = f"{tag}: first3={nodes[:3]} sum_all{n}={sum(nodes)}"
    if known is not None:
        s += f" known={known} {'OK' if sum(nodes) == known else 'DIFFERS'}"
    else:
        s += " (first measurement)"
    summary.append(s)
print("\n".join(summary))
with open(sys.argv[3], "w") as f:
    f.write("\n".join(out) + "\n")
with open(sys.argv[4], "w") as f:
    f.write("\n".join(summary) + "\n")
