#!/usr/bin/env python3
"""Planted-bug check for the pick-order oracle (S14 follow-up).

Copies src/, include/, the oracle and the root EPD into a scratch tree, plants one bug that makes the
FORGE_NOZERO_MOVE_BUFFERS=1 code read move-buffer storage it has not written, builds the oracle with the switch
on, runs it with the mutant's storage pattern, and requires that the oracle FAILS (non-zero exit) or prints a TOTAL
digest different from the reference. Also runs the unmutated copy as a control (pattern 01 and random), which must
reproduce the reference.

Mutants (each replacement must occur exactly once), with the pattern they run under:
  M1 picker_reads_past_count  MovePicker::pick_best scans one entry past count_ (src/search.cpp), pattern 01
  M2 movelist_end_past_size   MoveList::end() (non-const) ends one element past size_ (include/forge/board.hpp), 01
  M3 bad_captures_past_count  the BadCaptures stage returns one entry past bad_count_ (src/search.cpp), random
     (with a uniform byte pattern the extra entry has from == to, i.e. it reads as Move::none() and ends the list
     exactly where the real list ends, so this mutant needs the random pattern)
usage: mutation_check.py <src_root> <scratch_dir> --ref-digest HEX [--cxx g++] [--flags "..."] [--children N]
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

MUTANTS = [
    ("M1_picker_reads_past_count", "src/search.cpp",
     "for (std::size_t i = index_ + 1; i < count_; ++i) {",
     "for (std::size_t i = index_ + 1; i <= count_; ++i) {", "01"),
    ("M2_movelist_end_past_size", "include/forge/board.hpp",
     "[[nodiscard]] iterator end() { return data_.begin() + static_cast<std::ptrdiff_t>(size_); }",
     "[[nodiscard]] iterator end() { return data_.begin() + static_cast<std::ptrdiff_t>(size_ + 1); }", "01"),
    ("M3_bad_captures_past_count", "src/search.cpp",
     "if (bad_index_ < bad_count_) return bad_captures_[bad_index_++];",
     "if (bad_index_ <= bad_count_) return bad_captures_[bad_index_++];", "random"),
]
ORACLE = "opus_round1/sol_S14/followup_zerofill/picker_order_oracle.cpp"
CORE = ["bitboard", "board", "book", "eval", "eval_params", "nnue"]


def copy_tree(src_root, dst):
    if os.path.exists(dst):
        raise SystemExit(f"scratch tree {dst} exists; pass a new directory (nothing is deleted)")
    shutil.copytree(os.path.join(src_root, "src"), os.path.join(dst, "src"))
    shutil.copytree(os.path.join(src_root, "include"), os.path.join(dst, "include"))
    os.makedirs(os.path.join(dst, os.path.dirname(ORACLE)))
    shutil.copy2(os.path.join(src_root, ORACLE), os.path.join(dst, ORACLE))
    os.makedirs(os.path.join(dst, "tools", "openings"))
    shutil.copy2(os.path.join(src_root, "tools", "openings", "forge-10000.epd"),
                 os.path.join(dst, "tools", "openings", "forge-10000.epd"))


def build_and_run(tree, cxx, flags, children, tag, pattern):
    exe = os.path.join(tree, "oracle_" + tag)
    cmd = [cxx] + flags.split() + ["-DFORGE_NOZERO_MOVE_BUFFERS=1", "-I" + os.path.join(tree, "include"),
                                   os.path.join(tree, ORACLE)] + \
          [os.path.join(tree, "src", c + ".cpp") for c in CORE] + ["-pthread", "-o", exe]
    b = subprocess.run(cmd, capture_output=True, text=True)
    if b.returncode != 0:
        raise SystemExit(f"{tag}: build failed\n{b.stderr[-3000:]}")
    r = subprocess.run([exe, os.path.join(tree, "tools", "openings", "forge-10000.epd"), pattern, "--children", str(children)],
                       capture_output=True, text=True)
    m = re.search(r"^TOTAL .* digest ([0-9a-f]+)$", r.stdout, re.M)
    return r.returncode, (m.group(1) if m else None), r.stderr.strip()[-400:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src_root")
    ap.add_argument("scratch")
    ap.add_argument("--ref-digest", required=True)
    ap.add_argument("--cxx", default="g++")
    ap.add_argument("--flags", default="-std=c++20 -O3 -g -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math "
                                        "-fno-lifetime-dse -march=x86-64-v3 -mtune=znver5")
    ap.add_argument("--children", type=int, default=2000)
    a = ap.parse_args()
    os.makedirs(a.scratch, exist_ok=True)
    ok = True
    control = os.path.join(a.scratch, "control")
    copy_tree(a.src_root, control)
    for pattern in ("01", "random"):
        rc, digest, err = build_and_run(control, a.cxx, a.flags, a.children, "control", pattern)
        good = rc == 0 and digest == a.ref_digest
        ok &= good
        print(f"control (unmutated copy, pattern {pattern}): exit {rc} digest {digest} -> "
              f"{'reproduces the reference' if good else 'FAIL: differs'}")
    for name, rel, old, new, pattern in MUTANTS:
        tree = os.path.join(a.scratch, name)
        copy_tree(a.src_root, tree)
        path = os.path.join(tree, rel)
        text = open(path, encoding="utf-8").read()
        if text.count(old) != 1:
            raise SystemExit(f"{name}: pattern occurs {text.count(old)} times in {rel}")
        with open(path, "w", encoding="utf-8", newline="\n") as out:
            out.write(text.replace(old, new))
        rc, digest, err = build_and_run(tree, a.cxx, a.flags, a.children, name, pattern)
        caught = rc != 0 or digest != a.ref_digest
        ok &= caught
        detail = f"exit {rc}" + (f", stderr: {err}" if err else "") + f", digest {digest}"
        print(f"{name} (pattern {pattern}): {'CAUGHT' if caught else 'MISSED'} ({detail})")
    print("mutation check:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
