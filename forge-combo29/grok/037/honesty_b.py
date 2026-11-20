#!/usr/bin/env python3
"""Honesty check on one engine. Fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path


def read_until(proc, pred, limit=200000):
    lines = []
    while len(lines) < limit:
        line = proc.stdout.readline()
        if line == "":
            break
        lines.append(line)
        if pred(line):
            break
    return lines


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_one(exe: Path, commands):
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    sent = []

    def send(cmd: str) -> None:
        sent.append(cmd)
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    send("uci")
    lines = read_until(proc, lambda s: s.startswith("uciok"))
    id_name = ""
    for line in lines:
        if line.startswith("id name "):
            id_name = line[len("id name ") :].rstrip("\n")
    send("isready")
    lines += read_until(proc, lambda s: s.startswith("readyok"))
    for cmd in commands:
        send(cmd)
        if cmd == "isready" or cmd.startswith("position "):
            # position has no reply; isready does. Always wait on isready.
            if cmd == "isready":
                lines += read_until(proc, lambda s: s.startswith("readyok"))
        elif cmd.startswith("bench "):
            lines += read_until(proc, lambda s: "info string bench depth" in s)
        elif cmd.startswith("go perft"):
            lines += read_until(proc, lambda s: s.startswith("nodes "))
    send("quit")
    try:
        rest = proc.communicate(timeout=30)[0]
    except subprocess.TimeoutExpired:
        proc.kill()
        rest = proc.communicate()[0]
    if rest:
        lines.append(rest if rest.endswith("\n") else rest + "\n")
    return "".join(lines), sent, id_name


def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    tag = sys.argv[3] if len(sys.argv) > 3 else "B"
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256(exe)
    cases = [
        ("bench11", ["bench 11"]),
        ("bench13", ["bench 13"]),
        ("bench16", ["bench 16"]),
        ("perft5", ["position startpos", "isready", "go perft 5"]),
    ]
    expected = {
        "bench11": 312866,
        "bench13": 862329,
        "bench16": 3024920,
        "perft5": 4865609,
    }
    summary = []
    ok = True
    for name, commands in cases:
        text, sent, id_name = run_one(exe, commands)
        raw = out_dir / f"HONESTY_{tag}_{name}.txt"
        raw.write_text(text)
        nodes = None
        for line in text.splitlines():
            if name.startswith("bench") and "info string bench depth" in line:
                parts = line.split()
                if "nodes" in parts:
                    nodes = int(parts[parts.index("nodes") + 1])
            if name == "perft5" and line.startswith("nodes "):
                nodes = int(line.split()[1])
        meta = out_dir / f"HONESTY_{tag}_{name}.meta"
        option_lines = [c for c in sent if c.startswith("setoption ")]
        meta.write_text(
            "\n".join(
                [
                    f"exe={exe}",
                    f"sha256={digest}",
                    f"id_name={id_name}",
                    "options_sent:",
                    *option_lines,
                    f"commands={' | '.join(sent)}",
                    f"nodes={nodes}",
                    f"expected={expected[name]}",
                    "",
                ]
            )
        )
        match = nodes == expected[name]
        ok = ok and match
        summary.append(f"{name} nodes {nodes} expected {expected[name]} {'OK' if match else 'MISMATCH'}")
        print(summary[-1], flush=True)
    (out_dir / f"HONESTY_{tag}.txt").write_text("\n".join(summary) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
