#!/usr/bin/env python3
"""pc_build_check.py EXE OUTDIR : verify the r15 PC build's published numbers under three regimes.

File 5 gives these numbers for the PC's build (fresh process per line):

| settings | bench 11 | bench 13 | bench 16 | go perft 5 |
| none     | 312866   | 862329   | 3024920  | 4865609    |
| S14      | 242796   | 656517   | -        | -          |
| PC20     | 278024   | 587276   | -        | -          |

S14 = the 14 settings of file 1. PC20 = S14 then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
MateAlphaGuard true, OwnBook false (Threads 1, Hash 16 as always).

Every option name is checked against the exe's OWN uci list before it is sent, and the run STOPS on
`unknown option` / `invalid value` / `ERROR` — file 5 requires that. Harness rule from HARNESS_AUDIT.md: one
command, read stdout to its completion token, never close stdin mid-command.
"""
import os
import subprocess
import sys

EXE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BASE = [("Threads", "1"), ("Hash", "16")]
BAD = ("unknown option", "invalid value", "ERROR")


class E:
    def __init__(self, log):
        self.log = open(log, "w")
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(self, c):
        self.log.write(f">>> {c}\n")
        self.p.stdin.write(c + "\n")
        self.p.stdin.flush()

    def until(self, tok):
        while True:
            line = self.p.stdout.readline()
            if line == "":
                raise RuntimeError(f"engine died waiting for {tok!r}")
            self.log.write(line)
            self.log.flush()
            s = line.strip()
            for w in BAD:
                if w in s:
                    self.log.write(f"### STOP on error word {w!r}\n")
                    raise RuntimeError(f"engine refused a command: {s}")
            if s.startswith(tok):
                return s

    def close(self):
        self.send("quit")
        try:
            self.p.wait(timeout=120)
        except Exception:  # noqa: BLE001
            self.p.kill()
        self.log.close()


def uci_options(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    p.stdin.write("uci\n")
    p.stdin.flush()
    names = set()
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        s = line.strip()
        if s.startswith("option name "):
            rest = s[len("option name "):]
            names.add(rest.split(" type ")[0])
        if s == "uciok":
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.wait(timeout=30)
    except Exception:  # noqa: BLE001
        p.kill()
    return names


def run_case(name, settings, commands):
    e = E(f"{OUT}/{name}.raw")
    e.send("uci"); e.until("uciok")
    e.send("isready"); e.until("readyok")
    for opt, val in settings:
        e.send(f"setoption name {opt} value {val}")
        e.send("isready"); e.until("readyok")
    e.send("ucinewgame"); e.send("isready"); e.until("readyok")
    out = {}
    for cmd in commands:
        e.send(cmd)
        tok = "info string bench" if cmd.startswith("bench") else "nodes "
        line = e.until(tok)
        out[cmd] = line
    e.close()
    return out


opts = uci_options(EXE)
with open(f"{OUT}/uci_options.txt", "w") as f:
    f.write("\n".join(sorted(opts)) + "\n")

needed = [o for o, _ in BASE + S14 + PC20_EXTRA]
missing = [o for o in needed if o not in opts]
print(f"options in exe: {len(opts)}; missing of the ones I must send: {missing}")
if missing:
    sys.exit(f"FAIL: the exe does not list {missing} — do not guess option names")

rows = []
cases = [
    ("none", [], ["bench 11", "bench 13", "bench 16", "go perft 5"]),
    ("s14", BASE + S14, ["bench 11", "bench 13"]),
    ("pc20", BASE + S14 + PC20_EXTRA, ["bench 11", "bench 13"]),
]
expected = {
    ("none", "bench 11"): 312866, ("none", "bench 13"): 862329,
    ("none", "bench 16"): 3024920, ("none", "go perft 5"): 4865609,
    ("s14", "bench 11"): 242796, ("s14", "bench 13"): 656517,
    ("pc20", "bench 11"): 278024, ("pc20", "bench 13"): 587276,
}
for case, settings, cmds in cases:
    got = run_case(case, settings, cmds)
    for cmd, line in got.items():
        if "nodes " in line:
            val = int(line.split("nodes ")[1].split()[0])
        else:
            val = None
        exp = expected[(case, cmd)]
        ok = val == exp
        rows.append((case, cmd, exp, val, "MATCH" if ok else "MISMATCH", line))
        print(f"{case:5s} {cmd:12s} expected {exp:>8} got {val} {rows[-1][4]}")

with open(f"{OUT}/pc_build_check.txt", "w") as f:
    f.write(f"exe: {EXE}\n")
    f.write(subprocess.run(["sha256sum", EXE], capture_output=True, text=True).stdout)
    f.write("\ncase\tcommand\texpected\tgot\tverdict\tfull line\n")
    for r in rows:
        f.write("\t".join(str(x) for x in r) + "\n")
    bad = [r for r in rows if r[4] != "MATCH"]
    f.write(f"\nMATCH {len(rows)-len(bad)} of {len(rows)}\n")
print(f"\nMATCH {len(rows)-sum(1 for r in rows if r[4]!='MATCH')} of {len(rows)}")
