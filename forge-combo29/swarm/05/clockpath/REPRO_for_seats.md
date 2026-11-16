# REPRO for seats: the wtime clock path spends ~2-4% of its budget (seat 05, S-F37/S-F38/S-F39)

**One command, one file, no dependencies beyond python3.** Copy this file into your own folder, point it at YOUR
PC-build (or base-build) exe, and run it. If your numbers match mine, send a C line confirming S-F37.

## What to check

The owner's strength matches use `go wtime 6000 btime 6000 winc 60 binc 60`. On that command the engine reaches
about depth 19 in 0.23-0.36 s — it does not spend the 6 seconds. `go movetime 6000` on the same board spends 5.99 s
and reaches depth 27. Do you see the same?

## The script

```python
#!/usr/bin/env python3
"""clock_confirm.py EXE -- confirm seat 05's S-F37/S-F38/S-F39 on YOUR build.
Usage: python3 clock_confirm.py /path/to/your/forge
Reports: for startpos, `go wtime 6000 ...` vs `go movetime 6000`: wall time, depth, nodes, and the ratio
time-used / budget. Threads 1, Hash 16, OwnBook false (send OwnBook false or the book answers startpos)."""
import re, subprocess, sys, time

EXE = sys.argv[1]
OPTS = ["setoption name Threads value 1", "setoption name Hash value 16",
        "setoption name OwnBook value false",
        # PC20's six, harmless if your build knows them; drop this block on a base build
        "setoption name CuckooRep value true", "setoption name HistRework value 2",
        "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
        "setoption name MateAlphaGuard value true"]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")

def one(go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []
    def s(x): p.stdin.write(x + "\n"); p.stdin.flush()
    def u(t, lim=120):
        t0 = time.time()
        while time.time() - t0 < lim:
            l = p.stdout.readline()
            if l == "": return False
            l = l.rstrip(); L.append(l)
            if any(b in l for b in BAD): return False
            if l.startswith(t): return True
        return False
    s("uci"); u("uciok")
    for o in OPTS:
        s(o); s("isready")
        if not u("readyok"): p.kill(); return None
    s("ucinewgame"); s("isready"); u("readyok")
    s("position startpos"); s("isready"); u("readyok")
    t0 = time.monotonic(); s(go); ok = u("bestmove"); wall = time.monotonic() - t0
    s("quit")
    try: p.wait(timeout=20)
    except Exception: p.kill()
    if not ok: return None
    pv = [x for x in L if " pv " in x]; last = pv[-1] if pv else ""
    d = re.search(r"depth (\d+)", last); n = re.search(r"\bnodes (\d+)", last)
    book = any("book move" in x for x in L)
    return dict(wall=wall, depth=int(d.group(1)) if d else None,
                nodes=int(n.group(1)) if n else None, book=book)

BUDGET_MS = 6000
for label, go in (("wtime 6000+winc 60", "go wtime 6000 btime 6000 winc 60 binc 60"),
                  ("movetime 6000", "go movetime 6000")):
    r = one(go)
    if r is None:
        print(f"{label:22s} REFUSED / no bestmove (check the option list for your build)")
        continue
    pct = 100.0 * (r["wall"] * 1000) / BUDGET_MS
    print(f"{label:22s} wall {r['wall']:.2f}s  depth {r['depth']}  nodes {r['nodes']}  "
          f"used {pct:.1f}% of budget  book_line={r['book']}")
```

## What I measured (PC r15 + PC20, Threads 1, Hash 16, OwnBook false, 5 runs each)

| go | wall | depth | nodes | % of 6 s |
|---|---|---|---|---|
| `go wtime 6000 btime 6000 winc 60 binc 60` | 0.35-0.36 s | 19 | 650,246 | **~6 %** |
| `go movetime 6000` | 5.99 s | 27 | 7,061,631 | ~100 % |

Base build + S14 showed the same gap (0.23 s / d19 vs 5.99 s / d27 on startpos).

And varying only the clock (startpos) shows the allocation *ratio*, not a depth cap:

| clock | engine time | depth | used/clock |
|---|---|---|---|
| 1,000 ms | 95 ms | 15 | 9.5 % |
| 6,000 ms | 234 ms | 19 | 3.9 % |
| 30,000 ms | 911 ms | 21 | 3.0 % |
| 120,000 ms | 2,583 ms | 25 | 2.2 % |

## Tested note on this exact script

I ran the snippet above exactly as published, against my PC r15 build, and it gave:

```
wtime 6000+winc 60     wall 0.17s  depth 17  nodes 325076  used 2.9% of budget  book_line=False
movetime 6000          wall 5.99s  depth 24  nodes 8464586  used 99.8% of budget  book_line=False
```

Those absolute numbers differ slightly from my table above because this script sends only the six PC20 options and
**not** the full S14 set, so the search is a different (weaker) configuration — 2.9 % used at depth 17 rather than
3.9 % at depth 19. The GAP is the same either way, which is the point: `movetime` spends 99.8 % where `wtime`
spends 2.9 %. If you want the exact configuration of my table, add S14's 14 setoptions before the six.

## How to confirm

Run the script; if your `wtime 6000` uses a small fraction of the budget while `movetime 6000` uses nearly all of
it, that is the confirmation. Please send a C line with your build, settings and the two rows.

Evidence on my branch: `forge-combo29/swarm/05/clockpath/out/{clock_repro.txt,clock_cap.txt}`.
