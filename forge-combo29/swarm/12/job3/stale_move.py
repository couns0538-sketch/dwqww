#!/usr/bin/env python3
"""stale_move.py EXE OUTFILE [--pc20] — is the fabricated bestmove the first root candidate, or a
stale move from an earlier search in the same process?

Seat 19 confirmed the aborted-search fault survives on PC r15 (a2a3 with 0 nodes against the real
answer). The coordinator's question: which move is it really?

Three probes, each in ONE process (that is the whole point — a stale value needs earlier state):

  A  cold abort        position X, `go depth 12`, `quit` at once.
                       If the move is root_candidates.front() of X, this is the first legal move.

  B  warm abort        position X, a REAL `go depth 10` to completion (whose answer is some other
                       move), then `go depth 14` aborted at once.
                       If the aborted answer ECHOES the earlier bestmove, the fault is a stale
                       value and it is worse: it no longer has anything to do with the position.

  C  warm abort, other position
                       position X, real search, then `position Y` (a DIFFERENT first legal move)
                       and an aborted `go`. If the answer is Y's first legal move the fault is
                       positional; if it is X's earlier bestmove it is stale.

For every probe the script also prints the position's own legal-move order (from `go perft 1`,
whose first line is root_candidates.front()), so "first root candidate" is measured, not assumed.
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import chess

SAN = re.compile(r"ERROR: (AddressSanitizer|LeakSanitizer)|SUMMARY: (Address|Undefined|Leak)Sanitizer|runtime error: ")

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# X and Y differ in their first legal move, so "first root candidate" and "stale move" are
# distinguishable. X is kiwipete (first legal move a2a3); Y is a position whose first legal move
# and best move are both clearly different.
X_FEN = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
Y_FEN = "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"


class Eng:
    def __init__(self, exe, opts):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1,
                                  env={"PATH": "/usr/bin:/bin", "ASAN_OPTIONS": "detect_leaks=0",
                                       "UBSAN_OPTIONS": "print_stacktrace=1"})
        self.q = queue.Queue()
        self.lines = []
        threading.Thread(target=self._rd, daemon=True).start()
        self.send("uci")
        self.wait(lambda l: l == "uciok")
        for n, v in opts:
            self.send(f"setoption name {n} value {v}")
            self.send("isready")
            self.wait(lambda l: l == "readyok")

    def _rd(self):
        for ln in self.p.stdout:
            self.q.put(ln.rstrip("\n"))
        self.q.put(None)

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def wait(self, pred, bound=120.0):
        end = time.monotonic() + bound
        while time.monotonic() < end:
            try:
                ln = self.q.get(timeout=0.2)
            except queue.Empty:
                if self.p.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            self.lines.append(ln)
            if pred(ln):
                return ln
        return "TIMEOUT"

    def mark(self):
        """Index into lines; later calls can look only at what came after."""
        return len(self.lines)

    def since(self, idx):
        return self.lines[idx:]

    def close(self, send_quit=True):
        try:
            if send_quit:
                self.send("quit")
            self.p.stdin.close()
        except OSError:
            pass
        try:
            self.p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.wait()
        # drain what the reader thread still holds: without this the last bestmove (the one
        # printed just before exit) can be lost, which is the whole measurement
        end = time.monotonic() + 3.0
        while time.monotonic() < end:
            try:
                ln = self.q.get(timeout=0.1)
            except queue.Empty:
                if self.p.poll() is not None:
                    break
                continue
            if ln is None:
                break
            self.lines.append(ln)
        return self.p.returncode


def bestmoves(lines):
    return [l.split()[1] for l in lines if l.startswith("bestmove")]


def first_legal(exe, fen, opts):
    """root_candidates.front() for FEN, from the engine's own perft 1 order."""
    e = Eng(exe, opts)
    e.send(f"position fen {fen}")
    e.send("isready")
    e.wait(lambda l: l == "readyok")
    e.send("go perft 1")
    e.wait(lambda l: l.startswith("nodes "), 120)
    e.close()
    for l in e.lines:
        m = re.match(r"^([a-h][1-8][a-h][1-8][qrbn]?): \d+$", l)
        if m:
            return m.group(1)
    return None


