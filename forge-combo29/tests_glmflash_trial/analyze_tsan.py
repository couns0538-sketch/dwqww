#!/usr/bin/env python3
"""glmflash trial Step 5: group ThreadSanitizer reports from a raw log.

For every DIFFERENT report (grouped by the top frames of both stacks) it prints:
  - how often it occurred,
  - the top five frames of each stack,
  - whether any frame lies in nnue_v3.cpp or in Worker::static_evaluate_v3,
    or only elsewhere (for example the transposition table).

It does not judge whether a race is harmless; it lists what the tool printed.

Usage: python3 analyze_tsan.py <raw_tsan_log.txt> [<out_summary.txt>]
"""

import re
import sys
import hashlib
import pathlib
from collections import OrderedDict

SEP = re.compile(r"^={20,}\s*$")
STACK_HEAD = re.compile(r"^\s{2}\S.*\bby (thread [A-Za-z0-9]+|main thread)", re.IGNORECASE)
FRAME = re.compile(r"^\s+(#\d+)\s+(.*)$")

def parse_blocks(text: str):
    """Split the log into TSan report blocks; return list of (stacks, raw_lines)."""
    blocks = []
    current: list[str] = []
    for line in text.splitlines():
        if SEP.match(line):
            if current:
                blocks.append(current)
                current = []
        elif "WARNING: ThreadSanitizer" in line and not current:
            current.append(line)
        elif current:
            current.append(line)
    if current:
        blocks.append(current)
    parsed = []
    for block in blocks:
        stacks: list[list[str]] = []
        in_stack = False
        for line in block:
            if STACK_HEAD.match(line):
                stacks.append([])
                in_stack = True
            elif FRAME.match(line) and in_stack and stacks:
                stacks[-1].append(line.strip())
            elif line.strip() and not FRAME.match(line):
                # a non-frame, non-stack-header line ends the current stack
                in_stack = False
        parsed.append((stacks, block))
    return parsed

def classify(stacks) -> str:
    joined = "\n".join(f for stack in stacks for f in stack)
    tags = []
    if re.search(r"nnue_v3\.cpp", joined):
        tags.append("nnue_v3.cpp: yes")
    else:
        tags.append("nnue_v3.cpp: no")
    if re.search(r"static_evaluate_v3", joined):
        tags.append("Worker::static_evaluate_v3: yes")
    else:
        tags.append("Worker::static_evaluate_v3: no")
    if re.search(r"nnue_v3\.cpp|static_evaluate_v3", joined):
        tags.append("only elsewhere: no")
    else:
        tags.append("only elsewhere: yes")
    return "; ".join(tags)

def main() -> None:
    log_path = pathlib.Path(sys.argv[1])
    text = log_path.read_text(errors="replace")
    data = log_path.read_bytes()
    n_warn = text.count("WARNING: ThreadSanitizer")
    n_sum = len(re.findall(r"^SUMMARY: ThreadSanitizer", text, re.M))
    m = re.search(r"ThreadSanitizer: reported (\d+) warnings", text)
    reported = int(m.group(1)) if m else None

    groups: "OrderedDict[tuple, dict]" = OrderedDict()
    for stacks, block in parse_blocks(text):
        s1 = stacks[0] if len(stacks) > 0 else ["<no stack parsed>"]
        s2 = stacks[1] if len(stacks) > 1 else ["<no second stack>"]
        key = (tuple(s1[:5]), tuple(s2[:5]))
        g = groups.setdefault(key, {"count": 0, "stacks": (s1, s2), "blocks": []})
        g["count"] += 1
        if len(g["blocks"]) < 1:
            g["blocks"].append("\n".join(block))

    lines = []
    lines.append(f"log file: {log_path}")
    lines.append(f"size bytes: {len(data)}")
    lines.append(f"sha256: {hashlib.sha256(data).hexdigest()}")
    lines.append(f"blocks with WARNING: ThreadSanitizer: {n_warn}")
    lines.append(f"SUMMARY: ThreadSanitizer lines: {n_sum}")
    lines.append(f"TSan final 'reported N warnings': {reported}")
    lines.append(f"different report groups (top-5 frames of both stacks): {len(groups)}")
    lines.append("")
    for i, (key, g) in enumerate(groups.items(), 1):
        s1, s2 = g["stacks"]
        lines.append(f"== group {i}: occurred {g['count']} time(s) ==")
        lines.append("stack 1 top frames (up to 5):")
        for f in s1[:5]:
            lines.append(f"    {f}")
        lines.append("stack 2 top frames (up to 5):")
        for f in s2[:5]:
            lines.append(f"    {f}")
        lines.append(f"classification: {classify([s1, s2])}")
        lines.append("")
    out_text = "\n".join(lines)
    print(out_text)
    if len(sys.argv) > 2:
        pathlib.Path(sys.argv[2]).write_text(out_text + "\n")

if __name__ == "__main__":
    main()
