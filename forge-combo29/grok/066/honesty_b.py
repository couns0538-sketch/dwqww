#!/usr/bin/env python3
"""Honesty check: one fresh engine process per line, no setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path(sys.argv[1])
OUT = Path(sys.argv[2])
PREFIX = sys.argv[3]  # HONESTY_B or HONESTY_P

CASES = [
    ("bench11", "bench 11", 312866),
    ("bench13", "bench 13", 862329),
    ("bench16", "bench 16", 3024920),
    ("perft5", "go perft 5", 4865609),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def run(command: str) -> tuple[str, str, int]:
    proc = subprocess.run(
        [str(EXE)],
        input=command + "\nquit\n",
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )
    return proc.stdout, proc.stderr, proc.returncode


def nodes_of(text: str) -> int | None:
    found = None
    for line in text.splitlines():
        parts = line.split()
        if "nodes" in parts:
            idx = parts.index("nodes")
            if idx + 1 < len(parts) and parts[idx + 1].isdigit():
                found = int(parts[idx + 1])
    return found


def main() -> int:
    uci_out, uci_err, uci_rc = run("uci")
    id_name = ""
    for line in uci_out.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
    digest = sha256(EXE)
    (OUT / f"{PREFIX}_uci.txt").write_text(uci_out)
    (OUT / f"{PREFIX}_uci.meta").write_text(
        f"exe {EXE}\nsha256 {digest}\nid name {id_name}\ncommand uci\noptions\nreturncode {uci_rc}\n"
    )
    if uci_err:
        (OUT / f"{PREFIX}_uci.err").write_text(uci_err)
    summary = []
    failed = False
    for name, command, expect in CASES:
        stdout, stderr, rc = run(command)
        (OUT / f"{PREFIX}_{name}.txt").write_text(stdout)
        if stderr:
            (OUT / f"{PREFIX}_{name}.err").write_text(stderr)
        (OUT / f"{PREFIX}_{name}.meta").write_text(
            "\n".join(
                [
                    f"exe {EXE}",
                    f"sha256 {digest}",
                    f"id name {id_name}",
                    f"command {command}",
                    "options",
                    f"returncode {rc}",
                    "",
                ]
            )
        )
        got = nodes_of(stdout)
        ok = got == expect
        if not ok:
            failed = True
        summary.append(f"{command} nodes {got} expect {expect} {'OK' if ok else 'MISMATCH'}")
        print(summary[-1])
    text = "\n".join(summary) + "\n"
    (OUT / f"{PREFIX}.txt").write_text(text)
    (OUT / f"{PREFIX}.meta").write_text(
        f"exe {EXE}\nsha256 {digest}\nid name {id_name}\ncommand summary of the four fresh processes\noptions\n"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
