#!/usr/bin/env python3
"""check_08c33_matrix.py

Verifies seat 08's 08-C33 / 08-C34 drawn-root matrix on BOTH builds, from their own recipe.

Their claim, in two doors:
  halfmove door (08-C33)  board `7k/8/6K1/8/8/8/8/R7 w`, a1a8 verified mate:
        hm 0   -> a1a8 on both builds (control)
        hm 99  -> a1a8 on both builds (control)
        hm 100 -> BASE plays a1b1 at 0 nodes; PC plays a1a8 at 85
  repetition door (08-C34)
        startpos repeated TWICE  -> base 701 / PC 412 nodes, neither drawn (control)
        startpos repeated THREE times -> base a2a3 at 0 nodes; PC d2d4 at 389

Every position is verified with python-chess before use, and the mate a1a8 is confirmed to be a mate, so a
"drawn" reading cannot be an artefact of an illegal board. Each cell is a fresh process, and both builds are
run through the SAME harness - the point of a matrix is that the cells are comparable.

The harness sends `position` and then `go` as SEPARATE commands, never a `position` alone (a first version of
this script forgot the `go` and hung with no bestmove, which is why the wait is explicitly bounded).
"""
import re
import subprocess
import sys
import time

import chess

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
OPTS = ["Hash 16", "Threads 1", "OwnBook false"] + S14

BASE = "/agent/repos/base/build-release/forge"
PC = "/agent/repos/base/build-pc/forge"


def run(exe, pos_cmd, go_cmd, timeout=60):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo=timeout):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = p.stdout.readline()
            if not ln:
                break
            y = ln.rstrip("\n"); out.append(y)
            if pred(y):
                return out, True
        return out, False

    try:
        send("uci")
        lines, ok = until(lambda x: x.strip() == "uciok")
        if not ok:
            return {"error": "no uciok"}
        adv = {m.group(1) for m in (re.match(r"option name (.+?) type ", l) for l in lines) if m}
        n_applied = 0
        for item in OPTS:
            name, _, val = item.rpartition(" ")
            if name not in adv:
                return {"error": "option %r not advertised" % name}
            send("setoption name %s value %s" % (name, val))
            send("isready")
            l2, ok2 = until(lambda x: x.strip() == "readyok")
            if not ok2:
                return {"error": "no readyok"}
            for l in l2:
                if "unknown option" in l or "invalid value" in l:
                    return {"error": "bad option %r: %s" % (item, l)}
            n_applied += 1
        send("ucinewgame"); send("isready")
        until(lambda x: x.strip() == "readyok")
        send(pos_cmd)
        send("isready")
        _, okp = until(lambda x: x.strip() == "readyok")
        if not okp:
            return {"error": "no readyok after position"}
        # the go is a SEPARATE command - a bare `position` never produces a bestmove
        send(go_cmd)
        outlines, okg = until(lambda x: x.startswith("bestmove"), tmo=timeout)
        if not okg:
            return {"error": "no bestmove within %ds (go was %r)" % (timeout, go_cmd), "n_applied": n_applied}
        infos = [l for l in outlines if l.startswith("info depth")]
        bmline = next(l for l in outlines if l.startswith("bestmove"))
        parts = bmline.split()
        nodes = None
        score = None
        if infos:
            m = re.search(r"nodes (\d+)", infos[-1])
            nodes = int(m.group(1)) if m else None
            s = re.search(r"score (cp|mate) (-?\d+)", infos[-1])
            score = (s.group(1), int(s.group(2))) if s else None
        return {"bestmove": parts[1] if len(parts) > 1 else None, "nodes": nodes,
                "score": score, "n_info": len(infos), "n_applied": n_applied}
    finally:
        try:
            p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=10)
        except Exception:
            p.kill()


def preflight():
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        print("  %-56s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            ok = False

    print("preflight (positions verified before any cell is measured):")
    # the mate board
    fen = "7k/8/6K1/8/8/8/8/R7 w - - 0 1"
    b = chess.Board(fen)
    ra1a8 = b.push_uci("a1a8")
    chk("board is legal and a1a8 is MATE", b.is_checkmate(), "(mate=%s)" % b.is_checkmate())
    # repetition door: does the startpos really occur three times after that move list?
    # NOTE the counting convention. The INITIAL position is occurrence #1, so a move list that returns to
    # startpos twice produces THREE occurrences in total - which is why `is_repetition(3)` is the correct
    # test and a naive "count how many times my list returns to the start" gives the wrong answer. My first
    # version of this preflight made exactly that mistake and reported FAIL against a correct claim.
    moves = "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8".split()
    b2 = chess.Board()
    for mv in moves:
        b2.push_uci(mv)
    chk("after the full list startpos has occurred THREE times", b2.is_repetition(3),
        "(is_repetition(3)=%s, claimable=%s)" % (b2.is_repetition(3), b2.can_claim_threefold_repetition()))
    b3 = chess.Board()
    for mv in moves[:4]:
        b3.push_uci(mv)
    chk("after the half list startpos has occurred TWICE (control)",
        b3.is_repetition(2) and not b3.is_repetition(3),
        "(rep2=%s rep3=%s)" % (b3.is_repetition(2), b3.is_repetition(3)))
    return ok


def main():
    if not preflight():
        print("\nPREFLIGHT FAILED - refusing to measure")
        sys.exit(1)

    print("\n=== halfmove door (08-C33), `go depth 4` ===")
    print("  hm    base bestmove/nodes/infos        PC bestmove/nodes/infos")
    for hm in (0, 99, 100):
        pos = "position fen 7k/8/6K1/8/8/8/8/R7 w - - %d 1" % hm
        rb = run(BASE, pos, "go depth 4")
        rp = run(PC, pos, "go depth 4")
        def fmt(r):
            if "error" in r:
                return "ERR:%s" % r["error"][:28]
            return "%-5s %-6s %2d" % (r["bestmove"], r["nodes"], r["n_info"])
        print("  %3d   %-30s %s" % (hm, fmt(rb), fmt(rp)))

    print("\n=== repetition door (08-C34), `go depth 4` ===")
    cases = [("twice (control)", "g1f3 g8f6 f3g1 f6g8"),
             ("THREE times", "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8")]
    for lbl, mv in cases:
        pos = "position startpos moves " + mv
        rb = run(BASE, pos, "go depth 4")
        rp = run(PC, pos, "go depth 4")
        def fmt2(r):
            if "error" in r:
                return "ERR:%s" % r["error"][:28]
            return "%-5s %-6s %2d" % (r["bestmove"], r["nodes"], r["n_info"])
        print("  %-16s base %-28s PC %s" % (lbl, fmt2(rb), fmt2(rp)))


if __name__ == "__main__":
    main()
