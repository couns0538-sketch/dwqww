#!/usr/bin/env python3
"""Honesty check of exe B. One fresh process per line. No setoption."""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

EXE = Path("/agent/repos/base/forge-combo29/build/forge")
OUT = Path(__file__).resolve().parent
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


def run(lines: list[str], timeout: int) -> tuple[str, str, int]:
    proc = subprocess.run(
        [str(EXE)],
        input=("\n".join(lines) + "\n").encode(),
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace"), proc.returncode


def main() -> int:
    if not EXE.is_file():
        print(f"missing exe {EXE}", file=sys.stderr)
        return 2
    digest = sha256(EXE)
    id_out, id_err, id_rc = run(["uci", "quit"], 30)
    (OUT / "honesty_b_id.txt").write_text(id_out + (("\n# stderr\n" + id_err) if id_err else ""), encoding="utf-8")
    id_name = ""
    for line in id_out.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    rows = []
    ok = True
    for command, expected in EXPECTED.items():
        slug = command.replace(" ", "_")
        stdout, stderr, rc = run([command, "quit"], 300)
        raw_path = OUT / f"honesty_b_{slug}.txt"
        text = stdout
        if stderr:
            text += "\n# stderr\n" + stderr
        raw_path.write_text(text, encoding="utf-8")
        if command.startswith("bench"):
            found = [int(n) for n in re.findall(r"bench depth \d+ nodes (\d+)", stdout)]
        else:
            found = [int(n) for n in re.findall(r"(?m)^nodes (\d+)\s*$", stdout)]
        got = found[-1] if found else None
        match = got == expected
        ok = ok and match and rc == 0
        meta = (
            f"exe_started={EXE}\n"
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
        (OUT / f"honesty_b_{slug}.meta").write_text(meta, encoding="utf-8")
        rows.append((command, got, expected, match))
        print(f"{command} nodes {got} expected {expected} match {match}")
    summary = ["HONESTY exe B", f"exe_started={EXE}", f"sha256={digest}", f"id_name={id_name}"]
    for command, got, expected, match in rows:
        summary.append(f"{command} -> nodes {got} expected {expected} match {str(match).lower()}")
    summary.append("PASS" if ok else "FAIL")
    text = "\n".join(summary) + "\n"
    (OUT / "HONESTY_B.txt").write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
