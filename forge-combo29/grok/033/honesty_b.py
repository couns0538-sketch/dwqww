#!/usr/bin/env python3
"""Honesty check for one engine. Fresh process per line. No setoption."""
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(exe: Path, commands: str) -> str:
    result = subprocess.run(
        [str(exe)],
        input=commands,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout + result.stderr


def id_name(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :].strip()
    return ""


def nodes_of(text: str) -> int | None:
    found = None
    for line in text.splitlines():
        parts = line.split()
        if "nodes" in parts:
            index = parts.index("nodes")
            if index + 1 < len(parts):
                token = parts[index + 1]
                if token.isdigit():
                    found = int(token)
    return found


def write_meta(path: Path, exe: Path, digest: str, name: str, options: list[str]) -> None:
    lines = [
        f"exe={exe}",
        f"sha256={digest}",
        f"id_name={name}",
        "options:",
    ]
    lines.extend(options if options else ["(none)"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: honesty_b.py EXE OUTDIR", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    outdir = Path(sys.argv[2]).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    digest = sha256(exe)
    uci_text = run(exe, "uci\nquit\n")
    (outdir / "honesty_b_uci.txt").write_text(uci_text, encoding="utf-8")
    name = id_name(uci_text)
    write_meta(outdir / "honesty_b_uci.meta", exe, digest, name, [])

    jobs = [
        ("bench11", "bench 11\nquit\n", "honesty_b_bench11.txt"),
        ("bench13", "bench 13\nquit\n", "honesty_b_bench13.txt"),
        ("bench16", "bench 16\nquit\n", "honesty_b_bench16.txt"),
        ("perft5", "go perft 5\nquit\n", "honesty_b_perft5.txt"),
    ]
    rows = []
    ok = True
    for key, commands, filename in jobs:
        text = run(exe, commands)
        raw = outdir / filename
        raw.write_text(text, encoding="utf-8")
        write_meta(raw.with_suffix(".meta"), exe, digest, name, [])
        got = nodes_of(text)
        want = EXPECTED[key]
        match = got == want
        ok = ok and match
        rows.append((key, got, want, match, filename))

    report = outdir / "HONESTY_B.txt"
    body = [f"exe={exe}", f"sha256={digest}", f"id_name={name}", "setoption=none"]
    for key, got, want, match, filename in rows:
        body.append(f"{key} nodes={got} expected={want} match={str(match).lower()} file={filename}")
    body.append(f"pass={str(ok).lower()}")
    report.write_text("\n".join(body) + "\n", encoding="utf-8")
    print("\n".join(body))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
