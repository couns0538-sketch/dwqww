#!/usr/bin/env python3
"""honesty.py EXE OUTDIR TAG
Fresh process per line. No setoption. TAG is B or P.
Writes honesty_<TAG>_<name>.raw and .meta under OUTDIR.
"""
import hashlib
import os
import select
import subprocess
import sys

STOPS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
EXPECTED = {
    "bench11": ("bench 11", "bench", 312866),
    "bench13": ("bench 13", "bench", 862329),
    "bench16": ("bench 16", "bench", 3024920),
    "perft5": ("go perft 5", "perft", 4865609),
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Lines:
    def __init__(self, proc):
        self.proc = proc
        self.fd = proc.stdout.fileno()
        os.set_blocking(self.fd, False)
        self.buf = b""

    def readline(self, timeout):
        while b"\n" not in self.buf:
            ready, _, _ = select.select([self.fd], [], [], timeout)
            if not ready:
                raise SystemExit("STOP: timeout waiting for engine")
            chunk = os.read(self.fd, 1 << 16)
            if chunk == b"":
                raise SystemExit("STOP: unexpected EOF")
            self.buf += chunk
        raw, self.buf = self.buf.split(b"\n", 1)
        return raw.decode("utf-8", "replace").rstrip("\r")


def read_until(lines, log, done, timeout):
    while True:
        text = lines.readline(timeout)
        log.append(text)
        for stop in STOPS:
            if stop in text:
                raise SystemExit(f"STOP: {text}")
        if done(text):
            return text


def nodes_of(kind, line):
    if kind == "bench":
        parts = line.split()
        if "nodes" not in parts:
            raise SystemExit(f"STOP: no nodes in {line}")
        return int(parts[parts.index("nodes") + 1])
    if not line.startswith("nodes "):
        raise SystemExit(f"STOP: perft line {line}")
    return int(line.split()[1])


def one(exe, exe_sha, outdir, tag, name, command, kind, expected):
    proc = subprocess.Popen(
        [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    log = []
    id_name = ""
    lines = Lines(proc)
    try:
        proc.stdin.write((command + "\n").encode())
        proc.stdin.flush()
        if kind == "bench":
            line = read_until(lines, log, lambda t: t.startswith("info string bench "), 180)
        else:
            line = read_until(lines, log, lambda t: t.startswith("nodes "), 180)
        got = nodes_of(kind, line)
        proc.stdin.write(b"uci\n")
        proc.stdin.flush()
        read_until(lines, log, lambda t: t == "uciok", 30)
        for text in log:
            if text.startswith("id name "):
                id_name = text[len("id name "):]
        proc.stdin.write(b"quit\n")
        proc.stdin.flush()
        proc.wait(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()
    raw_path = f"{outdir}/honesty_{tag}_{name}.raw"
    meta_path = f"{outdir}/honesty_{tag}_{name}.meta"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(f">> {command}\n")
        wrote_uci = False
        for text in log:
            if not wrote_uci and text.startswith("id name "):
                f.write(">> uci\n")
                wrote_uci = True
            f.write(f"<< {text}\n")
        f.write(">> quit\n")
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"exe={exe}\n")
        f.write(f"sha256={exe_sha}\n")
        f.write(f"id_name={id_name}\n")
        f.write(f"command={command}\n")
        f.write("options=\n")
    status = "ok" if got == expected else "MISS"
    print(f"{tag} {name} nodes {got} expected {expected} {status}")
    return got == expected


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: honesty.py EXE OUTDIR TAG")
    exe, outdir, tag = sys.argv[1:]
    exe_sha = sha256_file(exe)
    ok = True
    for name, (command, kind, expected) in EXPECTED.items():
        if not one(exe, exe_sha, outdir, tag, name, command, kind, expected):
            ok = False
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
