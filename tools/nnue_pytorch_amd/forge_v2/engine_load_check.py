"""R7 J1: does a v2 net load and run in the Forge engine exe?  (UCI driver, no sleeps; waits for real output)
usage: python -I -B engine_load_check.py <forge.exe> <net.fnn2> [bench_depth=13]
Sends: uci; setoption NNUEKingBuckets 32, NNUEOutputBuckets 8, PureNnue 1, NNUEFile <net> (this order: setting
NNUEFile first prints transient errors until the shape options are set); isready -> readyok; bench <d>; then
`position startpos` + `go depth 8` and two material-down positions for an eval sanity line. Then the same exe with
no options (compiled-in lock net) runs bench <d> for the node/speed reference.
Exit 0 when readyok came, no 'ERROR' info string was printed after the last option, and both benches finished."""
import re
import subprocess
import sys

exe, net = sys.argv[1], sys.argv[2]
depth = int(sys.argv[3]) if len(sys.argv) > 3 else 13
POS = [("startpos", "position startpos"),
       ("white queen down", "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1"),
       ("white knight up", "position fen r1bqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")]


class Engine:
    def __init__(self, path):
        self.p = subprocess.Popen([path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1)
        self.lines = []

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def wait(self, pat):
        rx = re.compile(pat)
        for line in self.p.stdout:
            line = line.rstrip("\n")
            self.lines.append(line)
            m = rx.search(line)
            if m:
                return m
        raise SystemExit(f"engine exited before matching {pat!r}; last lines: {self.lines[-5:]}")

    def quit(self):
        self.send("quit")
        self.p.wait(timeout=60)


ok = True
e = Engine(exe)
e.send("uci")
e.wait(r"^uciok")
for opt in ("NNUEKingBuckets value 32", "NNUEOutputBuckets value 8", "PureNnue value 1", f"NNUEFile value {net}"):
    e.send(f"setoption name {opt}")
mark = len(e.lines)
e.send("isready")
e.wait(r"^readyok")
after = e.lines[mark:]
print("after options + isready:")
for line in after:
    print("  " + line)
# The shape options print transient "ERROR ... no v2 net is loaded" lines until NNUEFile is set: judge only
# what follows the load line (a "loaded" line must exist, the last v2 status must be "active", no ERROR after it).
loaded = [i for i, line in enumerate(after) if "NNUE v2: loaded" in line]
status = [line for line in after if "NNUE v2:" in line]
if not loaded or "active:" not in status[-1] or any("ERROR" in line for line in after[loaded[-1]:]):
    ok = False
e.send(f"bench {depth}")
m = e.wait(rf"bench depth {depth} nodes (\d+) time (\d+) nps (\d+)")
print(f"v2 net bench {depth}: nodes {m.group(1)} time {m.group(2)} ms nps {m.group(3)}")
for name, cmd in POS:
    e.send(cmd)
    e.send("go depth 8")
    sc = None
    while True:
        line = e.wait(r"^(info .*score (cp|mate) (-?\d+)|bestmove)").group(0)
        mm = re.search(r"score (cp|mate) (-?\d+)", line)
        if mm:
            sc = f"{mm.group(1)} {mm.group(2)}"
        if line.startswith("bestmove"):
            break
    print(f"  {name}: depth-8 score {sc} ({line})")
e.quit()
r = Engine(exe)
r.send("uci")
r.wait(r"^uciok")
r.send("isready")
r.wait(r"^readyok")
r.send(f"bench {depth}")
m2 = r.wait(rf"bench depth {depth} nodes (\d+) time (\d+) nps (\d+)")
print(f"compiled-in net bench {depth}: nodes {m2.group(1)} time {m2.group(2)} ms nps {m2.group(3)}")
r.quit()
print("ENGINE LOAD OK" if ok else "ENGINE LOAD FAIL")
sys.exit(0 if ok else 1)
