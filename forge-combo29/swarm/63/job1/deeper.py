"""Two harder questions about the repair's behaviour.

Q-A  Does the repair's scan ever run on a root that is NOT adjudicated drawn? (Counter
     evidence for "cost paid on every search".) Tested on 120 real middlegame/endgame
     positions drawn from random legal games, so mobility is realistic.

Q-B  On a drawn root with `go infinite` + `stop`, does the patched build still answer with
     exactly one info line and one bestmove, and does `stop` arrive safely?

Q-C  The same drawn root at `go movetime 50` and `go nodes 100000`: does the repair change
     what the engine answers when the limit is not a depth?
"""
import json
import random
import statistics
import subprocess
import sys
import time

import chess

sys.path.insert(0, "/home/ubuntu/job")
from ucih import Engine, EngineError  # noqa: E402

PROBE = "/home/ubuntu/b_probe/forge"
BASE = "/home/ubuntu/b_base/forge"
PATCHED = "/home/ubuntu/b_patched/forge"
SEED = 63001


def random_positions(n, seed=SEED):
    """Real positions from random legal games: mobility is realistic, not constructed."""
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        b = chess.Board()
        plies = rng.randint(20, 120)
        for _ in range(plies):
            moves = list(b.legal_moves)
            if not moves or b.is_game_over():
                break
            b.push(rng.choice(moves))
        if b.is_game_over() or not b.is_valid():
            continue
        if b.is_check():
            continue
        out.append((b.fen(), b.legal_moves.count(), b.halfmove_clock))
    return out


def probe_counters(fen, depth=10):
    import os
    import re
    env = dict(os.environ, SCANPROBE="1")
    script = "uci\nisready\nucinewgame\nisready\nposition fen %s\nisready\ngo depth %d\n" % (fen, depth)
    e = Engine(PROBE)
    try:
        e.send("ucinewgame")
        e.position(fen)
        e.go("go depth %d" % depth, timeout=300)
    finally:
        e.quit()
    return None


def main():
    print("== Q-A: does the scan run on non-drawn roots? (120 random real positions) ==")
    pos = random_positions(120)
    legal_counts = [n for _, n, _ in pos]
    print("legal moves: min=%d median=%d max=%d" % (min(legal_counts),
          statistics.median(legal_counts), max(legal_counts)))
    print("positions with 30+ legal moves: %d of %d" % (sum(1 for n in legal_counts if n >= 30), len(pos)))

    scanned = 0
    total = 0
    import os
    import re
    for fen, nlegal, hm in pos:
        env = dict(os.environ, SCANPROBE="1")
        script = ("uci\nisready\nucinewgame\nisready\nposition fen %s\nisready\ngo depth 8\nquit\n" % fen)
        p = subprocess.run([PROBE], input=script, capture_output=True, text=True, env=env, timeout=300)
        kv = {}
        for line in p.stderr.splitlines():
            if line.startswith("SCANPROBE"):
                d = {k: int(v) for k, v in re.findall(r"(\w+)=(\d+)", line)}
                if d.get("roots", 0) >= 1:
                    kv = d
        total += 1
        if kv.get("scanned_roots", 0) > 0:
            scanned += 1
    print("searches=%d, searches that entered the scan=%d" % (total, scanned))

    print("\n== Q-B: go infinite + stop on a drawn root ==")
    drawn = "8/8/3k4/8/2Q1B3/8/3K4/8 w - - 100 1"
    assert chess.Board(drawn).is_valid()
    for tag, exe in (("base", BASE), ("patched", PATCHED)):
        e = Engine(exe)
        try:
            e.send("ucinewgame")
            e.position(drawn)
            e.send("go infinite")
            time.sleep(0.30)
            e.send("stop")
            t0 = time.monotonic()
            # read to bestmove
            lines = []
            bm = None
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                try:
                    line = e.q.get(timeout=max(0.01, deadline - time.monotonic()))
                except Exception:
                    break
                if line is None:
                    break
                lines.append(line)
                if line.startswith("bestmove"):
                    bm = line.split()[1]
                    break
            dt = (time.monotonic() - t0) * 1000
            info = [l for l in lines if l.startswith("info depth")]
            print("%-8s stop->bestmove %.0f ms, info_lines=%d, bestmove=%s, depths=%r" %
                  (tag, dt, len(info), bm,
                   [int(l.split()[2]) for l in info]))
        finally:
            e.quit()

    print("\n== Q-C: limits that are not depth, on the same drawn root ==")
    for gocmd in ("go movetime 50", "go nodes 100000", "go depth 3"):
        for tag, exe in (("base", BASE), ("patched", PATCHED)):
            e = Engine(exe)
            try:
                e.send("ucinewgame")
                e.position(drawn)
                lines, bm, info = e.go(gocmd, timeout=120)
                print("%-8s %-18s info=%d bestmove=%s last=%s" %
                      (tag, gocmd, len(info), bm, info[-1] if info else "NONE"))
            finally:
                e.quit()


if __name__ == "__main__":
    main()
