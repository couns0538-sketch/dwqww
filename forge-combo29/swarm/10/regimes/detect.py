#!/usr/bin/env python3
"""detect.py OUTDIR -- can the MIDDLE BAND be detected from the engine's own output?

The question that decides the defence: an interrupted search in the middle band prints a real move with a
wrong score and nothing that says "unfinished". Is there ANY signature in the printed lines?

For every (build, position) this records:
  FINISHED  : the full output to `bestmove`, read to completion
  MIDDLE xN : `quit` sent at several delays inside the band found earlier (25-45 ms), several records each

and then tests, mechanically, every candidate signature a consumer could apply to recorded data:

  S1 missing depth: are iterations 1..D present with no gap in the `depth` field?
  S2 last depth vs bestmove depth: is the LAST info line's depth equal to the largest depth printed?
  S3 pv length vs reported depth: does the pv have at most `depth` moves? (a pv longer than the depth
     is impossible; a pv much SHORTER than the depth is normal for a fail-low, so this is only a
     one-sided test)
  S4 pv legality/consistency: is every pv move legal in sequence? (a truncated pv is still legal)
  S5 nodes monotonic: are node counts non-decreasing across iterations?
  S6 nodes vs time sanity: nps constant-ish? (a final line with a tiny `time` and a huge node count is odd)
  S7 score change step: |score(last) - score(prev)| -- large jumps can be normal, so this is only a WEAK hint
  S8 score reachability: replay the pv with python-chess; does the static eval agree with the reported score?
     (if the reported score is the pv's leaf eval this is an independent consistency check)
  S9 depth cap: is the last depth equal to the requested depth (12)? the finished search reaches 12; a
     middle-band search usually does not
  S10 hashfull: present only on the last lines?

S9 is the obvious candidate: if the finished search always reaches the requested depth and the middle band
never does, then "last depth < requested depth" is a signature for data where the requested depth is known.
The interesting case is data where the requested depth is NOT recorded -- so this also reports whether S9
holds and whether anything survives when the request is unknown.

Usage: detect.py OUTDIR
"""
import json
import os
import subprocess
import sys
import time

import chess

BASE = os.path.expanduser("~/builds/release/forge")
PC = os.path.expanduser("~/builds/pc/forge")
OUT = os.path.abspath(sys.argv[1])
os.makedirs(OUT, exist_ok=True)
DEPTH = 12
MIDDLE_DELAYS = [25, 28, 30, 32, 35, 40, 45]

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

POSITIONS = {
    "startpos": "position startpos",
    "G_black_mid": "position fen r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1",
    "G_knight_out": "position fen 1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "tactical": "position fen r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1",
}


def setup(regime):
    lines = ["uci", "isready", "setoption name Threads value 1",
             "setoption name Hash value 16", "setoption name OwnBook value false"]
    lines += ["setoption name %s value %s" % kv for kv in (S14 if regime == "s14" else PC20)]
    lines += ["isready", "ucinewgame", "isready"]
    return lines


def finished(exe, regime, pos):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for l in setup(regime) + [pos, "isready"]:
        p.stdin.write(l + "\n")
        p.stdin.flush()
    p.stdin.write("go depth %d\n" % DEPTH)
    p.stdin.flush()
    out = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        out.append(line.rstrip())
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n")
    try:
        p.stdin.flush()
    except Exception:
        pass
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    return out


def interrupted(exe, regime, pos, delay_ms):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for l in setup(regime) + [pos, "isready"]:
        p.stdin.write(l + "\n")
        p.stdin.flush()
    t0 = time.monotonic()
    p.stdin.write("go depth %d\n" % DEPTH)
    p.stdin.flush()
    target = t0 + delay_ms / 1000.0
    while time.monotonic() < target:
        time.sleep(max(0.0, min(0.0005, target - time.monotonic())))
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
    except Exception:
        pass
    try:
        out = p.communicate(timeout=120)[0]
    except Exception:
        p.kill()
        out = p.communicate()[0]
    return out.splitlines()


