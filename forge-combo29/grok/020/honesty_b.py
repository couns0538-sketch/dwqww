#!/usr/bin/env python3
"""Fresh-process honesty check of exe B. No setoption. Writes raw logs and HONESTY_B.txt."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path("/agent/repos/base/forge-combo29/build/forge")
OUT = Path(__file__).resolve().parent
EXPECT = {
    "bench 11": 312866,
    "bench 13": 862329,
    "bench 16": 3024920,
    "go perft 5": 4865609,
}


def run_one(command: str, raw_name: str) -> tuple[str, int | None]:
    proc = subprocess.run(
        [str(EXE)],
        input=command + "\nquit\n",
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    text = proc.stdout
    if proc.stderr:
        text += proc.stderr
    (OUT / raw_name).write_text(text)
    nodes = None
    for line in text.splitlines():
        if "nodes " in line:
            tail = line.strip().split()
            # last "nodes <int>" on the line
            if "nodes" in tail:
                idx = len(tail) - 1 - tail[::-1].index("nodes")
                if idx + 1 < len(tail) and tail[idx + 1].isdigit():
                    nodes = int(tail[idx + 1])
    return text, nodes


def main() -> int:
    sha = hashlib.sha256(EXE.read_bytes()).hexdigest()
    rows = []
    ok = True
    jobs = [
        ("bench 11", "honesty_b_bench11.txt"),
        ("bench 13", "honesty_b_bench13.txt"),
        ("bench 16", "honesty_b_bench16.txt"),
        ("go perft 5", "honesty_b_perft5.txt"),
    ]
    for command, raw_name in jobs:
        _text, nodes = run_one(command, raw_name)
        expect = EXPECT[command]
        status = "ok" if nodes == expect else "MISS"
        if status != "ok":
            ok = False
        rows.append((command, nodes, expect, status, raw_name))
        print(f"{command} nodes {nodes} expect {expect} {status}", flush=True)
    lines = [
        f"exe {EXE}",
        f"sha256 {sha}",
        "setoption none",
        "command nodes expect status raw",
    ]
    for command, nodes, expect, status, raw_name in rows:
        lines.append(f"{command} {nodes} {expect} {status} {raw_name}")
    lines.append("PASS" if ok else "FAIL")
    (OUT / "HONESTY_B.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
