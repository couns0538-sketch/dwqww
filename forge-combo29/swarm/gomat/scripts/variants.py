#!/usr/bin/env python3
"""Build mate-mode ABLATION variants: one compile-time switch per heuristic gate.

Every gate this touches is a place where `src/search.cpp` reads `mate_moves_` to
turn something OFF for `go mate N`. The switch is written as

    mate_moves_ == 0   ->   (GATE_<NAME> || mate_moves_ == 0)      # gate re-ENABLED when GATE_<NAME>=1
    mate_moves_ > 0    ->   (GATE_<NAME> == 0 && mate_moves_ > 0)  # block SUPPRESSED when GATE_<NAME>=1

so with `GATE_<NAME>=0` the translation unit is byte-identical to the base
commit's behaviour, and with `=1` the heuristic runs inside mate mode.

Line numbers are for commit 6b98f217. The script ASSERTS the expected source
text at each line before editing, so a moved line is an error rather than a
silent edit of the wrong gate — the failure mode findings §6 calls "a control
that cannot reach the code path it names".

Usage:
  variants.py --list
  variants.py --out /tmp/ab/NAME --gates TT,Iir
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

BASE_COMMIT = "6b98f217"
SRC = "src/search.cpp"

# name -> (line number, mode, exact expected text on that line)
GATES: dict[str, tuple[int, str, str]] = {
    "Window":  (1431, "gt0", "    if (mate_moves_ > 0) {"),
    "TTq":     (1452, "eq0", "        (mate_moves_ == 0 || (!is_mate_score(alpha) && !is_mate_score(beta))) &&"),
    "QSearchPrune": (1493, "eq0", "        if (mate_moves_ == 0 && !in_check && best_score > -MateInMaxPly) {"),
    "TTmain":  (1639, "eq0", "        (mate_moves_ == 0 || (!is_mate_score(alpha) && !is_mate_score(beta))) &&"),
    "RazorRfpNull": (1680, "eq0", "    if (!pv_node && !in_check && excluded.is_none() && !is_mate_score(beta) && mate_moves_ == 0 &&"),
    "Iir":     (1784, "eq0", "    if (mate_moves_ == 0 && !in_check && depth >= tune::IirDepth && tt_move.is_none() && (pv_node || cut_node)) --depth;"),
    "QuietExtinction": (1805, "eq0", "    const bool may_extinguish = tune::QuietExtinction && !root_node && !in_check && mate_moves_ == 0 &&"),
    "FutilityPrune": (1841, "eq0", "        if (!sound_mate_case && mate_moves_ == 0 && board.halfmove_clock() + depth < 100 && !root_node &&"),
    "SingularExt": (1929, "eq0", "        if (mate_moves_ == 0 && !root_node && depth >= tune::SingularDepth && move == tt_move && excluded.is_none() &&"),
    "CheckExt": (1955, "eq0", "        } else if (mate_moves_ == 0 && gives_check && depth >= tune::CheckExtensionDepth && !root_node &&"),
    "Lmr":     (1991, "eq0", "        if (mate_moves_ == 0 && board.halfmove_clock() + new_depth < 100 && depth >= 2 &&"),
}

# The macro name written into the source, so a build can be identified from its
# command line alone.
def macro(name: str) -> str:
    return "GATE_" + name.upper()


def patch_line(text: str, mode: str, name: str) -> str:
    m = macro(name)
    if mode == "gt0":
        assert "mate_moves_ > 0" in text, text
        return text.replace("mate_moves_ > 0", f"({m} == 0 && mate_moves_ > 0)")
    assert "mate_moves_ == 0" in text, text
    return text.replace("mate_moves_ == 0", f"({m} || mate_moves_ == 0)")


def build_variant(src_root: str, out_dir: str, enabled: list[str]) -> None:
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    shutil.copytree(os.path.join(src_root, "src"), os.path.join(out_dir, "src"))
    shutil.copytree(os.path.join(src_root, "include"), os.path.join(out_dir, "include"))
    shutil.copy2(os.path.join(src_root, "CMakeLists.txt"), out_dir)

    path = os.path.join(out_dir, "src", "search.cpp")
    with open(path) as fh:
        lines = fh.readlines()

    # Assert every expected line before editing any of them: a moved line must
    # stop the build, not silently patch the wrong gate.
    for name, (lineno, mode, expect) in GATES.items():
        got = lines[lineno - 1]
        if got.rstrip("\n") != expect:
            raise SystemExit(
                f"GATE {name}: line {lineno} of {SRC} is not what this script expects.\n"
                f"  expected: {expect!r}\n  found   : {got.rstrip()!r}\n"
                "The source moved; fix GATES before trusting any ablation result.")

    for name in enabled:
        lineno, mode, _ = GATES[name]
        lines[lineno - 1] = patch_line(lines[lineno - 1], mode, name)

    # Every gate macro gets a default of 0 at the top of the file, so a variant
    # that enables only some gates still compiles and "-DGATE_X=1" is the ONLY
    # way a gate can turn on. The defaults are #ifndef-guarded, so a -D on the
    # command line wins.
    defaults = ["// --- gate defaults injected by swarm/gomat/scripts/variants.py ---\n"]
    for n in GATES:
        defaults.append(f"#ifndef {macro(n)}\n#define {macro(n)} 0\n#endif\n")
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("#include"):
            insert_at = i + 1
    lines[insert_at:insert_at] = defaults + ["\n"]

    with open(path, "w") as fh:
        fh.writelines(lines)

    # The gate values MUST reach the compiler. Writing them only into GATES.txt
    # produced a directory of thirteen BYTE-IDENTICAL binaries, which looks like
    # a clean ablation table and is thirteen copies of the control build. The
    # defines therefore go into CMakeLists itself, where the build cannot miss
    # them, and the runner asserts each binary's sha256 differs from the control.
    defs = " ".join(f"{macro(n)}=1" for n in enabled)
    cmake_path = os.path.join(out_dir, "CMakeLists.txt")
    with open(cmake_path) as fh:
        cmake = fh.read()
    anchor = "target_compile_definitions(forge PRIVATE"
    assert anchor in cmake, "CMakeLists format changed; variants.py needs updating"
    injected = anchor + (f"\n  {defs}" if defs else "")
    cmake = cmake.replace(anchor, injected, 1)
    with open(cmake_path, "w") as fh:
        fh.write(cmake)

    with open(os.path.join(out_dir, "GATES.txt"), "w") as fh:
        fh.write(f"base commit {BASE_COMMIT}\n")
        fh.write(f"enabled gates: {', '.join(enabled) if enabled else '(none: pure mate mode)'}\n")
        fh.write(f"compile definitions: {defs or '(none)'}\n")
        for name in enabled:
            lineno, mode, expect = GATES[name]
            fh.write(f"  {name}: line {lineno} {mode}\n    was: {expect}\n"
                     f"    now: {patch_line(expect, mode, name)}\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--src", default=".")
    ap.add_argument("--out")
    ap.add_argument("--gates", default="")
    args = ap.parse_args()

    if args.list:
        for name, (lineno, mode, expect) in GATES.items():
            print(f"{name:16s} line {lineno:5d}  {mode:4s}  {expect.strip()[:80]}")
        print(f"\n{len(GATES)} gates")
        return 0

    if not args.out:
        raise SystemExit("--out is required unless --list")
    enabled = [g for g in args.gates.split(",") if g]
    unknown = [g for g in enabled if g not in GATES]
    if unknown:
        raise SystemExit(f"unknown gates: {unknown}; known: {list(GATES)}")
    build_variant(args.src, args.out, enabled)
    print(f"wrote {args.out} with gates: {enabled or '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
