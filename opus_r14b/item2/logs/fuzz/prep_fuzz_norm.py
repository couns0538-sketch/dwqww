#!/usr/bin/env python3
"""prep_fuzz_norm.py OUT_DIR [--cases 200] [--seed 7] - Opus R14-B: damaged normalized JSONL (Astra's format) into
`relabel2.py prepare --normalized`. Same verdicts as prep_fuzz.py: exit 0 with rows.tsv, or exit 2 with
"BAD INPUT: <file>:<line>: ..." (or "no rows selected") and nothing published; anything else is a finding.
"""
import json
import os
import random
import re
import subprocess
import sys
import time

R = "D:/grok-pc-data/dwqww/.claude/worktrees/o14b-r2/opus_r14b/item2/relabel2.py"
PY = "C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe"
SRC = "C:/o14b/t2_2158/norm_100.jsonl"


def mutate(lines, rng):
    kind = rng.choice(["syntax", "syntax", "type", "type", "missing", "extra", "source_kind", "source_row",
                       "order", "dup", "score_range", "fen", "result", "empty_line", "trailing_garbage", "empty",
                       "unicode", "nested"])
    L = list(lines)
    i = rng.randrange(len(L))
    rec = json.loads(L[i])
    if kind == "syntax":
        s = L[i]
        j = rng.randrange(len(s) - 1)
        L[i] = s[:j] + s[j + 1:]
    elif kind == "type":
        key = rng.choice(["score_stm", "result_white", "source_row", "ply", "fen"])
        rec[key] = rng.choice(["40", 4.5, None, [], {}, True, -1])
        L[i] = json.dumps(rec) + "\n"
    elif kind == "missing":
        del rec[rng.choice(list(rec))]
        L[i] = json.dumps(rec) + "\n"
    elif kind == "extra":
        rec["surprise"] = rng.choice([1, "x", None])
        L[i] = json.dumps(rec) + "\n"
    elif kind == "source_kind":
        rec["source_kind"] = rng.choice(["epd", "", None, "SELFPLAY"])
        L[i] = json.dumps(rec) + "\n"
    elif kind == "source_row":
        rec["source_row"] = rng.choice([0, -5, 10 ** 12, rec["source_row"] + 0.5])
        L[i] = json.dumps(rec) + "\n"
    elif kind == "order":
        j = rng.randrange(len(L))
        L[i], L[j] = L[j], L[i]
    elif kind == "dup":
        L.insert(i, L[i])
    elif kind == "score_range":
        rec["score_stm"] = rng.choice([99999999999, -40000, 32768, 32767])
        L[i] = json.dumps(rec) + "\n"
    elif kind == "fen":
        rec["fen"] = rng.choice(["8/8/8/8/8/8/8/8 w - - 0 1", "x", rec["fen"].rsplit(" ", 2)[0], rec["fen"] + "\t"])
        L[i] = json.dumps(rec) + "\n"
    elif kind == "result":
        rec["result_white"] = rng.choice([2, -2, 0.5, "1", None])
        L[i] = json.dumps(rec) + "\n"
    elif kind == "empty_line":
        L.insert(i, "\n")
    elif kind == "trailing_garbage":
        L[i] = L[i].rstrip("\n") + " xyz\n"
    elif kind == "empty":
        L = []
    elif kind == "unicode":
        rec["source"] = "forge_selfplay_\u00e9\u00df.txt"
        L[i] = json.dumps(rec, ensure_ascii=False) + "\n"
    elif kind == "nested":
        L[i] = json.dumps([rec]) + "\n"
    return kind, L


def main():
    out = sys.argv[1]
    n = int(sys.argv[sys.argv.index("--cases") + 1]) if "--cases" in sys.argv else 200
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 7
    os.makedirs(out)
    base = open(SRC, encoding="utf-8").read().splitlines(keepends=True)
    rng = random.Random(seed)
    bad, counts = 0, {}
    with open(os.path.join(out, "cases.tsv"), "x", encoding="utf-8", newline="\n") as log:
        log.write("case\tkind\texit\tverdict\tseconds\tmessage\n")
        for c in range(n):
            kind, lines = mutate(base, rng)
            d = os.path.join(out, f"c{c:03d}")
            os.makedirs(d)
            inp = os.path.join(d, "norm.jsonl")
            with open(inp, "w", encoding="utf-8", newline="") as fh:
                fh.write("".join(lines))
            job = os.path.join(d, "job")
            t0 = time.monotonic()
            try:
                p = subprocess.run([PY, "-I", "-B", R, "prepare", "--job", job, "--run-id", "fz", "--normalized", inp],
                                   capture_output=True, timeout=60)
                rc, err = p.returncode, p.stderr.decode("utf-8", "replace")
            except subprocess.TimeoutExpired:
                rc, err = "HANG", ""
            msg = (err.strip().splitlines() or [""])[-1][:160]
            published = os.path.exists(os.path.join(job, "rows.tsv"))
            if rc == 0 and published:
                verdict = "ok"
            elif rc == 2 and not published and (re.match(r"BAD INPUT: .*norm\.jsonl:\d+: ", msg)
                                                or msg.startswith("BAD INPUT: no rows selected")):
                verdict = "refused"
            else:
                verdict = "FINDING"
                bad += 1
            counts[(kind, verdict)] = counts.get((kind, verdict), 0) + 1
            log.write(f"c{c:03d}\t{kind}\t{rc}\t{verdict}\t{time.monotonic() - t0:.1f}\t{msg}\n")
            log.flush()
    for (kind, verdict), k in sorted(counts.items()):
        print(f"  {kind:16s} {verdict:8s} {k}")
    print(f"prep_fuzz_norm: {n} cases, findings {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
