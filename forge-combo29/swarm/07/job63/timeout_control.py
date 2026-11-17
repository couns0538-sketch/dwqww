#!/usr/bin/env python3
"""timeout_control.py -- is this seat's reader-deadline sound on a FAST case?

08-N2's remedy: prove a timeout against a case known to return quickly. If the fast case returns
without the deadline tripping, the timeout logic is not firing spuriously.

Uses the SAME LineReader class this seat's harnesses use (imported from job1/uci_drive.py), so the
instrument under test is the real one. Three cases:
  FAST  : `go nodes 1` -- returns in ~1 ms; a 5 s deadline must NOT trip and must return a bestmove.
  SLOW  : `go depth 20` -- returns in a few seconds; a 5 s deadline must still return a bestmove.
  TRIP  : `go infinite` with a 0.3 s deadline -- the deadline MUST trip (None), proving the timeout
          can fire at all. Without this third case, a "no trip" result proves nothing.
"""
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from uci_drive import LineReader   # the real instrument

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

def run(exe, go, deadline_s):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    r = LineReader(p.stdout)
    def send(c):
        p.stdin.write(c + "\n"); p.stdin.flush()
    send("uci")
    t_end = time.monotonic() + 30
    while True:
        l = r.readline(t_end)
        if l is None or l.strip() == "uciok":
            break
    for o in ["Hash value 16", "Threads value 1", "OwnBook value false"]:
        send("setoption name " + o); send("isready")
        while True:
            l = r.readline(time.monotonic() + 30)
            if l is None or l.strip() == "readyok":
                break
    send("ucinewgame"); send("isready")
    while True:
        l = r.readline(time.monotonic() + 30)
        if l is None or l.strip() == "readyok":
            break
    send("position fen " + FEN); send("isready")
    while True:
        l = r.readline(time.monotonic() + 30)
        if l is None or l.strip() == "readyok":
            break
    t0 = time.monotonic()
    send(go)
    best = None
    deadline = t0 + deadline_s
    while True:
        l = r.readline(deadline)
        if l is None:
            break
        if l.startswith("bestmove"):
            best = l.split()[1]; break
    elapsed = (time.monotonic() - t0) * 1000.0
    try:
        p.stdin.write("stop\n"); p.stdin.flush()
    except Exception:
        pass
    p.kill()
    try: p.wait(timeout=10)
    except Exception: pass
    return {"go": go, "deadline_s": deadline_s, "elapsed_ms": round(elapsed, 1),
            "bestmove": best, "tripped": best is None}

def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    cases = [("FAST_nodes1", "go nodes 1", 5.0),
             ("SLOW_depth20", "go depth 20", 60.0),
             ("TRIP_infinite", "go infinite", 0.3)]
    rows = []
    print(f"{'case':16s} {'go':14s} {'deadline':>9} {'elapsed':>10} {'bestmove':>9} tripped")
    for name, go, dl in cases:
        r = run(exe, go, dl); r["case"] = name; rows.append(r)
        print(f"{name:16s} {go:14s} {dl:>8.1f}s {r['elapsed_ms']:>9.1f}ms "
              f"{str(r['bestmove']):>9} {r['tripped']}", flush=True)
    json.dump(rows, open(os.path.join(outdir, "timeout_control.json"), "w"), indent=1)
    fast = [r for r in rows if r["case"] == "FAST_nodes1"][0]
    trip = [r for r in rows if r["case"] == "TRIP_infinite"][0]
    slow = [r for r in rows if r["case"] == "SLOW_depth20"][0]
    print()
    print(f"FAST case returned in {fast['elapsed_ms']} ms with bestmove {fast['bestmove']} "
          f"-> {'SOUND (no false trip)' if not fast['tripped'] else 'BUG (false trip)'}")
    print(f"SLOW case returned in {slow['elapsed_ms']} ms -> "
          f"{'OK' if not slow['tripped'] else 'tripped early'}")
    print(f"TRIP case tripped: {trip['tripped']} -> "
          f"{'timeout CAN fire (control passes)' if trip['tripped'] else 'CONTROL FAILED: timeout never fires'}")

if __name__ == "__main__":
    main()
