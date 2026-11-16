#!/usr/bin/env python3
"""setoption_aborts.py EXE OUTFILE — does `setoption` during a search stop the search?

The source says yes (`src/uci.cpp`: the `setoption` branch calls `stop_search()`), but the UCI
protocol allows a GUI to change an option without ending the search, and a GUI that does so will
believe its search is still running. This measures it with a control that must NOT stop
(`isready`) beside it, so a "stopped" verdict cannot be produced by the harness itself.

Per probe: start `go infinite`, wait 50 ms (the search is definitely producing depth lines), send
ONE command, then watch stdout for 1.5 s WITHOUT sending anything else. If a `bestmove` arrives in
that window, that command ended the search.

Controls:
  isready   must NOT stop the search (UCI requires isready to be answerable during a search)
  stop      MUST stop it — the positive control that the window can see a stop at all
"""
import json
import queue
import sys
import threading
import time
from pathlib import Path

POS = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"

COMMANDS = [
    ("isready", "CONTROL: must NOT stop"),
    ("stop", "CONTROL: must stop"),
    ("setoption name Hash value 64", "option change"),
    ("setoption name MultiPV value 3", "option change"),
    ("setoption name LmrQuietBase value 100", "option change (a plain tune knob)"),
    ("setoption name OwnBook value false", "option change"),
    ("ucinewgame", "new game"),
    ("position fen " + POS, "position reset"),
    ("go depth 4", "second go"),
]


def probe(exe, cmd, window=1.5):
    import subprocess
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1,
                         env={"PATH": "/usr/bin:/bin", "ASAN_OPTIONS": "detect_leaks=0"})
    q = queue.Queue()

    def rd():
        for l in p.stdout:
            q.put((time.monotonic(), l.rstrip()))
        q.put((time.monotonic(), None))
    threading.Thread(target=rd, daemon=True).start()
    p.stdin.write(f"uci\nsetoption name OwnBook value false\nposition fen {POS}\nisready\n"
                  f"go infinite\n")
    p.stdin.flush()
    time.sleep(0.05)
    t_mid = time.monotonic()
    p.stdin.write(cmd + "\n")
    p.stdin.flush()
    bestmoves, readyok = [], 0
    end = time.monotonic() + window
    while time.monotonic() < end:
        try:
            t, l = q.get(timeout=0.1)
        except queue.Empty:
            continue
        if l is None:
            break
        if l.startswith("bestmove"):
            bestmoves.append((round(t - t_mid, 3), l))
        if l == "readyok":
            readyok += 1
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.stdin.close()
    except OSError:
        pass
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return {"command": cmd, "stopped_therefore": bool(bestmoves),
            "bestmoves": [b[1] for b in bestmoves],
            "first_after_s": bestmoves[0][0] if bestmoves else None,
            "readyok_in_window": readyok}


def main():
    exe, outfile = sys.argv[1], sys.argv[2]
    print(f"exe {exe}")
    print(f"Threads 1 (no Threads option sent). Window 1.5 s, nothing sent while watching.\n")
    print(f"{'command':40} {'bestmove in window':18} {'verdict'}")
    rows = []
    for cmd, why in COMMANDS:
        r = probe(exe, cmd)
        r["why"] = why
        verdict = "STOPS THE SEARCH" if r["stopped_therefore"] else "search continues"
        rows.append(r)
        print(f"{cmd[:40]:40} {str(r['bestmoves']):18} {verdict}   ({why})")
    out = {"exe": exe, "rows": rows}
    Path(outfile).write_text(json.dumps(out, indent=1) + "\n")

    ctl_ready = next(r for r in rows if r["command"] == "isready")
    ctl_stop = next(r for r in rows if r["command"] == "stop")
    sets = [r for r in rows if r["command"].startswith("setoption")]
    print(f"\ncontrols: isready stopped it? {ctl_ready['stopped_therefore']} (must be False); "
          f"stop stopped it? {ctl_stop['stopped_therefore']} (must be True)")
    print(f"setoption commands that stopped the search: "
          f"{sum(1 for r in sets if r['stopped_therefore'])}/{len(sets)}")
    print(f"raw -> {outfile}")


if __name__ == "__main__":
    main()
