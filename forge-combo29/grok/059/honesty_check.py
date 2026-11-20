#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption. Tag selects the output names."""
import hashlib
import subprocess
import sys
from pathlib import Path

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


def run(exe: Path, command: str, timeout: int) -> tuple[str, str, int]:
    proc = subprocess.run(
        [str(exe)],
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
        for line in text.splitlines():
            if line.startswith("info string bench depth ") and " nodes " in line:
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        return None
    for line in text.splitlines():
        if line.startswith("nodes "):
            return int(line.split()[1])
    return None


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: honesty_check.py EXE TAG OUTDIR", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    tag = sys.argv[2]
    out_dir = Path(sys.argv[3])
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256(exe)
    ident_out, ident_err, ident_rc = run(exe, "uci", 30)
    (out_dir / f"{tag}_uci.txt").write_text(ident_out)
    (out_dir / f"{tag}_uci.err").write_text(ident_err)
    name = id_name_of(ident_out)
    rows = []
    failed = False
    for label, command, expected in CHECKS:
        stdout, stderr, rc = run(exe, command, 180)
        (out_dir / f"{tag}_{label}.txt").write_text(stdout)
        (out_dir / f"{tag}_{label}.err").write_text(stderr)
        (out_dir / f"{tag}_{label}.meta").write_text(
            "\n".join(
                [
                    f"exe={exe}",
                    f"sha256={digest}",
                    f"id_name={name}",
                    "options=",
                    f"command={command}",
                    "then=quit",
                    f"returncode={rc}",
                    f"identity_process={tag}_uci.txt",
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
    summary = out_dir / f"HONESTY_{tag}.txt"
    summary.write_text(
        "\n".join(
            [
                f"exe={exe}",
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
