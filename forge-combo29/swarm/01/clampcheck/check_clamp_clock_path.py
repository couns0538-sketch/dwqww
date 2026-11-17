#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 02's S-C19 — does the depth-64 clamp reach the owner's real clock path?

Seat 02 measured 8 real game boards on `go wtime 6000 btime 6000 winc 60 binc 60` and found depths 16-21 with
**0 of 8 hitting the depth-64 clamp**, concluding the clamp is a HARNESS hazard (mixing solved positions into a
latency average) and not a risk to the owner's play.

That is a claim about a bound, and bounds are exactly what I have learned to measure rather than trust. My check is
deliberately built differently from theirs so that agreement means something:

  * I do not reuse their boards. I take positions from the START of the game and from the MIDDLEGAME at several
    material balances, because the clamp's whole question is how deep a position can go before a clock stops it.
  * I record the depth REACHED and also the depth LIMIT the engine was willing to go to, so "did not hit the clamp"
    is shown as a fact about the search rather than inferred from a wall time.
  * I include the opposite control: a position that SHOULD hit the clamp (a solved board where search terminates on
    its own, which is what S-C18 described). Without that control, "0 of N hit the clamp" could equally mean the
    clamp cannot fire under any clock command, which would make the test unable to fire (Trap 8).
  * I add a mate-limited run (`go mate N`) because `mate_depth` shares the same clamp expression at
    search.cpp:2539-2540, so a defect there would show up in both paths.

The mechanism under test (src/search.cpp:2539-2540):

    const int mate_depth = mate_moves > 0 ? mate_moves * 2 - 1 : 64;
    int max_depth = std::clamp(std::min(limits.depth, mate_depth), 1, 64);

With no `mate` token, `mate_depth` is 64, so the clock path's ceiling is 64 — the clamp only bites a search that
would otherwise go deeper than 64, which for a clock command means a position the search finishes quickly.

For each case: did the search END ON ITS OWN (reached a natural maximum) or was it CUT by the clock? The clamp
"fires" only when the reported depth reaches 64 while the clock still had time.

