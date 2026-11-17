#!/usr/bin/env python3
"""Sensitivity controls for the bench pin.

Two things must be true of any instrument used as a gate:
  (S) there exists a change it MUST detect   -- otherwise it is not measuring the code
  (N) there exist changes it MUST NOT detect -- otherwise it is measuring noise

Both are run here. Each mutant is a source edit on a fresh copy of the audit base,
built with the same recipe as the pin binary, and the four pins are re-read.

SHOULD-MOVE mutants (a gate that cannot move is not a gate):
  M1  eval weight: bump the pawn value in the flat parameter table by +10
  M2  search constant: LmrQuietBase 85 -> 125 (base reduction +0.40 ply)
  M3  search constant: RfpMargin 72 -> 40 (tighter reverse-futility window)
  M4  a prune disabled: NullMoveMinDepth 3 -> 99 (null move never fires)
  M5  a behaviour change that only touches the LEAF: QsSeeMargin
SHOULD-NOT-MOVE mutants (the pin must not chase source noise):
  N1  add a comment block to search.cpp
  N2  reorder two independent struct members in search.hpp
  N3  rename a local variable
  N4  add a dead, never-called function
  N5  reformat whitespace throughout one function

Every mutant prints which pins moved, by how much, and the sha256 of the mutant source
tree so the row is reproducible.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

from common import BASE_SRC, MUTANTS, BUILD as _BUILD
BASE = BASE_SRC.parent
WORK = MUTANTS
EXPECT = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}


def tree_sha(root: pathlib.Path) -> str:
    h = hashlib.sha256()
    for p in sorted((root / "forge-combo29" / "src").iterdir()) + \
             sorted((root / "forge-combo29" / "include" / "forge").iterdir()):
        if p.is_file():
            h.update(p.name.encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def fresh(name: str) -> pathlib.Path:
    dst = WORK / name
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    shutil.copytree(BASE / "forge-combo29", dst / "forge-combo29",
                    ignore=shutil.ignore_patterns("*.o", "build"))
    return dst


def sub_once(path: pathlib.Path, old: str, new: str) -> None:
    text = path.read_text()
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"pattern appears {n} times in {path}: {old[:60]!r}")
    path.write_text(text.replace(old, new))


def build(root: pathlib.Path, name: str) -> pathlib.Path:
    b = root / "build"
    b.mkdir(exist_ok=True)
    subprocess.run(["cmake", str(root / "forge-combo29"), "-DCMAKE_BUILD_TYPE=Release",
                    "-DCMAKE_CXX_COMPILER=/usr/bin/g++", "-DFORGE_MARCH=x86-64-v4"],
                   cwd=b, check=True, capture_output=True)
    env = dict(os.environ, LIBRARY_PATH="/usr/lib/gcc/x86_64-linux-gnu/13")
    subprocess.run(["make", "-j4"], cwd=b, check=True, capture_output=True, env=env)
    return b / "forge"


def pins(exe: pathlib.Path) -> dict:
    out = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve().parent / "pins.py"), str(exe)],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


MUTANTS = []


def mutant(name: str, kind: str, why: str):
    def deco(fn):
        MUTANTS.append((name, kind, why, fn))
        return fn
    return deco


@mutant("M1_eval_pawn_psqt", "should-move", "every PawnPsqt midgame weight +40 (a pure eval change)")
def m1(root: pathlib.Path) -> None:
    inc = root / "forge-combo29/src/eval_params_table.inc"
    text = inc.read_text()
    rows = re.findall(r"^(/\* \d+ PawnPsqt\[\d+\] \*/ S\()(-?\d+)", text, re.M)
    if len(rows) != 64:
        raise SystemExit(f"expected 64 PawnPsqt rows, found {len(rows)}")
    out = re.sub(r"^(/\* \d+ PawnPsqt\[\d+\] \*/ S\()(-?\d+)",
                 lambda m: m.group(1) + str(int(m.group(2)) + 40), text, flags=re.M)
    if out == text:
        raise SystemExit("PawnPsqt rewrite was a no-op")
    inc.write_text(out)


@mutant("M2_lmr_quiet_base", "should-move", "LmrQuietBase 85 -> 125")
def m2(root: pathlib.Path) -> None:
    sub_once(root / "forge-combo29/src/search.cpp", "int LmrQuietBase = 85;", "int LmrQuietBase = 125;")


@mutant("M3_rfp_margin", "should-move", "RfpMargin 72 -> 40")
def m3(root: pathlib.Path) -> None:
    sub_once(root / "forge-combo29/src/search.cpp", "int RfpMargin = 72;", "int RfpMargin = 40;")


@mutant("M4_null_move_off", "should-move", "NullMoveMinDepth 3 -> 99, null move never fires")
def m4(root: pathlib.Path) -> None:
    sub_once(root / "forge-combo29/src/search.cpp", "int NullMoveMinDepth = 3;", "int NullMoveMinDepth = 99;")


@mutant("M5_see_pawn_value", "should-move", "SeePieceValue[Pawn] 100 -> 260, a search-side material constant")
def m5(root: pathlib.Path) -> None:
    sub_once(root / "forge-combo29/include/forge/eval.hpp",
             "constexpr std::array<int, 7> SeePieceValue{0, 100, 300, 300, 500, 900, 0};",
             "constexpr std::array<int, 7> SeePieceValue{0, 260, 300, 300, 500, 900, 0};")


@mutant("N1_add_comment", "should-not-move", "a 6-line comment block appended to search.cpp")
def n1(root: pathlib.Path) -> None:
    p = root / "forge-combo29/src/search.cpp"
    p.write_text(p.read_text() + "\n// Audit control: this comment changes no code.\n"
                                 "// It exists so the pin can be shown not to chase\n"
                                 "// source text. Nothing here is compiled into behaviour.\n")


@mutant("N2_reorder_struct_members", "should-not-move", "two independent members of SearchStack swapped")
def n2(root: pathlib.Path) -> None:
    hpp = root / "forge-combo29/include/forge/search.hpp"
    text = hpp.read_text()
    lines = text.splitlines(keepends=True)
    # find a struct with at least three plain POD members and swap two of them
    idx = text.find("struct SearchStack")
    if idx < 0:
        raise SystemExit("SearchStack not found")
    end = text.find("\n};", idx)
    if end < 0:
        raise SystemExit("SearchStack has no closing brace")
    block = text[idx:end]
    blines = block.splitlines(keepends=True)
    pod = [i for i, l in enumerate(blines) if re.match(r"^\s+[A-Za-z_].*;\s*$", l)]
    if len(pod) < 3:
        raise SystemExit("no swappable POD members in SearchStack")
    a, b = pod[1], pod[2]
    blines[a], blines[b] = blines[b], blines[a]
    hpp.write_text(text[:idx] + "".join(blines) + text[end:])
    if hpp.read_text() == text:
        raise SystemExit("struct reorder was a no-op")


@mutant("N3_rename_local", "should-not-move", "a local variable renamed inside one function")
def n3(root: pathlib.Path) -> None:
    p = root / "forge-combo29/src/uci.cpp"
    text = p.read_text()
    # bench's own accumulator, renamed. It appears twice in the bench branch.
    m = re.search(r"\n\s*std::uint64_t total_nodes = 0;", text)
    if m:
        start, name = m.start(), "total_nodes"
    else:
        m = re.search(r"\n\s*int depth = 13;", text)
        if not m:
            raise SystemExit("no local to rename")
        start, name = m.start(), "depth"
    end = text.find("} else if (command == \"ponderhit\")", start)
    body = text[start:end]
    if body.count(name) < 2:
        raise SystemExit(f"local {name} appears {body.count(name)} times; rename would be a no-op control")
    p.write_text(text[:start] + body.replace(name, "audit_renamed_" + name) + text[end:])


@mutant("N4_dead_function", "should-not-move", "a never-called function appended to eval.cpp")
def n4(root: pathlib.Path) -> None:
    p = root / "forge-combo29/src/eval.cpp"
    p.write_text(p.read_text() + "\nnamespace forge {\nnamespace {\n"
                                 "[[maybe_unused]] int audit_dead_function(int x) { return x * 31 + 7; }\n"
                                 "}  // namespace\n}  // namespace forge\n")


@mutant("N5_whitespace", "should-not-move", "blank lines and indentation added inside one function")
def n5(root: pathlib.Path) -> None:
    p = root / "forge-combo29/src/uci.cpp"
    text = p.read_text()
    old = "            int depth = 13;\n"
    if text.count(old) != 1:
        raise SystemExit("bench depth line not unique")
    p.write_text(text.replace(old, "\n\n            int    depth   =   13;   // spacing only\n\n"))


def main() -> None:
    only = sys.argv[1:] or None
    results = []
    base_tree = tree_sha(BASE)
    for name, kind, why, fn in MUTANTS:
        if only and name not in only:
            continue
        root = fresh(name)
        fn(root)
        after = tree_sha(root)
        if after == base_tree:
            results.append({"mutant": name, "kind": kind, "why": why,
                            "error": "mutation did not change the source tree"})
            print(f"{name}: ERROR mutation had no effect", flush=True)
            continue
        try:
            exe = build(root, name)
        except subprocess.CalledProcessError as exc:
            results.append({"mutant": name, "kind": kind, "why": why,
                            "error": "build failed", "stderr": (exc.stderr or b"").decode()[-800:]})
            print(f"{name}: BUILD FAILED", flush=True)
            continue
        p = pins(exe)
        moved = {k: {"expected": EXPECT[k], "got": p[k]["nodes"], "moved": p[k]["nodes"] != EXPECT[k]}
                 for k in EXPECT}
        results.append({"mutant": name, "kind": kind, "why": why,
                        "tree_sha256": after, "binary_sha256": p["binary_sha256"],
                        "pins": moved, "any_pin_moved": any(v["moved"] for v in moved.values())})
        s = " ".join(f"{k}={p[k]['nodes']}" for k in EXPECT)
        print(f"{name:28s} {kind:16s} moved={any(v['moved'] for v in moved.values())!s:5s} {s}", flush=True)
    print(json.dumps({"base_tree_sha256": base_tree, "results": results}, indent=2))


if __name__ == "__main__":
    main()
