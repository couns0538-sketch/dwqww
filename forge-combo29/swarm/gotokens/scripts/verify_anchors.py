#!/usr/bin/env python3
"""Check that the source anchors quoted in FINDINGS.md still say what they claim.

A line-number citation is the claim most likely to rot: it is checkable, it looks
authoritative, and nothing in a normal review re-reads the cited line. This reads
the base commit's `uci.cpp`, `search.cpp` and `uci_clock.hpp` and asserts that
each cited line contains the token the document says it does.

The anchors are the ones §2a, §3 and §4 rely on. If a line moves, this fails and
says which claim broke, rather than leaving the document pointing at nothing.
"""

from __future__ import annotations

import subprocess
import sys

BASE = "6b98f2170a3210e71beed04bbd2553972c253ed7"
REPO = "/agent/repos/dwqww"

# (path in repo, 1-based line, substring that must appear, what the doc claims)
ANCHORS = [
    ("forge-combo29/src/uci.cpp", 73, "bool is_go_keyword", "§1 the keyword list"),
    ("forge-combo29/src/uci.cpp", 80, "forge::SearchLimits parse_limits", "§1 parse_limits span starts here"),
    ("forge-combo29/src/uci.cpp", 91, "tokens[i++]", "§2a read_int consumes the value token"),
    ("forge-combo29/src/uci.cpp", 101, "parse_clock_ms(tokens[i++])", "§2a read_clock consumes the value token"),
    ("forge-combo29/src/uci.cpp", 103, "std::clamp(read_int(), 1, 64)", "§1 depth clamps to 1..64"),
    ("forge-combo29/src/uci.cpp", 106, "tokens[i++]", "§2a nodes branch consumes the value token"),
    ("forge-combo29/src/uci.cpp", 109, "result.ec == std::errc{}", "§2a nodes sets the limit only on success"),
    ("forge-combo29/src/uci.cpp", 110, "limits.nodes = value", "§2a the set that a failed parse skips"),
    ("forge-combo29/src/uci.cpp", 118, "std::clamp(read_int(), 0, 32)", "§1 mate clamps to 0..32"),
    ("forge-combo29/src/uci.cpp", 117, "std::max(1, read_int())", "§1 movestogo floors at 1"),
    ("forge-combo29/src/search.cpp", 2192, "std::max<std::int64_t>(1, limits.movetime_ms - overhead)",
     "§3 the 0-ms movetime becomes a 1 ms hard limit"),
    ("forge-combo29/src/search.cpp", 2320, "elapsed_ms() >= hard_limit_ms_", "§3 the root time check"),
    ("forge-combo29/src/search.cpp", 1287, "elapsed_ms() >= hard_limit_ms_", "§3 should_stop_with reads the same field"),
    ("forge-combo29/include/forge/uci_clock.hpp", 35, "result_out_of_range",
     "§2d an over-large clock clamps rather than failing"),
]

# Tokens whose absence would make a claim wrong rather than merely moved.
REQUIRED_SUBSTRINGS = [
    ("forge-combo29/src/uci.cpp", "if (token == \"depth\") limits.depth = std::clamp(read_int(), 1, 64);",
     "depth is the clamp-to-1 keyword"),
    ("forge-combo29/src/uci.cpp", "if (result.ec != std::errc{} || result.ptr != text.data() + text.size()) return 0;",
     "read_int returns 0 on failure"),
    ("forge-combo29/src/uci.cpp", "return forge::parse_clock_ms(tokens[i++]);",
     "read_clock delegates to the clamping parser"),
    ("forge-combo29/src/search.cpp", "if (limits.infinite) {", "infinite zeroes both time limits"),
    ("forge-combo29/src/uci.cpp", "const bool game_search =",
     "§4 the book eligibility predicate exists at uci.cpp:525"),
]


def read_line(path: str, lineno: int) -> str:
    out = subprocess.run(
        ["git", "-C", REPO, "show", f"{BASE}:{path}"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    if lineno > len(out):
        return ""
    return out[lineno - 1]


def read_file(path: str) -> str:
    return subprocess.run(
        ["git", "-C", REPO, "show", f"{BASE}:{path}"],
        capture_output=True, text=True, check=True,
    ).stdout


def main() -> int:
    failures: list[str] = []
    for path, lineno, needle, claim in ANCHORS:
        line = read_line(path, lineno)
        if needle not in line:
            failures.append(f"{path}:{lineno} should mention `{needle}` for {claim}; found: {line.strip()[:90]!r}")
    for path, needle, claim in REQUIRED_SUBSTRINGS:
        if needle not in read_file(path):
            failures.append(f"{path} no longer contains `{needle[:60]}` ({claim})")
    total = len(ANCHORS) + len(REQUIRED_SUBSTRINGS)
    print(f"{total} source anchors checked against {BASE}")
    if failures:
        print(f"\n{len(failures)} BROKEN ANCHOR(S):")
        for f in failures:
            print("  -", f)
        return 1
    print("every cited line still says what the document claims")
    return 0


if __name__ == "__main__":
    sys.exit(main())