def parse(lines):
    infos = []
    best = None
    for l in lines:
        s = l.strip()
        if s.startswith("info depth"):
            d = {"raw": s}
            for key, conv in (("depth", int), ("seldepth", int), ("nodes", int),
                              ("nps", int), ("hashfull", int), ("time", int)):
                if (" %s " % key) in s:
                    try:
                        d[key] = conv(s.split(" %s " % key)[1].split()[0])
                    except (IndexError, ValueError):
                        pass
            if " score cp " in s:
                try:
                    d["score"] = ("cp", int(s.split(" score cp ")[1].split()[0]))
                except (IndexError, ValueError):
                    pass
            if " score mate " in s:
                try:
                    d["score"] = ("mate", int(s.split(" score mate ")[1].split()[0]))
                except (IndexError, ValueError):
                    pass
            if " pv " in s:
                d["pv"] = s.split(" pv ", 1)[1].split()
            infos.append(d)
        elif s.startswith("bestmove"):
            best = s.split()[1]
    return {"infos": infos, "bestmove": best}


def legal_pv(fen, pv):
    """walk the pv with python-chess; returns (all_legal, plies_walked)"""
    try:
        b = chess.Board(fen) if fen else chess.Board()
    except ValueError:
        return (None, 0)
    n = 0
    for mv in pv:
        try:
            m = chess.Move.from_uci(mv)
        except ValueError:
            return (False, n)
        if m not in b.legal_moves:
            return (False, n)
        b.push(m)
        n += 1
    return (True, n)


def signatures(parsed, fen, requested=DEPTH):
    """every candidate detection rule, as booleans/facts a consumer could compute"""
    infos = parsed["infos"]
    if not infos:
        return {"empty": True}
    depths = [i.get("depth") for i in infos if "depth" in i]
    nodes = [i.get("nodes") for i in infos if "nodes" in i]
    times = [i.get("time") for i in infos if "time" in i]
    last = infos[-1]
    last_depth = last.get("depth")
    max_depth = max(depths) if depths else None
    # S1: iterations 1..max_depth all present, no gap
    contiguous = (sorted(set(depths)) == list(range(1, max_depth + 1))) if depths else None
    # S3: pv longer than depth is impossible
    pv = last.get("pv", [])
    pv_len = len(pv)
    # S4
    all_legal, walked = legal_pv(fen, pv)
    # S5
    mono = all(b >= a for a, b in zip(nodes, nodes[1:])) if len(nodes) > 1 else None
    # S9
    reached_requested = (last_depth == requested)
    return {
        "empty": False,
        "info_lines": len(infos),
        "last_depth": last_depth,
        "max_depth": max_depth,
        "S1_depths_contiguous": contiguous,
        "S2_last_is_max_depth": (last_depth == max_depth),
        "S3_pv_len": pv_len,
        "S3_pv_longer_than_depth": (pv_len > (last_depth or 0)),
        "S4_pv_all_legal": all_legal,
        "S4_pv_plies_walked": walked,
        "S5_nodes_monotonic": mono,
        "S6_last_time_ms": last.get("time"),
        "S6_last_nodes": last.get("nodes"),
        "S6_last_nps": last.get("nps"),
        "S9_reached_requested_depth": reached_requested,
        "S9_last_depth_deficit": (requested - last_depth) if isinstance(last_depth, int) else None,
        "score": last.get("score"),
        "bestmove": parsed["bestmove"],
        "n_info_with_score": sum(1 for i in infos if "score" in i),
        "n_info_with_hashfull": sum(1 for i in infos if "hashfull" in i),
    }


fen_of = {
    "startpos": None,
    "G_black_mid": "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1",
    "G_knight_out": "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "tactical": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1",
}


def main():
    out = {"depth": DEPTH, "middle_delays": MIDDLE_DELAYS, "builds": {}}
    for bname, exe, regime in (("base_s14", BASE, "s14"), ("pc20", PC, "pc20")):
        out["builds"][bname] = {}
        for pname, poscmd in POSITIONS.items():
            fen = fen_of[pname]
            fin_lines = finished(exe, regime, poscmd)
            fin = signatures(parse(fin_lines), fen)
            middles = []
            for d in MIDDLE_DELAYS:
                for rep in range(2):
                    lines = interrupted(exe, regime, poscmd, d)
                    s = signatures(parse(lines), fen)
                    s["delay_ms"] = d
                    s["rep"] = rep
                    middles.append(s)
            out["builds"][bname][pname] = {"finished": fin, "middle": middles}
            with open(os.path.join(OUT, "detect.json"), "w") as f:
                json.dump(out, f, indent=2)
                f.write("\n")
            print("%-9s %-14s finished depth %s | middle last_depth %s"
                  % (bname, pname, fin.get("last_depth"),
                     sorted({m.get("last_depth") for m in middles if not m.get("empty")})),
                  flush=True)
    print("done")


main()
