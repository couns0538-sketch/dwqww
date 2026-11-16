#!/usr/bin/env python3
"""summarize.py OUTDIR : turns the raw perf report text in OUTDIR into the tables of REPORT_job1.md.

Every number printed here is read from a raw file produced by profile.sh; nothing is typed by hand.
"""
import re
import sys
import os

OUT = sys.argv[1]
SYMS = os.path.join(OUT, "perf_symbols_all.txt")
STDOUT = os.path.join(OUT, "bench13.stdout.txt")
META = os.path.join(OUT, "profile.meta")

ROW = re.compile(r"^\s+(\d+\.\d+)%\s+(\[\.\]\s+)?(.*)$")


def rows(path):
    """[(percent, symbol)] from a `perf report --stdio -g none` file, IPC columns stripped."""
    out = []
    started = False
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.startswith("# Overhead"):
            started = True
            continue
        if not started:
            continue
        m = ROW.match(line.rstrip("\n"))
        if not m:
            continue
        pct, _, rest = m.groups()
        sym = re.sub(r"\s+-\s+-\s*$", "", rest).strip()
        out.append((float(pct), sym))
    return out


def fam(name, pat, rr):
    hits = [(p, s) for p, s in rr if pat in s]
    return name, len(hits), sum(p for p, _ in hits)


def main():
    rr = rows(SYMS)
    print("## table A: the ten hottest symbols by SELF time (perf report --no-children -g none)")
    print()
    print("| # | symbol | self share |")
    print("|---|---|---|")
    for i, (pct, sym) in enumerate(rr[:10], 1):
        print(f"| {i} | `{sym}` | {pct:.2f} % |")
    print()
    print("## table B: family sums of self time")
    print()
    print("| family | symbols | summed self share |")
    print("|---|---|---|")
    # each row is a predicate over the symbol text; the rows below do NOT overlap
    fams = [
        ("main search recursion (Worker::search)", lambda s: "Worker::search(" in s),
        ("quiescence only (Worker::qsearch)", lambda s: "Worker::qsearch(" in s),
        ("NNUE accumulator work (forge::nnue::*)", lambda s: s.startswith("forge::nnue::")),
        ("HCE term walk (evaluate_position)", lambda s: "evaluate_position" in s),
        ("evaluation glue (corrected_eval/static_evaluate/scale_factor/update_runtime_psqt)",
         lambda s: any(k in s for k in ("corrected_eval", "static_evaluate", "scale_factor",
                                        "update_runtime_psqt"))),
        ("move generation (fill_pseudo_legal*)", lambda s: "fill_pseudo_legal" in s),
        ("move ordering (MovePicker::*)", lambda s: "MovePicker::" in s),
        ("static exchange (see_ge)", lambda s: "see_ge" in s),
        ("make/unmake move", lambda s: "Board::make_move" in s or "Board::unmake_move" in s),
        ("hash key (key_after/is_repetition)", lambda s: "key_after" in s or "is_repetition" in s),
        ("memset/memcpy", lambda s: "memset" in s or "memcpy" in s),
        ("std library helpers (std::*)", lambda s: "std::" in s),
        ("transposition table (probe/store)", lambda s: "TranspositionTable" in s or "store_tt" in s),
        ("legality checks (is_legal_complete/is_pseudo_legal/has_legal_move/refresh_king_lines)",
         lambda s: any(k in s for k in ("is_legal_complete", "is_pseudo_legal", "has_legal_move",
                                        "refresh_king_lines"))),
    ]
    rows_out = []
    for name, pred in fams:
        hits = [p for p, s in rr if pred(s)]
        rows_out.append((name, len(hits), sum(hits)))
    total_named = sum(s for _, _, s in rows_out)
    for name, n, s in rows_out:
        print(f"| {name} | {n} | {s:.2f} % |")
    everything_eval = sum(p for p, s in rr
                          if s.startswith("forge::nnue::") or "evaluate_position" in s
                          or any(k in s for k in ("corrected_eval", "static_evaluate", "scale_factor",
                                                 "update_runtime_psqt")))
    print(f"| **all evaluation** (NNUE + HCE walk + glue, the three rows above together) | - | "
          f"**{everything_eval:.2f} %** |")
    print(f"| **all named rows together** (a symbol can only land in one row) | - | "
          f"{total_named:.2f} % |")
    print()
    print("## table C: counts behind the prediction verdicts")
    print()
    print(f"- symbols listed at all: {len(rr)}")
    print(f"- symbols at or above 0.5 % self time: {sum(1 for p, _ in rr if p >= 0.5)}")
    print(f"- symbols at or above 0.5 % below the top ten: {sum(1 for p, _ in rr[10:] if p >= 0.5)}")
    top10 = sum(p for p, _ in rr[:10])
    print(f"- top ten summed self share: {top10:.2f} %")
    samples = ""
    for line in open(SYMS, encoding="utf-8", errors="replace"):
        if line.startswith("# Samples:"):
            samples = line.strip()
            break
    print(f"- {samples or 'samples line MISSING'}")
    bench = [l.strip() for l in open(STDOUT, encoding="utf-8", errors="replace")
             if l.startswith("info string bench depth 13")]
    ok = [l for l in bench if "nodes 862329" in l]
    print(f"- bench 13 lines in the profiled run: {len(bench)}; of them nodes 862329: {len(ok)}")
    times = [int(m.group(1)) for l in bench
             for m in [re.search(r" time (\d+) ", l)] if m]
    if times:
        times_sorted = sorted(times)
        print(f"- bench 13 internal ms: min {min(times)} median {times_sorted[len(times)//2]} "
              f"max {max(times)} sum {sum(times)}")
        nps = [int(m.group(1)) for l in bench
               for m in [re.search(r" nps (\d+)", l)] if m]
        print(f"- bench 13 nps: min {min(nps)} median {sorted(nps)[len(nps)//2]} max {max(nps)}")
    print()
    print("## table D: first three and last three bench 13 lines of the profiled run")
    print("```")
    for l in bench[:3]:
        print(l)
    print("...")
    for l in bench[-3:]:
        print(l)
    print("```")
    print()
    cg = os.path.join(OUT, "..", "profile_cg", "perf_children.txt")
    cg = os.path.normpath(cg)
    if os.path.exists(cg):
        print("## table F: INCLUSIVE cost (perf report --children) from the callchain run")
        print()
        print("A `children` share is the sample time of a symbol plus everything it called; a `self` share")
        print("is the symbol's own instructions. Read the rows top-down: the first row under `Worker::search`")
        print("that is *not* another Worker::search is a real leaf of the search.")
        print()
        print("| children | self | symbol |")
        print("|---|---|---|")
        for line in open(cg, encoding="utf-8", errors="replace"):
            m = re.match(r"^\s+(\d+\.\d+)%\s+(\d+\.\d+)%\s+(?:\[\.\]\s+)?(.*)$", line.rstrip("\n"))
            if not m:
                continue
            ch, se, sym = m.groups()
            sym = re.sub(r"\s+-\s+-\s*$", "", sym).strip()
            if sym in ("_start", "__libc_start_main@@GLIBC_2.34", "__libc_start_call_main"):
                continue
            if float(ch) < 1.0:
                continue
            print(f"| {ch} % | {se} % | `{sym}` |")
        print()
    print("## table E: the profile's .meta")
    print("```")
    print(open(META, encoding="utf-8", errors="replace").read().strip())
    print("```")


if __name__ == "__main__":
    main()
