#!/usr/bin/env python3
"""S02 — check of seat 19's 19-F48: do `go nodes` and `go softnodes` pick DIFFERENT MOVES at the same budget?

Their claim: on 38 ambiguous set-G positions (top two moves within 15 cp by MultiPV 2 at depth 12), `go nodes N`
and `go softnodes N` disagreed on 7 cells (18.4 %), at N = 20000 and 50000, PC r15 + PC20, Threads 1, Hash 16,
cold. Divergences clustered at 2-12 cp gaps while the exactly-equal (0 cp) positions agreed everywhere.

My check is built from THEIR SENTENCE, not their script, and from MY OWN ambiguous positions instead of their
set-G list, so agreement between us is evidence rather than a copy:
  1. find ambiguous positions myself: for each of my boards, run MultiPV 2 at depth 12 and keep the ones whose top
     two scores are within 15 cp;
  2. on each, run `go nodes N` and `go softnodes N` at N = 20000 and 50000, cold, and compare bestmoves.

Threads 1, Hash 16, OwnBook false, PC20, fresh process per search, interactive driver.

usage: check_19f48.py <pc_exe> <outdir>
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out_48"

PC20 = [
    "setoption name Threads value 1", "setoption name Hash value 16",
    "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
    "setoption name CuckooRep value true", "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
    "setoption name MateAlphaGuard value true", "setoption name OwnBook value false",
]
# my own candidate boards: quiet, balanced positions where the top moves tend to be close
CANDIDATES = [
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "rnbq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1",
    "r3k2r/pppq1ppp/2npbn2/4p3/4P3/2NPBN2/PPPQ1PPP/R3K2R w KQkq - 0 1",
    "2rq1rk1/pp1bppbp/2np1np1/8/3NP3/1BN1BP2/PPPQ2PP/2KR3R w - - 0 11",
    "r1bq1rk1/pp3ppp/2nbpn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9",
    "rnbq1b1r/ppp2kpp/3p1n2/8/3PP3/8/PPP2PPP/RNBQKB1R w KQ - 0 6",
    "r2qk2r/ppp1bppp/2n1bn2/3p4/3P4/2N1BN2/PPPB1PPP/R2QKB1R w KQkq - 0 8",
    "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 7",
    "r1bqkbnr/pp1n1ppp/2p5/3pp3/3PP3/2N2N2/PPP2PPP/R1BQKB1R w KQkq - 0 6",
]
NS = [20000, 50000]


def run(fen, go, multipv=None):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    L = []
    threading.Thread(target=lambda: [L.append(l.rstrip("\n")) for l in p.stdout], daemon=True).start()

    def send(t):
        if p.poll() is None:
            try:
                p.stdin.write(t + "\n")
                p.stdin.flush()
            except Exception:
                pass

    def wait(pref, n0=0, to=180.0):
        dl = time.monotonic() + to
        while time.monotonic() < dl:
            if any(l.startswith(pref) for l in L[n0:]):
                return True
            if p.poll() is not None:
                return any(l.startswith(pref) for l in L[n0:])
            time.sleep(0.001)
        return False

    send("uci")
    if not wait("uciok"):
        raise SystemExit("FAIL: no uciok")
    for s in PC20:
        send(s)
    if multipv:
        send("setoption name MultiPV value %d" % multipv)
    send("isready")
    if not wait("readyok"):
        raise SystemExit("FAIL: no readyok")
    for line in L:
        if "unknown option" in line or "invalid value" in line:
            raise SystemExit("FAIL: option refused: %r" % line)
    send("position fen " + fen)
    send("isready")
    n0 = len(L)
    wait("readyok", n0)
    n0 = len(L)
    send(go)
    if not wait("bestmove", n0, 240):
        raise SystemExit("FAIL: no bestmove for %r" % go)
    seg = list(L[n0:])
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    bm = [l for l in seg if l.startswith("bestmove")]
    best = bm[-1].split()[1] if bm else None
    # for MultiPV 2, the top two scores at the deepest depth
    scores = {}
    for line in seg:
        m = re.match(r"info depth (\d+) multipv (\d+) score (\S+) (-?\d+)", line)
        if m:
            scores[(int(m.group(1)), int(m.group(2)))] = (m.group(3), int(m.group(4)))
    return best, scores


def main():
    os.makedirs(OUT, exist_ok=True)
    json.dump({"exe": EXE,
               "sha256": subprocess.run(["sha256sum", EXE], capture_output=True,
                                        text=True).stdout.split()[0],
               "threads": 1, "hash_mb": 16, "settings": "PC20", "options": PC20,
               "candidates": CANDIDATES, "ns": NS,
               "ambiguity_definition": "top two MultiPV-2 scores at depth 12 within 15 cp",
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)

    print("== step 1: find AMBIGUOUS positions with my own MultiPV 2 depth-12 scan")
    ambiguous = []
    for fen in CANDIDATES:
        _, sc = run(fen, "go depth 12", multipv=2)
        d12 = {k[1]: v for k, v in sc.items() if k[0] == 12}
        if 1 not in d12 or 2 not in d12:
            print("   %-40s no two lines at d12" % fen[:40])
            continue
        a, b = d12[1][1], d12[2][1]
        gap = abs(a - b)
        mark = gap <= 15
        print("   %-40s top2 %s %d / %s %d  gap %d  %s"
              % (fen[:40], d12[1][0], a, d12[2][0], b, gap, "AMBIGUOUS" if mark else ""), flush=True)
        if mark:
            ambiguous.append({"fen": fen, "s1": a, "s2": b, "gap": gap,
                              "kind1": d12[1][0], "kind2": d12[2][0]})
    print()
    print("ambiguous positions found: %d of %d" % (len(ambiguous), len(CANDIDATES)))
    print()

    print("== step 2: `go nodes N` vs `go softnodes N` at the same budget")
    print()
    print("| position | gap cp | N | go nodes bestmove | go softnodes bestmove | differ? |")
    print("|---|---|---|---|---|---|")
    rows = []
    differ = 0
    total = 0
    for a in ambiguous:
        for n in NS:
            bn, _ = run(a["fen"], "go nodes %d" % n)
            bs, _ = run(a["fen"], "go softnodes %d" % n)
            total += 1
            d = (bn != bs)
            differ += d
            rows.append({"fen": a["fen"], "gap": a["gap"], "n": n,
                         "nodes_bestmove": bn, "softnodes_bestmove": bs, "differ": d})
            print("| `%s` | %d | %d | %s | %s | %s |"
                  % (a["fen"][:38], a["gap"], n, bn, bs, "**DIFFERS**" if d else "same"), flush=True)
    json.dump(rows, open(os.path.join(OUT, "rows.json"), "w"), indent=1)

    print()
    print("### verdict")
    print("- ambiguous positions: %d" % len(ambiguous))
    print("- cells compared: %d" % total)
    print("- cells where `go nodes` and `go softnodes` picked DIFFERENT moves: **%d (%.1f %%)**"
          % (differ, 100.0 * differ / total if total else 0))
    if total == 0:
        sys.exit("FAIL: no ambiguous positions found, so the claim cannot be tested — that is NOT a refutation")
    if differ:
        print()
        print("CONCLUSION: CONFIRMS seat 19's 19-F48 in kind — the two commands can pick different moves at the")
        print("            same nominal budget on ambiguous positions. Their rate was 7/38 (18.4 %%).")
    else:
        print()
        print("CONCLUSION: did NOT reproduce on my boards — the two commands agreed in every cell here.")
        print("            That is a difference of sample, not a refutation of their 7/38.")


if __name__ == "__main__":
    main()
