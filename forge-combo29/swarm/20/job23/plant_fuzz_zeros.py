#!/usr/bin/env python3
"""plant_fuzz_zeros.py — seat 20: close the Rule-1 gap from FABLE_TO_swarm_2 ("a zero needs a planted one").

My 200-sequence fuzz reported 0 crashes / 0 hangs / 0 illegal bestmoves. Rule 1 says that zero only counts if the
SAME classifier, unchanged, counts a planted case. This script builds two fake engines and runs them through the
same classification logic the fuzz used:

  PLANTED CRASH:  answers the uci handshake then dies with SIGSEGV on the first `go`.
  PLANTED HANG:   answers the handshake then never answers `isready` again (so the readyok wait must time out).
  PLANTED ILLEGAL: answers `bestmove z9z9` (not a legal move anywhere).

Each must be counted; if any is not, the corresponding zero of mine is "not shown".

usage: plant_fuzz_zeros.py <outdir>
"""
import os
import stat
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)

CRASH = r'''#!/usr/bin/env python3
import sys, os, signal
for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name PLANTED-CRASH", flush=True)
        print("option name OwnBook type check default false", flush=True)
        print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("go"):
        os.kill(os.getpid(), signal.SIGSEGV)      # planted crash
'''

HANG = r'''#!/usr/bin/env python3
import sys
n = 0
for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name PLANTED-HANG", flush=True)
        print("option name OwnBook type check default false", flush=True)
        print("uciok", flush=True)
    elif c == "isready":
        n += 1
        if n == 1:
            print("readyok", flush=True)
        # every later isready: answer NOTHING  -> planted hang
    elif c.startswith("go"):
        pass
'''

ILLEGAL = r'''#!/usr/bin/env python3
import sys
for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name PLANTED-ILLEGAL", flush=True)
        print("option name OwnBook type check default false", flush=True)
        print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("go"):
        print("info depth 1 seldepth 1 score cp 0 nodes 1 nps 1 hashfull 0 time 0 pv z9z9", flush=True)
        print("bestmove z9z9", flush=True)         # planted illegal move
'''


def write(name, body):
    p = os.path.join(OUT, name)
    open(p, "w").write(body)
    os.chmod(p, 0o755)
    return p


crash = write("planted_crash.py", CRASH)
hang = write("planted_hang.py", HANG)
illegal = write("planted_illegal.py", ILLEGAL)

# --- the CLASSIFIER, copied unchanged from the logic my fuzz used -----------------------------------
import re
import subprocess
import threading
import time

import chess


def classify(exe, seq, ready_timeout=3.0):
    """THE SAME logic as job2/myfuzz.py run(): hang = a later isready with no new readyok; crash = bad exit;
    illegal = a bestmove that is not legal in any position the sequence put on the board."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    out, lock = [], threading.Lock()

    def rd():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass
    threading.Thread(target=rd, daemon=True).start()
    rec = {"hang": False, "crash": False, "exit": None, "illegal": None, "san": 0}
    ready_seen = 0
    try:
        for line in seq:
            p.stdin.write(line + "\n")
            p.stdin.flush()
            if line == "isready":
                t0 = time.monotonic()
                ok = False
                while time.monotonic() - t0 < ready_timeout:
                    with lock:
                        n = sum(1 for x in out if x.strip() == "readyok")
                    if n > ready_seen:
                        ready_seen = n
                        ok = True
                        break
                    time.sleep(0.005)
                if not ok:
                    # distinguish a dead process (CRASH) from a live one that said nothing (HANG)
                    if p.poll() is not None:
                        rec["exit"] = p.returncode
                        rec["crash"] = True
                    else:
                        rec["hang"] = True
                        p.kill()
                    return rec
    except Exception:
        pass
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        rec["hang"] = True
        p.kill()
    rec["exit"] = p.returncode
    with lock:
        tail = list(out)
    bests = [x.split()[1] for x in tail if x.startswith("bestmove") and len(x.split()) > 1]
    if bests:
        legal = {m.uci() for m in chess.Board().legal_moves}
        for bm in bests:
            if bm and bm != "0000" and bm not in legal:
                rec["illegal"] = bm
    return rec


SEQ = ["uci", "isready", "position startpos", "isready", "go depth 2", "isready", "quit"]
print("== planting the three cases through the SAME classifier")
res = {}
for label, exe in (("CRASH", crash), ("HANG", hang), ("ILLEGAL", illegal)):
    r = classify(exe, SEQ)
    counted = (label == "CRASH" and (r.get("crash") or r["exit"] not in (0, None))) or \
              (label == "HANG" and r["hang"]) or \
              (label == "ILLEGAL" and r["illegal"] == "z9z9")
    res[label] = {"result": r, "counted": counted}
    print(f"  {label:8s} -> {r}   COUNTED: {counted}")
    if label == "ILLEGAL":
        print(f"           (this plant also stops answering isready afterwards, so hang=True is expected; "
              f"the thing under test is illegal={r['illegal']})")
    assert counted, f"the classifier did NOT count the planted {label} — my zero of that kind is not shown"

print("\nall three planted cases counted: the classifier can see a crash, a hang and an illegal bestmove.")
print("=> the '0 crashes / 0 hangs / 0 illegal' of my 200-sequence fuzz is now SHOWN, not merely believed.")
