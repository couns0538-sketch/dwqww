#!/usr/bin/env python3
"""recount_glm.py -- MY OWN recount of glmflash5's match numbers from its committed game lists.

Input: gamelist_M*.txt files of the form
    <n>|<white>|<black>|<result>|<ending>|<start FEN>
where <white>/<black> are "cand" or "base".

For every match I compute, from the file alone:
  * W-L-D from the CANDIDATE's point of view (W = cand wins, L = cand loses, D = draw)
  * pairs = games / 2, and the pair score histogram over the 5 possible pair scores
    (0, 0.5, 1, 1.5, 2 points for the candidate, i.e. 0/0.25/0.5/0.75/1 normalised)
  * m = mean normalised pair score; Elo = 400*log10(m/(1-m))
  * sd = 400/(ln10 * m(1-m)) * sqrt(var/pairs), var = variance of the normalised pair scores
    (the brief's formula), and the 95 % interval Elo +- 1.96*sd
  * the endings census, and the two identities their stats script prints
  * opening disjointness against every other match in the same job (by start FEN)

usage: recount_glm.py JOB_DIR [JOB_DIR ...]
"""
import glob
import json
import math
import os
import sys
from collections import Counter


def load(path):
    games = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            parts = line.split("|")
            if len(parts) < 6:
                continue
            try:
                n = int(parts[0])
            except ValueError:
                continue
            games.append({"n": n, "white": parts[1], "black": parts[2], "result": parts[3],
                          "ending": parts[4], "fen": "|".join(parts[5:])})
    return games


def cand_points(g):
    """candidate's score in this game: 1, 0.5 or 0."""
    if g["result"] == "1-0":
        return 1.0 if g["white"] == "cand" else 0.0
    if g["result"] == "0-1":
        return 1.0 if g["black"] == "cand" else 0.0
    return 0.5


def analyse(path):
    games = load(path)
    name = os.path.basename(path).replace("gamelist_", "").replace(".txt", "")
    W = L = D = 0
    pts = []
    for g in games:
        p = cand_points(g)
        pts.append(p)
        if p == 1.0:
            W += 1
        elif p == 0.5:
            D += 1
        else:
            L += 1
    # pair consecutive games (1&2, 3&4, ...) as the two colours of one opening
    pair_scores = []
    pair_fens = []
    for i in range(0, len(games) - 1, 2):
        a, b = games[i], games[i + 1]
        s = (cand_points(a) + cand_points(b)) / 2.0     # normalised to [0,1]
        pair_scores.append(s)
        pair_fens.append(a["fen"])
        if a["fen"] != b["fen"]:
            pair_fens[-1] = a["fen"] + " ||MISMATCHED_OPENING|| " + b["fen"]
    pairs = len(pair_scores)
    m = sum(pair_scores) / pairs if pairs else float("nan")
    if 0.0 < m < 1.0:
        elo = 400.0 * math.log10(m / (1.0 - m))
        d = 400.0 / (math.log(10.0) * m * (1.0 - m))
    else:
        elo, d = float("nan"), float("nan")
    mean = m
    var_n = sum((x - mean) ** 2 for x in pair_scores) / pairs if pairs else float("nan")
    var_n1 = sum((x - mean) ** 2 for x in pair_scores) / (pairs - 1) if pairs > 1 else float("nan")
    sd = d * math.sqrt(var_n / pairs) if pairs else float("nan")
    sd_n1 = d * math.sqrt(var_n1 / pairs) if pairs else float("nan")
    hist = Counter(round(s * 2, 1) for s in pair_scores)   # 0, .5, 1, 1.5, 2
    endings = Counter(g["ending"] for g in games)
    white_mates = sum(1 for g in games if g["result"] == "1-0")
    black_mates = sum(1 for g in games if g["result"] == "0-1")
    return {
        "match": name, "games": len(games), "pairs": pairs,
        "W": W, "L": L, "D": D,
        "elo": round(elo, 2),
        "sd_brief": round(sd, 3), "ci_brief": [round(elo - 1.96 * sd, 2), round(elo + 1.96 * sd, 2)],
        "sd_n1": round(sd_n1, 3), "ci_n1": [round(elo - 1.96 * sd_n1, 2), round(elo + 1.96 * sd_n1, 2)],
        "pair_hist_0_05_1_15_2": [hist.get(k, 0) for k in (0, 0.5, 1, 1.5, 2)],
        "endings": dict(sorted(endings.items())),
        "identity_endings": white_mates + black_mates == W + L,
        "identity_results": W + L + D == len(games),
        "pair_opening_mismatch": sum(1 for f in pair_fens if "MISMATCHED" in f),
        "first_fen": pair_fens[0] if pair_fens else None,
        "_fens": pair_fens,
    }


def main():
    dirs = sys.argv[1:]
    out = {}
    for d in dirs:
        files = sorted(glob.glob(os.path.join(d, "gamelist_M*.txt")))
        job = {}
        for f in files:
            r = analyse(f)
            job[r["match"]] = r
        # opening disjointness across the matches of this job
        names = sorted(job)
        overlaps = {}
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                sa, sb = set(job[a]["_fens"]), set(job[b]["_fens"])
                inter = sa & sb
                if inter:
                    overlaps["%s vs %s" % (a, b)] = len(inter)
        for r in job.values():
            r.pop("_fens", None)
        out[os.path.basename(os.path.normpath(d))] = {
            "matches": {k: job[k] for k in names},
            "opening_overlaps": overlaps,
            "openings_disjoint_across_matches": not overlaps,
        }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
