#!/usr/bin/env python3
"""argv_check.py EXE — seat 12's independent check of seat 02's S-F1.

Claim: the engine takes no command-line arguments; `EXE bench 13` prints nothing and exits 0,
while the same command on stdin works. A harness that drives the exe by argv measures an engine
that never read the command, which silently produces zeros.

Checks, each its own subprocess:
  A  EXE with argv ["bench","13"], stdin CLOSED       -> bytes printed, exit code
  B  EXE with argv ["bench","13"], stdin also fed     -> does argv change anything at all
  C  EXE with argv [] and "bench 13\\nquit\\n" on stdin  -> the working form, as the control
  D  EXE with a nonsense argv ["--help"] and no stdin -> bytes, exit code
  E  EXE with argv [] and NO stdin at all (EOF)       -> bytes, exit code

A and C are the pair that decides the claim: if A prints 0 bytes and C prints a bench line, the
engine ignores argv. Without C, "A printed nothing" could mean the binary is broken.
"""
import subprocess
import sys


def run(args, stdin_text, close_stdin):
    if close_stdin:
        # stdin at /dev/null: the engine sees EOF immediately and argv is its only input
        p = subprocess.run(args, capture_output=True, text=True, timeout=180,
                           stdin=subprocess.DEVNULL)
    else:
        p = subprocess.run(args, input=stdin_text or "", capture_output=True, text=True,
                           timeout=180)
    return {"argv": args[1:], "stdout_bytes": len(p.stdout), "stderr_bytes": len(p.stderr),
            "exit": p.returncode, "head": p.stdout.splitlines()[:3]}


def main():
    exe = sys.argv[1]
    print(f"exe {exe}\n")
    rows = []
    print(f"{'case':46} {'stdout B':>9} {'exit':>5}  first line")
    cases = [
        ("A argv bench 13, stdin CLOSED", [exe, "bench", "13"], None, True),
        ("B argv bench 13, stdin empty", [exe, "bench", "13"], "", False),
        ("C argv none, 'bench 13' on stdin (CONTROL)", [exe], "bench 13\nquit\n", False),
        ("D argv --help, stdin CLOSED", [exe, "--help"], None, True),
        ("E argv none, stdin CLOSED (EOF at once)", [exe], None, True),
    ]
    for label, args, stdin_text, close in cases:
        r = run(args, stdin_text, close)
        rows.append((label, r))
        head = r["head"][0][:60] if r["head"] else "(nothing)"
        print(f"{label:46} {r['stdout_bytes']:>9} {r['exit']:>5}  {head}")

    a = rows[0][1]
    c = rows[2][1]
    claim_holds = a["stdout_bytes"] == 0 and a["exit"] == 0 and c["stdout_bytes"] > 0
    print(f"\nS-F1 claim (argv ignored, stdin required): "
          f"{'CONFIRMED' if claim_holds else 'NOT CONFIRMED'}")
    print(f"  argv run printed {a['stdout_bytes']} bytes; stdin control printed "
          f"{c['stdout_bytes']} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
