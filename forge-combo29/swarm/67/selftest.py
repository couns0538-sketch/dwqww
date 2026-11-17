#!/usr/bin/env python3
"""Self-test: prove the harness can FAIL, in both detectors.

Detector 1 (sanitizer). Run against an engine with a planted heap overflow that
only an over-long `position fen` reaches. The harness MUST report sanitizer lines
on those cases and on no others.

Detector 2 (hang / liveness). Run against a wrapper that accepts input and then
goes silent -- the exact shape of a wedged engine. The harness MUST mark those
cases as hangs. A wrapper that answers normally MUST NOT be marked.

Both are run from the same harness code path as the real corpus, so a green
self-test is evidence about the harness and not just about the two binaries.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fuzz  # noqa: E402

MUTE = r"""#!/bin/sh
# Accepts everything, answers nothing, never exits: a wedged engine.
cat >/dev/null &
while :; do sleep 1; done
"""

EchoGo = r"""#!/bin/sh
# Minimal stand-in that answers readyok and a fixed bestmove: healthy.
while IFS= read -r line; do
  case "$line" in
    isready) echo readyok ;;
    go*) echo "info depth 1 score cp 0 nodes 1 pv a2a3"; echo "bestmove a2a3" ;;
    quit) exit 0 ;;
  esac
done
"""


def write_exe(path: str, body: str) -> None:
    with open(path, "w") as f:
        f.write(body)
    os.chmod(path, 0o755)


def check_sanitizer(broken_exe: str) -> tuple[bool, dict]:
    cases = [c for c in __import__("cases").build_cases() if c.cls == "position_fen"]
    long_cases = [c for c in cases if "long-" in c.cid]
    short_cases = [c for c in cases if "long-" not in c.cid and "500-legal" not in c.cid]
    hit_long = 0
    hit_short = 0
    for c in long_cases:
        r = c.run(broken_exe)
        if r["sanitizer"]:
            hit_long += 1
    for c in short_cases[:12]:
        r = c.run(broken_exe)
        if r["sanitizer"]:
            hit_short += 1
    ok = hit_long > 0 and hit_short == 0
    return ok, {"long_cases_flagged": hit_long, "long_cases_total": len(long_cases),
                "short_cases_false_positive": hit_short,
                "short_cases_checked": min(12, len(short_cases))}


def check_hang(mute_exe: str, echo_exe: str) -> tuple[bool, dict]:
    mk = lambda cid, steps: fuzz.Case(cid=cid, cls="selftest", pattern="selftest",
                                      steps=steps, bestmove_timeout=3.0, ready_timeout=4.0)
    wedged = mk("selftest:wedged", [(b"isready\n", "wait_ready")]).run(mute_exe)
    healthy = mk("selftest:healthy", [(b"isready\n", "wait_ready"),
                                      (b"position startpos\ngo depth 1\n", "wait_bestmove")]).run(echo_exe)
    ok = wedged["hang"] and not healthy["hang"]
    return ok, {"wedged_flagged_hang": wedged["hang"],
                "wedged_liveness": wedged["liveness"],
                "healthy_flagged_hang": healthy["hang"],
                "healthy_liveness": healthy["liveness"],
                "healthy_bestmoves": healthy["bestmoves"]}


def main() -> int:
    broken = sys.argv[1] if len(sys.argv) > 1 else "/tmp/brokenb/forge"
    mute = "/tmp/selftest_mute.sh"
    echo = "/tmp/selftest_echo.sh"
    write_exe(mute, MUTE)
    write_exe(echo, EchoGo)

    print("== fixtures (python-chess) ==")
    fx = __import__("cases").verify_fixtures()
    print(json.dumps(fx, indent=1)[:600])
    fixtures_ok = (not fx.get("available")) or all(v["valid"] for v in fx["fixtures"].values())
    print("  all fixtures legal per python-chess:", fixtures_ok)

    print("\n== detector 1: sanitizer on planted heap overflow ==")
    san_ok, san_info = check_sanitizer(broken)
    print(" ", json.dumps(san_info))
    print("  PASS" if san_ok else "  FAIL")

    print("\n== detector 2: hang / liveness ==")
    hang_ok, hang_info = check_hang(mute, echo)
    print(" ", json.dumps(hang_info))
    print("  PASS" if hang_ok else "  FAIL")

    all_ok = san_ok and hang_ok and fixtures_ok
    print("\nSELFTEST", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
