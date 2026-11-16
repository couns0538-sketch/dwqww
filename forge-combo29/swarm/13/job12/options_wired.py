#!/usr/bin/env python3
"""Are the PC's six new search options actually WIRED UP?

FABLE file 5 added six UCI options behind switches: CuckooRep, HistRework, TtPruneV2, CorrHistV2,
MateAlphaGuard, OwnBook. Each is advertised in the exe's `uci` list. The question this script asks is
narrow and answerable: does changing each one change the engine's SEARCH BEHAVIOUR?

Method (all fresh process, Threads 1, Hash 16, no warm state):
  baseline  = S14, with the option at its DEFAULT value
  variant   = S14, with that ONE option changed
For each option, compare:
  * bench 11 node count
  * a depth-12 search of a fixed middlegame position: node count, score, bestmove
  * a depth-12 search of a fixed tactical position: same
An option that changes NOTHING on any of these is reported as INERT-ON-THESE-TESTS, which is a
prompt, not a conclusion: bench may not exercise a given feature, and an option can legitimately have
no effect on one position.

MateAlphaGuard is additionally tested where it must matter: a mate-in-1 board and a
halfmove-near-100 board, since a mate-guard that never changes anything on those would be suspicious.

Usage: options_wired.py EXE OUTDIR
"""
import hashlib
import json
import os
import re
import subprocess
import sys

EXE = sys.argv[1]
OUTDIR = sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
BASE = [("Threads", "1"), ("Hash", "16")]

# option -> (its default, the value we switch it to) per FABLE file 5's PC20 definition
OPTIONS = [
    ("CuckooRep", "false", "true"),
    ("HistRework", "0", "2"),
    ("TtPruneV2", "false", "true"),
    ("CorrHistV2", "false", "true"),
    ("MateAlphaGuard", "false", "true"),
    ("OwnBook", "true", "false"),
]

TACTICAL = "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"
MIDDLE = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"
MATE1 = "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1"
# a board a few half-moves from the fifty-move rule, where a mate guard could plausibly matter
NEAR50 = "7k/5Q2/6K1/8/8/8/8/8 w - - 96 60"

BAD = ("unknown option", "invalid value", "error")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run(opts, go_cmd, fen=None):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            l = p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if pred(l):
                return l

    send("uci")
    seen = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died in uci handshake")
        l = l.rstrip("\n")
        if l.startswith("option name"):
            seen.append(l)
        if l == "uciok":
            break
    for n, v in opts:
        if not any(o.startswith("option name %s " % n) for o in seen):
            raise SystemExit("FAIL: option %r not advertised" % n)
        send("setoption name %s value %s" % (n, v))
        send("isready")
        until(lambda s: s == "readyok")
    if fen:
        send("position fen " + fen)
    else:
        send("position startpos")
    send("isready")
    until(lambda s: s == "readyok")
    send(go_cmd)
    last = None
    bm = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died during search")
        l = l.rstrip("\n")
        if "bench depth" in l and "nodes" in l:
            last = l
            bm = "(bench)"
            break
        if l.startswith("bestmove"):
            bm = l
            break
        if l.startswith("info depth"):
            last = l
    send("quit")
    try:
        p.wait(timeout=15)
    except Exception:
        p.kill()

    def g(pat, cast=int):
        m = re.search(pat, last) if last else None
        return cast(m.group(1)) if m else None

    return {
        "nodes": g(r"\bnodes (\d+)"),
        "cp": g(r"\bscore cp (-?\d+)"),
        "mate": g(r"\bscore mate (-?\d+)"),
        "depth": g(r"\bdepth (\d+)"),
        "bestmove": bm,
    }


def main():
    probes = [
        ("bench11", "bench 11", None),
        ("tactical_d12", "go depth 12", TACTICAL),
        ("middle_d12", "go depth 12", MIDDLE),
        ("mate1_d12", "go depth 12", MATE1),
        ("near50_d12", "go depth 12", NEAR50),
    ]
    # baseline with every option at its default
    defaults = [(n, d) for n, d, _v in OPTIONS]
    baseline = {}
    for pname, cmd, fen in probes:
        baseline[pname] = run(BASE + S14 + defaults, cmd, fen)
        print("baseline %-12s %s" % (pname, baseline[pname]), flush=True)

    results = []
    for opt, dflt, on in OPTIONS:
        row = {"option": opt, "default": dflt, "variant": on, "probes": {}}
        changed = []
        for pname, cmd, fen in probes:
            opts = BASE + S14 + [(n, (on if n == opt else dv)) for n, dv, _vv in OPTIONS]
            r = run(opts, cmd, fen)
            same = (r["nodes"] == baseline[pname]["nodes"]
                    and r["cp"] == baseline[pname]["cp"]
                    and r["mate"] == baseline[pname]["mate"]
                    and r["bestmove"] == baseline[pname]["bestmove"])
            row["probes"][pname] = {"variant": r, "baseline": baseline[pname], "identical": same}
            if not same:
                changed.append(pname)
        row["changed_on"] = changed
        row["inert_on_all_probes"] = (len(changed) == 0)
        results.append(row)
        print("%-14s default=%-5s on=%-5s changed on: %s"
              % (opt, dflt, on, ", ".join(changed) or "NOTHING"), flush=True)

    summary = {
        "exe": os.path.abspath(EXE),
        "sha256": sha256(EXE),
        "settings": "Threads 1, Hash 16, S14, fresh process per run",
        "options_tested": len(OPTIONS),
        "inert_on_all_probes": [r["option"] for r in results if r["inert_on_all_probes"]],
        "note": "INERT here means 'no effect on these five probes' - bench and one position each. "
                "It is a prompt for a closer look, NOT proof an option is unwired.",
    }
    json.dump({"summary": summary, "results": results, "baseline": baseline},
              open(os.path.join(OUTDIR, "options_wired.json"), "w"), indent=1)
    print()
    for k, v in summary.items():
        print("%-24s %s" % (k, v))


main()
