#!/usr/bin/env python3
"""engine_perft.py : run `go perft D` for D in 1..4 on every FEN of a file, one engine process.

Every `position` is followed by `isready` and every line up to `readyok` is read; any of
"unknown option" / "invalid value" / "invalid FEN" / "illegal move" stops the run.

usage: engine_perft.py EXE FENS OUT_JSONL [MAXDEPTH]
Writes OUT_JSONL (one json object per FEN, with divide at the deepest depth) and OUT_JSONL.meta
"""
import hashlib
import json
import subprocess
import sys
import time

EXE = sys.argv[1]
FENS = sys.argv[2]
OUT = sys.argv[3]
MAXDEPTH = int(sys.argv[4]) if len(sys.argv) > 4 else 4
OPTFILE = sys.argv[5] if len(sys.argv) > 5 else None

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    fens = [line.strip() for line in open(FENS) if line.strip()]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    meta = {"exe_path_started": EXE, "sha256": sha256(EXE), "options_sent": [],
            "fens_file": FENS, "maxdepth": MAXDEPTH,
            "python_chess": None, "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    def send(line):
        p.stdin.write(line + "\n")
        p.stdin.flush()

    def read_until_readyok():
        lines = []
        send("isready")
        while True:
            line = p.stdout.readline()
            if not line:
                raise RuntimeError("engine died; got so far: %r" % lines[-5:])
            line = line.rstrip("\n")
            lines.append(line)
            for bad in BAD:
                if bad in line:
                    raise RuntimeError("STOP on %r" % line)
            if line.strip() == "readyok":
                return lines

    send("uci")
    id_name = None
    uci_option_names = []
    while True:
        line = p.stdout.readline().rstrip("\n")
        if line.startswith("id name "):
            id_name = line[8:]
        if line.startswith("option name "):
            uci_option_names.append(line.split("option name ")[1].split(" type ")[0])
        if line.strip() == "uciok":
            break
    meta["uci_option_names"] = uci_option_names
    meta["id_name"] = id_name
    read_until_readyok()
    send("ucinewgame")
    read_until_readyok()

    # OPTIONS (e.g. PC20): sent one by one, each followed by isready; every line up to readyok is read
    # and any of BAD stops the run. The option name is checked against the uci list first, so a typo
    # cannot pass silently as "the engine ignored it".
    uci_options = set(meta.get("uci_option_names") or [])
    if OPTFILE:
        for line in open(OPTFILE):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name = line.split("name ")[1].split(" value ")[0]
            if uci_options and name not in uci_options:
                raise RuntimeError("STOP: option %r is not in the engine's uci list" % name)
            send(line)
            read_until_readyok()
            meta["options_sent"].append(line)

    out = open(OUT, "w")
    t0 = time.time()
    for idx, fen in enumerate(fens):
        row = {"i": idx, "fen": fen, "nodes": {}, "divide": None, "illegal_bestmove": None}
        send("position fen " + fen)
        read_until_readyok()
        for depth in range(1, MAXDEPTH + 1):
            send("go perft %d" % depth)
            div = {}
            nodes = None
            while True:
                line = p.stdout.readline()
                if not line:
                    raise RuntimeError("engine died during perft")
                line = line.rstrip("\n")
                if not line:
                    continue
                if line.startswith("nodes "):
                    nodes = int(line.split()[1])
                    break
                if ":" in line:
                    move, cnt = line.split(":")
                    div[move.strip()] = int(cnt.strip())
            row["nodes"][str(depth)] = nodes
            if depth == MAXDEPTH:
                row["divide"] = div
        out.write(json.dumps(row) + "\n")
        if idx % 200 == 0:
            print("done %d/%d %.1fs" % (idx, len(fens), time.time() - t0), flush=True)
    out.close()
    send("quit")
    p.wait(timeout=10)
    meta["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    meta["elapsed_s"] = round(time.time() - t0, 1)
    with open(OUT + ".meta", "w") as f:
        json.dump(meta, f, indent=1)
    print("finished", meta["elapsed_s"], "s")


if __name__ == "__main__":
    main()
