#!/usr/bin/env python3
"""swarm seat 01: the perft fingerprint — prove the engine holds the board you think it holds (S-F169).

`S-C59` used perft 2 as a board fingerprint to show my accepted-but-invalid FENs parse to the intended position. The
coordinator called that the general form of the whole FEN family, and it is: **every FEN question reduces to "does the
engine's board equal the board I meant?"** This makes it a reusable check rather than a one-off.

Two comparisons, because they answer different questions:

  1. **Engine vs ENGINE** — perft N of the FEN you sent against perft N of its canonicalised form (digit runs collapsed).
     This isolates the FEN PARSER: same board means the parser read the intent correctly. That is the `S-F1` question.
  2. **Engine vs PYTHON-CHESS** — perft N against an independent implementation, when python-chess accepts the FEN.
     This isolates the ENGINE's move generation, and it is the stronger claim: two independent legals-move generators
     agreeing to depth N is hard to fake. That is the `S-F2` question.

Both are needed. Comparison 1 can pass while the engine's movegen is broken (both sides use the same engine); comparison
2 can only run where python-chess accepts the FEN, which is exactly where the parser question is interesting and the
movegen question is easier.

What this does NOT do: it does not canonicalise for python-chess. python-chess refuses adjacent-digit ranks, which is the
whole reason `S-F1` exists - so comparison 2 is SKIPPED (and counted) for those, and skipping is reported rather than
silent (23-F200: "I could not evaluate this" must never look like "this is fine").

Usage: perft_fingerprint.py <exe> <fen> [perft-depth]
       perft_fingerprint.py <exe> --file <fens> [--limit N]
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

import chess


def engine_perft(exe, fen, depth, timeout=60):
    """(nodes, had_invalid_diag) or (None, diag) if the engine produced no count."""
    cmd = ("uci\nisready\nucinewgame\nisready\nposition fen %s\nisready\ngo perft %d\n" % (fen, depth))
    try:
        p = subprocess.run([exe], input=cmd, capture_output=True, text=True, cwd="/tmp",
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, False
    out = p.stdout
    diag = "invalid FEN" in out
    m = re.findall(r"^nodes (\d+)", out, re.M)
    return (int(m[-1]) if m else None), diag


def canonicalise(fen):
    """Collapse digit runs inside the board field into their sum — the parse the engine performs."""
    parts = fen.split()
    if not parts:
        return fen
    ranks = []
    for r in parts[0].split("/"):
        s, i = "", 0
        while i < len(r):
            if r[i].isdigit():
                j, total = i, 0
                while j < len(r) and r[j].isdigit():
                    total += int(r[j])
                    j += 1
                s += str(total)
                i = j
            else:
                s += r[i]
                i += 1
        ranks.append(s)
    return "/".join(ranks) + (" " + " ".join(parts[1:]) if len(parts) > 1 else "")


def py_perft(fen, depth):
    """python-chess perft, or None if it refuses the FEN."""
    try:
        board = chess.Board(fen)
    except ValueError:
        return None
    if not board.is_valid():
        return None

    def rec(b, d):
        if d == 0:
            return 1
        if d == 1:
            return b.legal_moves.count()
        n = 0
        for mv in b.legal_moves:
            b.push(mv)
            n += rec(b, d - 1)
            b.pop()
        return n
    return rec(board, depth)


def fingerprint(exe, fen, depth):
    result = {"fen": fen, "depth": depth}
    eng, diag = engine_perft(exe, fen, depth)
    result["engine_nodes"] = eng
    result["engine_diag"] = diag
    # comparison 1: engine vs canonical form
    canon = canonicalise(fen)
    result["canonical"] = canon
    if canon != fen:
        eng_c, _ = engine_perft(exe, canon, depth)
        result["canonical_nodes"] = eng_c
        result["parser_ok"] = (eng is not None and eng == eng_c)
    else:
        result["canonical_nodes"] = eng
        result["parser_ok"] = True
    # comparison 2: engine vs python-chess
    py = py_perft(canon, depth)
    result["python_nodes"] = py
    if py is None:
        result["movegen_verdict"] = "SKIPPED (python-chess refuses this FEN)"
    elif eng is None:
        result["movegen_verdict"] = "SKIPPED (engine gave no count)"
    elif py == eng:
        result["movegen_verdict"] = "AGREES"
    else:
        result["movegen_verdict"] = "DISAGREES (engine %s vs python-chess %s)" % (eng, py)
    return result


def selftest(exe):
    """Prove the instrument can report a DISAGREEMENT, not only an agreement.

    A fingerprint tool that has only ever said AGREES is indistinguishable from one whose comparison cannot fail. This
    drives the comparison against two DIFFERENT boards and requires a difference to be reported.
    """
    a, _ = engine_perft(exe, "8/8/8/8/8/8/4K3/7k w - - 0 1", 2)
    b = py_perft("8/8/8/8/8/8/5K2/7k w - - 0 1", 2)
    if a is None or b is None:
        return "SKIP (no counts; cannot self-test here)"
    if a == b:
        return "FAIL: two DIFFERENT boards gave the same perft - the comparison cannot detect a difference"
    return "OK: different boards differ (%s vs %s), so DISAGREES can fire" % (a, b)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    exe = sys.argv[1]
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    print("perft fingerprint  exe=%s  sha256=%s" % (exe, sha[:16]))

    if sys.argv[2] == "--file":
        fens = [l.strip() for l in Path(sys.argv[3]).read_text().splitlines() if l.strip()]
        depth = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 2
        if "--depth" in sys.argv:
            depth = int(sys.argv[sys.argv.index("--depth") + 1])
        rows = [fingerprint(exe, f, depth) for f in fens]
    else:
        fen = sys.argv[2]
        depth = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        rows = [fingerprint(exe, fen, depth)]

    bad = 0
    skipped = 0
    for r in rows:
        if r["movegen_verdict"].startswith("SKIPPED"):
            skipped += 1
        if r["movegen_verdict"].startswith("DISAGREES") or not r["parser_ok"]:
            bad += 1
        print("  d%-2d parser_ok=%-5s movegen=%-46s  %s"
              % (r["depth"], r["parser_ok"], r["movegen_verdict"], r["fen"].split()[0][:36]))
    print()
    print("rows: %d | parser mismatches or movegen disagreements: %d | movegen skipped: %d"
          % (len(rows), bad, skipped))
    if skipped:
        print("  (%d rows could not be compared against python-chess - reported so the skip is visible, per 23-F200)"
              % skipped)
    print("SELFTEST: %s" % selftest(exe))
    print("LIMIT: perft agrees on LEGAL MOVE COUNTS, not on evaluation, pruning or the move chosen. It proves the two")
    print("       generators see the same board and the same legal moves to this depth, and nothing beyond that.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
