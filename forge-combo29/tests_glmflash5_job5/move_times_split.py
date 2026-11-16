import re, statistics, sys

# Per-move elapsed per engine from a fastchess trace log, with move buckets.
# elapsed = bestmove stamp - last unmatched 'go' stamp of the same engine.
# move index = the engine's own move counter (its n-th 'go').

GO = re.compile(r"\[Engine\] \[([\d:.]+)\] <\s*\d+>\s+(\w+) <--- go ")
BM = re.compile(r"\[Engine\] \[([\d:.]+)\] <\s*\d+>\s+(\w+) ---> bestmove")

def tsec(stamp):
    h, m, s = stamp.split(":")
    s, us = s.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(us) / 1e6

def moves(path):
    last_go = {}
    counter = {}
    out = []
    for line in open(path, errors="replace"):
        m = GO.search(line)
        if m:
            eng = m.group(2)
            counter[eng] = counter.get(eng, 0) + 1
            last_go[eng] = (tsec(m.group(1)), counter[eng])
            continue
        m = BM.search(line)
        if m and m.group(2) in last_go:
            ts, idx = last_go.pop(m.group(2))
            out.append((m.group(2), idx, (tsec(m.group(1)) - ts) * 1000.0))
    return out

def bucket(idx):
    if idx <= 20:
        return "1-20"
    if idx <= 40:
        return "21-40"
    return "41+"

path = sys.argv[1]
mv = moves(path)
for side in ("cand", "base"):
    xs = [(i, e) for n, i, e in mv if n == side]
    if not xs:
        continue
    es = sorted(e for _, e in xs)
    print(f"{side}: moves={len(xs)} mean={statistics.fmean(es):.1f} median={es[len(es)//2]:.1f} max={es[-1]:.1f}")
    for b in ("1-20", "21-40", "41+"):
        ys = sorted(e for i, e in xs if bucket(i) == b)
        if ys:
            print(f"  {side} moves {b}: n={len(ys)} mean={statistics.fmean(ys):.1f} "
                  f"median={ys[len(ys)//2]:.1f} max={ys[-1]:.1f}")
