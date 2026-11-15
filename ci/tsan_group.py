"""Groups ThreadSanitizer reports (Opus session, 2026-11-15).

Reads stderr files, cuts them into reports (from "WARNING: ThreadSanitizer:" to the next "=================="),
and groups the reports by their kind plus the top five frames of each of the first two stacks (addresses and build
ids removed). For every group: how often it occurred, in which files, the frames, and where they lie: in
nnue_v3.cpp, in Worker::static_evaluate_v3, in uci.cpp, or elsewhere. No report is judged harmless or not.

    python tsan_group.py <out file> <stderr file> [<stderr file> ...]
"""
from __future__ import annotations

import re
import sys
from collections import OrderedDict

FRAME = re.compile(r"^\s+#(\d+)\s+(.*)$")
NOISE = re.compile(r"\s*\((?:[^()]*\+0x[0-9a-f]+|BuildId: [0-9a-f]+)\)")


def reports(text: str) -> list[str]:
    out, cur = [], None
    for line in text.splitlines():
        if "WARNING: ThreadSanitizer:" in line:
            if cur:
                out.append("\n".join(cur))
            cur = [line]
        elif cur is not None:
            if line.startswith("=================="):
                out.append("\n".join(cur))
                cur = None
            else:
                cur.append(line)
    if cur:
        out.append("\n".join(cur))
    return out


def key_of(rep: str) -> tuple[str, tuple[tuple[str, ...], ...]]:
    lines = rep.splitlines()
    kind = lines[0].split("ThreadSanitizer:", 1)[1].strip()
    kind = re.sub(r"\(pid=\d+\)", "", kind).strip()
    stacks: list[list[str]] = []
    cur: list[str] | None = None
    for ln in lines[1:]:
        m = FRAME.match(ln)
        if m:
            if m.group(1) == "0":
                cur = []
                stacks.append(cur)
            if cur is not None and len(cur) < 5:
                cur.append(NOISE.sub("", m.group(2)).strip())
    return kind, tuple(tuple(s) for s in stacks[:2])


def where(frames: tuple[tuple[str, ...], ...]) -> str:
    flat = " ".join(" ".join(s) for s in frames)
    places = [name for name, mark in (("nnue_v3.cpp", "nnue_v3.cpp"), ("Worker::static_evaluate_v3", "static_evaluate_v3"),
                                      ("uci.cpp", "uci.cpp")) if mark in flat]
    return ", ".join(places) if places else "elsewhere"


def main() -> int:
    out_path, files = sys.argv[1], sys.argv[2:]
    groups: "OrderedDict[tuple, dict]" = OrderedDict()
    total = 0
    for f in files:
        try:
            text = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for rep in reports(text):
            total += 1
            k = key_of(rep)
            g = groups.setdefault(k, {"count": 0, "files": set(), "first": rep})
            g["count"] += 1
            g["files"].add(f.replace("\\", "/").rsplit("/", 1)[-1])
    lines = [f"ThreadSanitizer reports in {len(files)} files: {total}, in {len(groups)} different groups", ""]
    for i, ((kind, frames), g) in enumerate(groups.items(), 1):
        lines.append(f"== group {i}: {kind} | {g['count']} times | in: {', '.join(sorted(g['files']))} | frames lie in: {where(frames)}")
        for j, st in enumerate(frames, 1):
            lines.append(f"   stack {j}:")
            lines += [f"      #{n} {fr}" for n, fr in enumerate(st)]
        lines.append("   first full report:")
        lines += ["      " + x for x in g["first"].splitlines()[:60]]
        lines.append("")
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(lines[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
