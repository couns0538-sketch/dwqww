#!/usr/bin/env python3
"""plant_fault.py — prove an ASan+UBSan build is actually instrumented.

A sanitizer claim is vacuous unless the binary can be shown to CATCH a fault. This plants
one fault at a time at the exact site the candidate patch touches (the root-draw scan in
search.cpp), selected by the FORGE_PLANT env var, and asserts the binary reports it:

  FORGE_PLANT=asan   -> heap-buffer-overflow  (small offset: stays in the redzone, so ASan
                         classifies it rather than reporting a bare SEGV)
  FORGE_PLANT=ubsan  -> signed integer overflow

Two separate runs because ASan aborts on the first error, so one build cannot demonstrate
both a classifier hit and an independent UBSan hit in a single execution.

The shipped tree is never modified: this works on a scratch copy.
"""
import os
import re
import shutil
import subprocess
import sys

SRC_TREE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/work/candV_A/forge-combo29"
SCRATCH = "/home/ubuntu/work/plant_scratch"
BUILD = "/home/ubuntu/work/plant_build"
BASE_ENV = dict(os.environ)
BASE_ENV["LIBRARY_PATH"] = "/usr/lib/gcc/x86_64-linux-gnu/13"
BASE_ENV["ASAN_OPTIONS"] = "detect_leaks=0"

PLANT = """\
    // PLANTED FAULT (scratch tree only): exercised at the exact statement the candidate patch
    // adds, so a clean run of the real build is evidence rather than an absence of code paths.
    {
        const char* mode = std::getenv("FORGE_PLANT");
        if (mode != nullptr && std::strcmp(mode, "asan") == 0) {
            volatile int* heap = new int[4];
            heap[0] = 7;
            volatile int probe = heap[heap[0] + 4];     // reads past the allocation
            (void)probe;
            delete[] heap;
        } else if (mode != nullptr && std::strcmp(mode, "ubsan") == 0) {
            volatile int big = 2147483647;
            volatile int one = 1;
            volatile int sum = big + one;               // signed integer overflow
            (void)sum;
        }
    }
"""


def build(tree, outdir):
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    subprocess.run(["cmake", "-S", tree, "-B", outdir,
                    "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
                    "-DCMAKE_CXX_COMPILER=/usr/bin/g++",
                    "-DCMAKE_CXX_FLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer",
                    "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=address,undefined"],
                   check=True, capture_output=True, env=BASE_ENV)
    subprocess.run(["cmake", "--build", outdir, "-j4"], check=True, capture_output=True, env=BASE_ENV)
    return os.path.join(outdir, "forge")


def try_catch(exe, mode, timeout=900):
    env = dict(BASE_ENV)
    env["FORGE_PLANT"] = mode
    script = "uci\nposition fen 4k3/8/8/8/8/8/8/4K3 w - - 0 1\nisready\ngo depth 4\nquit\n"
    try:
        p = subprocess.run([exe], input=script, capture_output=True, text=True,
                           timeout=timeout, env=env)
    except subprocess.TimeoutExpired as exc:
        return (exc.stdout or "") + (exc.stderr or ""), False
    return p.stdout + p.stderr, p.returncode != 0


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    shutil.copytree(SRC_TREE, SCRATCH)
    path = os.path.join(SCRATCH, "src", "search.cpp")
    text = open(path).read()
    anchor = "    const bool root_drawn = root_draw_adjudicated;"
    assert text.count(anchor) == 1, "anchor not found exactly once"
    body = PLANT + anchor
    open(path, "w").write(text.replace(anchor, body))
    if "#include <cstring>" not in text:
        open(path, "w").write(open(path).read().replace(
            "#include <cstdint>", "#include <cstdint>\n#include <cstring>", 1))
    print("planted at:", anchor.strip())

    exe = build(SCRATCH, BUILD)
    print("planted binary:", exe)
    print("real binary unchanged:", SRC_TREE)

    blob_a, crash_a = try_catch(exe, "asan")
    a_classified = ("AddressSanitizer" in blob_a
                    and re.search(r"heap-buffer-overflow|stack-buffer-overflow", blob_a) is not None)
    print("\n--- FORGE_PLANT=asan")
    print("  nonzero exit:", crash_a, " classified heap/stack overflow:", a_classified)
    for line in [l for l in blob_a.splitlines() if "ERROR: AddressSanitizer" in l][:3]:
        print("   ", line.strip())

    blob_u, crash_u = try_catch(exe, "ubsan")
    u_caught = re.search(r"runtime error: signed integer overflow", blob_u) is not None
    print("\n--- FORGE_PLANT=ubsan")
    print("  nonzero exit:", crash_u, " signed-overflow report:", u_caught)
    for line in [l for l in blob_u.splitlines() if "runtime error" in l][:3]:
        print("   ", line.strip())

    # the same binary with no plant must be clean, or the "clean run" proves nothing
    blob_n, _ = try_catch(exe, "")
    n_clean = "AddressSanitizer" not in blob_n and "runtime error" not in blob_n
    print("\n--- FORGE_PLANT unset (negative control)")
    print("  clean:", n_clean)

    ok = a_classified and u_caught and n_clean
    print("\nVERDICT:", "PASS - both sanitizers are live and the negative control is clean" if ok
          else "FAIL - the sanitizer claim would be vacuous")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
