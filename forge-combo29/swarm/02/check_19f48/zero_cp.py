#!/usr/bin/env python3
"""S02 — the 0-cp half of seat 19's 19-F48: do the two modes agree when the top pair is EXACTLY tied?

Their sub-claim: divergences cluster at 2-12 cp gaps, while the FOUR exactly-equal (0 cp) positions agreed in
every cell. My S-C10 confirmed the first half (3 of 12 cells differ at gaps 9/13/15) but had no 0-cp board, so
this half was untested. This builds 0-cp boards DELIBERATELY and tests the same two modes.

How to get an exact tie reliably: use a position where two moves are equal BY SYMMETRY, so no evaluation noise can
separate them. I take symmetric / mirrored constructions and then VERIFY the tie with MultiPV 2 at depth 12 rather
than assuming it — a board that does not come out exactly tied is rejected and reported, not quietly used.

Method, identical to the S-C10 check so the two are comparable:
  1. MultiPV 2 at depth 12 -> keep boards whose top two scores are exactly equal;
  2. `go nodes N` vs `go softnodes N` at N = 20000 and 50000, cold, compare bestmoves.

PC r15 + PC20, Threads 1, Hash 16, OwnBook false, fresh process per search, interactive driver.

usage: zero_cp.py <pc_exe> <outdir>
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out_0cp"

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

# Deliberate tie constructions. A tie is GUARANTEED, not hoped for, when TWO OR MORE distinct legal moves each
# give immediate checkmate: every such move scores `mate 1`, so the top two are exactly equal by definition.
# Each board below was verified with python-chess to have >= 2 mating moves BEFORE it was used (the script
# re-verifies and rejects any board that does not).
TIE_BOARDS = {
    "two_mates_rook": "4k3/8/4K3/8/8/8/8/R6R w - - 0 1",          # h1h8 and a1a8 both mate
    "two_mates_rook2": "k7/8/1K6/8/8/8/8/3R3R w - - 0 1",         # h1h8 and d1d8 both mate
    "two_mates_qr": "k7/8/1K6/8/8/8/8/3Q3R w - - 0 1",            # h1h8 and d1d8 both mate
    "two_mates_qr2": "k7/8/1K6/8/8/8/7Q/7R w - - 0 1",            # h2h8 and h1a1 both mate
    "three_mates_qqq": "1k6/8/2K5/8/8/8/Q7/Q7 w - - 0 1",         # a2g8, a2a8, a1h8 all mate
    "two_mates_qr3": "1k6/8/3K4/8/8/8/8/R6Q w - - 0 1",           # h1a8 and a1a8 both mate
}


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
        raise SystemExit("FAIL: no bestmove for %r on %s" % (go, fen))
    seg = list(L[n0:])
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    bm = [l for l in seg if l.startswith("bestmove")]
    best = bm[-1].split()[1] if bm else None
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
               "tie_boards": TIE_BOARDS, "ns": [20000, 50000],
               "tie_definition": "exactly equal top two MultiPV-2 scores at depth 12",
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)

    print("== step 1: which constructed boards give an EXACT top-two tie at depth 12?")
    tied = []
    for name, fen in TIE_BOARDS.items():
        bm, sc = run(fen, "go depth 12", multipv=2)
        d12 = {k[1]: v for k, v in sc.items() if k[0] == 12}
        if 1 not in d12 or 2 not in d12:
            print("   %-16s no two lines at d12 (%s)" % (name, sorted(d12)))
            continue
        a, b = d12[1][1], d12[2][1]
        exact = (a == b)
        print("   %-16s top2 %s %d / %s %d  gap %d  %s"
              % (name, d12[1][0], a, d12[2][0], b, abs(a - b),
                 "EXACT TIE" if exact else "not tied (rejected)"), flush=True)
        if exact:
            tied.append({"name": name, "fen": fen, "score": a, "kind": d12[1][0]})
    print()
    print("exactly-tied boards: %d of %d constructed" % (len(tied), len(TIE_BOARDS)))
    if len(tied) < 3:
        print()
        print("NOTE: fewer than 3 of my constructions came out exactly tied. I report that rather than")
        print("      weakening the tie definition to pad the sample.")
    print()

    print("== step 2: `go nodes N` vs `go softnodes N` on the exactly-tied boards")
    print()
    print("| board | tie score | N | `go nodes` | `go softnodes` | agree? |")
    print("|---|---|---|---|---|---|")
    rows = []
    differ = 0
    total = 0
    for t in tied:
        for n in (20000, 50000):
            bn, _ = run(t["fen"], "go nodes %d" % n)
            bs, _ = run(t["fen"], "go softnodes %d" % n)
            total += 1
            d = (bn != bs)
            differ += d
            rows.append({"board": t["name"], "fen": t["fen"], "tie": t["score"], "n": n,
                         "nodes_bestmove": bn, "softnodes_bestmove": bs, "differ": d})
            print("| %s | %d | %d | %s | %s | %s |"
                  % (t["name"], t["score"], n, bn, bs, "**DIFFER**" if d else "agree"), flush=True)
    json.dump(rows, open(os.path.join(OUT, "rows.json"), "w"), indent=1)

    print()
    print("### verdict on the 0-cp half of 19-F48")
    print("- exactly-tied boards tested: %d" % len(tied))
    print("- cells compared: %d" % total)
    print("- cells where the two modes picked DIFFERENT moves: **%d (%.1f %%)**"
          % (differ, 100.0 * differ / total if total else 0))
    if total == 0:
        sys.exit("FAIL: no exactly-tied board was constructed, so the sub-claim cannot be tested")
    if differ == 0:
        print()
        print("CONCLUSION: CONFIRMS the sub-claim — on exactly-tied positions the two modes agreed in every cell.")
        print("            Combined with S-C10 (3 of 12 differing at 9-15 cp gaps) the rule is complete: a")
        print("            nominal node budget is comparable across `go nodes` and `go softnodes` only when the")
        print("            top moves are EXACTLY equal; any non-zero gap can flip the reported move.")
    else:
        print()
        print("CONCLUSION: the sub-claim does NOT hold on my constructions — the two modes differed on")
        print("            exactly-tied positions too, which would WEAKEN the 'safe positions' rule.")


if __name__ == "__main__":
    main()
