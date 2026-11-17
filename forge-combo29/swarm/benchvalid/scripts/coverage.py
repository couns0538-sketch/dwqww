#!/usr/bin/env python3
"""Function- and line-level coverage, per translation unit, for a UCI command script.

Usage: coverage.py <cov-build-dir> <label> <command-file>
Reports, per source file: functions executed / total, lines executed / total,
and writes JSON. Uses gcov's intermediate text output (-i is unreliable across
gcov versions, so this parses the `.gcov` per-line text instead).
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

def demangle(sym: str) -> str:
    try:
        r = subprocess.run(["c++filt", sym], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or sym
    except Exception:
        return sym


GCOV_FUNC = re.compile(r"^function (\S+) called (\d+) returned \S+ blocks executed (\S+)$")
GCOV_LINE = re.compile(r"^\s*(#####|=====|-|[0-9]+(?:\*)?|\$+):\s*([0-9]+):(.*)$")


def run(cov_dir: str, label: str, cmd_path: str) -> dict:
    gcda = []
    for root, _dirs, files in os.walk(cov_dir):
        for f in files:
            if f.endswith(".gcda"):
                gcda.append(os.path.join(root, f))
    for f in gcda:
        os.remove(f)

    script = pathlib.Path(cmd_path).read_text()
    p = subprocess.run([os.path.join(cov_dir, "forge")], input=script, capture_output=True, text=True, timeout=3600)

    work = pathlib.Path(cov_dir) / "_gcov" / label
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    per_file = {}
    for g in sorted(pathlib.Path(cov_dir).rglob("*.gcda")):
        objdir = g.parent
        srcs = list(objdir.glob(g.stem + ".gcno"))
        if not srcs:
            continue
        sub = subprocess.run(["gcov", "-b", "-c", "-f", "-o", str(objdir.resolve()), str(srcs[0].resolve())],
                             capture_output=True, text=True, cwd=str(work))
        name = g.stem.replace(".cpp", "")
        fns, lines_total, lines_hit = [], 0, 0
        gcov_file = work / (g.stem + ".cpp.gcov")
        if not gcov_file.exists():
            cands = list(work.glob(g.stem + "*.gcov"))
            gcov_file = cands[0] if cands else None
        text = gcov_file.read_text() if gcov_file else ""
        for line in text.splitlines():
            m = GCOV_FUNC.match(line.strip())
            if m:
                fns.append({"name": demangle(m.group(1)), "called": int(m.group(2))})
                continue
            m = GCOV_LINE.match(line)
            if m:
                count, lineno = m.group(1), int(m.group(2))
                body = m.group(3).strip()
                if count == "-" or body in ("", "{", "}"):
                    continue  # no executable code on this line
                lines_total += 1
                if count[0].isdigit():
                    if int(count.rstrip("*")) > 0:
                        lines_hit += 1
        per_file[name] = {
            "functions": len(fns),
            "functions_called": sum(1 for f in fns if f["called"] > 0),
            "functions_never_called": [f["name"] for f in fns if f["called"] == 0],
            "lines": lines_total,
            "lines_hit": lines_hit,
            "line_pct": round(100.0 * lines_hit / lines_total, 1) if lines_total else None,
        }

    # The .gcov per-line text for the largest unit, if asked for later.
    return {
        "label": label,
        "command_file": cmd_path,
        "command_file_sha256_script": script,
        "exit_code": p.returncode,
        "stdout_tail": p.stdout.strip().splitlines()[-4:],
        "files": per_file,
    }


if __name__ == "__main__":
    result = run(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(result, indent=2))
