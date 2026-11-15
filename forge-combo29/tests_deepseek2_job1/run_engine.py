#!/usr/bin/env python3
"""Job 1 part B runner: drive Forge over UCI.

Modes
  fresh       one process per case: position fen S0 moves <full list>, go depth 12
  warmed      one process per case, NO ucinewgame: at every position where the
              BARE KING is to move, send `position fen S0 moves <prefix>` and the
              search, read bestmove, then continue with the list's move anyway.
  warmclear   like warmed, but `setoption name Clear Hash` right before the last
              search (B4 minimal-change experiment)

Every engine line is kept; the per-case record holds the bestmove and the last
info line before it.
"""

import json
import subprocess
import sys
import time

ENGINE = sys.argv[1] if len(sys.argv) > 1 else "forge"
CASES = sys.argv[2] if len(sys.argv) > 2 else "cases.json"
MODE = sys.argv[3] if len(sys.argv) > 3 else "fresh"
OUT = sys.argv[4] if len(sys.argv) > 4 else "out.json"
LIMIT = sys.argv[5] if len(sys.argv) > 5 else "depth 12"
HASH = sys.argv[6] if len(sys.argv) > 6 else "16"
ONLY = int(sys.argv[7]) if len(sys.argv) > 7 else -1   # optional case cap


class Engine:
    def __init__(self):
        self.p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        self.until("uciok")

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def until(self, token, timeout=60.0):
        lines = []
        t0 = time.time()
        while True:
            line = self.p.stdout.readline()
            if line == "":
                raise RuntimeError("engine died waiting for " + token)
            line = line.strip()
            lines.append(line)
            if line.startswith(token):
                return lines
            if time.time() - t0 > timeout:
                raise RuntimeError("timeout waiting for " + token)

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def search(eng, pos_cmd, limit):
    eng.send(pos_cmd)
    eng.send("go " + limit)
    lines = eng.until("bestmove", timeout=180)
    best = None
    last_info = None
    for ln in lines:
        if ln.startswith("info") and " score " in ln:
            last_info = ln
        if ln.startswith("bestmove"):
            best = ln.split()[1]
    return best, last_info, lines


def main():
    data = json.load(open(CASES))
    cases = data["cases"]
    if ONLY > 0:
        cases = cases[:ONLY]
    recs = []
    t0 = time.time()
    for idx, c in enumerate(cases):
        s0, moves, want = c["s0"], c["moves"], c["rep_move"]
        pos_full = "position fen " + s0 + " moves " + " ".join(moves)
        rec = {"i": idx, "s0": s0, "moves": moves, "want": want, "searches": []}
        try:
            if MODE == "fresh":
                eng = Engine()
                eng.send("setoption name Threads value 1")
                eng.send("setoption name Hash value " + HASH)
                eng.send("isready")
                eng.until("readyok")
                best, info, lines = search(eng, pos_full, LIMIT)
                eng.quit()
                rec["searches"].append({"prefix": 7, "best": best, "info": info})
            else:
                eng = Engine()
                eng.send("setoption name Threads value 1")
                eng.send("setoption name Hash value " + HASH)
                eng.send("isready")
                eng.until("readyok")
                # black to move after 1, 3, 5 and 7 plies
                for k in (1, 3, 5, 7):
                    prefix = "position fen " + s0 + " moves " + " ".join(moves[:k])
                    if MODE == "warmclear" and k == 7:
                        eng.send("setoption name Clear Hash")
                        eng.send("isready")
                        eng.until("readyok")
                    best, info, lines = search(eng, prefix, LIMIT)
                    rec["searches"].append({"prefix": k, "best": best, "info": info})
                eng.quit()
            final = rec["searches"][-1]["best"]
            rec["final"] = final
            rec["played_k"] = (final == want)
        except Exception as exc:
            rec["error"] = str(exc)
            rec["played_k"] = None
        recs.append(rec)
        if (idx + 1) % 25 == 0:
            ok = sum(1 for r in recs if r.get("played_k"))
            err = sum(1 for r in recs if "error" in r)
            print(f"{idx+1}/{len(cases)} played_k={ok} errors={err} elapsed={time.time()-t0:.0f}s",
                  flush=True)
    json.dump({"engine": ENGINE, "mode": MODE, "limit": LIMIT, "hash": HASH,
               "cases_file": CASES, "records": recs}, open(OUT, "w"), indent=1)
    ok = sum(1 for r in recs if r.get("played_k"))
    bad = sum(1 for r in recs if r.get("played_k") is False)
    err = sum(1 for r in recs if "error" in r)
    print(f"DONE mode={MODE} limit={LIMIT} hash={HASH} cases={len(recs)} played_k={ok} "
          f"did_not={bad} errors={err} seconds={time.time()-t0:.0f}")


if __name__ == "__main__":
    main()
