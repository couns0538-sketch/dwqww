"""R7 J4: games per hour of a fastchess run from its PGN (read only).
usage: python -I -B pgn_rate.py <games.pgn> [--last-minutes M]
Uses the GameStartTime / GameEndTime / GameDuration / PlyCount / Termination tags fastchess writes. Prints the
games, the wall span (first start .. last end), games/hour over the whole span and over the last M minutes
(default 60), the mean / median game duration, the mean ply count and the termination counts."""
import collections
import datetime as dt
import re
import statistics
import sys

path = sys.argv[1]
last_min = float(sys.argv[sys.argv.index("--last-minutes") + 1]) if "--last-minutes" in sys.argv else 60.0
TAG = re.compile(r'^\[(\w+) "(.*)"\]')
games = []
cur = {}
with open(path, encoding="utf-8", errors="replace") as f:
    for line in f:
        m = TAG.match(line)
        if m:
            if m.group(1) == "Event" and cur:
                games.append(cur)
                cur = {}
            cur[m.group(1)] = m.group(2)
if cur:
    games.append(cur)


def ts(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S %z")


def dur(s):
    h, m, sec = (int(x) for x in s.split(":"))
    return 3600 * h + 60 * m + sec


games = [g for g in games if "GameEndTime" in g and "GameStartTime" in g]
starts = [ts(g["GameStartTime"]) for g in games]
ends = sorted(ts(g["GameEndTime"]) for g in games)
span_h = (ends[-1] - min(starts)).total_seconds() / 3600
cut = ends[-1] - dt.timedelta(minutes=last_min)
recent = [e for e in ends if e > cut]
durs = [dur(g["GameDuration"]) for g in games if "GameDuration" in g]
plies = [int(g["PlyCount"]) for g in games if "PlyCount" in g]
term = collections.Counter(g.get("Termination", "?") for g in games)
print(f"games {len(games)}  first start {min(starts)}  last end {ends[-1]}  span {span_h:.3f} h")
print(f"games/hour over the span: {len(games) / span_h:.1f}")
print(f"games/hour over the last {last_min:.0f} min: {len(recent) / (last_min / 60):.1f}")
print(f"game duration: mean {statistics.mean(durs):.2f} s, median {statistics.median(durs):.1f} s; "
      f"plies: mean {statistics.mean(plies):.1f}, median {statistics.median(plies):.0f}")
print("terminations:", dict(term))
