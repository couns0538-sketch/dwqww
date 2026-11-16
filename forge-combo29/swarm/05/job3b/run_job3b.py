#!/usr/bin/env python3
"""run_job3.py EXE OUTDIR [LABEL] -- job 3: checkmated and stalemated ROOT positions (10 each) with three
different go commands each (`go depth 5`, `go nodes 100`, `go movetime 50`), capturing the exact answer lines and
any sanitizer output. One fresh process per (position, go) pair.

Sanitizer discipline:
  * ASAN_OPTIONS and UBSAN_OPTIONS are CLEARED for every child unless --keep-env is passed;
  * an empty environment is not assumed: the runner records, in the .meta, the sanitizer env it set;
  * crashes, sanitizer lines and hangs are counted, not swallowed.
"""
import hashlib
import os
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
OUT = sys.argv[2]
LABEL = sys.argv[3] if len(sys.argv) > 3 else "run"
KEEP_ENV = "--keep-env" in sys.argv
HANG_S = 30
os.makedirs(OUT, exist_ok=True)

S14 = [
    "setoption name Threads value 1", "setoption name Hash value 16",
    "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
]
GO_CMDS = ["go depth 5", "go nodes 100", "go movetime 50"]

# Ten checkmate positions (side to move is CHECKMATED) and ten stalemate positions. Each was checked with
# python-chess in make_roots.py, which writes these same files.
def read_epd(name):
    with open(f"positions/{name}.epd") as f:
        return [l.strip() for l in f if l.strip()]


MATE_POS = read_epd("mate_root_521")
STALE_POS = read_epd("stale_root_521")
assert len(MATE_POS) == 10 and len(STALE_POS) == 10, (len(MATE_POS), len(STALE_POS))

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")
SAN = re.compile(r"(AddressSanitizer|UndefinedBehaviorSanitizer|runtime error|LeakSanitizer|SUMMARY:)")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def env_for_child():
    e = dict(os.environ)
    if not KEEP_ENV:
        e.pop("ASAN_OPTIONS", None)
        e.pop("UBSAN_OPTIONS", None)
        e.pop("TSAN_OPTIONS", None)
        e.pop("LSAN_OPTIONS", None)
    return e


def run_one(fen, go_cmd):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1, env=env_for_child())
    out = []
    crashed = False
    hung = False

    def send(s):
        try:
            p.stdin.write(s + "\n")
            p.stdin.flush()
        except Exception:
            pass

    send("uci")
    send("isready")
    for o in S14:
        send(o)
        send("isready")
    send("ucinewgame")
    send("isready")
    send(f"position fen {fen}")
    send("isready")
    send(go_cmd)
    # read until bestmove or timeout
    deadline = time.time() + HANG_S
    got_best = False
    while time.time() < deadline:
        line = p.stdout.readline()
        if line == "":
            break
        out.append(line.rstrip("\n"))
        if line.startswith("bestmove"):
            got_best = True
            break
    if not got_best:
        hung = True
        try:
            p.kill()
        except Exception:
            pass
    send("quit")
    try:
        rc = p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
        rc = -9
    # drain whatever is left (sanitizer report comes after)
    try:
        rest = p.stdout.read()
        if rest:
            out += rest.splitlines()
    except Exception:
        pass
    if rc not in (0, None) and not hung:
        crashed = True
    if any(SAN.search(x) for x in out):
        crashed = True
    return out, crashed, hung, rc


with open(f"{OUT}/meta.txt", "w") as m:
    m.write(f"label: {LABEL}\n")
    m.write(f"exe_started: {os.path.abspath(EXE)}\n")
    m.write(f"sha256: {sha256(EXE)}\n")
    m.write(f"nm_asan_symbols: {subprocess.run(['bash','-lc',f'nm -C {EXE} | grep -c __asan_'],capture_output=True,text=True).stdout.strip()}\n")
    m.write(f"nm_ubsan_symbols: {subprocess.run(['bash','-lc',f'nm -C {EXE} | grep -c __ubsan_'],capture_output=True,text=True).stdout.strip()}\n")
    m.write(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
    m.write(f"ASAN_OPTIONS_kept: {KEEP_ENV}   env_in_child: "
            f"{'inherited' if KEEP_ENV else 'ASAN_OPTIONS/UBSAN_OPTIONS/TSAN_OPTIONS/LSAN_OPTIONS removed'}\n")
    m.write("option lines sent (isready after each):\n")
    for o in S14:
        m.write("  " + o + "\n")
    m.write("go lines: " + "; ".join(GO_CMDS) + "\n")
    mm = subprocess.run([EXE], input="uci\nquit\n", capture_output=True, text=True,
                        env=env_for_child())
    for l in mm.stdout.splitlines():
        if l.startswith("id name"):
            m.write("id_name: " + l + "\n")

rows = []
for kind, poslist in (("mate", MATE_POS), ("stale", STALE_POS)):
    path = f"{OUT}/{kind}.raw.txt"
    with open(path, "w") as f:
        for i, fen in enumerate(poslist):
            for go_cmd in GO_CMDS:
                f.write(f"### pos {i} {kind} go=\"{go_cmd}\" {fen}\n")
                lines, crashed, hung, rc = run_one(fen, go_cmd)
                for l in lines:
                    f.write(l + "\n")
                f.write(f"### end crashed={crashed} hung={hung} rc={rc}\n")
                f.flush()
                best = next((l for l in lines if l.startswith("bestmove")), "(none)")
                san = [l for l in lines if SAN.search(l)]
                info = [l for l in lines if " pv " in l]
                rows.append((kind, i, go_cmd, best, len(san), crashed, hung,
                             info[-1] if info else "(no pv)"))
                print(f"{kind} {i:2d} {go_cmd:16s} {best:20s} san={len(san)} crashed={crashed} hung={hung}")

with open(f"{OUT}/table.txt", "w") as f:
    f.write("| kind | pos | go | bestmove | sanitizer lines | crashed | hung | last pv |\n")
    f.write("|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        f.write(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | {r[7][:80]} |\n")
print(f"\ntotal runs: {len(rows)}  sanitizer lines: {sum(r[4] for r in rows)}  "
      f"crashes: {sum(1 for r in rows if r[5])}  hangs: {sum(1 for r in rows if r[6])}")
