#!/usr/bin/env python3
# Turn a fastchess min PGN into the compact per-game log required by job 1:
# one line per game: round, which side had white, the opening's FEN, the result.
# Also recount W-L-D and the pentanomial pair counts for cand (verification).
import re
import sys

def games(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        cur_tags = None
        for line in f:
            line = line.rstrip("\n")
            if line.startswith('[Event "'):
                if cur_tags is not None:
                    yield cur_tags
                cur_tags = {}
            if cur_tags is not None:
                m = re.match(r'\[(\w+) "(.*?)"\]\s*$', line)
                if m:
                    cur_tags[m.group(1)] = m.group(2)
        if cur_tags is not None:
            yield cur_tags

def main(path, cand_name, out_path):
    wl = {"W": 0, "L": 0, "D": 0}
    ptn = [0, 0, 0, 0, 0]
    rounds = {}
    lines = []
    for t in games(path):
        r = t.get("Round", "?")
        white = t.get("White", "?")
        res = t.get("Result", "?")
        fen = t.get("FEN", "startpos")
        lines.append(f"{r}\t{white}\t{fen}\t{res}")
        if res == "1/2-1/2":
            p = 0.5
            wl["D"] += 1
        elif (res == "1-0") == (white == cand_name):
            p = 1.0
            wl["W"] += 1
        else:
            p = 0.0
            wl["L"] += 1
        rounds.setdefault(r, []).append(p)
    for r, ps in rounds.items():
        pts = sum(ps)
        b = min(4, max(0, int(pts * 2)))
        ptn[b] += 1
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    n = wl["W"] + wl["L"] + wl["D"]
    print(f"{path}: games={n} cand W-L-D={wl['W']}-{wl['L']}-{wl['D']} "
          f"Ptnml(0-2)={[*ptn]} rounds={len(rounds)}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
