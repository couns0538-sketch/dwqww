#!/usr/bin/env python3
"""train_driver.py - feed a frozen LTO+PGO training workload (v2) to an instrumented Forge exe, waiting for real output.

  train_driver.py EXE WORKLOAD NETS_MANIFEST OUT_TXT --net NAME=PATH [--net NAME=PATH]... [--timeout SEC]

Workload v1 is plain stdin (bench only). v2 also has `go` searches at Threads=2, and a `go` is stopped by the next UCI
command, so v2 needs a driver that waits for `bestmove` before it sends the next line. Rules:
  - {NET:name} placeholders are replaced by the --net path; that file's full sha256 must equal the manifest's.
  - Only `setoption name Threads` and `setoption name EvalFileHalfKA` are allowed (all other options stay at default).
  - Waits: uci -> uciok, isready -> readyok, bench N -> 'bench depth N nodes', go -> bestmove, quit -> process exit 0.
  - Every EvalFileHalfKA setoption must print 'info string EvalFileHalfKA loaded' (no ERROR) before the next readyok.
Writes the engine output to OUT_TXT and the resolved input to OUT_TXT.input.txt (LF). Exit 0 only if all checks pass.
Pipes are binary and lines end in LF, so the engine reads exactly the bytes of the resolved input.
"""
import hashlib
import queue
import re
import subprocess
import sys
import threading
import time

ALLOWED_SETOPTION = re.compile(r"^setoption name (Threads|EvalFileHalfKA) value \S")


def die(msg):
    print("train_driver: FAIL: " + msg, flush=True)
    sys.exit(1)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def parse_args(argv):
    if len(argv) < 4:
        sys.exit(__doc__)
    exe, workload, manifest, out = argv[:4]
    nets, timeout, i = {}, 3600.0, 4
    while i < len(argv):
        if argv[i] == "--net" and i + 1 < len(argv):
            name, _, path = argv[i + 1].partition("=")
            if not name or not path:
                die("bad --net " + argv[i + 1])
            nets[name] = path
            i += 2
        elif argv[i] == "--timeout" and i + 1 < len(argv):
            timeout = float(argv[i + 1])
            i += 2
        else:
            die("unknown argument " + argv[i])
    return exe, workload, manifest, out, nets, timeout


def main(argv):
    exe, workload, manifest, out, nets, timeout = parse_args(argv)
    want = {}
    for raw in open(manifest, "rb").read().decode("utf-8").split("\n"):
        line = raw.strip()
        if line and not line.startswith("#"):
            name, digest = line.split()[:2]
            want[name] = digest.lower()
    for name, path in nets.items():
        if name not in want:
            die("net %s is not in %s" % (name, manifest))
        got = sha256_file(path)
        if got != want[name]:
            die("net %s sha256 %s != manifest %s (%s)" % (name, got, want[name], path))
        print("net %s sha256 %s OK %s" % (name, got, path), flush=True)
    text = open(workload, "rb").read().decode("ascii")
    if "\r" in text:
        die("workload has CR bytes (must be LF)")
    lines = [l for l in text.split("\n") if l]

    def resolve(line):
        def sub(m):
            if m.group(1) not in nets:
                die("no --net for {NET:%s}" % m.group(1))
            return nets[m.group(1)]
        return re.sub(r"\{NET:(\w+)\}", sub, line)

    lines = [resolve(l) for l in lines]
    for l in lines:
        if l.startswith("setoption") and not ALLOWED_SETOPTION.match(l):
            die("setoption not allowed in the frozen workload: " + l)
    if lines[-1] != "quit":
        die("workload must end with quit")
    with open(out + ".input.txt", "wb") as f:
        f.write(("\n".join(lines) + "\n").encode("ascii"))

    log = open(out, "wb")
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines_q = queue.Queue()

    def reader():
        for b in iter(proc.stdout.readline, b""):
            log.write(b)
            lines_q.put(b.decode("utf-8", "replace").rstrip("\r\n"))
        lines_q.put(None)

    threading.Thread(target=reader, daemon=True).start()
    deadline = time.monotonic() + timeout
    counts = {"bench": 0, "go": 0, "load": 0}
    pending_load = 0

    def wait_for(rx):
        nonlocal pending_load
        r = re.compile(rx)
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                proc.kill()
                die("timeout after %.0fs waiting for %s" % (timeout, rx))
            try:
                got = lines_q.get(timeout=min(left, 5.0))
            except queue.Empty:
                continue
            if got is None:
                die("engine exited while waiting for " + rx)
            if got.startswith("info string ERROR"):
                die("engine error: " + got)
            if got.startswith("info string EvalFileHalfKA loaded"):
                pending_load -= 1
                counts["load"] += 1
            if r.search(got):
                return got

    for l in lines:
        proc.stdin.write((l + "\n").encode("ascii"))
        proc.stdin.flush()
        cmd = l.split()[0]
        if cmd == "uci":
            wait_for(r"^uciok")
        elif cmd == "isready":
            wait_for(r"^readyok")
            if pending_load != 0:
                die("EvalFileHalfKA setoption without a 'loaded' line before readyok")
        elif cmd == "bench":
            got = wait_for(r"bench depth %s nodes \d+" % l.split()[1])
            counts["bench"] += 1
            print(got, flush=True)
        elif cmd == "go":
            wait_for(r"^bestmove ")
            counts["go"] += 1
        elif l.startswith("setoption name EvalFileHalfKA"):
            pending_load += 1
    proc.stdin.close()
    try:
        rc = proc.wait(timeout=max(1.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        proc.kill()
        die("engine did not exit after quit")
    while lines_q.get() is not None:
        pass
    log.close()
    want_counts = {"bench": sum(l.startswith("bench ") for l in lines), "go": sum(l.startswith("go ") for l in lines),
                   "load": sum(l.startswith("setoption name EvalFileHalfKA") for l in lines)}
    print("counts bench %(bench)d go %(go)d load %(load)d" % counts, flush=True)
    if counts != want_counts:
        die("counts %s != workload %s" % (counts, want_counts))
    if rc != 0:
        die("engine exit code %d" % rc)
    print("train_driver: OK", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
