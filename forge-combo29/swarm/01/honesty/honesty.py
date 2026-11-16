#!/usr/bin/env python3
"""swarm seat 01 honesty check: four known numbers, one fresh engine process per line.

Usage: honesty.py <exe> <outdir>
Writes per-check raw output files and a meta file (exe path, sha256, id name, lines sent).
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path


def run_one(exe, lines, timeout=900):
    p = subprocess.run([exe], input="\n".join(lines) + "\n", text=True,
                       capture_output=True, timeout=timeout)
    return p.stdout + p.stderr


def main():
    exe = sys.argv[1]
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)

    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    ident = run_one(exe, ["uci", "quit"])
    idname = ""
    for line in ident.splitlines():
        if line.startswith("id name "):
            idname = line
    meta = [
        "exe_started: %s" % exe,
        "sha256: %s" % sha,
        idname,
        "id line present: %s" % bool(idname),
        "--- every line sent per check follows (each check = own process) ---",
        "bench11: bench 11",
        "bench13: bench 13",
        "bench16: bench 16",
        "perft5: position startpos ; go perft 5",
        "no setoption and no isready were sent (the four pins ask for that)",
    ]
    (outdir / "meta.txt").write_text("\n".join(meta) + "\n")

    checks = [
        ("bench11", ["bench 11"], r"nodes\s+(\d+)"),
        ("bench13", ["bench 13"], r"nodes\s+(\d+)"),
        ("bench16", ["bench 16"], r"nodes\s+(\d+)"),
        ("perft5", ["position startpos", "go perft 5"], r"^nodes\s+(\d+)"),
    ]
    expect = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}

    rows = []
    for name, lines, pat in checks:
        out = run_one(exe, lines)
        (outdir / (name + ".txt")).write_text(out)
        m = re.findall(pat, out, re.MULTILINE)
        got = int(m[0]) if m else None
        rows.append((name, got, expect[name], "PASS" if got == expect[name] else "FAIL"))

    summary = ["check\tgot\texpected\tverdict"]
    for name, got, exp, verdict in rows:
        summary.append("%s\t%s\t%d\t%s" % (name, got, exp, verdict))
    text = "\n".join(summary) + "\n"
    (outdir / "summary.txt").write_text(text)
    print(text, end="")
    print("ALL PASS" if all(r[3] == "PASS" for r in rows) else "MISS")


if __name__ == "__main__":
    main()
