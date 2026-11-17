#!/usr/bin/env python3
"""ceiling_bench.py CLAIMSJSON OUTJSONL CAPSEC -- how far does exhaustive mate verification actually reach?

For each (fen, claimed mate) pair, walk n=1..|N| with the exhaustive A/D solver and record per-budget: completed or
timed out, the verdict, wall-clock, memo size. A timeout is recorded as TIMEOUT - never as "not forced" - because the
distinction is exactly what makes board 106 a candidate rather than a refutation.

Claims are processed smallest |N| first so the cheap ones bank even if the run is cut short.

Solver here is a copy of claimcheck.py's A/D with a node counter and a hard time check, so a single budget cannot
overrun the cap by much.
"""
import json
import sys
import time

import chess

sys.setrecursionlimit(100000)

CAP = 600


class Timeout(Exception):
    pass


class Budget:
    def __init__(self, seconds):
        self.deadline = time.time() + seconds
        self.nodes = 0

    def tick(self):
        self.nodes += 1
        if (self.nodes & 1023) == 0 and time.time() > self.deadline:
            raise Timeout()


def A(board, n, memo, bud):
    bud.tick()
    if n <= 0:
        return False
    key = (board.board_fen(), board.turn, board.castling_rights, board.ep_square, n)
    if key in memo:
        return memo[key]
    res = False
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop(); res = True; break
        if board.is_game_over(claim_draw=False):
            board.pop(); continue
        hit = D(board, n - 1, memo, bud)
        board.pop()
        if hit:
            res = True; break
    memo[key] = res
    return res


def D(board, m, memo, bud):
    bud.tick()
    if board.is_checkmate():
        return True
    if board.is_game_over(claim_draw=False):
        return False
    key = (board.board_fen(), board.turn, board.castling_rights, board.ep_square, -m)
    if key in memo:
        return memo[key]
    res = True
    for mv in board.legal_moves:
        board.push(mv)
        ok = A(board, m, memo, bud)
        board.pop()
        if not ok:
            res = False
            break
    memo[key] = res
    return res


def bench(fen, claimed, cap):
    b = chess.Board(fen)
    attacker_is_stm = claimed > 0
    steps = []
    truth = None
    for n in range(1, abs(claimed) + 1):
        bud = Budget(cap)
        memo = {}
        t0 = time.time()
        try:
            hit = A(b, n, memo, bud) if attacker_is_stm else D(b, n, memo, bud)
        except Timeout:
            steps.append({"n": n, "status": "TIMEOUT", "secs": round(time.time() - t0, 1),
                          "memo": len(memo), "nodes": bud.nodes})
            return {"adjudicated": False, "truth": None, "steps": steps}
        steps.append({"n": n, "status": "forced" if hit else "not_forced",
                      "secs": round(time.time() - t0, 1), "memo": len(memo), "nodes": bud.nodes})
        if hit:
            truth = n
            break
    if truth is None:
        return {"adjudicated": False, "truth": None, "steps": steps}
    verdict = "CORRECT" if truth == abs(claimed) else ("TOO_SHORT" if truth > abs(claimed) else "TOO_LONG")
    return {"adjudicated": True, "truth": truth, "verdict": verdict, "steps": steps}


def main():
    inp, outp, cap = sys.argv[1], sys.argv[2], float(sys.argv[3])
    claims = json.load(open(inp))
    claims.sort(key=lambda c: (abs(c["value"]), c["fen"]))
    print(f"{len(claims)} claims, cap {cap}s per budget", flush=True)
    with open(outp, "w") as out:
        for i, c in enumerate(claims):
            r = bench(c["fen"], c["value"], cap)
            rec = {"fen": c["fen"], "value": c["value"], "src": c.get("src"), **r}
            out.write(json.dumps(rec) + "\n")
            out.flush()
            tag = r["verdict"] if r["adjudicated"] else "UNADJUDICATED"
            print(f"  [{i+1}/{len(claims)}] |N|={abs(c['value']):2d} {tag}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
