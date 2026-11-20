#!/usr/bin/env python3
"""Fresh-process honesty check. No setoption. One process per command.

python3 honesty.py <exe> <out-prefix>
Writes <prefix>_bench11.txt and .meta, and the same for bench13, bench16, perft5.
"""
import hashlib
import queue
import subprocess
import sys
import threading
import time

EXPECTED = {
    "bench 11": 312866,
    "bench 13": 862329,
    "bench 16": 3024920,
    "go perft 5": 4865609,
}
STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_command(exe, command, out_path, meta_path, exe_sha):
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    lines = []
    q = queue.Queue()

    def reader():
        for line in proc.stdout:
            q.put(line)
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(text):
        proc.stdin.write(text + "\n")
        proc.stdin.flush()

    def read_until(pred, timeout):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                line = q.get(timeout=0.2)
            except queue.Empty:
                if proc.poll() is not None:
                    break
                continue
            if line is None:
                break
            lines.append(line)
            if any(bit in line for bit in STOP_BITS):
                raise SystemExit(f"STOP: {line.rstrip()}")
            if pred(line):
                return True
        return False

    send("uci")
    if not read_until(lambda line: line.strip() == "uciok", 30):
        raise SystemExit(f"no uciok for {command}")
    id_name = ""
    for line in lines:
        if line.startswith("id name "):
            id_name = line[len("id name "):].rstrip("\r\n")
    send(command)
    if command.startswith("bench"):
        ok = read_until(lambda line: line.startswith("info string bench depth "), 600)
    else:
        ok = read_until(lambda line: line.startswith("nodes "), 180)
    if not ok:
        raise SystemExit(f"no result line for {command}")
    send("quit")
    read_until(lambda line: False, 3)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    err = proc.stderr.read()
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"started_exe: {exe}\n")
        f.write(f"sha256: {exe_sha}\n")
        f.write(f"id_name: {id_name}\n")
        f.write(f"command: {command}\n")
        f.write("options_sent:\n")
        f.write("(none)\n")
        if err:
            f.write("stderr:\n")
            f.write(err)
    nodes = None
    if command.startswith("bench"):
        for line in lines:
            if line.startswith("info string bench depth "):
                parts = line.split()
                nodes = int(parts[parts.index("nodes") + 1])
    else:
        for line in lines:
            if line.startswith("nodes "):
                nodes = int(line.split()[1])
    return nodes, id_name


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: honesty.py <exe> <out-prefix>")
    exe, prefix = sys.argv[1], sys.argv[2]
    exe_sha = sha256_file(exe)
    failed = False
    for command, expected in EXPECTED.items():
        tag = command.replace(" ", "")
        out_path = f"{prefix}_{tag}.txt"
        meta_path = f"{prefix}_{tag}.meta"
        nodes, id_name = run_command(exe, command, out_path, meta_path, exe_sha)
        status = "OK" if nodes == expected else "MISS"
        if nodes != expected:
            failed = True
        print(f"{status} {command} nodes {nodes} expected {expected} id {id_name}", flush=True)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
