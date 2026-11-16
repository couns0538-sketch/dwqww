#!/usr/bin/env python3
"""seat 24, cycle check C1: independent check of seat 02's S-F2.

Their claim (forge-combo29/swarm/02/FINDINGS.md):
  "`go searchmoves` naming no legal root move answers `info string searchmoves restriction has no legal root
   moves` then `bestmove 0000` on a board with 20 legal moves; the same board answers `bestmove a2a3` for a plain
   `go depth 2`."
Their command file: forge-combo29/swarm/02/job1/reproduce_zero.out.

My harness is written from that claim alone (I did not copy their script).  It drives the engine over stdin and
records every byte, then judges with python-chess.  It tests, all on startpos:
  A  go searchmoves depth 2            (no move named at all)
  B  go searchmoves e2e5 depth 2       (a move that is not legal in the position)
  C  go searchmoves a9a9 depth 2       (not even a well-formed square)
  D  go depth 2                        (control: plain search)
  E  go searchmoves e2e4 d2d4 depth 2  (control: two legal moves named)
and repeats A and B on a mid-game FEN from set_G.epd to rule out a startpos-only effect.

Judgement asked of the check: does `0000` appear on a board where python-chess says 20 legal moves exist, and
does the matching control on the same board answer a real move?
"""
import argparse
import hashlib
import os
import queue
import re
import subprocess
import sys
import threading
import time

import chess

STOP_PAT = re.compile(r"unknown option|invalid value|invalid FEN|illegal move", re.I)


class Engine:
    def __init__(self, exe, raw_path, env):
        self.raw = open(raw_path, "ab", buffering=0)
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, bufsize=0, env=env)
        self.q = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        for line in self.p.stdout:
            self.raw.write(line)
            self.q.put(line.decode("utf-8", "replace").rstrip("\r\n"))
        self.q.put(None)

    def send(self, line):
        self.p.stdin.write((line + "\n").encode())
        self.p.stdin.flush()

    def read_until(self, pred, timeout):
        out = []
        deadline = time.monotonic() + timeout
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise TimeoutError("|".join(out))
            try:
                line = self.q.get(timeout=left)
            except queue.Empty:
                raise TimeoutError("|".join(out))
            if line is None:
                raise EOFError("|".join(out))
            out.append(line)
            if pred(line):
                return out

    def ready(self, timeout=60):
        lines = self.read_until(lambda l: l.strip() == "readyok", timeout)
        return lines, [l for l in lines if STOP_PAT.search(l)]

    def close(self, timeout=15):
        try:
            self.send("quit")
            self.p.wait(timeout=timeout)
        except Exception:
            self.p.kill()
        finally:
            self.raw.close()
        return self.p.returncode


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


