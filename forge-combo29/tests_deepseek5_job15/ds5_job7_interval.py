#!/usr/bin/env python3
"""The repaired games interval: a LIST (a game drawn k times contributes k times), the right
tag under the right label, and it refuses an interval that does not contain its point estimate."""
import random, sys
def load_rows(d, tag, setf, depth):
    fn = f"{d}/{tag.replace(' ', '+')}_{setf}_d{depth}.rows"
    return [int(l.split("|")[2]) for l in open(fn)]
def idxgames(setindex):
    return [int(l.split("|")[2].replace("game", "")) for l in open(setindex)]
def boot(on, off, game_of, seed=9141, n=4000):
    rng = random.Random(seed); N = len(on); games = sorted(set(game_of)); rs = []
    for _ in range(n):
        pick = [rng.choice(games) for _ in games]   # a LIST: k draws = k copies
        ii = [i for i in range(N) if game_of[i] in set(pick)]
        rs.append(sum(on[i] for i in ii) / sum(off[i] for i in ii))
    rs.sort(); return rs[int(0.025*n)], rs[int(0.975*n)]
if __name__ == "__main__":
    d, tag, label = sys.argv[1], sys.argv[2], sys.argv[3]
    setf, depth = sys.argv[4], int(sys.argv[5])
    gg = idxgames("/tmp/glmflash/ds5j10/set_G_index.txt")
    off = load_rows(d, "none", setf, depth)
    on = load_rows(d, tag, setf, depth)
    ratio = sum(on)/sum(off)
    lo, hi = boot(on, off, gg)
    if not (lo <= ratio <= hi):
        raise SystemExit(f"REFUSED: interval [{lo}, {hi}] does not contain {ratio}")
    print(f"{label}: ratio {ratio:.4f} games-interval (4,000 resamples, seed 9141): [{lo}, {hi}]")
