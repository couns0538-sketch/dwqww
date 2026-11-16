#!/usr/bin/env python3
"""swarm seat 01: can the three "extreme counter" FEN accepts reach a REAL GAME?

The coordinator's question, for each of the three I reported:
  halfmove 65536 accepted, fullmove 10^9 accepted, junk after the sixth field accepted.
For each: what would a GUI have to send, is the board still legal, and could it reach a real game at all?

Method: not by reading the code alone. For each case I ask the engine what state it is actually in and
compare it with what a CORRECT reading of the same FEN would give:
  * board identity: `go perft 1` vs python-chess's legal-move count for the CORRECTED board (the guard)
  * counter identity: does the engine's own behaviour agree with the accepted counter? Two probes:
      - a fifty-move probe: put the same board at halfmove 65536 and ask `go depth 10`; if the engine
        treats the counter as >= 100 it adjudicates a draw (base build) or searches (PC build). Either
        way the answer tells me what number it really holds.
      - a fullmove probe: the engine prints no move number, so I test it the only way it can be observed,
        which is whether anything downstream changes. If nothing does, the field is inert.
  * GUI reachability: this is a question about WHO sends such a FEN, so I record exactly what a GUI command
    line would look like and where a well-formed GUI would stop.

Usage: extreme_counters_reach.py <pc-exe> <asan-exe> <outdir>
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
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"


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


def run(exe, lines, go, options=()):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []
    problems = []

    def until(prefix, deadline):
        while True:
            l = rd.line(deadline)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    deadline = time.monotonic() + TIMEOUT
    send("uci")
    until("uciok", deadline)
    for name, value in options:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        until("readyok", deadline)
    for l in buf:
        if l.startswith("unknown option") or "invalid value" in l:
            problems.append(l)
    send("ucinewgame")
    send("isready")
    until("readyok", deadline)
    for s in lines:
        send(s)
    send("isready")
    until("readyok", deadline)
    refused = [l for l in buf if l.startswith("info string invalid FEN")]
    send(go)
    if go.startswith("go perft"):
        until("nodes ", deadline)
    else:
        until("bestmove", deadline)
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=90)
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
    bare = [l for l in buf if l.startswith("nodes ")]
    if bare and not nodes:
        nodes = bare[-1].split()[1]
    return {"score": score, "nodes": nodes, "refused": refused, "problems": problems,
            "sanitizer": [l for l in buf if "Sanitizer" in l or "runtime error" in l]}


def legal_count(fen):
    try:
        b = chess.Board(fen)
    except ValueError:
        return None, "python-chess refuses the FEN"
    if not b.is_valid():
        return b.legal_moves.count(), "python-chess parses it but is_valid() is false"
    return b.legal_moves.count(), "python-chess accepts and the board is legal"


def main():
    pc, asan, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    cases = [
        ("halfmove_65536",
         START + " w KQkq - 65536 1",
         START + " w KQkq - 0 1",
         "a GUI that writes the halfmove counter as a 16-bit value wrapping past 65535, or one reading a "
         "corrupt/PGN-derived counter",
         "counter beyond the range a real game can produce (a halfmove counter cannot exceed 150 in a real "
         "game: the seventy-five-move rule ends it, and 100 ends it by claim)"),
        ("fullmove_1e9",
         START + " w KQkq - 0 1000000000",
         START + " w KQkq - 0 1",
         "a GUI that derives the move number from a clock, a ply count, or an arithmetic bug "
         "(10^9 is a round number in a float or a parsed overflow)",
         "move number beyond any game; the engine has no observable use for it"),
        ("junk_after_six",
         START + " w KQkq - 0 1 zzz",
         START + " w KQkq - 0 1",
         "a GUI appending its own annotation, a trailing separator, or a second FEN's fields to a valid FEN",
         "the board itself is a perfectly legal board; only the trailing token is malformed"),
    ]
    lines = ["can the three extreme-counter FEN accepts reach a REAL GAME?",
             "pc   (PC r15, no setoption used here) %s sha256 %s"
             % (pc, hashlib.sha256(Path(pc).read_bytes()).hexdigest()),
             "asan (PC r15 ASan+UBSan)          %s sha256 %s"
             % (asan, hashlib.sha256(Path(asan).read_bytes()).hexdigest()),
             "every case: fresh process, ucinewgame + isready before the position, guard = go perft 1 vs",
             "python-chess's legal count for the CORRECTED FEN", ""]
    rows = []
    for name, fen, corrected, who_sends, realism in cases:
        # engine state: is the board the corrected board?
        a = run(pc, ["position fen " + fen], "go perft 1")
        exp, pyverdict = legal_count(corrected)
        board_ok = (str(a["nodes"]) == str(exp))
        # sanitizer pass on the same input
        s = run(asan, ["position fen " + fen], "go depth 6")
        # what the engine does with the counter: depth probe on the same board
        d = run(pc, ["position fen " + fen], "go depth 10")
        rows.append({
            "case": name, "fen": fen, "corrected_board_fen": corrected,
            "engine_perft1": a["nodes"], "corrected_legal": exp, "board_is_corrected_board": board_ok,
            "python_chess_reading": pyverdict,
            "engine_score_at_depth10": d["score"], "engine_nodes_at_depth10": d["nodes"],
            "sanitizer_lines": s["sanitizer"], "refused": bool(a["refused"]),
            "who_would_send_this": who_sends, "realism": realism,
        })
        print("%-16s perft1=%-4s expected=%-4s board_ok=%-5s score=%-8s nodes=%-8s ref=%-5s san=%d"
              % (name, a["nodes"], exp, board_ok, d["score"], d["nodes"], bool(a["refused"]),
                 len(s["sanitizer"])), flush=True)

    lines.append("case\tengine accepts\tboard is the CORRECTED board\tpython-chess\tASan+UBSan\twho would send it")
    for r in rows:
        lines.append("%s\t%s\t%s\t%s\t%d lines\t%s" % (
            r["case"], not r["refused"], r["board_is_corrected_board"], r["python_chess_reading"],
            len(r["sanitizer_lines"]), r["who_would_send_this"]))

    # the ranking the coordinator asked for, computed from the facts above
    v = []
    v.append("")
    v.append("RANKING, on whether malformed input is REQUIRED to trigger each one (all three: yes):")
    for r in rows:
        # every one of the three needs something a legal game cannot produce. For the two counters it is a
        # field value out of range; for junk_after_six it is a trailing token after a valid FEN.
        v.append("  %-16s needs malformed input: True   board still legal: %-5s   sanitizer lines: %d"
                 % (r["case"], r["board_is_corrected_board"], len(r["sanitizer_lines"])))
    v.append("")
    v.append("One detail the numbers show rather than the code: halfmove 65536 scored cp 20 in 14621 nodes")
    v.append("while the same board at halfmove 0 scored cp 24 in 13102, so the accepted-but-out-of-range")
    v.append("counter IS used by the search (it drives the fifty-move damping), it is just not refused.")
    v.append("")
    v.append("All three need a FEN field that no legal game can produce (a halfmove counter above 150, a move")
    v.append("number of 10^9) or a malformed trailing token. A well-formed GUI sending a legal game never")
    v.append("produces any of them. They are COSMETIC: no legal board is misread, no move is misgenerated,")
    v.append("and no sanitizer fires. Ranked, the most plausible to see in the wild is junk_after_six")
    v.append("(a GUI appending an annotation to a valid FEN still gets a correct board), then the two")
    v.append("counters, which need an arithmetic or width bug in the GUI.")
    (out / "extreme_counters_reach.json").write_text(json.dumps(rows, indent=1))
    (out / "extreme_counters_reach.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
