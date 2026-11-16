import re, statistics, sys

# Per-move elapsed per (game, side) from a fastchess trace log.
# Structure discovered in the job-5 probe log: with concurrency 2, fastchess
# reuses ONE process per tournament slot across concurrent games; the same tid
# plays 'cand' in one game and 'base' in the other. Games on a tid are told
# apart by the moves-count resetting. Within one game a tid hosts ONE side
# only, so that side's n-th search is its n-th move of that game.

POS = re.compile(r"\[Engine\] \[([\d:.]+)\] <\s*\d+>\s+(\w+) <--- position fen .*?( moves.*)?$")
GO = re.compile(r"\[Engine\] \[([\d:.]+)\] <\s*\d+>\s+(\w+) <--- go ")
BM = re.compile(r"\[Engine\] \[([\d:.]+)\] <\s*\d+>\s+(\w+) ---> bestmove")

def tsec(stamp):
    h, m, s = stamp.split(":")
    s, us = s.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(us) / 1e6

def game_moves(path):
    # returns list of (name, game_key, move_index_within_game, elapsed_ms)
    out = []
    last_pos_moves = {}
    game_no = {}
    last_go = {}
    for line in open(path, errors="replace"):
        m = POS.search(line)
        if m:
            tid = None
            mt = re.search(r"<\s*(\d+)>", line)
            tid = mt.group(1)
            rest = m.group(2)
            mvpart = m.group(3) or ""
            n = len(mvpart.split()) if mvpart.strip() else 0
            prev = last_pos_moves.get(tid, -1)
            if n <= prev:
                game_no[tid] = game_no.get(tid, 0) + 1
            last_pos_moves[tid] = n
            continue
        mt = re.search(r"<\s*(\d+)>", line)
        if not mt:
            continue
        tid = mt.group(1)
        m = GO.search(line)
        if m:
            g = game_no.get(tid, 0)
            last_go[(tid, g)] = (tsec(m.group(1)), m.group(2))
            continue
        m = BM.search(line)
        if m:
            g = game_no.get(tid, 0)
            key = (tid, g)
            if key in last_go:
                ts, name = last_go.pop(key)
                # move index: per (tid,game) this side's search count
                out.append((name, g, 0, (tsec(m.group(1)) - ts) * 1000.0, tid))
    # assign per-(tid,game) running index
    from collections import defaultdict
    cnt = defaultdict(int)
    final = []
    for name, g, _, e, tid in out:
        cnt[(tid, g, name)] += 1
        final.append((name, f"t{tid}g{g}", cnt[(tid, g, name)], e))
    return final

def bucket(idx):
    if idx <= 20:
        return "1-20"
    if idx <= 40:
        return "21-40"
    return "41+"

path = sys.argv[1]
mv = game_moves(path)
names = sorted(set(n for n, _, _, _ in mv))
for side in names:
    xs = [(i, e) for n, gk, i, e in mv if n == side]
    es = sorted(e for _, e in xs)
    print(f"{side}: moves={len(xs)} games={len(set(gk for n,gk,_,_ in mv if n==side))} "
          f"mean={statistics.fmean(es):.1f} median={es[len(es)//2]:.1f} max={es[-1]:.1f}")
    for b in ("1-20", "21-40", "41+"):
        ys = sorted(e for i, e in xs if bucket(i) == b)
        if ys:
            print(f"  {side} own-move {b}: n={len(ys)} mean={statistics.fmean(ys):.1f} "
                  f"median={ys[len(ys)//2]:.1f} max={ys[-1]:.1f}")
