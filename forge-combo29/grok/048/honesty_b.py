#!/usr/bin/env python3
"""Honesty check for exe B. One fresh process per command. No setoption."""
import hashlib
import pathlib
import subprocess
import sys

EXE = pathlib.Path("/agent/repos/base/forge-combo29/build/forge")
OUT = pathlib.Path(__file__).resolve().parent

EXPECTED = {
    "bench 11": 312866,
    "bench 13": 862329,
    "bench 16": 3024920,
    "go perft 5": 4865609,
}


def run(command: str) -> str:
    proc = subprocess.run(
        [str(EXE)],
        input=command + "\nquit\n",
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"engine exit {proc.returncode} for {command}")
    return proc.stdout


def nodes_of(command: str, text: str) -> int:
    if command.startswith("bench"):
        for line in text.splitlines():
            if "bench depth" in line and " nodes " in line:
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        raise SystemExit(f"no bench nodes in output for {command}")
    for line in reversed(text.splitlines()):
        if line.startswith("nodes "):
            return int(line.split()[1])
    raise SystemExit(f"no perft nodes in output for {command}")


def main() -> None:
    if not EXE.is_file():
        raise SystemExit(f"missing exe {EXE}")
    sha = hashlib.sha256(EXE.read_bytes()).hexdigest()
    id_proc = subprocess.run(
        [str(EXE)],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        check=False,
    )
    id_name = ""
    for line in id_proc.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    (OUT / "idname.raw.txt").write_text(id_proc.stdout)
    chunks = []
    failed = False
    for command, expect in EXPECTED.items():
        text = run(command)
        slug = command.replace(" ", "")
        (OUT / f"{slug}.raw.txt").write_text(text)
        got = nodes_of(command, text)
        meta = (
            f"exe={EXE}\n"
            f"sha256={sha}\n"
            f"id_name={id_name}\n"
            f"id_name_source=separate process, command uci, same exe path\n"
            f"options_sent=\n"
            f"command={command}\n"
            f"nodes={got}\n"
            f"expected={expect}\n"
        )
        (OUT / f"{slug}.meta.txt").write_text(meta)
        status = "OK" if got == expect else "MISMATCH"
        if got != expect:
            failed = True
        chunks.append(f"COMMAND {command}\n{text.rstrip()}\nNODES {got} EXPECT {expect} {status}\n")
        print(f"{command} nodes {got} {status}")
    (OUT / "HONESTY_B.txt").write_text("\n".join(chunks) + "\n")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
