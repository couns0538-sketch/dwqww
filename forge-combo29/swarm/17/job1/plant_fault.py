#!/usr/bin/env python3
"""Build a scratch copy of the engine with ONE planted fault, for the sanitizer proof.

usage: plant_fault.py <src_tree> <dst_tree> <fault>

fault = asan_override  : a heap over-read behind the `bench` command (depth read past an array end)
fault = ubsan_override : a signed integer overflow behind `go depth 2`
fault = none           : a plain copy (control)

The copy is source only (no build dirs). The planted lines are marked PLANTED so they are
easy to find, and the copy is NEVER committed: it lives outside the repository.
"""
import os
import shutil
import sys

PLANT_HEADER = "// PLANTED FAULT (seat 17 sanitizer proof): "

ASAN_SNIPPET = r'''
// PLANTED FAULT (seat 17 sanitizer proof): heap over-read driven by a special FEN.
namespace planted_fault {
inline int read_past_end() {
    int* heap = new int[4];
    for (int i = 0; i < 4; ++i) heap[i] = i;
    // Read one element past the allocation: ASan must report heap-buffer-overflow.
    const int stolen = heap[4];
    delete[] heap;
    return stolen;
}
} // namespace planted_fault
'''

UBSAN_SNIPPET = r'''
// PLANTED FAULT (seat 17 sanitizer proof): signed overflow driven by a special `go depth`.
// volatile keeps the compiler from folding the arithmetic away at -O3.
namespace planted_fault {
inline int overflow_on(int depth) {
    volatile int value = 2147483000;
    for (volatile int i = 0; i < depth * 1000; ++i) value = value + 1000;
    return value;
}
} // namespace planted_fault
'''


def copy_tree(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("build*", ".git", "*.o", "*.a"))


def find_main_source(root):
    for name in ("src/uci.cpp",):
        path = os.path.join(root, name)
        if os.path.exists(path):
            return path
    raise SystemExit("no src/uci.cpp in %s" % root)


def plant(root, fault):
    src = find_main_source(root)
    text = open(src).read()
    if fault == "asan_override":
        snippet = ASAN_SNIPPET
        # Call it at the top of the bench block, so running `bench` triggers it once.
        marker = '} else if (command == "bench") {\n'
        pos = text.find(marker)
        if pos < 0:
            raise SystemExit("no bench block found")
        insert_at = pos + len(marker)
        hook = (
            "            // PLANTED FAULT hook (runs once per bench command)\n"
            '            fprintf(stderr, "planted value %d\\n", planted_fault::read_past_end());\n'
        )
        text = text[:insert_at] + hook + text[insert_at:]
        text = text.replace("namespace forge {", snippet + "\nnamespace forge {", 1)
        if "#include <cstdio>" not in text:
            text = text.replace("#include <iostream>", "#include <cstdio>\n#include <iostream>", 1)
        print("planted asan fault (%s)" % src)
    elif fault == "ubsan_override":
        snippet = UBSAN_SNIPPET
        marker = '} else if (command == "go") {\n'
        pos = text.find(marker)
        if pos < 0:
            raise SystemExit("no go block found")
        insert_at = pos + len(marker)
        hook = (
            "            // PLANTED FAULT hook (runs once per go command)\n"
            "            if (planted_fault::overflow_on(2) < 0) { }\n"
        )
        text = text[:insert_at] + hook + text[insert_at:]
        text = text.replace("namespace forge {", snippet + "\nnamespace forge {", 1)
        print("planted ubsan fault (%s)" % src)
    elif fault == "none":
        print("plain copy, no fault planted")
    else:
        raise SystemExit("unknown fault %s" % fault)
    open(src, "w").write(text)


def main():
    src, dst, fault = sys.argv[1:4]
    copy_tree(src, dst)
    plant(dst, fault)
    print("wrote %s" % dst)


if __name__ == "__main__":
    main()
