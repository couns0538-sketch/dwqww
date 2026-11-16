#!/usr/bin/env python3
"""check_15f35_clock.py <exe> <outdir> [--settings PC20] [--games N] [--maxplies P]

Independent check of seat 15's 15-F35: at the owner's real control (6 s + 0.06/move, `wtime 6000
btime 6000 winc 60 binc 60`), does the clock path actually DRAIN toward a forfeit?

Their claim, in their numbers: median 105 ms used per move against a 60 ms increment -> ~73 ms net
drain per move; 6,000 / 73 is about 82 moves; their 30-game set reached a 160-ply cap with only 174 ms
left; and the per-move cost falling in the endgame (217 -> 83 ms) is the only reason it did not forfeit.
"A game reaching ~165 plies would have forfeited."

My harness, written from that sentence (not copying theirs):
  - self-play from a start position, PC build, PC20, Threads 1, Hash 16
  - a REAL clock per side, decremented by the measured wall time of each move, incremented by 60 ms
    after each move (Fischer), with a hard forfeit if a side's clock goes <= 0
  - the engine's own limits come from `wtime/btime/winc/binc`, i.e. the same command the match program uses
  - I record, per move: side, wall ms, nodes, depth, remaining clock for the mover after the move
  - I report median/p99 wall, the net drain per move, the ply count where each side's clock would reach
    zero at the measured median, and whether any game actually forfeits

A control run at a POSITIVE-sum control (6 s + 0.5 s increment) shows the harness can see a clock that does
NOT drain, so "drain" is not just my arithmetic.
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
         "MateAlphaGuard true", "OwnBook false"]


class Engine:
    def __init__(self, exe, settings):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.s("uci")
        lines, ok = self.until(lambda x: x.strip() == "uciok")
        if not ok:
            raise RuntimeError("no uciok")
        adv = {m.group(1) for m in (re.match(r"option name (.+?) type ", l) for l in lines) if m}
        for item in settings:
            name, _, val = item.rpartition(" ")
            if name not in adv:
                raise RuntimeError("option %r not advertised" % name)
            self.s("setoption name %s value %s" % (name, val))
        self.s("ucinewgame"); self.s("isready")
        self.until(lambda x: x.strip() == "readyok")

    def s(self, line):
        self.p.stdin.write(line + "\n"); self.p.stdin.flush()

    def until(self, pred, tmo=120):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = self.p.stdout.readline()
            if not ln:
                break
            y = ln.rstrip("\n"); out.append(y)
            if pred(y):
                return out, True
        return out, False

    def move(self, moves_uci, wtime, btime, winc, binc, timeout=60):
        pos = "position startpos"
        if moves_uci:
            pos += " moves " + " ".join(moves_uci)
        self.s(pos); self.s("isready")
        if not self.until(lambda x: x.strip() == "readyok")[1]:
            raise RuntimeError("no readyok before go")
        cmd = "go wtime %d btime %d winc %d binc %d" % (wtime, btime, winc, binc)
        t0 = time.monotonic()
        self.s(cmd)
        lines, ok = self.until(lambda x: x.startswith("bestmove"), tmo=timeout)
        wall = (time.monotonic() - t0) * 1000.0
        if not ok:
            return {"timeout": True, "wall_ms": wall, "bestmove": None}
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        infos = [l for l in lines if l.startswith("info depth")]
        last = infos[-1] if infos else ""
        n = re.search(r"nodes (\d+)", last)
        d = re.search(r"depth (\d+)", last)
        return {"timeout": False, "wall_ms": wall, "bestmove": bm,
                "nodes": int(n.group(1)) if n else None,
                "depth": int(d.group(1)) if d else None,
                "info_lines": len(infos)}

    def close(self):
        try:
            self.s("quit"); self.p.wait(timeout=15)
        except Exception:
            self.p.kill()


def play_game(exe, settings, start_fen_moves, wtime0, btime0, winc, binc, maxplies, hard_cap_ms=30000):
    """Self-play with a real decremented clock. Returns the move log and how the game ended."""
    e = Engine(exe, settings)
    moves = []
    w, b = wtime0, btime0
    log = []
    try:
        for ply in range(maxplies):
            white = (ply % 2 == 0)
            t_w, t_b = (w, b) if white else (w, b)
            r = e.move(moves, max(1, int(w)), max(1, int(b)), winc, binc, timeout=hard_cap_ms / 1000)
            if r["timeout"]:
                return {"ended": "HANG", "ply": ply, "log": log, "moves": moves,
                        "white_left": w, "black_left": b}
            if r["bestmove"] in (None, "0000"):
                return {"ended": "NO_MOVE", "ply": ply, "log": log, "moves": moves,
                        "white_left": w, "black_left": b}
            spent = r["wall_ms"]
            # spend, then add the increment for the side that moved
            if white:
                w = w - spent + winc
            else:
                b = b - spent + binc
            log.append({"ply": ply, "side": "w" if white else "b", "wall_ms": round(spent, 1),
                        "nodes": r["nodes"], "depth": r["depth"], "move": r["bestmove"],
                        "white_left": round(w, 1), "black_left": round(b, 1)})
            moves.append(r["bestmove"])
            if w <= 0:
                return {"ended": "WHITE_FORFEIT", "ply": ply, "log": log, "moves": moves,
                        "white_left": w, "black_left": b}
            if b <= 0:
                return {"ended": "BLACK_FORFEIT", "ply": ply, "log": log, "moves": moves,
                        "white_left": w, "black_left": b}
            # the other side's clock is unchanged this ply
            if white:
                t_b = b
            else:
                t_w = w
        return {"ended": "PLY_CAP", "ply": maxplies, "log": log, "moves": moves,
                "white_left": w, "black_left": b}
    finally:
        e.close()


def summarise(runs, label):
    walls, drains = [], []
    for g in runs:
        for row in g["log"]:
            walls.append(row["wall_ms"])
        # net drain per MOVE for each side, from the log's own clock columns
        pass
    out = {"label": label, "games": len(runs),
           "endings": {}, "median_wall_ms": None, "p99_wall_ms": None}
    for g in runs:
        out["endings"][g["ended"]] = out["endings"].get(g["ended"], 0) + 1
    if walls:
        walls.sort()
        out["median_wall_ms"] = round(statistics.median(walls), 1)
        out["p99_wall_ms"] = round(walls[int(0.99 * (len(walls) - 1))], 1)
        out["max_wall_ms"] = round(walls[-1], 1)
        out["n_moves"] = len(walls)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--settings", default="PC20", choices=["PC20", "S14", "none"])
    ap.add_argument("--games", type=int, default=4)
    ap.add_argument("--maxplies", type=int, default=200)
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    settings = {"none": ["Hash 16", "Threads 1", "OwnBook false"],
                "S14": ["Hash 16", "Threads 1", "OwnBook false"] + S14,
                "PC20": ["Hash 16", "Threads 1"] + S14 + PC20X}[a.settings]

    tests = [("owner 6s+0.06", 6000, 6000, 60, 60),
             ("control 6s+0.5 (positive sum)", 6000, 6000, 500, 500)]
    out = {"exe": exe, "settings": a.settings, "threads": 1, "maxplies": a.maxplies,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "runs": {}}

    for label, wt, bt, wi, bi in tests:
        runs = []
        for g in range(a.games):
            r = play_game(exe, settings, [], wt, bt, wi, bi, a.maxplies)
            r["game"] = g
            runs.append(r)
            print("%-30s game %d: ended %-14s at ply %-4d clocks w=%.0f b=%.0f"
                  % (label, g, r["ended"], r["ply"], r["white_left"], r["black_left"]))
        s = summarise(runs, label)
        s["increment_ms"] = wi
        s["runs"] = runs
        out["runs"][label] = s
        inc = wi
        if s["median_wall_ms"]:
            s["net_drain_per_move_ms"] = round(s["median_wall_ms"] - inc, 1)
            if inc and s["median_wall_ms"] > inc:
                s["plies_to_zero_at_median"] = int(6000 / (s["median_wall_ms"] - inc))
            else:
                s["plies_to_zero_at_median"] = None
        print("   -> %s: n=%s median %s ms p99 %s ms max %s; net drain %s ms/move; "
              "plies to zero at median: %s"
              % (label, s["n_moves"], s["median_wall_ms"], s["p99_wall_ms"], s["max_wall_ms"],
                 s.get("net_drain_per_move_ms"), s.get("plies_to_zero_at_median")))

    with open(os.path.join(a.outdir, "check_15f35.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote", os.path.join(a.outdir, "check_15f35.json"))


if __name__ == "__main__":
    main()
