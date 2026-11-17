#!/usr/bin/env python3
"""Run real searches on the verification build and report any incremental-vs-reference abort.

Built with -DFORGE_NNUE_V3_VERIFY=1, the engine compares every incrementally produced
evaluation against a fresh reference evaluation inside static_evaluate_v3 and calls
std::_Exit(3) on a mismatch, printing the FEN. That makes this check independent of my own
harness: the search's own control flow, dirty-piece plumbing and ply stack are exercised.

A search that ends in `bestmove` with a normal exit status found no mismatch among every
evaluation that search performed. The evaluation count is not observable from outside, so the
reported denominators are positions searched and the node counts the engine printed.

Usage: verify_search.py <verify engine> <net> <fens> <budget> <out json>
"""
import json
import queue
import subprocess
import sys
import threading
import time

EXE, NET, FENS, BUDGET, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
TIMEOUT = 300.0


def run_one(fen):
    proc = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    q = queue.Queue()

    def reader():
        for line in proc.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def until(prefix):
        out = []
        deadline = time.monotonic() + TIMEOUT
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("timeout waiting for %r" % prefix)
            line = q.get(timeout=remaining)
            if line is None:
                raise EOFError("engine exited while waiting for %r" % prefix)
            out.append(line)
            if line.startswith(prefix):
                return out

    send("uci")
    until("uciok")
    send("setoption name NNUEArchFile value " + NET)
    send("isready")
    until("readyok")
    send("setoption name NNUEArch value true")
    send("isready")
    until("readyok")
    send("setoption name Threads value 1")
    send("isready")
    until("readyok")
    send("setoption name Hash value 16")
    send("isready")
    until("readyok")
    send("ucinewgame")
    send("isready")
    until("readyok")
    send("position fen " + fen)
    send("isready")
    pos = until("readyok")
    if any("invalid FEN" in line for line in pos):
        proc.kill()
        return {"fen": fen, "status": "refused"}
    send("go " + BUDGET)
    out = until("bestmove")
    nodes = None
    for line in out:
        if line.startswith("info depth") and " nodes " in line:
            parts = line.split()
            nodes = int(parts[parts.index("nodes") + 1])
    send("quit")
    try:
        proc.wait(timeout=30)
    except Exception:
        proc.kill()
    stderr = proc.stderr.read() if proc.stderr else ""
    return {"fen": fen, "bestmove": out[-1], "nodes": nodes, "exit": proc.returncode,
            "mismatch": "verification mismatch" in stderr, "stderr": stderr[-400:]}


def main():
    raw = [l.strip() for l in open(FENS) if l.strip()]
    # Accept "<fen>" or "<fen> | <moves>"; only the FEN is searched here. Sequence lines are
    # for the incremental harness, and feeding one to the engine would reach a 300 s timeout
    # per line, which is how an earlier run of this script silently stalled.
    fens = []
    for line in raw:
        fen = line.split("|")[0].strip()
        if fen:
            fens.append(fen)
    rows = []
    mismatches = 0
    refused = 0
    abnormal = 0
    total_nodes = 0
    for index, fen in enumerate(fens, 1):
        try:
            result = run_one(fen)
        except (TimeoutError, EOFError) as exc:
            print("VERIFY ERROR position %d: %s" % (index, exc))
            abnormal += 1
            continue
        rows.append(result)
        if result.get("status") == "refused":
            refused += 1
        elif result.get("mismatch"):
            mismatches += 1
            print("VERIFY MISMATCH position %d %s" % (index, result.get("stderr", "").strip()))
        elif result.get("exit") != 0:
            abnormal += 1
            print("VERIFY ABNORMAL position %d exit %s" % (index, result.get("exit")))
        if result.get("nodes"):
            total_nodes += result["nodes"]
        if index % 25 == 0:
            print("VERIFY progress %d/%d" % (index, len(fens)))
    print("VERIFY searched %d refused %d mismatches %d abnormal %d total_nodes %d budget %s"
          % (len(rows) - refused, refused, mismatches, abnormal, total_nodes, BUDGET))
    with open(OUT, "w") as handle:
        json.dump({"budget": BUDGET, "searched": len(rows) - refused, "refused": refused,
                   "mismatches": mismatches, "abnormal": abnormal,
                   "total_nodes": total_nodes, "rows": rows}, handle, indent=1)
    return 0 if mismatches == 0 and abnormal == 0 and refused == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
