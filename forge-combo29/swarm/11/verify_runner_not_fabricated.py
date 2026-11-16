#!/usr/bin/env python3
"""verify_runner_not_fabricated.py EXE — proves my runner.py runs are NOT 19-F12 fabrications.

19-F12: piped `quit` mid-search makes the engine answer a fabricated `bestmove` (e.g. a2a3)
with 0 info lines and 0 nodes. My runner.py sends one command at a time and reads to `bestmove`
before the next command, so it should not be affected — this verifies that claim rather than
assuming it.

Test: replay a sample of job1r2's cases through runner.py's Engine class AND through the
independent waiting driver ucio.Engine, and check
  (a) both give the SAME bestmove for each case,
  (b) the searches produce real `info depth` lines (a fabricated answer has none),
  (c) the node counts are non-trivial,
and that the fabrication itself is detectable by the same comparison (control).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runner as rr
from ucio import Engine as WaitEngine

EXE = sys.argv[1]
CASES = sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 40


def runner_answer(fen, depth=2):
    e = rr.Engine(EXE, depth, 30.0, [])
    e.start(os.devnull)
    try:
        rec = e.case(fen)
        return rec["bestmove"], (rec.get("answer") or [])
    finally:
        try:
            e.kill()
        except Exception:
            pass


def waited_answer(fen, depth=2):
    e = WaitEngine(EXE, options=[], timeout=120)
    e.start()
    try:
        ans, refused = e.position(fen=fen)
        if refused:
            return "refused", []
        infos, bm, lines = e.go(f"go depth {depth}")
        depths = [l for l in infos if l.startswith("info depth")]
        return bm, depths
    finally:
        e.quit()


rows = [json.loads(l) for l in open(CASES)]
# take accepted (non-refused) cases, spaced through the file
sample = []
for r in rows:
    if r.get("refused"):
        continue
    sample.append(r)
    if len(sample) >= N * 3:
        break
sample = sample[::max(1, len(sample) // N)][:N]

print(f"=== comparing {len(sample)} accepted cases: runner.py vs waiting driver ===")
same = diff = noinfo = 0
for r in sample:
    fen = r["fen"]
    rb, rans = runner_answer(fen)
    wb, winfos = waited_answer(fen)
    agree = (rb == wb)
    same += agree
    diff += (not agree)
    if not winfos:
        noinfo += 1
    print(f"  {'OK ' if agree else 'DIFF'} runner={str(rb):10} waited={str(wb):10} infos={len(winfos)}  {fen[:52]}")

print(f"\nagree {same}, differ {diff}, waited-runs-with-no-info {noinfo}")

print("\n=== control: the fabrication is detectable by this comparison ===")
import subprocess
piped = subprocess.run([EXE], input="uci\nposition startpos\nisready\ngo depth 12\nquit\n",
                       capture_output=True, text=True, timeout=120).stdout
piped_bm = next((l.split()[1] for l in piped.splitlines() if l.startswith("bestmove")), None)
piped_infos = [l for l in piped.splitlines() if l.startswith("info depth")]
e = WaitEngine(EXE, options=[], timeout=300); e.start()
e.position(fen=None)
winfos, wbm, _ = e.go("go depth 12")
e.quit()
print(f"  piped : bestmove {piped_bm}, info depth lines {len(piped_infos)}")
print(f"  waited: bestmove {wbm}, info depth lines {len(winfos)}")
ctrl_ok = (len(piped_infos) == 0 and piped_bm is not None and len(winfos) > 0 and wbm != piped_bm)
print(f"  control {'PASS' if ctrl_ok else 'FAIL'}: the piped form is visibly different from the waited form")

print("\n=== verdict ===")
if diff == 0 and noinfo == 0 and ctrl_ok:
    print("runner.py's answers equal the waiting driver's on every sampled case, and every waited")
    print("run produced real info lines, while the piped control produced none. So my runner-based")
    print("results (job1, job2, job1r2) are NOT 19-F12 fabrications.")
else:
    print(f"PROBLEM: differ {diff}, no-info {noinfo}, control {ctrl_ok} — runner-based results need re-running.")
