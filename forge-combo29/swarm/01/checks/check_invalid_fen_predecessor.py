#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 27's S-C84 — does an illegal FEN make the engine search the PREVIOUS position?

Their claim, in three parts:
  1. an illegal FEN is correctly diagnosed (`info string invalid FEN: ...`);
  2. **one** info string is printed and then the engine searches anyway;
  3. it searches **whatever was last set successfully**, not startpos - so in a long session the answer is the
     PREVIOUS position's answer, and a harness with one malformed FEN records a DUPLICATE ROW that looks genuine.

Part 3 is the consequential one and the part worth confirming independently, because it turns a malformed input into a
plausible measurement. My check is built to distinguish it from the two alternatives:

  A. a startpos fallback  -> the answer would be startpos's, identical regardless of what preceded it;
  B. a refusal (no search) -> there would be NO bestmove, or bestmove 0000;
  C. the previous position (their claim) -> the answer is the PREVIOUS position's answer, and CHANGES with it.

The test that separates C from A: run the same invalid FEN after TWO DIFFERENT valid positions. If the answer follows
the predecessor, it is C; if it is constant, it is A. That is the discriminating experiment and it is what this does.

Also checks the duplicate-row consequence directly: does the engine's answer for the invalid FEN equal its answer for
the predecessor? If yes, a harness would log two identical rows for what it believes are two positions.

Usage: check_invalid_fen_predecessor.py <exe> <outdir>
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

# Two valid positions with unmistakably different best answers, and one illegal FEN (adjacent kings).
VALID_A = ("A: rook mate in 1", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1")
VALID_B = ("B: black to move, quiet", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
INVALID = ("illegal: adjacent kings", "8/8/8/3kK3/8/8/8/8 w - - 0 1")


def session(exe, first_fen, invalid_fen, label):
    """Set `first_fen`, search it, then set `invalid_fen` and search that. Record both answers."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, cwd="/tmp")

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(prefix, collect=None):
        for line in p.stdout:
            line = line.rstrip("\n")
            if collect is not None:
                collect.append(line)
            if line.startswith(prefix):
                return line
        return None

    def search(fen, collect):
        send("position fen " + fen)
        send("isready")
        until("readyok", collect)
        send("go depth 8")
        last = None
        for line in p.stdout:
            line = line.rstrip("\n")
            collect.append(line)
            if line.startswith("info depth") and " pv " in line:
                last = line
            if line.startswith("bestmove"):
                return line, last
        return None, last

    send("uci")
    until("uciok")
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    send("isready")
    until("readyok")
    send("ucinewgame")
    send("isready")
    until("readyok")

    first_log = []
    bm_first, info_first = search(first_fen, first_log)

    inv_log = []
    bm_inv, info_inv = search(invalid_fen, inv_log)

    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()

    strings = [l for l in inv_log if l.startswith("info string")]
    return {
        "label": label,
        "first_fen": first_fen,
        "first_bestmove": bm_first.split()[1] if bm_first and len(bm_first.split()) > 1 else None,
        "first_score": next((re.search(r"score (cp|mate) (-?\d+)", l).group(0) for l in reversed(first_log)
                             if "score" in l), None),
        "invalid_bestmove": bm_inv.split()[1] if bm_inv and len(bm_inv.split()) > 1 else None,
        "invalid_score": next((re.search(r"score (cp|mate) (-?\d+)", l).group(0) for l in reversed(inv_log)
                               if "score" in l), None),
        "info_strings_on_invalid": strings,
        "invalid_had_bestmove": bm_inv is not None,
    }


def main():
    exe, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()

    a = session(exe, VALID_A[1], INVALID[1], VALID_A[0])
    b = session(exe, VALID_B[1], INVALID[1], VALID_B[0])

    lines = ["CHECK of seat 27's S-C84: does an illegal FEN make the engine search the PREVIOUS position?",
             "exe: %s" % exe, "sha256: %s" % sha,
             "Threads 1, Hash 16, OwnBook false, go depth 8. The invalid FEN is %s." % INVALID[1], "",
             "THE DISCRIMINATING TEST: the same invalid FEN after two DIFFERENT valid positions.",
             "  A startpos fallback would give the SAME answer both times.",
             "  A refusal would give no bestmove.",
             "  Searching the PREVIOUS position gives each predecessor's own answer.", ""]

    for r in (a, b):
        lines.append("--- preceded by %s" % r["label"])
        lines.append("  predecessor answer : %s (%s)" % (r["first_bestmove"], r["first_score"]))
        lines.append("  invalid-FEN answer : %s (%s)" % (r["invalid_bestmove"], r["invalid_score"]))
        lines.append("  info strings       : %s" % (r["info_strings_on_invalid"] or "NONE"))
        lines.append("  bestmove emitted   : %s" % ("yes" if r["invalid_had_bestmove"] else "NO"))
        lines.append("")

    follows_predecessor = (a["invalid_bestmove"] == a["first_bestmove"] and
                           b["invalid_bestmove"] == b["first_bestmove"] and
                           a["invalid_bestmove"] != b["invalid_bestmove"])
    same_both = (a["invalid_bestmove"] == b["invalid_bestmove"])
    refused = (not a["invalid_had_bestmove"] and not b["invalid_had_bestmove"])
    diagnosed = bool(a["info_strings_on_invalid"]) and bool(b["info_strings_on_invalid"])

    lines.append("VERDICT")
    if refused:
        lines.append("  REFUSED: no bestmove on the invalid FEN. Seat 27's claim does NOT reproduce here.")
    elif follows_predecessor:
        lines.append("  **CONFIRMS seat 27's S-C84 part 3: the answer FOLLOWS THE PREDECESSOR.** Each invalid-FEN")
        lines.append("  answer equals its own predecessor's answer, and the two differ from each other - which is the")
        lines.append("  discriminator: a startpos fallback would have been identical in both sessions.")
        if diagnosed:
            lines.append("  And the engine DID diagnose it (%s), so the diagnosis and the search both happen."
                         % a["info_strings_on_invalid"][0][:70])
        if a["invalid_score"] and a["first_score"] and a["invalid_score"] == a["first_score"]:
            lines.append("  **THE DUPLICATE-ROW CONSEQUENCE IS REAL: the score matches the predecessor's too**, so a")
            lines.append("  harness logging (fen, bestmove, score) would record two indistinguishable rows.")
    elif same_both:
        lines.append("  PARTIAL: the answer is the SAME after both predecessors (%s), which is a START POSITION"
                     % a["invalid_bestmove"])
        lines.append("  fallback rather than a previous-position search. That contradicts their part 3 but not parts 1-2.")
    else:
        lines.append("  DOES NOT MATCH either model - reported as measured; inspect the transcripts.")

    (out / "check_invalid_fen_predecessor.json").write_text(json.dumps({"sha": sha, "a": a, "b": b}, indent=1))
    txt = "\n".join(lines) + "\n"
    (out / "check_invalid_fen_predecessor.txt").write_text(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
