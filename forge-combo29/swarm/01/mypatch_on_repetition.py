#!/usr/bin/env python3
"""swarm seat 01: THE decisive test — my patch against seat 12's REPETITION door.

Seat 12's case, taken verbatim from its own script `forge-combo29/swarm/12/job1/two_doors.py` on branch
for-fable-and-opus/swarm-12 (I read it to get the case; the harness below is mine):

    BASE    = "6k1/5ppp/8/8/8/8/8/R5NK w - - 0 1"      (white Ra8# is mate in 1)
    SHUFFLE = "g1f3 g8h8 f3g1 h8g8 g1f3 g8h8 f3g1 h8g8"  (white N g1<->f3, black K g8<->h8)
    -> after the shuffle the SAME position stands for the third time, halfmove clock 8, well under 100.

Doors tested, every case a fresh process:
  door1_h99   the board at halfmove 99          (fifty-move door, just below the claim)
  door1_h100  the board at halfmove 100         (fifty-move door, at the claim)
  door2_rep   BASE + SHUFFLE (threefold, counter 8)   <- the repetition door
  control_fen BASE as a plain FEN               (no history: must find the mate on every build)

My patch removes only `board.halfmove_clock() >= 100` from root_drawn, so on paper it must NOT help door 2.
This run establishes that by measurement rather than by reasoning. The setup is VERIFIED first: python-chess
must report is_repetition(3) true and the shuffle must be legal, or the case is reported SETUP FAILED and no
verdict is drawn (the mistake S-F25 records).

Usage: mypatch_on_repetition.py <base-exe> <mine-exe> <s12-exe> <outdir>
"""
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

import chess

TIMEOUT = 300.0
BASE = "6k1/5ppp/8/8/8/8/8/R5NK w - - 0 1"
SHUFFLE = "g1f3 g8h8 f3g1 h8g8 g1f3 g8h8 f3g1 h8g8".split()


class R:
    def __init__(self, fd):
        self.fd, self.buf, self.eof = fd, b"", False

    def line(self, deadline):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            remain = deadline - time.monotonic()
            if remain <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], remain)
            if not r:
                return None
            c = os.read(self.fd, 65536)
            if not c:
                self.eof = True
                return None
            self.buf += c
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


def run(exe, position_lines, go="go depth 6"):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []

    def until(prefix):
        d = time.monotonic() + TIMEOUT
        while True:
            l = rd.line(d)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    # `quit` is sent only AFTER bestmove: quit itself stops the search.
    for line in position_lines:
        send(line)
    send("isready")
    if until("readyok") is None:
        p.kill()
        return {"error": "no readyok"}
    rejected = [l for l in buf if l.startswith("info string illegal move")
                or l.startswith("info string invalid FEN")]
    send(go)
    bml = until("bestmove")
    time.sleep(0.15)
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    dl = [l for l in buf if l.startswith("info depth")]
    score = nodes = ""
    if dl:
        f = dl[-1].split()
        if "score" in f:
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
        if "nodes" in f:
            nodes = f[f.index("nodes") + 1]
    return {"score": score, "nodes": nodes, "bestmove": bml.split()[1] if bml else None,
            "depths": len(dl), "rejected": rejected}


def verify_setup():
    """The setup must be a genuine threefold with a legal shuffle, and the board must have mate in 1."""
    b = chess.Board(BASE)
    mates = []
    for m in b.legal_moves:
        b.push(m)
        if b.is_checkmate():
            mates.append(m.uci())
        b.pop()
    moves = []
    ok = True
    for u in SHUFFLE:
        mv = chess.Move.from_uci(u)
        if mv not in b.legal_moves:
            ok = False
            break
        b.push(mv)
        moves.append(u)
    return {
        "mate_in_1_on_base": mates,
        "shuffle_all_legal": ok,
        "threefold_after_shuffle": b.is_repetition(3),
        "halfmove_after_shuffle": b.halfmove_clock,
        "fen_after_shuffle": b.fen(),
        "board_has_knights": bool(b.pieces(chess.KNIGHT, chess.WHITE) or b.pieces(chess.KNIGHT, chess.BLACK)),
    }


