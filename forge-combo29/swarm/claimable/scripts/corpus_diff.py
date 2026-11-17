#!/usr/bin/env python3
"""corpus_diff.py — measure the BLAST RADIUS of the fix over a real corpus.

The claim under test is "the rule only changes answers at roots where a draw is actually
claimable". The way to test it is a differential over many real positions: every non-drawn
root must be bit-identical (same bestmove, same score, same node count), and any root that
differs must be shown to be a claimable-draw root.

Positions come from self-play of the LOCK build, so they are real reachable boards rather
than hand-picked ones. A FEN cannot carry repetition history, which is stated as a limit:
this sweep exercises the fifty-move arm (which a FEN can carry) and the non-drawn majority,
not the repetition arm — the repetition arm is covered by the named fixtures instead.

Usage: corpus_diff.py A_EXE B_EXE --games N --plies M
"""
import argparse
import json
import queue
import re
import subprocess
import sys
import threading
import time

import chess

ENV = {"PATH": "/usr/bin:/bin", "ASAN_OPTIONS": "detect_leaks=0"}
OPENINGS = [
    [],
    ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
    ["d2d4", "d7d5", "c2c4", "e7e6"],
    ["e2e4", "c7c5", "g1f3", "d7d6"],
    ["d2d4", "g8f6", "c2c4", "g7g6"],
    ["e2e4", "e7e6", "d2d4", "d7d5"],
]


class Engine:
    def __init__(self, exe, hash_mb=16):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1, env=ENV)
        self.q = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()
        self.send("uci")
        self.send("setoption name OwnBook value false")
        self.send(f"setoption name Hash value {hash_mb}")
        self.send("setoption name Threads value 1")
        self.await_("uciok")

    def _pump(self):
        try:
            for line in self.p.stdout:
                self.q.put(line.rstrip())
        finally:
            self.q.put(None)

    def send(self, cmd):
        try:
            self.p.stdin.write(cmd + "\n")
            self.p.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    def await_(self, prefix, timeout=300):
        out = []
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                line = self.q.get(timeout=0.3)
            except queue.Empty:
                continue
            if line is None:
                break
            out.append(line)
            if line.startswith(prefix):
                break
        return out

    def search(self, pos, depth):
        self.send("ucinewgame")
        self.send("isready")
        self.await_("readyok")
        self.send(pos)
        self.send("isready")
        self.await_("readyok")
        self.send(f"go depth {depth}")
        out = self.await_("bestmove", timeout=600)
        infos = [x for x in out if x.startswith("info depth")]
        bms = [x for x in out if x.startswith("bestmove")]
        rec = {"bestmove": bms[-1].split()[1] if bms else None, "score": None, "nodes": None}
        if infos:
            m = re.search(r"score (cp|mate) (-?\d+)", infos[-1])
            rec["score"] = f"{m.group(1)} {m.group(2)}" if m else None
            n = re.search(r" nodes (\d+)", infos[-1])
            rec["nodes"] = int(n.group(1)) if n else None
        return rec

    def quit(self):
        self.send("quit")
        try:
            self.p.stdin.close()
            self.p.wait(timeout=15)
        except Exception:
            self.p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--games", type=int, default=6)
    ap.add_argument("--plies", type=int, default=40)
    ap.add_argument("--depth", type=int, default=8)
    ap.add_argument("--out", default="/home/ubuntu/work/ev/corpus_diff.json")
    args = ap.parse_args()

    a, b = Engine(args.a), Engine(args.b)
    rows = []
    try:
        for gi in range(args.games):
            opening = OPENINGS[gi % len(OPENINGS)]
            board = chess.Board()
            for mv in opening:
                board.push_uci(mv)
            moves = list(opening)
            for ply in range(args.plies):
                if board.is_game_over(claim_draw=False):
                    break
                pos = "position startpos" + ((" moves " + " ".join(moves)) if moves else "")
                ra = a.search(pos, args.depth)
                if ra["bestmove"] in (None, "0000", "(none)"):
                    break
                # both engines get the SAME position (by move list), so history is identical
                rb = b.search(pos, args.depth)
                fen = board.fen()
                claimable = board.halfmove_clock >= 100 or board.is_repetition(3)
                # "resets available" is what makes the rule decline the claim
                resets = [m.uci() for m in board.legal_moves
                          if (board.piece_at(m.from_square)
                              and board.piece_at(m.from_square).piece_type == chess.PAWN)
                          or board.is_capture(m)]
                differs = (ra["bestmove"] != rb["bestmove"] or ra["score"] != rb["score"]
                           or ra["nodes"] != rb["nodes"])
                rows.append({"game": gi, "ply": ply, "fen": fen,
                             "halfmove": board.halfmove_clock,
                             "claimable": claimable, "resets": len(resets),
                             "a": ra, "b": rb, "differs": differs})
                try:
                    board.push_uci(ra["bestmove"])
                except ValueError:
                    break
                moves.append(ra["bestmove"])
    finally:
        a.quit()
        b.quit()

    total = len(rows)
    diff = [r for r in rows if r["differs"]]
    claimable_rows = [r for r in rows if r["claimable"]]
    unexplained = [r for r in diff if not r["claimable"]]
    summary = {
        "positions": total,
        "differing": len(diff),
        "claimable_roots": len(claimable_rows),
        "claimable_and_differing": len([r for r in diff if r["claimable"]]),
        "NON_CLAIMABLE_DIFF": len(unexplained),
        "unexplained_examples": unexplained[:10],
        "differing_examples": diff[:10],
    }
    json.dump({"summary": summary, "rows": rows}, open(args.out, "w"), indent=2)
    print(json.dumps(summary, indent=2))
    return 0 if not unexplained else 1


if __name__ == "__main__":
    sys.exit(main())
