import re, statistics

# Per-move elapsed per engine from a fastchess trace log:
# elapsed = bestmove stamp - the 'go' stamp of the same engine's last unmatched go.

GO = re.compile(r"\[Engine\] \[([\d:.]+)\] <\s*\d+>\s+(\w+) <--- go ")
BM = re.compile(r"\[Engine\] \[([\d:.]+)\] <\s*\d+>\s+(\w+) ---> bestmove")

def tsec(stamp):
    h, m, s = stamp.split(":")
    s, us = s.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(us) / 1e6

def moves(path):
    last_go = {}
    out = []
    for line in open(path, errors="replace"):
        m = GO.search(line)
        if m:
            last_go[m.group(2)] = tsec(m.group(1))
            continue
        m = BM.search(line)
        if m and m.group(2) in last_go:
            out.append((m.group(2), (tsec(m.group(1)) - last_go.pop(m.group(2))) * 1000.0))
    return out

for tag, path in [("OFF (probe K0b, no options)", "probe_K0b.log"),
                  ("ON  (probe M1b, TmFinishIteration=true)", "probe_M1b.log")]:
    mv = moves(path)
    for side in ("cand", "base", "A", "B"):
        xs = sorted(e for n, e in mv if n == side)
        if not xs:
            continue
        print(f"{tag} side {side}: moves={len(xs)} mean={statistics.fmean(xs):.1f} ms "
              f"median={xs[len(xs)//2]:.1f} max={xs[-1]:.1f}")
