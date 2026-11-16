#!/usr/bin/env python3
"""swarm seat 01: re-run my base-tree FEN finds on the PC r15 build under PC20 (Threads 1).

For each find, the PC build is asked the same question my base-tree run asked, with a board guard so a
refused `position` line cannot masquerade as a result (S-F36).

Cases (all from my own FINDINGS):
  adjacent digits   "8/p4k1p/2R212/..." must still be ACCEPTED (the digit-summing rule; known, not a find)
  double check      "3k4/3P1q2/..." accepted at halfmove 0 (S-F2)
  junk after 6th    "… - 0 1 zzz" accepted, board unchanged (S-C1 / S11-F1)
  halfmove 65536    accepted, clamp cosmetic (S-F8)
  fullmove 1e9      accepted (S-F8)
  ep wrong rank     refused (job2)
  two white kings   refused (job2)
  pawn on rank 8    refused (job2)
  1000-ply moves    accepted, prefix rule (S-F9/S-F10)
  checkmated root   mate 0 (S-F32 / seat 21's door) under PC20

Settings: PC20 (S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true,
OwnBook false) plus Threads 1 and Hash 16, each setoption followed by isready read to readyok, ucinewgame
before every search.

Usage: pc_rerun_findings.py <pc-exe> <base-exe> <outdir> [plies-file]
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

TIMEOUT = 600.0

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
              ("Threads", "1"), ("Hash", "16")]


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


def run(exe, position_lines, options, go):
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
    if until("uciok", deadline) is None:
        problems.append("no uciok")
    for name, value in options:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        if until("readyok", deadline) is None:
            problems.append("no readyok after %s" % name)
            break
    for l in buf:
        if l.startswith("unknown option") or l.startswith("ERROR") or "invalid value" in l:
            problems.append(l)
    send("ucinewgame")
    send("isready")
    until("readyok", deadline)
    for line in position_lines:
        send(line)
    send("isready")
    if until("readyok", deadline) is None:
        problems.append("no readyok after position")
    refused = [l for l in buf if l.startswith("info string invalid FEN")]
    illegal = [l for l in buf if l.startswith("info string illegal move")]
    send(go)
    if go.startswith("go perft"):
        node_line = until("nodes ", deadline)
        bml = node_line
    else:
        bml = until("bestmove", deadline)
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=120)
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
    bm = None
    if bml and bml.startswith("bestmove"):
        parts = bml.split()
        bm = parts[1] if len(parts) > 1 else None
    return {"score": score, "nodes": nodes, "bestmove": bm, "refused": refused,
            "illegal": illegal, "problems": problems, "depths": len(dl)}


def expected_board(position_lines):
    """Return the board the lines should leave, or None when python-chess itself refuses the FEN.

    None means "python-chess cannot compute an expected board", which is exactly the case for the
    adjacent-digit FEN: the guard must then fall back to "the engine's own answer is the measurement"
    and say so, instead of crashing or silently passing.
    """
    b = chess.Board()
    for line in position_lines:
        parts = line.split()
        if not parts or parts[0] != "position":
            continue
        if parts[1] == "startpos":
            b = chess.Board()
            rest = parts[2:]
        else:
            try:
                b = chess.Board(" ".join(parts[2:8]))
            except ValueError:
                return None
            rest = parts[8:]
        if rest and rest[0] == "moves":
            for u in rest[1:]:
                mv = chess.Move.from_uci(u)
                if mv not in b.legal_moves:
                    break
                b.push(mv)
    return b


def main():
    pc, base, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    plies_file = sys.argv[4] if len(sys.argv) > 4 else None
    out.mkdir(parents=True, exist_ok=True)
    long_fen = "8" * 3000 + " w - - 0 1"
    cases = []

    def add(name, pos, go, question, expectation):
        cases.append({"name": name, "pos": pos, "go": go, "question": question,
                      "expectation": expectation})

    add("adjacent_digits", ["position fen 8/p4k1p/2R212/8/4rP2/1N2P3/P1p1K1PP/8 b - - 0 1"],
        "go perft 1", "is a rank with two adjacent digits still accepted?",
        "base: ACCEPTED (digit-sum rule). Does the PC build refuse it now?")
    add("double_check", ["position fen 3k4/3P1q2/5K2/8/8/5r2/7p/7R w - - 0 1"],
        "go perft 2", "is an impossible double-check position still accepted?",
        "base: ACCEPTED, perft 2 = 64. PC: same?")
    add("junk_after_six", ["position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 zzz"],
        "go perft 1", "are tokens after the sixth FEN field still ignored?",
        "base: ACCEPTED with the clean board. PC: same?")
    add("halfmove_65536", ["position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 65536 1"],
        "go perft 1", "is a halfmove counter above 65535 still accepted?", "base: ACCEPTED")
    add("fullmove_1e9", ["position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1000000000"],
        "go perft 1", "is a fullmove of 10^9 still accepted?", "base: ACCEPTED")
    add("ep_wrong_rank", ["position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 1"],
        "go perft 1", "is an impossible ep square still refused?", "base: REFUSED")
    add("two_white_kings", ["position fen 4k3/8/8/8/8/8/8/K3K3 w - - 0 1"], "go perft 1",
        "two white kings still refused?", "base: REFUSED")
    add("pawn_on_rank8", ["position fen 4P3/8/8/8/8/8/8/K6k w - - 0 1"], "go perft 1",
        "a white pawn on rank 8 still refused?", "base: REFUSED")
    add("three_thousand_chars", ["position fen " + long_fen], "go perft 1",
        "a 3,000-character field still refused without a crash?", "base: REFUSED")
    add("checkmated_root", ["position fen 4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60"], "go depth 8",
        "does a checkmated root still report mate 0 (seat 21's door)?", "base: mate 0, bestmove 0000")
    if plies_file and Path(plies_file).exists():
        plies = Path(plies_file).read_text().split()
        add("long_move_list", ["position startpos moves " + " ".join(plies)], "go perft 1",
            "is a 1,000-ply move list still applied correctly?", "base: accepted, perft 1 = 16")

    lines = ["my base-tree FEN finds re-run on the PC r15 build under PC20, Threads 1, Hash 16",
             "pc   %s sha256 %s" % (pc, hashlib.sha256(Path(pc).read_bytes()).hexdigest()),
             "base %s sha256 %s" % (base, hashlib.sha256(Path(base).read_bytes()).hexdigest()),
             "PC20: " + ", ".join("%s=%s" % kv for kv in PC20),
             "base runs: no setoption (the base build has no CuckooRep etc.)",
             "GUARD: every case's board is checked with `go perft 1` against python-chess before the answer",
             ""]
    lines.append("case\tquestion\tPC20 answer\tbase answer\tboard guard\treading")
    rows = []
    guard_fail = []
    for c in cases:
        a = run(pc, c["pos"], PC20, c["go"])
        b = run(base, c["pos"], [], c["go"])
        exp = expected_board(c["pos"])
        ga = run(pc, c["pos"], PC20, "go perft 1")
        gb = run(base, c["pos"], [], "go perft 1")
        if exp is None:
            # python-chess refuses this FEN too, so no expected board exists. The guard then only
            # requires the two builds to AGREE with each other, and the row says so.
            ok_a = ok_b = (ga["refused"] == gb["refused"] and str(ga["nodes"]) == str(gb["nodes"]))
            if not (ok_a and ok_b):
                guard_fail.append("%s: builds disagree (pc ref=%s nodes=%s, base ref=%s nodes=%s)"
                                  % (c["name"], bool(ga["refused"]), ga["nodes"],
                                     bool(gb["refused"]), gb["nodes"]))
        else:
            ok_a = (ga["refused"] and a["refused"]) or (str(ga["nodes"]) == str(exp.legal_moves.count()))
            ok_b = (gb["refused"] and b["refused"]) or (str(gb["nodes"]) == str(exp.legal_moves.count()))
            if not (ok_a and ok_b):
                guard_fail.append("%s: guard pc=%s base=%s expected=%d" %
                                  (c["name"], ga["nodes"], gb["nodes"], exp.legal_moves.count()))
        rows.append({"case": c["name"], "question": c["question"], "expectation": c["expectation"],
                     "pc": a, "base": b, "guard_pc": ok_a, "guard_base": ok_b})
        print("%-20s pc %-9s/%-8s ref=%-5s | base %-9s/%-8s ref=%-5s"
              % (c["name"], a["score"], a["nodes"], bool(a["refused"]),
                 b["score"], b["nodes"], bool(b["refused"])), flush=True)
        lines.append("%s\t%s\t%s\t%s\t%s\t%s" % (
            c["name"], c["question"],
            ("REFUSED: " + a["refused"][0][:60]) if a["refused"] else ("%s/%s/%s" % (a["score"], a["nodes"], a["bestmove"])),
            ("REFUSED: " + b["refused"][0][:60]) if b["refused"] else ("%s/%s/%s" % (b["score"], b["nodes"], b["bestmove"])),
            ("ok (expected board)" if (ok_a and ok_b and exp is not None)
             else "ok (builds agree; python-chess refuses this FEN too)" if (ok_a and ok_b)
             else "FAILED"), c["expectation"]))
    lines.append("")
    if guard_fail:
        lines.append("GUARD FAILURES:")
        lines.extend("  " + g for g in guard_fail)
    else:
        lines.append("GUARD: clean on every case (both builds on the intended board, or both refused).")
    (out / "pc_rerun_findings.json").write_text(json.dumps(rows, indent=1))
    (out / "pc_rerun_findings.txt").write_text("\n".join(lines) + "\n")
    print("")
    print("\n".join(lines[-2:]))


if __name__ == "__main__":
    main()
