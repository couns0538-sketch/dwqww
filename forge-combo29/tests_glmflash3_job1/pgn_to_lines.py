#!/usr/bin/env python3
# Parse a fastchess min=true PGN into one line per game:
#   round|white|black|result|opening FEN
# and print the score / pair-interval statistics computed from those lines.
# Pair = the two games of one opening with colours reversed (same Round header);
# pair score = (cand points in the two games) / 2 in {0, 0.25, 0.5, 0.75, 1}.
import re
import sys
import math

def parse(path):
    games = []
    headers = {}
    for line in open(path):
        line = line.rstrip('\n')
        if line.startswith('['):
            m = re.match(r'\[(\w+)\s+"(.*)"\]\s*$', line)
            if m:
                headers[m.group(1)] = m.group(2)
            continue
        if line.strip() == '':
            if headers:
                games.append(dict(headers))
                headers = {}
            continue
        # movetext line: the game ends at the blank line that follows
    if headers:
        games.append(dict(headers))
    return games

def main():
    path = sys.argv[1]
    cand_name = sys.argv[2] if len(sys.argv) > 2 else 'cand'
    games = parse(path)
    out_lines = []
    pairs = {}
    w = l = d = 0
    for g in games:
        rnd = g.get('Round', '?')
        white, black = g.get('White', '?'), g.get('Black', '?')
        result = g.get('Result', '?')
        fen = g.get('FEN', 'startpos')
        out_lines.append(f"{rnd}|{white}|{black}|{result}|{fen}")
        cand_white = white == cand_name
        if result == '1-0':
            pts = 1.0 if cand_white else 0.0
        elif result == '0-1':
            pts = 0.0 if cand_white else 1.0
        elif result == '1/2-1/2':
            pts = 0.5
        else:
            pts = None  # unfinished game: counted in the file, excluded from stats
        if pts is not None:
            if pts == 1.0:
                w += 1
            elif pts == 0.0:
                l += 1
            else:
                d += 1
            pairs.setdefault(rnd, []).append(pts)
    n = w + l + d
    with open(path.rsplit('.', 1)[0] + '_games.txt', 'w') as f:
        f.write('\n'.join(out_lines) + '\n')

    print(f"games={n} (parsed={len(games)}) W={w} L={l} D={d}")
    if n == 0:
        return
    s = (w + d / 2) / n
    if 0 < s < 1:
        elo = -400 * math.log10(1 / s - 1)
        print(f"score={s:.4f} Elo={elo:.2f}")
    else:
        print(f"score={s:.4f} Elo=+-inf (score at boundary)")

    scores = sorted(sum(v) / 2 for v in pairs.values())
    m = len(scores)
    if m > 1:
        mean = sum(scores) / m
        var = sum((x - mean) ** 2 for x in scores) / (m - 1)
        e = math.sqrt(var / m)
        lo, hi = mean - 1.96 * e, mean + 1.96 * e
        def to_elo(x):
            return -400 * math.log10(1 / x - 1) if 0 < x < 1 else float('-inf') if x <= 0 else float('inf')
        print(f"pairs={m} mean_pair_score={mean:.4f} se={e:.4f} "
              f"pairElo95=[{to_elo(lo):.2f},{to_elo(hi):.2f}]"
              f"  (mean score {mean:.4f} -> {to_elo(mean):.2f})")
    else:
        print(f"pairs={m} (too few for a pair interval)")

if __name__ == '__main__':
    main()
