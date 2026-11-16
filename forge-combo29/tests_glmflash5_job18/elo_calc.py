#!/usr/bin/env python3
"""Elo from fastchess PGN, pentanomial over opening pairs."""
import sys, re, json

def parse_pgn(fn):
    games = []
    with open(fn) as f:
        game = {}
        for line in f:
            line = line.strip()
            if line.startswith('[Result "'):
                game['result'] = line.split('"')[1]
            if line.startswith('[White "'):
                game['white'] = line.split('"')[1]
            if line.startswith('[Black "'):
                game['black'] = line.split('"')[1]
            if line == '' and game:
                if 'result' in game and 'white' in game:
                    games.append(game)
                game = {}
    return games

def elo_score(wins, losses, draws):
    games = wins + losses + draws
    if games == 0: return 0, [0, 0]
    score = (wins + 0.5 * draws) / games
    # Elo from score
    if score >= 1.0: elo = 800
    elif score <= 0.0: elo = -800
    else: elo = -400 * (10 ** (-score / 400) - 1) / (1 - 10 ** (-score / 400)) if score != 0.5 else 0
    import math
    n = games
    # approximate 95% interval using the binomial standard error
    p = score
    se = math.sqrt(max(p * (1 - p), 0.000001) / n)
    elo_se = 400 / math.log(10) * se * 1.96
    return elo, [round(elo - elo_se, 2), round(elo + elo_se, 2)]

def pentanomial(pairs):
    # pairs: list of (result1, result2) for each opening pair
    counts = [0] * 5  # LL, LD, LW/WL(D), WD, WW from the pair's perspective
    for r1, r2 in pairs:
        s1 = 1 if r1 == '1-0' else (0.5 if r1 == '1/2-1/2' else 0)
        s2 = 1 if r2 == '1-0' else (0.5 if r2 == '1/2-1/2' else 0)
        tot = s1 + s2
        if tot == 0: counts[0] += 1      # LL
        elif tot == 0.5: counts[1] += 1  # LD or DL
        elif tot == 1.0: counts[2] += 1  # LW or WL (or DD)
        elif tot == 1.5: counts[3] += 1  # WD or DW
        else: counts[4] += 1             # WW
    return counts

if __name__ == '__main__':
    fn = sys.argv[1]
    cand_name = sys.argv[2] if len(sys.argv) > 2 else 'cand'
    games = parse_pgn(fn)
    wins = losses = draws = 0
    pairs = []
    i = 0
    while i + 1 < len(games):
        g1, g2 = games[i], games[i + 1]
        # determine the result from the candidate's perspective
        def score_for(g, name):
            if g['result'] == '1-0':
                return 1 if g['white'] == name else 0
            elif g['result'] == '0-1':
                return 1 if g['black'] == name else 0
            return 0.5
        s1 = score_for(g1, cand_name)
        s2 = score_for(g2, cand_name)
        if s1 == 1: wins += 1
        elif s1 == 0: losses += 1
        else: draws += 1
        if s2 == 1: wins += 1
        elif s2 == 0: losses += 1
        else: draws += 1
        # the pair results (from the candidate's perspective)
        r1 = '1-0' if s1 == 1 else ('0-1' if s1 == 0 else '1/2-1/2')
        r2 = '1-0' if s2 == 1 else ('0-1' if s2 == 0 else '1/2-1/2')
        pairs.append((r1, r2))
        i += 2
    counts = pentanomial(pairs)
    elo, interval = elo_score(wins, losses, draws)
    print(f"wins + losses + draws = {wins + losses + draws}")
    print(f"pentanomial: {counts} (sum {sum(counts)})")
    print(f"Elo: {elo:.2f} [{interval[0]}, {interval[1]}]")
