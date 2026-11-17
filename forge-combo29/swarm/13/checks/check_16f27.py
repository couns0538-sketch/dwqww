#!/usr/bin/env python3
"""Check of seat 16's S-F27 / S-F29: do identical self-play starts CONVERGE, and do varied starts not?

Their claims:
  S-F27: ten deterministic self-play games from ONE start give only THREE distinct final positions
         (seven of ten identical), because the engine is deterministic at Threads 1 with fixed limits.
  S-F29: ten games from ten DIFFERENT starts give TEN distinct finals — so the convergence was the fixed
         starting point, not a search property.

That matters for self-play training data: if games from one start converge, a data set needs varied starts.

My method, deliberately different from theirs so a shared bug cannot produce a shared answer:
  * fixed-NODE self-play (not the clock), so the "millisecond drift" they cite cannot be the mechanism
    here — determinism is then guaranteed by construction and the question becomes purely about variety;
  * two arms: (a) 10 games from startpos, (b) 10 games from 10 distinct G positions;
  * each game plays DEPTH plies, both sides searched with the same fixed budget, PC20, Threads 1, Hash 16,
    one process per game (fresh), so state cannot carry between games;
  * compare final FENs (the position, ignoring the move counters) and the move sequences.

If the mechanism is "determinism at Threads 1" then arm (a) should give exactly ONE distinct final, not
three — a cleaner and stronger statement than theirs, and my arm (b) tests whether variety restores it.

Usage: selfplay.py EXE FENS OUTDIR [NGAMES] [PLIES] [NODES]
"""
import json
import os
import subprocess
import sys

import chess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
from settings import PC20, describe  # noqa: E402

EXE = sys.argv[1]
FENS = sys.argv[2]
OUTDIR = sys.argv[3]
NGAMES = int(sys.argv[4]) if len(sys.argv) > 4 else 10
PLIES = int(sys.argv[5]) if len(sys.argv) > 5 else 40
NODES = int(sys.argv[6]) if len(sys.argv) > 6 else 4000
os.makedirs(OUTDIR, exist_ok=True)
BAD = ("unknown option", "invalid value", "error")
STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class Eng:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
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
        for n, v in PC20:
            if not any(o.startswith("option name %s " % n) for o in seen):
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
                raise SystemExit("FAIL: engine died")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if l == "readyok":
                return

    def move(self, fen):
        self.send("position fen " + fen)
        self.ready()
        self.send("go nodes %d" % NODES)
        bm = None
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died during search")
            l = l.rstrip("\n")
            if l.startswith("bestmove"):
                bm = l
                break
        return bm.split()[1] if bm and len(bm.split()) > 1 else None

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def key(fen):
    """Position identity the way a repetition check sees it: pieces, side, castling, ep."""
    return " ".join(fen.split()[:4])


def play(start_fen):
    """One self-play game, fresh process. Returns (final position key, move list)."""
    e = Eng()
    b = chess.Board(start_fen)
    moves = []
    for _ in range(PLIES):
        if not b.legal_moves or b.is_game_over(claim_draw=False):
            break
        mv = e.move(b.fen())
        try:
            m = chess.Move.from_uci(mv)
        except (ValueError, TypeError):
            break
        if m not in b.legal_moves:
            moves.append("ILLEGAL:" + str(mv))
            break
        moves.append(mv)
        b.push(m)
    e.close()
    return key(b.fen()), " ".join(moves), b.fen()


def arm(name, starts, rows):
    seen = {}
    for i, fen in enumerate(starts):
        k, seq, full = play(fen)
        rows.append({"arm": name, "game": i, "start": fen, "final_key": k,
                     "final_fen": full, "moves": seq})
        seen.setdefault(k, []).append(i)
        print("  %-8s game %2d final %s..." % (name, i, k[:44]), flush=True)
    return seen


def main():
    g_fens = [l.strip() for l in open(FENS) if l.strip()]
    rows = []
    print("ARM A: %d games from the SAME start (startpos)" % NGAMES)
    a = arm("same_start", [STARTPOS] * NGAMES, rows)
    starts_b = g_fens[:NGAMES]
    print("ARM B: %d games from %d DIFFERENT G positions" % (NGAMES, len(starts_b)))
    b_arm = arm("varied_starts", starts_b, rows)

    def distinct(seen):
        return len(seen)

    def biggest_group(seen):
        return max((len(v) for v in seen.values()), default=0)

    seqs_a = {r["moves"] for r in rows if r["arm"] == "same_start"}
    seqs_b = {r["moves"] for r in rows if r["arm"] == "varied_starts"}
    summary = {
        "exe": os.path.abspath(EXE), "settings": describe(PC20),
        "budget": "go nodes %d" % NODES, "plies_target": PLIES, "games_per_arm": NGAMES,
        "same_start_distinct_finals": distinct(a),
        "same_start_largest_identical_group": biggest_group(a),
        "same_start_distinct_move_sequences": len(seqs_a),
        "varied_start_distinct_finals": distinct(b_arm),
        "varied_start_largest_identical_group": biggest_group(b_arm),
        "varied_start_distinct_move_sequences": len(seqs_b),
        "note": "final positions compared on pieces+side+castling+ep (move counters ignored). "
                "Fixed NODE budget, so clock drift cannot be the divergence mechanism here.",
    }
    json.dump({"summary": summary, "rows": rows},
              open(os.path.join(OUTDIR, "selfplay.json"), "w"), indent=1)
    print()
    for k, v in summary.items():
        print("%-38s %s" % (k, v))


main()
