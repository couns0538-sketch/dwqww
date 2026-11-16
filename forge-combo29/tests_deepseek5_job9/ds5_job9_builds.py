#!/usr/bin/env python3
"""job9 Part A: build the P/A/S variants of the TSan tree from the clean source."""
import shutil
import subprocess
import os

CLEAN = "/tmp/ds5_tsan"
APPLY = "apply_history"  # the function whose body gets the counter/plant

def plant_plain(path):
    t = open(path, encoding="utf-8").read()
    anchor = "void apply_history(std::int16_t& entry, int bonus) {"
    i = t.index(anchor); j = t.index("\n", i) + 1
    t = t[:j] + "    ++pl_hist_upd;\n" + t[j:]
    anchor2 = "void Worker::update_correction(const Board& board, int depth, int best_score, int static_eval) {"
    i = t.index(anchor2); j = t.index("\n", i) + 1
    t = t[:j] + "    ++pl_corr_upd;\n" + t[j:]
    first = t.index("namespace forge {")
    decls = ("namespace forge {\nint pl_hist_upd = 0;\nint pl_corr_upd = 0;\n")
    t = t[:first] + decls + t[first + len("namespace forge {\n"):]
    open(path, "w").write(t)

def plant_atomic(path):
    t = open(path, encoding="utf-8").read()
    anchor = "void apply_history(std::int16_t& entry, int bonus) {"
    i = t.index(anchor); j = t.index("\n", i) + 1
    t = t[:j] + "    pl_hist_upd.fetch_add(1, std::memory_order_relaxed);\n" + t[j:]
    anchor2 = "void Worker::update_correction(const Board& board, int depth, int best_score, int static_eval) {"
    i = t.index(anchor2); j = t.index("\n", i) + 1
    t = t[:j] + "    pl_corr_upd.fetch_add(1, std::memory_order_relaxed);\n" + t[j:]
    first = t.index("namespace forge {")
    decls = ("namespace forge {\n#include <atomic>\nstd::atomic<int> pl_hist_upd{0};\nstd::atomic<int> pl_corr_upd{0};\n")
    t = t[:first] + decls + t[first + len("namespace forge {\n"):]
    open(path, "w").write(t)

def plant_shared(path):
    plant_atomic(path)
    t = open(path, encoding="utf-8").read()
    # the TRUE shared write: apply_history ALSO applies the bonus to one static entry
    anchor = "void apply_history(std::int16_t& entry, int bonus) {"
    i = t.index(anchor); j = t.index("\n", i) + 1
    t = t[:j] + "    shared_plant_entry = static_cast<std::int16_t>(shared_plant_entry + bonus);\n" + t[j:]
    t = t.replace("std::atomic<int> pl_hist_upd{0};",
                  "std::atomic<int> pl_hist_upd{0};\nstatic std::int16_t shared_plant_entry = 0;  // job9 S: the planted TRUE shared write")
    open(path, "w").write(t)

def build(src, name):
    dst = f"/tmp/ds5_j9_{name}"
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    shutil.rmtree(f"{dst}/build", ignore_errors=True)
    if name == "P":
        plant_plain(f"{dst}/src/search.cpp")
    elif name == "A":
        plant_atomic(f"{dst}/src/search.cpp")
    elif name == "S":
        plant_shared(f"{dst}/src/search.cpp")
    r = subprocess.run(["cmake", "-S", dst, "-B", f"{dst}/build", "-DCMAKE_BUILD_TYPE=Release",
                        "-DCMAKE_CXX_COMPILER=/usr/bin/g++",
                        "-DCMAKE_CXX_FLAGS=-DFORGE_NNUE_HIDDEN=256 -fsanitize=thread -fno-omit-frame-pointer -g",
                        "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(name, "CONFIG FAIL", r.stderr[-300:]); return False
    r = subprocess.run(["cmake", "--build", f"{dst}/build", "--target", "forge", "-j4"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(name, "BUILD FAIL", r.stdout[-500:], r.stderr[-500:]); return False
    print(name, "BUILD OK")
    return True

if __name__ == "__main__":
    for name in ("P", "A", "S"):
        build(CLEAN, name)
