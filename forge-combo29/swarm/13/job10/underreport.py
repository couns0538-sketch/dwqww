#!/usr/bin/env python3
"""Reproduce attempt for another seat's "under-reported mate at go nodes 20000" on endgame boards.

Their finding: at `go nodes 20000` on endgame boards, the engine claims a mate distance its own PV
does not deliver (2 of 14 boards).

My harness asks the strict question, at `go nodes 20000` only:
    claim mate +M  ->  does the engine's own PV reach CHECKMATE within 2M-1 plies?
    claim mate -M  ->  does the opponent force mate within 2|M|-1 plies after the first move?
plus, independently of the claim, does the PV reach mate at all, and at which ply.

TWO DISCIPLINES are run, because a shared-process (warm TT) run is a known source of different node
counts on this engine (seat 10's warm/cold finding) and could produce exactly such a claim:
  FRESH  : one fresh engine process per search, PC20 applied, Threads 1, Hash 16
  SHARED : ONE process for the whole position list, `ucinewgame` between searches (cold-ish board
           but a process that has run before), PC20, Threads 1, Hash 16
Each position is searched REP times in each discipline.

Position set: the 21 job-9 mate positions + the 6 job-9b lost positions = 27 boards.

Usage: underreport.py EXE POSITIONS OUTDIR [REPS] [NODES]
"""
import json
import os
import re
import subprocess
import sys

import chess

EXE = sys.argv[1]
POSFILE = sys.argv[2]
OUTDIR = sys.argv[3]
REPS = int(sys.argv[4]) if len(sys.argv) > 4 else 5
NODES = int(sys.argv[5]) if len(sys.argv) > 5 else 20000
os.makedirs(OUTDIR, exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC6 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]
PC20 = [("Threads", "1"), ("Hash", "16")] + S14 + PC6
BAD = ("unknown option", "invalid value", "error")


def pv_mates_at(fen, pv):
    """Ply at which this PV delivers checkmate, or None."""
    if not pv:
        return None
    b = chess.Board(fen)
    for i, u in enumerate(pv, 1):
        try:
            m = chess.Move.from_uci(u)
        except ValueError:
            return None
        if m not in b.legal_moves:
            return None
        b.push(m)
        if b.is_checkmate():
            return i
    return None


def forces_mate(b, n):
    if n <= 0:
        return False
    moves = list(b.legal_moves)
    if not moves:
        return False
    for m in moves:
        b.push(m)
        if b.is_checkmate():
            b.pop()
            return True
        if n >= 2:
            opp = list(b.legal_moves)
            if opp:
                all_mated = True
                for om in opp:
                    b.push(om)
                    ok = forces_mate(b, n - 2)
                    b.pop()
                    if not ok:
                        all_mated = False
                        break
                if all_mated:
                    b.pop()
                    return True
        b.pop()
    return False


def side_is_mated_within(b, n):
    if b.is_checkmate():
        return True
    if not b.legal_moves:
        return False
    for m in b.legal_moves:
        b.push(m)
        ok = forces_mate(b, n - 1)
        b.pop()
        if ok:
            return True
    return False


