#!/usr/bin/env python3
"""quit_eof.py — does this build answer a FABRICATED `bestmove` when the input ends mid-search,
and if so: with what node count, and is that move legal?

This is a CHECK of seat 19's 19-F12 (a `C` line), not a finding of my own: they own the
plant/control. What I add beyond it is the two questions they did not answer:
  1. does the fabricated bestmove EVER come with a NONZERO node count?
  2. is the fabricated bestmove EVER ILLEGAL (or `0000` where moves exist)?

Cases, each in its OWN engine process, all timed with time.monotonic():
  A  control: `go depth D`, read stdout UNTIL bestmove, only then quit   -> the honest answer
  B  `go depth D` then `quit` immediately (same write, no read)          -> 19-F12
  C  `go depth D` then close stdin immediately (EOF, no quit)            -> 19-F12 via EOF
  D  `go depth D`, sleep 2 s, then `quit`                                -> a cut-short real search
  E  `go depth D`, sleep 200 ms, then `quit`                             -> mid-search cut
  F  `go infinite`, sleep 50 ms, then `quit`                             -> infinite cut
  G  `go nodes 100000`, `quit` immediately                               -> 19-F12 on a node limit
  H  `isready` during the search, then quit 2 s later                    -> control: isready is harmless

Case A is the one that matters for my own validity: it proves what the engine answers when
the harness behaves. Case B/C/G are the fault. Cases D/E/H prove a real search survives.

Every case records: every line read, the bestmove, the LAST node count in any `info` line,
the number of info lines, the wall time, the exit code, and whether the move is legal in
python-chess.

Usage: python3 quit_eof.py EXE OUTDIR POSITIONS [DEPTH]
"""
import json
import os
import queue
import subprocess
import sys
import threading
import time

import chess

ENGINE = None
OUT = None
DEPTH = 12


def drain(p, q, until=None, limit=60.0):
    got = []
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        try:
            ln = q.get(timeout=0.05)
        except queue.Empty:
            if p.poll() is not None and q.empty():
                break
            continue
        got.append(ln)
        if until and (ln == until or ln.startswith(until)):
            return got, True
    return got, False


def classify(tag, fen, commands, got, wall, rc, err, stdin_closed, mode):
    best = ""
    last_nodes = None
    infos = 0
    for ln in got:
        if ln.startswith("bestmove"):
            best = ln
        if ln.startswith("info "):
            infos += 1
            if " nodes " in ln:
                try:
                    last_nodes = int(ln.split(" nodes ")[1].split()[0])
                except Exception:
                    pass
    mv = best.split()[1] if len(best.split()) > 1 else ""
    legal = None
    note = ""
    try:
        board = chess.Board(fen)
        nlegal = board.legal_moves.count()
        if mv == "0000":
            legal = (nlegal == 0)
        elif mv:
            try:
                legal = chess.Move.from_uci(mv) in board.legal_moves
            except Exception:
                legal = False
        else:
            legal = None
            note = "no bestmove line at all"
    except Exception as e:
        legal = None
        note = "python-chess rejects the FEN: %s" % e
    # INTEGRITY GATE (seat 19's measurement-integrity warning). A missing number must never
    # pass as a measurement. These are recorded as explicit booleans, and check_quit.py
    # refuses to print any verdict built on a field whose flag is false.
    have_bestmove = bool(best)
    have_nodes = last_nodes is not None
    have_move = bool(mv)
    rec = {"case": tag, "mode": mode, "fen": fen, "commands": commands, "bestmove": best,
           "move": mv, "last_nodes": last_nodes, "info_lines": infos,
           "measured": {"bestmove_line_found": have_bestmove,
                        "node_count_found": have_nodes,
                        "move_field_found": have_move},
           "wall": round(wall, 3), "exit": rc, "legal": legal, "note": note,
           "stdin_closed_before_bestmove": stdin_closed,
           "fabricated": bool(best) and infos == 0,
           "all_lines": got, "stderr": err}
    with open(os.path.join(OUT, "%s.jsonl" % tag), "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def new_engine():
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l.rstrip("\r\n")) for l in p.stdout],
                     daemon=True).start()
    err = []
    threading.Thread(target=lambda: [err.append(l.rstrip()) for l in p.stderr],
                     daemon=True).start()
    return p, q, err


def send(p, text):
    try:
        p.stdin.write(text + "\n")
        p.stdin.flush()
        return True
    except (BrokenPipeError, ValueError):
        return False


def run_case(tag, fen, commands, mode="abort", sleep_before_quit=None,
             close_instead=False, isready_during=None):
    p, q, err = new_engine()
    t0 = time.monotonic()

    # Option/position setup is never pipelined: read readyok each time.
    for c in commands["setup"]:
        if not send(p, c):
            break
        if c.startswith(("setoption", "position", "isready", "ucinewgame")):
            drain(p, q, until="readyok", limit=20.0)
    got = []
    if mode == "control":
        send(p, commands["go"])
        got += drain(p, q, until="bestmove", limit=120.0)[0]
        wall = time.monotonic() - t0
        send(p, "quit")
        rc = p.wait(timeout=20)
        return classify(tag, fen, commands, got, wall, rc, err, False, "control")

    send(p, commands["go"])
    closed = False
    if isready_during is not None:
        time.sleep(isready_during)
        send(p, "isready")
        got += drain(p, q, until="readyok", limit=5.0)[0]
    if sleep_before_quit is not None:
        time.sleep(sleep_before_quit)
    if close_instead:
        try:
            p.stdin.close()
            closed = True
        except Exception:
            pass
    else:
        send(p, "quit")
    rest = drain(p, q, until="bestmove", limit=60.0)[0]
    got += rest
    wall = time.monotonic() - t0
    try:
        rc = p.wait(timeout=20)
    except Exception:
        p.kill()
        rc = "killed"
    return classify(tag, fen, commands, got, wall, rc, err, closed, "abort")


def main():
    global ENGINE, OUT, DEPTH
    ENGINE = sys.argv[1]
    OUT = sys.argv[2]
    posfile = sys.argv[3]
    if len(sys.argv) > 4:
        DEPTH = int(sys.argv[4])
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".jsonl"):
            os.remove(os.path.join(OUT, f))
    fens = [l.strip().split(";")[0].strip() for l in open(posfile) if l.strip()]

    for fen in fens:
        setup = ["uci", "isready"]
        setup += OPTS
        setup += ["ucinewgame", "isready", "position fen " + fen]
        d = DEPTH
        run_case("A_control", fen, {"setup": setup, "go": "go depth %d" % d}, mode="control")
        run_case("B_quit_now", fen, {"setup": setup, "go": "go depth %d" % d})
        run_case("C_eof_now", fen, {"setup": setup, "go": "go depth %d" % d}, close_instead=True)
        run_case("D_quit_2s", fen, {"setup": setup, "go": "go depth %d" % d}, sleep_before_quit=2.0)
        run_case("E_quit_200ms", fen, {"setup": setup, "go": "go depth %d" % d}, sleep_before_quit=0.2)
        run_case("F_infinite_quit", fen, {"setup": setup, "go": "go infinite"}, sleep_before_quit=0.05)
        run_case("G_nodes_quit", fen, {"setup": setup, "go": "go nodes 100000"})
        run_case("H_isready_then_quit", fen, {"setup": setup, "go": "go depth %d" % d},
                 isready_during=0.3, sleep_before_quit=2.0)
        print(".", end="", flush=True)
    print("\ncases written to %s" % OUT)


if __name__ == "__main__":
    main()
