#!/usr/bin/env python3
"""Honesty check: one fresh engine process per line, no setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXPECTED = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}
COMMANDS = {
    "bench11": "bench 11\nquit\n",
    "bench13": "bench 13\nquit\n",
    "bench16": "bench 16\nquit\n",
    "perft5": "go perft 5\nquit\n",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(exe: Path, script: str, timeout: int) -> str:
    result = subprocess.run(
        [str(exe)],
        input=script,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return result.stdout + result.stderr


def nodes_of(text: str, kind: str) -> int:
    if kind == "perft5":
        last = None
        for line in text.splitlines():
            if line.startswith("nodes "):
                last = int(line.split()[1])
        if last is None:
            raise SystemExit("perft produced no nodes line")
        return last
    last = None
    for line in text.splitlines():
        if " nodes " in line and line.startswith("info string bench"):
            parts = line.split()
            last = int(parts[parts.index("nodes") + 1])
    if last is None:
        raise SystemExit("bench produced no nodes line:\n" + text)
    return last


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: honesty_b.py <exe> <out-dir>")
    exe = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    digest = sha256(exe)
    uci = run(exe, "uci\nquit\n", 30)
    (out / "honesty_b_uci.txt").write_text(uci)
    id_name = ""
    for line in uci.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    summary = [
        f"exe {exe}",
        f"sha256 {digest}",
        f"id name {id_name}",
        "setoption lines: none",
    ]
    failed = False
    for kind, script in COMMANDS.items():
        text = run(exe, script, 240)
        (out / f"honesty_b_{kind}.txt").write_text(text)
        got = nodes_of(text, kind)
        ok = got == EXPECTED[kind]
        if not ok:
            failed = True
        meta = (
            f"exe {exe}\n"
            f"sha256 {digest}\n"
            f"id name {id_name}\n"
            f"command {script.strip()}\n"
            "option lines: none\n"
            f"nodes {got}\n"
            f"expected {EXPECTED[kind]}\n"
            f"match {str(ok).lower()}\n"
        )
        (out / f"honesty_b_{kind}.meta").write_text(meta)
        summary.append(f"{kind} nodes {got} expected {EXPECTED[kind]} match {str(ok).lower()}")
    summary.append("FAIL" if failed else "PASS")
    (out / "HONESTY_B.txt").write_text("\n".join(summary) + "\n")
    print("\n".join(summary))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
