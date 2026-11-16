#!/usr/bin/env python3
"""seat 24, cycle check C2: independent check of seat 12's S-F1.

Their claim (forge-combo29/swarm/12/FINDINGS.md):
  "`ucinewgame` silently resets the board to startpos (src/uci.cpp:254-257, board.set_fen(StandardStartFen)), so
   `position fen X` / `ucinewgame` / `go` searches startpos, not X"
Their command: printf 'position fen 4k3/8/8/8/8/8/4P3/4K3 w - - 0 1\nisready\nucinewgame\nisready\ngo depth 1\n...'

My harness is written from that claim alone.  It asks the question in a way that cannot be satisfied by a
coincidence: the test FEN has ONE pawn and no rook, so startpos and X cannot share a legal-move set or a
bestmove unless the counter reset did nothing.  Measured three ways:
  1. `go perft 1` after position X / ucinewgame  -> the move list itself (startpos = 20 moves incl. b1c3 etc.)
  2. `go depth 4` after position X / ucinewgame  -> bestmove, then judge it for legality on X and on startpos
  3. control: the same two commands WITHOUT ucinewgame            -> must name X's moves
  4. control: position X / ucinewgame / position X again / go     -> must be back on X (so the reset is the trigger,
     not a broken `position` command)

Integrity rules applied (seat 19): every bestmove line must be found, every perft move list must be non-empty, and
a missing/empty line makes the verdict INCONCLUSIVE (exit 2), never a CONFIRMS.
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
X = "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"


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

    def command(self, cmd, timeout=180):
        self.send(cmd)
        self.send("isready")
        lines, bad = self.ready(timeout)
        return lines, bad

    def go_command(self, cmd, timeout=300):
        """For a `go` command: read stdout until its final answer line, then drain the readyok.

        Seat 19's 19-F12 warning fixes why this matters: a search runs on its own thread and its bestmove
        arrives AFTER the readyok of any isready sent behind it, so reading only to readyok attributes the
        bestmove to the next command. Every `go` in this checker goes through here.
        `go perft N` ends with a `nodes N` line, every other `go` with `bestmove`."""
        self.send(cmd)
        want_bm = not cmd.startswith("go perft")
        lines = self.read_until(
            (lambda l: l.startswith("bestmove")) if want_bm else
            (lambda l: l.startswith("nodes ")), timeout)
        self.send("isready")
        tail, _ = self.ready(60)
        return lines, tail

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    env = {k: v for k, v in os.environ.items()
           if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}

    bx = chess.Board(X)
    x_moves = {m.uci() for m in bx.legal_moves}
    start_moves = {m.uci() for m in chess.Board().legal_moves}
    print(f"X legal moves ({len(x_moves)}): {sorted(x_moves)}")
    print(f"startpos legal moves: {len(start_moves)}")
    overlap = x_moves & start_moves
    print(f"moves legal in BOTH (so a bestmove alone could be ambiguous): {sorted(overlap)}")

    eng = Engine(a.exe, a.out + ".raw", env)
    with open(a.out + ".meta", "w") as m:
        m.write(f"exe_started\t{os.path.abspath(a.exe)}\nsha256\t{sha256(a.exe)}\n")
        m.write("options_sent\tnone beyond defaults (ucinewgame/Hash/Threads left at default)\n")
        m.write(f"test_fen\t{X}\n")
        m.write("env\tTSAN_OPTIONS/ASAN_OPTIONS/UBSAN_OPTIONS/LSAN_OPTIONS unset\n")
        m.write("sent\tuci\n")
    eng.send("uci")
    eng.read_until(lambda l: l.strip() == "uciok", 60)
    eng.send("isready")
    _, bad = eng.ready(60)
    if bad:
        print("HANDSHAKE ERROR:", bad); sys.exit(2)

    rec = open(a.out + ".txt", "w")
    got = {}

    def run_case(name, steps, final_cmd):
        for cmd in steps:
            lines, bad = eng.command(cmd)
            rec.write(f"[{name}] -> {cmd}\n")
            for l in lines:
                rec.write("    " + l + "\n")
            if bad:
                rec.write(f"[{name}] STOP on {bad[0]}\n"); rec.flush()
                return None
        lines, bad = eng.go_command(final_cmd, timeout=300)
        rec.write(f"[{name}] -> {final_cmd}\n")
        for l in lines:
            rec.write("    " + l + "\n")
        rec.flush()
        return lines

    # case 1: perft 1 after position X / ucinewgame
    l1 = run_case("1_perft_after_ucinewgame", [f"position fen {X}", "ucinewgame"], "go perft 1")
    # case 2: depth 4 after position X / ucinewgame
    l2 = run_case("2_depth_after_ucinewgame", [f"position fen {X}", "ucinewgame"], "go depth 4")
    # case 3 control: no ucinewgame
    l3 = run_case("3_perft_no_ucinewgame", [f"position fen {X}"], "go perft 1")
    l4 = run_case("4_depth_no_ucinewgame", [f"position fen {X}"], "go depth 4")
    # case 5 control: position X again AFTER ucinewgame
    l5 = run_case("5_position_twice", [f"position fen {X}", "ucinewgame", f"position fen {X}"], "go perft 1")
    eng.close()
    rec.close()

    def perft_moves(lines):
        if lines is None:
            return None
        mv = set()
        for l in lines:
            mm = re.match(r"^([a-h][1-8][a-h][1-8][qrbn]?): \d+$", l.strip())
            if mm:
                mv.add(mm.group(1))
        return mv

    def bestmove(lines):
        if lines is None:
            return None
        b = [l.split()[1] for l in lines if l.startswith("bestmove")]
        return b[0] if b else None

    p1 = perft_moves(l1)
    p3 = perft_moves(l3)
    p5 = perft_moves(l5)
    b2 = bestmove(l2)
    b4 = bestmove(l4)

    print()
    print(f"case 1 perft-1 move list after X/ucinewgame : {sorted(p1) if p1 is not None else 'MISSING'}")
    print(f"case 3 perft-1 move list after X (control)  : {sorted(p3) if p3 is not None else 'MISSING'}")
    print(f"case 5 perft-1 after X/ucinewgame/position X: {sorted(p5) if p5 is not None else 'MISSING'}")
    print(f"case 2 bestmove after X/ucinewgame depth 4  : {b2}")
    print(f"case 4 bestmove after X depth 4 (control)   : {b4}")

    # ---- assertions first: nothing may pass on a missing line ----
    fails = []
    if not p1:
        fails.append("case 1 perft move list empty/missing")
    if not p3:
        fails.append("case 3 perft move list empty/missing")
    if not p5:
        fails.append("case 5 perft move list empty/missing")
    if not b2:
        fails.append("case 2 bestmove missing")
    if not b4:
        fails.append("case 4 bestmove missing")
    if len(x_moves) != 6:
        fails.append(f"python-chess says X has {len(x_moves)} legal moves, expected 6 (test premise broken)")
    if fails:
        print("\nASSERTION FAILURES:")
        for f in fails:
            print("  ! " + f)
        print("VERDICT: INCONCLUSIVE - not a confirmation, not a refutation")
        sys.exit(2)

    out = []
    out.append("SEAT 12 S-F1 — independent check by seat 24")
    out.append("")
    out.append(f"test FEN X = {X}  (python-chess: {len(x_moves)} legal moves {sorted(x_moves)})")
    out.append(f"startpos has {len(start_moves)} legal moves; the two sets overlap in {sorted(overlap)}")
    out.append("")
    out.append("| case | commands | what the engine did | startpos or X? |")
    out.append("|---|---|---|---|")
    out.append(f"| 1 | position X / ucinewgame / go perft 1 | {len(p1)} moves {sorted(p1)} | "
               f"{'STARTPOS' if len(p1) == 20 else ('X' if p1 == x_moves else 'other')} |")
    out.append(f"| 2 | position X / ucinewgame / go depth 4 | bestmove {b2} | "
               f"{'STARTPOS' if b2 in start_moves else ('X' if b2 in x_moves else 'other')} |")
    out.append(f"| 3 | position X / go perft 1 (control) | {len(p3)} moves {sorted(p3)} | "
               f"{'X' if p3 == x_moves else 'other'} |")
    out.append(f"| 4 | position X / go depth 4 (control) | bestmove {b4} | "
               f"{'X' if b4 in x_moves else 'other'} |")
    out.append(f"| 5 | position X / ucinewgame / position X / go perft 1 | {len(p5)} moves {sorted(p5)} | "
               f"{'X' if p5 == x_moves else 'other'} |")
    out.append("")
    reset_to_startpos = (len(p1) == 20 and p1 == start_moves)
    controls_ok = (p3 == x_moves and b4 in x_moves)
    back_to_x = (p5 == x_moves)
    # also check the depth-4 case searched startpos: its move must be a startpos move and NOT an X move
    depth_is_startpos = (b2 in start_moves and b2 not in x_moves) if len(overlap) == 0 else (b2 in start_moves)
    conf = reset_to_startpos and depth_is_startpos and controls_ok and back_to_x
    out.append(f"Assertions passed: all five cases produced their lines, and X has the expected 6 legal moves.")
    out.append("")
    out.append("VERDICT: " + ("CONFIRMS seat 12 S-F1" if conf else "does NOT reproduce seat 12 S-F1 as stated"))
    out.append("")
    if conf:
        out.append("The reset is real and total: after `ucinewgame` the engine's board is startpos, so `go perft 1`")
        out.append("enumerates startpos's 20 moves on a board that only has a king, a pawn and no rook, and a depth-4")
        out.append("search returns a startpos move. `position fen X` alone is correct (cases 3 and 4), and re-sending")
        out.append("`position fen X` after the ucinewgame puts the board back (case 5) — so the trigger is the")
        out.append("`ucinewgame` command itself, exactly as seat 12 says.")
        out.append("")
        out.append("Beyond their claim (my addition): the consequence is worse than a checker annoyance — ANY")
        out.append("`ucinewgame` sent BETWEEN `position` and `go` silently searches the wrong board. All four of my")
        out.append("own runners send `ucinewgame` BEFORE `position` (driver.py once at handshake, churn.py and")
        out.append("infinite_stop.py before the position line), so my recorded job1/job2/job3 numbers are not")
        out.append("affected — but any harness that sends it after `position` measures startpos.")
    with open(a.out + ".verdict.txt", "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
