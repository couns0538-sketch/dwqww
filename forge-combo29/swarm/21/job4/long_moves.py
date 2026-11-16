#!/usr/bin/env python3
"""long_moves.py EXE OUTDIR [NPLIES]

Area 1 job 3.
  1. Build a random legal game with python-chess from SEED 2101 until it has NPLIES
     (default 1000) plies or the game ends; if the game ends early, back up to the last
     position that still had a legal move, as the brief requires.
  2. Send `position startpos moves <the whole list>` and compare perft 1 with python-chess.
  3. Send the same list with ONE illegal move inserted at ply 1, 10 and 500, and read the
     kept position back with `go perft 1`; compare with the legal prefix.

Every case is a fresh process; the raw stdout is kept per case. The illegal token is chosen
to be syntactically valid UCI but illegal in that position (a1a8 when the side to move has
no piece on a1, else e1e8), and recorded exactly.
"""
import json
import os
import random
import subprocess
import sys

import chess

SEED = 2101


def build_game(nplies):
    rng = random.Random(SEED)
    board = chess.Board()
    plies = []
    boards = [board.copy()]
    while len(plies) < nplies:
        moves = list(board.legal_moves)
        if not moves:
            break
        m = rng.choice(moves)
        board.push(m)
        plies.append(m.uci())
        boards.append(board.copy())
    if len(plies) < nplies:
        # the game ended early: the last position that still had a legal move
        while boards and not boards[-1].legal_moves:
            boards.pop()
        return plies, boards
    return plies, boards


def illegal_token(board):
    """A UCI-shaped move, with a REAL piece on the from-square, that is illegal here.
    Preference order: (1) a piece on the from-square, destination occupied by a friend or
    a geometrically impossible target; (2) any illegal UCI string."""
    legal = {m.uci() for m in board.legal_moves}
    for frm in chess.SQUARES:
        piece = board.piece_at(frm)
        if piece is None:
            continue
        for to in chess.SQUARES:
            tok = chess.square_name(frm) + chess.square_name(to)
            if tok in legal or frm == to:
                continue
            target = board.piece_at(to)
            if target is not None and target.color == piece.color:
                return tok  # capturing your own piece
    for frm in chess.SQUARES:
        if board.piece_at(frm) is None:
            continue
        for to in chess.SQUARES:
            tok = chess.square_name(frm) + chess.square_name(to)
            if tok not in legal and frm != to:
                return tok
    raise RuntimeError("no illegal token found")


def illegal_token_garbage(board):
    """A token that is not even UCI-shaped (5 chars, bad square names)."""
    return "z9z9"


def run(exe, outdir, name, lines, timeout=300):
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    p = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                       capture_output=True, timeout=timeout, env=env)
    with open(os.path.join(outdir, name + ".txt"), "w") as fh:
        fh.write("=== exe: %s\n" % os.path.abspath(exe))
        fh.write("=== lines sent (longest line truncated in this record only):\n")
        for s in lines:
            fh.write(">>> " + (s if len(s) < 400 else s[:400] + " ... <%d chars>" % len(s)) + "\n")
        fh.write("=== stdout:\n" + p.stdout + "\n=== stderr:\n" + p.stderr)
        fh.write("=== returncode: %d\n" % p.returncode)
    return p


def nodes(p):
    return [ln.split()[1] for ln in p.stdout.splitlines() if ln.startswith("nodes ")]


SAN = ("__asan_", "__ubsan_", "AddressSanitizer", "Sanitizer", "runtime error",
       "SUMMARY: UndefinedBehavior", "SEGV")


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    nplies = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
    os.makedirs(outdir, exist_ok=True)

    plies, boards = build_game(nplies)
    with open(os.path.join(outdir, "game_moves.txt"), "w") as fh:
        fh.write("SEED %d, %d plies\n" % (SEED, len(plies)))
        for i, m in enumerate(plies, 1):
            fh.write("%d %s\n" % (i, m))
    rows = []
    summary = {"nplies": len(plies)}

    # ---- 1. the whole legal list
    full = "position startpos moves " + " ".join(plies)
    p_full = run(exe, outdir, "full_list", [full, "isready", "go perft 1"])
    eng_full = nodes(p_full)
    py_full = boards[-1].legal_moves.count()
    summary["full"] = dict(engine=eng_full, python=py_full,
                           san=any(m in p_full.stdout or m in p_full.stderr for m in SAN),
                           refused_lines=[l for l in p_full.stdout.splitlines() if l.startswith("info string")])
    rows.append(("full 1,000-ply legal list", eng_full[0] if eng_full else "-", py_full))
    # ---- 2. one illegal move inserted at ply k (real piece on the from-square)
    for k in (1, 10, 500):
        if k > len(plies):
            continue
        prefix = plies[:k - 1]
        pos = boards[k - 1]
        tok = illegal_token(pos)
        seq = prefix + [tok] + plies[k - 1:]
        line = "position startpos moves " + " ".join(seq)
        p = run(exe, outdir, "illegal_at_%d" % k, [line, "isready", "go perft 1", "isready", "go perft 2"])
        got = nodes(p)
        expect_prefix = boards[k - 1].legal_moves.count()

        def perft2(bd):
            t = 0
            for m in bd.legal_moves:
                bd.push(m)
                t += bd.legal_moves.count()
                bd.pop()
            return t

        expect_prefix2 = perft2(boards[k - 1].copy())
        infos = [l for l in p.stdout.splitlines() if l.startswith("info string")]
        summary["illegal_%d" % k] = dict(token=tok, engine=got, prefix_count=expect_prefix,
                                         prefix_perft2=expect_prefix2, answer_lines=infos,
                                         san=any(m in p.stdout or m in p.stderr for m in SAN),
                                         readyok=p.stdout.count("readyok"))
        rows.append(("illegal move at ply %d (%s)" % (k, tok),
                     "%s / %s" % (got[0] if got else "-", got[1] if len(got) > 1 else "-"),
                     "prefix %d / %d" % (expect_prefix, expect_prefix2)))

    # ---- 3. a token that is not UCI at all, and an over-long move list
    pos1 = boards[0]
    garbage_seq = [illegal_token_garbage(pos1)] + plies
    p_g = run(exe, outdir, "garbage_at_1", ["position startpos moves " + " ".join(garbage_seq),
                                           "isready", "go perft 1"])
    summary["garbage_1"] = dict(engine=nodes(p_g),
                                answer_lines=[l for l in p_g.stdout.splitlines() if l.startswith("info string")],
                                san=any(m in p_g.stdout for m in SAN))
    rows.append(("non-UCI token at ply 1 (z9z9)", (nodes(p_g) or ["-"])[0], "prefix 20 / 400"))

    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    lines = ["| case | engine perft 1 | python-chess (prefix / full) |", "|---|---|---|"]
    for name, eng, py in rows:
        lines.append("| %s | %s | %s |" % (name, eng, py))
    san_any = any(v.get("san") for v in summary.values() if isinstance(v, dict))
    lines.append("")
    lines.append("sanitizer lines anywhere: %s" % san_any)
    text = "\n".join(lines)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