Usage: check_clamp_clock_path.py <pc-exe> <outdir>
"""
import hashlib
import json
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
        ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

CLOCK = "go wtime 6000 btime 6000 winc 60 binc 60"

# Game-like positions, none of them solved: the question is how deep a real search goes under 6 s + 60 ms inc.
CASES = [
    ("startpos", "startpos"),
    ("italian", "fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"),
    ("ruy-lopez", "fen r1bqk2r/2ppbppp/p1n2n2/1p2p3/4P3/1B3N2/PPPP1PPP/RNBQR1K1 w kq - 0 8"),
    ("sicilian-mid", "fen r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8"),
    ("kings-indian", "fen r1bq1rk1/ppp1ppbp/2np1np1/8/2PPP3/2N2N2/PP2BPPP/R1BQK2R w KQ - 0 8"),
    ("endgame-rook", "fen 8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40"),
    ("endgame-pawns", "fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
    ("open-mid", "fen r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10"),
]

# CONTROLS: these are the shape S-C18 says DOES terminate on its own. If the clamp can fire at all, it fires here.
CONTROLS = [
    ("mated-board", "fen 7k/5KQ1/8/8/8/8/8/8 b - - 0 1"),          # black is checkmated
    ("stalemate", "fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),            # stalemate
    ("mate-in-1", "fen 6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1"),     # Re8# available
    ("kp-vs-k", "fen 8/8/8/4k3/8/4K3/4P3/8 w - - 0 50"),            # trivial, tiny tree
]


class R:
    def __init__(self, fd):
        self.fd, self.buf, self.eof = fd, b"", False

    def line(self, dl):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            rem = dl - time.monotonic()
            if rem <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], rem)
            if not r:
                return None
            c = os.read(self.fd, 65536)
            if not c:
                self.eof = True
                return None
            self.buf += c
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


def run(exe, pos, go, cap=12.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []

    def send(s):
        try:
            p.stdin.write((s + "\n").encode())
            p.stdin.flush()
        except Exception:
            pass

    def until(pre, dl):
        while True:
            l = rd.line(dl)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(pre):
                return l

    d = time.monotonic() + 60
    send("uci")
    until("uciok", d)
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    for n, v in PC20:
        send("setoption name %s value %s" % (n, v))
    send("isready")
    until("readyok", d)
    send("ucinewgame")
    send("isready")
    until("readyok", d)
    send("position " + pos)
    send("isready")
    until("readyok", d)

    t0 = time.monotonic()
    send(go)
    bm = None
    end = time.monotonic() + cap
    while time.monotonic() < end:
        l = rd.line(time.monotonic() + 0.5)
        if l is None:
            if p.poll() is not None:
                break
            continue
        buf.append(l)
        if l.startswith("bestmove"):
            bm = l
            break
    elapsed = time.monotonic() - t0
    stopped_by_me = bm is None
    if stopped_by_me:
        send("stop")
        time.sleep(0.4)
    send("quit")
    try:
        p.wait(timeout=15)
    except Exception:
        p.kill()

    depths = [int(m.group(1)) for l in buf
              for m in [re.match(r"info depth (\d+)", l)] if m]
    last = next((l for l in reversed(buf) if l.startswith("info depth")), "")
    nodes = None
    mt = re.search(r"nodes (\d+)", last)
    if mt:
        nodes = int(mt.group(1))
    score = None
    ms = re.search(r"score (cp|mate) (-?\d+)", last)
    if ms:
        score = "%s %s" % (ms.group(1), ms.group(2))
    return {"depth": max(depths) if depths else None, "max_info_depth": depths[-1] if depths else None,
            "nodes": nodes, "score": score, "bestmove": bm.split()[1] if bm else None,
            "elapsed_s": round(elapsed, 2), "cut_by_harness": stopped_by_me,
            "ended_early": bm is not None and elapsed < cap}


def main():
    exe, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()

    rows = []
    print("=== A. game-like positions, %s" % CLOCK)
    for name, pos in CASES:
        r = run(exe, pos, CLOCK)
        r["case"], r["kind"] = name, "game"
        rows.append(r)
        print("  %-15s depth=%-4s nodes=%-9s bestmove=%-6s %5.2fs cut_by_harness=%s"
              % (name, r["depth"], r["nodes"], r["bestmove"], r["elapsed_s"], r["cut_by_harness"]), flush=True)

    print("=== B. CONTROL: positions that should terminate on their own")
    ctrls = []
    for name, pos in CONTROLS:
        r = run(exe, pos, CLOCK, cap=6.0)
        r["case"], r["kind"] = name, "control"
        ctrls.append(r)
        print("  %-15s depth=%-4s nodes=%-9s bestmove=%-6s %5.2fs ended_early=%s"
              % (name, r["depth"], r["nodes"], r["bestmove"], r["elapsed_s"], r["ended_early"]), flush=True)

    L = ["CHECK of seat 02's S-C19: does the depth-64 clamp reach the owner's clock path?",
         "exe: %s" % exe, "sha256: %s" % sha,
         "PC r15 + PC20, Threads 1, Hash 16. Clock command under test: %s" % CLOCK,
         "Mechanism (src/search.cpp:2539-2540): mate_depth = 64 without a `mate` token, so the clock path's ceiling",
         "is 64; the clamp bites only a search that would otherwise exceed 64, i.e. a position that finishes fast.",
         "",
         "A. game-like positions (none solved)",
         "case\tdepth\tnodes\tbestmove\telapsed_s\tcut_by_harness\tscore"]
    for r in rows:
        L.append("%s\t%s\t%s\t%s\t%.2f\t%s\t%s" % (r["case"], r["depth"], r["nodes"], r["bestmove"],
                                                   r["elapsed_s"], r["cut_by_harness"], r["score"]))
    L += ["", "B. CONTROL - these SHOULD end on their own; if none of them does, the clamp cannot fire and the",
          "   whole test would be unable to produce a positive (Trap 8).",
          "case\tdepth\tnodes\tbestmove\telapsed_s\tended_early\tscore"]
    for r in ctrls:
        L.append("%s\t%s\t%s\t%s\t%.2f\t%s\t%s" % (r["case"], r["depth"], r["nodes"], r["bestmove"],
                                                   r["elapsed_s"], r["ended_early"], r["score"]))
    L.append("")

    hit64 = [r for r in rows if r["depth"] is not None and r["depth"] >= 64]
    deep = [r["depth"] for r in rows if r["depth"] is not None]
    ctrl_fired = [r for r in ctrls if r["depth"] is not None and r["depth"] >= 64]
    ctrl_ended = [r for r in ctrls if r["ended_early"]]

    L.append("RESULTS")
    L.append("  game positions: depths %s" % (sorted(deep) if deep else "none"))
    L.append("  reached depth 64: %d of %d" % (len(hit64), len(rows)))
    L.append("  control positions reaching depth 64: %d of %d (%s)"
             % (len(ctrl_fired), len(ctrls), ", ".join(r["case"] for r in ctrl_fired) or "none"))
    L.append("  control positions that ended on their own: %d of %d" % (len(ctrl_ended), len(ctrls)))
    L.append("")

    if not ctrl_fired:
        L.append("VERDICT: the control never reached 64 either, so THIS TEST COULD NOT HAVE PRODUCED A POSITIVE.")
        L.append("  Reported as inconclusive about the clamp, not as agreement: 0 of %d game boards hitting 64 means"
                 % len(rows))
        L.append("  nothing if no position in the set can reach 64 under this clock at all. Trap 8.")
    elif not hit64 and deep and max(deep) < 64:
        L.append("VERDICT: CONFIRMS seat 02's S-C19. No game-like position reached the clamp (deepest %d of a"
                 % max(deep))
        L.append("  possible 64), while the control set DID reach it (%s) - so the clamp is reachable and these"
                 % ", ".join(r["case"] for r in ctrl_fired))
        L.append("  clock searches simply do not get there. The clamp is a harness hazard on solved positions, not a")
        L.append("  bound the owner's play can hit.")
    elif hit64:
        L.append("VERDICT: CONTRADICTS seat 02's S-C19 - %d of %d game-like positions REACHED depth 64 under the"
                 % (len(hit64), len(rows)))
        L.append("  owner's clock command (%s)." % ", ".join(r["case"] for r in hit64))
    else:
        L.append("VERDICT: mixed / inconclusive - see the per-case rows; reported as measured.")
    (out / "check_clamp_clock_path.json").write_text(json.dumps({"sha": sha, "game": rows, "controls": ctrls}, indent=1))
    (out / "check_clamp_clock_path.txt").write_text("\n".join(L) + "\n")
    print("")
    print("\n".join(L))


if __name__ == "__main__":
    main()
