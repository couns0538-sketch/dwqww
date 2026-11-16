#!/usr/bin/env python3
"""uci_drive.py EXE -- interactive UCI driver used by the authority check and by every probe.
Reads a JSON job on argv[1]: {"options": [...], "positions": [{"fen":..., "go": "go depth 12"}],
"movetime_cap_s": 120}
Never pre-feeds quit (that aborts a search); reads every line up to readyok after setoption/position and
STOPS on unknown option / invalid value / invalid FEN / illegal move.
Prints, per position, the last `info ... pv` line, the score, and the bestmove line.
"""
import json
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
JOB = json.load(open(sys.argv[2]))
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        self.until("uciok")

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def until(self, token, limit=600.0):
        got = []
        deadline = time.time() + limit
        while time.time() < deadline:
            line = self.p.stdout.readline()
            if line == "":
                got.append("### EOF")
                return got
            line = line.rstrip("\n")
            got.append(line)
            if line.startswith(token):
                return got
            for b in BAD:
                if b in line:
                    got.append("### HARNESS_STOP " + b)
                    return got
        got.append("### TIMEOUT")
        return got

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


cap = JOB.get("movetime_cap_s", 120)
e = Engine(EXE)
for o in JOB.get("options", []):
    e.send(o)
    e.send("isready")
    r = e.until("readyok")
    if any("### HARNESS_STOP" in x or "### TIMEOUT" in x or "### EOF" in x for x in r):
        print(f"HARNESS_STOP after option {o}: {[x for x in r if x.startswith('###')]}")
        e.close()
        sys.exit(2)
e.send("ucinewgame")
e.send("isready")
e.until("readyok")
for pos in JOB["positions"]:
    fen = pos["fen"] if pos.get("fen") else "startpos"
    e.send(f"position fen {fen}" if pos.get("fen") else "position startpos")
    e.send("isready")
    r = e.until("readyok")
    if any("### HARNESS_STOP" in x for x in r):
        print(f"### pos fen={fen} HARNESS_STOP position refused: "
              f"{[x for x in r if x.startswith('###')]}")
        continue
    e.send(pos["go"])
    block = e.until("bestmove", cap)
    pv = [l for l in block if re.search(r"\binfo\b.*\bpv\b", l)]
    bm = [l for l in block if l.startswith("bestmove")]
    print(f"### pos fen={fen} go=\"{pos['go']}\"")
    if pv:
        print("last_pv: " + pv[-1])
        m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
        print(f"score: {m.group(1)} {m.group(2)}" if m else "score: (absent)")
    else:
        print("last_pv: (none)")
    print(f"bestmove_line: {bm[0] if bm else '(none)'}")
    tail = [x for x in block if x.startswith("###")]
    if tail:
        print("notes: " + "; ".join(tail))
e.close()
