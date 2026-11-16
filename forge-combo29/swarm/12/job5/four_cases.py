#!/usr/bin/env python3
"""four_cases.py — the four cases the coordinator named, on whichever builds are given.

1. fifty-move CLAIMABLE with a reset available   (must stop being cp 0)
2. repetition where the WINNING side moves        (must stop being cp 0)
3. repetition where the LOSING side moves         (cp 0 is CORRECT and must stay)
4. genuine forced draw, K v K                     (cp 0 is CORRECT and must stay — the control a
                                                   bad fix breaks)

Usage: four_cases.py EXE LABEL [EXE LABEL ...]
Prints one table per build; Threads 1 (no Threads option is sent anywhere).
"""
import queue
import re
import subprocess
import sys
import threading
import time

import chess

POS = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def ask(exe, posline, depth=12, extra=""):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1,
                         env={"PATH": "/usr/bin:/bin", "ASAN_OPTIONS": "detect_leaks=0"})
    q = queue.Queue()
    out = []
    threading.Thread(target=lambda: ([q.put(l.rstrip()) for l in p.stdout], q.put(None)),
                     daemon=True).start()
    p.stdin.write(f"uci\nsetoption name OwnBook value false\n{posline}\nisready\n"
                  f"go depth {depth}{extra}\n")
    p.stdin.flush()
    end = time.monotonic() + 180
    while time.monotonic() < end:
        try:
            l = q.get(timeout=0.3)
            if l is None:
                break
            out.append(l)
            if l.startswith("bestmove"):
                break
        except queue.Empty:
            continue
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.stdin.close()
    except OSError:
        pass
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    infos = [x for x in out if x.startswith("info depth")]
    bms = [x for x in out if x.startswith("bestmove")]
    score = nodes = None
    if infos:
        s = re.search(r"score (cp|mate) (-?\d+)", infos[-1])
        score = f"{s.group(1)} {s.group(2)}" if s else None
        n = re.search(r" nodes (\d+)", infos[-1])
        nodes = int(n.group(1)) if n else None
    return score, nodes, (bms[-1].split()[1] if bms else None)


# --- the four cases -------------------------------------------------------------
FM_RESET = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/RP2N1PP/3R2K1 w - - 99 1"      # seat 25's board shape
REP_WIN = ("4k3/8/8/8/8/8/4P3/R3K3 w - - 0 40",
           "a1a2 e8d8 a2a1 d8e8 a1a2 e8d8 a2a1")   # black to move; d8e8 -> 3-fold, White (winning) to move
REP_LOSE = ("4k3/8/8/8/8/8/4P3/R3K3 w - - 0 40",
            "a1a2 e8d8 a2a1 d8e8 a1a2 e8d8 a2a1 d8e8")  # White to move; 3-fold, White is the LOSER? no:
            # White has R+P and is winning there; for a losing side to move at a 3-fold we use the
            # board below, where BLACK is to move and Black is the one who is lost.
KVK = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"
KRVSK_NORESET = "4k3/8/8/8/8/8/8/R3K2r w - - 100 1"     # no pawn moves, no captures anywhere


def main():
    pairs = [(sys.argv[i], sys.argv[i + 1]) for i in range(1, len(sys.argv), 2)]
    for exe, label in pairs:
        print(f"\n================ {label}  ({exe}) — Threads 1, go depth 12")

        # 1. fifty-move claimable WITH a reset available (seat 25's board)
        s, n, bm = ask(exe, f"position fen {FM_RESET}")
        print(f"1 fifty-move claimable, reset available : score {str(s):9} nodes {str(n):>7} bm {bm}")

        # 2. repetition where the WINNING side is to move at the repeated node
        base, moves = REP_WIN
        s, n, bm = ask(exe, f"position fen {base} moves {moves}")
        print(f"2 repetition, WINNING side to move      : score {str(s):9} nodes {str(n):>7} bm {bm}")

        # 3. repetition where the LOSING side is to move at the repeated node
        s, n, bm = ask(exe, "position fen 4k3/8/8/8/8/8/R3P3/4K3 b - - 9 44")  # black lost, 3-fold claim
        s2, n2, bm2 = ask(exe, f"position fen 4k3/8/8/8/8/8/4P3/R3K3 w - - 0 40 moves "
                                f"a1a2 e8d8 a2a1 d8e8 a1a2 e8d8 a2a1 d8e8 a1a2")
        print(f"3 repetition, LOSING side to move       : by-moves {str(s2):9} (plain-fen control {str(s):9})")

        # 4. genuine forced draw: K v K  (must stay cp 0)
        s, n, bm = ask(exe, f"position fen {KVK}")
        print(f"4 forced draw K v K                     : score {str(s):9} nodes {str(n):>7} bm {bm}")

        # extra control: fifty-move with NO reset possible (must stay cp 0)
        s, n, bm = ask(exe, f"position fen {KRVSK_NORESET}")
        print(f"  control: clock 100, NO reset possible : score {str(s):9} nodes {str(n):>7} bm {bm}")


if __name__ == "__main__":
    main()
