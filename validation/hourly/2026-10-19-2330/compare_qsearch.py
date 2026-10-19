#!/usr/bin/env python3
"""Forge 6.4 qsearch candidate deterministic equivalence probe (Python 3.10+).

Usage: python compare_qsearch.py --baseline PATH --candidate PATH --out RESULTS
Runs 24 fixed-depth positions with fresh engine processes, Threads=1, Hash=16.
An exact result is necessary for this speed-only change, not evidence of Elo.
"""
import argparse
import hashlib
import json
import pathlib
import queue
import re
import subprocess
import sys
import threading
import time

FENS = (
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
    "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
    "4k3/4r3/8/8/8/8/8/4K3 w - - 0 1",
    "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
    "r4q1k/p2bR1rp/2p2Q1N/5p2/5p2/2P5/PP3PPP/R5K1 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "6k1/5ppp/8/8/8/8/8/4R1K1 w - - 0 1",
    "4k3/8/8/8/8/8/4p3/3RK3 b - - 0 1",
    "7k/8/8/8/8/8/8/KR6 w - - 99 1",
)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_engine(executable, fen, depth, deadline_secs=60):
    process = subprocess.Popen(
        [str(executable)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    messages = queue.Queue()

    def collect_stdout():
        for line in process.stdout:
            messages.put(line.rstrip("\n"))
        messages.put(None)

    thread = threading.Thread(target=collect_stdout, daemon=True)
    thread.start()
    lines = []

    def send(*commands):
        process.stdin.write("\n".join(commands) + "\n")
        process.stdin.flush()

    def read_until(prefix, timeout):
        limit = time.monotonic() + timeout
        while True:
            remaining = limit - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("timed out waiting for " + prefix)
            try:
                line = messages.get(timeout=remaining)
            except queue.Empty as exc:
                raise TimeoutError("timed out waiting for " + prefix) from exc
            if line is None:
                raise RuntimeError("engine EOF before " + prefix)
            lines.append(line)
            if line.startswith(prefix):
                return line

    try:
        send("uci")
        read_until("uciok", 10)
        send("setoption name Threads value 1", "setoption name Hash value 16",
             "setoption name OwnBook value false", "isready")
        read_until("readyok", 10)
        send("position fen " + fen, "go depth " + str(depth))
        bestmove_line = read_until("bestmove ", deadline_secs)
        info = [line for line in lines if re.search(r"^info depth " + str(depth) + r"(?:\s|$)", line)]
        info = [line for line in info if " score " in line and " nodes " in line]
        if not info:
            raise RuntimeError("no principal-variation info at target depth")
        last = info[-1]
        match_score = re.search(r"\bscore (cp|mate) (-?\d+)", last)
        match_nodes = re.search(r"\bnodes (\d+)", last)
        match_pv = re.search(r"\bpv (\S.+|\S)$", last)
        if not match_score or not match_nodes:
            raise RuntimeError("missing score or nodes at target depth")
        result = {
            "bestmove": bestmove_line.split()[1],
            "score": [match_score.group(1), int(match_score.group(2))],
            "nodes": int(match_nodes.group(1)),
            "pv": match_pv.group(1) if match_pv else "",
        }
        return result, lines
    finally:
        if process.poll() is None:
            try:
                send("quit")
            except (BrokenPipeError, OSError):
                pass
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=pathlib.Path, required=True)
    parser.add_argument("--candidate", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    report = {
        "protocol": "fresh-engine single-threaded paired fixed-depth search; exact behavior",
        "source_baseline_sha": "9108d012526be80c6d163f7cab684e6acd9abf8d",
        "source_candidate_sha": "3dddd864d45288787b6e949dca5528e88be9f535",
        "build_hashes": {
            "baseline": sha256_file(args.baseline),
            "candidate": sha256_file(args.candidate),
        },
        "probe_results": [],
        "errors": [],
    }
    for ix, fen in enumerate(FENS):
        for depth in (7, 9):
            entry = {"fen": fen, "depth": depth, "index": ix}
            try:
                baseline, base_log = run_engine(args.baseline, fen, depth)
                candidate, cand_log = run_engine(args.candidate, fen, depth)
                stem = f"fen{ix:02d}_d{depth}"
                (args.out / f"{stem}_baseline.log").write_text("\n".join(base_log) + "\n")
                (args.out / f"{stem}_candidate.log").write_text("\n".join(cand_log) + "\n")
                entry.update(baseline=baseline, candidate=candidate,
                             same=baseline == candidate)
            except Exception as exc:
                entry.update(same=False, error=repr(exc))
                report["errors"].append(repr(exc))
            report["probe_results"].append(entry)
            (args.out / "results.json").write_text(json.dumps(report, indent=2))
    count = len(report["probe_results"])
    failures = sum(not entry["same"] for entry in report["probe_results"])
    report.update(count=count, failures=failures,
                  status="PASS" if failures == 0 else "FAIL")
    (args.out / "results.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"count": count, "failures": failures, "status": report["status"]}))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
