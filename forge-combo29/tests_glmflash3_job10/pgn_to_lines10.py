#!/usr/bin/env python3
# Job 10 per-game file: ONE line per game: round|white|black|result|how it ended|opening FEN.
# The PGN entries and fastchess's "Finished game N (...) : result {reason}" lines are both written
# in finish order; they are joined by position after checking the counts agree.
import re
import sys
import math

def parse_pgn(path):
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
    if headers:
        games.append(dict(headers))
    return games

def parse_reasons(path):
    out = []
    pat = re.compile(r'Finished game (\d+) \(([^)]+)\): (\S+) \{([^}]*)\}')
    for line in open(path):
        m = pat.search(line)
        if m:
            out.append((int(m.group(1)), m.group(2), m.group(3), m.group(4)))
    return out

def main():
    pgn, outf, cand = sys.argv[1], sys.argv[2], sys.argv[3]
    games = parse_pgn(pgn)
    fins = parse_reasons(outf)
    if len(games) != len(fins):
        print(f"WARNING: pgn games {len(games)} != finished lines {len(fins)}; joining the smaller count")
    n = min(len(games), len(fins))
    lines = []
    w = l = d = 0
    pairs = {}
    endings = {}
    for i in range(n):
        g, (_, pairing, result, reason) = games[i], fins[i]
        rnd, white, black = g.get('Round', '?'), g.get('White', '?'), g.get('Black', '?')
        fen = g.get('FEN', 'startpos')
        lines.append(f"{rnd}|{white}|{black}|{result}|{reason}|{fen}")
        endings[reason] = endings.get(reason, 0) + 1
        cw = white == cand
        pts = (1.0 if cw else 0.0) if result == '1-0' else \
              (0.0 if cw else 1.0) if result == '0-1' else 0.5
        if pts == 1: w += 1
        elif pts == 0: l += 1
        else: d += 1
        pairs.setdefault(rnd, []).append(pts)
    with open(pgn.rsplit('.', 1)[0] + '_games10.txt', 'w') as f:
        f.write('\n'.join(lines) + '\n')
    tot = w + l + d
    print(f"games={tot} W={w} L={l} D={d}")
    print("endings:")
    for reason, count in sorted(endings.items(), key=lambda kv: -kv[1]):
        print(f"  {count:5d}  {reason}")
    faults = sum(v for k, v in endings.items() if re.search(r'illegal|disconnect|crash|stall|time', k, re.I))
    print(f"faults={faults}")
    s = (w + d / 2) / tot if tot else 0
    f_elo = lambda x: -400 * math.log10(1 / x - 1) if 0 < x < 1 else (float('-inf') if x <= 0 else float('inf'))
    print(f"score={s:.4f} Elo={f_elo(s):.2f}")
    full = [v for v in pairs.values() if len(v) == 2]
    sc = [sum(v) / 2 for v in full]
    m = len(sc)
    if m > 1:
        mean = sum(sc) / m
        e = math.sqrt(sum((x - mean) ** 2 for x in sc) / (m - 1) / m)
        print(f"pairs={m} mean_pair={mean:.4f} se={e:.4f} pair95=[{f_elo(mean-1.96*e):.2f},{f_elo(mean+1.96*e):.2f}]")

if __name__ == '__main__':
    main()
