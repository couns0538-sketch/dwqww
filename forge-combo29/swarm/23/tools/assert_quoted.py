#!/usr/bin/env python3
"""assert_quoted.py : the self-catching check for the error I made in 23-C20.

The error: I wrote a finding that named a board and a move pair, and the FEN I quoted belonged to a DIFFERENT
board from the one whose behaviour I was describing. The prose and the evidence had drifted apart, and nothing in
my workflow compared them.

This module makes that class self-catching: hand it the exact claim you are about to publish — (fen, form, expected
move) — and it RE-RUNS each one from scratch and refuses to pass if any result disagrees with the stated one.

usage:
    from assert_quoted import assert_claims
    assert_claims(engine, opts, [
        {"fen": "...", "form": "fen",   "expect_move": "b4f8"},
        {"fen": "...", "form": "moves", "moves": "e2e4 ...", "expect_move": "f1b5"},
    ])

The point is not that it is clever; it is that the quoted FEN and the quoted move are checked against each other by
the same binary that produced them, at publish time.
"""
import re
import subprocess

INFO = re.compile(r"^info depth (\d+).*?nodes (\d+)")


def _run(engine, opts, position_cmd, budget_cmd="go softnodes 2000"):
    p = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    names = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("engine died in uci")
        s = l.strip()
        if s.startswith("option name "):
            names.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    for line in opts:
        nm = line.split("name ")[1].split(" value ")[0]
        if nm not in names:
            raise RuntimeError("STOP: option %r not in the engine's uci list" % nm)
        p.stdin.write(line + "\n"); p.stdin.flush()
        p.stdin.write("isready\n"); p.stdin.flush()
        while p.stdout.readline().strip() != "readyok":
            pass
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write(position_cmd + "\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write(budget_cmd + "\n"); p.stdin.flush()
    nodes = 0
    bm = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("engine died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            nodes = int(m.group(2))
        if s.startswith("bestmove"):
            bm = s.split()[1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return bm, nodes


def assert_claims(engine, opts, claims, verbose=True):
    """Re-run every quoted claim. Returns True only if EVERY one matches what the text says."""
    ok = True
    for i, c in enumerate(claims, 1):
        if c["form"] == "fen":
            cmd = "position fen " + c["fen"]
        else:
            cmd = "position startpos moves " + c["moves"]
        move, nodes = _run(engine, opts, cmd)
        good = move == c["expect_move"]
        if not good:
            ok = False
        if verbose:
            print("  %s claim %d: %s -> %s @ %d nodes (text says %s)"
                  % ("PASS" if good else "FAIL", i, c.get("label", c["form"]),
                     move, nodes, c["expect_move"]))
    return ok


if __name__ == "__main__":
    # Self-demonstration on the exact pair from 23-C20, including a DELIBERATELY WRONG claim,
    # so the checker is shown able to fail as well as pass.
    import sys
    engine = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/pcbuild/forge"
    optfile = sys.argv[2] if len(sys.argv) > 2 else "/agent/repos/dwqww/forge-combo29/swarm/23/job7/pc20_opts.txt"
    opts = [l.strip() for l in open(optfile) if l.strip() and not l.startswith("#")]
    opts.append("setoption name OwnBook value false")
    RUY_FEN = "r1bqkbnr/1ppp1ppp/p1n5/4p3/1B2P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4"
    RUY_MOVES = "e2e4 e7e5 g1f3 b8c6 f1b4 a7a6"
    real = [
        {"label": "Ruy FEN form", "form": "fen", "fen": RUY_FEN, "expect_move": "b4f8"},
        {"label": "Ruy moves form", "form": "moves", "moves": RUY_MOVES, "expect_move": "f1b5"},
    ]
    print("== the two claims as published in 23-C20 (both should PASS)")
    print("all passed:", assert_claims(engine, opts, real))
    print()
    print("== the SAME claims with one move deliberately wrong (must FAIL, proving the checker fires)")
    broken = [dict(real[0], expect_move="f1b5"), dict(real[1], expect_move="b4f8")]
    print("all passed:", assert_claims(engine, opts, broken), "(must be False)")
