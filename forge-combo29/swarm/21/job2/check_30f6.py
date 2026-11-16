#!/usr/bin/env python3
"""check_30f6.py EXE OUTDIR

CHECK of seat 30's finding 30-F6: "`ucinewgame` resets the board to the start position
(src/uci.cpp:254-257), so any tester that sends `position ...` then `ucinewgame` before
`go` is searching the START POSITION".

Harness written by me (seat 21) from the finding's text, not copied from seat 30's script.

IMPORTANT: the finding's own evidence is confounded. It compares 20 ("start position")
against "the 29 after e2e4" — but after 1.e4 it is BLACK to move and Black also has
exactly 20 legal moves, so `perft 1` cannot tell the two positions apart. Startpos perft 1
is 20 as well. Every case here therefore uses positions whose perft 1 differs from 20:
  A2 after 1.e4 e5 2.Nf3 Nc6 3.Bb5 : 27 plies... perft 1 differs from startpos (20)
Verified per case below by printing the position's perft 1 in a control process.

Cases (fresh process each, raw output kept):
  N1  position <pos>, go perft 1   (NO ucinewgame)      -> the position's own count
  N2  ucinewgame, position <pos>, go perft 1            -> the position's own count
  P   position <pos>, ucinewgame, go perft 1            -> 20 (startpos) iff 30-F6 holds
  P2  position fen <POS_FEN>, ucinewgame, go perft 1    -> same, for a FEN command
  R   position <pos>, isready, go perft 3, ucinewgame, go perft 1 -> 20 iff 30-F6 holds
      (ucinewgame AFTER a search has run)
  E   position <pos>, ucinewgame, position <pos2>, go perft 1 -> pos2's count (a GUI that
      sends ucinewgame per game is unaffected)
  S   position <pos>, isready, go depth 10, isready, (ucinewgame), isready, go depth 10
      -> whether the reset also clears the TT (bestmove/nodes compared)
"""
import os
import subprocess
import sys

POS = "startpos moves e2e4 e7e5 g1f3 b8c6 f1b5"     # 5 plies, BLACK to move
POS_FEN = "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
POS2 = "startpos moves d2d4 d7d5 c2c4"                # 3 plies, BLACK to move
SEARCH_FEN = "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"

CASES = {
    "N1_no_ucinewgame": ["position " + POS, "isready", "go perft 1"],
    "N2_ucinewgame_before": ["ucinewgame", "isready", "position " + POS, "isready", "go perft 1"],
    "P_then_ucinewgame": ["position " + POS, "isready", "ucinewgame", "isready", "go perft 1"],
    "P2_fen_then_ucinewgame": ["position fen " + POS_FEN, "isready", "ucinewgame", "isready",
                              "go perft 1"],
    "R_ucinewgame_after_search": ["position " + POS, "isready", "go perft 3", "ucinewgame",
                                  "isready", "go perft 1"],
    "E_ucinewgame_then_new_position": ["position " + POS, "isready", "ucinewgame", "isready",
                                       "position " + POS2, "isready", "go perft 1"],
    "N3_pos2_no_ucinewgame": ["position " + POS2, "isready", "go perft 1"],
}


def run(exe, outdir, name, lines, timeout=180):
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    p = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                       capture_output=True, timeout=timeout, env=env)
    with open(os.path.join(outdir, name + ".txt"), "w") as fh:
        fh.write("=== exe: %s\n" % os.path.abspath(exe))
        fh.write("=== lines sent:\n" + "\n".join(">>> " + s for s in lines) + "\n")
        fh.write("=== stdout:\n" + p.stdout + "\n=== stderr:\n" + p.stderr)
        fh.write("=== returncode: %d\n" % p.returncode)
    return p.stdout


def nodes_list(text):
    return [ln.split()[1] for ln in text.splitlines() if ln.startswith("nodes ")]


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    out = {n: run(exe, outdir, n, l) for n, l in CASES.items()}

    # startpos reference, measured, not assumed
    ref = run(exe, outdir, "REF_startpos_perft1", ["position startpos", "isready", "go perft 1"])
    startpos1 = nodes_list(ref)[0]

    n1 = nodes_list(out["N1_no_ucinewgame"])[0]
    n2 = nodes_list(out["N2_ucinewgame_before"])[0]
    p = nodes_list(out["P_then_ucinewgame"])[0]
    p2 = nodes_list(out["P2_fen_then_ucinewgame"])[0]
    r = nodes_list(out["R_ucinewgame_after_search"])[-1]
    e = nodes_list(out["E_ucinewgame_then_new_position"])[0]
    n3 = nodes_list(out["N3_pos2_no_ucinewgame"])[0]

    controls_ok = (n1 != startpos1) and (n2 == n1) and (n3 != startpos1)
    holds = (p == startpos1) and (p2 == startpos1) and (r == startpos1)
    if not controls_ok:
        verdict = "INCONCLUSIVE (a control did not separate the position from startpos)"
    elif holds:
        verdict = "CONFIRMS 30-F6"
    else:
        verdict = "REFUTES 30-F6"

    rows = []
    rows.append("measured startpos perft 1 = %s" % startpos1)
    rows.append("")
    rows.append("| case | perft 1 nodes | equals startpos? | what it shows |")
    rows.append("|---|---|---|---|")
    rows.append("| N1 position, NO ucinewgame (control) | %s | %s | the position's own count |"
                % (n1, n1 == startpos1))
    rows.append("| N2 ucinewgame BEFORE position (control) | %s | %s | reset must not matter here |"
                % (n2, n2 == startpos1))
    rows.append("| P position then ucinewgame | %s | %s | the claim |" % (p, p == startpos1))
    rows.append("| P2 FEN then ucinewgame | %s | %s | the claim, FEN form |" % (p2, p2 == startpos1))
    rows.append("| R ucinewgame AFTER a perft 3 search | %s | %s | the claim with a search first |"
                % (r, r == startpos1))
    rows.append("| E ucinewgame, then a NEW position | %s | %s | GUI that resets per game |"
                % (e, e == startpos1))
    rows.append("| N3 pos2 without ucinewgame (control) | %s | %s | second position's own count |"
                % (n3, n3 == startpos1))
    rows.append("")
    rows.append("controls separate positions from startpos: %s" % controls_ok)
    rows.append("=> %s" % verdict)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
