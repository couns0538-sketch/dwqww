#!/usr/bin/env python3
"""Bestmove-mismatch rate under the EXACT job-3 protocol, measured on several position sets.

Protocol (identical to job3/harness_search.py, no changes):
  Threads 1, Hash 16, S14 through 14 setoption lines (each followed by isready, all lines read),
  ucinewgame + isready before EVERY go, `position fen <FEN>` + isready, `go depth 10`.
  Both halves searched in the SAME process, original first then its mirror (job-3 behaviour).
  OwnBook: NOT set in job 3 (recorded as a scoping fact); this script sets it false and says so,
  and reports both so the difference is visible.

usage: rate_sets.py EXE DEPTH LABEL FENFILE [LABEL FENFILE ...]
"""
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


class E:
    def __init__(self, exe, ownbook):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.w("uci")
        while self.r().strip() != "uciok":
            pass
        opts = [("Threads", "1"), ("Hash", "16")]
        if ownbook:
            opts.insert(0, ("OwnBook", "false"))
        for n, v in opts + S14:
            self.w("setoption name %s value %s" % (n, v))
            self.w("isready")
            self.ready()

    def w(self, c):
        self.p.stdin.write(c + "\n")
        self.p.stdin.flush()

    def r(self):
        line = self.p.stdout.readline()
        if line == "":
            raise RuntimeError("died")
        return line

    def ready(self):
        while True:
            line = self.r().strip()
            if any(m in line for m in ("unknown option", "invalid value")):
                raise RuntimeError(line)
            if line == "readyok":
                return

    def go(self, fen, d):
        self.w("ucinewgame")
        self.w("isready")
        self.ready()
        self.w("position fen " + fen)
        self.w("isready")
        self.ready()
        self.w("go depth %d" % d)
        last = None
        while True:
            line = self.r().strip()
            if " pv " in line and line.startswith("info"):
                last = line
            if line.startswith("bestmove"):
                bm = line.split()[1]
                break
        t = last.split() if last else []
        return {"bm": bm,
                "kind": t[t.index("score") + 1] if "score" in t else None,
                "score": int(t[t.index("score") + 2]) if "score" in t else None,
                "nodes": int(t[t.index("nodes") + 1]) if "nodes" in t else None}


def rate(exe, fens, depth, ownbook):
    ea, eb = E(exe, ownbook), E(exe, ownbook)
    n = bm_diff = sc_diff = 0
    for fen in fens:
        mfen = chess.Board(fen).mirror().fen()
        a = ea.go(fen, depth)
        b = eb.go(mfen, depth)
        n += 1
        if b["bm"] != mir(a["bm"]):
            bm_diff += 1
        if a["kind"] != b["kind"] or a["score"] != b["score"]:
            sc_diff += 1
    ea.p.kill()
    eb.p.kill()
    return n, bm_diff, sc_diff


def main():
    exe, depth = sys.argv[1], int(sys.argv[2])
    rest = sys.argv[3:]
    pairs = [(rest[i], rest[i + 1]) for i in range(0, len(rest), 2)]
    print("| set | positions | bestmoves mismatched | rate | scores differed | rate | OwnBook false |")
    print("|---|---|---|---|---|---|---|")
    for label, path in pairs:
        fens = [l.strip() for l in open(path) if l.strip()]
        for ownbook in (False, True):
            n, bm, sc = rate(exe, fens, depth, ownbook)
            print("| %s | %d | %d | %.1f%% | %d | %.1f%% | %s |"
                  % (label, n, bm, 100.0 * bm / max(n, 1), sc, 100.0 * sc / max(n, 1), ownbook))


if __name__ == "__main__":
    main()