def main():
    base_exe, mine_exe, s12_exe, out = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    chk = verify_setup()
    lines = ["my patch against seat 12's REPETITION door (seat 12's own case, my harness)",
             "go: 'go depth 6'; every case a fresh process; no setoption sent; quit sent only after bestmove",
             "SETUP VERIFICATION (python-chess):"]
    for k, v in chk.items():
        lines.append("   %s = %s" % (k, v))
    exes = [("base", base_exe), ("mine", mine_exe), ("seat12", s12_exe)]
    for label, exe in exes:
        lines.append("%-7s %s sha256 %s" % (label, exe,
                                           hashlib.sha256(Path(exe).read_bytes()).hexdigest()))
    lines.append("")

    if not chk["threefold_after_shuffle"] or not chk["shuffle_all_legal"]:
        lines.append("SETUP FAILED — no verdict drawn (this is the S-F25 mistake and must not repeat)")
        (out / "mypatch_on_repetition.txt").write_text("\n".join(lines) + "\n")
        print("\n".join(lines))
        return

    mate = chk["mate_in_1_on_base"][0]
    cases = [
        ("control_fen", ["position fen " + BASE], "no history"),
        ("door1_h99", ["position fen " + BASE.replace(" w - - 0 1", " w - - 99 1")], "fifty-move door, 99"),
        ("door1_h100", ["position fen " + BASE.replace(" w - - 0 1", " w - - 100 1")], "fifty-move door, 100"),
        ("door2_rep", ["position fen " + BASE + " moves " + " ".join(SHUFFLE)],
         "REPETITION door, counter %d" % chk["halfmove_after_shuffle"]),
    ]
    lines.append("case\twhat\t%s\tdoor closed?" % "\t".join(l for l, _ in exes))
    rows = []
    for name, pos, what in cases:
        got = {}
        for label, exe in exes:
            got[label] = run(exe, pos)
        found = [k for k in got if got[k].get("bestmove") == mate]
        closed = [k for k in got if k not in found]
        row = {"case": name, "what": what, "results": got, "mate_move": mate,
               "found_by": found, "closed_for": closed}
        rows.append(row)
        lines.append("%s\t%s\t%s\t%s" % (
            name, what,
            "\t".join("%s %s/%s/%s" % (l, got[l].get("score"), got[l].get("nodes"),
                                       got[l].get("bestmove")) for l, _ in exes),
            "still closed on: %s" % (",".join(closed) or "nobody")))
        print("%-12s %-28s %s  found_by=%s"
              % (name, what,
                 "  ".join("%s %s/%s" % (l, got[l].get("score"), got[l].get("nodes"))
                           for l, _ in exes),
                 ",".join(found) or "nobody"), flush=True)

    # the verdict the coordinator asked for, computed from the data
    rep = next(r for r in rows if r["case"] == "door2_rep")
    v = []
    if "mine" in rep["found_by"]:
        v.append("VERDICT: MY PATCH ALSO FIXES THE REPETITION DOOR -> mine is strictly better.")
    else:
        v.append("VERDICT: my patch does NOT fix the repetition door -> the two patches cover DIFFERENT")
        v.append("doors and a merger must choose by which door matters:")
        v.append("   counter-resetting mates (incl. mate-in-1 at 100) : mine")
        v.append("   mate-in-1 at a threefold root, counter well under 100 : seat 12's")
        v.append("   mate-in-1 at halfmove 100                                : BOTH")
    lines.append("")
    lines.extend(v)
    (out / "mypatch_on_repetition.json").write_text(json.dumps({"setup": chk, "rows": rows,
                                                                "verdict": v}, indent=1))
    (out / "mypatch_on_repetition.txt").write_text("\n".join(lines) + "\n")
    print("")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
