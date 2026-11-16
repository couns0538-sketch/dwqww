#!/usr/bin/env python3
"""Honesty check for the PC r15 build under the three settings regimes of FABLE_TO_swarm_5.

Regimes (file 4 warns that pins and sums use DIFFERENT settings, so each is measured separately):
  none : a fresh engine, NO setoption at all.  Expected 312866 / 862329 / 3024920 / perft 5 4865609.
  S14  : Threads 1, Hash 16, then the 14 S14 settings.  Expected bench 11 242796, bench 13 656517.
  PC20 : S14 then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true,
         OwnBook false.  Expected bench 11 278024, bench 13 587276.

Every setoption is followed by isready and every line up to readyok is read; the run STOPS on
`unknown option`, `invalid value` or `ERROR`. Option lines sent are recorded in the .meta file.

usage: pc20_pins.py EXE OUTFILE META
"""
import hashlib
import subprocess
import sys

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BASIC = [("Threads", "1"), ("Hash", "16")]
BAD = ("unknown option", "invalid value", "ERROR", "illegal")


class E:
    def __init__(self, exe, opts):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.name = None
        self.w("uci")
        while True:
            line = self.r()
            if line.startswith("id name"):
                self.name = line.strip()
            if line.strip() == "uciok":
                break
        self.sent = []
        for n, v in opts:
            self.w("setoption name %s value %s" % (n, v))
            self.w("isready")
            self.ready()
            self.sent.append("setoption name %s value %s" % (n, v))

    def w(self, c):
        self.p.stdin.write(c + "\n")
        self.p.stdin.flush()

    def r(self):
        line = self.p.stdout.readline()
        if line == "":
            raise RuntimeError("engine died")
        return line

    def ready(self):
        while True:
            line = self.r().strip()
            if any(m in line for m in BAD):
                raise RuntimeError(line)
            if line == "readyok":
                return

    def bench(self, depth):
        self.w("bench %d" % depth)
        self.w("isready")
        lines = []
        while True:
            line = self.r().strip()
            lines.append(line)
            if any(m in line for m in BAD):
                raise RuntimeError(line)
            if line == "readyok":
                break
        for line in lines:
            if "bench depth" in line and "nodes" in line:
                tok = line.split()
                return int(tok[tok.index("nodes") + 1])
        return None

    def perft(self, depth):
        # `go perft N` prints one "nodes <count>" line at the end, then readyok follows because an
        # isready was queued before it. Do not wait for "Nodes searched": this engine never prints it.
        self.w("position startpos")
        self.w("isready")
        self.ready()
        self.w("go perft %d" % depth)
        self.w("isready")
        seen = None
        while True:
            line = self.r().strip()
            if any(m in line for m in BAD):
                raise RuntimeError(line)
            if line.startswith("nodes "):
                seen = int(line.split()[1])
            if line == "readyok":
                return seen

    def quit(self):
        try:
            self.w("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def measure(exe, label, opts):
    e = E(exe, opts)
    out = {"label": label, "options": e.sent, "id_name": e.name}
    out["bench11"] = e.bench(11)
    out["bench13"] = e.bench(13)
    out["bench16"] = e.bench(16)
    out["perft5"] = e.perft(5)
    e.quit()
    return out


def main():
    exe, outfile, metafile = sys.argv[1:4]
    rows = [measure(exe, "none", []),
            measure(exe, "S14", BASIC + S14),
            measure(exe, "PC20", BASIC + PC20)]
    expect = {"none": (312866, 862329, 3024920, 4865609),
              "S14": (242796, 656517, None, None),
              "PC20": (278024, 587276, None, None)}
    with open(outfile, "w") as fh:
        fh.write("| settings | bench 11 | bench 13 | bench 16 | perft 5 | matches FABLE 5? |\n")
        fh.write("|---|---|---|---|---|---|\n")
        for r in rows:
            exp = expect[r["label"]]
            got = (r["bench11"], r["bench13"], r["bench16"], r["perft5"])
            ok = all(e is None or e == g for e, g in zip(exp, got))
            fh.write("| %s | %s | %s | %s | %s | %s |\n" % (r["label"], got[0], got[1], got[2], got[3],
                                                          "YES" if ok else "NO"))
        fh.write("\n")
        for r in rows:
            fh.write("### %s\nexpected: %s\ngot:      %s\noption lines sent: %s\n\n"
                     % (r["label"], expect[r["label"]],
                        (r["bench11"], r["bench13"], r["bench16"], r["perft5"]),
                        "; ".join(r["options"]) if r["options"] else "NONE"))
    with open(metafile, "w") as fh:
        fh.write("exe_started: %s\nexe_sha256: %s\nid_name: %s\n"
                 % (exe, sha256(exe), rows[0]["id_name"]))
        fh.write("regimes: none (no setoption at all), S14, PC20 - see the .txt for every option line\n")
    print(open(outfile).read())


if __name__ == "__main__":
    main()
