#!/usr/bin/env python3
"""Decisive state probe for the colour-mirror search asymmetry (area 6).

Three modes, SAME 353 G pairs, depth 10, S14, Threads 1, Hash 16, OwnBook false:

  fresh    : each search is the FIRST search in a brand-new process (ucinewgame first, nothing
             searched before it). No cross-search state can exist. Position and its mirror each
             get their own process.
  same     : ONE process for the pair, original searched first, then its mirror.
             (This is what the original job-3 harness did.)
  reverse  : ONE process for the pair, mirror searched first, then the original.

Each process sends: uci, setoption OwnBook false, Threads 1, Hash 16, S14..., then for every search
ucinewgame + isready (which clears TT, history, killers, correction history and the pawn cache, see
Searcher::clear / Worker::clear), position fen + isready, go depth N.

Outcomes are appended as JSON lines; analyse_state.py compares the three modes.

usage: probe_state.py MODE EXE FENFILE OUTFILE META DEPTH
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
ERROR_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        self.name = None
        while True:
            line = self.readline()
            if line.startswith("id name"):
                self.name = line.strip()
            if line.strip() == "uciok":
                break
        self.sent = []
        for n, v in [("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")] + S14:
            self.send("setoption name %s value %s" % (n, v))
            self.send("isready")
            self.wait_ready()
            self.sent.append("setoption name %s value %s" % (n, v))
        self.send("isready")
        self.wait_ready()
        self.searches = 0

    def send(self, c):
        self.p.stdin.write(c + "\n")
        self.p.stdin.flush()

    def readline(self):
        line = self.p.stdout.readline()
        if line == "":
            raise RuntimeError("engine died")
        return line

    def wait_ready(self):
        while True:
            line = self.readline().strip()
            if any(m in line for m in ERROR_MARKERS):
                raise RuntimeError(line)
            if line == "readyok":
                return

    def search(self, fen, depth):
        self.send("ucinewgame")
        self.send("isready")
        self.wait_ready()
        self.send("position fen " + fen)
        self.send("isready")
        self.wait_ready()
        self.send("go depth %d" % depth)
        pv = None
        while True:
            line = self.readline().strip()
            if " pv " in line and line.startswith("info"):
                pv = line
            if line.startswith("bestmove"):
                bm = line.split()[1]
                break
        self.searches += 1
        t = pv.split() if pv else []
        return {"bm": bm,
                "kind": t[t.index("score") + 1] if "score" in t else None,
                "score": int(t[t.index("score") + 2]) if "score" in t else None,
                "nodes": int(t[t.index("nodes") + 1]) if "nodes" in t else None,
                "pv": t[t.index("pv") + 1:] if "pv" in t else [],
                "search_index_in_process": self.searches - 1}

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    mode, exe, fenfile, outfile, metafile, depth = sys.argv[1:7]
    depth = int(depth)
    fens = [l.strip() for l in open(fenfile) if l.strip()]
    meta = ["exe_started: " + exe, "exe_sha256: " + sha256(exe), "mode: " + mode,
            "fenfile: " + fenfile, "fenfile_sha256: " + sha256(fenfile),
            "depth: %d" % depth,
            "ownbook: setoption name OwnBook value false (sent in every process)",
            "clear_between_searches: ucinewgame + isready",
            "positions: %d" % len(fens)]
    out = open(outfile, "w")
    for i, fen in enumerate(fens):
        mfen = chess.Board(fen).mirror().fen()
        if mode == "fresh":
            e1 = Engine(exe)
            if i == 0:
                meta.append("id_name: " + str(e1.name))
                meta.append("option_lines_sent: " + "; ".join(e1.sent))
            a = e1.search(fen, depth)
            e1.quit()
            e2 = Engine(exe)
            b = e2.search(mfen, depth)
            e2.quit()
        elif mode in ("same", "reverse"):
            e = Engine(exe)
            if i == 0:
                meta.append("id_name: " + str(e.name))
                meta.append("option_lines_sent: " + "; ".join(e.sent))
            if mode == "same":
                a = e.search(fen, depth)
                b = e.search(mfen, depth)
            else:
                b = e.search(mfen, depth)
                a = e.search(fen, depth)
            e.quit()
        else:
            raise SystemExit("bad mode " + mode)
        out.write(json.dumps({"index": i, "fen": fen, "mfen": mfen, "self": a, "mirror": b}) + "\n")
        if (i + 1) % 25 == 0:
            out.flush()
            print("... %d/%d" % (i + 1, len(fens)), flush=True)
    out.close()
    with open(metafile, "w") as fh:
        fh.write("\n".join(meta) + "\n")
    print("mode=%s rows=%d" % (mode, len(fens)))


if __name__ == "__main__":
    main()
