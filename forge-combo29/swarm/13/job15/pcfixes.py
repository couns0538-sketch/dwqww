#!/usr/bin/env python3
"""Verify the PC patch's enabled fixes that can be tested from UCI.

FABLE file 5's patch declares seven fixes. Reading the patch comments (not guessing), their state is:

  FORGE_FIX_ROOT_DRAWN            1   (default on)  -> verified separately as S-F17
  FORGE_FIX_HARD_LIMIT_EMERGENCY  1   (default on)  -> TESTED HERE
  FORGE_FIX_BARE_KING_LMR_CAP     1   (default on)  -> TESTED HERE
  FORGE_FIX_GO_PARSE              1   (default on)  -> TESTED HERE
  FORGE_FIX_ISREADY_PENDING       1   (default on)  -> TESTED HERE
  FORGE_FIX_BARE_KING_ONE_THREAD  0   (OFF since 16:30; patch says it fixes mates but loses hard endings)
  FORGE_FIX_ABORT_PUBLISH         0   (OFF since 16:45; patch says measured, "it is not a repair")

The two OFF switches are a finding in themselves: they are declared but compiled out, so a reader who
assumes "the patch fixes X" for those two is wrong.

Tests (all fresh process, Threads 1, Hash 16, OwnBook false):
  T1 GO_PARSE: `go wtime btime 50` (no value after wtime) — patch says r9 lost the clock here.
     On the PC build the clock must survive: the search should use time, not answer instantly unsearched.
  T2 GO_PARSE control: `go wtime 50 btime 50` must NOT be broken by the fix (normal clock honoured).
  T3 HARD_LIMIT_EMERGENCY: `go wtime 11 btime 11` (hard limit already passed before search starts) —
     patch says it must play the hash move or search one ply with <=2000 nodes, NOT an unsearched first
     legal move. Distinguish: an unsearched answer has 0 nodes; the fix should give >0 nodes or a hash
     move. Compare against `go wtime 10`.
  T4 ISREADY_PENDING: cannot exercise without NNUEArch, which this build does not advertise; recorded
     as untestable here rather than claimed.
  T5 BARE_KING_LMR_CAP: needs a lone-king rooting position and warm history at depth 14 to show missed
     mates. A cheap smoke test only: a K+R vs K mate must still be found. A full test is out of scope
     for this script and is stated as such.

Usage: pcfixes.py BASE_EXE PC_EXE OUTDIR
"""
import json
import os
import re
import subprocess
import sys
import time

BASE_EXE = sys.argv[1]
PC_EXE = sys.argv[2]
OUTDIR = sys.argv[3]
os.makedirs(OUTDIR, exist_ok=True)
OPTS = [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")]
BAD = ("unknown option", "invalid value", "error")


def run(exe, pos_cmd, go_cmd, limit=10.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            l = p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died")
            l = l.rstrip("\n")
            if any(x in l.lower() for x in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if pred(l):
                return l

    send("uci")
    seen = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died in uci handshake")
        l = l.rstrip("\n")
        if l.startswith("option name"):
            seen.append(l)
        if l == "uciok":
            break
    for n, v in OPTS:
        if not any(o.startswith("option name %s " % n) for o in seen):
            continue
        send("setoption name %s value %s" % (n, v))
        send("isready")
        until(lambda s: s == "readyok")
    send(pos_cmd)
    send("isready")
    until(lambda s: s == "readyok")

    t0 = time.monotonic()
    send(go_cmd)
    last = None
    bm = None
    infos = 0
    # read with a deadline so a hang is reported as a timeout, not an infinite loop
    p.stdout.flush()
    while time.monotonic() - t0 < limit:
        l = p.stdout.readline()
        if not l:
            break
        l = l.rstrip("\n")
        if l.startswith("info depth"):
            last = l
            infos += 1
        if l.startswith("bestmove"):
            bm = l
            break
    elapsed = time.monotonic() - t0
    try:
        send("quit")
        p.wait(timeout=5)
    except Exception:
        p.kill()

    def g(pat):
        m = re.search(pat, last) if last else None
        return int(m.group(1)) if m else None

    return {"bestmove": (bm.split()[1] if bm and len(bm.split()) > 1 else None),
            "info_lines": infos, "nodes": g(r"\bnodes (\d+)"),
            "depth": g(r"\bdepth (\d+)"), "cp": g(r"\bscore cp (-?\d+)"),
            "mate": g(r"\bscore mate (-?\d+)"),
            "seconds": round(elapsed, 3), "answered": bm is not None}


START = "position startpos"
# Verified with python-chess: is_valid() True and no STATUS_OPPOSITE_CHECK.
# (My first attempt used 7k/8/6K1/8/8/8/8/7R, which is STATUS_OPPOSITE_CHECK - black in check with
#  WHITE to move - so the engine refused the FEN, kept startpos, and "answered" e2e4. That looked like
#  an illegal move from the engine and was entirely my test's fault.)
MATE_KRK = "position fen 6k1/8/5K2/8/8/8/8/7R w - - 0 1"

cases = [
    ("T1 go wtime btime 50 (GO_PARSE: clock must survive)", START, "go wtime btime 50"),
    ("T2 go wtime 50 btime 50 (GO_PARSE control)", START, "go wtime 50 btime 50"),
    ("T3a go wtime 11 btime 11 (HARD_LIMIT_EMERGENCY)", START, "go wtime 11 btime 11"),
    ("T3b go wtime 10 btime 10 (comparison)", START, "go wtime 10 btime 10"),
    ("T5 K+R vs K mate must be found (BARE_KING cap smoke)", MATE_KRK, "go depth 14"),
]

rows = []
for label, pos, go in cases:
    row = {"case": label, "position": pos, "go": go}
    for tag, exe in (("base", BASE_EXE), ("pc", PC_EXE)):
        try:
            row[tag] = run(exe, pos, go)
        except SystemExit as e:
            row[tag] = {"error": str(e)}
    rows.append(row)
    print("%-52s base: %s" % (label, json.dumps(row["base"])))
    print("%-52s pc  : %s" % ("", json.dumps(row["pc"])), flush=True)

out = {"base_exe": os.path.abspath(BASE_EXE), "pc_exe": os.path.abspath(PC_EXE),
       "rows": rows, "untestable": {
           "FORGE_FIX_ISREADY_PENDING":
               "needs NNUEArch, which this build does not advertise; not claimed either way",
           "FORGE_FIX_BARE_KING_LMR_CAP":
               "full test needs lone-king roots with warm history at depth 14 (missed-mate counting); "
               "only a smoke test that K+R vs K is still mated is done here",
           "FORGE_FIX_BARE_KING_ONE_THREAD": "compiled OUT (default 0)",
           "FORGE_FIX_ABORT_PUBLISH": "compiled OUT (default 0)",
       }}
json.dump(out, open(os.path.join(OUTDIR, "pcfixes.json"), "w"), indent=1)
print()
print("Two of the seven fixes are compiled OUT by default — see the summary in REPORT_pcfixes.md.")
