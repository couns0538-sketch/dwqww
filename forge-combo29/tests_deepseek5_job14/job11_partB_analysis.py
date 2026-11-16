#!/usr/bin/env python3
"""The two-interval analysis (positions and games) used in jobs 11 and 14.
The games interval: resample len(games) games WITH replacement from the games that have
positions in the set; every drawn game contributes ALL its positions. 4,000 resamples."""
import random, collections, json
def load_rows(d, tag, setf, depth):
    fn = f"{d}/{tag.replace(' ', '+')}_{setf}_d{depth}.rows"
    return [int(l.split("|")[2]) for l in open(fn)]
def load_cnt_rows(fn):
    return [int(l.split("|")[2]) for l in open(fn).readlines()[1:]]
def idxgames(setindex):
    return [int(l.split("|")[2].replace("game", "")) for l in open(setindex)]
def boot(on, off, game_of, seed=9141, n=4000, mode="game"):
    rng = random.Random(seed); N = len(on); games = sorted(set(game_of)); rs = []
    for _ in range(n):
        if mode == "pos":
            ii = [rng.randrange(N) for _ in range(N)]
        else:
            pick = set(rng.choice(games) for _ in games)
            ii = [i for i in range(N) if game_of[i] in pick]
        rs.append(sum(on[i] for i in ii) / sum(off[i] for i in ii))
    rs.sort(); return round(rs[int(0.025*n)], 4), round(rs[int(0.975*n)], 4)
if __name__ == "__main__":
    gg = idxgames("/tmp/glmflash/ds5j10/set_G_index.txt")
    off = load_rows("/tmp/glmflash/ds5j10", "none", "set_G.epd", 12)
    on = load_rows("/tmp/glmflash/ds5j10", "LmrDeeperShallower true", "set_G.epd", 12)
    lo, hi = boot(on, off, gg)
    print(f"shal on G depth 12, games interval (4,000 resamples, seed 9141): [{lo}, {hi}]")
