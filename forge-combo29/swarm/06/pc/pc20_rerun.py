#!/usr/bin/env python3
"""Re-run seat 06's own findings on the PC r15 build under PC20.

PC20 = Threads 1, Hash 16, the 14 S14 settings, CuckooRep true, HistRework 2, TtPruneV2 true,
CorrHistV2 true, MateAlphaGuard true, OwnBook false. Threads is ALWAYS 1 (owner's rule, 2026-11-16).

Modes:
  eval     - `eval` of each FEN and of its colour mirror (re-tests S-F1); compares hce/nnue/total.
  search   - depth-N search of each FEN and of its colour mirror (re-tests S-F6/S-F7); compares
             bestmove (mirrored), score (EQUAL rule: the colour mirror flips the side to move, so the
             side-to-move-relative score must be equal) and node counts.

usage: pc20_rerun.py eval|search EXE FENFILE OUTFILE META DEPTH
"""
import hashlib
import json
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BAD = ("unknown option", "invalid value", "ERROR")


class E:
    def __init__(self, exe):
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
        for n, v in [("Threads", "1"), ("Hash", "16")] + PC20:
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

    def position(self, fen):
        self.w("position fen " + fen)
        self.w("isready")
        self.ready()

    def eval_fen(self, fen):
        self.position(fen)
        self.w("eval")
        self.w("isready")
        out = None
        while True:
            line = self.r().strip()
            if any(m in line for m in BAD):
                raise RuntimeError(line)
            if line.startswith("info string eval"):
                tok = line.split()
                d = {}
                for k in ("hce", "nnue", "total"):
                    if k in tok:
                        d[k] = int(tok[tok.index(k) + 1])
                out = d
            if line == "readyok":
                return out

    def search(self, fen, depth):
        self.w("ucinewgame")
        self.w("isready")
        self.ready()
        self.position(fen)
        self.w("go depth %d" % depth)
        last = None
        while True:
            line = self.r().strip()
            if any(m in line for m in BAD):
                raise RuntimeError(line)
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

    def quit(self):
        try:
            self.w("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    mode, exe, fenfile, outfile, metafile, depth = sys.argv[1:7]
    depth = int(depth)
    fens = [l.strip() for l in open(fenfile) if l.strip()]
    e = E(exe)
    meta = ["exe_started: " + exe, "exe_sha256: " + sha256(exe), "id_name: " + str(e.name),
            "settings: PC20 (Threads 1, Hash 16, 14 S14 settings, CuckooRep true, HistRework 2,",
            "          TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false)",
            "threads: 1 (owner's rule of 2026-11-16 - no score above Threads 1)",
            "mode: " + mode, "depth: %d" % depth,
            "fenfile: " + fenfile, "fenfile_sha256: " + sha256(fenfile),
            "option_lines_sent: " + "; ".join(e.sent),
            "positions: %d" % len(fens)]
    rows = []
    fails = []
    for i, fen in enumerate(fens):
        try:
            board = chess.Board(fen)
        except Exception as exc:
            fails.append((i, fen, str(exc)))
            continue
        mfen = board.mirror().fen()
        try:
            if mode == "eval":
                a = e.eval_fen(fen)
                b = e.eval_fen(mfen)
            else:
                a = e.search(fen, depth)
                b = e.search(mfen, depth)
        except RuntimeError as exc:
            fails.append((i, fen, str(exc)))
            e = E(exe)
            continue
        rows.append({"index": i, "fen": fen, "mfen": mfen, "self": a, "mirror": b})
    e.quit()
    with open(outfile, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    with open(metafile, "w") as fh:
        fh.write("\n".join(meta) + "\n")
        fh.write("rows: %d\nfailures: %d\n" % (len(rows), len(fails)))
        for f in fails:
            fh.write("FAIL %s\n" % json.dumps(f))
    print("rows=%d failures=%d" % (len(rows), len(fails)))


if __name__ == "__main__":
    main()
