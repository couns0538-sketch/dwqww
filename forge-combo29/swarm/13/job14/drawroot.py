#!/usr/bin/env python3
"""Verify FABLE file 6's headline claim: the drawn-root defect is REPAIRED on the PC build.

File 6 says: on the base tree 6b98f217 a drawn root (halfmove counter >= 100, or third occurrence of a
position) is scored 0 and the engine searches 0 nodes, playing its first legal move even when a mate is
on the board; and that on the owner's PC this is REPAIRED since 15 November, so such a root is searched
like any other (only insufficient material is still answered at once).

This tests that claim directly on both builds, which is the question that actually matters: does the PC
patch deliver the fix, and does the base tree still have the defect?

Cases, each a FRESH process, Threads 1, Hash 16, OwnBook false:
  A. mate-in-1 at halfmove 100   -> base: expect 0 nodes / first legal move; PC: expect the MATE
  B. mate-in-1 at halfmove 150   -> same expectation
  C. mate-in-1 at halfmove 0     -> both builds should find the mate (control)
  D. mate-in-1 at halfmove 99    -> both should find the mate (control, just below the threshold)
  E. a THIRD-OCCURRENCE repetition root with a mate available, reached by a real move sequence
     -> base: expect the drawn-root behaviour; PC: expect the mate
  F. K vs K (insufficient material) -> BOTH builds should answer at once (file 6 says only this
     remains), which is a control that the fix did not overshoot

A case is reported with its node count, score, bestmove, and whether the bestmove is the mating move.

Usage: drawroot.py BASE_EXE PC_EXE OUTDIR
"""
import json
import os
import re
import subprocess
import sys

import chess

BASE_EXE = sys.argv[1]
PC_EXE = sys.argv[2]
OUTDIR = sys.argv[3]
os.makedirs(OUTDIR, exist_ok=True)

