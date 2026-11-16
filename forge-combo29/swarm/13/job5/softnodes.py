#!/usr/bin/env python3
"""Area: `go softnodes N` on the PC r15 build under PC20, Threads 1, Hash 16.

FABLE_TO_swarm_6 asks three things about the PC's self-play budget:
  1. is it DETERMINISTIC run to run (it must be);
  2. does it stop at the END OF A FINISHED DEPTH (not mid-depth);
  3. how far PAST N does it go (the overshoot), and does that overshoot scale with N.

Method per (position, N):
  * fresh process, PC20 applied in full with isready/readyok after every setoption;
  * send `go softnodes N`, read every line to `bestmove`;
  * record: the last depth whose `info` line completed, the node count on that line, whether an
    `info string softnodes nodes X` line appeared, and the bestmove;
  * determinism: run every (position, N) TWICE in separate processes and compare the whole
    (depth, nodes, score, bestmove) tuple.

"Stops at a finished depth" is tested as: the nodes on the last info line are the nodes of a
COMPLETE depth, i.e. re-running the same position with `go depth <that depth>` gives the SAME node
count. If softnodes stopped mid-depth the two counts would differ. That is a real test, not an
assumption about the output format.

Usage: softnodes.py EXE FENS OUTDIR [NS]
"""
import hashlib
import json
import os
import re
import subprocess
import sys

EXE = sys.argv[1]
FENS = sys.argv[2]
OUTDIR = sys.argv[3]
NS = [int(x) for x in (sys.argv[4] if len(sys.argv) > 4 else "200,500,1000,2000,5000,20000,50000").split(",")]
os.makedirs(OUTDIR, exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC6 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]
PC20 = [("Threads", "1"), ("Hash", "16")] + S14 + PC6
assert len(PC20) == 22, "PC20 must be 22 entries; a short list silently measures a different regime"
BAD = ("unknown option", "invalid value", "error")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run(fen, go_cmd):
    """One search in a fresh PC20 process. Returns the parsed result."""
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    sent = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()
        sent.append(s)

    def until(pred, what):
        while True:
            l = p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died waiting for %s" % what)
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r while waiting for %s" % (l, what))
            if pred(l):
                return l

    send("uci")
    opts = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died in uci handshake")
        l = l.rstrip("\n")
        if l.startswith("option name"):
            opts.append(l)
        if l == "uciok":
            break
    for n, v in PC20:
        if not any(o.startswith("option name %s " % n) for o in opts):
            raise SystemExit("FAIL: option %r not advertised by %s" % (n, EXE))
        send("setoption name %s value %s" % (n, v))
        send("isready")
        until(lambda s: s == "readyok", "readyok after %s" % n)
    send("position fen " + fen)
    send("isready")
    until(lambda s: s == "readyok", "readyok after position")
    send(go_cmd)

    infos = []
    softline = None
    bm = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: engine died during search")
        l = l.rstrip("\n")
        if any(b in l.lower() for b in BAD):
            raise SystemExit("FAIL: bad line %r during search" % l)
        if l.startswith("bestmove"):
            bm = l
            break
        if l.startswith("info string softnodes"):
            softline = l
        elif l.startswith("info depth"):
            infos.append(l)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()

    def parse_depth(l):
        m = re.search(r"\bdepth (\d+)", l)
        return int(m.group(1)) if m else None

    def parse_nodes(l):
        m = re.search(r"\bnodes (\d+)", l)
        return int(m.group(1)) if m else None

    def parse_score(l):
        m = re.search(r"\bscore (cp|mate) (-?\d+)", l)
        return (m.group(1), int(m.group(2))) if m else None

    last = infos[-1] if infos else None
    return {
        "go": go_cmd,
        "info_lines": len(infos),
        "max_depth": parse_depth(last) if last else None,
        "nodes": parse_nodes(last) if last else None,
        "score": parse_score(last) if last else None,
        "bestmove": bm,
        "softnodes_line": softline,
        "softnodes_reported": (int(re.search(r"nodes (\d+)", softline).group(1))
                               if softline and re.search(r"nodes (\d+)", softline) else None),
        "sent": sent,
    }


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()]
    results = []
    for fi, fen in enumerate(fens):
        for N in NS:
            a = run(fen, "go softnodes %d" % N)
            b = run(fen, "go softnodes %d" % N)
            det = (a["max_depth"], a["nodes"], a["score"], a["bestmove"]) == \
                  (b["max_depth"], b["nodes"], b["score"], b["bestmove"])
            # "finished depth" test: `go depth <reached>` must give the same node count
            fin = None
            if a["max_depth"]:
                c = run(fen, "go depth %d" % a["max_depth"])
                fin = (c["nodes"] == a["nodes"])
            overshoot = None
            if a["nodes"] is not None:
                overshoot = a["nodes"] - N
            row = {
                "position": fi, "fen": fen, "N": N,
                "depth_reached": a["max_depth"], "nodes": a["nodes"],
                "overshoot": overshoot,
                "overshoot_pct": (round(100.0 * overshoot / N, 1) if overshoot is not None and N else None),
                "score": a["score"], "bestmove": a["bestmove"],
                "softnodes_line": a["softnodes_line"],
                "softnodes_reported": a["softnodes_reported"],
                "deterministic_two_runs": det,
                "run_a": a, "run_b_nodes": b["nodes"], "run_b_depth": b["max_depth"],
                "finished_depth_matches_go_depth": fin,
            }
            results.append(row)
            print("pos %d N %-6d depth %-3s nodes %-8s over %-7s det %-5s finished %-5s"
                  % (fi, N, a["max_depth"], a["nodes"], overshoot, det, fin), flush=True)

    summary = {
        "build": os.path.abspath(EXE),
        "sha256": sha256(EXE),
        "settings": "PC20 (Threads 1, Hash 16, S14, PC6)",
        "positions": len(fens),
        "N_values": NS,
        "runs": len(results),
        "deterministic_runs": sum(1 for r in results if r["deterministic_two_runs"]),
        "runs_total": len(results),
        "finished_depth_ok": sum(1 for r in results if r["finished_depth_matches_go_depth"]),
        "finished_depth_checked": sum(1 for r in results if r["finished_depth_matches_go_depth"] is not None),
        "overshoot_min": min((r["overshoot"] for r in results if r["overshoot"] is not None), default=None),
        "overshoot_max": max((r["overshoot"] for r in results if r["overshoot"] is not None), default=None),
    }
    with open(os.path.join(OUTDIR, "softnodes.json"), "w") as f:
        json.dump({"summary": summary, "rows": results}, f, indent=1)
    print()
    for k, v in summary.items():
        print("%-28s %s" % (k, v))


main()
