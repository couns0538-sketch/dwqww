#!/usr/bin/env python3
"""seat 17 harness validation against swarm broadcast 19-F12.

19-F12: piping `quit` (or closing stdin) while a search runs makes this build answer a
fabricated `bestmove` with 0 nodes. This script measures BOTH harness styles on the same
engine and position and prints what each one gets, so my own results are either validated
or invalidated on the record.

  style A "pipelined"  : all commands written at once, stdin closed immediately (the bad one)
  style B "read-to-bestmove": each command written, stdout read until bestmove, then quit
                            (what my uci_driver.py does)

usage: harness_check.py <exe> <outdir>
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci_driver import run_one

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def pipelined(exe, go_line, log_path, delay_s=0.0):
    """Write everything at once; optionally hold stdin open delay_s before quit."""
    payload = "uci\nisready\nposition startpos\nisready\n%s\n" % go_line
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    proc.stdin.write(payload)
    proc.stdin.flush()
    if delay_s:
        time.sleep(delay_s)
        proc.stdin.write("quit\n")
        proc.stdin.flush()
    out, _ = proc.communicate(timeout=180)
    with open(log_path, "w") as handle:
        handle.write(out)
    return parse(out)


def parse(text):
    """Parse an engine log. A field that is NOT in the output is None ("not measured"),
    never 0: seat 19's warning is that a missing line must not read as a measured zero."""
    lines = text.splitlines()
    infos = [ln for ln in lines if ln.startswith("info depth")]
    moves = [ln for ln in lines if ln.startswith("bestmove")]
    nodes = None
    if infos:
        last = infos[-1]
        if " nodes " in last:
            nodes = int(last.split(" nodes ")[1].split()[0])
    return {"bestmove": moves[-1] if moves else None, "info_depth_lines": len(infos), "last_nodes": nodes}


def require_measured(tag, record, expect_search):
    """Fail loudly when a claim rests on a line the engine never printed."""
    problems = []
    if record["bestmove"] is None:
        problems.append("no bestmove line")
    if expect_search:
        if record["info_depth_lines"] == 0:
            problems.append("no info depth line (the search did not run)")
        if record["last_nodes"] is None:
            problems.append("no 'nodes' field in the last info depth line")
    if problems:
        raise SystemExit("FATAL: %s is not a measurement: %s" % (tag, "; ".join(problems)))
    return record


def main():
    exe, outdir = sys.argv[1:3]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for go_line in ("go depth 12", "go nodes 50000"):
        tag = go_line.replace(" ", "_")
        a = pipelined(exe, go_line, os.path.join(outdir, "A_pipelined_%s.log" % tag))
        b = pipelined(exe, go_line, os.path.join(outdir, "A2_pipelined_2s_%s.log" % tag), delay_s=2.0)
        c_info = run_one(exe, ["uci", "isready", "position startpos", "isready", go_line],
                         180, os.path.join(outdir, "B_readbestmove_%s.log" % tag))
        c = parse(open(os.path.join(outdir, "B_readbestmove_%s.log" % tag)).read())
        # The pipelined cases are EXPECTED to be empty (that is 19-F12); the read-to-bestmove
        # case is the one that must be a real measurement, so only it is asserted.
        require_measured("B read-to-bestmove %s" % go_line, c, expect_search=True)
        rows.append((go_line, "A pipelined+closed", a, "A2 pipelined+2s", b,
                     "B read-to-bestmove (mine)", {**c, "bestmove": c_info["bestmove"]}))
    print("%-14s | %-28s | %-28s | %s" % ("go", "A pipelined, stdin closed", "A2 pipelined, quit at 2s", "B read-to-bestmove (my harness)"))
    for go_line, _, a, _, b, _, c in rows:
        print("%-14s | %-28s | %-28s | %s" % (go_line, "%s nodes=%s lines=%d" % (a["bestmove"], a["last_nodes"], a["info_depth_lines"]),
                                              "%s nodes=%s lines=%d" % (b["bestmove"], b["last_nodes"], b["info_depth_lines"]),
                                              "%s nodes=%s lines=%d" % (c["bestmove"], c["last_nodes"], c["info_depth_lines"])))
    with open(os.path.join(outdir, "harness_check.txt"), "w") as handle:
        for go_line, la, a, lb, b, lc, c in rows:
            handle.write("%s\n  %s: %s\n  %s: %s\n  %s: %s\n\n" % (go_line, la, a, lb, b, lc, c))


if __name__ == "__main__":
    main()
