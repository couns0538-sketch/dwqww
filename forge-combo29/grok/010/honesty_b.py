#!/usr/bin/env python3
"""Honesty check for one engine. Fresh process per line. No setoption.

Writes raw stdout beside this script and HONESTY_B.txt with the parsed nodes.
"""
import hashlib
import os
import queue
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else ""
PREFIX = sys.argv[2] if len(sys.argv) > 2 else "b"
EXPECTED = [
    ("bench11", ["bench 11"], "info string bench ", 312866),
    ("bench13", ["bench 13"], "info string bench ", 862329),
    ("bench16", ["bench 16"], "info string bench ", 3024920),
    ("perft5", ["go perft 5"], "nodes ", 4865609),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def start_reader(proc):
    lines = queue.Queue()

    def pump():
        for line in proc.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=pump, daemon=True).start()
    return lines


def read_until(lines, prefix, timeout_s):
    collected = []
    deadline = time.time() + timeout_s
    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            raise TimeoutError("no output for %s seconds; collected %d lines" % (timeout_s, len(collected)))
        try:
            line = lines.get(timeout=remaining)
        except queue.Empty as exc:
            raise TimeoutError("no output for %s seconds; collected %d lines" % (timeout_s, len(collected))) from exc
        if line is None:
            break
        collected.append(line)
        if line.startswith(prefix):
            break
    return collected


def nodes_from(line, prefix):
    if prefix == "nodes ":
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "nodes":
            return int(parts[1])
        raise ValueError("bad perft line: " + line.rstrip())
    # info string bench depth N nodes N time N nps N
    parts = line.split()
    if "nodes" not in parts:
        raise ValueError("bad bench line: " + line.rstrip())
    return int(parts[parts.index("nodes") + 1])


def one(tag, commands, stop_prefix, digest):
    raw_path = os.path.join(HERE, "%s_%s.txt" % (PREFIX, tag))
    err_path = os.path.join(HERE, "%s_%s.err" % (PREFIX, tag))
    meta_path = os.path.join(HERE, "%s_%s.meta" % (PREFIX, tag))
    with open(err_path, "w", encoding="utf-8") as err_handle:
        proc = subprocess.Popen(
            [EXE],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=err_handle,
            text=True,
            bufsize=1,
        )
        collected = []
        id_name = ""
        incoming = start_reader(proc)
        try:
            proc.stdin.write("uci\n")
            proc.stdin.flush()
            uci_lines = read_until(incoming, "uciok", 30)
            collected.extend(uci_lines)
            for line in uci_lines:
                if line.startswith("id name "):
                    id_name = line[len("id name "):].rstrip("\n")
            for command in commands:
                proc.stdin.write(command + "\n")
                proc.stdin.flush()
                collected.extend(read_until(incoming, stop_prefix, 180))
            proc.stdin.write("quit\n")
            proc.stdin.flush()
            proc.wait(timeout=20)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=10)
    with open(raw_path, "w", encoding="utf-8") as raw:
        raw.writelines(collected)
    hit = ""
    for line in collected:
        if line.startswith(stop_prefix):
            hit = line
    got = nodes_from(hit, stop_prefix) if hit else None
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write("exe %s\n" % EXE)
        meta.write("sha256 %s\n" % digest)
        meta.write("id name %s\n" % id_name)
        meta.write("options\n")
        meta.write("(none)\n")
        meta.write("commands uci; %s; quit\n" % "; ".join(commands))
    return got, hit.rstrip("\n") if hit else ""


def main():
    if not EXE or not os.path.isfile(EXE):
        print("missing exe", file=sys.stderr)
        return 2
    digest = sha256_file(EXE)
    report = []
    failed = False
    for tag, commands, prefix, expected in EXPECTED:
        got, line = one(tag, commands, prefix, digest)
        ok = got == expected
        failed = failed or not ok
        report.append("%s nodes %s expected %s %s" % (tag, got, expected, "PASS" if ok else "FAIL"))
        report.append(line)
    text = "\n".join(report) + "\n"
    out = os.path.join(HERE, "HONESTY_%s.txt" % PREFIX.upper())
    with open(out, "w", encoding="utf-8") as handle:
        handle.write(text)
    sys.stdout.write(text)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
