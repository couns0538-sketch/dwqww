#!/usr/bin/env python3
# glmflash2 job 1 helper. Reads a fastchess min PGN and prints:
#  - per-game line file content: round|white-engine|black-engine|result|opening FEN
#  - W-L-D for the engine named "cand"
#  - pentanomial pair counts (pairs are consecutive games with the same Round,
#    colors swapped, produced by -repeat)
#  - score for cand and a logistic Elo with error from the spread of pair scores
#    (independent of fastchess; used as a cross-check and for cut-short matches).
import re, sys, math

TAG = re.compile(r'\[(\w+) "(.*)"\]')

def parse(path):
    games, tags, has_moves = [], {}, False
    def close():
        nonlocal tags, has_moves
        if tags.get("Result") is not None:
            games.append({"round": tags.get("Round", "?"),
                          "white": tags.get("White", "?"),
                          "black": tags.get("Black", "?"),
                          "result": tags["Result"],
                          "fen": tags.get("FEN", "?")})
        tags, has_moves = {}, False
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('[Event '):
                close()
                continue
            m = TAG.match(line)
            if m:
                tags[m.group(1)] = m.group(2)
            else:
                has_moves = True
    close()
    return games

def cand_point(g, cand):
    if g["result"] == "1-0":
        return 1.0 if g["white"] == cand else 0.0
    if g["result"] == "0-1":
        return 0.0 if g["white"] == cand else 1.0
    return 0.5

def main(path, cand="cand"):
    games = parse(path)
    lines = ["%s|%s|%s|%s|%s" % (g["round"], g["white"], g["black"],
                                 g["result"], g["fen"]) for g in games]
    pts1 = [cand_point(g, cand) for g in games]
    w = sum(p == 1.0 for p in pts1)
    l = sum(p == 0.0 for p in pts1)
    d = sum(p == 0.5 for p in pts1)
    pent = [0] * 5
    pair_pts = []
    rounds = {}
    for g, p in zip(games, pts1):
        rounds.setdefault(g["round"], []).append(p)
    for r in sorted(rounds, key=lambda x: int(x) if str(x).isdigit() else 0):
        ps = rounds[r]
        if len(ps) != 2:
            continue  # round cut short by a killed match: no full pair
        p = ps[0] + ps[1]
        pent[int(p * 2)] += 1
        pair_pts.append(p / 2.0)
    n_games = len(games)
    n_pairs = len(pair_pts)
    score = (w + 0.5 * d) / n_games if n_games else float("nan")
    s = sum(pair_pts) / n_pairs if n_pairs else float("nan")
    if n_pairs > 1:
        var_s = sum((x - s) ** 2 for x in pair_pts) / (n_pairs - 1)
        se_s = math.sqrt(var_s / n_pairs)
    else:
        se_s = float("nan")
    if 0 < s < 1:
        elo = -400 * math.log10(1 / s - 1)
        se_elo = 400 / (math.log(10) * s * (1 - s)) * se_s
    else:
        elo, se_elo = float("inf") if s >= 1 else float("-inf"), float("nan")
    print("games=%d cand_W=%d cand_L=%d cand_D=%d" % (n_games, w, l, d))
    print("score=%.4f pairs=%d pentanomial=[%d,%d,%d,%d,%d]" %
          (score, n_pairs, pent[0], pent[1], pent[2], pent[3], pent[4]))
    print("my_elo=%.2f my_elo_err=%.2f (logistic score->Elo, pair-level error)"
          % (elo, se_elo))
    print("-- per-game lines follow (round|white|black|result|fen) --")
    try:
        for line in lines:
            print(line)
    except BrokenPipeError:
        pass

if __name__ == "__main__":
    main(sys.argv[1])
