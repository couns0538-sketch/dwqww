#!/usr/bin/env python3
"""corrhist_strength.py EXE FENS OUTDIR [LIMIT] : does CorrHistV2 improve the RESULT, or only the node count?

19-F32 showed CorrHistV2 saves 4.3 % of nodes on bench 13. A node saving is not a strength claim. This test
runs the SAME positions to the SAME depth with the option ON and OFF and compares the best moves and scores.

Build PC r15, Threads 1, PC20 minus/holding everything else constant. One fresh process per arm, and within an
arm one process for all positions with `ucinewgame` before each (cold, per 19-F22). Every search is awaited to
`bestmove` (19-F12).

Output per position: move_on, score_on, move_off, score_off, and a match/mismatch flag. Then a summary.

IMPORTANT on what a difference means: a differing move is NOT proof that either option is stronger — it means
the two settings play different chess, so a node saving cannot be read as a gain without games.
"""
import os
import subprocess
import sys

exe, fens, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
limit = int(sys.argv[4]) if len(sys.argv) > 4 else 200
depth = 12
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Hash", "16")]

positions = []
for line in open(fens):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    positions.append(line.split(";")[0].strip())
positions = positions[:limit]


class Eng:
    def __init__(self, corr):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.send("uci")
        self.read_to(lambda l: l.startswith("uciok"))
        opts = list(S14) + [("CorrHistV2", "true" if corr else "false")]
        for k, v in opts:
            self.send("setoption name %s value %s" % (k, v))
            self.send("isready")
            got = self.read_to(lambda l: l.startswith("readyok"))
            for g in got:
                if "unknown option" in g or "invalid value" in g or g.startswith("ERROR"):
                    raise SystemExit("REFUSED: %r" % g)

    def send(self, l):
        self.p.stdin.write(l + "\n")
        self.p.stdin.flush()

    def read_to(self, pred, limit=100000):
        got = []
        for _ in range(limit):
            l = self.p.stdout.readline()
            if not l:
                return got
            l = l.rstrip("\n")
            got.append(l)
            if pred(l):
                return got
        return got

    def search(self, fen):
        self.send("ucinewgame")
        self.send("isready")
        self.read_to(lambda l: l.startswith("readyok"))
        self.send("position fen " + fen)
        self.send("isready")
        self.read_to(lambda l: l.startswith("readyok"))
        self.send("go depth %d" % depth)
        block = self.read_to(lambda l: l.startswith("bestmove"))
        info = None
        best = None
        nodes = 0
        score = None
        for l in block:
            if l.startswith("info depth"):
                info = l
            if l.startswith("bestmove"):
                best = l.split()[1] if len(l.split()) > 1 else None
        if info:
            if " nodes " in info:
                try:
                    nodes = int(info.split("nodes ")[1].split()[0])
                except (IndexError, ValueError):
                    pass
            if "score cp " in info:
                score = ("cp", int(info.split("score cp ")[1].split()[0]))
            elif "score mate " in info:
                score = ("mate", int(info.split("score mate ")[1].split()[0]))
        return best, score, nodes

    def close(self):
        try:
            self.send("quit")
            self.p.communicate(timeout=60)
        except Exception:  # noqa: BLE001
            self.p.kill()


on = Eng(True)
off = Eng(False)
rows = []
for i, fen in enumerate(positions):
    m_on, s_on, n_on = on.search(fen)
    m_off, s_off, n_off = off.search(fen)
    rows.append((i, fen, m_on, s_on, n_on, m_off, s_off, n_off))
    if (i + 1) % 25 == 0:
        print("  %d/%d" % (i + 1, len(positions)), flush=True)
on.close()
off.close()

with open(os.path.join(outdir, "corrhist_strength.txt"), "w") as fh:
    fh.write("build PC r15, Threads 1, depth %d, PC20 held constant with CorrHistV2 toggled\n" % depth)
    fh.write("%d positions from %s\n\n" % (len(rows), fens))
    fh.write("%-4s %-8s %-10s %-10s %-6s\n" % ("idx", "move_on", "score_on", "move_off/score_off", "same"))
    same = 0
    score_diff = 0
    for i, fen, mo, so, no, mf, sf, nf in rows:
        eq = (mo == mf)
        same += eq
        if so != sf:
            score_diff += 1
        fh.write("%-4d %-8s %-10s %-10s %-6s\n" % (i, mo, str(so), str(mf) + "/" + str(sf),
                                                   "yes" if eq else "NO"))
    fh.write("\n## summary\n")
    fh.write("positions: %d\n" % len(rows))
    fh.write("same bestmove: %d (%.1f %%)\n" % (same, 100.0 * same / len(rows)))
    fh.write("different bestmove: %d (%.1f %%)\n" % (len(rows) - same, 100.0 * (len(rows) - same) / len(rows)))
    fh.write("different score: %d\n" % score_diff)
    tot_on = sum(r[4] for r in rows)
    tot_off = sum(r[7] for r in rows)
    fh.write("total nodes on:  %d\n" % tot_on)
    fh.write("total nodes off: %d\n" % tot_off)
    if tot_off:
        fh.write("node change: %+.2f %%\n" % (100.0 * (tot_on - tot_off) / tot_off))
    fh.write("\nA differing move means the two settings PLAY DIFFERENT CHESS. It is not by itself evidence\n")
    fh.write("that either is stronger; a node saving plus a different move needs games to adjudicate.\n")
print(open(os.path.join(outdir, "corrhist_strength.txt")).read()[-1600:])