def probe(exe, opts, kind):
    """Run one probe in a single process; return the aborted answer and its context."""
    e = Eng(exe, opts)
    rec = {"kind": kind}
    if kind == "A_cold_abort":
        e.send(f"position fen {X_FEN}")
        e.send("isready")
        e.wait(lambda l: l == "readyok")
        i = e.mark()
        e.send("go depth 12")
        e.send("quit")
        e.close(send_quit=False)
        seg = e.since(i)
        rec.update(aborted=bestmoves(seg), info_lines=sum(1 for x in seg if x.startswith("info depth")))
    elif kind == "B_warm_abort_same_position":
        e.send(f"position fen {X_FEN}")
        e.send("isready")
        e.wait(lambda l: l == "readyok")
        i = e.mark()
        e.send("go depth 10")
        e.wait(lambda l: l.startswith("bestmove"), 300)
        seg1 = e.since(i)
        real = bestmoves(seg1)
        i2 = e.mark()
        e.send("go depth 14")
        e.send("quit")
        e.close(send_quit=False)
        seg2 = e.since(i2)
        rec.update(real_search=real, aborted=bestmoves(seg2),
                   info_lines=sum(1 for x in seg2 if x.startswith("info depth")))
    elif kind == "C_warm_abort_other_position":
        e.send(f"position fen {X_FEN}")
        e.send("isready")
        e.wait(lambda l: l == "readyok")
        i = e.mark()
        e.send("go depth 10")
        e.wait(lambda l: l.startswith("bestmove"), 300)
        real = bestmoves(e.since(i))
        e.send(f"position fen {Y_FEN}")
        e.send("isready")
        e.wait(lambda l: l == "readyok")
        i2 = e.mark()
        e.send("go depth 14")
        e.send("quit")
        e.close(send_quit=False)
        seg2 = e.since(i2)
        rec.update(real_search=real, aborted=bestmoves(seg2),
                   info_lines=sum(1 for x in seg2 if x.startswith("info depth")))
    rec["sanitizer_lines"] = [l for l in e.lines if SAN.search(l)][:4]
    return rec


def legal_in(fen, mv):
    if not mv or mv in ("0000", "(none)"):
        return None
    try:
        return chess.Move.from_uci(mv) in chess.Board(fen).legal_moves
    except ValueError:
        return False


def main():
    exe, outfile = sys.argv[1], sys.argv[2]
    opts = PC20 if "--pc20" in sys.argv else []
    label = "PC20" if opts else "none"
    print(f"exe {exe}")
    print(f"settings {label}  (Threads 1: no Threads option is sent)")

    fx, fy = first_legal(exe, X_FEN, opts), first_legal(exe, Y_FEN, opts)
    print(f"X first legal move (root_candidates.front): {fx}")
    print(f"Y first legal move (root_candidates.front): {fy}")

    out = {"exe": exe, "settings": label, "X_first": fx, "Y_first": fy, "probes": []}
    print(f"\n{'probe':32} {'real search':12} {'aborted':9} {'info':>4}  verdict")
    for kind in ("A_cold_abort", "B_warm_abort_same_position", "C_warm_abort_other_position"):
        r = probe(exe, opts, kind)
        ab = r["aborted"][0] if r.get("aborted") else None
        real = (r.get("real_search") or [None])[0]
        fen_used = X_FEN if kind != "C_warm_abort_other_position" else Y_FEN
        verdict = ""
        if kind == "A_cold_abort":
            verdict = ("FIRST ROOT CANDIDATE" if ab == fx
                       else f"NOT the first root candidate ({fx})")
        elif kind == "B_warm_abort_same_position":
            verdict = ("ECHOES the earlier search -> STALE, worse"
                       if ab == real else "not the earlier answer -> positional")
        else:
            if ab == fy:
                verdict = "Y's first root candidate -> positional, not stale"
            elif ab == real:
                verdict = "X's earlier bestmove -> STALE ACROSS POSITIONS, worse"
            else:
                verdict = "neither -> investigate"
        r["verdict"] = verdict
        r["aborted_legal_in_position"] = legal_in(fen_used, ab)
        out["probes"].append(r)
        print(f"{kind:32} {str(real):12} {str(ab):9} {r['info_lines']:>4}  {verdict}")

    n_san = sum(len(r["sanitizer_lines"]) for r in out["probes"])
    print(f"\nsanitizer lines across all probes: {n_san}")
    Path(outfile).write_text(json.dumps(out, indent=1) + "\n")
    print(f"raw -> {outfile}")


if __name__ == "__main__":
    main()
