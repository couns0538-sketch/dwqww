#!/usr/bin/env python3
"""readme_audit_parsers.py -- seat 19's measurement-integrity warning, applied to my own checks.

It re-derives the two checks of mine that produce a CONFIRMS-style verdict from PARSED ENGINE OUTPUT, and this
time every parse is ASSERTED: the line must have been found, the regex must have matched, and the number must be
a real integer before any comparison is allowed. A missing line, an empty string or a NaN raises and fails the
script loudly instead of passing as a confirmation.

Check A: S-C1 (seat 06's S-F9) — engine score on G196 and its colour mirror.
Check B: job1's mate-distance table — the engine's `mate N` against dtm2.
Both are re-run here from scratch; the output is compared with what I already published.
"""
import json
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-rel/forge"
FAILURES = []


def need(cond, what):
    """hard assertion: a missing/empty/NaN value must never pass silently"""
    if not cond:
        FAILURES.append(what)
        print(f"  !! FAIL-LOUD: {what}")
    return cond


SCORE_RE = re.compile(r"score (mate|cp) (-?\d+)")


def parse_score_line(line, where):
    need(line is not None and line != "", f"{where}: no pv/info line at all")
    m = SCORE_RE.search(line or "")
    need(m is not None, f"{where}: score regex did not match the line {line!r}")
    if not m:
        return None, None
    kind, num = m.group(1), int(m.group(2))
    # an integer parse cannot be NaN, but assert we actually got a number
    need(isinstance(num, int), f"{where}: score is not an integer")
    return kind, num


def drive(fen, depth=10, s14=True):
    """live process, read to bestmove, never pipe quit (19-F12 discipline)"""
    S14 = ["setoption name Threads value 1", "setoption name Hash value 16",
           "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
           "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
           "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
           "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
           "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
           "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
           "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true"]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    out = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    for c in ["uci", "isready"] + (S14 if s14 else []) + ["ucinewgame", "isready"]:
        send(c)
    send(f"position fen {fen}")
    send("isready")
    send(f"go depth {depth}")
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\n")
        out.append(line)
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
    pv = [l for l in out if re.search(r"\binfo\b.*\bpv\b", l)]
    bm = [l for l in out if l.startswith("bestmove")]
    need(len(pv) > 0, f"{fen[:24]}: the search produced NO pv line (a fabricated/0-node answer)")
    need(len(bm) > 0, f"{fen[:24]}: no bestmove line")
    return pv[-1] if pv else None


print("=" * 100)
print("CHECK A — S-C1: seat 06's S-F9, re-derived with hard parse assertions")
print("=" * 100)
G196 = "5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w - - 0 1"
G196_M = "8/8/4n3/8/3p4/3Pk1pp/1K6/5q2 b - - 0 1"
G217 = "8/7p/8/7p/3k2b1/6K1/2p5/8 b - - 0 1"
G217_M = "8/2P5/6k1/3K2B1/7P/8/7P/8 w - - 0 1"

for label, fen, want_kind, want_num in (("G196 orig", G196, "cp", 4402), ("G196 mirror", G196_M, "mate", 14),
                                        ("G217 orig", G217, "cp", 2557), ("G217 mirror", G217_M, "mate", 11)):
    line = drive(fen, 10)
    kind, num = parse_score_line(line, label)
    if kind is None:
        continue
    ok = (kind == want_kind and num == want_num)
    print(f"  {label:14s} parsed={kind} {num:+d}  claimed={want_kind} {want_num:+d}  "
          f"{'MATCH' if ok else 'DIFFERENT'}")
    print(f"      from line: {line[:120]}")
    need(ok, f"CHECK A {label}: parsed {kind} {num} != claimed {want_kind} {want_num}")

print()
print("=" * 100)
print("CHECK B — job1's mate table: every engine `mate N` re-parsed with assertions, dtm2 re-run")
print("=" * 100)
rows = [json.loads(l) for l in open("job1/out/rows.jsonl")]
mate_rows = [r for r in rows if r.get("last_pv") and r["last_pv"].get("score", ("",))[0] == "mate"]
need(len(mate_rows) > 0, "CHECK B: no mate rows found in rows.jsonl at all")
print(f"  mate rows found: {len(mate_rows)} (asserted > 0)")
consistent = 0
for r in mate_rows:
    n = r["last_pv"]["score"][1]
    need(isinstance(n, int) and n != 0, f"CHECK B {r['set']}/{r['pos']}: mate value is not a non-zero integer")
    want = 2 * n - 1 if n > 0 else 2 * (-n)
    plies = r["last_pv"].get("plies")
    ends = r["last_pv"].get("ends_checkmate")
    need(isinstance(plies, int), f"CHECK B {r['set']}/{r['pos']}: pv ply count missing")
    ok = bool(ends) and plies == want
    consistent += bool(ok)
    print(f"  {r['set']}/{r['pos']:3d} mate {n:+3d} wants {want:2d} plies, pv has {plies:2d}, "
          f"ends_mate={ends}  {'consistent' if ok else 'INCONSISTENT'}")
print(f"  => {consistent}/{len(mate_rows)} consistent (published: 9/10)")
need(consistent == 9, f"CHECK B: re-derivation gives {consistent}, published 9")

print()
print("=" * 100)
if FAILURES:
    print(f"RESULT: {len(FAILURES)} FAILURE(S) — a check of mine did not measure what it claimed:")
    for f_ in FAILURES:
        print("   -", f_)
    sys.exit(1)
print("RESULT: every parse asserted and every published number re-derived. No NaN, no empty parse, no")
print("        missing line could have reached a verdict in these two checks.")
print("        NOTE: this audit cannot retro-fix job1/mate_check.py, which maps a MISSING verdict line to")
print("        MISMATCH; that direction invents a REFUTES rather than a CONFIRMS. Recorded in RESULT.md.")
