#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption."""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

EXPECTED = {
    "bench 11": 312866,
    "bench 13": 862329,
    "bench 16": 3024920,
    "go perft 5": 4865609,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def run(exe: Path, lines: list[str], timeout: int) -> tuple[str, str, int]:
    proc = subprocess.run(
        [str(exe)],
        input=("\n".join(lines) + "\n").encode(),
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace"), proc.returncode


def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    prefix = sys.argv[2]
    out = Path(sys.argv[3]).resolve()
    digest = sha256(exe)
    id_out, id_err, id_rc = run(exe, ["uci", "quit"], 60)
    (out / f"{prefix}_id.txt").write_text(id_out + (("\n# stderr\n" + id_err) if id_err else ""), encoding="utf-8")
    id_name = ""
    for line in id_out.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    rows = []
    ok = True
    for command, expected in EXPECTED.items():
        slug = command.replace(" ", "_")
        stdout, stderr, rc = run(exe, [command, "quit"], 300)
        text = stdout + (("\n# stderr\n" + stderr) if stderr else "")
        (out / f"{prefix}_{slug}.txt").write_text(text, encoding="utf-8")
        if command.startswith("bench"):
            found = [int(n) for n in re.findall(r"bench depth \d+ nodes (\d+)", stdout)]
        else:
            found = [int(n) for n in re.findall(r"(?m)^nodes (\d+)\s*$", stdout)]
        got = found[-1] if found else None
        match = got == expected
        ok = ok and match and rc == 0
        meta = (
            f"exe_started={exe}\n"
            f"sha256={digest}\n"
            f"id_name={id_name}\n"
            f"options_sent=\n"
            f"command={command}\n"
            f"exit={rc}\n"
            f"nodes={got}\n"
            f"expected={expected}\n"
            f"match={str(match).lower()}\n"
            f"id_probe_exit={id_rc}\n"
        )
        (out / f"{prefix}_{slug}.meta").write_text(meta, encoding="utf-8")
        rows.append((command, got, expected, match))
        print(f"{command} nodes {got} expected {expected} match {match}")
    summary = [f"HONESTY {prefix}", f"exe_started={exe}", f"sha256={digest}", f"id_name={id_name}"]
    for command, got, expected, match in rows:
        summary.append(f"{command} -> nodes {got} expected {expected} match {str(match).lower()}")
    summary.append("PASS" if ok else "FAIL")
    text = "\n".join(summary) + "\n"
    (out / f"HONESTY_{prefix}.txt").write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
