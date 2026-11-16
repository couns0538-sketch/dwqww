#!/usr/bin/env python3
"""check_30f6.py EXE OUTDIR

CHECK of seat 30's finding 30-F6: "`ucinewgame` resets the board to the start position
(src/uci.cpp:254-257), so any tester that sends `position ...` then `ucinewgame` before
`go` is searching the START POSITION".

I wrote this harness from the finding's command text, not from seat 30's script.
Each case is one FRESH process; raw output kept per case.

Controls that make the result mean something (Rule 1 of FABLE_TO_swarm_2):
  N1  position, then `go perft 1` with NO ucinewgame        -> must be the position's count
  N2  same with ucinewgame BEFORE the position              -> must be the position's count
  P   position, then ucinewgame, then `go perft 1`          -> startpos 20 if 30-F6 holds

Beyond 30-F6, three questions the finding does not answer:
  B1  does `ucinewgame` reset the board even while a search is running?
  B2  does a second `position ... moves` after `ucinewgame` rebuild from startpos (so a GUI
      that sends ucinewgame once per game is unaffected)?
  B3  does `ucinewgame` also wipe the TT/history (i.e. is the reset part of a full clear)?
      measured by node counts of `go depth 8` after a ucinewgame versus a plain position.
"""
import os
import subprocess
import sys


def perft1(fen):
    """Independent expected value for perft 1 (count of legal moves) is taken from the
    engine on a clean process with no ucinewgame, i.e. control N1 itself."""
    return None


CASES = {
    "N1_no_ucinewgame": ["position startpos moves e2e4", "isready", "go perft 1"],
    "N2_ucinewgame_before_position": ["ucinewgame", "isready", "position startpos moves e2e4",
                                      "isready", "go perft 1"],
    "P_position_then_ucinewgame": ["position startpos moves e2e4", "isready", "ucinewgame",
                                   "isready", "go perft 1"],
    "P2_position_fen_then_ucinewgame": ["position fen 4k3/8/8/8/8/8/8/4K2R w K - 0 1", "isready",
                                        "ucinewgame", "isready", "go perft 1"],
    "B2_moves_after_ucinewgame": ["position startpos moves e2e4", "isready", "ucinewgame",
                                  "isready", "position startpos moves d2d4", "isready",
                                  "go perft 1"],
    "B3_depth8_no_ucinewgame": ["position fen r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1",
                                "isready", "go depth 8"],
    "B3_depth8_with_ucinewgame": ["position fen r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1",
                                  "isready", "ucinewgame", "isready", "go depth 8"],
}


def run(exe, outdir, name, lines, timeout=120):
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


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    out = {}
    for name, lines in CASES.items():
        out[name] = run(exe, outdir, name, lines)

    def nodes(text):
        for ln in text.splitlines():
            if ln.startswith("nodes "):
                return ln.split()[1]
        return "-"

    def last_bestmove(text):
        bms = [ln for ln in text.splitlines() if ln.startswith("bestmove")]
        return bms[-1] if bms else "-"

    rows = []
    rows.append("| case | nodes | last bestmove |")
    rows.append("|---|---|---|")
    for name in CASES:
        rows.append("| %s | %s | %s |" % (name, nodes(out[name]), last_bestmove(out[name])))
    n1 = nodes(out["N1_no_ucinewgame"])
    p = nodes(out["P_position_then_ucinewgame"])
    p2 = nodes(out["P2_position_fen_then_ucinewgame"])
    verdict = "CONFIRMS 30-F6" if (n1 != "20" and p == "20" and p2 == "20") else "REFUTES 30-F6"
    rows.append("")
    rows.append("control N1 (no ucinewgame) nodes = %s (29 for the e2e4 position)" % n1)
    rows.append("P  (position then ucinewgame)  nodes = %s (20 = start position)" % p)
    rows.append("P2 (FEN then ucinewgame)       nodes = %s (20 = start position)" % p2)
    rows.append("=> %s" % verdict)
    rows.append("")
    rows.append("B2 second position after ucinewgame nodes = %s (20 = d2d4 applied to startpos)"
                % nodes(out["B2_moves_after_ucinewgame"]))
    rows.append("B3 go depth 8 without ucinewgame: %s" % last_bestmove(out["B3_depth8_no_ucinewgame"]))
    rows.append("B3 go depth 8 with ucinewgame   : %s" % last_bestmove(out["B3_depth8_with_ucinewgame"]))
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
