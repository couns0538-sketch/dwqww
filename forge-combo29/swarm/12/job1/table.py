#!/usr/bin/env python3
"""table.py RESULT.jsonl [RESULT2.jsonl ...] — build the job-1 table from the raw records.

Reads only the runner's JSONL; nothing here is typed by hand. Prints the five counts the
report needs, then the per-sequence list of every sequence that fired anything.
"""
import json
import sys


def load(paths):
    recs = []
    for p in paths:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    recs.append(json.loads(line))
    return recs


def main():
    paths = sys.argv[1:]
    recs = load(paths)
    n = len(recs)
    crash = [r["seq"] for r in recs if r["crash"]]
    hang = [r["seq"] for r in recs if r["hang"]]
    san = [r["seq"] for r in recs if r["sanitizer_lines"]]
    ill = [r["seq"] for r in recs if r.get("illegal_confirmed")]
    nonzero = [r["seq"] for r in recs if r["exit"] not in (0, None)]
    unchecked = sum(len(r.get("unchecked_bestmoves", [])) for r in recs)
    total_bm = sum(r.get("bestmoves", 0) for r in recs)
    wall = sum(r["wall_s"] for r in recs)

    print(f"files: {', '.join(paths)}")
    print(f"sequences                 {n}")
    print(f"UCI lines total           {sum(r['lines'] for r in recs)}")
    print(f"bestmoves produced        {total_bm}")
    print(f"bestmoves not checkable   {unchecked}")
    print(f"wall seconds total        {wall:.1f}")
    print()
    print("| quantity | count | sequences |")
    print("|---|---|---|")
    print(f"| sequences run | {n} | - |")
    print(f"| crashes (signal) | {len(crash)} | {', '.join(crash[:20]) or '-'} |")
    print(f"| hangs (no readyok in 20 s) | {len(hang)} | {', '.join(hang[:20]) or '-'} |")
    print(f"| sanitizer lines | {len(san)} | {', '.join(san[:20]) or '-'} |")
    print(f"| illegal bestmoves (re-checked in a fresh process) | {len(ill)} | {', '.join(ill[:20]) or '-'} |")
    print(f"| nonzero exit status | {len(nonzero)} | {', '.join(nonzero[:20]) or '-'} |")
    print()
    bad = [r for r in recs if r["crash"] or r["hang"] or r["sanitizer_lines"]
           or r.get("illegal_confirmed") or r["exit"] not in (0, None)]
    if not bad:
        print("no sequence fired anything; nothing further to list")
        return
    for r in bad:
        print(f"--- {r['seq']}: exit={r['exit']} crash={r['crash']} hang={r['hang']} "
              f"san={r['sanitizer_lines']} wall={r['wall_s']}s")
        for s in r["sanitizer_excerpt"]:
            print(f"    SAN {s}")
        for x in r.get("recheck", []):
            print(f"    recheck {x}")
        print(f"    tail: {r['transcript_tail']}")


if __name__ == "__main__":
    main()
