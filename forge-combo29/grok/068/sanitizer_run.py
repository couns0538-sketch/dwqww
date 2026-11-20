#!/usr/bin/env python3
"""Same runner for the sanitizer build and the scratch build.
Invokes suite_nodes.py, then prints every AddressSanitizer or UndefinedBehaviorSanitizer line.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUITE = HERE / "suite_nodes.py"


def main() -> int:
    if len(sys.argv) != 6:
        print("usage: sanitizer_run.py EXE FENS DEPTH OUTSTEM EXTRA", file=sys.stderr)
        return 2
    exe, fens, depth, out_stem, extra = sys.argv[1:]
    exe_path = Path(exe).resolve()
    nm = subprocess.run(["nm", "-C", str(exe_path)], capture_output=True, text=True, check=False)
    asan_count = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=0"
    env["UBSAN_OPTIONS"] = "print_stacktrace=1:halt_on_error=0"
    proc = subprocess.run(
        [sys.executable, str(SUITE), str(exe_path), fens, depth, out_stem, extra],
        text=True,
        capture_output=True,
        env=env,
    )
    stderr_path = Path(out_stem + ".stderr")
    stderr_text = stderr_path.read_text() if stderr_path.exists() else ""
    markers = ("AddressSanitizer", "UndefinedBehaviorSanitizer", "runtime error:")
    hits = [line for line in stderr_text.splitlines() if any(marker in line for marker in markers)]
    summary = [
        f"exe {exe_path}",
        f"asan_symbols {asan_count}",
        f"suite_exit {proc.returncode}",
        f"sanitizer_lines {len(hits)}",
    ]
    if hits:
        summary.append("first " + hits[0])
    text = "\n".join(summary) + "\n"
    Path(out_stem + ".san").write_text(text)
    sys.stdout.write(text)
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.returncode not in (0, 1) and not hits:
        sys.stdout.write(proc.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
