#!/usr/bin/env python3
# Own Elo + pair interval from a compact per-game log (round, white, fen, result).
# Fable's formula: s = (wins + draws/2) / games, Elo = -400*log10(1/s - 1);
# error from the PAIR scores (0, 0.5, 1, 1.5, 2 divided by 2): mean m, standard
# error e = sample_stdev/sqrt(n_pairs), bounds converted the same way.
import math
import sys

def read_games(path):
    games = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 4:
                continue
            games.append(parts)
    return games

def elo_from_score(s):
    if s <= 0 or s >= 1:
        return float("-inf") if s <= 0 else float("inf")
    return -400.0 * math.log10(1.0 / s - 1.0)

def main(path, out_path=None):
    games = read_games(path)
    rounds = {}
    w = l = d = 0
    for r, white, _fen, res in games:
        rounds.setdefault(r, []).append((white, res))
        if res == "1/2-1/2":
            d += 1
        elif (res == "1-0") == (white == "cand"):
            w += 1
        else:
            l += 1
    qs = []
    for r, gs in rounds.items():
        pts = 0.0
        for white, res in gs:
            if res == "1/2-1/2":
                pts += 0.5
            elif (res == "1-0") == (white == "cand"):
                pts += 1.0
        qs.append(pts / 2.0)
    n = w + l + d
    npr = len(qs)
    s = (w + d / 2.0) / n
    elo = elo_from_score(s)
    m = sum(qs) / npr
    if npr > 1:
        var = sum((q - m) ** 2 for q in qs) / (npr - 1)
        e = math.sqrt(var) / math.sqrt(npr)
    else:
        e = None
    if e is not None and e > 0 and 0 < m - 1.96 * e and m + 1.96 * e < 1:
        lo = elo_from_score(m - 1.96 * e)
        hi = elo_from_score(m + 1.96 * e)
    elif e is not None and e > 0:
        lo = elo_from_score(max(1e-9, m - 1.96 * e))
        hi = elo_from_score(min(1 - 1e-9, m + 1.96 * e))
    else:
        lo = hi = float("nan")
    ptn = [0] * 5
    for q in qs:
        ptn[min(4, max(0, int(round(q * 4))))] += 1
    if e is not None:
        line = (f"{path}: games={n} W-L-D={w}-{l}-{d} pairs={npr} "
                f"Ptnml(0-2)={[*ptn]} s={s:.5f} "
                f"myElo={elo:.2f} myInterval=[{lo:.2f}, {hi:.2f}] (m={m:.5f}, e={e:.5f})")
    else:
        line = (f"{path}: games={n} W-L-D={w}-{l}-{d} pairs={npr} "
                f"Ptnml(0-2)={[*ptn]} s={s:.5f} "
                f"myElo={elo:.2f} myInterval=[n/a, n/a] (m={m:.5f}, e=n/a, single pair)")
    print(line)
    if out_path:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
