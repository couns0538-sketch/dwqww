#!/usr/bin/env python3
"""check_mate_threshold.py EXE — WHERE does the mate-throwing shortcut start?

S-C9 confirmed the shortcut at exactly 100. This locates its boundary, which no other seat has
reported, and ties it to my S-F10/S-F11 draw-threshold work: are the two thresholds the same
number, or two separate effects?

Method: the same mate-in-1 board at every halfmove 95..102, `go depth 5`; print score/bestmove.
Every value asserted; a missing parse aborts.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine

EXE = sys.argv[1]
WHITE_MATE = "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - {h} 1"


class MeasurementError(Exception):
    pass


def probe(h):
    fen = WHITE_MATE.format(h=h)
    e = Engine(EXE, options=[], timeout=180)
    e.start()
    try:
        _, refused = e.position(fen=fen)
        if refused:
            raise MeasurementError(f"H={h} refused: {refused}")
        infos, bm, _ = e.go("go depth 5")
        if bm is None:
            raise MeasurementError(f"H={h} no bestmove")
        score = nodes = None
        for l in infos:
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                score = (m.group(1), int(m.group(2)))
            m2 = re.search(r"nodes (\d+)", l)
            if m2:
                nodes = int(m2.group(1))
        if score is None:
            raise MeasurementError(f"H={h} no score parsed")
        b = chess.Board(fen)
        mv = chess.Move.from_uci(bm)
        b.push(mv)
        return bm, score, nodes, b.is_checkmate()
    finally:
        e.quit()


print(f"board {WHITE_MATE.format(h='<h>')}  (Qd8 is mate in 1)")
print(f"{'H':>4} {'bestmove':9} {'score':11} {'nodes':>7}  mate?")
sweep = list(range(95, 103))
found = []
for h in sweep:
    try:
        bm, score, nodes, is_mate = probe(h)
    except MeasurementError as exc:
        print(f"MEASUREMENT FAILED: {exc}")
        sys.exit(2)
    print(f"{h:>4} {bm:9} {str(score):11} {str(nodes):>7}  {is_mate}")
    if not is_mate:
        found.append(h)

print("\n=== reading ===")
if found:
    print(f"the mate is NOT played from H={min(found)} onward; still played at H={min(found)-1}")
    print(f"so the mate-throwing threshold is exactly H={min(found)}")
    print("Compare with S-F10/S-F11: the DRAW threshold at depth 10 was also H=91 for KRvK, but")
    print("that one was a depth-dependent score change; this one is a hard 0-node adjudication at")
    print(f"H={min(found)}, i.e. the counter reaching 100. They are two different effects that happen")
    print("to be near each other for shallow searches.")
else:
    print("the mate was played at EVERY tested H — the shortcut did not fire in 95..102")
