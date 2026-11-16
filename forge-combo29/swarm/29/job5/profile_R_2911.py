#!/usr/bin/env python3
"""CHECK of 19-F13 (seat 19), written from its command file alone -- a harness of MY OWN, not a copy of theirs.

19-F13 claims: "on the PC-relevant families (depth 12 over 200 of the new R_1911 set) MovePicker::pick_best is
7.93 % -- hotter than MovePicker::next at 5.71 % and up from 6.35 % on bench 13 -- and TT probe_body is 5.77 %,
up from 2.09 % on bench 13."

Why this matters for me: my own 29-F7 says the move-SCORING loop dominates the selection loop, which would put
MovePicker::next above pick_best. If 19-F13 is right on a depth-12 position set, my F7 was an artefact of profiling
`bench` (a single shallow search per position, repeated) rather than a real deep search.

Method (mine): I do not have their R_1911.fens, so I build my own PC-relevant set from the brief's own sources --
200 positions from O (tests_kimi5_job3/first200.fens) and the first 200 of G (tests_kimi5_job5/set_G.epd) -- and
profile `go depth 12` over each with perf task-clock sampling (the only event this unprivileged user can open).
Then I run the SAME profile on `bench 13` and compare the two rankings, which is exactly the comparison 19-F13
makes. Every parsed share is asserted to exist; a missing symbol aborts instead of printing 0.
"""
import re, subprocess, sys, os

EXE = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/check19f13"
os.makedirs(OUT, exist_ok=True)
PERF = "/usr/lib/linux-tools/6.8.0-149-generic/perf"

WANT = ["MovePicker::pick_best", "MovePicker::next(bool)", "probe_body", "see_ge", "fill_pseudo_legal",
        "Worker::search", "qsearch", "evaluate_position"]


def perf_profile(cmds, tag):
    """Drive the engine with `cmds` (piped, but the LAST command is `quit` only after all searches finish,
    so nothing is aborted -- see 19-F12), under perf record; return the flat symbol table."""
    data = os.path.join(OUT, f"{tag}.data")
    script = os.path.join(OUT, f"{tag}_driver.py")
    # CRITICAL (19-F12): write every command but read stdout to the FINAL token, so no search is aborted by
    # EOF or by an early `quit`. The old version wrote everything and waited, which aborted all 400 searches.
    with open(script, "w") as f:
        f.write(
            "import subprocess\n"
            f"cmds={cmds!r}\n"
            f"p=subprocess.Popen([{EXE!r}],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)\n"
            "out=[]\n"
            "for c in cmds[:-1]:\n"
            "    p.stdin.write(c+'\\n'); p.stdin.flush()\n"
            "    if c=='isready':\n"
            "        for line in p.stdout:\n"
            "            out.append(line)\n"
            "            if line.startswith('readyok'): break\n"
            "    elif c.startswith('go '):\n"
            "        for line in p.stdout:\n"
            "            out.append(line)\n"
            "            if line.startswith('bestmove'): break\n"
            "p.stdin.write('quit\\n'); p.stdin.flush(); p.wait()\n"
            "n=sum(1 for l in out if l.startswith('bestmove'))\n"
            "print('bestmoves:',n)\n"
            "assert n>0, 'ABORT: no bestmove -- harness protocol broken'\n")

    subprocess.run([PERF, "record", "-q", "-e", "task-clock", "-o", data,
                    sys.executable, script], check=False, capture_output=True)
    rep = subprocess.run([PERF, "report", "-i", data, "--stdio", "--no-children", "--percent-limit", "0.2"],
                         capture_output=True, text=True)
    return rep.stdout


def shares(report):
    got = {}
    for line in report.splitlines():
        m = re.match(r'^\s+([0-9]+\.[0-9]+)%\s+\S+\s+\S+\s+\[\S\]\s+(.*)$', line)
        if not m:
            continue
        pct, sym = float(m.group(1)), m.group(2).strip()
        for w in WANT:
            if w in sym and (w not in got or pct > got[w]):
                got[w] = pct
    return got


fens = []
for p in sys.argv[3:]:
    fens += [l.strip() for l in open(p) if l.strip()][:200]
if not fens:
    raise SystemExit("ABORT: no positions given")

print(f"positions: {len(fens)}  depth 12")

# --- deep-search profile (the "PC-relevant family" shape) ---
cmds = ["uci", "setoption name Hash value 16", "setoption name Threads value 1",
        "setoption name OwnBook value false", "isready"]
for fen in fens:
    cmds += [f"position fen {fen}", "go depth 12"]
cmds += ["quit"]
deep = shares(perf_profile(cmds, "deep"))

# --- bench 13 profile (what I profiled for F7) ---
bench = shares(perf_profile(["uci", "setoption name Hash value 16",
                             "setoption name Threads value 1", "isready", "bench 13", "quit"], "bench"))

rows = []
for w in WANT:
    d = deep.get(w)
    b = bench.get(w)
    rows.append((w, d, b))
    print(f"{w:28s} deep-search {('%.2f%%' % d) if d is not None else 'NOT FOUND':>9}   "
          f"bench13 {('%.2f%%' % b) if b is not None else 'NOT FOUND':>9}")

missing = [w for w, d, b in rows if d is None or b is None]
if missing:
    print(f"\nNOTE: {missing} did not appear in one of the two profiles (too small to sample). "
          "No conclusion is drawn for those.")

pb_d, pb_b = deep.get("MovePicker::pick_best"), bench.get("MovePicker::pick_best")
nx_d, nx_b = deep.get("MovePicker::next(bool)"), bench.get("MovePicker::next(bool)")
print()
if None in (pb_d, nx_d, pb_b, nx_b):
    print("VERDICT: INCONCLUSIVE -- a required symbol was not sampled; refusing to judge 19-F13.")
else:
    print(f"deep search : pick_best {pb_d:.2f}% vs next {nx_d:.2f}%  -> "
          f"{'pick_best HOTTER (19-F13 direction)' if pb_d > nx_d else 'next hotter (my F7 direction)'}")
    print(f"bench 13    : pick_best {pb_b:.2f}% vs next {nx_b:.2f}%  -> "
          f"{'pick_best hotter' if pb_b > nx_b else 'next hotter'}")
    ok = pb_d > nx_d
    print("VERDICT:", "CONFIRMS 19-F13 (pick_best outranks next on a deep position set)" if ok
          else "REFUTES 19-F13 (pick_best does not outrank next on my deep position set)")
