#!/usr/bin/env python3
"""recount_pools.py -- MY OWN pooling of glmflash5's matches, and the independence question.

Reads the gamelists of several job folders, pools the pairs of the matches the report names,
and reports:
  * pairs, pooled Elo (from the pooled normalised pair score), and the 95 % interval by the
    brief's formula (sd = 400/(ln10 m(1-m)) * sqrt(var/pairs)) AND by the naive formula that
    treats the pool as one long match (same thing, recomputed from the raw pair scores);
  * the OPENING OVERLAP between every pair of matches in the pool -- if two matches play the
    same openings, their pairs are not independent and the pooled interval is too narrow.

usage: recount_pools.py
"""
import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util

spec = importlib.util.spec_from_file_location(
    "rc", os.path.join(os.path.dirname(os.path.abspath(__file__)), "recount_glm.py"))
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)

JOBS = {
    "job22": "/home/ubuntu/work/glm22/forge-combo29/tests_glmflash5_job22",
    "job23": "/home/ubuntu/work/glm23/forge-combo29/tests_glmflash5_job23",
    "job24": "/home/ubuntu/work/glm24/forge-combo29/tests_glmflash5_job24",
}
POOLS = {
    "variant@2000 (M49+M51+M52+M55+M56)": ["M49", "M51", "M52", "M55", "M56"],
    "CED8alone@2000 (M53+M57+M58)": ["M53", "M57", "M58"],
    "variant@20000 (M54+M59)": ["M54", "M59"],
}


def pair_scores(path):
    games = rc.load(path)
    out, fens = [], []
    for i in range(0, len(games) - 1, 2):
        s = (rc.cand_points(games[i]) + rc.cand_points(games[i + 1])) / 2.0
        out.append(s)
        fens.append(games[i]["fen"])
    return out, fens


def elo_ci(scores):
    n = len(scores)
    m = sum(scores) / n
    if not (0.0 < m < 1.0):
        return None
    elo = 400.0 * math.log10(m / (1.0 - m))
    d = 400.0 / (math.log(10.0) * m * (1.0 - m))
    var = sum((x - m) ** 2 for x in scores) / n
    sd = d * math.sqrt(var / n)
    return {"pairs": n, "mean_norm": round(m, 5), "elo": round(elo, 2),
            "sd": round(sd, 3),
            "ci95": [round(elo - 1.96 * sd, 2), round(elo + 1.96 * sd, 2)]}


def main():
    files = {}
    for job, d in JOBS.items():
        for p in sorted(glob.glob(os.path.join(d, "gamelist_M*.txt"))):
            files[os.path.basename(p).replace("gamelist_", "").replace(".txt", "")] = p
    out = {"matches_available": sorted(files), "pools": {}}
    for label, names in POOLS.items():
        missing = [n for n in names if n not in files]
        if missing:
            out["pools"][label] = {"missing_gamelists": missing}
            continue
        scores, fensets, per = [], {}, {}
        for n in names:
            s, f = pair_scores(files[n])
            scores += s
            fensets[n] = set(f)
            per[n] = elo_ci(s)
        overlaps = {}
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                inter = fensets[a] & fensets[b]
                if inter:
                    overlaps["%s vs %s" % (a, b)] = len(inter)
        out["pools"][label] = {
            "pooled": elo_ci(scores),
            "per_match": per,
            "opening_overlaps": overlaps,
            "openings_disjoint": not overlaps,
            "sum_of_match_pairs": sum(per[n]["pairs"] for n in names),
        }
    print(json.dumps(out, indent=1))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "pools_result.json"), "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
