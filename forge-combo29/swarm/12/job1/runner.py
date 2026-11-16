#!/usr/bin/env python3
"""runner.py EXE SEQDIR RESULTFILE [TIMEOUT_S] — replay UCI sequences, one fresh process each.

For every seq_NNNN.txt: spawn EXE, write the file's lines on stdin, read stdout until EOF
(the sequence itself ends with `quit`) or until TIMEOUT_S passes with no new output.

Recorded per sequence (one JSON line in RESULTFILE):
  seq, exit, wall_s, hang (no complete answer within TIMEOUT_S of the last write),
  crash (negative return code / killed by signal), sanitizer_lines (count + the lines),
  bestmoves (list of (position_key, bestmove)), illegal_bestmoves.

A "bestmove" is checked against the position in force when `go` was sent: the last
`position` command before that `go`, with its legal move prefix applied; an unparseable
position means the check is skipped and the bestmove is marked checked=false.
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import chess

SAN_RE = re.compile(
    r"(ERROR: AddressSanitizer|ERROR: LeakSanitizer|runtime error:|SUMMARY: (Address|Undefined|Leak)")
)


def position_state(lines_so_far):
    """Return the board implied by the last `position` command, or None."""
    state = None
    for raw in lines_so_far:
        line = raw.strip()
        if not line.startswith("position"):
            continue
        try:
            if line.startswith("position startpos"):
                board = chess.Board()
                rest = line[len("position startpos"):].strip()
            elif line.startswith("position fen "):
                rest_fen = line[len("position fen "):]
                m = re.search(r"\s+moves\s+(.*)$", rest_fen)
                fen = rest_fen[: m.start()].strip() if m else rest_fen.strip()
                board = chess.Board(fen)
                rest = ("moves " + m.group(1)) if m else ""
            else:
                state = None
                continue
            if rest.startswith("moves"):
                for mv in rest[len("moves"):].split():
                    try:
                        board.push_uci(mv)
                    except ValueError:
                        break          # engine keeps the legal prefix
            state = board.fen()
        except Exception:
            state = None
    return state


def run_one(exe, seq_path, timeout_s):
    lines = seq_path.read_text().splitlines()
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1,
                            env={"PATH": "/usr/bin:/bin", "ASAN_OPTIONS": "detect_leaks=0",
                                 "UBSAN_OPTIONS": "print_stacktrace=1"})
    q = queue.Queue()
    collected = []

    def reader():
        for ln in proc.stdout:
            q.put(ln)
        q.put(None)
    threading.Thread(target=reader, daemon=True).start()

    t0 = time.monotonic()
    sent_prefix = []
    bestmoves = []
    hang = False
    try:
        for line in lines:
            prefix_now = list(sent_prefix)
            proc.stdin.write(line + "\n")
            proc.stdin.flush()
            sent_prefix.append(line)
            deadline = time.monotonic() + timeout_s
            if line.strip().startswith("go"):
                # consume output until bestmove or timeout
                while True:
                    remain = deadline - time.monotonic()
                    if remain <= 0:
                        hang = True
                        break
                    try:
                        ln = q.get(timeout=min(remain, 0.5))
                    except queue.Empty:
                        if proc.poll() is not None:
                            break
                        continue
                    if ln is None:
                        break
                    collected.append(ln.rstrip("\n"))
                    if ln.startswith("bestmove"):
                        bestmoves.append((position_state(prefix_now), ln.strip()))
                        break
                if hang:
                    break
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        pass

    try:
        rc = proc.wait(timeout=max(1.0, timeout_s - (time.monotonic() - t0)))
    except subprocess.TimeoutExpired:
        hang = True
        proc.kill()
        rc = proc.wait()

    # drain whatever is left
    end = time.monotonic() + 2.0
    while time.monotonic() < end:
        try:
            ln = q.get(timeout=0.2)
        except queue.Empty:
            break
        if ln is None:
            break
        collected.append(ln.rstrip("\n"))

    wall = time.monotonic() - t0
    san = [c for c in collected if SAN_RE.search(c)]
    illegal = []
    for fen, bm in bestmoves:
        word = bm.split()[1] if len(bm.split()) > 1 else "?"
        if fen is None:
            illegal.append({"fen": None, "bestmove": word, "checked": False})
            continue
        if word in ("0000", "(none)"):
            board = chess.Board(fen)
            if board.legal_moves:              # 0000 with moves available is a fault
                illegal.append({"fen": fen, "bestmove": word, "checked": True,
                                "why": "0000 with legal moves"})
            continue
        try:
            mv = chess.Move.from_uci(word)
            if mv not in chess.Board(fen).legal_moves:
                illegal.append({"fen": fen, "bestmove": word, "checked": True,
                                "why": "not legal in position"})
        except ValueError:
            illegal.append({"fen": fen, "bestmove": word, "checked": True, "why": "unparseable"})

    return {
        "seq": seq_path.name,
        "exit": rc,
        "wall_s": round(wall, 3),
        "hang": hang,
        "crash": rc is not None and rc < 0,
        "sanitizer_lines": len(san),
        "sanitizer_excerpt": san[:6],
        "bestmoves": [{"fen": f, "bm": b} for f, b in bestmoves],
        "illegal_bestmoves": [i for i in illegal if i.get("checked")],
        "unchecked_bestmoves": [i for i in illegal if not i.get("checked")],
    }


def main():
    exe = sys.argv[1]
    seqdir = Path(sys.argv[2])
    result = Path(sys.argv[3])
    timeout_s = float(sys.argv[4]) if len(sys.argv) > 4 else 20.0
    seqs = sorted(seqdir.glob("seq_*.txt"))
    with result.open("w") as out:
        for i, sp in enumerate(seqs):
            rec = run_one(exe, sp, timeout_s)
            out.write(json.dumps(rec) + "\n")
            out.flush()
            if rec["crash"] or rec["sanitizer_lines"] or rec["hang"]:
                print(f"[{i+1}/{len(seqs)}] {rec['seq']}: crash={rec['crash']} "
                      f"hang={rec['hang']} san={rec['sanitizer_lines']}", flush=True)
    print(f"done {len(seqs)} sequences -> {result}")


if __name__ == "__main__":
    main()