class Eng:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        opts = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: died in uci handshake")
            l = l.rstrip("\n")
            if l.startswith("option name"):
                opts.append(l)
            if l == "uciok":
                break
        for n, v in PC20:
            if not any(o.startswith("option name %s " % n) for o in opts):
                raise SystemExit("FAIL: option %r not advertised" % n)
            self.send("setoption name %s value %s" % (n, v))
            self.ready()

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def ready(self):
        self.send("isready")
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: died waiting readyok")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if l == "readyok":
                return

    def search(self, fen):
        self.send("ucinewgame")
        self.send("position fen " + fen)
        self.ready()
        self.send("go nodes %d" % NODES)
        last = None
        bm = None
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: died during search")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if l.startswith("bestmove"):
                bm = l
                break
            if l.startswith("info depth"):
                last = l
        mt = re.search(r"score mate (-?\d+)", last) if last else None
        cp = re.search(r"score cp (-?\d+)", last) if last else None
        dp = re.search(r"\bdepth (\d+)", last) if last else None
        nd = re.search(r"\bnodes (\d+)", last) if last else None
        pv = last.split(" pv ", 1)[1].split() if last and " pv " in last else []
        return {"mate": int(mt.group(1)) if mt else None,
                "cp": int(cp.group(1)) if cp else None,
                "depth": int(dp.group(1)) if dp else None,
                "nodes": int(nd.group(1)) if nd else None,
                "bestmove": bm, "pv": pv}

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def judge(fen, r):
    """Decide whether this run's mate claim is delivered. None for non-mate scores."""
    m = r["mate"]
    d = pv_mates_at(fen, r["pv"])
    if m is None:
        return {"claim": None, "pv_mate_ply": d, "verdict": "no_mate_claim"}
    if m > 0:
        need = 2 * m - 1
        ok = d is not None and d <= need
        return {"claim": m, "need_plies": need, "pv_mate_ply": d,
                "verdict": "delivered" if ok else "UNDER_REPORTED_OR_WRONG"}
    # m < 0: the opponent forces the mate; check that exhaustively
    need = 2 * abs(m) - 1
    ok = side_is_mated_within(chess.Board(fen), 2 * abs(m))
    return {"claim": m, "need_plies": 2 * abs(m), "pv_mate_ply": d,
            "verdict": "delivered" if ok else "UNDER_REPORTED_OR_WRONG"}


def main():
    pos = json.load(open(POSFILE))
    boards = []
    for p in pos:
        if isinstance(p, str):
            boards.append({"fen": p, "true_mate_plies": None, "note": "lost position (job 9b)"})
        else:
            boards.append(p)
    print("boards:", len(boards), "reps per discipline:", REPS, "nodes:", NODES)

    rows = []
    # FRESH discipline: new process per search
    for bi, b in enumerate(boards):
        for rep in range(REPS):
            e = Eng()
            r = e.search(b["fen"])
            e.close()
            j = judge(b["fen"], r)
            rows.append({"discipline": "fresh", "board": bi, "rep": rep,
                         "fen": b["fen"], "true_mate_plies": b.get("true_mate_plies"),
                         "note": b.get("note", ""), **r, **j})
    print("fresh done", flush=True)

    # SHARED discipline: one process, ucinewgame between
    e = Eng()
    for bi, b in enumerate(boards):
        for rep in range(REPS):
            r = e.search(b["fen"])
            j = judge(b["fen"], r)
            rows.append({"discipline": "shared", "board": bi, "rep": rep,
                         "fen": b["fen"], "true_mate_plies": b.get("true_mate_plies"),
                         "note": b.get("note", ""), **r, **j})
    e.close()
    print("shared done", flush=True)

    claims = [r for r in rows if r["claim"] is not None]
    bad = [r for r in claims if r["verdict"] == "UNDER_REPORTED_OR_WRONG"]
    summary = {
        "boards": len(boards),
        "reps_per_discipline": REPS,
        "nodes": NODES,
        "runs": len(rows),
        "runs_with_mate_claim": len(claims),
        "runs_with_cp": len([r for r in rows if r["claim"] is None and r["cp"] is not None]),
        "under_reported": len(bad),
        "boards_affected": len({r["fen"] for r in bad}),
        "fresh_runs": len([r for r in rows if r["discipline"] == "fresh"]),
        "shared_runs": len([r for r in rows if r["discipline"] == "shared"]),
        "under_reported_fresh": len([r for r in bad if r["discipline"] == "fresh"]),
        "under_reported_shared": len([r for r in bad if r["discipline"] == "shared"]),
    }
    json.dump({"summary": summary, "under_reported_detail": bad, "rows": rows},
              open(os.path.join(OUTDIR, "underreport.json"), "w"), indent=1)
    print()
    for k, v in summary.items():
        print("%-32s %s" % (k, v))
    if bad:
        print()
        print("UNDER-REPORTED RUNS:")
        for r in bad:
            print("  %s board %d rep %d: claim %d need %s, PV mates at %s"
                  % (r["discipline"], r["board"], r["rep"], r["claim"],
                     r.get("need_plies"), r["pv_mate_ply"]))
            print("    FEN", r["fen"])
            print("    PV ", " ".join(r["pv"]))


main()
