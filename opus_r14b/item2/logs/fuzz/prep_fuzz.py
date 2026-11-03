#!/usr/bin/env python3
"""prep_fuzz.py OUT_DIR [--cases 200] [--seed 7] - Opus R14-B: damaged self-play text into `relabel2.py prepare`.
Each case: the first 400 lines of a real self-play file with seeded damage (byte flips, a deleted / duplicated / cut
line, a field swapped, a FEN field changed, CRLF, NUL, a BOM in the middle, a truncated last line, an empty file).
relabel2 must either prepare (exit 0) or refuse with exit 2 and a "BAD INPUT: <file>:<line>: ..." message; a
traceback (exit 1), any other exit code, a hang (60 s) or a published rows.tsv after a refusal is a finding.
Runs the frozen relabel2.py from the worktree with the venv Python (BelowNormal inherited from this driver).
"""
import os
import random
import re
import subprocess
import sys
import time

R = "D:/grok-pc-data/dwqww/.claude/worktrees/o14b-r2/opus_r14b/item2/relabel2.py"
PY = "C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe"
SRC = "D:/grok-pc-data/selfplay_out/forge_selfplay_001.txt"


def mutate(lines, rng):
    kind = rng.choice(["flip", "flip", "flip", "delete", "dup", "cut", "swap", "fenfield", "crlf", "nul", "bom",
                       "trunc_last", "empty", "score_text", "result_text", "extra_field"])
    L = list(lines)
    i = rng.randrange(len(L))
    if kind == "flip":
        b = bytearray(L[i], "latin-1")
        for _ in range(rng.choice((1, 3))):
            b[rng.randrange(len(b) - 1)] = rng.randrange(32, 127)
        L[i] = b.decode("latin-1")
    elif kind == "delete":
        del L[i]
    elif kind == "dup":
        L.insert(i, L[i])
    elif kind == "cut":
        L[i] = L[i][: rng.randrange(1, len(L[i]) - 1)] + "\n"
    elif kind == "swap":
        f = L[i].rstrip("\n").split("|")
        if len(f) == 3:
            f[1], f[2] = f[2], f[1]
        L[i] = "|".join(f) + "\n"
    elif kind == "fenfield":
        f = L[i].split("|", 1)
        parts = f[0].split()
        j = rng.randrange(len(parts))
        parts[j] = rng.choice(["x", "-", "99", "KQkqX", "e9", "", "8/8/8/8/8/8/8/8"])
        L[i] = " ".join(parts) + " |" + f[1]
    elif kind == "crlf":
        L[i] = L[i].rstrip("\n") + "\r\n"
    elif kind == "nul":
        L[i] = L[i][:5] + "\x00" + L[i][5:]
    elif kind == "bom":
        L[i] = "\ufeff" + L[i]
    elif kind == "trunc_last":
        L[-1] = L[-1].rstrip("\n")[:-3]
    elif kind == "empty":
        L = []
    elif kind == "score_text":
        f = L[i].split("|")
        f[1] = rng.choice([" 1e3 ", " -", " 12.5 ", " +7 ", " 99999999999 ", " nan "])
        L[i] = "|".join(f)
    elif kind == "result_text":
        f = L[i].rstrip("\n").split("|")
        f[2] = rng.choice([" 2", " -1", " 0.25", " draw", ""])
        L[i] = "|".join(f) + "\n"
    elif kind == "extra_field":
        L[i] = L[i].rstrip("\n") + " | 5\n"
    return kind, L


def main():
    out = sys.argv[1]
    n = int(sys.argv[sys.argv.index("--cases") + 1]) if "--cases" in sys.argv else 200
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 7
    os.makedirs(out)
    with open(SRC, encoding="utf-8") as fh:
        base = [next(fh) for _ in range(400)]
    rng = random.Random(seed)
    bad = 0
    counts = {}
    with open(os.path.join(out, "cases.tsv"), "x", encoding="utf-8", newline="\n") as log:
        log.write("case\tkind\texit\tverdict\tseconds\tmessage\n")
        for c in range(n):
            kind, lines = mutate(base, rng)
            d = os.path.join(out, f"c{c:03d}")
            os.makedirs(d)
            inp = os.path.join(d, "forge_selfplay_001.txt")
            with open(inp, "w", encoding="utf-8", newline="") as fh:
                fh.write("".join(lines))
            job = os.path.join(d, "job")
            t0 = time.monotonic()
            try:
                p = subprocess.run([PY, "-I", "-B", R, "prepare", "--job", job, "--run-id", "fz", "--selfplay", inp,
                                    "--min-free-gb", "50"], capture_output=True, timeout=60)
                rc, err = p.returncode, p.stderr.decode("utf-8", "replace")
            except subprocess.TimeoutExpired:
                rc, err = "HANG", ""
            sec = time.monotonic() - t0
            msg = (err.strip().splitlines() or [""])[-1][:160]
            published = os.path.exists(os.path.join(job, "rows.tsv"))
            if rc == 0 and published:
                verdict = "ok"
            elif rc == 2 and re.match(r"BAD INPUT: .*forge_selfplay_001\.txt:\d+: ", msg) and not published:
                verdict = "refused"
            elif rc == 2 and msg.startswith("BAD INPUT: no rows selected") and not published:
                verdict = "refused"
            else:
                verdict = "FINDING"
                bad += 1
            counts[(kind, verdict)] = counts.get((kind, verdict), 0) + 1
            log.write(f"c{c:03d}\t{kind}\t{rc}\t{verdict}\t{sec:.1f}\t{msg}\n")
            log.flush()
    for (kind, verdict), k in sorted(counts.items()):
        print(f"  {kind:12s} {verdict:8s} {k}")
    print(f"prep_fuzz: {n} cases, findings {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
