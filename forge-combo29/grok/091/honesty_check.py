#!/usr/bin/env python3
"""Honesty check. One fresh engine process per command. No setoption."""
import hashlib
import pathlib
import subprocess
import sys

EXPECTED = {
    "bench 11": "312866",
    "bench 13": "862329",
    "bench 16": "3024920",
    "go perft 5": "4865609",
}


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name(text):
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name "):]
    return ""


def node_line(text, command):
    if command.startswith("bench"):
        for line in text.splitlines():
            if line.startswith("info string bench depth "):
                return line
        return ""
    for line in reversed(text.splitlines()):
        if line.startswith("nodes "):
            return line
    return ""


def nodes_of(line):
    parts = line.split()
    if "nodes" not in parts:
        return ""
    return parts[parts.index("nodes") + 1]


def main():
    if len(sys.argv) != 4:
        print("usage: honesty_check.py EXE OUTDIR TAG", file=sys.stderr)
        return 2
    exe = pathlib.Path(sys.argv[1]).resolve()
    out_dir = pathlib.Path(sys.argv[2]).resolve()
    tag = sys.argv[3]
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256_file(exe)
    failed = False
    combined = []
    for command, expected in EXPECTED.items():
        slug = command.replace(" ", "")
        proc = subprocess.run(
            [str(exe)],
            input=f"uci\nisready\n{command}\nquit\n",
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
        raw_path = out_dir / f"honesty_{tag}_{slug}.txt"
        meta_path = out_dir / f"honesty_{tag}_{slug}.meta"
        raw = proc.stdout
        if proc.stderr:
            raw = raw + "\n--- stderr ---\n" + proc.stderr
        raw_path.write_text(raw)
        name = id_name(proc.stdout)
        meta = (
            f"exe={exe}\n"
            f"sha256={digest}\n"
            f"id_name={name}\n"
            f"options_sent=none\n"
            f"command={command}\n"
            f"returncode={proc.returncode}\n"
        )
        meta_path.write_text(meta)
        line = node_line(proc.stdout, command)
        got = nodes_of(line)
        status = "PASS" if got == expected else "FAIL"
        if status != "PASS":
            failed = True
        record = f"{status} {command} expected {expected} got {got} line {line}"
        print(record)
        combined.append(record)
        combined.append(f"FILE {raw_path.name}")
        combined.append(raw.rstrip("\n"))
        combined.append("")
    summary = out_dir / f"HONESTY_{tag.upper()}.txt"
    summary.write_text("\n".join(combined) + "\n")
    print(f"wrote {summary}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
