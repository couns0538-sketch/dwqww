import subprocess, sys, threading, queue, time, math

# Job 7 calibration: 7 settings x 2 clock lines x 100 positions, one process
# per setting; ucinewgame + isready before every go; per search: bestmove,
# last depth, wall time go->bestmove, count of 'info string TmFinishIteration'.

DEF = "/tmp/forgebuild/forge"

SETTINGS = [
    ("N1", []),
    ("N2", []),
    ("F",  [("TmFinishIteration", "true")]),
    ("B0", [("TmFinishIteration", "true"), ("TmSoftDivisor", "20"), ("TmIncrementPercent", "83")]),
    ("B1", [("TmFinishIteration", "true"), ("TmSoftDivisor", "18"), ("TmIncrementPercent", "91")]),
    ("B2", [("TmFinishIteration", "true"), ("TmSoftDivisor", "16"), ("TmIncrementPercent", "103")]),
    ("P",  [("TmSoftDivisor", "18"), ("TmIncrementPercent", "91")]),
]
LINES = ["go wtime 2000 btime 2000 winc 20 binc 20",
         "go wtime 400 btime 400 winc 20 binc 20"]

def reader(proc, q):
    for line in proc.stdout:
        q.put(line.rstrip("\n"))
    q.put(None)

class Eng:
    def __init__(self, options=()):
        self.p = subprocess.Popen([DEF], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
            if line.startswith("info") and " depth " in line:
                self.last_depth = line
            if line.startswith("info string TmFinishIteration"):
                self.holds += 1

    def search(self, fen, go_line):
        self.send("ucinewgame")
        self.send("isready")
        self.until("readyok")
        self.send(f"position fen {fen}")
        self.send("isready")
        self.until("readyok")
        self.last_depth = ""
        self.holds = 0
        t0 = time.monotonic()
        self.send(go_line)
        bm = self.until("bestmove")
        wall_ms = (time.monotonic() - t0) * 1000.0
        toks = (self.last_depth or "").split()
        depth = toks[toks.index("depth") + 1] if "depth" in toks else "?"
        return bm.split()[1], depth, wall_ms, self.holds

fens = [l.strip() for l in open(sys.argv[1])][:100]
data = {}
for name, opts in SETTINGS:
    e = Eng(opts)
    for li, go_line in enumerate(LINES):
        rows = []
        for i, fen in enumerate(fens, 1):
            bm, dep, w, h = e.search(fen, go_line)
            rows.append((bm, int(dep) if dep.isdigit() else -1, w, h))
        data[(name, li)] = rows
    e.p.kill()

out_lines = []
for (name, li), rows in sorted(data.items()):
    for i, (bm, dep, w, h) in enumerate(rows, 1):
        out_lines.append(f"{name}|{LINES[li]}|{i}|{bm}|{dep}|{w:.2f}|{h}")
with open(sys.argv[2], "w") as f:
    f.write("\n".join(out_lines) + "\n")

n1 = data[("N1", 0)], data[("N1", 1)]
report = []
for name, _ in SETTINGS[1:]:
    for li in (0, 1):
        r = data[(name, li)]
        n1r = data[("N1", li)]
        ratio = sum(x[2] for x in r) / sum(x[2] for x in n1r)
        lower = sum(1 for x, y in zip(r, n1r) if x[1] < y[1])
        higher = sum(1 for x, y in zip(r, n1r) if x[1] > y[1])
        bmdiff = sum(1 for x, y in zip(r, n1r) if x[0] != y[0])
        report.append(f"{name} vs N1, line {LINES[li].split()[2]}+{LINES[li].split()[4]}: "
                      f"ratio={ratio:.3f} lower_depth={lower} higher_depth={higher} bmdiff={bmdiff}")
print("\n".join(report))
with open(sys.argv[3], "w") as f:
    f.write("\n".join(report) + "\n")
