#!/usr/bin/env python3
"""kimi5 job 30 step 1: what job 27's "worst ply group" column counts, and the corrected column.

The column was made by the committed command `python3 tests_kimi5_job27/step4_totals_j27.py`
(rerun on the committed rows in step1_rerun_committed_command.txt: it reproduces the report's
numbers exactly: 250, 231, 238, 246, 261 soft; 216, 193, 199, 209, 204 hard).

WHAT IT COUNTS: for each keep+budget, the changed best moves (vs that budget's keep-1024 rows)
are bucketed by `ply = i % 60`, i the 0-based row index inside the 1,200-row file. Every game has
exactly 60 searches (the replay loops `for ply in range(60)`), so i % 60 EQUALS the row's own ply
field on every row. The bug is the bucket boundaries: `"1-9" if ply < 9 else ("10-29" if ply < 29
else "30-59")` puts ply in {0..8} / {9..28} / {29..58} - the bucket LABELLED "30-59" actually
counts plies 29-58 (and "10-29" counts 9-28, "1-9" counts 0-8). Off by one at both upper bounds.

THE CORRECTED COLUMN below buckets the same changed rows by the row's own ply field with the
boundaries the labels say: 1-9, 10-29, 30-59 (ply 0 never changes - KA3). It reproduces the
numbers Opus recomputed (242, 222, 230, 237, 254 soft; 210, 189, 193, 205, 197 hard). The
report's conclusion stands: plies 30-59 are the worst group in every non-default row.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = os.path.join(HERE, "..", "tests_kimi5_job27", "rows2")

print("keep budget changed committedColumn(29-58 as '30-59') corrected(30-59 by ply field)")
for b in ["soft", "hard"]:
    dfl = [json.loads(l) for l in open(os.path.join(ROWS, f"keep1024_{b}.jsonl"))]
    for k in [896, 768, 512, 256, 0]:
        rows = [json.loads(l) for l in open(os.path.join(ROWS, f"keep{k}_{b}.jsonl"))]
        ch = [i for i in range(1200) if rows[i]["bestmove"] != dfl[i]["bestmove"]]
        committed = sum(1 for i in ch if i % 60 >= 29)            # the committed command's bucket
        corrected = sum(1 for i in ch if 30 <= rows[i]["ply"] <= 59)
        print(f"{k} {b} {len(ch)} {committed} {corrected}")
