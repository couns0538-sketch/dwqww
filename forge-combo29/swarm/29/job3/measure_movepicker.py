#!/usr/bin/env python3
"""Job 3, P1 test: inside MovePicker, is the SCORING loop or the SELECTION loop the larger cost?

Scoring = pushing a Scored{score} into moves_ for every generated move (`push_scored`, plus the history reads in
`quiet_history_sum` / capture_history). Selection = `pick_best`'s max scan and `std::sort`.

Numbers come from callgrind self-cost per source line (exact instruction counts), not from timing, so machine
load cannot affect them. Input: the callgrind annotation text produced by callgrind_annotate --auto=yes.
"""
import re, sys

txt = open(sys.argv[1]).read()
pat = re.compile(r'^\s*([0-9][0-9,]*)\s+\(\s*([0-9.]+)%\)\s{2,}(.*)$')

SCORE_KEYS = ("int score = main[move.from][move.to]", "score += (*cont1)", "score += (*cont2)",
              "score += (*cont4)", "moves_[count_++] = Scored", "int score = 10 * value + capture_history",
              "push_scored(move, score)", "const Score value", "score += Us == White",
              "if (!seeded_ || score > seeded_score_)", "seeded_score_ = score")
SELECT_KEYS = ("std::sort(", "__introsort_loop", "chunk_max", "_mm256_permutevar8x32",
               "if (score > best_score)", "best_score = score", "std::swap(moves_[index_]")

def bucket(keys):
    total = 0
    hits = []
    for line in txt.splitlines():
        m = pat.match(line)
        if not m:
            continue
        src = m.group(3).strip()
        if src.startswith("=>"):
            continue
        if any(k in src for k in keys):
            v = int(m.group(1).replace(",", ""))
            total += v
            hits.append((v, src[:78]))
    return total, hits

s, sh = bucket(SCORE_KEYS)
c, ch = bucket(SELECT_KEYS)
print(f"scoring-loop self instructions : {s:>13,}")
for v, src in sorted(sh, reverse=True)[:6]:
    print(f"      {v:>11,}  {src}")
print(f"selection-loop self instructions: {c:>13,}")
for v, src in sorted(ch, reverse=True)[:6]:
    print(f"      {v:>11,}  {src}")
print()
print(f"ratio scoring/selection = {s/c:.2f}x  (P1 predicted scoring dominates; killed if selection > 2x scoring)")
print("VERDICT:", "P1 SURVIVES" if s > 0.5 * c else "P1 KILLED")
