#!/usr/bin/env python3
"""check_21F1.py EXE OUTDIR : independent check of seat 21's finding 21-F1.

WHAT 21-F1 CLAIMS
  The brief's area-1 known line "an impossible-castling FEN is ACCEPTED (perft 3 8,902 against
  python-chess 8,802 on the same board)" is a misdiagnosis: this build REFUSES that FEN, and 8,902 is
  simply startpos perft 3, i.e. the position left on the board because the refused command changed nothing.

HOW I TEST IT (my own harness, written from the finding's text, not from seat 21's script)
  Five independent sub-claims, each with its own fresh engine process:
    A. The FEN the brief's number must come from -- startpos with h1 emptied but KQ castling rights kept --
       is REFUSED, and an `invalid FEN` line is printed.
    B. startpos perft 3 is exactly 8902, on this build, sent as a clean command.
    C. python-chess perft 3 of that same impossible-castling board is exactly 8802 (the brief's other number),
       which is what makes "8,902 vs 8,802 on the same board" impossible as a like-for-like comparison.
    D. After the refused FEN, `go perft 3` returns 8902 -- i.e. the refused command left startpos on the board.
    E. After startpos and then the refused FEN, `go perft 3` again returns 8902.
  Also: the same experiment with a FEN that is refused for a DIFFERENT reason (only 3 fields), to see whether
  the stickiness is general rather than special to castling rights.

VERDICT RULE (fixed before running)
  CONFIRMS if A refused, B == 8902, C == 8802, D == 8902, E == 8902.
  REFUTES if any of those fails, and the output shows which.
"""
import os
import subprocess
import sys

import chess

CASTLE_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1"
THREE_FIELD = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq"
OTHER = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"


def perft_py(fen, depth):
    board = chess.Board(fen)

    def rec(bd, d):
        if d == 0:
            return 1
        total = 0
        for mv in bd.legal_moves:
            bd.push(mv)
            total += rec(bd, d - 1)
            bd.pop()
        return total

    return rec(board, depth)


def run(exe, outdir, name, lines):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    proc = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                          capture_output=True, timeout=600, env=env)
    with open(os.path.join(outdir, name + ".txt"), "w") as fh:
        fh.write("exe: " + os.path.abspath(exe) + "\n")
        fh.write("lines sent:\n" + "\n".join(">>> " + s for s in lines) + "\n")
        fh.write("stdout:\n" + proc.stdout + "\nstderr:\n" + proc.stderr)
        fh.write("returncode: %d\n" % proc.returncode)
    return proc.stdout


def nodes(stdout):
    vals = [int(l.split()[1]) for l in stdout.splitlines() if l.startswith("nodes ")]
    return vals[-1] if vals else None


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)

    a_out = run(exe, outdir, "A_castle_fen_only", ["position fen " + CASTLE_FEN, "isready", "go perft 3"])
    a_refused = ("invalid FEN" in a_out)
    a_nodes = nodes(a_out)

    b_out = run(exe, outdir, "B_startpos_perft3", ["position startpos", "isready", "go perft 3"])
    b_nodes = nodes(b_out)

    c_nodes = perft_py(CASTLE_FEN, 3)
    with open(os.path.join(outdir, "C_python_chess.txt"), "w") as fh:
        fh.write("position: " + CASTLE_FEN + "\npython-chess perft 3: %d\n" % c_nodes)
        fh.write("python-chess startpos perft 3: %d\n" % perft_py(chess.STARTING_FEN, 3))
        fh.write("python-chess board.is_valid(): %s\n" % chess.Board(CASTLE_FEN).is_valid())

    d_out = run(exe, outdir, "D_fen_then_perft", ["position fen " + CASTLE_FEN, "isready", "go perft 3"])
    d_refused = ("invalid FEN" in d_out)
    d_nodes = nodes(d_out)

    e_out = run(exe, outdir, "E_startpos_fen_perft",
                ["position startpos", "isready", "position fen " + CASTLE_FEN, "isready", "go perft 3"])
    e_nodes = nodes(e_out)

    f_out = run(exe, outdir, "F_three_fields_then_perft",
                ["position startpos", "isready", "position fen " + THREE_FIELD, "isready", "go perft 3"])
    f_refused = ("invalid FEN" in f_out)
    f_nodes = nodes(f_out)

    g_out = run(exe, outdir, "G_both_fens",
                ["position fen " + CASTLE_FEN, "isready", "position fen " + OTHER, "isready", "go perft 1"])
    g_nodes = nodes(g_out)
    g_other_py = perft_py(OTHER, 1)

    checks = [
        ("A: the castle-rights FEN is REFUSED", a_refused, "invalid FEN line printed: %s" % a_refused),
        ("B: startpos perft 3 == 8902", b_nodes == 8902, "got %s" % b_nodes),
        ("C: python-chess perft 3 of that board == 8802", c_nodes == 8802, "got %d" % c_nodes),
        ("D: after the refused FEN, perft 3 == 8902 (startpos left in place)", d_nodes == 8902, "got %s" % d_nodes),
        ("E: startpos then refused FEN, perft 3 == 8902", e_nodes == 8902, "got %s" % e_nodes),
        ("F: a 3-field FEN is refused and also leaves startpos (8902)",
         f_refused and f_nodes == 8902, "refused=%s nodes=%s" % (f_refused, f_nodes)),
        ("G: a legal FEN after the refused one takes effect (KvK perft 1 == python-chess)",
         g_nodes == g_other_py, "engine %s vs python %d" % (g_nodes, g_other_py)),
    ]
    verdict = "CONFIRMS" if all(ok for _, ok, _ in checks) else "REFUTES"
    with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
        fh.write("check of 21-F1 by seat 19 (independent harness, written from the finding's text)\n")
        fh.write("exe: %s\n" % os.path.abspath(exe))
        fh.write("date-utc: %s\n\n" % subprocess.run(["date", "-u"], capture_output=True, text=True).stdout.strip())
        for label, ok, detail in checks:
            fh.write("%-6s %s  [%s]\n" % ("PASS" if ok else "FAIL", label, detail))
        fh.write("\nA alone refused: %s ; A's reported nodes: %s\n" % (a_refused, a_nodes))
        fh.write("VERDICT %s 21-F1\n" % verdict)
    print(open(os.path.join(outdir, "RESULT.txt")).read())


if __name__ == "__main__":
    main()
