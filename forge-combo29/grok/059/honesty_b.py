#!/usr/bin/env python3
"""Honesty check for exe B. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path("/agent/repos/base/forge-combo29/build/forge")
OUT_DIR = Path(__file__).resolve().parent
CHECKS = [
    ("bench11", "bench 11", 312866),
    ("bench13", "bench 13", 862329),
    ("bench16", "bench 16", 3024920),
    ("perft5", "go perft 5", 4865609),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: str, timeout: int) -> tuple[str, str, int]:
    proc = subprocess.run(
        [str(EXE)],
        input=command + "\nquit\n",
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return proc.stdout, proc.stderr, proc.returncode


def id_name_of(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return ""


def nodes_of(label: str, text: str) -> int | None:
    if label.startswith("bench"):
        prefix = "info string bench depth "
        for line in text.splitlines():
            if line.startswith(prefix) and " nodes " in line:
                parts = line.split()
                # info string bench depth D nodes N time ...
                if "nodes" in parts:
                    return int(parts[parts.index("nodes") + 1])
        return None
    for line in text.splitlines():
        if line.startswith("nodes "):
            return int(line.split()[1])
    return None


def main() -> int:
    digest = sha256(EXE)
    ident_out, ident_err, ident_rc = run("uci", 30)
    (OUT_DIR / "honesty_b_uci.txt").write_text(ident_out)
    (OUT_DIR / "honesty_b_uci.err").write_text(ident_err)
    name = id_name_of(ident_out)
    rows = []
    failed = False
    for label, command, expected in CHECKS:
        stdout, stderr, rc = run(command, 180)
        raw = OUT_DIR / f"honesty_b_{label}.txt"
        err = OUT_DIR / f"honesty_b_{label}.err"
        meta = OUT_DIR / f"honesty_b_{label}.meta"
        raw.write_text(stdout)
        err.write_text(stderr)
        meta.write_text(
            "\n".join(
                [
                    f"exe={EXE}",
                    f"sha256={digest}",
                    f"id_name={name}",
                    "options=",
                    f"command={command}",
                    "then=quit",
                    f"returncode={rc}",
                    "identity_process=honesty_b_uci.txt",
                    f"identity_returncode={ident_rc}",
                    "",
                ]
            )
        )
        got = nodes_of(label, stdout)
        ok = got == expected and rc == 0 and stderr == ""
        if not ok:
            failed = True
        rows.append(f"{command} nodes {got} expected {expected} {'ok' if ok else 'FAIL'}")
    summary = OUT_DIR / "HONESTY_B.txt"
    summary.write_text(
        "\n".join(
            [
                f"exe={EXE}",
                f"sha256={digest}",
                f"id_name={name}",
                *rows,
                "FAIL" if failed else "PASS",
                "",
            ]
        )
    )
    print(summary.read_text(), end="")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
