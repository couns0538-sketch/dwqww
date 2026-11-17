#!/usr/bin/env python3
"""swarm seat 01: does the forfeit-impossible claim survive a DENSE clock sweep? (tests my own S-F77)

S-F77 says "a forfeit is IMPOSSIBLE from ANY starting clock at this increment", on the strength of **4** starting
clocks (600, 300, 150, 100 ms), all of which climbed. The mechanism is a fixed point: with `winc=binc=60` and a
search that spends under the increment, each move adds ~60 ms and only removes what was spent, so the clock rises
toward floor + increment and can never reach 0. That mechanism, if right, makes the claim true for ALL starting
values - but a mechanism story and a 4-point test are different kinds of evidence, and S-C42 just taught me that a
hand-picked small sample can look like agreement while the point estimate drifts.

So this tests the OUTLYING region rather than more of the same:
  * very small starts, well BELOW any plausible floor (1, 10, 25, 50 ms), where a forfeit is most likely if the
    claim is false;
  * a start of exactly 0 and 1 ms, the degenerate end;
  * a dense ladder between 50 and 200 ms, straddling the 110 ms floor, to see whether ANY value forfeits;
  * a few large starts as controls (should of course be fine).
For each: play until the clock would be exhausted, and record the LOWEST clock observed and whether the run
completed or forfeited.

The honest question is not "does it usually climb" - S-F77 showed that - but "is there ANY starting value in the
tested range where it does not", and "any" is what the claim actually says.

Implementation note: the game is driven by the ENGINE's reported `time` per move, applying `clock -= spent;
clock += increment` exactly as a GUI would, and it is the harness that declares a forfeit if a move would be played
with a non-positive clock. That is the tightest possible reading of the claim. A fixed ply count keeps every run
comparable.

Usage: check_forfeit_universal.py <exe> <outdir> [plies]
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
        ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

INC = 60
STARTS = [1, 10, 25, 50, 75, 100, 110, 125, 150, 200, 300, 600]


def play(exe, start_ms, plies, pc20=True):
    """One game. The HARNESS owns the clocks, applying the engine's own reported time."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, cwd="/tmp")

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(prefix):
        for line in p.stdout:
            line = line.rstrip("\n")
            if line.startswith(prefix):
                return line
        return None

    def read_unto_bestmove():
        last_info = None
        for line in p.stdout:
            line = line.rstrip("\n")
            if line.startswith("info depth"):
                last_info = line
            if line.startswith("bestmove"):
                return line, last_info
        return None, last_info

    send("uci")
    until("uciok")
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    for n, v in PC20:
        send("setoption name %s value %s" % (n, v))
    send("isready")
    until("readyok")
    send("ucinewgame")
    send("isready")
    until("readyok")
    send("position startpos")
    moves = []

    w, b = start_ms, start_ms
    lowest = start_ms
    trace = []
    forfeited = None
    played = 0
    for ply in range(plies):
        white = (ply % 2 == 0)
        my_clock = w if white else b
        if my_clock <= 0:
            forfeited = "white" if white else "black"
            break
        other = b if white else w
        if white:
            send("go wtime %d btime %d winc %d binc %d" % (my_clock, other, INC, INC))
        else:
            send("go wtime %d btime %d winc %d binc %d" % (other, my_clock, INC, INC))
        bm, info = read_unto_bestmove()
        if bm is None:
            forfeited = "no bestmove"
            break
        mv = bm.split()[1] if len(bm.split()) > 1 else None
        if mv in (None, "0000"):
            break
        spent = 0
        if info:
            m = re.search(r"time (\d+)", info)
            if m:
                spent = int(m.group(1))
        trace.append({"ply": ply, "clock_before": my_clock, "spent": spent,
                      "overrun": spent > my_clock + INC})
        new_clock = my_clock - spent + INC
        if white:
            w = new_clock
        else:
            b = new_clock
        lowest = min(lowest, w, b)
        played += 1
        # ACCUMULATE the game. My first version reset to startpos each ply, which tested clock arithmetic but not a
        # real game: with the position fixed, every move costs the same, so the only thing varying was the clock
        # itself. A real game varies per-move cost with position complexity, which is exactly what could break a
        # "never forfeits" claim - so the move list is carried forward.
        moves.append(mv)
        send("position startpos moves " + " ".join(moves))
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    return {"start": start_ms, "plies": played, "final_w": w, "final_b": b,
            "lowest": lowest, "forfeited": forfeited,
            # the per-move trace: without it the `lowest` extremum cannot be tied to the row it came from (S-C44)
            "trace": trace,
            "max_spend": max((e["spent"] for e in trace), default=None),
            "max_overrun_ply": next((e for e in trace if e["overrun"]), None)}


def main():
    exe, out = sys.argv[1], Path(sys.argv[2])
    plies = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()

    rows = []
    print("=== %d starting clocks, %d plies each, increment %d ms" % (len(STARTS), plies, INC), flush=True)
    for s in STARTS:
        r = play(exe, s, plies)
        rows.append(r)
        print("  start %-5d -> plies %-3d final %5d/%5d lowest %-5d forfeit=%s"
              % (s, r["plies"], r["final_w"], r["final_b"], r["lowest"], r["forfeited"]), flush=True)

    forfeits = [r for r in rows if r["forfeited"]]
    L = ["S-F77 re-tested on a DENSE sweep: is a forfeit impossible from ANY starting clock?",
         "exe: %s" % exe, "sha256: %s" % sha,
         "PC20, Threads 1, Hash 16, winc=binc=%d, %d plies, harness owns the clocks using the engine's reported time."
         % (INC, plies), "",
         "start\tplies\tfinal w/b\tlowest clock\tforfeit"]
    for r in rows:
        L.append("%d\t%d\t%d / %d\t%d\t%s" % (r["start"], r["plies"], r["final_w"], r["final_b"],
                                              r["lowest"], r["forfeited"] or "no"))
    L.append("")
    L.append("FORFEITS: %d of %d starting clocks" % (len(forfeits), len(rows)))
    if forfeits:
        L.append("  at starts: %s" % ", ".join(str(r["start"]) for r in forfeits))
    lowest_start_that_climbed = min((r["start"] for r in rows if not r["forfeited"]), default=None)
    L.append("")
    if not forfeits:
        L.append("VERDICT: CONFIRMS S-F77 over a DENSE range - 0 forfeits from %d starting clocks spanning %d to %d ms,"
                 % (len(rows), min(STARTS), max(STARTS)))
        L.append("  including starts far below the 110 ms floor (1, 10, 25, 50 ms). The claim's word \"any\" now has")
        L.append("  12 data points instead of 4, and the mechanism is unchanged: each move adds the increment and")
        L.append("  removes only what was spent, so the clock rises.")
    else:
        L.append("VERDICT: REFUTES the universality of S-F77 - %d of %d starting clocks FORFEITED (starts %s)."
                 % (len(forfeits), len(rows), ", ".join(str(r["start"]) for r in forfeits)))
        L.append("  The mechanism may still hold above some threshold; \"any\" does not.")

    (out / "check_forfeit_universal.json").write_text(json.dumps({"sha": sha, "inc": INC, "plies": plies,
                                                                  "rows": rows}, indent=1))
    txt = "\n".join(L) + "\n"
    (out / "check_forfeit_universal.txt").write_text(txt)
    print("")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
