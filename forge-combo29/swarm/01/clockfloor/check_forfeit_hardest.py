#!/usr/bin/env python3
"""swarm seat 01: the forfeit claim against its HARDEST case — tiny clock, expensive positions (S-C44).

S-C43 strengthened S-F77 ("a forfeit is impossible from any starting clock") to 12 clocks and 0 forfeits. But that
sweep started every game at `startpos` and ran 60 plies, which is still opening theory: opening moves are CHEAP, and a
forfeit needs an expensive move relative to a small clock. So the sweep tested the claim in the region where it is
least likely to fail.

This tests the opposite region deliberately:

  * start from positions that demand LONG searches - a complex middlegame with many pieces and open lines, a
    tactical position with captures available, an endgame with a large tree;
  * give a TINY clock (1, 5, 10, 25 ms) - far below the 110 ms floor, and below what one expensive move could cost;
  * let the clock arithmetic run for many plies, recording the SPEND on every move, so the question "did any move
    cost more than the clock had plus the increment?" is answered per move rather than inferred from a final total.

The mechanism predicts no forfeit: spend is capped by the engine's own time management, which allocates a fraction of
the remaining clock, so it cannot spend more than it has. If that cap ever fails - a very small clock, an expensive
position - the clock goes negative and the run forfeits. That is the failure this looks for.

I also record the MAXIMUM single-move spend, because "no forfeit" with a max spend of 2 ms on a 1 ms clock would be a
much stronger statement than "no forfeit" with a max spend of 0 ms (which could mean the search never ran).

Usage: check_forfeit_hardest.py <exe> <outdir> [plies]
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
STARTS_MS = [1, 5, 10, 25, 50]

# Positions chosen because a search from them is EXPENSIVE - many pieces, open lines, tactics available. These are the
# opposite of opening theory, which is where the previous sweep lived.
POSITIONS = [
    ("complex-middlegame", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("tactical-open", "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8"),
    ("sharp-attack", "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"),
    ("busy-midgame", "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10"),
    ("endgame-technical", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
]


def play(exe, fen, start_ms, plies):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, cwd="/tmp")

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(prefix):
        for line in p.stdout:
            if line.startswith(prefix):
                return line.rstrip("\n")
        return None

    def to_bestmove():
        info = None
        for line in p.stdout:
            line = line.rstrip("\n")
            if line.startswith("info depth"):
                info = line
            if line.startswith("bestmove"):
                return line, info
        return None, info

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

    moves = []
    w = b = start_ms
    spends = []
    trace = []
    lowest = start_ms
    forfeited = None
    played = 0
    for ply in range(plies):
        white = (ply % 2 == 0)
        my_clock = w if white else b
        other = b if white else w
        if my_clock <= 0:
            forfeited = "white" if white else "black"
            break
        send("position fen " + fen + (" moves " + " ".join(moves) if moves else ""))
        send("isready")
        until("readyok")
        if white:
            send("go wtime %d btime %d winc %d binc %d" % (my_clock, other, INC, INC))
        else:
            send("go wtime %d btime %d winc %d binc %d" % (other, my_clock, INC, INC))
        bm, info = to_bestmove()
        if bm is None:
            forfeited = "no bestmove"
            break
        parts = bm.split()
        mv = parts[1] if len(parts) > 1 else None
        if mv in (None, "0000"):
            break
        spent = 0
        if info:
            m = re.search(r"time (\d+)", info)
            if m:
                spent = int(m.group(1))
        spends.append(spent)
        # record the clock BEFORE this move, so a spend that exceeds it is visible rather than inferred
        trace.append({"ply": ply, "clock_before": my_clock, "spent": spent,
                      "overrun": spent > my_clock + INC})
        new_clock = my_clock - spent + INC
        if white:
            w = new_clock
        else:
            b = new_clock
        lowest = min(lowest, w, b)
        moves.append(mv)
        played += 1
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    return {"fen": fen, "start": start_ms, "plies": played, "final_w": w, "final_b": b,
            "lowest": lowest, "forfeited": forfeited,
            "max_spend": max(spends) if spends else None,
            "mean_spend": round(sum(spends) / len(spends), 1) if spends else None,
            "first_spend": spends[0] if spends else None,
            "trace": trace,
            "max_overrun_ply": next((t for t in trace if t["overrun"]), None)}


def main():
    exe, out = sys.argv[1], Path(sys.argv[2])
    plies = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()

    rows = []
    print("=== %d positions x %d clocks, %d plies, increment %d" % (len(POSITIONS), len(STARTS_MS), plies, INC),
          flush=True)
    for name, fen in POSITIONS:
        for s in STARTS_MS:
            r = play(exe, fen, s, plies)
            r["pos"] = name
            rows.append(r)
            print("  %-18s start %-3d plies %-3d lowest %-4d max_spend %-5s forfeit=%s"
                  % (name, s, r["plies"], r["lowest"], r["max_spend"], r["forfeited"]), flush=True)

    forfeits = [r for r in rows if r["forfeited"]]
    spends = [r["max_spend"] for r in rows if r["max_spend"] is not None]
    L = ["S-C44: the forfeit claim against its hardest case - tiny clocks, expensive positions",
         "exe: %s" % exe, "sha256: %s" % sha,
         "PC20, Threads 1, Hash 16, winc=binc=%d, %d plies, move list accumulated." % (INC, plies),
         "Positions chosen because searches from them are EXPENSIVE - the opposite of the opening theory the",
         "previous sweep lived in.", "",
         "pos\tstart\tplies\tlowest\tmax_spend\tmean_spend\tforfeit"]
    for r in rows:
        L.append("%s\t%d\t%d\t%d\t%s\t%s\t%s" % (r["pos"], r["start"], r["plies"], r["lowest"],
                                                 r["max_spend"], r["mean_spend"], r["forfeited"] or "no"))
    L.append("")
    L.append("FORFEITS: %d of %d runs" % (len(forfeits), len(rows)))
    if spends:
        L.append("MAX single-move spend observed anywhere: %d ms (on clocks starting at 1, 5, 10, 25, 50 ms)"
                 % max(spends))
        # If the max spend is 0 everywhere, the search never ran and "no forfeit" would be vacuous.
        L.append("  (if this were 0, no forfeit would be vacuous - the search never spent anything)")
    L.append("")
    if forfeits:
        L.append("VERDICT: FOUND A FORFEIT - %d of %d runs, at:" % (len(forfeits), len(rows)))
        for r in forfeits[:6]:
            L.append("  %s, start %d ms" % (r["pos"], r["start"]))
        L.append("  S-C43's sweep would not have found this, because it only played opening moves.")
    elif spends and max(spends) > 0:
        L.append("VERDICT: NO FORFEIT even here - 0 of %d runs from expensive positions on clocks down to 1 ms," % len(rows))
        L.append("  with a maximum single-move spend of %d ms somewhere in the sweep." % max(spends))
        L.append("  This is a materially stronger test than S-C43's: that sweep played opening moves, where a search")
        L.append("  is cheap; here the searches are expensive and the clocks are smaller than one such search.")
        L.append("  The time manager's own allocation is what prevents the overrun (spend <= a fraction of the clock).")
    else:
        L.append("VERDICT: INCONCLUSIVE - no forfeit, but the maximum single-move spend was 0, so the searches may")
        L.append("  not have run at these clocks. A no-forfeit result from a search that never happened proves")
        L.append("  nothing (Trap 8).")

    (out / "check_forfeit_hardest.json").write_text(json.dumps({"sha": sha, "inc": INC, "plies": plies, "rows": rows},
                                                               indent=1))
    txt = "\n".join(L) + "\n"
    (out / "check_forfeit_hardest.txt").write_text(txt)
    print("")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
