#!/usr/bin/env python3
"""S02 check of seat 16's S-F6: the built-in book is probed ONLY on a game search (`go wtime/btime`,
`go movetime`), never on `go depth`, `go nodes` or `go infinite` — so the book cannot influence an analysis.

Their claim, read from their FINDINGS line: "src/uci.cpp:524-528 probes it only when `game_search` holds, i.e.
only for `go wtime/btime` or `go movetime` (not `go depth`, `go nodes` or `go infinite`); 3 opening positions at
depth 10 give no book line and 30 G positions give identical depth-10 bestmove and score with OwnBook true vs
false".

My check tests the MECHANISM directly rather than their counts: for one OPENING position (where a book hit is
most likely), send each `go` form twice — with OwnBook true and false — and record whether a
`info string book move` line appears and whether the bestmove differs. If the book only fires on game searches,
the book line appears for `go wtime`/`go movetime` and NOT for `go depth`/`go nodes`/`go infinite`.

Each search is the first of a fresh process (COLD, per seat 10's rule) and is driven INTERACTIVELY (per 19-F12:
piping and closing stdin makes this build invent a bestmove). A `go infinite` is stopped by the driver.

usage: check_book_gate.py <exe> <outdir>
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/base/forge-combo29/build/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out"
OPENING = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
FORMS = [
    ("go depth 8", False),
    ("go nodes 20000", False),
    ("go infinite", True),
    ("go wtime 5000 btime 5000", False),
    ("go movetime 300", False),
]


def run(fen, go, ownbook, stop_it):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    L = []
    threading.Thread(target=lambda: [L.append(l.rstrip("\n")) for l in p.stdout], daemon=True).start()

    def say(t):
        p.stdin.write(t + "\n")
        p.stdin.flush()

    def wait(pref, n0=0, to=90):
        dl = time.time() + to
        while time.time() < dl:
            if any(l.startswith(pref) for l in L[n0:]):
                return True
            time.sleep(0.002)
        return False

    say("uci")
    wait("uciok")
    say("isready")
    wait("readyok")
    say("setoption name OwnBook value %s" % ("true" if ownbook else "false"))
    say("isready")
    n = len(L)
    wait("readyok", n)
    say("position fen " + fen)
    say("isready")
    n = len(L)
    wait("readyok", n)
    n2 = len(L)
    say(go)
    if stop_it:
        time.sleep(0.25)
        say("stop")
    got = wait("bestmove", n2, 90)
    say("quit")
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    if not got:
        sys.exit("FAIL: no bestmove for %r (OwnBook=%s); refusing to record" % (go, ownbook))
    seg = L[n2:]
    book = [l for l in seg if "book move" in l]
    bm = [l for l in seg if l.startswith("bestmove")]
    info = [l for l in seg if l.startswith("info depth")]
    return {"go": go, "ownbook": ownbook, "book_lines": book,
            "bestmove": bm[-1].split()[1] if bm else None,
            "info_depth_lines": len(info), "out": seg}


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("| go form | OwnBook | book line? | bestmove | info depth lines |")
    print("|---|---|---|---|---|")
    for go, stop_it in FORMS:
        for ownbook in (True, False):
            r = run(OPENING, go, ownbook, stop_it)
            r.pop("out")
            rows.append(r)
            print("| `%s` | %s | %s | %s | %d |"
                  % (go, "true" if ownbook else "false",
                     "YES: " + r["book_lines"][0] if r["book_lines"] else "no",
                     r["bestmove"], r["info_depth_lines"]))
    json.dump(rows, open(os.path.join(OUT, "rows.json"), "w"), indent=1)
    json.dump({"exe": EXE,
               "sha256": subprocess.run(["sha256sum", EXE], capture_output=True,
                                        text=True).stdout.split()[0],
               "position": OPENING, "position_why": "startpos, where a book hit is most likely",
               "option_lines_sent": ["setoption name OwnBook value true|false"],
               "driver": "interactive, one search per fresh process (COLD); go infinite stopped by the driver",
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)

    def book_on(go):
        return any(r["book_lines"] for r in rows if r["go"] == go and r["ownbook"] is True)

    def same_either_way(go):
        on = [r for r in rows if r["go"] == go and r["ownbook"] is True][0]
        off = [r for r in rows if r["go"] == go and r["ownbook"] is False][0]
        return on["bestmove"] == off["bestmove"]

    checks = {
        "a book line DOES appear for `go movetime` with OwnBook true": book_on("go movetime 300"),
        "a book line DOES appear for `go wtime` with OwnBook true": book_on("go wtime 5000 btime 5000"),
        "NO book line for `go depth 8` with OwnBook true": not book_on("go depth 8"),
        "NO book line for `go nodes 20000` with OwnBook true": not book_on("go nodes 20000"),
        "NO book line for `go infinite` with OwnBook true": not book_on("go infinite"),
        "`go depth 8` gives the same bestmove with OwnBook on and off": same_either_way("go depth 8"),
    }
    print()
    print("### verdict checks")
    for k, v in checks.items():
        print("- %-64s %s" % (k, "PASS" if v else "FAIL"))
    json.dump(checks, open(os.path.join(OUT, "checks.json"), "w"), indent=1)
    if not all(checks.values()):
        sys.exit("CONCLUSION: REFUTES S-F6 on: %s" % "; ".join(k for k, v in checks.items() if not v))
    print()
    print("CONCLUSION: CONFIRMS S-F6 — the book is consulted only for game searches, never for "
          "`go depth`/`nodes`/`infinite`, so it cannot influence an analysis search.")


if __name__ == "__main__":
    main()