OPTS_BASE = [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")]
BAD = ("unknown option", "invalid value", "error")

# A mate-in-1 where white plays Ra8#. Halfmove/fullmove are overridden per case.
MATE_FEN_BODY = "6k1/5ppp/8/8/8/8/8/R5K1 w - - {} 1"
MATE_MOVE = "a1a8"


def mate_cases():
    return [
        ("A mate1 halfmove 100", MATE_FEN_BODY.format(100)),
        ("B mate1 halfmove 150", MATE_FEN_BODY.format(150)),
        ("C mate1 halfmove 0   (control)", MATE_FEN_BODY.format(0)),
        ("D mate1 halfmove 99  (control)", MATE_FEN_BODY.format(99)),
    ]


REP_MOVES_THRICE = ["a1a2", "g8h8", "a2a1", "h8g8",
                    "a1a2", "g8h8", "a2a1", "h8g8"]   # puts the position on the board a THIRD time
REP_MOVES_TWICE = REP_MOVES_THRICE[:4]               # two occurrences only (control)


def repetition_position_cmd(thrice=True):
    """A `position ... moves` command that genuinely repeats the start position.

    A bare `position fen` CANNOT express a repetition: a FEN carries no occurrence history, so the
    engine cannot know the position has been seen before. My first attempt used a bare FEN and the
    case was therefore vacuous (it "passed" while testing nothing). This returns a move-list command
    instead, and asserts the repetition actually occurred and the halfmove clock did NOT reset.
    """
    start = "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1"
    b = chess.Board(start)
    moves = REP_MOVES_THRICE if thrice else REP_MOVES_TWICE

    def key(board):
        """The engine's repetition key: pieces, side to move, castling, ep — NOT the move counters.
        Keying on the full FEN string was my second mistake here: the halfmove/fullmove fields change
        on every shuffle, so a full-FEN dict reported 1 occurrence for a genuine 3-fold repetition."""
        return " ".join(board.fen().split()[:4])

    counts = {key(b): 1}
    for u in moves:
        m = chess.Move.from_uci(u)
        if m not in b.legal_moves:
            raise SystemExit("FAIL: repetition move %s illegal in %s" % (u, b.fen()))
        b.push(m)
        counts[key(b)] = counts.get(key(b), 0) + 1
    want = 3 if thrice else 2
    if counts.get(key(b), 0) < want:
        raise SystemExit("FAIL: repetition built %d occurrences, wanted %d"
                         % (counts.get(key(b), 0), want))
    if b.halfmove_clock == 0:
        raise SystemExit("FAIL: halfmove clock reset - this is not a repetition candidate")
    return "position fen " + start + " moves " + " ".join(moves)


def run(exe, pos_cmd, go_cmd="go depth 8"):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            l = p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died")
            l = l.rstrip("\n")
            if any(x in l.lower() for x in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if pred(l):
                return l

    send("uci")
    seen = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died in uci handshake")
        l = l.rstrip("\n")
        if l.startswith("option name"):
            seen.append(l)
        if l == "uciok":
            break
    for n, v in OPTS_BASE:
        if not any(o.startswith("option name %s " % n) for o in seen):
            continue
        send("setoption name %s value %s" % (n, v))
        send("isready")
        until(lambda s: s == "readyok")
    send(pos_cmd)
    send("isready")
    until(lambda s: s == "readyok")
    send(go_cmd)
    last = None
    bm = None
    infos = 0
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died during search")
        l = l.rstrip("\n")
        if l.startswith("info depth"):
            last = l
            infos += 1
        if l.startswith("bestmove"):
            bm = l
            break
    send("quit")
    try:
        p.wait(timeout=15)
    except Exception:
        p.kill()

    def g(pat):
        m = re.search(pat, last) if last else None
        return int(m.group(1)) if m else None

    mv = bm.split()[1] if bm and len(bm.split()) > 1 else None
    return {"bestmove": mv, "info_lines": infos,
            "nodes": g(r"\bnodes (\d+)"), "cp": g(r"\bscore cp (-?\d+)"),
            "mate": g(r"\bscore mate (-?\d+)"), "depth": g(r"\bdepth (\d+)")}


def is_mating_move(fen, mv):
    if not mv:
        return False
    try:
        m = chess.Move.from_uci(mv)
    except ValueError:
        return False
    b = chess.Board(fen)
    if m not in b.legal_moves:
        return False
    b.push(m)
    return b.is_checkmate()


def main():
    cases = [(lab, "position fen " + fen) for lab, fen in mate_cases()]
    cases.append(("E third-occurrence + mate", repetition_position_cmd(thrice=True)))
    cases.append(("E2 two occurrences (control)", repetition_position_cmd(thrice=False)))
    cases.append(("F KvK insufficient material",
                  "position fen 8/8/8/4k3/8/8/4K3/8 w - - 0 1"))

    reps = {c[0]: True for c in cases}
    # how many times is the E position on the board? report it, because the CASE depends on it
    out = []
    for label, poscmd in cases:
        fen = poscmd.split("position fen ")[1].split(" moves ")[0]
        row = {"case": label, "fen": fen, "position_cmd": poscmd}
        for tag, exe in (("base", BASE_EXE), ("pc", PC_EXE)):
            try:
                r = run(exe, poscmd)
            except SystemExit as e:
                r = {"error": str(e)}
            r["is_mate_move"] = is_mating_move(fen, r.get("bestmove"))
            row[tag] = r
        out.append(row)
        print("%-32s base: nodes %-7s mate %-5s bm %-6s mate_move %-5s | pc: nodes %-7s mate %-5s bm %-6s mate_move %s"
              % (label,
                 row["base"].get("nodes"), row["base"].get("mate"), row["base"].get("bestmove"),
                 row["base"].get("is_mate_move"),
                 row["pc"].get("nodes"), row["pc"].get("mate"), row["pc"].get("bestmove"),
                 row["pc"].get("is_mate_move")), flush=True)

    # verdicts
    a, b_, c, d = out[0], out[1], out[2], out[3]
    e, e2, f = out[4], out[5], out[6]
    checks = []
    checks.append(("C control: both builds find the mate at halfmove 0",
                   c["base"].get("is_mate_move") and c["pc"].get("is_mate_move")))
    checks.append(("D control: both builds find the mate at halfmove 99",
                   d["base"].get("is_mate_move") and d["pc"].get("is_mate_move")))
    checks.append(("base build DOES have the drawn-root defect at halfmove 100 (file 6's claim)",
                   not a["base"].get("is_mate_move")))
    checks.append(("PC build REPAIRS it at halfmove 100 (file 6's claim)",
                   a["pc"].get("is_mate_move")))
    checks.append(("PC build repairs it at halfmove 150 too", b_["pc"].get("is_mate_move")))
    checks.append(("E control: with only TWO occurrences BOTH builds find the mate",
                   e2["base"].get("is_mate_move") and e2["pc"].get("is_mate_move")))
    checks.append(("base build HAS the third-occurrence defect (0 nodes, mate missed)",
                   not e["base"].get("is_mate_move")))
    checks.append(("PC build repairs the third-occurrence case", e["pc"].get("is_mate_move")))
    checks.append(("F control: KvK is still answered at once on BOTH builds",
                   (f["base"].get("nodes") or 0) == 0 and (f["pc"].get("nodes") or 0) == 0))

    summary = {"base_exe": os.path.abspath(BASE_EXE), "pc_exe": os.path.abspath(PC_EXE),
               "checks": [{"claim": c_, "holds": bool(h)} for c_, h in checks],
               "all_claims_hold": all(h for _c, h in checks)}
    json.dump({"summary": summary, "rows": out},
              open(os.path.join(OUTDIR, "drawroot.json"), "w"), indent=1)
    print()
    for c_, h in checks:
        print("%-70s %s" % (c_, "HOLDS" if h else "DOES NOT HOLD"))


main()
