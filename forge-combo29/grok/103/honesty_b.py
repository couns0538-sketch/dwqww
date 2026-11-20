#!/usr/bin/env python3
"""Honesty check: fresh process per command, no setoption. Writes raw output and .meta."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXPECTED = {
    "bench11": ("bench 11", 312866),
    "bench13": ("bench 13", 862329),
    "bench16": ("bench 16", 3024920),
    "perft5": ("go perft 5", 4865609),
}

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

def read_until(proc, predicate, limit_lines=200000):
    lines = []
    while len(lines) < limit_lines:
        line = proc.stdout.readline()
        if line == "":
            break
        lines.append(line)
        if predicate(line):
            break
    return lines

def run_case(exe: Path, command: str):
    proc = subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write("uci\n")
    proc.stdin.flush()
    prelude = read_until(proc, lambda line: line.strip() == "uciok")
    proc.stdin.write(command + "\n")
    proc.stdin.flush()
    if command.startswith("bench"):
        body = read_until(proc, lambda line: "bench depth" in line)
    else:
        body = read_until(proc, lambda line: line.startswith("nodes "))
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    try:
        rest = proc.communicate(timeout=30)[0]
    except subprocess.TimeoutExpired:
        proc.kill()
        rest = proc.communicate()[0]
    if rest:
        body.append(rest if rest.endswith("\n") else rest + "\n")
    id_name = ""
    for line in prelude:
        if line.startswith("id name "):
            id_name = line[len("id name "):].rstrip("\n")
    return prelude + body, id_name

def parse_nodes(tag: str, text: str):
    if tag.startswith("bench"):
        for line in reversed(text.splitlines()):
            if "bench depth" in line and " nodes " in line:
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        return None
    for line in reversed(text.splitlines()):
        if line.startswith("nodes "):
            return int(line.split()[1])
    return None

def main() -> int:
    if len(sys.argv) != 3:
        print("usage: honesty_b.py EXE OUTDIR", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256_file(exe)
    summary = []
    failed = False
    for tag, (command, expect) in EXPECTED.items():
        raw_lines, id_name = run_case(exe, command)
        text = "".join(raw_lines)
        raw_path = out_dir / f"honesty_b_{tag}.txt"
        meta_path = out_dir / f"honesty_b_{tag}.meta"
        raw_path.write_text(text)
        meta = (
            f"exe={exe}\n"
            f"sha256={digest}\n"
            f"id_name={id_name}\n"
            f"command={command}\n"
            f"options_sent=0\n"
        )
        meta_path.write_text(meta)
        got = parse_nodes(tag, text)
        ok = got == expect
        if not ok:
            failed = True
        summary.append(f"{command} nodes {got} expected {expect} {'OK' if ok else 'FAIL'}")
        print(summary[-1], flush=True)
    report = out_dir / "HONESTY_B.txt"
    report.write_text(
        f"exe={exe}\nsha256={digest}\n" + "\n".join(summary) + "\n"
        + ("HONESTY_B PASS\n" if not failed else "HONESTY_B FAIL\n")
    )
    print(report.read_text(), end="")
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
