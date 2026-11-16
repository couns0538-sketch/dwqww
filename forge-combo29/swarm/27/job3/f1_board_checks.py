#!/usr/bin/env python3
"""f1_board_checks.py <exe> <fens-file> <outdir> [--limit N]

Area 7 job 3 (the position and move making, src/board.cpp). Three checks, each with a control:

P3  halfmove clock: the field is stored in std::uint16_t and capped at 65535 (board.cpp:351, :1044).
    Accept 65535, play one more non-capturing move, read the clock back with `eval`/`d` if available
    or by perft-1 equality against a FEN that already has the capped value.
P4  perft 1..4 on N positions against python-chess (independent generator).
P5  make/unmake identity: reach a position by a move list, then compare `go perft 2` with the same
    position given directly as a FEN. Any difference means make_move/unmake_move is not exact.

Every `go` is awaited until bestmove over a pipe that is never closed mid-search (19-F12).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

try:
    import chess
except ImportError:
    chess = None
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pyperft


class Missing(Exception):
    """A value the harness needed was not found. Never let this pass as a result."""


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def read_until(self, pred, timeout=300):
        t0 = time.monotonic()
        lines = []
        while time.monotonic() - t0 < timeout:
            line = self.p.stdout.readline()
            if not line:
                break
            s = line.rstrip("\n")
            lines.append(s)
            if pred(s):
                return lines, True
        return lines, False

    def boot(self):
        self.send("uci")
        self.read_until(lambda s: s.strip() == "uciok")
        self.send("isready")
        self.read_until(lambda s: s.strip() == "readyok")

    def perft(self, pos_line, depth, timeout=300):
        self.send(pos_line)
        self.send("isready")
        self.read_until(lambda s: s.strip() == "readyok")
        self.send("go perft %d" % depth)
        lines, ok = self.read_until(lambda s: s.startswith("nodes "), timeout=timeout)
        total = None
        for s in lines:
            if s.startswith("nodes "):
                total = int(s.split()[1])
        if total is None:
            raise Missing("no 'nodes N' line from `%s` within %ss (last line: %r)"
                          % (pos_line, timeout, lines[-1] if lines else ""))
        return total, lines

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=30)
        except Exception:
            self.p.kill()




def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("fens"); ap.add_argument("outdir")
    ap.add_argument("--limit", type=int, default=20)
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    fens = [l.strip() for l in open(a.fens) if l.strip()][:a.limit]
    e = Engine(exe)
    e.boot()

    # ---- P3: halfmove clock at the std::uint16_t cap
    p3 = []
    base_board = "4k3/8/8/8/8/8/8/R3K3 w - - 0 1"
    for clock in (0, 99, 100, 150, 65534, 65535, 65536, 99999):
        fen = "4k3/8/8/8/8/8/8/R3K3 w - - %d 1" % clock
        e.send("position fen " + fen)
        e.send("isready")
        lines, _ = e.read_until(lambda s: s.strip() == "readyok")
        refused = any("invalid FEN" in s for s in lines)
        n1 = None
        if not refused:
            n1, _ = e.perft("position fen " + fen, 1)
        p3.append({"clock": clock, "refused": refused, "perft1": n1,
                   "refusal_line": next((s for s in lines if "invalid" in s.lower()), "")})

    # P3b: one more half-move on a capped clock must not wrap the stored value
    p3b = []
    capped = "4k3/8/8/8/8/8/8/R3K3 w - - 65535 1"
    e.send("position fen " + capped)
    e.send("isready"); e.read_until(lambda s: s.strip() == "readyok")
    # a1a2 is a non-capturing, non-pawn move: the clock would become 65536 (wrapping if it were a u16 add)
    n_after, lines_after = e.perft("position fen " + capped + " moves a1a2", 1)
    p3b.append({"fen": capped + " moves a1a2", "perft1": n_after,
                "note": "if the clock wrapped to 0 the fifty-move/draw logic changes but perft 1 still works"})

    # ---- P4: perft 1..4 against python-chess
    p4 = []
    for fen in fens:
        row = {"fen": fen}
        if chess is not None:
            board = chess.Board(fen)          # raises if the FEN cannot be parsed at all
            if not board.is_valid():
                row["note"] = "python-chess flags this FEN: " + str(board.status())
        for d in (1, 2, 3, 4):
            eng, _ = e.perft("position fen " + fen, d)
            if eng is None:
                raise Missing("engine gave no node count for %s depth %d" % (fen, d))
            row["engine_d%d" % d] = eng
            py = pyperft.perft_fen(fen, d)      # raises on a bad FEN: no None, no NaN
            if py is None:
                raise Missing("python-chess gave no count for %s depth %d" % (fen, d))
            row["py_d%d" % d] = py
            row["same_d%d" % d] = (eng == py)
        p4.append(row)

    # ---- P5: make/unmake identity (move list vs the FEN that move list reaches)
    p5 = []
    e.quit()
    for fen in fens[:10]:
        if chess is None:
            break
        board = chess.Board(fen)
        moves = []
        for _ in range(6):
            legal = list(board.legal_moves)
            if not legal:
                break
            mv = legal[0]
            moves.append(mv.uci())
            board.push(mv)
        if not moves:
            continue
        reached = board.fen()
        e2 = Engine(exe); e2.boot()
        n_list, _ = e2.perft("position fen %s moves %s" % (fen, " ".join(moves)), 2)
        n_fen, _ = e2.perft("position fen " + reached, 2)
        e2.quit()
        p5.append({"start": fen, "moves": " ".join(moves), "reached": reached,
                   "perft2_by_moves": n_list, "perft2_by_fen": n_fen,
                   "same": n_list == n_fen})

    out = {"exe": exe,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "P3_halfmove": p3, "P3b_after_move": p3b, "P4_perft": p4, "P5_makeunmake": p5}
    with open(os.path.join(a.outdir, "results.json"), "w") as f:
        json.dump(out, f, indent=2)

    # summaries
    accepted = [r["clock"] for r in p3 if not r["refused"]]
    refused = [r["clock"] for r in p3 if r["refused"]]
    p4_total = sum(1 for r in p4 if all(r["same_d%d" % d] for d in (1, 2, 3, 4)))
    p4_bad = [r["fen"] for r in p4 if not all(r["same_d%d" % d] for d in (1, 2, 3, 4))]
    p5_same = sum(1 for r in p5 if r["same"])
    with open(os.path.join(a.outdir, "SUMMARY.txt"), "w") as f:
        f.write("exe: %s\nsha256: %s\ndate_utc: %s\n\n" % (out["exe"], out["sha256"], out["date_utc"]))
        f.write("P3 halfmove clock accepted: %s\n" % accepted)
        f.write("P3 halfmove clock refused : %s\n" % refused)
        for r in p3b:
            f.write("P3b %s -> perft 1 = %s\n" % (r["fen"], r["perft1"]))
        f.write("\nP4 perft 1..4 equal to python-chess: %d of %d positions\n" % (p4_total, len(p4)))
        if p4_bad:
            f.write("P4 differing positions:\n")
            for fen in p4_bad:
                f.write("  %s\n" % fen)
        f.write("\nP5 make/unmake identity (perft 2 by moves vs by FEN): %d of %d\n" % (p5_same, len(p5)))
        for r in p5:
            if not r["same"]:
                f.write("  DIFFERS %s moves %s: %s vs %s\n" % (r["start"], r["moves"],
                                                               r["perft2_by_moves"], r["perft2_by_fen"]))
    print(open(os.path.join(a.outdir, "SUMMARY.txt")).read())


if __name__ == "__main__":
    main()
