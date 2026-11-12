#!/usr/bin/env python
"""match_elo.py - JOB E (2026-11-11): result of a paired-opening match, recomputed from the PGN. Own code.

  match_elo.py --pgn games.pgn --cand cand [--out result.json]

Every opening is played twice with colours reversed (fastchess -games 2 -repeat); the two games share a Round tag.
The unit of analysis is the opening pair: the candidate's pair score is 0, 0.5, 1, 1.5 or 2 (pentanomial).
  score      = mean pair score / 2
  SE         = sample SD of (pair score / 2) / sqrt(pairs)          (pairs as the independent units)
  Elo        = -400 * log10(1 / score - 1); the 95 % interval is the Elo of score -+ 1.96 * SE
Pairs with a missing game are left out of the paired figures and counted separately. W/D/L, time forfeits and
other abnormal terminations are counted per game from the Result and Termination tags.
"""
import argparse
import json
import math
import re
from collections import Counter, defaultdict


def elo(score):
    score = min(max(score, 1e-6), 1 - 1e-6)
    return -400.0 * math.log10(1.0 / score - 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pgn", required=True)
    ap.add_argument("--cand", default="cand")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    games = []
    tags = {}
    with open(a.pgn, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.match(r'^\[(\w+) "(.*)"\]\s*$', line)
            if m:
                if m.group(1) == "Event" and tags:
                    games.append(tags)
                    tags = {}
                tags[m.group(1)] = m.group(2)
    if tags:
        games.append(tags)
    w = d = l = 0
    term = Counter()
    forfeits = Counter()
    rounds = defaultdict(list)
    unfinished = 0
    for g in games:
        res = g.get("Result", "*")
        white_is_cand = g.get("White") == a.cand
        if res == "1-0":
            s = 1.0 if white_is_cand else 0.0
        elif res == "0-1":
            s = 0.0 if white_is_cand else 1.0
        elif res == "1/2-1/2":
            s = 0.5
        else:
            unfinished += 1
            continue
        w += s == 1.0
        d += s == 0.5
        l += s == 0.0
        t = g.get("Termination", "normal")
        term[t] += 1
        if t.lower() not in ("normal", "adjudication", ""):
            loser = (g.get("Black") if res == "1-0" else g.get("White")) if res != "1/2-1/2" else "draw"
            forfeits[f"{t}: {loser}"] += 1
        rounds[g.get("Round", "?")].append(s)
    pairs = [sum(v) for v in rounds.values() if len(v) == 2]
    odd = sum(1 for v in rounds.values() if len(v) != 2)
    n = len(pairs)
    penta = [sum(1 for p in pairs if p == x) for x in (0.0, 0.5, 1.0, 1.5, 2.0)]
    out = {"pgn": a.pgn, "candidate": a.cand, "games": w + d + l, "unfinished_games": unfinished, "W": int(w), "D": int(d),
           "L": int(l), "score_all_games": (w + 0.5 * d) / max(1, w + d + l), "terminations": dict(term),
           "abnormal_terminations": dict(forfeits), "pairs": n, "rounds_without_two_games": odd, "pentanomial_0_to_2": penta}
    if n > 1:
        xs = [p / 2.0 for p in pairs]
        mean = sum(xs) / n
        var = sum((x - mean) ** 2 for x in xs) / (n - 1)
        se = math.sqrt(var / n)
        out.update({"pair_score": mean, "pair_se": se, "elo": elo(mean), "elo_95_low": elo(mean - 1.96 * se),
                    "elo_95_high": elo(mean + 1.96 * se), "los": 0.5 * (1.0 + math.erf((mean - 0.5) / (se * math.sqrt(2.0)))) if se > 0 else None,
                    "method": "pentanomial: opening pairs as units, normal 95 % interval on the mean pair score, mapped to Elo"})
        # trinomial figure for comparison only (treats games as independent; too narrow or too wide with paired openings)
        tot = w + d + l
        s = (w + 0.5 * d) / tot
        var3 = (w * (1 - s) ** 2 + d * (0.5 - s) ** 2 + l * s ** 2) / tot
        se3 = math.sqrt(var3 / tot)
        out["trinomial_for_comparison"] = {"elo": elo(s), "elo_95_low": elo(s - 1.96 * se3), "elo_95_high": elo(s + 1.96 * se3)}
    print(json.dumps(out, indent=1, sort_keys=True))
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
