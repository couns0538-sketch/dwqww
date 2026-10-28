#!/usr/bin/env python3
"""R3-5 planted-bug check (forge-engine-verify section 4): each mutant changes one line of the engine; the new
regression test that guards that rule must FAIL on it (and pass on the unmodified source).

usage: mutation_check.py <worktree> <scratch_dir> [--only name,...] [--timeout S]
  <scratch_dir> gets one fresh folder per run (never reused, nothing is deleted):
    base/      objects of the unmodified sources and the test programs
    <mutant>/  src + include copy with the one-line patch, the recompiled object, the linked test programs
Compiler: MSYS2 ucrt64 g++ with the CMake Release flags of cmake_build.sh (-O3 -march=x86-64-v3 -mtune=znver5,
no FMA contraction, static). Run under `nice -n 19` (children inherit the priority).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

GPP = "C:/msys64/ucrt64/bin/g++.exe"
FLAGS = ["-std=c++20", "-O3", "-DNDEBUG", "-march=x86-64-v3", "-mtune=znver5", "-fno-fast-math", "-ffp-contract=off",
         "-DFORGE_NNUE_HIDDEN=256"]
CORE = ["bitboard", "board", "book", "datagen", "eval", "eval_params", "nnue", "search"]  # forge_core (CMakeLists.txt)
TESTS = {"perft": "perft_suite_tests", "draw": "draw_rules_tests", "ttmate": "tt_mate_tb_tests"}

# name: (file, old, new, what the bug does, test runs that must fail)
MUTANTS = {
    "P1_ep_capture_not_removed": (
        "src/board.cpp",
        "    if ((move.flags & EnPassant) != 0U) captured_square = move.to - pawn_push_delta(us);\n    Bitboard removed = 0;",
        "    Bitboard removed = 0;",
        "is_legal: the pawn taken en passant stays on the board (rank pins through both pawns are missed)",
        ["perft_cpw", "perft_edge"]),
    "P2_castle_through_attacked_f1": (
        "src/board.cpp",
        "                piece_at(7) == WR && !square_attacked(5, Black) && !square_attacked(6, Black)) {\n                push(4, 6, KingCastle);",
        "                piece_at(7) == WR && !square_attacked(6, Black)) {\n                push(4, 6, KingCastle);",
        "move generation: white may castle short through an attacked f1",
        ["perft_cpw", "perft_edge"]),
    "R1_no_twofold_in_search": (
        "src/board.cpp",
        "            if (i >= static_cast<std::ptrdiff_t>(root_index)) return true;\n",
        "",
        "is_repetition(root): a repetition after the root needs a third occurrence too",
        ["draw"]),
    "R2_history_needs_three": (
        "src/board.cpp",
        "            if (++count >= 2) return true;",
        "            if (++count >= 3) return true;",
        "is_repetition(root): positions before the root need three earlier occurrences (fourfold)",
        ["draw"]),
    "R3_mate_on_100_is_draw": (
        "src/search/checks.inc",
        "        return !board.in_check() || board.has_legal_move();",
        "        return true;",
        "is_draw: a checkmate delivered on the 100th half-move counts as a draw",
        ["draw"]),
    "R4_capture_keeps_clock": (
        "src/board.cpp",
        "    if (undo.captured != Empty || piece_type(moving) == Pawn) halfmove_ = 0;",
        "    if (piece_type(moving) == Pawn) halfmove_ = 0;",
        "make_move: captures do not reset the 50-move counter",
        ["draw"]),
    "R5_no_claim_in_qsearch": (
        "src/search/qsearch.inc",
        "    const bool claim = options::intended_threefold && board.can_claim_threefold_by_next_move();",
        "    const bool claim = false;",
        "qsearch: IntendedThreefold never floors at the draw score (issue #7 regression)",
        ["draw"]),
    "M1_mate_stored_without_ply": (
        "src/search/scores.inc",
        "    if (score >= syzygy::TbWinInMaxPly) return score >= MateInMaxPly || syzygy::tb_scores ? score + ply : score;",
        "    if (score >= syzygy::TbWinInMaxPly) return score;",
        "score_to_tt: winning mate scores are stored relative to the root, not the node",
        ["ttmate"]),
    "M2_mate_read_without_ply": (
        "src/search/scores.inc",
        "    if (score >= syzygy::TbWinInMaxPly) return score >= MateInMaxPly || syzygy::tb_scores ? score - ply : score;",
        "    if (score >= syzygy::TbWinInMaxPly) return score;",
        "score_from_tt: winning mate scores are read back without the node's ply",
        ["ttmate"]),
    "M3_mated_read_without_ply": (
        "src/search/scores.inc",
        "    if (score <= -syzygy::TbWinInMaxPly) return score <= -MateInMaxPly || syzygy::tb_scores ? score + ply : score;",
        "    if (score <= -syzygy::TbWinInMaxPly) return score;",
        "score_from_tt: losing mate scores are read back without the node's ply",
        ["ttmate"]),
    "O1_corrhistplus_clamp_8": (
        "src/uci.cpp",
        "forge::options::corr_hist_plus = static_cast<std::uint8_t>(std::clamp(value, 0, 7));",
        "forge::options::corr_hist_plus = static_cast<std::uint8_t>(std::clamp(value, 0, 8));",
        "setoption CorrHistPlus clamps to 8 instead of the advertised max 7",
        ["options"]),
    "O2_hash_invalid_silent": (
        "src/uci.cpp",
        "                    { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << \"info string invalid value for option \" << name << std::endl; }",
        "                    {}",
        "setoption Hash / Threads / Move Overhead: a non-integer value is ignored silently",
        ["options"]),
}


def log(message: str):
    print(time.strftime("%H:%M:%S"), message, flush=True)


def compile_object(root: Path, source: Path, obj: Path, extra: list[str]):
    obj.parent.mkdir(parents=True, exist_ok=True)
    cmd = [GPP, *FLAGS, f"-I{root / 'include'}", *extra, "-c", str(source), "-o", str(obj)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"compile failed: {source}\n{result.stderr[-4000:]}")


def link(objects: list[Path], exe: Path):
    cmd = [GPP, *[str(o) for o in objects], "-static", "-pthread", "-o", str(exe)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"link failed: {exe}\n{result.stderr[-4000:]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("worktree", type=Path)
    parser.add_argument("scratch", type=Path)
    parser.add_argument("--only", default="")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--python", default=sys.executable, help="interpreter for the UCI test scripts")
    args = parser.parse_args()
    os.environ["PATH"] = "C:/msys64/ucrt64/bin;" + os.environ["PATH"]
    tree = args.worktree.resolve()
    run_dir = args.scratch / time.strftime("run_%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True)
    only = {name for name in args.only.split(",") if name}
    selected = {name: m for name, m in MUTANTS.items() if not only or name in only}

    # Baseline objects (the unmodified worktree) and the test programs' objects.
    base = run_dir / "base"
    log(f"baseline objects in {base}")
    for name in CORE + ["uci"]:
        compile_object(tree, tree / "src" / f"{name}.cpp", base / f"{name}.o", [])
    for key, test in TESTS.items():
        compile_object(tree, tree / "tests" / f"{test}.cpp", base / f"{test}.o", [])

    tsv = tree / "tests" / "data" / "perft_suite.tsv"
    reference = tree / "tests" / "syzygy_reference.tsv"

    def runs_for(exe_dir: Path):
        return {
            "perft_cpw": [str(exe_dir / "perft_suite_tests.exe"), str(tsv), "--group", "cpw", "--max-depth", "5"],
            "perft_edge": [str(exe_dir / "perft_suite_tests.exe"), str(tsv), "--group", "edge", "--max-depth", "5"],
            "draw": [str(exe_dir / "draw_rules_tests.exe")],
            "ttmate": [str(exe_dir / "tt_mate_tb_tests.exe"), str(reference)],
            "options": [args.python, "-I", "-B", str(tree / "tools" / "uci_options_regression.py"),
                        str(exe_dir / "forge.exe"), "--workdir", str(exe_dir / "work")],
        }

    def build(exe_dir: Path, objects: dict[str, Path], needed: set[str]):
        core = [objects[name] for name in CORE]
        exe_dir.mkdir(parents=True, exist_ok=True)
        for key, test in TESTS.items():
            if any(run.startswith(key) for run in needed):
                link([base / f"{test}.o", *core], exe_dir / f"{test}.exe")
        if "options" in needed:
            link([objects["uci"], *core], exe_dir / "forge.exe")

    def execute(cmd: list[str], logfile: Path) -> tuple[int, list[str]]:
        start = time.monotonic()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout)
            code, output = result.returncode, result.stdout + result.stderr
        except subprocess.TimeoutExpired as error:
            code = "timeout"
            output = (error.stdout or b"").decode(errors="replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        logfile.write_text(output, encoding="utf-8", errors="replace")
        fails = [line for line in output.splitlines() if line.startswith("FAIL") or "AssertionError" in line
                 or "Error" in line][:6]
        return code, fails + [f"({time.monotonic() - start:.1f} s)"]

    results = {}
    needed_all = set()
    for name, (_, _, _, _, runs) in selected.items():
        needed_all.update(runs)
    # Control: the unmodified sources pass every test run used below.
    control_dir = run_dir / "control"
    build(control_dir, {name: base / f"{name}.o" for name in CORE + ["uci"]}, needed_all)
    for run in sorted(needed_all):
        code, fails = execute(runs_for(control_dir)[run], control_dir / f"{run}.log")
        results[f"control {run}"] = {"exit": code, "notes": fails, "ok": code == 0}
        log(f"control {run}: exit {code} {fails[-1]}")

    for name, (file, old, new, what, runs) in selected.items():
        folder = run_dir / name
        for part in ("src", "include"):
            shutil.copytree(tree / part, folder / part)
        target = folder / file
        text = target.read_bytes().decode("utf-8")
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"{name}: pattern occurs {count} times in {file}")
        target.write_bytes(text.replace(old, new).encode("utf-8"))
        unit = "search" if file.startswith("src/search/") else Path(file).stem
        objects = {n: base / f"{n}.o" for n in CORE + ["uci"]}
        objects[unit] = folder / "obj" / f"{unit}.o"
        compile_object(folder, folder / "src" / f"{unit}.cpp", objects[unit], [f"-I{folder / 'src'}"])
        build(folder / "bin", objects, set(runs))
        for run in runs:
            code, fails = execute(runs_for(folder / "bin")[run], folder / f"{run}.log")
            killed = code != 0
            results[f"{name} {run}"] = {"bug": what, "file": file, "exit": code, "notes": fails, "killed": killed}
            log(f"{name} {run}: {'KILLED' if killed else 'SURVIVED'} (exit {code}) {fails[:3]}")
    summary = run_dir / "mutation_results.json"
    summary.write_text(json.dumps(results, indent=2), encoding="utf-8")
    controls_ok = all(v.get("ok", True) for k, v in results.items() if k.startswith("control"))
    killed = [k for k, v in results.items() if not k.startswith("control") and v["killed"]]
    survived = [k for k, v in results.items() if not k.startswith("control") and not v["killed"]]
    log(f"controls pass: {controls_ok}; killed {len(killed)}; survived {len(survived)}: {survived}")
    log(f"results: {summary}")
    return 0 if controls_ok and not survived else 1


if __name__ == "__main__":
    sys.exit(main())
