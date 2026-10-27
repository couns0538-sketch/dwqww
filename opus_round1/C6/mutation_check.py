#!/usr/bin/env python3
"""Plant one bug at a time in a scratch copy of the tree and check that forge_cuckoo_tests fails.

usage: mutation_check.py <repo_root> <scratch_dir> [cmake configure args...]
Needs cmake, ninja and a C++20 compiler on PATH. Builds with -j 1 (only the test target).
The test's last output line starts with FAIL when any check fails (= mutation caught).
"""
import pathlib
import shutil
import subprocess
import sys

MUTATIONS = [
    # name, file, old, new
    ("clock_window_off_by_one", "src/board.cpp",
     "std::min<std::size_t>(static_cast<std::size_t>(halfmove_) + 1, 65535)",
     "std::min<std::size_t>(static_cast<std::size_t>(halfmove_), 65535)"),
    ("null_window_ignored", "src/board.cpp",
     "const std::size_t span = std::min(std::min(clock, since_null), size);",
     "const std::size_t span = std::min(clock, size);"),
    ("null_window_off_by_one", "src/board.cpp",
     "std::min<std::size_t>(static_cast<std::size_t>(plies_from_null_) + 1, 1024)",
     "std::min<std::size_t>(static_cast<std::size_t>(plies_from_null_), 1024)"),
    ("pre_root_single_occurrence_counts", "src/board.cpp",
     "if (now - distance >= root_index) return true;",
     "return true;"),
    ("pre_root_second_occurrence_ignored", "src/board.cpp",
     "if (keys[now - further] == earlier) return true;",
     "if (false && keys[now - further] == earlier) return true;"),
    ("path_check_removed", "src/board.cpp",
     "(attacks::between(from, to) & occupied()) != 0) {",
     "false) {"),
    ("second_cuckoo_slot_not_probed", "src/board.cpp",
     "    slot = cuckoo_slot_high(key);\n    if (CuckooMoves.keys[slot] == key) return &CuckooMoves.moves[slot];\n",
     ""),
    ("move_key_without_side", "src/board.cpp",
     "return piece_key(a, static_cast<Piece>(piece)) ^ piece_key(b, static_cast<Piece>(piece)) ^ Z.side;",
     "return piece_key(a, static_cast<Piece>(piece)) ^ piece_key(b, static_cast<Piece>(piece));"),
    ("opponent_filter_and_colour_check_removed", "src/board.cpp",
     "        if (opponent != 0) continue;\n",
     "        (void)opponent;\n",
     "        if (color_of(piece) != side_) continue;\n",
     ""),
    ("search_bound_disabled", "src/search/cuckoo.inc",
     "if (depth > 0 && alpha < DrawScore",
     "if (false && depth > 0 && alpha < DrawScore"),
    ("qsearch_bound_disabled", "src/search/cuckoo.inc",
     "if (alpha < DrawScore && may_repeat(board)",
     "if (false && alpha < DrawScore && may_repeat(board)"),
    ("clock_pretest_off_by_one", "src/search/cuckoo.inc",
     "return board.halfmove_clock() >= 3;",
     "return board.halfmove_clock() >= 4;"),
    ("search_floor_removed", "src/search/cuckoo.inc",
     "return std::max(search_cuckoo_body(board, ss, depth, DrawScore, beta, cut_node), DrawScore);",
     "return search_cuckoo_body(board, ss, depth, DrawScore, beta, cut_node);"),
    ("qsearch_floor_removed", "src/search/cuckoo.inc",
     "return std::max(qsearch_cuckoo_body(board, ss, DrawScore, beta), DrawScore);",
     "return qsearch_cuckoo_body(board, ss, DrawScore, beta);"),
    ("root_dispatch_ignores_option", "src/search/iterative.inc",
     "iteration_score = options::cuckoo_rep ? search_cuckoo(board, ss, depth, alpha, beta, false)",
     "iteration_score = false ? search_cuckoo(board, ss, depth, alpha, beta, false)"),
]


def main():
    root = pathlib.Path(sys.argv[1]).resolve()
    scratch = pathlib.Path(sys.argv[2]).resolve()
    extra = sys.argv[3:]
    src = scratch / "src_copy"
    build = scratch / "build"
    scratch.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        shutil.copytree(root, src, ignore=shutil.ignore_patterns(".git", "opus_round1", "__pycache__"))
    configure = ["cmake", "-S", str(src), "-B", str(build), "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release",
                 "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"] + extra
    with open(scratch / "configure.log", "w") as log:
        subprocess.run(configure, stdout=log, stderr=subprocess.STDOUT, check=True)
    exe = build / ("forge_cuckoo_tests.exe" if sys.platform == "win32" else "forge_cuckoo_tests")

    def build_and_run(tag):
        with open(scratch / f"build_{tag}.log", "w") as log:
            ok = subprocess.run(["cmake", "--build", str(build), "--target", "forge_cuckoo_tests", "-j", "1"],
                                stdout=log, stderr=subprocess.STDOUT).returncode == 0
        if not ok:
            return None
        out = subprocess.run([str(exe)], capture_output=True, text=True).stdout.strip().splitlines()
        return out[-1] if out else ""

    status = 0
    baseline = build_and_run("baseline")
    print(f"BASELINE -> {baseline}", flush=True)
    if not baseline or not baseline.startswith("PASS"):
        print("baseline does not pass; aborting")
        return 1
    for mutation in MUTATIONS:
        name, rel = mutation[0], mutation[1]
        pairs = list(zip(mutation[2::2], mutation[3::2]))
        path = src / rel
        original = path.read_text(encoding="utf-8")
        text = original
        missing = False
        for old, new in pairs:
            if text.count(old) != 1:
                missing = True
                break
            text = text.replace(old, new, 1)
        if missing:
            print(f"MUTATION {name}: pattern not found")
            status = 1
            continue
        path.write_text(text, encoding="utf-8", newline="\n")
        try:
            last = build_and_run(name)
        finally:
            path.write_text(original, encoding="utf-8", newline="\n")
        if last is None:
            print(f"MUTATION {name}: build failed (see build_{name}.log)")
            status = 1
        elif last.startswith("FAIL"):
            print(f"MUTATION {name} -> caught ({last})", flush=True)
        else:
            print(f"MUTATION {name} -> NOT caught ({last})", flush=True)
            status = 1
    print(f"mutation_check status={status}")
    return status


if __name__ == "__main__":
    sys.exit(main())
