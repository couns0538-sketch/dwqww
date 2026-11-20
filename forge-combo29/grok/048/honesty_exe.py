#!/usr/bin/env python3
"""Honesty check. Usage: honesty_exe.py EXE OUTDIR TAG"""
import hashlib
import pathlib
import subprocess
import sys

EXPECTED = {
    "bench 11": 312866,
    "bench 13": 862329,
    "bench 16": 3024920,
    "go perft 5": 4865609,
}


def run(exe: str, command: str) -> str:
    proc = subprocess.run(
        [exe],
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
        raise SystemExit(f"no bench nodes for {command}")
    for line in reversed(text.splitlines()):
        if line.startswith("nodes "):
            return int(line.split()[1])
    raise SystemExit(f"no perft nodes for {command}")


def main() -> None:
    exe = pathlib.Path(sys.argv[1]).resolve()
    out = pathlib.Path(sys.argv[2])
    tag = sys.argv[3]
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    id_proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, check=False)
    id_name = ""
    for line in id_proc.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    (out / f"{tag}_idname.raw.txt").write_text(id_proc.stdout)
    chunks = []
    failed = False
    for command, expect in EXPECTED.items():
        text = run(str(exe), command)
        slug = tag + "_" + command.replace(" ", "")
        (out / f"{slug}.raw.txt").write_text(text)
        got = nodes_of(command, text)
        (out / f"{slug}.meta.txt").write_text(
            f"exe={exe}\nsha256={sha}\nid_name={id_name}\n"
            f"id_name_source=separate process, command uci, same exe path\n"
            f"options_sent=\ncommand={command}\nnodes={got}\nexpected={expect}\n"
        )
        status = "OK" if got == expect else "MISMATCH"
        if got != expect:
            failed = True
        chunks.append(f"COMMAND {command}\n{text.rstrip()}\nNODES {got} EXPECT {expect} {status}\n")
        print(f"{command} nodes {got} {status}")
    (out / f"HONESTY_{tag}.txt").write_text("\n".join(chunks) + "\n")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
