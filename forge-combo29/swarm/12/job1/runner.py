#!/usr/bin/env python3
"""runner.py EXE SEQDIR RESULTFILE [TIMEOUT_S] — replay UCI sequences, one fresh process each.

The sequence file already ends with `isready` + `quit`, so the run is:
  spawn EXE, write every line except the final two, then send `isready` and wait for a
  `readyok` within TIMEOUT_S  -> no readyok in time is a HANG (process killed, counted);
  then send `quit` and wait TIMEOUT_S for the process to exit -> no exit is also a HANG.

Per sequence the record holds: exit code, crash (signal), hang, sanitizer lines, every
`bestmove` with the position that was in force at its `go`, and the illegal bestmoves.
A bestmove is associated with the oldest `go` that is expected to answer with one
(perft and `go` without a search limit do not); `0000` is legal only with no legal moves.
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
    r"ERROR: (AddressSanitizer|LeakSanitizer)|SUMMARY: (Address|Undefined|Leak)Sanitizer|"
    r"runtime error: "
)


def position_state(lines_so_far):
    """Board implied by the last `position` command the engine could accept.

    A refused FEN leaves the previous position in force (FABLE_TO_swarm_1 documents this),
    so an unparseable `position` keeps the last good board instead of clearing it; illegal
    moves truncate to the legal prefix, which is also what the engine keeps.
    """
    state = chess.Board().fen()      # the engine starts on startpos, so this is the default
    for raw in lines_so_far:
        line = raw.strip()
        if line == "ucinewgame":
            # measured: ucinewgame sets the board back to startpos (src/uci.cpp:254-257)
            state = chess.Board().fen()
            continue
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
                continue
            if rest.startswith("moves"):
                for mv in rest[len("moves"):].split():
                    try:
                        board.push_uci(mv)
                    except ValueError:
                        break
            state = board.fen()
        except Exception:
            continue          # refused FEN: previous position stays
    return state


def expects_bestmove(go_line):
    """Every `go` answers with a bestmove except `go perft` (measured: bare `go`, `go bananas`
    and `go depth 0` all answer within milliseconds; a `go infinite`/`ponder` answers at stop)."""
    return "perft" not in go_line.split()


def run_one(exe, seq_path, timeout_s):
    lines = seq_path.read_text().splitlines()
    if len(lines) < 2:
        lines += ["isready", "quit"]
    body, tail = lines[:-2], lines[-2:]

    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1,
                            env={"PATH": "/usr/bin:/bin", "ASAN_OPTIONS": "detect_leaks=0",
                                 "UBSAN_OPTIONS": "print_stacktrace=1"})
    out = queue.Queue()
    collected = []

    def reader():
        for ln in proc.stdout:
            out.put(ln.rstrip("\n"))
        out.put(None)
    threading.Thread(target=reader, daemon=True).start()

    def pump(deadline, stop_on):
        """Collect lines until `stop_on(line)` or deadline; returns matched line or None."""
        while True:
            remain = deadline - time.monotonic()
            if remain <= 0:
                return None
            try:
                ln = out.get(timeout=min(remain, 0.2))
            except queue.Empty:
                if proc.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            collected.append(ln)
            if stop_on(ln):
                return ln

    launched = []            # FIFO of fens: one entry per `go` the engine owes a bestmove for
    bestmoves = []
    unattributed = []
    sent = []
    t0 = time.monotonic()
    hang = False

    def drain(wait_s=0.0):
        """Collect buffered lines for at most wait_s; each bestmove settles the oldest go."""
        deadline = time.monotonic() + wait_s
        while True:
            try:
                ln = out.get(timeout=max(0.0, min(0.05, deadline - time.monotonic())))
            except queue.Empty:
                if time.monotonic() >= deadline:
                    return
                continue
            if ln is None:
                return
            collected.append(ln)
            if ln.startswith("bestmove"):
                if launched:
                    bestmoves.append((launched.pop(0), ln.strip()))
                else:
                    unattributed.append(ln.strip())

    try:
        for line in body:
            proc.stdin.write(line + "\n")
            proc.stdin.flush()
            sent.append(line)
            s = line.strip()
            if s.startswith("go") and expects_bestmove(s):
                launched.append(position_state(sent[:-1]))
            drain(0.02)            # pick up answers already produced, never block
        proc.stdin.write(tail[0] + "\n")       # the sequence's own isready
        proc.stdin.flush()
        sent.append(tail[0])
        if pump(time.monotonic() + timeout_s, lambda l: l.strip() == "readyok") is None:
            hang = True
        drain(0.2)
        proc.stdin.write(tail[1] + "\n")       # the sequence's own quit
        proc.stdin.flush()
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        pass

    try:
        rc = proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        hang = True
        proc.kill()
        rc = proc.wait()

    end = time.monotonic() + 2.0
    while time.monotonic() < end:
        try:
            ln = out.get(timeout=0.2)
        except queue.Empty:
            break
        if ln is None:
            break
        collected.append(ln)

    # leftovers after quit: the bestmove of a search that was still open arrives here
    for c in collected:
        if c.startswith("bestmove") and launched:
            bestmoves.append((launched.pop(0), c.strip()))

    wall = time.monotonic() - t0
    san = [c for c in collected if SAN_RE.search(c)]
    illegal, unchecked = [], []
    for fen, bm in bestmoves:
        parts = bm.split()
        word = parts[1] if len(parts) > 1 else "?"
        if fen is None:
            unchecked.append({"bestmove": word, "why": "position unparseable"})
            continue
        board = chess.Board(fen)
        if word in ("0000", "(none)"):
            if board.legal_moves:
                illegal.append({"fen": fen, "bestmove": word, "why": "0000 with legal moves"})
            continue
        try:
            mv = chess.Move.from_uci(word)
        except ValueError:
            illegal.append({"fen": fen, "bestmove": word, "why": "unparseable"})
            continue
        if mv not in board.legal_moves:
            illegal.append({"fen": fen, "bestmove": word, "why": "not legal in position"})

    return {
        "seq": seq_path.name,
        "exit": rc,
        "wall_s": round(wall, 3),
        "hang": hang,
        "crash": rc is not None and rc < 0,
        "sanitizer_lines": len(san),
        "sanitizer_excerpt": san[:8],
        "bestmoves": len(bestmoves),
        "unattributed_bestmoves": unattributed,
        "illegal_bestmoves": illegal,
        "unchecked_bestmoves": unchecked,
        "lines": len(lines),
        "transcript_tail": collected[-6:],
    }


def verify_illegal(exe, fen):
    """Ask a fresh process for a bestmove in FEN and report whether it is legal there."""
    script = f"position fen {fen}\nisready\ngo depth 1\nisready\nquit\n"
    p = subprocess.run([exe], input=script, capture_output=True, text=True, timeout=60,
                       env={"PATH": "/usr/bin:/bin", "ASAN_OPTIONS": "detect_leaks=0",
                            "UBSAN_OPTIONS": "print_stacktrace=1"})
    bms = [l.split()[1] for l in p.stdout.splitlines() if l.startswith("bestmove")]
    if not bms:
        return {"fen": fen, "bestmove": None, "verdict": "no bestmove"}
    word = bms[-1]
    board = chess.Board(fen)
    if word in ("0000", "(none)"):
        ok = not any(board.legal_moves)
    else:
        try:
            ok = chess.Move.from_uci(word) in board.legal_moves
        except ValueError:
            ok = False
    return {"fen": fen, "bestmove": word, "verdict": "legal in fresh process" if ok
            else "ILLEGAL in fresh process"}


def main():
    exe = sys.argv[1]
    seqdir = Path(sys.argv[2])
    result = Path(sys.argv[3])
    timeout_s = float(sys.argv[4]) if len(sys.argv) > 4 else 20.0
    seqs = sorted(seqdir.glob("seq_*.txt"))
    with result.open("w") as out:
        for i, sp in enumerate(seqs):
            rec = run_one(exe, sp, timeout_s)
            if rec["illegal_bestmoves"]:
                rec["recheck"] = [verify_illegal(exe, x["fen"]) for x in rec["illegal_bestmoves"]]
                rec["illegal_confirmed"] = sum(
                    1 for r in rec["recheck"] if r["verdict"] == "ILLEGAL in fresh process")
            else:
                rec["recheck"] = []
                rec["illegal_confirmed"] = 0
            out.write(json.dumps(rec) + "\n")
            out.flush()
            if rec["crash"] or rec["sanitizer_lines"] or rec["hang"] or rec["illegal_confirmed"]:
                print(f"[{i+1}/{len(seqs)}] {rec['seq']}: crash={rec['crash']} hang={rec['hang']} "
                      f"san={rec['sanitizer_lines']} illegal={rec['illegal_confirmed']}", flush=True)
    print(f"done {len(seqs)} sequences -> {result}")


if __name__ == "__main__":
    main()
