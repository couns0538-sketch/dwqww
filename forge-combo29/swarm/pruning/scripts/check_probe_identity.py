#!/usr/bin/env python3
"""Prove the probe is PASSIVE before any count taken with it is trusted.

Three arms are compared on the four honesty pins:
  A  build/base/forge    the AUDIT BASE (6b98f217) rebuilt from pristine source
  B  build/clean/forge   this branch's source (audit base + probe edits, probe off)
  C  build/probe/forge   the same source with -DFORGE_PRUNE_PROBE=ON

Claim under test: A == B == C on every pin. B == A proves the branch's committed
source behaves exactly like the audit base when the probe is compiled out. C == A
proves the probe only READS. If C differs, every counter it reports is suspect
and this script fails loudly.

All three arms are BUILT, not shipped as blobs (`scripts/build.sh all`). An
earlier version of this script required a committed pre-edit binary; that binary
is gitignored, so the check could not run from a clean clone. Building the base
from git is both reproducible and a stronger test.

Pins must be sent on stdin as UCI commands. `./forge bench 11` as argv prints
nothing and exits 0 (brief trap; that is a silent way to record no number), so
this script refuses to use argv form.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

PINS = {
    "bench11": (["bench 11"], 312866),
    "bench13": (["bench 13"], 862329),
    "bench16": (["bench 16"], 3024920),
    "perft5": (["go perft 5"], 4865609),
}


def run_pin(binary: str, commands: list[str]) -> int:
    """One process per pin. `bench N` must arrive on stdin (brief trap 3)."""
    payload = "\n".join(commands) + "\nquit\n"
    proc = subprocess.run([binary], input=payload, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"{binary} exited {proc.returncode}: {proc.stderr[:400]}")
    for line in proc.stdout.splitlines():
        if line.startswith("info string bench depth"):
            return int(line.split("nodes")[1].split()[0])
        if line.startswith("nodes "):
            return int(line.split()[1])
    raise RuntimeError(f"{binary} produced no pin line for {commands}: {proc.stdout[:400]}")


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "build/base/forge"
    clean = sys.argv[2] if len(sys.argv) > 2 else "build/clean/forge"
    probe = sys.argv[3] if len(sys.argv) > 3 else "build/probe/forge"

    missing = [p for p in (base, clean, probe) if not os.path.exists(p)]
    if missing:
        print(f"missing build arm(s): {missing}\n"
              f"run: bash scripts/build.sh all\n"
              f"(all three arms are built from source; no binary is committed)", file=sys.stderr)
        return 2

    results: dict[str, dict[str, int]] = {}
    failures: list[str] = []
    for name, binary in (("base", base), ("clean", clean), ("probe", probe)):
        results[name] = {}
        for pin, (cmds, expected) in PINS.items():
            got = run_pin(binary, cmds)
            results[name][pin] = got
            if got != expected:
                failures.append(f"{name}/{pin}: got {got}, pin says {expected}")

    for pin in PINS:
        vals = {n: results[n][pin] for n in ("base", "clean", "probe")}
        if len(set(vals.values())) != 1:
            failures.append(f"{pin}: arms disagree {vals}")

    print(json.dumps({"results": results, "failures": failures}, indent=2))
    if failures:
        print("\nFAIL -- an arm does not match its pin, or the probe is not passive.", file=sys.stderr)
        return 1
    print("\nOK -- all four pins match in all three arms; the probe is passive.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
