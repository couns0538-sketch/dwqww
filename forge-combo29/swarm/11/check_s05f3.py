#!/usr/bin/env python3
"""check_s05f3.py EXE — seat 11's INDEPENDENT check of seat 05's S-F3 (fifty-move threshold).

S-F3: "The fifty-move draw is applied about 9 plies early: `1K6/8/8/3R4/8/8/8/k7 w - - H 1` at
`go depth 10` scores `cp 472` for H=0..75, `cp 314` at H=90, then exactly `cp 0` from H=91."

Uses ucio.Engine, which WAITS for bestmove before sending anything else. A fully-piped run
makes `quit` abort the search and prints no info lines at all — my first attempt used that and
measured nothing, so this file exists.

Controls: bare kings must be drawish at H=0; KRvK at H=0 must NOT be.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucio import Engine

EXE = sys.argv[1]
KRK = "1K6/8/8/3R4/8/8/8/k7 w - - {h} 1"
BARE = "1K6/8/8/8/8/8/8/k7 w - - {h} 1"


def probe(fen, depth=10):
    e = Engine(EXE, options=["OwnBook false"], timeout=300)
    e.start()
    try:
        answer, refused = e.position(fen=fen)
        if refused:
            return {"status": "REFUSED", "detail": refused}
        infos, bm, allines = e.go(f"go depth {depth}")
        scored = [(int(m.group(1)), int(m.group(2)))
                  for l in infos
                  for m in [re.search(r"depth (\d+).*score (cp|mate) (-?\d+)", l)] if m]
        last = None
        for l in infos:
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                last = (m.group(1), int(m.group(2)))
        return {"status": "no-info" if not infos else "scored", "last": last,
                "n_info": len(infos), "bestmove": bm, "san": e.drain_stderr()}
    finally:
        e.quit()


def drawish(r):
    return r["status"] == "no-info" or r.get("last") == ("cp", 0)


print("=== the curve (KRvK, go depth 10, wait for bestmove) ===")
print(f"{'H':>4} {'status':>8} {'n_info':>7} {'last score':>14}  bestmove")
sweep = [0, 50, 75, 85, 88, 90, 91, 92, 95, 99, 100]
res = {}
for h in sweep:
    r = probe(KRK.format(h=h))
    res[h] = r
    print(f"{h:>4} {r['status']:>8} {r.get('n_info',0):>7} {str(r.get('last')):>14}  {r.get('bestmove')}")

print("\n=== controls ===")
bare = probe(BARE.format(h=0))
print(f"  bare kings H=0 : {bare['status']} {bare.get('last')} (must be drawish)")

print("\n=== verdict on S-F3 ===")
ok = True
def chk(n, c, d=""):
    global ok
    ok = ok and c
    print(f"  {'PASS' if c else 'FAIL'}  {n}{('  — ' + d) if d else ''}")

chk("KRvK at H=0 is a real search with a non-zero score", not drawish(res[0]),
    f"{res[0]['status']} {res[0].get('last')}")
chk("bare kings at H=0 is drawish (control)", drawish(bare), f"{bare['status']} {bare.get('last')}")
dh = [h for h in sweep if drawish(res[h])]
print(f"  drawish at H = {dh}")
chk("H=90 is still a win (S-F3 says cp 314)", not drawish(res[90]), f"{res[90].get('last')}")
chk("the first drawish H is 91 (S-F3's claim)", (min(dh) if dh else None) == 91,
    f"first drawish H = {min(dh) if dh else None}")

print()
if ok:
    print("RESULT: CONFIRMS S-F3 — the fifty-move draw takes effect at H=91, nine plies early.")
    print("        The 472/314 centipawn VALUES are printed above for comparison; I do not")
    print("        assert them because seat 05 may have used a different depth/option set.")
else:
    print("RESULT: does NOT reproduce S-F3 as stated; the curve above is the evidence.")
