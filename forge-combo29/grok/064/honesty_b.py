#!/usr/bin/env python3
"""Honesty check on exe B. One fresh process per line. No setoption."""
import hashlib
import pathlib
import subprocess
import sys

EXE = pathlib.Path("/agent/repos/base/forge-combo29/build/forge")
OUT = pathlib.Path(__file__).resolve().parent
CASES = [
    ("bench11", ["uci", "bench 11", "quit"], "312866"),
    ("bench13", ["uci", "bench 13", "quit"], "862329"),
    ("bench16", ["uci", "bench 16", "quit"], "3024920"),
    ("perft5", ["uci", "go perft 5", "quit"], "4865609"),
]


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return ""


def main() -> int:
    if not EXE.is_file():
        print(f"missing exe {EXE}", file=sys.stderr)
        return 2
    digest = sha256(EXE)
    lines = []
    failed = False
    for name, commands, expect in CASES:
        proc = subprocess.run(
            [str(EXE)],
            input="\n".join(commands) + "\n",
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
        raw = proc.stdout
        (OUT / f"honesty_b_{name}.txt").write_text(raw)
        (OUT / f"honesty_b_{name}.err").write_text(proc.stderr)
        meta = (
            f"exe {EXE}\n"
            f"sha256 {digest}\n"
            f"id name {id_name(raw)}\n"
            "options\n"
            "(none)\n"
            "commands\n"
            + "\n".join(commands)
            + "\n"
        )
        (OUT / f"honesty_b_{name}.meta").write_text(meta)
        got = ""
        for line in raw.splitlines():
            if " nodes " in f" {line} " or line.startswith("nodes ") or " nodes " in line:
                parts = line.replace(":", " ").split()
                if "nodes" in parts:
                    got = parts[parts.index("nodes") + 1]
        ok = got == expect and proc.returncode == 0
        if not ok:
            failed = True
        lines.append(f"{name} nodes {got} expect {expect} {'OK' if ok else 'FAIL'}")
        print(lines[-1], flush=True)
    (OUT / "HONESTY_B.txt").write_text(
        "\n".join(
            [
                f"exe {EXE}",
                f"sha256 {digest}",
                *lines,
            ]
        )
        + "\n"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
