#!/usr/bin/env python3
"""Which PART of MovePicker dominates on the PC build under PC20, at Threads 1?

Splits the picker's cost into its stages using callgrind's per-line attribution on the portable -g build (the only
build callgrind can profile), then attributes each MovePicker line to a stage:
  scoring (history reads, push_scored, check-square test) / selection (pick_best scan + sort) /
  generation (generate_captures, generate_quiets, generate_evasions) / stage dispatch.
"""
import re, subprocess, sys
OUT = sys.argv[1]
rep = subprocess.run(["callgrind_annotate","--auto=yes","--threshold=99",OUT],
                     capture_output=True, text=True).stdout
open("/tmp/pcann.txt","w").write(rep)

pat = re.compile(r'^\s*([0-9][0-9,]*)\s+\(\s*([0-9.]+)%\)\s{2,}(.*)$')
STAGES = {
 "scoring": ("int score = main[move.from][move.to]", "score += (*cont1)", "score += (*cont2)",
             "score += (*cont4)", "moves_[count_++] = Scored", "push_scored(move, score)",
             "if (!seeded_ || score > seeded_score_)", "seeded_score_ = score",
             "int score = 10 * value + capture_history", "value += 12000",
             "if ((check_squares[", "const Piece piece = board.piece_at(move.from)"),
 "selection": ("if (score > best_score)", "best_score = score", "std::swap(moves_[index_]",
               "chunk_max", "_mm256_permutevar8x32", "std::sort(", "__introsort_loop",
               "while (index_ < count_)"),
 "generation": ("init_check_squares", "generate_pseudo_legal(buffer_", "board_.generate_pseudo_legal",
                "check_squares_[Pawn]", "check_squares_[Knight]", "check_squares_[Bishop]",
                "check_squares_[Rook]", "check_squares_[Queen]"),
 "dispatch": ("switch (stage_)", "case MainTT", "case GoodCaptures", "case QuietMoves",
              "case BadCaptures", "case QsCaptures", "case Evasions", "stage_ = static_cast<Stage>"),
}
tot = {}
allrows = []
seen = set()
for line in rep.splitlines():
    m = pat.match(line)
    if not m: continue
    src = m.group(3).strip()
    if src.startswith("=>"): continue
    v = int(m.group(1).replace(",", ""))
    key = (v, src)
    if key in seen:
        continue
    seen.add(key)
    allrows.append((v, src))
    for st, keys in STAGES.items():
        if any(k in src for k in keys):
            tot[st] = tot.get(st, 0) + v
            break
m = re.search(r"([0-9,]+) \(100\.0%\)\s+PROGRAM TOTALS", rep)
if not m:
    raise SystemExit("ABORT: no PROGRAM TOTALS -- refusing to report shares")
total = int(m.group(1).replace(",", ""))
print(f"total attributed instructions: {total:,}")
print()
print("| stage | instructions | share of run |")
print("|---|---|---|")
for st in ("scoring","selection","generation","dispatch"):
    v = tot.get(st, 0)
    print(f"| {st} | {v:,} | {100*v/total:.2f} % |")
print()
print("largest single lines in the picker family:")
for v, src in sorted([r for r in allrows if any(k in r[1] for ks in STAGES.values() for k in ks)], reverse=True)[:8]:
    print(f"  {v:>12,}  {src[:88]}")
