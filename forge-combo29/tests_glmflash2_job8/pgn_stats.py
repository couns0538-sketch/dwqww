#!/usr/bin/env python3
# glmflash2 job 1/2 helper. Reads one or more fastchess min PGNs and prints:
#  - per-game line file content: round|white-engine|black-engine|result|opening FEN
#  - W-L-D for the engine named "cand" (pooled over all files)
#  - pentanomial pair counts (pairs are the two games of one [Round] tag; rounds
#    with fewer than 2 games are skipped, so a SIGINT-cut match loses only the
#    unfinished round)
#  - score for cand, Elo = -400*log10(1/s-1) where s = mean pair points / 2, and
#    the 95% pair interval m +/- 1.96*e (e = standard error of s over pairs).
# Multiple PGNs are pooled: pair counts add, the interval is computed on the
# pooled set of pairs. Validated against fastchess on controls 1 and 2 of job 1
# (identical W-L-D, pentanomial and Elo point estimate).
import re, sys, math

TAG = re.compile(r'\[(\w+) "(.*)"\]')

def parse(path, idx=0):
    games, tags = [], {}
    def close():
        nonlocal tags
        if tags.get("Result") is not None:
            games.append({"file": idx,
                          "round": tags.get("Round", "?"),
                          "white": tags.get("White", "?"),
                          "black": tags.get("Black", "?"),
                          "result": tags["Result"],
                          "fen": tags.get("FEN", "?")})
        tags = {}
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
    close()
    return games

def cand_point(g, cand):
    if g["result"] == "1-0":
        return 1.0 if g["white"] == cand else 0.0
    if g["result"] == "0-1":
        return 0.0 if g["white"] == cand else 1.0
    return 0.5

def main(paths, cand="cand"):
    games = []
    for i, p in enumerate(paths):
        games.extend(parse(p, i))
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
        rounds.setdefault((g["file"], g["round"]), []).append(p)
    for r in sorted(rounds, key=lambda x: int(x) if str(x).isdigit() else 0):
        ps = rounds[r]
        if len(ps) != 2:
            continue
        p = ps[0] + ps[1]
        pent[int(p * 2)] += 1
        pair_pts.append(p / 2.0)
    n_games = len(games)
    n_pairs = len(pair_pts)
    score = (w + 0.5 * d) / n_games if n_games else float("nan")
    s = sum(pair_pts) / n_pairs if n_pairs else float("nan")
    if n_pairs > 1:
        var_s = sum((x - s) ** 2 for x in pair_pts) / (n_pairs - 1)
        e = math.sqrt(var_s / n_pairs)
    else:
        e = float("nan")
    if 0 < s < 1:
        elo = -400 * math.log10(1 / s - 1)
        s_lo, s_hi = s - 1.96 * e, s + 1.96 * e
        lo_elo = -400 * math.log10(1 / s_lo - 1) if s_lo > 0 else float("-inf")
        hi_elo = -400 * math.log10(1 / s_hi - 1) if s_hi < 1 else float("inf")
        err95 = max(elo - lo_elo, hi_elo - elo) if e == e else float("nan")
    else:
        elo, err95 = float("inf") if s >= 1 else float("-inf"), float("nan")
    print("games=%d cand_W=%d cand_L=%d cand_D=%d" % (n_games, w, l, d))
    print("score=%.4f pairs=%d pentanomial=[%d,%d,%d,%d,%d]" %
          (score, n_pairs, pent[0], pent[1], pent[2], pent[3], pent[4]))
    print("my_elo=%.2f my_err95=%.2f (Elo from mean pair score; 95%% pair interval)"
          % (elo, err95))
    print("-- per-game lines follow (round|white|black|result|fen) --")
    try:
        for line in lines:
            print(line)
    except BrokenPipeError:
        pass

if __name__ == "__main__":
    main(sys.argv[1:])
