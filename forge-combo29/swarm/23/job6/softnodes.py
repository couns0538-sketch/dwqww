#!/usr/bin/env python3
"""softnodes.py : measure `go softnodes N` on a build, fresh process per run, PC20, Threads 1, Hash 16.

For each requested N it records, from the engine's own output: every `info depth ... nodes ...` line,
the final `bestmove`, the node count of the last info line, and whether any depth number appears twice
(the signature of a partial-depth line).

Also does an IN-PROCESS repeat mode: same N several times in one process, either with `ucinewgame`
between or with nothing between, so the two orders can be compared.

usage: softnodes.py EXE OPTFILE OUTJSON MODE N [N ...]
       MODE = fresh | inproc_ucinewgame | inproc_plain
"""
import hashlib
import json
import re
import subprocess
import sys
import time

EXE, OPTFILE, OUTJSON, MODE = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
NS = []

INFO = re.compile(r"^info depth (\d+).*?nodes (\d+)")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def start():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    opts = [l.strip() for l in open(OPTFILE) if l.strip() and not l.startswith("#")]
    p.stdin.write("uci\n")
    p.stdin.flush()
    names = set()
    while True:
        line = p.stdout.readline()
        if not line:
            raise RuntimeError("engine died during uci")
        line = line.strip()
        if line.startswith("option name "):
            names.add(line.split("option name ")[1].split(" type ")[0])
        if line == "uciok":
            break
    for line in opts:
        name = line.split("name ")[1].split(" value ")[0]
        if name not in names:
            raise RuntimeError("STOP: option %r not in the engine's uci list" % name)
        p.stdin.write(line + "\n")
        p.stdin.flush()
        p.stdin.write("isready\n")
        p.stdin.flush()
        while True:
            l2 = p.stdout.readline()
            if not l2:
                raise RuntimeError("engine died during option %s" % line)
            if "unknown option" in l2 or "invalid value" in l2 or "ERROR" in l2:
                raise RuntimeError("STOP on %r" % l2.strip())
            if l2.strip() == "readyok":
                break
    return p, opts


def search(p, fen, n):
    """send position + go softnodes n, read to bestmove, return the record."""
    p.stdin.write("position fen %s\n" % fen)
    p.stdin.flush()
    p.stdin.write("isready\n")
    p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    t0 = time.monotonic()
    p.stdin.write("go softnodes %d\n" % n)
    p.stdin.flush()
    depths = []
    pv = None
    while True:
        line = p.stdout.readline()
        if not line:
            raise RuntimeError("engine died during go softnodes")
        line = line.strip()
        m = INFO.match(line)
        if m:
            depths.append((int(m.group(1)), int(m.group(2))))
            pv = line
        if line.startswith("bestmove"):
            wall = time.monotonic() - t0
            last_nodes = depths[-1][1] if depths else 0
            seen = {}
            partial = False
            for d, _ in depths:
                seen[d] = seen.get(d, 0) + 1
                if seen[d] > 1:
                    partial = True
            return {"n": n, "fen": fen, "bestmove": line.split()[1],
                    "last_nodes": last_nodes, "depths": depths,
                    "n_info_lines": len(depths), "partial_depth_line": partial,
                    "final_info": pv, "wall_s": round(wall, 4)}


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()]
    records = []
    if MODE == "fresh":
        for n in NS:
            for fen in fens:
                p, opts = start()
                rec = search(p, fen, n)
                p.stdin.write("quit\n"); p.stdin.flush()
                try:
                    p.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    p.kill()
                rec["mode"] = "fresh"
                records.append(rec)
    else:
        p, opts = start()
        for n in NS:
            for fen in fens:
                for rep in range(3):
                    if MODE == "inproc_ucinewgame":
                        p.stdin.write("ucinewgame\n"); p.stdin.flush()
                        p.stdin.write("isready\n"); p.stdin.flush()
                        while p.stdout.readline().strip() != "readyok":
                            pass
                    rec = search(p, fen, n)
                    rec["mode"] = MODE
                    rec["rep"] = rep
                    records.append(rec)
        p.stdin.write("quit\n"); p.stdin.flush()
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
    meta = {"exe_path_started": EXE, "sha256": sha256(EXE), "options_sent": opts,
            "mode": MODE, "ns": NS, "n_fens": len(fens),
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(OUTJSON, "w") as f:
        json.dump({"meta": meta, "records": records}, f, indent=1)
    print("wrote %d records to %s" % (len(records), OUTJSON))


FENS = "fens10.txt"
if __name__ == "__main__":
    # FENS is the 6th positional after MODE; the N list is argv[5:-1]
    FENS = sys.argv[-1]
    NS = [int(x) for x in sys.argv[5:-1]]
    main()
