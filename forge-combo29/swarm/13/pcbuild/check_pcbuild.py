#!/usr/bin/env python3
"""Verify the PC r15 build's known numbers (FABLE_TO_swarm_5), with Threads 1 stated explicitly.

SWARM RULE (seat 04's report): every score must come from Threads 1 unless the job is about
threading. Perft and bench here are single-threaded by construction, and this script sends
`setoption name Threads value 1` explicitly in every regime so the tables cannot be mistaken.

Three regimes, each in a FRESH process, interactive (read to the expected token, never close stdin
mid-command):
  none : Threads 1 only          -> bench 11 312866, bench 13 862329, bench 16 3024920, perft 5 4865609
  S14  : S14 (14 settings)       -> bench 11 242796, bench 13 656517
  PC20 : S14 + the six PC ones   -> bench 11 278024, bench 13 587276
Every setoption is sent with isready and read to readyok; `unknown option`/`invalid value`/`ERROR`
is fatal, and every option name is first checked against the exe's own `uci` list.
"""
import hashlib
import subprocess
import sys

EXE = sys.argv[1]
S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC6 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]
THREADS1 = [("Threads", "1"), ("Hash", "16")]
BAD = ("unknown option", "invalid value", "error")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


class Eng:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.log = []
        self.sent = []
        self.send("uci")
        self.options = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died during the uci handshake")
            l = l.rstrip("\n")
            self.log.append(l)
            if l.startswith("id name"):
                self.idname = l
            if l.startswith("option name"):
                self.options.append(l)
            if l == "uciok":
                break

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()
        self.sent.append(s)

    def ready(self):
        self.send("isready")
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died waiting for readyok")
            l = l.rstrip("\n")
            self.log.append(l)
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad answer line: %r" % l)
            if l == "readyok":
                return

    def wait_line(self, pred, what):
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died waiting for %s" % what)
            l = l.rstrip("\n")
            self.log.append(l)
            if pred(l):
                return l

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def apply_opts(e, opts):
    for n, v in opts:
        if not any(o.startswith("option name %s " % n) for o in e.options):
            raise SystemExit("FAIL: option %r is NOT in the exe's uci list (would be an unknown option)" % n)
        e.send("setoption name %s value %s" % (n, v))
        e.ready()


def bench(depth, opts):
    e = Eng()
    apply_opts(e, opts)
    e.ready()
    e.send("bench %d" % depth)
    line = e.wait_line(lambda s: "bench depth" in s and "nodes" in s, "the bench line")
    e.close()
    p = line.split()
    return int(p[p.index("nodes") + 1]), e


def perft5(opts):
    e = Eng()
    apply_opts(e, opts)
    e.ready()
    e.send("go perft 5")
    line = e.wait_line(lambda s: s.startswith("nodes "), "the perft nodes line")
    e.close()
    return int(line.split()[1]), e


print("exe", EXE)
print("sha256", sha256(EXE))
res = {}
for regime, opts in (("none", THREADS1), ("S14", THREADS1 + S14), ("PC20", THREADS1 + S14 + PC6)):
    b11, e1 = bench(11, opts)
    b13, _ = bench(13, opts)
    res[regime] = {"bench11": b11, "bench13": b13}
    print("%-5s bench 11 = %-8d bench 13 = %-8d" % (regime, b11, b13), flush=True)
b16, e16 = bench(16, THREADS1)
print("none  bench 16 = %d" % b16)
p5, e5 = perft5(THREADS1)
print("none  go perft 5 = %d" % p5)

print()
print("id name:", e16.idname)
print("options advertised:", len(e16.options))
print("regime 'none' setoptions sent:", e16.sent[:4])
print("regime 'PC20' setoptions sent:", res and [s for s in e1.sent if s.startswith("setoption")][:3], "...")

want = {("none", "bench11"): 312866, ("none", "bench13"): 862329, ("S14", "bench11"): 242796,
        ("S14", "bench13"): 656517, ("PC20", "bench11"): 278024, ("PC20", "bench13"): 587276}
ok = True
for (reg, k), v in sorted(want.items()):
    got = res[reg][k]
    m = got == v
    ok &= m
    print(f"{reg:5s} {k:8s} got {got:8d} want {v:8d} {'MATCH' if m else 'MISMATCH'}")
m = b16 == 3024920
ok &= m
print(f"none  bench16  got {b16:8d} want 3024920 {'MATCH' if m else 'MISMATCH'}")
m = p5 == 4865609
ok &= m
print(f"none  perft5   got {p5:8d} want 4865609 {'MATCH' if m else 'MISMATCH'}")
print()
print("PC BUILD VERDICT:", "ALL KNOWN NUMBERS MATCH" if ok else "MISMATCH - this build is not used")
