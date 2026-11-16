#!/usr/bin/env python3
"""Test FORGE_FIX_BARE_KING_LMR_CAP: does the PC build MISS fewer mates in lone-king endings?

The patch claims: with one thread, when the root has a lone king and the node has one, a late move is
reduced by at most one ply; pruning unchanged. Effect claimed: KBB-K 175/300 vs 142, KBN-K 43 vs 35,
KQ-K and KR-K unchanged at 300/300, and mates missed at depth 14 fall from 13 to 1 across 400 searches.

I test the part I can verify honestly: build lone-king positions where python-chess confirms a FORCED
MATE exists within the search depth, then check whether the engine at `go depth 14` reports a mate.
A "missed mate" is a position whose true mate distance is <= 14 plies but where the engine reports a
cp score instead of `mate N`.

IMPORTANT SCOPE LIMIT: the patch's claim is about warm history tables ("after Clear Hash" / "with its
net"). This script uses a FRESH process per position, which is the COLD case, and a SHARED process
variant, which is the warm case. Both are reported separately and neither is silently mixed.

Usage: loneking.py BASE_EXE PC_EXE OUTDIR [MAXPOS] [DEPTH] [TRUE_MATE_MAX_PLIES]
"""
import json
import os
import re
import subprocess
import sys

import chess

BASE_EXE = sys.argv[1]
PC_EXE = sys.argv[2]
OUTDIR = sys.argv[3]
MAXPOS = int(sys.argv[4]) if len(sys.argv) > 4 else 40
DEPTH = int(sys.argv[5]) if len(sys.argv) > 5 else 14
TRUE_MAX = int(sys.argv[6]) if len(sys.argv) > 6 else 9   # true mate within this many plies
os.makedirs(OUTDIR, exist_ok=True)