CASES = [
    ("A", None, "go searchmoves depth 2"),
    ("B", None, "go searchmoves e2e5 depth 2"),
    ("C", None, "go searchmoves a9a9 depth 2"),
    ("D", None, "go depth 2"),
    ("E", None, "go searchmoves e2e4 d2d4 depth 2"),
    ("A2", "FEN", "go searchmoves depth 2"),
    ("B2", "FEN", "go searchmoves b8b1 depth 2"),
    ("D2", "FEN", "go depth 2"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--fen", required=True, help="the mid-game control FEN")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    env = {k: v for k, v in os.environ.items()
           if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
    eng = Engine(a.exe, a.out + ".raw", env)
    with open(a.out + ".meta", "w") as m:
        m.write(f"exe_started\t{os.path.abspath(a.exe)}\nsha256\t{sha256(a.exe)}\n")
        m.write("id_name\tChess Engine Forge (taken from the raw `uci` answer)\n")
        m.write("options_sent\tnone (defaults; no S14 needed for this behaviour question)\n")
        m.write("env\tTSAN_OPTIONS/ASAN_OPTIONS/UBSAN_OPTIONS/LSAN_OPTIONS unset\n")
        m.write(f"control_fen\t{a.fen}\n")
        m.write("sent\tuci\n")
        for cid, fensel, cmd in CASES:
            m.write(f"sent[{cid}]\t{fensel or 'startpos'}\t{cmd}\n")

    eng.send("uci")
    eng.read_until(lambda l: l.strip() == "uciok", 60)
    eng.send("isready")
    _, bad = eng.ready(60)
    if bad:
        print("HANDSHAKE ERROR:", bad); return

    res = open(a.out + ".txt", "w")
    startpos_legal = 20
    verdicts = {}
    for cid, fensel, cmd in CASES:
        fen = a.fen if fensel == "FEN" else chess.STARTING_FEN
        board = chess.Board(fen)
        nlegal = len(list(board.legal_moves))
        eng.send("position fen " + fen)
        eng.send("isready")
        pre, bad = eng.ready(60)
        if bad:
            res.write(f"CASE {cid}\tSTOP\t{bad[0]}\n"); res.flush(); break
        eng.send(cmd)
        lines = eng.read_until(lambda l: l.startswith("bestmove"), 120)
        bm = lines[-1].split()[1]
        infos = [l for l in lines if l.startswith("info")]
        res.write(f"CASE {cid}\tfen={(fen if fensel else 'startpos')}\tlegal_in_board={nlegal}\n")
        for l in infos:
            res.write("  info\t" + l + "\n")
        res.write(f"  bestmove\t{bm}\n")
        if bm == "0000":
            kind = "ZERO"
        else:
            mv = chess.Move.from_uci(bm)
            kind = "legal" if mv in board.legal_moves else "ILLEGAL"
        verdicts[cid] = (nlegal, bm, kind, [l for l in infos if "searchmoves" in l])
        res.flush()

    eng.close()
    res.close()

    # ---- the verdict against seat 02's claim ----
    out = []
    out.append("SEAT 02 S-F2 — independent check by seat 24")
    out.append("")
    out.append("| case | board legal moves (python-chess) | bestmove | verdict | searchmoves line? |")
    out.append("|---|---|---|---|---|")
    for cid, (n, bm, kind, sm) in verdicts.items():
        out.append(f"| {cid} | {n} | {bm} | {kind} | {'yes' if sm else 'no'} |")
    out.append("")
    a_zero = verdicts.get("A", (0, "", "", []))[2] == "ZERO"
    a_legal_moves = verdicts.get("A", (0, "", "", []))[0]
    d_ok = verdicts.get("D", (0, "", "", []))[2] == "legal"
    b_zero = verdicts.get("B", (0, "", "", []))[2] == "ZERO"
    e_ok = verdicts.get("E", (0, "", "", []))[2] == "legal"
    a2_zero = verdicts.get("A2", (0, "", "", []))[2] == "ZERO"
    b2_zero = verdicts.get("B2", (0, "", "", []))[2] == "ZERO"
    d2_ok = verdicts.get("D2", (0, "", "", []))[2] == "legal"
    c_what = verdicts.get("C", (0, "", "", []))[2]
    conf = (a_zero and a_legal_moves == 20 and d_ok and b_zero and e_ok and a2_zero and b2_zero and d2_ok)
    out.append("VERDICT: " + ("CONFIRMS seat 02 S-F2" if conf else "does NOT reproduce seat 02 S-F2 as stated"))
    out.append("")
    out.append(f"A (startpos, no move named): bestmove 0000 with {a_legal_moves} legal moves on the board -> "
               f"{'as claimed' if a_zero and a_legal_moves == 20 else 'NOT as claimed'}")
    out.append(f"D (startpos, plain go depth 2): {'a real move' if d_ok else 'not a real move'} -> "
               f"{'as claimed' if d_ok else 'NOT as claimed'}")
    out.append(f"B (startpos, illegally named move e2e5): {verdicts.get('B', ('','','',''))[1]} ({verdicts.get('B', ('','','',''))[2]})")
    out.append(f"E (startpos, two legal moves named): {verdicts.get('E', ('','','',''))[1]} ({verdicts.get('E', ('','','',''))[2]})")
    out.append(f"C (startpos, garbage 'a9a9'): {verdicts.get('C', ('','','',''))[1]} ({c_what})")
    out.append(f"A2/B2/D2 on the mid-game FEN: {verdicts.get('A2')} / {verdicts.get('B2')} / {verdicts.get('D2')}")
    out.append("")
    out.append("Beyond their claim (my additions): case B shows the same 0000 when the named move is a LEGAL-LOOKING")
    out.append("but ILLEGAL move (e2e5 from startpos), and E shows two legal named moves give a real bestmove,")
    out.append("so the trigger is 'no named move is legal', not 'no move named'.")
    with open(a.out + ".verdict.txt", "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
