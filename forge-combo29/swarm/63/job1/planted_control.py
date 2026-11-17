"""Plant one fault behind input we control, and prove the same runner reports it.

The brief's rule: "0 sanitizer lines" counts only with (1) sanitizer symbols in the exe and
(2) a scratch copy with a planted fault that the SAME runner catches. Without the planted
run, a zero is indistinguishable from a build without instrumentation or a stale option.

The fault: on a FEN whose board part is a sentinel, read one byte past a heap buffer.
ASan must print "heap-buffer-overflow" and exit non-zero.
"""
import os
import re
import subprocess
import sys

EXE = sys.argv[1]
TAG = sys.argv[2]


def count_symbols(exe):
    asan = subprocess.run(["nm", "-C", exe], capture_output=True, text=True).stdout
    return asan.count("__asan_"), asan.count("__ubsan_")


def run(exe, script, env=None):
    e = dict(os.environ)
    e.pop("ASAN_OPTIONS", None)
    e.pop("UBSAN_OPTIONS", None)
    e.pop("TSAN_OPTIONS", None)
    if env:
        e.update(env)
    p = subprocess.run([exe], input=script, capture_output=True, text=True, env=e, timeout=300)
    return p.stdout + p.stderr, p.returncode


def sanitizer_lines(text):
    pats = ["ERROR: AddressSanitizer", "runtime error:", "SUMMARY: "]
    return [l for l in text.splitlines() if any(p in l for p in pats)]


def main():
    a, u = count_symbols(EXE)
    print("%s: __asan_ symbols = %d, __ubsan_ symbols = %d" % (TAG, a, u))
    print("planted-control-required: %s" % ("YES (instrumented)" if a > 0 else "NO (not instrumented)"))

    # 1. the honest run: the drawn-root fixtures plus a bench, no fault path taken
    honest = "uci\nisready\nposition startpos\ngo perft 4\nisready\nposition fen 8/8/3k4/8/2Q1B3/8/3K4/8 w - - 100 1\nisready\ngo depth 6\nisready\nquit\n"
    out, rc = run(EXE, honest)
    lines = sanitizer_lines(out)
    print("\n[honest run] exit=%d sanitizer_lines=%d" % (rc, len(lines)))
    for l in lines[:5]:
        print("   ", l)

    # 2. the planted-fault run, same runner
    planted = "uci\nisready\nposition fen 8/8/3k4/8/2Q1B3/8/3K4/8 w - - 100 1\nisready\ngo faultprobe\nisready\nquit\n"
    out2, rc2 = run(EXE, planted)
    lines2 = sanitizer_lines(out2)
    print("\n[planted run] exit=%d sanitizer_lines=%d" % (rc2, len(lines2)))
    for l in lines2[:5]:
        print("   ", l)

    ok = (len(lines) == 0 and len(lines2) > 0)
    print("\nVERDICT: %s — honest run clean (%d) AND planted run caught (%d)" %
          ("CONTROL HOLDS" if ok else "CONTROL FAILS", len(lines), len(lines2)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
