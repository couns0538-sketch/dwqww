#!/usr/bin/env python3
"""seat 17 sanitizer proof runner.

Runs the SAME runner over three engines and reports the sanitizer lines each produced:
  1. the real ASan+UBSan build of the engine, on a normal search
  2. a scratch copy of the engine with ONE planted heap over-read (ASan) behind `bench`
  3. a scratch copy with ONE planted signed overflow (UBSan) behind `go`

The brief: a run "under a sanitizer" counts only with (1) nm -C <exe> | grep -c __asan_
above 0 in the .meta and (2) a planted fault counted by the same runner. This script
produces exactly those two proofs plus the control.

usage: proof_runner.py <real_exe> <planted_asan_exe> <planted_ubsan_exe> <outdir>
"""
import datetime
import hashlib
import json
import os
import subprocess
import time
import sys


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def symbol_count(exe, marker):
    proc = subprocess.run(["nm", "-C", exe], capture_output=True, text=True)
    return sum(1 for line in proc.stdout.splitlines() if marker in line)


def drive(exe, lines, timeout_s, log_path):
    """Drive the engine one command at a time, reading each answer before the next.

    NEVER pipelines `quit` into a running search: swarm broadcast 19-F12 shows that a pipelined
    `quit` makes this build answer a fabricated `bestmove` with 0 nodes, so the search under test
    would not have run at all and "0 sanitizer lines" would mean nothing. `go` is read until
    `bestmove`; `isready`/`setoption` are read until `readyok`.
    The planted-fault engines still fire their fault: their hook runs before the search starts.
    """
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    chunks = []
    timed_out = False
    start = time.monotonic()
    try:
        for line in lines:
            if line == "quit":
                break
            proc.stdin.write(line + "\n")
            proc.stdin.flush()
            if line.startswith("go"):
                deadline = time.monotonic() + timeout_s
                while time.monotonic() < deadline:
                    reply = proc.stdout.readline()
                    if reply == "":
                        break
                    chunks.append(reply)
                    if reply.startswith("bestmove"):
                        break
                else:
                    timed_out = True
                    proc.kill()
                    break
            elif line == "isready" or line.startswith("setoption") or line == "uci":
                deadline = time.monotonic() + 120
                while time.monotonic() < deadline:
                    reply = proc.stdout.readline()
                    if reply == "":
                        break
                    chunks.append(reply)
                    if reply.strip() in ("readyok", "uciok"):
                        break
        if proc.poll() is None:
            proc.stdin.write("quit\n")
            proc.stdin.flush()
        out, _ = proc.communicate(timeout=60)
        chunks.append(out or "")
    except (BrokenPipeError, subprocess.TimeoutExpired):
        proc.kill()
        out, _ = proc.communicate()
        chunks.append(out or "")
    text = "".join(chunks)
    with open(log_path, "w") as handle:
        handle.write(text)
    return proc.returncode, timed_out, text


def collect(text):
    words = ["AddressSanitizer", "runtime error:", "UndefinedBehaviorSanitizer",
             "heap-buffer-overflow", "stack-buffer-overflow", "SEGV", "SUMMARY: "]
    hits = []
    for line in text.splitlines():
        if any(word in line for word in words):
            hits.append(line.strip())
    return hits


def main():
    real, planted_asan, planted_ubsan, outdir = sys.argv[1:5]
    os.makedirs(outdir, exist_ok=True)
    report = {"date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "runs": []}

    cases = [
        ("real_normal_search", real, ["uci", "isready", "position startpos", "go depth 6", "quit"], 1, 0),
        ("planted_heap_overread", planted_asan, ["uci", "isready", "bench 5", "quit"], 0, 2),
        ("planted_signed_overflow", planted_ubsan, ["uci", "isready", "position startpos", "go depth 1", "quit"], 0, 1),
    ]
    for name, exe, lines, min_depth_lines, min_sanitizer in cases:
        log_path = os.path.join(outdir, name + ".log")
        rc, timed_out, text = drive(exe, lines, 240, log_path)
        hits = collect(text)
        depth_lines = [ln for ln in text.splitlines() if ln.startswith("info depth")]
        nodes = None
        for ln in reversed(depth_lines):
            if " nodes " in ln:
                nodes = int(ln.split(" nodes ")[1].split()[0])
                break
        meta = {
            "name": name,
            "exe": exe,
            "sha256": sha256(exe),
            "asan_symbols": symbol_count(exe, "__asan_"),
            "ubsan_symbols": symbol_count(exe, "__ubsan_"),
            "commands": lines,
            "rc": rc,
            "timed_out": timed_out,
            "info_depth_lines": len(depth_lines),
            "last_nodes": nodes,
            "sanitizer_lines": len(hits),
            "sanitizer_examples": hits[:3],
        }
        # Fail loudly: a case must show the evidence it exists to show. The real-search case must
        # have actually searched (depth lines and a node count); the planted cases must have been
        # counted by the runner. A missing line can never pass as a clean zero.
        problems = []
        if len(depth_lines) < min_depth_lines:
            problems.append("expected >= %d info depth line(s), saw %d"
                            % (min_depth_lines, len(depth_lines)))
        if min_depth_lines > 0 and nodes is None:
            problems.append("no 'nodes' field in any info depth line")
        if len(hits) < min_sanitizer:
            problems.append("expected >= %d sanitizer line(s), saw %d" % (min_sanitizer, len(hits)))
        if problems:
            raise SystemExit("FATAL: case %s proves nothing: %s" % (name, "; ".join(problems)))
        with open(os.path.join(outdir, name + ".meta"), "w") as handle:
            json.dump(meta, handle, indent=1)
        report["runs"].append(meta)
        print(json.dumps(meta, indent=1))

    with open(os.path.join(outdir, "proof.json"), "w") as handle:
        json.dump(report, handle, indent=1)


if __name__ == "__main__":
    main()
