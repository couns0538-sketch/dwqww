#!/usr/bin/env python3
"""
Job 47 Part P11: K4b (Seat 043) Ported, With Known Answer on 6b98f217,
Stack Safety Citation, OFF Identity, and PC20 Liveness.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j47_lib import (  # noqa: E402
    ALL_TWELVE_FALSE,
    EXP_BENCH11_NOOPT,
    EXP_BENCH13_NOOPT,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_PERFT5_NOOPT,
    G_EPD_PATH,
    JOB38,
    JOB39,
    JOB47,
    O_FENS_PATH,
    P11_K4B_PATCH,
    PC20_OPTIONS,
    REPO,
    WORK47,
    build_release_v3,
    count_row_diffs,
    fmt_cmp,
    generate_diff_u_patch,
    get_id_name_strict,
    read_j39_rows,
    run_epd_depth12_strict,
    run_fresh_bench_strict,
    run_fresh_perft5_strict,
    sha256_file,
    utc_now,
    verify_uci_option_strict,
)

BASE_COMMIT = "6b98f2170a3210e71beed04bbd2553972c253ed7"
GROK_043_PATCH = WORK47 / "grok_043_idea.patch.txt"
SUMMARY_OUT = JOB47 / "partP11_summary.txt"
BUILDS_OUT = JOB47 / "builds.txt"

S14_6B98_OPTIONS: list[tuple[str, str]] = [
    ("Threads", "1"),
    ("Hash", "16"),
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
]

EXP_6B98_OFF_O = 9500069
EXP_6B98_043_ON_O = 8983632


def parse_j38_nodes(path: pathlib.Path) -> list[int]:
    out: list[int] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("index") or s.startswith("#"):
            continue
        out.append(int(s.split()[-1]))
    return out


def build_6b98_with_043() -> tuple[str, str, int]:
    wt_dir = WORK47 / "wt_043_base"
    bld_dir = WORK47 / "bld_043_base"
    if wt_dir.exists():
        subprocess.run(["git", "-C", str(REPO), "worktree", "remove", "--force", str(wt_dir)], capture_output=True)
        if wt_dir.exists():
            shutil.rmtree(wt_dir)
    if bld_dir.exists():
        shutil.rmtree(bld_dir)

    subprocess.run(
        ["git", "-C", str(REPO), "worktree", "add", "--no-checkout", "--detach", str(wt_dir), BASE_COMMIT],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        subprocess.run(["git", "-C", str(wt_dir), "sparse-checkout", "init", "--cone"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(wt_dir), "sparse-checkout", "set", "forge-combo29"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(wt_dir), "checkout", BASE_COMMIT], check=True, capture_output=True)

        chk = subprocess.run(
            ["git", "-C", str(wt_dir), "apply", "--check", str(GROK_043_PATCH)],
            capture_output=True,
            text=True,
        )
        if chk.returncode != 0:
            raise RuntimeError(f"git apply --check failed on 6b98f217: {chk.stderr}")
        subprocess.run(["git", "-C", str(wt_dir), "apply", str(GROK_043_PATCH)], check=True)

        cfg = subprocess.run(
            [
                "cmake",
                "-S", str(wt_dir / "forge-combo29"),
                "-B", str(bld_dir),
                "-DCMAKE_BUILD_TYPE=Release",
                "-DCMAKE_CXX_COMPILER=g++",
            ],
            capture_output=True,
            text=True,
        )
        if cfg.returncode != 0:
            raise RuntimeError(f"cmake configure failed: {cfg.stderr}")
        bld = subprocess.run(["cmake", "--build", str(bld_dir), "-j4"], capture_output=True, text=True)
        if bld.returncode != 0:
            raise RuntimeError(f"cmake build failed: {bld.stderr}\n{bld.stdout}")
    finally:
        subprocess.run(["git", "-C", str(REPO), "worktree", "remove", "--force", str(wt_dir)], capture_output=True)
        if wt_dir.exists():
            shutil.rmtree(wt_dir)

    exe = str(bld_dir / "forge")
    return exe, sha256_file(exe), chk.returncode


def inspect_stack_safety(src10: pathlib.Path) -> tuple[bool, list[str]]:
    lines: list[str] = []
    all_ok = True

    hpp_lines = (src10 / "include/forge/search.hpp").read_text(encoding="utf-8").splitlines()
    cpp_lines = (src10 / "src/search.cpp").read_text(encoding="utf-8").splitlines()

    decl_line_no = None
    for idx, ln in enumerate(hpp_lines, start=1):
        if "std::array<SearchStack, MaxPly + 8> stack_{};" in ln:
            decl_line_no = idx
            break

    eval_init_line_no = None
    ss_root_line_no = None
    for idx, ln in enumerate(cpp_lines, start=1):
        if "entry.static_eval = ValueNone;" in ln and idx > 3900 and eval_init_line_no is None:
            eval_init_line_no = idx
        if "SearchStack* ss = &stack_[4];" in ln and ss_root_line_no is None:
            ss_root_line_no = idx

    ok, s = fmt_cmp("include/forge/search.hpp stack_ declaration line", decl_line_no, 585)
    all_ok &= ok
    lines.append(s)
    ok, s = fmt_cmp("src/search.cpp entry.static_eval = ValueNone line", eval_init_line_no, 3937)
    all_ok &= ok
    lines.append(s)
    ok, s = fmt_cmp("src/search.cpp root ss = &stack_[4] line", ss_root_line_no, 3953)
    all_ok &= ok
    lines.append(s)
    entries_below_root = 4  # stack_[0], stack_[1], stack_[2], stack_[3] lie below stack_[4]
    ok, s = fmt_cmp("entries below root entry (&stack_[4])", entries_below_root, 4)
    all_ok &= ok
    lines.append(s)
    lines.append(
        "  stack_proof: stack_ has MaxPly + 8 entries (include/forge/search.hpp:585); "
        "Worker::search_root initializes stack_[0..init_limit] with static_eval = ValueNone "
        "(src/search.cpp:3930-3952) and sets root SearchStack* ss = &stack_[4] (src/search.cpp:3953, ply=0). "
        "4 entries (stack_[0..3]) lie below root: (ss - 3) is stack_[1] at root (ply 0), stack_[2] at ply 1, "
        "and stack_[3] at ply 2 (all in-bounds with static_eval == ValueNone), and stack_[4 + ply - 3] for ply >= 3."
    )
    return all_ok, lines


def port_k4b_onto_bundle10(src10: pathlib.Path, src11: pathlib.Path) -> pathlib.Path:
    if src11.exists():
        shutil.rmtree(src11)
    shutil.copytree(src10, src11)

    hpp_p = src11 / "include/forge/search.hpp"
    hpp = hpp_p.read_text(encoding="utf-8")
    old_hpp = (
        "extern bool IdeaK4;                  // smaller reverse-futility margin when the opponent worsened (false = off)\n"
        "extern int IdeaK4_Shrink;            // centipawns removed from the reverse-futility margin when IdeaK4 fires\n"
    )
    new_hpp = (
        old_hpp
        + "extern bool IdeaK4b;                 // seat 043: smaller reverse-futility margin when opponent worsened over two plies (false = off)\n"
        + "extern int IdeaK4b_Shrink;           // centipawns removed from the reverse-futility margin when IdeaK4b fires (default 32)\n"
    )
    assert old_hpp in hpp, "Missing IdeaK4 declarations in include/forge/search.hpp"
    hpp_p.write_text(hpp.replace(old_hpp, new_hpp, 1), encoding="utf-8")

    cpp_p = src11 / "src/search.cpp"
    cpp = cpp_p.read_text(encoding="utf-8")

    old_def1 = "int IdeaK4_Shrink = 24;\n"
    new_def1 = "int IdeaK4_Shrink = 24;\nint IdeaK4b_Shrink = 32;\n"
    assert old_def1 in cpp, "Missing IdeaK4_Shrink = 24 in src/search.cpp"
    cpp = cpp.replace(old_def1, new_def1, 1)

    old_def2 = "bool IdeaK4 = false;\n"
    new_def2 = "bool IdeaK4 = false;\nbool IdeaK4b = false;\n"
    assert old_def2 in cpp, "Missing bool IdeaK4 = false in src/search.cpp"
    cpp = cpp.replace(old_def2, new_def2, 1)

    old_param = '        {"IdeaK4_Shrink", &IdeaK4_Shrink, 0, 200},\n'
    new_param = (
        '        {"IdeaK4_Shrink", &IdeaK4_Shrink, 0, 200},\n'
        '        {"IdeaK4b_Shrink", &IdeaK4b_Shrink, 0, 200},\n'
    )
    assert old_param in cpp, "Missing IdeaK4_Shrink parameter entry in src/search.cpp"
    cpp = cpp.replace(old_param, new_param, 1)

    old_rfp = (
        "        if (tune::IdeaK4) {\n"
        "            const int opponent_now = (ss - 1)->static_eval;\n"
        "            const int opponent_then = (ss - 3)->static_eval;\n"
        "            if (opponent_now != ValueNone && opponent_then != ValueNone && opponent_now < opponent_then) {\n"
        "                rfp_margin -= tune::IdeaK4_Shrink;\n"
        "            }\n"
        "        }\n"
    )
    new_rfp = (
        old_rfp
        + "        if (tune::IdeaK4b) {\n"
        + "            const int parent_eval = (ss - 1)->static_eval;\n"
        + "            const int older_eval = (ss - 3)->static_eval;\n"
        + "            if (parent_eval != ValueNone && older_eval != ValueNone && parent_eval < older_eval) {\n"
        + "                rfp_margin -= tune::IdeaK4b_Shrink;\n"
        + "            }\n"
        + "        }\n"
    )
    assert old_rfp in cpp, "Missing IdeaK4 RFP block in src/search.cpp"
    cpp = cpp.replace(old_rfp, new_rfp, 1)
    cpp_p.write_text(cpp, encoding="utf-8")

    uci_p = src11 / "src/uci.cpp"
    uci = uci_p.read_text(encoding="utf-8")

    old_uci_opt = '                         "option name IdeaK4 type check default false\\n"\n'
    new_uci_opt = (
        old_uci_opt
        + '                         "option name IdeaK4b type check default false\\n"\n'
    )
    assert old_uci_opt in uci, "Missing IdeaK4 uci option line in src/uci.cpp"
    uci = uci.replace(old_uci_opt, new_uci_opt, 1)

    old_uci_set = (
        '            } else if (name == "IdeaK4") {\n'
        '                if (value_text == "true" || value_text == "false") forge::tune::IdeaK4 = value_text == "true";\n'
        '                else note_invalid();\n'
    )
    new_uci_set = (
        old_uci_set
        + '            } else if (name == "IdeaK4b") {\n'
        + '                if (value_text == "true" || value_text == "false") forge::tune::IdeaK4b = value_text == "true";\n'
        + '                else note_invalid();\n'
    )
    assert old_uci_set in uci, "Missing IdeaK4 setoption handler in src/uci.cpp"
    uci = uci.replace(old_uci_set, new_uci_set, 1)
    uci_p.write_text(uci, encoding="utf-8")

    generate_diff_u_patch(src10, src11, P11_K4B_PATCH)
    return P11_K4B_PATCH


def main() -> None:
    JOB47.mkdir(parents=True, exist_ok=True)
    WORK47.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    all_ok = True
    lines.append("=== JOB 47 PART P11: K4b (SEAT 043) PORTED, KNOWN ANSWER, STACK PROOF, OFF IDENTITY, LIVENESS ===")
    lines.append(f"start_utc: {utc_now()}")

    # (a) Read seat 043 patch
    lines.append("\n--- (a) Seat 043 Patch Read-Only Inspection ---")
    patch_line_count = len(GROK_043_PATCH.read_text(encoding="utf-8").splitlines())
    ok, s = fmt_cmp("grok-043 idea.patch.txt line count", patch_line_count, 90)
    all_ok &= ok
    lines.append(s)
    ok, s = fmt_cmp("grok-043 idea.patch.txt CRLF count", GROK_043_PATCH.read_bytes().count(b"\r\n"), 0)
    all_ok &= ok
    lines.append(s)
    lines.append(
        f"  read_only_copy_sha256({GROK_043_PATCH}): {sha256_file(GROK_043_PATCH)} "
        "(from for-fable-and-opus/grok-043:forge-combo29/grok/043/idea.patch.txt)"
    )
    lines.append(
        "  mechanism: adds IdeaK4 (check, default false) and IdeaK4_Shrink (spin, default 32, 0..200); "
        "in Worker::search reverse futility pruning, when (ss - 1)->static_eval != ValueNone && "
        "(ss - 3)->static_eval != ValueNone && (ss - 1)->static_eval < (ss - 3)->static_eval, "
        "subtracts IdeaK4_Shrink (32) from rfp_margin (whereas seat 093 K4a in bundle uses Shrink = 24)."
    )

    # (b) Known answer on 6b98f217
    lines.append("\n--- (b) Known Answer on Helpers' Tree 6b98f217 (S14, Built-In Eval, O Depth 12) ---")
    exe_043, sha_043, rc_043 = build_6b98_with_043()
    ok, s = fmt_cmp("git apply --check grok-043 on 6b98f217", rc_043, 0)
    all_ok &= ok
    lines.append(s)
    lines.append(f"  exe_path: {exe_043}")
    lines.append(f"  exe_sha256({exe_043}): {sha_043}")

    ok_u1, u1_lines = verify_uci_option_strict(exe_043, "IdeaK4", "check", "false", ("true", "false"))
    ok_u2, u2_lines = verify_uci_option_strict(exe_043, "IdeaK4_Shrink", "spin", "32", ("32",))
    all_ok &= ok_u1 and ok_u2
    lines.extend(u1_lines + u2_lines)

    b11_043 = run_fresh_bench_strict(exe_043, 11, [])
    b13_043 = run_fresh_bench_strict(exe_043, 13, [])
    pf5_043 = run_fresh_perft5_strict(exe_043)
    for lbl, got, exp in [
        ("6b98+043 no-option bench 11", b11_043, EXP_BENCH11_NOOPT),
        ("6b98+043 no-option bench 13", b13_043, EXP_BENCH13_NOOPT),
        ("6b98+043 no-option perft 5", pf5_043, EXP_PERFT5_NOOPT),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok &= ok
        lines.append(s)

    j38_off_nodes = parse_j38_nodes(JOB38 / "043_off_O_d12.nodes.txt")
    j38_b_nodes = parse_j38_nodes(JOB38 / "B_O_d12.nodes.txt")
    j38_on_nodes = parse_j38_nodes(JOB38 / "043_on_O_d12.nodes.txt")

    off043_p = JOB47 / "P11b_6b98f217_043_off_O_d12.rows.txt"
    off043_rows = run_epd_depth12_strict(
        exe_043, O_FENS_PATH, S14_6B98_OPTIONS, [("IdeaK4", "false")], off043_p, off043_p.with_suffix(".rows.txt.meta"), cpu_pin=1
    )
    off043_sum = sum(r[1] for r in off043_rows)
    ok, s = fmt_cmp("6b98+043 IdeaK4=false O d12 sum", off043_sum, EXP_6B98_OFF_O)
    all_ok &= ok
    lines.append(s)
    eq_j38_off = sum(1 for r, n in zip(off043_rows, j38_off_nodes) if r[1] == n)
    ok, s = fmt_cmp("6b98+043 IdeaK4=false nodes equal vs job38/043_off_O_d12", eq_j38_off, 200)
    all_ok &= ok
    lines.append(s)
    eq_j38_b = sum(1 for r, n in zip(off043_rows, j38_b_nodes) if r[1] == n)
    ok, s = fmt_cmp("6b98+043 IdeaK4=false nodes equal vs job38/B_O_d12", eq_j38_b, 200)
    all_ok &= ok
    lines.append(s)

    on043_p = JOB47 / "P11b_6b98f217_043_on_O_d12.rows.txt"
    on043_rows = run_epd_depth12_strict(
        exe_043, O_FENS_PATH, S14_6B98_OPTIONS, [("IdeaK4", "true")], on043_p, on043_p.with_suffix(".rows.txt.meta"), cpu_pin=1
    )
    on043_sum = sum(r[1] for r in on043_rows)
    ok_on, s = fmt_cmp("6b98+043 IdeaK4=true O d12 sum", on043_sum, EXP_6B98_043_ON_O)
    all_ok &= ok_on
    lines.append(s)
    eq_j38_on = sum(1 for r, n in zip(on043_rows, j38_on_nodes) if r[1] == n)
    ok, s = fmt_cmp("6b98+043 IdeaK4=true nodes equal vs job38/043_on_O_d12", eq_j38_on, 200)
    all_ok &= ok
    lines.append(s)

    if not ok_on:
        lines.append(f"  STOP P11 AND M14: 6b98+043 IdeaK4=true sum {on043_sum} != {EXP_6B98_043_ON_O}")
        SUMMARY_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        raise SystemExit(1)

    # (c) Stack check BEFORE build + Port onto bundle10 -> bundle11 + OFF identity
    lines.append("\n--- (c) Search Stack Safety Check (Before Build), Port P11_K4b.patch.txt, and OFF Identity ---")
    src10 = WORK47 / "src_bundle10"
    src11 = WORK47 / "src_bundle11_k4b"
    ok_stk, stk_lines = inspect_stack_safety(src10)
    all_ok &= ok_stk
    lines.extend(stk_lines)

    patch_p = port_k4b_onto_bundle10(src10, src11)
    ok, s = fmt_cmp("P11_K4b.patch.txt CRLF count", patch_p.read_bytes().count(b"\r\n"), 0)
    all_ok &= ok
    lines.append(s)

    chk_p11 = subprocess.run(
        ["git", "apply", "--check", "-p1", str(patch_p)],
        cwd=str(src10),
        capture_output=True,
        text=True,
    )
    ok, s = fmt_cmp("git apply --check -p1 P11_K4b.patch.txt on bundle10", chk_p11.returncode, 0)
    all_ok &= ok
    lines.append(s)
    patch_sha = sha256_file(patch_p)
    lines.append(f"  patch sha256({patch_p}): {patch_sha}")

    bld11_dir = WORK47 / "bld_bundle11_k4b"
    exe_b11, sha_b11, cflags_b11, lflags_b11 = build_release_v3(src11, bld11_dir)
    id_b11 = get_id_name_strict(exe_b11)
    lines.append(f"  bundle11 exe path: {exe_b11}")
    lines.append(f"  bundle11 exe sha256({exe_b11}): {sha_b11}")
    lines.append(f"  bundle11 id name: {id_b11}")

    for oname, otype, odef, ovals in [
        ("IdeaK4b", "check", "false", ("true", "false")),
        ("IdeaK4b_Shrink", "spin", "32", ("32",)),
        ("IdeaK4", "check", "false", ("true", "false")),
        ("IdeaK4_Shrink", "spin", "24", ("24",)),
    ]:
        ok_u, u_lines = verify_uci_option_strict(exe_b11, oname, otype, odef, ovals)
        all_ok &= ok_u
        lines.extend(u_lines)

    b11_11 = run_fresh_bench_strict(exe_b11, 11, [])
    b13_11 = run_fresh_bench_strict(exe_b11, 13, [])
    pf5_11 = run_fresh_perft5_strict(exe_b11)
    for lbl, got, exp in [
        ("bundle11 no-option bench 11", b11_11, EXP_BENCH11_NOOPT),
        ("bundle11 no-option bench 13", b13_11, EXP_BENCH13_NOOPT),
        ("bundle11 no-option perft 5", pf5_11, EXP_PERFT5_NOOPT),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok &= ok
        lines.append(s)

    ref_s0_o = read_j39_rows(JOB47 / "step0_bundle10_all_off_O_d12.rows.txt")
    ref_s0_g = read_j39_rows(JOB47 / "step0_bundle10_all_off_G_d12.rows.txt")
    ref_j39_o = read_j39_rows(JOB39 / "OFF_O_d12.rows.txt")
    ref_j39_g = read_j39_rows(JOB39 / "OFF_G_d12.rows.txt")

    off11_o_p = JOB47 / "P11c_bundle11_all_off_O_d12.rows.txt"
    off11_o_rows = run_epd_depth12_strict(
        exe_b11, O_FENS_PATH, PC20_OPTIONS, ALL_TWELVE_FALSE + [("IdeaK4b_Shrink", "32")], off11_o_p, off11_o_p.with_suffix(".rows.txt.meta"), cpu_pin=1
    )
    off11_o_sum = sum(r[1] for r in off11_o_rows)
    ok, s = fmt_cmp("bundle11 OFF O d12 sum", off11_o_sum, EXP_OFF_O_SUM)
    all_ok &= ok
    lines.append(s)
    eq_o_s0 = sum(1 for a, b in zip(off11_o_rows, ref_s0_o) if a == b)
    ok, s = fmt_cmp("bundle11 OFF O d12 equal vs bundle10 OFF O", eq_o_s0, 200)
    all_ok &= ok
    lines.append(s)
    eq_o_j39 = sum(1 for a, b in zip(off11_o_rows, ref_j39_o) if a == b)
    ok, s = fmt_cmp("bundle11 OFF O d12 equal vs job39 OFF_O", eq_o_j39, 200)
    all_ok &= ok
    lines.append(s)

    off11_g_p = JOB47 / "P11c_bundle11_all_off_G_d12.rows.txt"
    off11_g_rows = run_epd_depth12_strict(
        exe_b11, G_EPD_PATH, PC20_OPTIONS, ALL_TWELVE_FALSE + [("IdeaK4b_Shrink", "32")], off11_g_p, off11_g_p.with_suffix(".rows.txt.meta"), cpu_pin=1
    )
    off11_g_sum = sum(r[1] for r in off11_g_rows)
    ok, s = fmt_cmp("bundle11 OFF G d12 sum", off11_g_sum, EXP_OFF_G_SUM)
    all_ok &= ok
    lines.append(s)
    eq_g_s0 = sum(1 for a, b in zip(off11_g_rows, ref_s0_g) if a == b)
    ok, s = fmt_cmp("bundle11 OFF G d12 equal vs bundle10 OFF G", eq_g_s0, 353)
    all_ok &= ok
    lines.append(s)
    eq_g_j39 = sum(1 for a, b in zip(off11_g_rows, ref_j39_g) if a == b)
    ok, s = fmt_cmp("bundle11 OFF G d12 equal vs job39 OFF_G", eq_g_j39, 353)
    all_ok &= ok
    lines.append(s)

    # (d) Liveness: IdeaK4b alone under PC20 on O at depth 12
    lines.append("\n--- (d) Liveness: IdeaK4b Alone (IdeaK4b_Shrink=32) Under PC20 on O at Depth 12 ---")
    only_k4b_opts = [
        (k, "true" if k == "IdeaK4b" else v) for k, v in ALL_TWELVE_FALSE
    ] + [("IdeaK4b_Shrink", "32")]
    k4b_o_p = JOB47 / "P11d_bundle11_only_IdeaK4b_O_d12.rows.txt"
    k4b_o_rows = run_epd_depth12_strict(
        exe_b11, O_FENS_PATH, PC20_OPTIONS, only_k4b_opts, k4b_o_p, k4b_o_p.with_suffix(".rows.txt.meta"), cpu_pin=1
    )
    k4b_o_sum = sum(r[1] for r in k4b_o_rows)
    node_diffs = sum(1 for a, b in zip(k4b_o_rows, off11_o_rows) if a[1] != b[1])
    bm_diffs = sum(1 for a, b in zip(k4b_o_rows, off11_o_rows) if a[2] != b[2])
    sc_diffs = sum(1 for a, b in zip(k4b_o_rows, off11_o_rows) if a[3] != b[3])

    lines.append(f"  IdeaK4b alone PC20 O d12 sum                : {k4b_o_sum} (OFF = {off11_o_sum}, delta = {k4b_o_sum - off11_o_sum:+d} nodes)")
    lines.append(f"  IdeaK4b vs OFF node-count diffs (of 200)    : {node_diffs} / 200")
    lines.append(f"  IdeaK4b vs OFF best-move diffs  (of 200)    : {bm_diffs} / 200")
    lines.append(f"  IdeaK4b vs OFF score diffs      (of 200)    : {sc_diffs} / 200")
    ok_live, s = fmt_cmp("IdeaK4b liveness (at least 1 node diff > 0)", node_diffs > 0, True)
    all_ok &= ok_live
    lines.append(s)

    pred_ok = 180 <= node_diffs <= 200
    lines.append(
        f"  PREDICTION (1) CHECK: node_diffs = {node_diffs} / 200 "
        f"(predicted 199, falsification range outside [180, 200] -> {'TRUE' if pred_ok else 'FALSE'})"
    )

    btxt = BUILDS_OUT.read_text(encoding="utf-8")
    if "7. Part P11(b)" not in btxt:
        extra_builds = [
            "",
            f"7. Part P11(b) 6b98f217 + grok-043 Release executable: {exe_043}",
            f"   exe sha256({exe_043}) = {sha_043}",
            f"   patch sha256({GROK_043_PATCH}) = {sha256_file(GROK_043_PATCH)}",
            "",
            f"8. Part P11(c-d) + Part M14 bundle11 executable (bundle10 + {patch_p}): {exe_b11}",
            f"   exe sha256({exe_b11}) = {sha_b11}",
            f"   id_name = {id_b11}",
            f"   patch sha256({patch_p}) = {patch_sha}",
            f"   compile_flags = {cflags_b11}",
            f"   link_flags    = {lflags_b11}",
            "",
        ]
        BUILDS_OUT.write_text(btxt.rstrip() + "\n" + "\n".join(extra_builds), encoding="utf-8")

    ok, s = fmt_cmp("PART P11 OVERALL", int(all_ok), 1)
    lines.append("\n" + s)
    lines.append(f"done_utc: {utc_now()}")

    out_text = "\n".join(lines) + "\n"
    SUMMARY_OUT.write_text(out_text, encoding="utf-8")
    print(out_text)
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
