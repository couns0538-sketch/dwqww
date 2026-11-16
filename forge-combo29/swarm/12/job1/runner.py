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


def is_unbounded(go_line):
    """Searches that only a later stop/ponderhit/quit ends.

    Measured on this engine: `go infinite`, `go ponder ...` and a bare `go` (with no limit at
    all) all keep searching — after a bare `go` the bestmove arrives only when a later command
    stops it. Every other `go` (depth, nodes, movetime, clocks, mate, searchmoves) answers on
    its own within the 20 s the job allows.
    """
    words = go_line.split()
    if "infinite" in words or "ponder" in words:
        return True
    limits = {"depth", "nodes", "softnodes", "movetime", "movestogo", "wtime", "btime",
              "winc", "binc", "mate", "searchmoves"}
    return not any(w in limits for w in words[1:])


def expects_bestmove(go_line):
    """Every `go` answers with a bestmove except `go perft`."""
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

    bestmoves = []
    unattributed = []
    sent = []
    t0 = time.monotonic()
    hang = False
    open_search = None       # fen of a search the engine still owes a bestmove for
    last_output_at = [time.monotonic()]

    def settle(quiet_s=0.08):
        """Read until the engine has been silent for quiet_s, attributing every bestmove.

        Called before sending a new `go`, so a bestmove the engine still owed from an earlier
        (interrupted or unbounded) search is consumed first and can never be mistaken for the
        answer of the search about to start. Attribution is by the search that was open.
        """
        nonlocal open_search
        while True:
            try:
                ln = out.get(timeout=quiet_s)
            except queue.Empty:
                if time.monotonic() - last_output_at[0] >= quiet_s:
                    return
                continue
            if ln is None:
                return
            last_output_at[0] = time.monotonic()
            collected.append(ln)
            if ln.startswith("bestmove"):
                if open_search is not None:
                    bestmoves.append((open_search, ln.strip()))
                    open_search = None
                else:
                    unattributed.append(ln.strip())

    def read_until_bestmove(bound_s):
        """Block until a bestmove arrives (or the process ends); return (line, fen_or_None)."""
        nonlocal open_search
        deadline = time.monotonic() + bound_s
        while time.monotonic() < deadline:
            try:
                ln = out.get(timeout=0.2)
            except queue.Empty:
                if proc.poll() is not None:
                    return None, None
                continue
            if ln is None:
                return None, None
            last_output_at[0] = time.monotonic()
            collected.append(ln)
            if ln.startswith("bestmove"):
                fen = open_search
                open_search = None
                return ln, fen
        return "TIMEOUT", None

    try:
        for line in body:
            s = line.strip()
            words = s.split()
            if s.startswith("go") and expects_bestmove(s):
                settle()                       # nothing stale may survive into this search
                proc.stdin.write(line + "\n")
                proc.stdin.flush()
                sent.append(line)
                fen = position_state(sent[:-1])
                open_search = fen
                if is_unbounded(s):
                    continue                   # answered later; settle() picks it up
                ln, got = read_until_bestmove(timeout_s)
                if ln is None:
                    hang = True
                    break
                if ln == "TIMEOUT":
                    hang = True                # a bounded search that never answers
                    break
                bestmoves.append((got or fen, ln.strip()))
            else:
                proc.stdin.write(line + "\n")
                proc.stdin.flush()
                sent.append(line)
                if open_search is not None and (s in ("stop", "ponderhit", "ucinewgame")
                                                or s.startswith("position")
                                                or s.startswith("setoption")):
                    # the engine's stop_search() joins its worker, so the owed bestmove is
                    # already written; take it now rather than after the next command
                    ln, got = read_until_bestmove(5.0)
                    if ln not in (None, "TIMEOUT"):
                        bestmoves.append((got or open_search, ln.strip()))
                        open_search = None
                    elif ln is None:
                        open_search = None
                # collect whatever else arrived without blocking
                while True:
                    try:
                        ln = out.get_nowait()
                    except queue.Empty:
                        break
                    if ln is None:
                        break
                    collected.append(ln)
                    if ln.startswith("bestmove"):
                        unattributed.append(ln.strip())   # no search was open for it

        if not hang:
            proc.stdin.write(tail[0] + "\n")       # the sequence's own isready
            proc.stdin.flush()
            sent.append(tail[0])
            if pump(time.monotonic() + timeout_s, lambda l: l.strip() == "readyok") is None:
                hang = True
            while True:
                try:
                    ln = out.get_nowait()
                except queue.Empty:
                    break
                if ln is None:
                    break
                collected.append(ln)
                if ln.startswith("bestmove") and open_search is not None:
                    bestmoves.append((open_search, ln.strip()))
                    open_search = None
                elif ln.startswith("bestmove"):
                    unattributed.append(ln.strip())
        if not hang:
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
        if ln.startswith("bestmove") and open_search is not None:
            bestmoves.append((open_search, ln.strip()))
            open_search = None

    wall = time.monotonic() - t0
    san = [c for c in collected if SAN_RE.search(c)]
    # A zero sanitizer count only counts if a search demonstrably ran: record the deepest
    # depth and the largest node count any `info depth` line reported.
    max_depth_seen, max_nodes_seen, info_depth_lines = 0, 0, 0
    for c in collected:
        if not c.startswith("info depth"):
            continue
        info_depth_lines += 1
        md = re.search(r"^info depth (\d+)", c)
        mn = re.search(r" nodes (\d+)", c)
        if md:
            max_depth_seen = max(max_depth_seen, int(md.group(1)))
        if mn:
            max_nodes_seen = max(max_nodes_seen, int(mn.group(1)))
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
        "max_depth_seen": max_depth_seen,
        "max_nodes_seen": max_nodes_seen,
        "info_depth_lines": info_depth_lines,
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