OPTS = [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")]
BAD = ("unknown option", "invalid value", "error")


def forces_mate(b, n):
    """Side to move forces mate within n plies."""
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


def true_mate_plies(fen, cap=TRUE_MAX):
    b = chess.Board(fen)
    for n in range(1, cap + 1, 2):
        if forces_mate(b, n):
            return n
    return None


def build_positions_from(path):
    """Reuse positions whose true mate distance was ALREADY computed exhaustively (job 9's set),
    instead of rebuilding them expensively here."""
    data = json.load(open(path))
    return [{"fen": d["fen"], "kind": d.get("kind", d.get("note", "reused")),
             "true_mate_plies": d["true_mate_plies"]} for d in data if d.get("true_mate_plies")]


def build_positions():
    """Lone black king vs K + two pieces, at varied king placements, filtered to a FORCED mate
    within TRUE_MAX plies (verified by exhaustive search). Lopsided enough to be a lone-king ending
    while still being a real forced mate rather than a trivial one-mover."""
    configs = [
        ("KQvK", [chess.QUEEN]),
        ("KRvK", [chess.ROOK]),
        ("KRRvK", [chess.ROOK, chess.ROOK]),
        ("KBBvK", [chess.BISHOP, chess.BISHOP]),
        ("KQBrK", [chess.QUEEN, chess.ROOK]),
    ]
    out = []
    wk_squares = [chess.C6, chess.F6, chess.D5, chess.B3, chess.G4, chess.E7]
    for name, pieces in configs:
        got = 0
        for wk in wk_squares:
            for bk in chess.SQUARES:
                if got >= max(1, MAXPOS // len(configs)):
                    break
                if bk == wk or chess.square_distance(bk, wk) <= 1:
                    continue
                b = chess.Board(None)
                b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                free = [s for s in chess.SQUARES
                        if s not in (wk, bk)]
                # deterministic placement: spread the pieces over a coarse grid of squares
                cand = [free[i] for i in range(0, len(free), 7)][:len(pieces)]
                if len(cand) < len(pieces):
                    continue
                for sq, pt in zip(cand, pieces):
                    b.set_piece_at(sq, chess.Piece(pt, chess.WHITE))
                b.turn = chess.WHITE
                if not b.is_valid() or b.is_check():
                    continue
                if b.status() & chess.STATUS_OPPOSITE_CHECK:
                    continue
                d = true_mate_plies(b.fen())
                if d is not None:
                    out.append({"fen": b.fen(), "kind": name, "true_mate_plies": d})
                    got += 1
            if got >= max(1, MAXPOS // len(configs)):
                break
    return out[:MAXPOS]


class Eng:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)

        def send(s):
            self.p.stdin.write(s + "\n")
            self.p.stdin.flush()

        self.send = send
        send("uci")
        seen = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: died in uci handshake")
            l = l.rstrip("\n")
            if l.startswith("option name"):
                seen.append(l)
            if l == "uciok":
                break
        for n, v in OPTS:
            if not any(o.startswith("option name %s " % n) for o in seen):
                continue
            send("setoption name %s value %s" % (n, v))
            send("isready")
            while self.p.stdout.readline().rstrip("\n") != "readyok":
                pass

    def search(self, fen, warm=False):
        if warm:
            self.send("ucinewgame")
        self.send("position fen " + fen)
        self.send("isready")
        while self.p.stdout.readline().rstrip("\n") != "readyok":
            pass
        self.send("go depth %d" % DEPTH)
        last = None
        bm = None
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: died during search")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if l.startswith("info depth"):
                last = l
            if l.startswith("bestmove"):
                bm = l
                break
        mt = re.search(r"score mate (-?\d+)", last) if last else None
        cp = re.search(r"score cp (-?\d+)", last) if last else None
        nd = re.search(r"nodes (\d+)", last) if last else None
        return {"mate": int(mt.group(1)) if mt else None,
                "cp": int(cp.group(1)) if cp else None,
                "nodes": int(nd.group(1)) if nd else None,
                "bestmove": (bm.split()[1] if bm and len(bm.split()) > 1 else None)}

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def main():
    reuse = os.environ.get("REUSE_POSITIONS")
    pos = build_positions_from(reuse) if reuse else build_positions()
    if not pos:
        raise SystemExit("FAIL: no lone-king forced-mate positions were built")
    print("built", len(pos), "positions with a verified forced mate within",
          TRUE_MAX, "plies", flush=True)
    json.dump(pos, open(os.path.join(OUTDIR, "positions.json"), "w"), indent=1)

    rows = []
    for label, exe in (("base", BASE_EXE), ("pc", PC_EXE)):
        # COLD: fresh process per position
        for p in pos:
            e = Eng(exe)
            r = e.search(p["fen"])
            e.close()
            r.update({"build": label, "discipline": "cold", "fen": p["fen"],
                      "kind": p["kind"], "true_mate_plies": p["true_mate_plies"]})
            r["found_mate"] = r["mate"] is not None and r["mate"] > 0
            rows.append(r)
        # WARM: one process, ucinewgame between
        e = Eng(exe)
        for p in pos:
            r = e.search(p["fen"], warm=True)
            r.update({"build": label, "discipline": "warm", "fen": p["fen"],
                      "kind": p["kind"], "true_mate_plies": p["true_mate_plies"]})
            r["found_mate"] = r["mate"] is not None and r["mate"] > 0
            rows.append(r)
        e.close()
        print(label, "done", flush=True)

    def count(build, disc):
        sel = [r for r in rows if r["build"] == build and r["discipline"] == disc]
        return len(sel), sum(1 for r in sel if r["found_mate"])

    summary = {"positions": len(pos), "depth": DEPTH, "true_mate_max_plies": TRUE_MAX,
               "exe_base": os.path.abspath(BASE_EXE), "exe_pc": os.path.abspath(PC_EXE)}
    for disc in ("cold", "warm"):
        for build in ("base", "pc"):
            n, f = count(build, disc)
            summary["%s_%s_mates_found" % (build, disc)] = "%d/%d" % (f, n)
            summary["%s_%s_missed" % (build, disc)] = n - f
    json.dump({"summary": summary, "rows": rows},
              open(os.path.join(OUTDIR, "loneking.json"), "w"), indent=1)
    print()
    for k, v in summary.items():
        print("%-34s %s" % (k, v))


main()
