"""Runs the positive control of a sanitizer build (Opus, 2026-11-15; Fable's rule: no sanitizer result counts unless
its planted faults are reported with the same compiler and flags).

    python controls.py <asan|tsan> <san_control executable> <results file>
Exit code 0 only if "none" runs clean and every planted fault is reported; else 1 (the job must then fail).
"""
from __future__ import annotations

import subprocess
import sys

# For each planted fault the report lines that count. "stack" may be caught by UBSan's bounds check before
# AddressSanitizer sees it (seen 2026-11-15 with clang: "runtime error: index 12 out of bounds"); either report counts.
EXPECT = {
    "asan": [("none", None), ("heap", ("ERROR: AddressSanitizer",)),
             ("stack", ("ERROR: AddressSanitizer", "runtime error:")), ("uaf", ("ERROR: AddressSanitizer",)),
             ("signed", ("runtime error:",)), ("shift", ("runtime error:",))],
    "tsan": [("none", None), ("race", ("WARNING: ThreadSanitizer: data race",))],
}
ANY_REPORT = ("ERROR: AddressSanitizer", "runtime error:", "WARNING: ThreadSanitizer", "ERROR: LeakSanitizer")


def main() -> int:
    kind, exe, out = sys.argv[1], sys.argv[2], sys.argv[3]
    lines, ok_all = [f"positive control, {kind} build: {exe}"], True
    for mode, mark in EXPECT[kind]:
        p = subprocess.run([exe, mode], capture_output=True, text=True, timeout=120)
        err = p.stderr
        if mark is None:
            ok = p.returncode == 0 and "clean run" in p.stdout and not any(m in err for m in ANY_REPORT)
            want = "exit 0, 'clean run', no report"
        else:
            ok = p.returncode != 0 and any(m in err for m in mark)
            want = "exit not 0 and " + " or ".join(f"'{m}'" for m in mark) + " on stderr"
        ok_all &= ok
        lines.append(f"  {mode:7s} exit {p.returncode:4d} | expected: {want} | {'OK' if ok else 'NOT AS EXPECTED'}")
        first = next((ln for ln in err.splitlines() if any(m in ln for m in ANY_REPORT)), "")
        if first:
            lines.append(f"          first report line: {first.strip()[:200]}")
    lines.append("RESULT: " + ("PASS (every planted fault reported, the clean run clean)" if ok_all else
                               "FAIL (the sanitizer did not report as it must; results of this job do not count)"))
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
