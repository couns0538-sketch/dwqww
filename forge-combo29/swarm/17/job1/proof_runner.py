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
    """Write commands, read to the end of output, then quit. Returns (rc, timed_out, text)."""
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    chunks = []
    timed_out = False
    try:
        payload = "\n".join(lines) + "\n"
        proc.stdin.write(payload)
        proc.stdin.flush()
        # Read everything until the process closes or the timeout hits.
        out, _ = proc.communicate(timeout=timeout_s)
        chunks.append(out or "")
    except subprocess.TimeoutExpired:
        timed_out = True
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
        ("real_normal_search", real, ["uci", "isready", "position startpos", "go depth 6", "quit"]),
        ("planted_heap_overread", planted_asan, ["uci", "isready", "bench 5", "quit"]),
        ("planted_signed_overflow", planted_ubsan, ["uci", "isready", "position startpos", "go depth 1", "quit"]),
    ]
    for name, exe, lines in cases:
        log_path = os.path.join(outdir, name + ".log")
        rc, timed_out, text = drive(exe, lines, 240, log_path)
        hits = collect(text)
        meta = {
            "name": name,
            "exe": exe,
            "sha256": sha256(exe),
            "asan_symbols": symbol_count(exe, "__asan_"),
            "ubsan_symbols": symbol_count(exe, "__ubsan_"),
            "commands": lines,
            "rc": rc,
            "timed_out": timed_out,
            "sanitizer_lines": len(hits),
            "sanitizer_examples": hits[:3],
        }
        with open(os.path.join(outdir, name + ".meta"), "w") as handle:
            json.dump(meta, handle, indent=1)
        report["runs"].append(meta)
        print(json.dumps(meta, indent=1))

    with open(os.path.join(outdir, "proof.json"), "w") as handle:
        json.dump(report, handle, indent=1)


if __name__ == "__main__":
    main()
