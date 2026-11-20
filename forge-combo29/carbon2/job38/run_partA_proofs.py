#!/usr/bin/env python3
"""
Job 38 Part A (`A1` + `A3` deterministic proofs & `s10_variant.patch.txt` generation):
1. Generates `s10_variant.patch.txt` from `031/idea.patch.txt` with:
   - shrink called/applied ONLY when `alpha < best_score && best_score < beta`
   - probe search executed on a dedicated stack slice (`shuffle_stack_`) so the
     outer node's `SearchStack* ss` (and descendants) is never touched.
2. Applies `031/idea.patch.txt`, `081/idea.patch.txt`, and `s10_variant.patch.txt`
   each to its own fresh worktree of `6b98f217` (`git apply --check` first),
   builds Release with `g++`, checks the 4 no-option numbers, checks `S14` switch-off
   on `O` (200) and `G` (353) position-by-position vs `exe B`, and measures `S14`
   switch-on `O` rows (comparing `031` and `081` position-by-position against their
   committed rows).
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j38_harness import (
    BASE_COMMIT,
    EXP_BENCH11,
    EXP_BENCH13,
    EXP_BENCH16,
    EXP_G_SUM,
    EXP_O_SUM,
    EXP_PERFT5,
    FENS_G,
    FENS_O,
    OUT38,
    REPO,
    WORK38,
    build_worktree_patch,
    check_four_numbers,
    fmt_pass,
    measure_depth_set,
    utc_now,
)


def parse_200_rows(path: pathlib.Path, expected_n: int = 200) -> list[int]:
    rows: list[int] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("index"):
            continue
        pts = s.split()
        if len(pts) == 1 and pts[0].isdigit():
            rows.append(int(pts[0]))
        elif len(pts) >= 2 and pts[0].isdigit():
            idx = int(pts[0])
            if 1 <= idx <= expected_n and idx == len(rows) + 1:
                rows.append(int(pts[-1]))
    if len(rows) != expected_n:
        raise RuntimeError(f"Expected {expected_n} rows in {path}, parsed {len(rows)}")
    return rows


def make_s10_variant_patch() -> pathlib.Path:
    wt = WORK38 / "wt_make_var"
    if wt.exists():
        subprocess.run(["git", "-C", str(REPO), "worktree", "remove", "--force", str(wt)], capture_output=True)
        if wt.exists():
            shutil.rmtree(wt)
    subprocess.run(
        ["git", "-C", str(REPO), "worktree", "add", "--no-checkout", "--detach", str(wt), BASE_COMMIT],
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "-C", str(wt), "sparse-checkout", "init", "--cone"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(wt), "sparse-checkout", "set", "forge-combo29"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(wt), "checkout", BASE_COMMIT], check=True, capture_output=True)

    p031 = WORK38 / "seats/031/idea.patch.txt"
    subprocess.run(["git", "-C", str(wt), "apply", str(p031)], check=True)

    # 1. Update include/forge/search.hpp: add dedicated probe stack `shuffle_stack_`
    hpp = wt / "forge-combo29/include/forge/search.hpp"
    hpp_txt = hpp.read_text(encoding="utf-8")
    old_hpp = (
        "    bool shuffle_suppress_ = false;\n"
        "    Color shuffle_winner_ = White;\n"
    )
    new_hpp = (
        "    bool shuffle_suppress_ = false;\n"
        "    Color shuffle_winner_ = White;\n"
        "    std::unique_ptr<std::array<SearchStack, MaxPly + 8>> shuffle_stack_;\n"
    )
    assert old_hpp in hpp_txt, "Expected shuffle_suppress_ block in search.hpp"
    hpp.write_text(hpp_txt.replace(old_hpp, new_hpp, 1), encoding="utf-8")

    # 2. Update src/search.cpp:
    cpp = wt / "forge-combo29/src/search.cpp"
    cpp_txt = cpp.read_text(encoding="utf-8")

    old_clear = (
        "    shuffle_suppress_ = false;\n"
        "    shuffle_winner_ = White;\n"
    )
    new_clear = (
        "    shuffle_suppress_ = false;\n"
        "    shuffle_winner_ = White;\n"
        "    if (shuffle_stack_) {\n"
        "        for (SearchStack& entry : *shuffle_stack_) entry = SearchStack{};\n"
        "    }\n"
    )
    assert old_clear in cpp_txt, "Expected clear block in search.cpp"
    cpp_txt = cpp_txt.replace(old_clear, new_clear, 1)

    old_probe = (
        "    if (shuffle_suppress_ || ss->ply < 2) return best_score;\n"
    )
    new_probe_guard = (
        "    if (shuffle_suppress_ || ss->ply < 2 || ss->ply >= MaxPly) return best_score;\n"
    )
    assert old_probe in cpp_txt, "Expected ply guard in shrink_shuffle_score"
    cpp_txt = cpp_txt.replace(old_probe, new_probe_guard, 1)

    old_call_probe = (
        "    const bool saved_suppress = shuffle_suppress_;\n"
        "    const Color saved_winner = shuffle_winner_;\n"
        "    shuffle_suppress_ = true;\n"
        "    shuffle_winner_ = winner;\n"
        "    const int probe = search(board, ss, tune::IdeaS10_Probe, lo, hi, false);\n"
        "    shuffle_suppress_ = saved_suppress;\n"
        "    shuffle_winner_ = saved_winner;\n"
    )
    new_call_probe = (
        "    if (!shuffle_stack_) {\n"
        "        shuffle_stack_ = std::make_unique<std::array<SearchStack, MaxPly + 8>>();\n"
        "    }\n"
        "    auto& pstack = *shuffle_stack_;\n"
        "    const int ply = ss->ply;\n"
        "    for (int i = 0; i < MaxPly + 8; ++i) {\n"
        "        SearchStack& entry = pstack[static_cast<std::size_t>(i)];\n"
        "        entry.pv_length = 0;\n"
        "        entry.ply = i - 4;\n"
        "        entry.current_move = Move::none();\n"
        "        entry.excluded_move = Move::none();\n"
        "        entry.killers = {};\n"
        "        entry.moved_piece = Empty;\n"
        "        entry.static_eval = ValueNone;\n"
        "        entry.raw_eval = ValueNone;\n"
        "        entry.move_count = 0;\n"
        "        entry.arrival_index = 0;\n"
        "        entry.cutoff_count = 0;\n"
        "        entry.double_extensions = 0;\n"
        "        entry.withheld_plies = 0;\n"
        "        entry.in_check = false;\n"
        "        entry.tt_pv = false;\n"
        "        entry.null_move_allowed = true;\n"
        "        entry.continuation = &(*continuation_history_)[Empty][0];\n"
        "        entry.accumulator.valid = false;\n"
        "        entry.runtime_psqt.valid = false;\n"
        "        entry.entered_null = false;\n"
        "        entry.diff_known = false;\n"
        "        entry.dirty.count = 0;\n"
        "    }\n"
        "    for (int k = -4; k <= 0; ++k) {\n"
        "        pstack[static_cast<std::size_t>(ply + 4 + k)] = *(ss + k);\n"
        "    }\n"
        "    SearchStack* probe_ss = &pstack[static_cast<std::size_t>(ply + 4)];\n"
        "    probe_ss->excluded_move = Move::none();\n"
        "    probe_ss->withheld_plies = 0;\n"
        "    const bool saved_suppress = shuffle_suppress_;\n"
        "    const Color saved_winner = shuffle_winner_;\n"
        "    shuffle_suppress_ = true;\n"
        "    shuffle_winner_ = winner;\n"
        "    const int probe = search(board, probe_ss, tune::IdeaS10_Probe, lo, hi, false);\n"
        "    shuffle_suppress_ = saved_suppress;\n"
        "    shuffle_winner_ = saved_winner;\n"
    )
    assert old_call_probe in cpp_txt, "Expected probe search block in shrink_shuffle_score"
    cpp_txt = cpp_txt.replace(old_call_probe, new_call_probe, 1)

    old_loop_head = (
        "    int wide_quiet_misses = 0;\n"
        "    bool futility_tight = false;\n\n"
        "    Move move;\n"
    )
    new_loop_head = (
        "    int wide_quiet_misses = 0;\n"
        "    bool futility_tight = false;\n"
        "    const int orig_alpha = alpha;\n\n"
        "    Move move;\n"
    )
    assert old_loop_head in cpp_txt, "Expected move-loop header in Worker::search"
    cpp_txt = cpp_txt.replace(old_loop_head, new_loop_head, 1)

    old_outer = (
        "    // IdeaS10 is off by default. The call is skipped, so node counts stay put.\n"
        "    if (tune::IdeaS10) {\n"
        "        best_score = shrink_shuffle_score(board, ss, depth, best_score);\n"
        "        if (aborted_) return 0;\n"
        "    }\n"
    )
    new_outer = (
        "    // IdeaS10 is off by default; when on, shrink only interior scores (orig_alpha < best_score < beta).\n"
        "    if (tune::IdeaS10 && orig_alpha < best_score && best_score < beta) {\n"
        "        best_score = shrink_shuffle_score(board, ss, depth, best_score);\n"
        "        if (aborted_) return 0;\n"
        "    }\n"
    )
    assert old_outer in cpp_txt, "Expected outer call site in Worker::search"
    cpp_txt = cpp_txt.replace(old_outer, new_outer, 1)
    cpp.write_text(cpp_txt, encoding="utf-8")

    diff_res = subprocess.run(["git", "-C", str(wt), "diff"], check=True, capture_output=True, text=True)
    out_patch = OUT38 / "s10_variant.patch.txt"
    out_patch.write_text(diff_res.stdout, encoding="utf-8")
    subprocess.run(["git", "-C", str(REPO), "worktree", "remove", "--force", str(wt)], check=True, capture_output=True)
    return out_patch


def main() -> int:
    base_O = parse_200_rows(OUT38 / "B_O_d12.nodes.txt", 200)
    base_G = parse_200_rows(OUT38 / "B_G_d12.nodes.txt", 353)

    var_patch = make_s10_variant_patch()
    specs = [
        (
            "031",
            WORK38 / "seats/031/idea.patch.txt",
            WORK38 / "seats/031/P_on_O_d12.nodes.txt",
            10937472,
            195,
        ),
        (
            "081",
            WORK38 / "seats/081/idea.patch.txt",
            WORK38 / "seats/081/O_p_on_d12.nodes.txt",
            9542904,
            10,
        ),
        (
            "s10_variant",
            var_patch,
            None,
            None,
            None,
        ),
    ]

    out_lines = [f"=== JOB 38 PART A PROOFS (031, 081, s10_variant) ===", f"start_utc: {utc_now()}"]
    build_lines: list[str] = []
    all_ok = True

    for tag, patch_path, seat_rows_path, known_sum, known_diff_base in specs:
        ok_b, msg_b, exe_p, sha_p = build_worktree_patch(tag, patch_path)
        out_lines.append(f"\n--- [{tag}] patch={patch_path} ---")
        out_lines.append(f"apply_and_build: {'PASS' if ok_b else 'FAIL'} | {msg_b}")
        out_lines.append(f"exe: {exe_p}")
        out_lines.append(f"sha256: {sha_p}")
        if not ok_b:
            all_ok = False
            continue

        build_lines.append(
            f"[PartA {tag}] commit={BASE_COMMIT} patch={patch_path.name} apply={msg_b} exe={exe_p} sha256={sha_p}"
        )

        four = check_four_numbers(exe_p)
        for k, exp in [("bench11", EXP_BENCH11), ("bench13", EXP_BENCH13), ("bench16", EXP_BENCH16), ("perft5", EXP_PERFT5)]:
            ok1, s1 = fmt_pass(f"{tag} {k}", four[k], exp)
            all_ok = all_ok and ok1
            out_lines.append("  " + s1)

        # S14 off on O and G
        off_O = measure_depth_set(exe_p, FENS_O, 12, [("IdeaS10", "false")], OUT38 / f"{tag}_off_O_d12.nodes.txt")
        off_G = measure_depth_set(exe_p, FENS_G, 12, [("IdeaS10", "false")], OUT38 / f"{tag}_off_G_d12.nodes.txt")

        diff_off_O = sum(1 for a, b in zip(off_O, base_O) if a != b)
        diff_off_G = sum(1 for a, b in zip(off_G, base_G) if a != b)
        ok_oo, s_oo = fmt_pass(f"{tag} S14 off O sum", sum(off_O), EXP_O_SUM)
        ok_ood, s_ood = fmt_pass(f"{tag} S14 off O differ_from_base", diff_off_O, 0)
        ok_og, s_og = fmt_pass(f"{tag} S14 off G sum", sum(off_G), EXP_G_SUM)
        ok_ogd, s_ogd = fmt_pass(f"{tag} S14 off G differ_from_base", diff_off_G, 0)
        all_ok = all_ok and ok_oo and ok_ood and ok_og and ok_ogd
        out_lines.extend(["  " + s_oo, "  " + s_ood, "  " + s_og, "  " + s_ogd])

        # S14 on on O
        on_O = measure_depth_set(exe_p, FENS_O, 12, [("IdeaS10", "true")], OUT38 / f"{tag}_on_O_d12.nodes.txt")
        diff_on_base = [i + 1 for i, (a, b) in enumerate(zip(on_O, base_O)) if a != b]
        out_lines.append(
            f"  {tag} S14 on O: sum={sum(on_O)} | differ_from_base={len(diff_on_base)}/200 | first_diffs={diff_on_base[:10]}"
        )
        if known_sum is not None:
            ok_ks, s_ks = fmt_pass(f"{tag} S14 on O sum vs known", sum(on_O), known_sum)
            ok_kd, s_kd = fmt_pass(f"{tag} S14 on O differ_from_base vs known", len(diff_on_base), known_diff_base)
            all_ok = all_ok and ok_ks and ok_kd
            out_lines.extend(["  " + s_ks, "  " + s_kd])
        if seat_rows_path is not None:
            seat_rows = parse_200_rows(seat_rows_path, 200)
            diff_vs_seat = [i + 1 for i, (a, b) in enumerate(zip(on_O, seat_rows)) if a != b]
            ok_sr, s_sr = fmt_pass(f"{tag} S14 on O differ_vs_seat_committed ({seat_rows_path.name})", len(diff_vs_seat), 0)
            ok_ss, s_ss = fmt_pass(f"{tag} S14 on O sum_vs_seat_committed", sum(on_O), sum(seat_rows))
            all_ok = all_ok and ok_sr and ok_ss
            out_lines.extend(["  " + s_sr, "  " + s_ss])

    # Also compare s10_variant on_O against 031 on_O
    var_on = parse_200_rows(OUT38 / "s10_variant_on_O_d12.nodes.txt", 200)
    r031_on = parse_200_rows(OUT38 / "031_on_O_d12.nodes.txt", 200)
    diff_var_031 = [i + 1 for i, (a, b) in enumerate(zip(var_on, r031_on)) if a != b]
    out_lines.append(
        f"\ns10_variant_on_O vs 031_on_O: var_sum={sum(var_on)} vs 031_sum={sum(r031_on)} | positions_differ={len(diff_var_031)}/200"
    )
    for idx in [i for i, (a, b) in enumerate(zip(var_on, base_O), start=1) if a != b][:10]:
        out_lines.append(f"  s10_variant_on_O != base at pos #{idx}: var={var_on[idx-1]} vs base={base_O[idx-1]} (031={r031_on[idx-1]})")

    end_ts = utc_now()
    out_lines.append(f"\nOVERALL_PART_A_PROOFS: {'PASS' if all_ok else 'FAIL'}")
    out_lines.append(f"done_utc: {end_ts}")

    (OUT38 / "partA_proofs_raw.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    with open(OUT38 / "builds.txt", "a", encoding="utf-8") as bf:
        for bl in build_lines:
            bf.write(bl + "\n")
    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
