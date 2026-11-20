#!/usr/bin/env python3
"""
Job 38 Part B (`run_partB.py`):
Five twin pairs:
  - B1  (030, 080)
  - S32 (024, 074)
  - K4  (043, 093)
  - B8  (028, 078)
  - S13 (016, 066)
For each seat:
  1) Fresh worktree of `6b98f217`, `git apply --check`, `git apply`, Release build (`g++`).
  2) Four no-option honesty numbers (`bench 11`, `bench 13`, `bench 16`, `go perft 5`).
  3) With `S14`:
     - switch off = `O` rows (`<seat>_off_O_d12.nodes.txt` + `.meta`), verified position-by-position vs `exe B` (`0/200` differ).
     - switch on  = `O` rows (`<seat>_on_O_d12.nodes.txt` + `.meta`), compared position-by-position vs the seat's own committed switch-on `O` rows.
  4) Per twin pair: side-by-side sums, positions differing between twins, and if different, the first three differing positions (1-based index, FEN, twin A nodes, twin B nodes, base nodes).
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j38_harness import (
    BASE_COMMIT,
    EXP_BENCH11,
    EXP_BENCH13,
    EXP_BENCH16,
    EXP_O_SUM,
    EXP_PERFT5,
    FENS_O,
    OUT38,
    WORK38,
    build_worktree_patch,
    check_four_numbers,
    fmt_pass,
    load_fens,
    measure_depth_set,
    utc_now,
)

PAIRS = [
    ("B1", "IdeaB1", ("030", "O_P_on_d12.txt"), ("080", "O_P_on_d12.txt")),
    ("S32", "IdeaS32", ("024", "P_on_O_d12.raw"), ("074", "p_on_O.raw.txt")),
    ("K4", "IdeaK4", ("043", "proof/P_on_O_d12.txt"), ("093", "O_P_on.raw.txt")),
    ("B8", "IdeaB8", ("028", "O12_P_on.txt"), ("078", "P_on_O_d12.raw")),
    ("S13", "IdeaS13", ("016", "P_on_O_d12.txt"), ("066", "O_Pon_d12.txt")),
]


def parse_raw_uci_200(path: pathlib.Path) -> list[int]:
    nodes_re = re.compile(r"\bnodes\s+(\d+)\b")
    depth_re = re.compile(r"\bdepth\s+(\d+)\b")
    out: list[int] = []
    cur: int | None = None
    for ln in path.read_text(encoding="utf-8").splitlines():
        st = ln.strip()
        if st.startswith("info "):
            mn = nodes_re.search(st)
            md = depth_re.search(st)
            if mn and md:
                cur = int(mn.group(1))
        elif st.startswith("bestmove "):
            if cur is None:
                raise RuntimeError(f"Missing info nodes before bestmove in {path}")
            out.append(cur)
            cur = None
    if len(out) != 200:
        raise RuntimeError(f"Expected 200 bestmoves in {path}, got {len(out)}")
    return out


def parse_our_200(path: pathlib.Path) -> list[int]:
    rows: list[int] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("index"):
            continue
        pts = s.split()
        rows.append(int(pts[-1]))
    assert len(rows) == 200
    return rows


def main() -> int:
    fens_o = load_fens(FENS_O)
    base_O = parse_our_200(OUT38 / "B_O_d12.nodes.txt")

    lines = [f"=== JOB 38 PART B: FIVE TWIN PAIRS ===", f"start_utc: {utc_now()}"]
    build_lines: list[str] = []
    all_ok = True
    equal_pairs: list[str] = []
    diff_pairs: list[str] = []
    seat_on_rows: dict[str, list[int]] = {}

    for idea_name, opt_name, (sA, fA), (sB, fB) in PAIRS:
        lines.append(f"\n=======================================================================")
        lines.append(f"PAIR {idea_name} ({opt_name}): seats {sA} and {sB}")
        lines.append(f"=======================================================================")
        for seat, committed_rel in [(sA, fA), (sB, fB)]:
            patch_path = WORK38 / f"seats/{seat}/idea.patch.txt"
            committed_path = WORK38 / f"seats/{seat}/{committed_rel}"
            ok_b, msg_b, exe_p, sha_p = build_worktree_patch(seat, patch_path)
            lines.append(f"\n--- Seat {seat} ({opt_name}) ---")
            lines.append(f"  apply_and_build: {'PASS' if ok_b else 'FAIL'} | {msg_b}")
            lines.append(f"  exe: {exe_p}")
            lines.append(f"  sha256: {sha_p}")
            if not ok_b:
                all_ok = False
                continue
            build_lines.append(
                f"[PartB {seat} {idea_name}] commit={BASE_COMMIT} patch=seats/{seat}/idea.patch.txt apply={msg_b} exe={exe_p} sha256={sha_p}"
            )

            four = check_four_numbers(exe_p)
            for k, exp in [("bench11", EXP_BENCH11), ("bench13", EXP_BENCH13), ("bench16", EXP_BENCH16), ("perft5", EXP_PERFT5)]:
                ok1, s1 = fmt_pass(f"{seat} {k}", four[k], exp)
                all_ok = all_ok and ok1
                lines.append("  " + s1)

            off_O = measure_depth_set(exe_p, FENS_O, 12, [(opt_name, "false")], OUT38 / f"{seat}_off_O_d12.nodes.txt")
            diff_off = sum(1 for a, b in zip(off_O, base_O) if a != b)
            ok_os, s_os = fmt_pass(f"{seat} S14 off O sum", sum(off_O), EXP_O_SUM)
            ok_od, s_od = fmt_pass(f"{seat} S14 off O differ_from_base", diff_off, 0)
            all_ok = all_ok and ok_os and ok_od
            lines.extend(["  " + s_os, "  " + s_od])

            on_O = measure_depth_set(exe_p, FENS_O, 12, [(opt_name, "true")], OUT38 / f"{seat}_on_O_d12.nodes.txt")
            seat_on_rows[seat] = on_O
            diff_base = sum(1 for a, b in zip(on_O, base_O) if a != b)
            committed_rows = parse_raw_uci_200(committed_path)
            diff_committed = [i + 1 for i, (a, b) in enumerate(zip(on_O, committed_rows)) if a != b]
            lines.append(
                f"  {seat} S14 on O: sum={sum(on_O)} | differ_from_base={diff_base}/200"
            )
            ok_cs, s_cs = fmt_pass(
                f"{seat} S14 on O sum_vs_seat_committed ({committed_rel})", sum(on_O), sum(committed_rows)
            )
            ok_cd, s_cd = fmt_pass(
                f"{seat} S14 on O differ_vs_seat_committed ({committed_rel})", len(diff_committed), 0
            )
            lines.extend(["  " + s_cs, "  " + s_cd])
            if diff_committed:
                lines.append(f"  WARNING: Seat {seat} committed rows ({committed_rel}) differ at {len(diff_committed)} positions: {diff_committed[:10]}")

        rA = seat_on_rows[sA]
        rB = seat_on_rows[sB]
        twin_diffs = [i + 1 for i, (a, b) in enumerate(zip(rA, rB)) if a != b]
        verdict = "EQUAL" if len(twin_diffs) == 0 else "DIFFERENT"
        if verdict == "EQUAL":
            equal_pairs.append(f"{idea_name} ({sA},{sB})")
        else:
            diff_pairs.append(f"{idea_name} ({sA},{sB})")
        lines.append(f"\n>>> PAIR {idea_name} ({sA} vs {sB}) TWIN COMPARISON:")
        lines.append(
            f"  {sA}_sum={sum(rA)} | {sB}_sum={sum(rB)} | twin_differ={len(twin_diffs)}/200 | verdict={verdict}"
        )
        if twin_diffs:
            lines.append(f"  First 3 positions where {sA} and {sB} differ:")
            for pos_idx in twin_diffs[:3]:
                lines.append(
                    f"    pos #{pos_idx}: {sA}={rA[pos_idx-1]} vs {sB}={rB[pos_idx-1]} (base={base_O[pos_idx-1]}) | FEN: {fens_o[pos_idx-1]}"
                )

    lines.append(f"\n=======================================================================")
    lines.append(f"SUMMARY: equal_twin_pairs={len(equal_pairs)}/5 {equal_pairs} | different_twin_pairs={len(diff_pairs)}/5 {diff_pairs}")
    lines.append(f"OVERALL_PART_B_HARNESS: {'PASS' if all_ok else 'FAIL'}")
    lines.append(f"done_utc: {utc_now()}")

    (OUT38 / "partB_raw.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with open(OUT38 / "builds.txt", "a", encoding="utf-8") as bf:
        for bl in build_lines:
            bf.write(bl + "\n")
    print("\n".join(lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
