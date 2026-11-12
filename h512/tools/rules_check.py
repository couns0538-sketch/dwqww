#!/usr/bin/env python
"""rules_check.py - JOB E (2026-11-11): legal-move, terminal-position and draw-rule handling of a candidate exe
against the lock exe. Own code.

  rules_check.py --lock LOCK.exe --cand CAND.exe [--cand-opt "setoption ..."]... --out result.json

The candidate's evaluation differs from the lock's, so only things that must NOT depend on the evaluation are
compared:
  perft      node counts of `go perft` on the start position and Kiwipete against the known values and the lock
  terminal   checkmate and stalemate at the root: identical output (best move and score)
  mate       forced mates: identical mate score and the same mating move
  draw       insufficient material and a 50-move-rule position where every move reaches the limit: score cp 0
  legal      the best move of every search is legal (python-chess)
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys

import chess

START = chess.STARTING_FEN
KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
PERFT = [("startpos", START, 5, 4865609), ("kiwipete", KIWI, 4, 4085603),
         ("ep+promo", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 5, 674624),
         ("promotions", "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1", 4, 182838)]
CASES = [
    ("mate_in_1", "6k1/5ppp/8/8/8/8/8/R3K3 w - - 0 1", "mate", 6),
    ("mate_in_2", "r1bq2r1/b4pk1/p1pp1p2/1p2pP2/1P2P1PB/3P4/1PPQ2P1/R3K2R w - - 0 1", "mate", 8),
    ("checkmated", "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3", "terminal", 4),
    ("stalemated", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", "terminal", 4),
    ("K_v_K", "8/8/4k3/8/8/3K4/8/8 w - - 0 1", "draw", 8),
    ("KN_v_K", "8/8/4k3/8/8/3KN3/8/8 w - - 0 1", "draw", 8),
    ("KB_v_K", "8/8/4k3/8/8/3KB3/8/8 b - - 0 1", "draw", 8),
    ("fifty_move_clock_99", "8/8/4k3/8/8/3K1R2/8/8 w - - 99 80", "draw", 8),
    ("fifty_move_clock_100", "8/8/4k3/8/8/3KR3/8/8 b - - 100 80", "draw", 6),
]


def session(exe, opts, commands, wait_for=None):
    """One engine process. With wait_for (a line prefix) the output is read until that line before `quit` is sent,
    so a search is never cut short by the quit command."""
    text = "uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\n"
    text += "".join(o + "\n" for o in opts) + "isready\n" + commands
    if wait_for is None:
        p = subprocess.run([exe], input=text + "quit\n", capture_output=True, text=True, timeout=900)
        return p.returncode, p.stdout
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    p.stdin.write(text)
    p.stdin.flush()
    lines = []
    for line in p.stdout:
        lines.append(line)
        if line.startswith(wait_for):
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    lines += p.stdout.readlines()
    return p.wait(timeout=60), "".join(lines)


def run(exe, opts):
    out = {}
    for name, fen, depth, expect in PERFT:
        rc, text = session(exe, opts, f"position fen {fen}\ngo perft {depth}\n")
        nums = [int(x) for x in re.findall(r"(?im)^(?:info string )?(?:perft|nodes searched|total)[^\d\n]*(\d+)\s*$", text)]
        if not nums:
            nums = [int(x) for x in re.findall(r"(\d{5,})", text.split("readyok")[-1])]
        out["perft_" + name] = {"depth": depth, "nodes": nums[-1] if nums else None, "expected": expect, "exit": rc}
    for name, fen, kind, depth in CASES:
        rc, text = session(exe, opts, f"ucinewgame\nposition fen {fen}\ngo depth {depth}\n", wait_for="bestmove")
        body = text.split("readyok")[-1]
        scores = re.findall(r"score (cp|mate) (-?\d+)", body)
        best = re.findall(r"bestmove (\S+)", body)
        out[name] = {"kind": kind, "fen": fen, "score": list(scores[-1]) if scores else None, "bestmove": best[-1] if best else None, "exit": rc}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock", required=True)
    ap.add_argument("--cand", required=True)
    ap.add_argument("--cand-opt", action="append", default=[])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    lock = run(a.lock, [])
    cand = run(a.cand, a.cand_opt)
    res = {"lock": {"exe": a.lock, "md5": hashlib.md5(open(a.lock, "rb").read()).hexdigest(), "results": lock},
           "cand": {"exe": a.cand, "md5": hashlib.md5(open(a.cand, "rb").read()).hexdigest(), "options": a.cand_opt, "results": cand},
           "checks": {}}
    ok = True
    for name, fen, depth, expect in PERFT:
        k = "perft_" + name
        good = cand[k]["nodes"] == expect and lock[k]["nodes"] == expect
        res["checks"][k] = good
        ok &= good
    for name, fen, kind, depth in CASES:
        c, l = cand[name], lock[name]
        board = chess.Board(fen)
        legal = [m.uci() for m in board.legal_moves]
        if kind == "terminal":
            good = (c["score"] == l["score"]) and (c["bestmove"] == l["bestmove"]) and not legal
        elif kind == "mate":
            good = c["score"] is not None and c["score"] == l["score"] and c["score"][0] == "mate" and c["bestmove"] in legal
            if good and c["score"] == ["mate", "1"]:
                board.push_uci(c["bestmove"])
                good = board.is_checkmate()
        else:
            good = c["score"] == ["cp", "0"] and l["score"] == ["cp", "0"] and (c["bestmove"] in legal or not legal)
        res["checks"][name] = bool(good)
        ok &= bool(good)
    res["PASS"] = bool(ok)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    for k, v in res["checks"].items():
        c = cand.get(k, {})
        print(f"{'ok  ' if v else 'FAIL'} {k}: cand {c.get('nodes', '')}{c.get('score', '')} {c.get('bestmove', '')} | lock "
              f"{lock[k].get('nodes', '')}{lock[k].get('score', '')} {lock[k].get('bestmove', '')}")
    print("RULES PASS" if ok else "RULES FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
