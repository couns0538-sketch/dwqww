#!/usr/bin/env python3
"""S02 — the owner's real match path, and whether S-F7 can reach it.

FABLE_TO_swarm_6 names what the PC really does:
  engine   PC build, PC20, Threads 1, Hash 16
  self-play `go softnodes 2000`
  matches   `go nodes` 20000, 50000, 250000
  strength  clock 6 s + 0.06 s per move
  positions from real games

Two things to settle, both asked for:
  (1) Do those commands use MultiPV at all? PC20 does not name it (verified: the 22 PC20 option names contain
      no MultiPV), and the engine advertises `MultiPV ... default 1`. So on a FRESH process the answer is 1.
  (2) Can a MultiPV above 1 REACH that path? Only if something sets it and does not reset it. So the test is:
      set MultiPV to each value a GUI might leave behind, then run the owner's ACTUAL match command, and measure
      the cost — against Hash 16, because that is the Hash the matches use (not 2048).

Every run: PC20 + the MultiPV value under test, Threads 1, Hash 16, OwnBook false, fresh process, interactive
driver, COLD. Several real-game positions supplied here as FENs (from the middlegame/endgame boards this seat
has used throughout, which are game positions, not synthetic).

usage: match_path.py <pc_exe> <outdir> [runs]
"""
import json
import os
import re
import statistics
import subprocess
import sys
import threading
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out_match"
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 3

PC20_NO_MPV = [
    "setoption name Threads value 1",
    "setoption name Hash value 16",
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
    "setoption name CuckooRep value true",
    "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true",
    "setoption name CorrHistV2 value true",
    "setoption name MateAlphaGuard value true",
    "setoption name OwnBook value false",
]
POSITIONS = {
    "game_mid1": "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "game_mid2": "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "game_end": "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
}
# the owner's actual commands
COMMANDS = {
    "selfplay_softnodes_2000": "go softnodes 2000",
    "match_nodes_20000": "go nodes 20000",
    "match_nodes_50000": "go nodes 50000",
    "match_nodes_250000": "go nodes 250000",
    "strength_clock_6s": "go wtime 6000 btime 6000 winc 60 binc 60",
}


def run(fen, cmd, multipv):
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
    for s in PC20_NO_MPV:
        send(s)
    if multipv is not None:
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
    t0 = time.monotonic()
    send(cmd)
    if not wait("bestmove", n0, 240):
        raise SystemExit("FAIL: no bestmove for %r" % cmd)
    ms = (time.monotonic() - t0) * 1000.0
    seg = list(L[n0:])
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    depths = [int(m.group(1)) for l in seg for m in [re.match(r"info depth (\d+) ", l)] if m]
    nodes = [int(m.group(1)) for l in seg for m in [re.search(r" nodes (\d+)", l)] if m]
    bm = [l for l in seg if l.startswith("bestmove")]
    norm = [re.sub(r"(time|nps) \d+", r"\1 <X>", l) for l in seg if l.startswith("info depth")]
    return {"ms": round(ms, 0), "depth": max(depths) if depths else 0,
            "nodes": nodes[-1] if nodes else None,
            "bestmove": bm[-1].split()[1] if bm else None, "norm": norm}


def main():
    os.makedirs(OUT, exist_ok=True)
    json.dump({"exe": EXE,
               "sha256": subprocess.run(["sha256sum", EXE], capture_output=True,
                                        text=True).stdout.split()[0],
               "threads": 1, "hash_mb": 16, "settings": "PC20 (which does NOT set MultiPV)",
               "multipv_values_tested": [None, 2, 4, 8],
               "multipv_note": "None = leave MultiPV at the engine default, i.e. the owner's match path",
               "commands": COMMANDS, "positions": POSITIONS, "runs": RUNS,
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)

    rows = []
    for cmd_name, cmd in COMMANDS.items():
        for mpv in (None, 2, 4, 8):
            for pos_name, fen in POSITIONS.items():
                rs = [run(fen, cmd, mpv) for _ in range(RUNS)]
                det = all(r["norm"] == rs[0]["norm"] for r in rs)
                bm_same = all(r["bestmove"] == rs[0]["bestmove"] for r in rs)
                row = {"command": cmd_name, "multipv": mpv, "position": pos_name,
                       "deterministic": det, "bestmove_same": bm_same,
                       "depth": rs[0]["depth"], "nodes": rs[0]["nodes"],
                       "bestmove": rs[0]["bestmove"],
                       "median_ms": statistics.median([r["ms"] for r in rs])}
                rows.append(row)
                print("  %-26s MPV=%-4s %-10s det=%-5s depth=%-3d nodes=%-8s bm=%-5s %6.0f ms"
                      % (cmd_name, mpv if mpv else "default", pos_name, det,
                         row["depth"], row["nodes"], row["bestmove"], row["median_ms"]), flush=True)

    print()
    print("### does MultiPV change what the owner's commands produce? (median of %d runs)" % RUNS)
    print()
    print("| command | MPV default: depth / nodes / ms | MPV 2 | MPV 4 | MPV 8 | output changes at MPV 8? |")
    print("|---|---|---|---|---|---|")
    for cmd_name in COMMANDS:
        def cell(mpv):
            sub = [r for r in rows if r["command"] == cmd_name and r["multipv"] == mpv]
            if not sub:
                return "-"
            d = statistics.median([r["depth"] for r in sub])
            n = statistics.median([r["nodes"] or 0 for r in sub])
            t = statistics.median([r["median_ms"] for r in sub])
            return "d%.0f / %d / %.0f ms" % (d, n, t)
        base = [r for r in rows if r["command"] == cmd_name and r["multipv"] is None]
        m8 = [r for r in rows if r["command"] == cmd_name and r["multipv"] == 8]
        changed = any(b["norm"] != m["norm"] for b, m in zip(base, m8)) if base and m8 else None
        print("| %s | %s | %s | %s | %s | %s |"
              % (cmd_name, cell(None), cell(2), cell(4), cell(8),
                 "YES" if changed else ("no" if changed is False else "-")))
    json.dump(rows, open(os.path.join(OUT, "rows.json"), "w"), indent=1)

    print()
    print("### determinism, every cell")
    bad = [r for r in rows if not r["deterministic"]]
    print("- cells not deterministic across %d runs: %d of %d" % (RUNS, len(bad), len(rows)))
    for r in bad:
        print("    %s MPV=%s %s" % (r["command"], r["multipv"], r["position"]))


if __name__ == "__main__":
    main()
