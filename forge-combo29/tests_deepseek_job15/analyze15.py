#!/usr/bin/env python3
# Analyze a runner15 match json: ending counts, W-L-D for cand, Elo + 95% pair interval
# from complete pairs, node-time forfeits per side, mean node-ms (and nodes) per move per
# side (from the clock account: 10000 - left - 100*moves_of_that_side), mean moves per game.
import collections
import json
import math
import sys

def elo(s):
    if s <= 0 or s >= 1:
        return float("-inf") if s <= 0 else float("inf")
    return -400.0 * math.log10(1.0 / s - 1.0)

def main(path, out_path=None):
    games = json.load(open(path))
    ends = collections.Counter(g["end"] for g in games)
    w = l = d = 0
    forfeit = collections.Counter()
    w_spent = w_moves = b_spent = b_moves = 0
    plies = []
    pair_pts = collections.defaultdict(list)
    for gi, g in enumerate(games):
        plies.append(g["plies"])
        # cand is side A in swap=0 (plays black), side B in swap=1 (plays white)
        cand_is_white = g["swap"] == 1
        if g["end"] == "node-time forfeit":
            loser_side = "white" if g["winner"] == "black" else "black"
            cand_lost = (loser_side == "white") == cand_is_white
            forfeit["cand" if cand_lost else "base"] += 1
        if g["end"] == "mate":
            cand_win = (g["winner"] == "white") == cand_is_white
            pts = 1.0 if cand_win else 0.0
        elif g["end"] == "node-time forfeit":
            pts = 1.0 if not (("g['winner']=='black'" and False) or False) or False else (1.0 if not cand_lost else 0.0)
        else:
            pts = 0.5  # stalemate/threefold/fifty/insufficient/cap scored as draws (cap count disclosed)
        if g["end"] == "node-time forfeit":
            pts = 1.0 if not cand_lost else 0.0
        w += pts == 1.0
        l += pts == 0.0
        d += pts == 0.5
        pair_pts[gi // 2].append(pts)
        # clock account per side
        wmoves = (g["plies"] + 1) // 2 if g["swap"] == 0 else g["plies"] // 2
        bmoves = g["plies"] - wmoves
        # white side spent: 10000 - w_left - 100*wmoves (increment added after each move)
        w_spent += 10000 - g["w_ms_left"] - 100 * wmoves
        b_spent += 10000 - g["b_ms_left"] - 100 * bmoves
        w_moves += wmoves
        b_moves += bmoves
    qs = sorted(pair_pts)  # keys
    plist = [sum(pair_pts[k]) / 2.0 for k in sorted(pair_pts) if len(pair_pts[k]) == 2]
    incomplete = sum(1 for k in pair_pts if len(pair_pts[k]) != 2)
    n = w + l + d
    s = (w + d / 2.0) / n
    npr = len(plist)
    m = sum(plist) / npr
    var = sum((q - m) ** 2 for q in plist) / (npr - 1)
    e = math.sqrt(var) / math.sqrt(npr)
    ptn = collections.Counter(round(q * 4) for q in plist)
    line = (f"{path}: games={n} W-L-D={w}-{l}-{d} ends={dict(ends)} "
            f"forfeit cand/base={forfeit['cand']}/{forfeit['base']} "
            f"pairs={npr} incomplete={incomplete} Ptnml(0-2)={[ptn[i] for i in range(5)]} "
            f"myElo={elo(s):.2f} myInterval=[{elo(max(1e-9, m - 1.96 * e)):.2f}, {elo(min(1 - 1e-9, m + 1.96 * e)):.2f}] "
            f"mean_moves_per_game={sum(plies)/n:.1f} "
            f"cand_side: mean {w_spent/max(1,w_moves):.0f} node-ms/move ({w_spent*100/max(1,w_moves):.0f} nodes), "
            f"base_side: mean {b_spent/max(1,b_moves):.0f} node-ms/move ({b_spent*100/max(1,b_moves):.0f} nodes)")
    print(line)
    if out_path:
        open(out_path, "a").write(line + "\n")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
