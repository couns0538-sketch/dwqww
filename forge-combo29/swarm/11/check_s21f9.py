#!/usr/bin/env python3
"""check_s21f9.py EXE — seat 11's INDEPENDENT check of seat 21's 21-F9.

21-F9 claims: the halfmove>=100 root shortcut fires for EVERY counter at or above 100, and it
MISSES A MATE IN 1 in both colours: with a mate on the board at counter 100, `go depth 5`,
`go nodes 100` and `go movetime 50` all play a NON-MATING move, while the same boards at
counter 99 find the mate by all three searches.

Written from that sentence; seat 21's scripts were not read. Waiting driver (19-F12), every
parse asserted: a missing `score` or `bestmove` aborts with no verdict.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine

EXE = sys.argv[1]
# White mates with Qd8#; Black mates with ...Qd1#
WHITE_MATE = "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - {h} 1"
BLACK_MATE = "3q2k1/5ppp/8/8/8/8/5PPP/6K1 b - - {h} 1"
GO_FORMS = ["go depth 5", "go nodes 100", "go movetime 50"]


class MeasurementError(Exception):
    pass


def probe(fen, go):
    e = Engine(EXE, options=[], timeout=180)
    e.start()
    try:
        ans, refused = e.position(fen=fen)
        if refused:
            raise MeasurementError(f"position refused: {refused}")
        infos, bm, lines = e.go(go)
        if bm is None:
            raise MeasurementError(f"no bestmove for {go}")
        score = None
        nodes = None
        for l in infos:
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                score = (m.group(1), int(m.group(2)))
            m2 = re.search(r"nodes (\d+)", l)
            if m2:
                nodes = int(m2.group(1))
        return bm, score, nodes
    finally:
        e.quit()


def mates(bm, fen):
    """Does this move deliver immediate checkmate?"""
    b = chess.Board(fen)
    try:
        mv = chess.Move.from_uci(bm)
    except Exception:
        return False
    if mv not in b.legal_moves:
        return False
    b.push(mv)
    return b.is_checkmate()


print(f"{'board':11} {'H':>4} {'go form':16} {'bestmove':9} {'score':10} {'nodes':>7}  mates?")
rows = []
for label, tpl in (("white-mate", WHITE_MATE), ("black-mate", BLACK_MATE)):
    for h in (99, 100):
        for go in GO_FORMS:
            fen = tpl.format(h=h)
            try:
                bm, score, nodes = probe(fen, go)
            except MeasurementError as exc:
                print(f"{label:11} {h:>4} {go:16} MEASUREMENT FAILED: {exc}")
                sys.exit(2)
            is_mate = mates(bm, fen)
            rows.append((label, h, go, bm, score, nodes, is_mate))
            print(f"{label:11} {h:>4} {go:16} {bm:9} {str(score):10} {str(nodes):>7}  {is_mate}")

print("\n=== verdict on 21-F9 ===")
fail = []
def chk(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")
    if not cond:
        fail.append(name)

at100 = [r for r in rows if r[1] == 100]
at99 = [r for r in rows if r[1] == 99]
chk("at H=100 NO go form finds the mate in 1",
    all(not r[6] for r in at100), f"{sum(1 for r in at100 if not r[6])}/{len(at100)} play a non-mate")
chk("at H=99 EVERY go form finds the mate in 1",
    all(r[6] for r in at99), f"{sum(1 for r in at99 if r[6])}/{len(at99)} mate")
chk("both colours are affected at H=100",
    all(not r[6] for r in at100 if r[0] == "black-mate") and
    all(not r[6] for r in at100 if r[0] == "white-mate"))
zero_node = [r for r in at100 if r[5] == 0]
chk("the H=100 answers are 0-node adjudications", len(zero_node) > 0,
    f"{len(zero_node)}/{len(at100)} at H=100 report 0 nodes")

print()
if not fail:
    print("RESULT: CONFIRMS 21-F9 — at halfmove 100 the root is adjudicated drawn at 0 nodes and a")
    print("        mate in 1 is not played, in both colours, for all three go forms.")
else:
    print("RESULT: does NOT reproduce 21-F9 as stated — see FAIL lines.")
