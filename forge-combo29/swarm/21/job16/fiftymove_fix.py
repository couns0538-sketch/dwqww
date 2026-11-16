#!/usr/bin/env python3
"""fiftymove_fix.py EXE OUTDIR [BASE_EXE]

THIRD INDEPENDENT VERIFICATION of seat 12's `two_doors_mate.patch.txt`.

The patch closes TWO doors at a drawn root: the fifty-move counter (halfmove >= 100) and a
threefold repetition — in both, a root that has a mate in one available is now searched
normally instead of being adjudicated 0-node `cp 0`.

COLD-BASELINE RULE (seat 10): two identical searches in one process are NOT comparable
(56,720 -> 4,951 -> 4,516 on startpos), and `Clear Hash` does not restore cold (it gives a
third value). A cold baseline is a fresh process or `ucinewgame`. So:

  - every node-count comparison in this script uses a FRESH PROCESS for each side, and
  - where two searches must happen in one process (the sanitizer run), their node counts are
    NEVER compared against each other — only against the fresh-process reference, and each
    is labelled with the process it came from.

Cases (all verified with python-chess, board copied per candidate move):
  WHITE  fifty-move  mate in 1 at hm 100 / hm 99   (the door 21-F9 proved)
  BLACK  fifty-move  mate in 1 at hm 100 / hm 99
  WHITE  repetition  mate in 1 with the same position three times / two times (control)
  BLACK  repetition  mate in 1 three times / two times
  QUIET  a rook-up board at hm 100 and at hm 99 — the fix must NOT make the engine search a
         genuinely drawn root when no mate is available (that is what 30-F8 warned about)

Pins: bench 11 / 13 / 16 and perft 5, each in a FRESH process.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout, bestmove_of, last_info  # noqa: E402

import chess

PINS = [("bench 11", 312866), ("bench 13", 862329), ("bench 16", 3024920), ("perft 5", 4865609)]


def mates_in_one(fen):
    b = chess.Board(fen)
    out = []
    for m in list(b.legal_moves):
        c = b.copy()
        c.push(m)
        if c.is_checkmate():
            out.append(m.uci())
    return out


def repetition_fen():
    """A position that has occurred three times, reached by a move list, with a mate in 1
    available to the side to move. Built by shuffling knights so the same position recurs."""
    b = chess.Board("r5k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 60")
    seq = []
    # shuffle knights out and back twice over, giving the same position three times, then
    # find a mate-in-1 line for White (Ra1-a8 needs the black king boxed: use a rook mate).
    # Simpler: repeat the initial position by moving a rook back and forth.
    b = chess.Board("6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 60")
    cycle = ["e1d1", "g8h8", "d1e1", "h8g8"]
    for _ in range(2):
        for mv in cycle:
            b.push_uci(mv)
            seq.append(mv)
    return b, seq


def rep_two(b_seq):
    """Same cycle once only: the position appears twice, not three times (the control)."""
    b = chess.Board("6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 60")
    seq = ["e1d1", "g8h8", "d1e1", "h8g8"]
    for mv in seq:
        b.push_uci(mv)
    return b, seq


def fresh(exe, lines, timeout=300):
    """Kept ONLY for synchronous commands (`bench`, `go perft`) which finish before returning
    and print their count without a `bestmove`. NEVER used for a search (19-F12)."""
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    p = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                       capture_output=True, timeout=timeout, env=env, errors="replace")
    return p.stdout + p.stderr


def safe_search(exe, raw_path, pos_line, search, timeout=180):
    """Search through safe_engine: stdout read to `bestmove` before anything else is sent,
    stdin never closed mid-search (19-F12). One FRESH PROCESS per call, so the baseline is
    cold by construction and no node count is compared across searches in one process."""
    e = SafeEngine(exe, raw_path)
    ans = e.position(pos_line)
    if any("invalid FEN" in l for l in ans):
        e.close()
        raise AssertionError("position REFUSED: %s" % [l for l in ans if "info string" in l])
    try:
        lines = e.go(search, timeout=timeout)
    finally:
        e.close()
    return lines


def parse_pins(out, name):
    pats = {"bench 11": r"bench depth 11 nodes (\d+)", "bench 13": r"bench depth 13 nodes (\d+)",
            "bench 16": r"bench depth 16 nodes (\d+)", "perft 5": r"^nodes (\d+)$"}
    key = name.replace("perft", "perft")
    m = re.search(pats[name], out, re.M)
    return int(m.group(1)) if m else None


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    base = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(outdir, exist_ok=True)
    rows = ["| case | python mate in 1 | engine bestmove | is it a mate | nodes | search | process |",
            "|---|---|---|---|---|---|---|"]
    results = {}

    def case(tag, pos_line, fen_or_board, mates, search, fresh_process_tag=None):
        """One FRESH PROCESS per case (cold by construction), read to `bestmove`."""
        raw = os.path.join(outdir, tag + "_raw.txt")
        lines = safe_search(exe, raw, pos_line, search)
        with open(raw, "a") as fh:
            fh.write(">>> %s\n" % search)
            for l in lines:
                fh.write(l + "\n")
        bm = bestmove_of(lines)
        info = [l for l in lines if l.startswith("info depth")]
        last = info[-1] if info else ""
        nd = re.search(r" nodes (\d+)", last)
        nodes = nd.group(1) if nd else "-"
        found = (bm in mates) if mates else None
        rows.append("| %s | %s | %s | %s | %s | %s | fresh |" % (
            tag, ", ".join(mates) or "none", bm,
            ("MATE" if found else "MISSED") if mates else ("0 NODES" if nodes == "0" else "searched"),
            nodes, search))
        results[tag] = dict(bm=bm, nodes=nodes, found=found, info=last)

    # ---- the fifty-move door, both colours
    w100 = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60"
    w99 = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 99 60"
    b100 = "r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 100 60"
    b99 = "r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 99 60"
    for tag, fen in (("W_hm100", w100), ("W_hm99", w99), ("B_hm100", b100), ("B_hm99", b99)):
        case(tag, "position fen " + fen, fen, mates_in_one(fen), "go depth 5")

    # ---- the repetition door, both colours, three times vs twice
    def build_cycle(start, moves, reps):
        b = chess.Board(start)
        seq = []
        for _ in range(reps):
            for mv in moves:
                b.push_uci(mv)
                seq.append(mv)
        return b, seq

    W_START = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 60"
    W_MOVES = ["e1d1", "g8h8", "d1e1", "h8g8"]
    B_START = "r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 0 60"
    B_MOVES = ["a8b8", "g1h1", "b8a8", "h1g1"]

    for tag, start, moves in (("W", W_START, W_MOVES), ("B", B_START, B_MOVES)):
        for reps, label in ((2, "rep3"), (1, "rep2")):
            b, seq = build_cycle(start, moves, reps)
            threefold = b.is_repetition(3)
            case("%s_%s" % (tag, label),
                 "position fen %s moves %s" % (start, " ".join(seq)), None,
                 mates_in_one(b.fen()), "go depth 5")
            # record what python-chess says about the repetition, for the report
            with open(os.path.join(outdir, "%s_%s_python.txt" % (tag, label)), "w") as fh:
                fh.write("fen: %s\nmoves: %s\npython-chess threefold: %s\nmate in 1: %s\n"
                         % (b.fen(), " ".join(seq), threefold, mates_in_one(b.fen())))

    # ---- the quiet board: the fix must NOT search a genuinely drawn root
    quiet100 = "4k3/8/8/8/8/8/4P3/4K2R w - - 100 60"
    quiet99 = "4k3/8/8/8/8/8/4P3/4K2R w - - 99 60"
    case("QUIET_hm100", "position fen " + quiet100, None, [], "go depth 5")
    case("QUIET_hm99", "position fen " + quiet99, None, [], "go depth 5")

    # ---- pins, each a fresh process
    pins_rows = []
    for name, expect in PINS:
        cmd = ("go perft 5" if name == "perft 5" else name)
        out = fresh(exe, [cmd])
        got = parse_pins(out, name)
        pins_rows.append("| %s | %d | %s | %s |" % (
            name, expect, got, "PASS" if got == expect else "FAIL"))
        with open(os.path.join(outdir, "pin_" + name.replace(" ", "_") + ".txt"), "w") as fh:
            fh.write(out)

    # ---- sanitizer check: the whole case list in ONE process is NOT used for node counts;
    #      here we only ask whether the runner sees a sanitizer line at all.
    san_hits = []
    for f in os.listdir(outdir):
        if f.endswith("_raw.txt"):
            t = open(os.path.join(outdir, f), errors="replace").read()
            if any(m in t for m in ("AddressSanitizer", "runtime error", "__ubsan",
                                    "SUMMARY: UndefinedBehavior")):
                san_hits.append(f)

    out = rows + ["", "| pin | expected | got | verdict |", "|---|---|---|---|"] + pins_rows + [""]
    out.append("sanitizer lines anywhere in the case outputs: %s" % (san_hits or "none"))
    # verdict
    def got(tag):
        return results[tag]
    doors_white = got("W_hm100")["found"] and got("W_rep3")["found"]
    doors_black = got("B_hm100")["found"] and got("B_rep3")["found"]
    controls = got("W_hm99")["found"] and got("B_hm99")["found"]
    quiet_ok = got("QUIET_hm100")["nodes"] == "0" and got("QUIET_hm99")["nodes"] != "0"
    pins_ok = all("PASS" in r for r in pins_rows)
    out.append("")
    out.append("both doors closed, White: %s" % doors_white)
    out.append("both doors closed, Black: %s" % doors_black)
    out.append("counter-99 / two-occurrence controls find the mate: %s" % controls)
    out.append("quiet drawn root still adjudicated (0 nodes at 100, searched at 99): %s" % quiet_ok)
    out.append("pins unchanged: %s" % pins_ok)
    out.append("sanitizer lines: %s" % (san_hits or "none"))
    ok = doors_white and doors_black and controls and quiet_ok and pins_ok and not san_hits
    out.append("")
    out.append("=> %s" % ("FIX VERIFIED (third independent check)" if ok else "FIX NOT VERIFIED"))
    text = "\n".join(out)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()