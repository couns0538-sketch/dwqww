#!/usr/bin/env python3
"""abort_probe.py EXE [--pc20] — does an aborted search still publish a fabricated bestmove?

Seat 12's fault, and the reason file 5 ships FORGE_FIX_ABORT_PUBLISH and FORGE_FIX_ISREADY_PENDING.
Both `go` forms are tested on every build:

  bounded      `go depth 12` then `quit` at once         (the search is killed before depth 1)
  unbounded    `go infinite` then `quit` at once
  nodes        `go nodes 2000000` then `quit` at once
  stop-path    `go infinite`, `stop` immediately, then read the answer

For each: the bestmove, the number of `info depth` lines before it, the last node count, and
whether the move is legal in the position. A FABRICATED answer is one where no `info depth` line
was printed at all (the engine never reached depth 1) yet a bestmove came out. The move being
legal does not make it non-fabricated; the point is that no search produced it.

`--pc20` sends the 20 PC settings before the test, because the owner's PC always does.

Every case is a fresh process. Nothing here closes stdin mid-search except the `quit` case, which
IS the thing being measured — that is stated, not hidden.
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

SAN = re.compile(r"ERROR: (AddressSanitizer|LeakSanitizer)|SUMMARY: (Address|Undefined|Leak)Sanitizer|runtime error: ")

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

POS = "position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
BOARD = chess.Board(POS.split("fen ")[1])


def run(exe, script_tail, opts, timeout_s=60):
    """One fresh process; returns every output line and the exit code."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    out = []
    threading.Thread(target=lambda: ([q.put(l.rstrip("\n")) for l in p.stdout], q.put(None)),
                     daemon=True).start()
    try:
        p.stdin.write("uci\n")
        p.stdin.flush()
        # read uciok before anything else, so the option list is complete
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            ln = q.get(timeout=0.5)
            if ln is None:
                break
            out.append(ln)
            if ln == "uciok":
                break
        for name, value in opts:
            p.stdin.write(f"setoption name {name} value {value}\nisready\n")
            p.stdin.flush()
            while time.monotonic() < deadline:
                ln = q.get(timeout=0.5)
                if ln is None:
                    break
                out.append(ln)
                if ln == "readyok":
                    break
        p.stdin.write(script_tail)
        p.stdin.flush()
        while time.monotonic() < deadline:
            try:
                ln = q.get(timeout=0.2)
            except queue.Empty:
                if p.poll() is not None:
                    break
                continue
            if ln is None:
                break
            out.append(ln)
    except (BrokenPipeError, OSError):
        pass
    try:
        p.stdin.close()
    except OSError:
        pass
    try:
        rc = p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
        rc = p.wait()
    return out, rc


def analyse(lines):
    infos = [l for l in lines if l.startswith("info depth")]
    bms = [l for l in lines if l.startswith("bestmove")]
    bm = bms[-1].split()[1] if bms else None
    nodes = None
    if infos:
        m = re.search(r" nodes (\d+)", infos[-1])
        nodes = int(m.group(1)) if m else None
    legal = None
    if bm and bm not in ("0000", "(none)"):
        try:
            legal = chess.Move.from_uci(bm) in BOARD.legal_moves
        except ValueError:
            legal = False
    return {
        "bestmove": bm,
        "info_depth_lines": len(infos),
        "last_nodes": nodes,
        "bestmove_legal": legal,
        # fabricated = a move was published although the search never reached depth 1
        "fabricated": bool(bms) and len(infos) == 0,
        "sanitizer_lines": [l for l in lines if SAN.search(l)][:4],
    }


CASES = [
    ("bounded_quit", "position fen " + POS.split("fen ")[1] + "\nisready\ngo depth 12\nquit\n"),
    ("unbounded_quit", "position fen " + POS.split("fen ")[1] + "\nisready\ngo infinite\nquit\n"),
    ("nodes_quit", "position fen " + POS.split("fen ")[1] + "\nisready\ngo nodes 2000000\nquit\n"),
    ("stop_immediately", "position fen " + POS.split("fen ")[1] + "\nisready\ngo infinite\nstop\nisready\nquit\n"),
]


def main():
    exe = sys.argv[1]
    use_pc20 = "--pc20" in sys.argv
    opts = PC20 if use_pc20 else []
    label = "PC20" if use_pc20 else "none"
    print(f"exe {exe}")
    print(f"settings {label}")
    print(f"\n{'case':18} {'bestmove':9} {'info':>5} {'nodes':>8} {'legal':>6} {'FABRICATED':>11} san")
    rows = []
    for name, tail in CASES:
        lines, rc = run(exe, tail, opts)
        a = analyse(lines)
        a.update({"case": name, "exit": rc, "settings": label})
        rows.append(a)
        print(f"{name:18} {str(a['bestmove']):9} {a['info_depth_lines']:>5} "
              f"{str(a['last_nodes']):>8} {str(a['bestmove_legal']):>6} "
              f"{str(a['fabricated']):>11} {len(a['sanitizer_lines'])}")
    n_fab = sum(1 for r in rows if r["fabricated"])
    print(f"\nfabricated bestmoves: {n_fab}/{len(rows)}")
    out = {"exe": exe, "settings": label, "rows": rows, "fabricated": n_fab}
    Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + "\n") if len(sys.argv) > 2 else None
    return 0


if __name__ == "__main__":
    sys.exit(main())
