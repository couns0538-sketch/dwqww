#!/usr/bin/env python3
"""
Job 42 Part P8 (`build_and_verify_p8.py`):
- Adds `IdeaS13_Hoist` (`check`, default `false`) on top of `r15d + v3 + bundle_grok7.patch.txt`:
  when `IdeaS13 && IdeaS13_Hoist`, computes `s13_hoisted_prep = break_prep_order(board, move)` on the
  PARENT's position before `board.make_move(move, undo)` and reads that local in LMR; when `IdeaS13_Hoist`
  is `false`, executes Job 39's path identically.
- Emits `forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt` (`diff -u`, LF, against `r15d + v3 + bundle_grok7.patch.txt`).
- Verifies all OFF locks, `IdeaS13_Hoist` alone = OFF (`200 == 200`), all 7 existing switches unchanged (`200 == 200`),
  runs `O` d12, `G` d12, and `Set A line L` with `IdeaS13 + IdeaS13_Hoist` both on, and runs the separate
  scratch counter build (`P8c`) summed via `sum_p8_counters.py`.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j42_lib import (  # noqa: E402
    ALL_EIGHT_IDEA_FALSE,
    BUNDLE7_PATCH,
    EIGHT_SWITCH_NAMES,
    EXP_NOPC20_HD_FALSE_BENCH13,
    EXP_NOPC20_HD_TRUE_BENCH13,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_SETA_L_NODES,
    EXP_SETA_L_RECORDS,
    EXP_SETA_L_SHA,
    G_EPD_PATH,
    JOB39,
    JOB42,
    O_FENS_PATH,
    SEVEN_SWITCH_SPECS,
    WORK42,
    apply_patch_to_fresh_v3,
    build_release_v3,
    diff_rows,
    fmt_cmp,
    generate_diff_u_patch,
    get_id_name,
    load_fens,
    pc20_option_lines,
    read_j39_rows,
    run_epd_depth12,
    run_fresh_bench,
    run_selfgame_set_with_options,
    sha256_file,
    utc_now,
    verify_all_off_numbers,
    verify_uci_option_check,
    write_seta_meta,
    write_v2_v3_rows,
)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    cnt = text.count(old)
    if cnt != 1:
        raise RuntimeError(f"[{label}] expected 1 occurrence, found {cnt}:\n{old!r}")
    return text.replace(old, new, 1)


def inject_p8_hoist(tree_dir: pathlib.Path) -> None:
    # 1. include/forge/search.hpp
    shpp_p = tree_dir / "include/forge/search.hpp"
    shpp = shpp_p.read_text(encoding="utf-8")
    shpp = replace_once(
        shpp,
        "extern bool IdeaS13;                 // credit the quiet piece move before a same-side pawn break (false = off)\n",
        "extern bool IdeaS13;                 // credit the quiet piece move before a same-side pawn break (false = off)\n"
        "extern bool IdeaS13_Hoist;           // read break_prep_order on parent before make_move for LMR (false = off)\n",
        "search.hpp IdeaS13_Hoist extern",
    )
    shpp_p.write_text(shpp, encoding="utf-8")

    # 2. src/search.cpp
    scpp_p = tree_dir / "src/search.cpp"
    scpp = scpp_p.read_text(encoding="utf-8")
    scpp = replace_once(
        scpp,
        "bool IdeaS13 = false;\n",
        "bool IdeaS13 = false;\nbool IdeaS13_Hoist = false;\n",
        "search.cpp IdeaS13_Hoist def",
    )
    scpp = replace_once(
        scpp,
        "        (ss + 1)->ply = ply + 1;\n"
        "        (ss + 1)->arrival_index = move_count;\n"
        "        record_move(ss, board, move);\n"
        "        Undo undo;\n"
        "        (void)board.make_move(move, undo);\n",
        "        (ss + 1)->ply = ply + 1;\n"
        "        (ss + 1)->arrival_index = move_count;\n"
        "        record_move(ss, board, move);\n"
        "        const int s13_hoisted_prep =\n"
        "            (tune::IdeaS13 && tune::IdeaS13_Hoist && quiet) ? break_prep_order(board, move) : 0;\n"
        "        Undo undo;\n"
        "        (void)board.make_move(move, undo);\n",
        "search.cpp hoist before make_move",
    )
    scpp = replace_once(
        scpp,
        "            if (tune::IdeaS13 && quiet) {\n"
        "                const int prep = break_prep_order(board, move);\n",
        "            if (tune::IdeaS13 && quiet) {\n"
        "                const int prep = tune::IdeaS13_Hoist ? s13_hoisted_prep : break_prep_order(board, move);\n",
        "search.cpp LMR prep read",
    )
    scpp_p.write_text(scpp, encoding="utf-8")

    # 3. src/uci.cpp
    ucpp_p = tree_dir / "src/uci.cpp"
    ucpp = ucpp_p.read_text(encoding="utf-8")
    ucpp = replace_once(
        ucpp,
        '                         "option name IdeaS13 type check default false\\n"\n',
        '                         "option name IdeaS13 type check default false\\n"\n'
        '                         "option name IdeaS13_Hoist type check default false\\n"\n',
        "uci.cpp IdeaS13_Hoist decl",
    )
    ucpp = replace_once(
        ucpp,
        '            } else if (name == "IdeaB8b") {\n'
        '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8b = value_text == "true";\n'
        '                else note_invalid();\n',
        '            } else if (name == "IdeaB8b") {\n'
        '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8b = value_text == "true";\n'
        '                else note_invalid();\n'
        '            } else if (name == "IdeaS13_Hoist") {\n'
        '                if (value_text == "true" || value_text == "false") forge::tune::IdeaS13_Hoist = value_text == "true";\n'
        '                else note_invalid();\n',
        "uci.cpp IdeaS13_Hoist setoption",
    )
    ucpp_p.write_text(ucpp, encoding="utf-8")


def inject_scratch_counter(tree_dir: pathlib.Path) -> None:
    """
    Scratch-only instrumentation on `/tmp/carbon2_job42/src_p8_counter` (NEVER on `bundle8`).
    """
    shpp_p = tree_dir / "include/forge/search.hpp"
    shpp = shpp_p.read_text(encoding="utf-8")
    shpp = replace_once(
        shpp,
        "    void reset_node_count() {\n"
        "        local_nodes_ = 0;\n"
        "        nodes_.store(0, std::memory_order_relaxed);\n"
        "    }\n",
        "    void reset_node_count() {\n"
        "        local_nodes_ = 0;\n"
        "        nodes_.store(0, std::memory_order_relaxed);\n"
        "        p8_prep_gt0_ = 0;\n"
        "        p8_shorten_gt0_ = 0;\n"
        "    }\n"
        "    std::uint64_t p8_prep_gt0_ = 0;\n"
        "    std::uint64_t p8_shorten_gt0_ = 0;\n",
        "counter search.hpp fields",
    )
    shpp_p.write_text(shpp, encoding="utf-8")

    scpp_p = tree_dir / "src/search.cpp"
    scpp = scpp_p.read_text(encoding="utf-8")
    scpp = replace_once(
        scpp,
        "            if (tune::IdeaS13 && quiet) {\n"
        "                const int prep = tune::IdeaS13_Hoist ? s13_hoisted_prep : break_prep_order(board, move);\n"
        "                if (prep > 0) {\n"
        "                    int shorten = prep / tune::IdeaS13_ReduceDivisor;\n"
        "                    if (shorten > 1) shorten = 1;\n"
        "                    r -= shorten;\n"
        "                }\n"
        "            }\n",
        "            if (tune::IdeaS13 && quiet) {\n"
        "                const int prep = tune::IdeaS13_Hoist ? s13_hoisted_prep : break_prep_order(board, move);\n"
        "                if (prep > 0) {\n"
        "                    ++p8_prep_gt0_;\n"
        "                    int shorten = prep / tune::IdeaS13_ReduceDivisor;\n"
        "                    if (shorten > 1) shorten = 1;\n"
        "                    if (shorten > 0) ++p8_shorten_gt0_;\n"
        "                    r -= shorten;\n"
        "                }\n"
        "            }\n",
        "counter search.cpp LMR increment",
    )
    scpp = replace_once(
        scpp,
        "    for (auto& helper : helpers) helper.join();\n"
        "    shared_.stop.store(external_stop, std::memory_order_relaxed);\n"
        "    return result;\n",
        "    for (auto& helper : helpers) helper.join();\n"
        "    shared_.stop.store(external_stop, std::memory_order_relaxed);\n"
        "    if (emit_info) {\n"
        "        std::uint64_t sum_prep = 0;\n"
        "        std::uint64_t sum_shorten = 0;\n"
        "        for (const Worker* w : all) {\n"
        "            sum_prep += w->p8_prep_gt0_;\n"
        "            sum_shorten += w->p8_shorten_gt0_;\n"
        "        }\n"
        "        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());\n"
        '        std::cout << "info string p8_s13_counter prep_gt0 " << sum_prep\n'
        '                  << " shorten_gt0 " << sum_shorten << std::endl;\n'
        "    }\n"
        "    return result;\n",
        "counter search.cpp emit_info print",
    )
    scpp_p.write_text(scpp, encoding="utf-8")


def run_counter_o_d12(
    counter_exe: str,
    fens: list[str],
    extra_opts: list[tuple[str, str]],
    raw_out: pathlib.Path,
    meta_out: pathlib.Path,
    cpu_pin: int = 1,
) -> None:
    opt_lines = pc20_option_lines(extra_opts)
    proc = subprocess.Popen(
        ["taskset", "-c", str(cpu_pin), counter_exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write("uci\n")
    proc.stdin.flush()
    id_name = "id name <unknown>"
    while True:
        ln = proc.stdout.readline().rstrip("\r\n")
        if ln.startswith("id name "):
            id_name = ln
        elif ln == "uciok":
            break

    proc.stdin.write("".join(o + "\n" for o in opt_lines) + "isready\n")
    proc.stdin.flush()
    while proc.stdout.readline().rstrip("\r\n") != "readyok":
        pass

    rows_txt = [
        "position\tnodes\tprep_gt0\tshorten_gt0\tbestmove\tscore",
    ]
    sum_nd = 0
    sum_pr = 0
    sum_sh = 0
    for idx, fen in enumerate(fens, start=1):
        proc.stdin.write(f"ucinewgame\nisready\nposition fen {fen}\nisready\ngo depth 12\n")
        proc.stdin.flush()
        ready_seen = 0
        while ready_seen < 2:
            if proc.stdout.readline().rstrip("\r\n") == "readyok":
                ready_seen += 1
        last_nd = None
        last_sc = ""
        prep_val = None
        sh_val = None
        bm = None
        while True:
            ln = proc.stdout.readline().rstrip("\r\n")
            if ln.startswith("bestmove "):
                bm = ln.split()[1]
                break
            if ln.startswith("info string p8_s13_counter "):
                toks = ln.split()
                prep_val = int(toks[toks.index("prep_gt0") + 1])
                sh_val = int(toks[toks.index("shorten_gt0") + 1])
            elif ln.startswith("info ") and " nodes " in ln:
                toks = ln.split()
                last_nd = int(toks[toks.index("nodes") + 1])
                if "score" in toks:
                    si = toks.index("score")
                    last_sc = f"{toks[si + 1]} {toks[si + 2]}"
        assert last_nd is not None and prep_val is not None and sh_val is not None and bm is not None
        sum_nd += last_nd
        sum_pr += prep_val
        sum_sh += sh_val
        rows_txt.append(f"{idx}\t{last_nd}\t{prep_val}\t{sh_val}\t{bm}\t{last_sc}")

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    stderr_txt = proc.stderr.read() if proc.stderr else ""
    rc = proc.wait()
    if rc != 0 or stderr_txt:
        raise RuntimeError(f"Counter exe rc={rc} stderr={stderr_txt!r}")

    hdr = f"# positions={len(fens)} depth=12 sum_nodes={sum_nd} sum_prep_gt0={sum_pr} sum_shorten_gt0={sum_sh}"
    raw_out.write_text(hdr + "\n" + "\n".join(rows_txt) + "\n", encoding="utf-8")
    meta_out.write_text(
        "\n".join(
            [
                f"exe_path: {counter_exe}",
                f"exe_sha256: {sha256_file(pathlib.Path(counter_exe))}",
                f"id_name: {id_name}",
                f"set_path: {O_FENS_PATH}",
                f"positions: {len(fens)}",
                f"sum_nodes: {sum_nd}",
                f"sum_prep_gt0: {sum_pr}",
                f"sum_shorten_gt0: {sum_sh}",
                "options_sent_begin:",
                *[f"  {o}" for o in opt_lines],
                "options_sent_end",
                f"utc_completed: {utc_now()}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    out_lines = [
        "=== JOB 42 PART P8: IdeaS13_Hoist Patch, Bundle8 Build, Known Answers, Rows, and Scratch Counter Build ===",
        f"start_utc: {utc_now()}",
        "",
    ]
    all_ok = True

    # 1. Base tree = r15d + v3 + bundle_grok7.patch.txt
    base_b7 = WORK42 / "base_r15d_v3_bundle7"
    ok_b7, _ = apply_patch_to_fresh_v3(BUNDLE7_PATCH, base_b7)
    if not ok_b7:
        raise RuntimeError("Failed applying bundle_grok7.patch.txt")

    gen_b8 = WORK42 / "gen_src_bundle8"
    if gen_b8.exists():
        shutil.rmtree(gen_b8)
    shutil.copytree(base_b7, gen_b8)
    inject_p8_hoist(gen_b8)

    patch_p8 = JOB42 / "P8_S13_hoist.patch.txt"
    generate_diff_u_patch(base_b7, gen_b8, patch_p8)

    # Verify patch applies cleanly to a fresh r15d + v3 + bundle_grok7 tree
    src_b8 = WORK42 / "src_bundle8"
    ok_b7_2, _ = apply_patch_to_fresh_v3(BUNDLE7_PATCH, src_b8)
    if not ok_b7_2:
        raise RuntimeError("Failed applying bundle_grok7 to src_bundle8")
    chk = subprocess.run(["git", "apply", "--check", "-p1", str(patch_p8)], cwd=str(src_b8), capture_output=True, text=True)
    ok_chk, s_chk = fmt_cmp("P8_S13_hoist git apply --check -p1 on r15d+v3+bundle7", chk.returncode, 0)
    all_ok = all_ok and ok_chk
    subprocess.run(["git", "apply", "-p1", str(patch_p8)], cwd=str(src_b8), check=True)

    raw_p8 = patch_p8.read_bytes()
    ok_crlf, s_crlf = fmt_cmp("P8_S13_hoist.patch.txt CRLF count", raw_p8.count(b"\r\n"), 0)
    all_ok = all_ok and ok_crlf
    p8_sha = sha256_file(patch_p8)
    p8_lines = len(raw_p8.decode("utf-8").splitlines())

    b8_exe, b8_sha, b8_cf, b8_lf = build_release_v3(src_b8, WORK42 / "bld_bundle8")
    out_lines.extend(
        [
            "--- 1. P8_S13_hoist.patch.txt & Clean Bundle8 Build ---",
            s_crlf,
            s_chk,
            f"  patch path                                  : {patch_p8}",
            f"  patch lines({patch_p8}) : {p8_lines}",
            f"  patch sha256({patch_p8}) : {p8_sha}",
            f"  bundle8 exe path                            : {b8_exe}",
            f"  bundle8 exe sha256({b8_exe}) : {b8_sha}",
            f"  bundle8 id name                             : {get_id_name(b8_exe)}",
        ]
    )

    for uopt in ["IdeaS13_Hoist", "IdeaS13", "IdeaB8b", "HindsightDepth"]:
        ok_u, u_lines = verify_uci_option_check(b8_exe, uopt)
        all_ok = all_ok and ok_u
        out_lines.extend(u_lines)

    # 2. All switches OFF = every OFF number of Step 0 + OFF O & OFF G
    out_lines.append("")
    out_lines.append("--- 2. Bundle8 All-Switches-OFF Verification ---")
    ok_off_def, off_def_l = verify_all_off_numbers("bundle8_default_off", b8_exe, None)
    ok_off_exp, off_exp_l = verify_all_off_numbers("bundle8_explicit_8_false", b8_exe, ALL_EIGHT_IDEA_FALSE)
    all_ok = all_ok and ok_off_def and ok_off_exp
    out_lines.extend(off_def_l + off_exp_l)

    nopc20_opts = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        "setoption name OwnBook value false",
        *[f"setoption name {k} value {v}" for k, v in ALL_EIGHT_IDEA_FALSE],
    ]
    b13_f = run_fresh_bench(b8_exe, 13, nopc20_opts + ["setoption name HindsightDepth value false"])
    b13_t = run_fresh_bench(b8_exe, 13, nopc20_opts + ["setoption name HindsightDepth value true"])
    ok_nf, s_nf = fmt_cmp("bundle8 no-PC20 HindsightDepth=false bench 13", b13_f, EXP_NOPC20_HD_FALSE_BENCH13)
    ok_nt, s_nt = fmt_cmp("bundle8 no-PC20 HindsightDepth=true bench 13", b13_t, EXP_NOPC20_HD_TRUE_BENCH13)
    all_ok = all_ok and ok_nf and ok_nt
    out_lines.extend([s_nf, s_nt])

    j39_off_o = read_j39_rows(JOB39 / "OFF_O_d12.rows.txt")
    j39_off_g = read_j39_rows(JOB39 / "OFF_G_d12.rows.txt")
    b8_off_o = run_epd_depth12(
        b8_exe, O_FENS_PATH, ALL_EIGHT_IDEA_FALSE,
        JOB42 / "P8_bundle8_all_off_O_d12.rows.txt",
        JOB42 / "P8_bundle8_all_off_O_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    b8_off_g = run_epd_depth12(
        b8_exe, G_EPD_PATH, ALL_EIGHT_IDEA_FALSE,
        JOB42 / "P8_bundle8_all_off_G_d12.rows.txt",
        JOB42 / "P8_bundle8_all_off_G_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    do_off, _ = diff_rows(b8_off_o, j39_off_o)
    dg_off, _ = diff_rows(b8_off_g, j39_off_g)
    ok_oo, s_oo = fmt_cmp("bundle8 OFF O equal pos vs J39 OFF O", 200 - do_off, 200)
    ok_og, s_og = fmt_cmp("bundle8 OFF G equal pos vs J39 OFF G", 353 - dg_off, 353)
    all_ok = all_ok and ok_oo and ok_og
    out_lines.extend([s_oo, s_og])

    # 3. IdeaS13_Hoist=true with IdeaS13=false == OFF O rows (200 == 200)
    out_lines.append("")
    out_lines.append("--- 3. IdeaS13_Hoist=true with IdeaS13=false Equals OFF O Rows (200 == 200) ---")
    hoist_only_opts = [(o, "true" if o == "IdeaS13_Hoist" else "false") for o in EIGHT_SWITCH_NAMES]
    hoist_only_o = run_epd_depth12(
        b8_exe, O_FENS_PATH, hoist_only_opts,
        JOB42 / "P8_bundle8_only_Hoist_S13_off_O_d12.rows.txt",
        JOB42 / "P8_bundle8_only_Hoist_S13_off_O_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    d_ho, _ = diff_rows(hoist_only_o, j39_off_o)
    ok_ho1, s_ho1 = fmt_cmp("IdeaS13_Hoist alone (IdeaS13=false) O sum vs OFF", sum(r[1] for r in hoist_only_o), EXP_OFF_O_SUM)
    ok_ho2, s_ho2 = fmt_cmp("IdeaS13_Hoist alone (IdeaS13=false) equal pos vs OFF", 200 - d_ho, 200)
    all_ok = all_ok and ok_ho1 and ok_ho2
    out_lines.extend([s_ho1, s_ho2])

    # 4. All 7 existing switches alone on (with IdeaS13_Hoist=false) == Job 39 / Job 41 O rows
    out_lines.append("")
    out_lines.append("--- 4. All 7 Existing Switches Alone ON (IdeaS13_Hoist=false) vs Job 39 / Job 41 O Rows ---")
    for short, opt_name, ref_path, exp_sum in SEVEN_SWITCH_SPECS:
        opts = [(o, "true" if o == opt_name else "false") for o in EIGHT_SWITCH_NAMES]
        rows = run_epd_depth12(
            b8_exe, O_FENS_PATH, opts,
            JOB42 / f"P8_bundle8_only_{short}_O_d12.rows.txt",
            JOB42 / f"P8_bundle8_only_{short}_O_d12.rows.txt.meta",
            depth=12, cpu_pin=1,
        )
        ref_r = read_j39_rows(ref_path)
        any_d, _ = diff_rows(rows, ref_r)
        ok1, ss1 = fmt_cmp(f"bundle8 only {opt_name} O sum", sum(r[1] for r in rows), exp_sum)
        ok2, ss2 = fmt_cmp(f"bundle8 only {opt_name} equal pos", 200 - any_d, 200)
        all_ok = all_ok and ok1 and ok2
        out_lines.extend([ss1, ss2])

    # 5. Both IdeaS13=true and IdeaS13_Hoist=true: O d12, G d12, Set A line L
    out_lines.append("")
    out_lines.append("--- 5. IdeaS13=true + IdeaS13_Hoist=true: O d12, G d12, and Set A Line L ---")
    both_s13_opts = [(o, "true" if o in ("IdeaS13", "IdeaS13_Hoist") else "false") for o in EIGHT_SWITCH_NAMES]
    s13h_o = run_epd_depth12(
        b8_exe, O_FENS_PATH, both_s13_opts,
        JOB42 / "P8_bundle8_S13_and_Hoist_O_d12.rows.txt",
        JOB42 / "P8_bundle8_S13_and_Hoist_O_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    s13h_g = run_epd_depth12(
        b8_exe, G_EPD_PATH, both_s13_opts,
        JOB42 / "P8_bundle8_S13_and_Hoist_G_d12.rows.txt",
        JOB42 / "P8_bundle8_S13_and_Hoist_G_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    j39_s13_o = read_j39_rows(JOB39 / "P4_S13_016_on_O_d12.rows.txt")
    j39_s13_g = read_j39_rows(JOB39 / "P4_S13_016_on_G_d12.rows.txt")

    any_o_vs_s13, nd_o_vs_s13 = diff_rows(s13h_o, j39_s13_o)
    bm_o_vs_s13 = sum(1 for a, b in zip(s13h_o, j39_s13_o) if a[2] != b[2])
    sc_o_vs_s13 = sum(1 for a, b in zip(s13h_o, j39_s13_o) if a[3] != b[3])

    any_o_vs_off, nd_o_vs_off = diff_rows(s13h_o, j39_off_o)
    bm_o_vs_off = sum(1 for a, b in zip(s13h_o, j39_off_o) if a[2] != b[2])
    sc_o_vs_off = sum(1 for a, b in zip(s13h_o, j39_off_o) if a[3] != b[3])

    any_g_vs_s13, nd_g_vs_s13 = diff_rows(s13h_g, j39_s13_g)
    bm_g_vs_s13 = sum(1 for a, b in zip(s13h_g, j39_s13_g) if a[2] != b[2])
    sc_g_vs_s13 = sum(1 for a, b in zip(s13h_g, j39_s13_g) if a[3] != b[3])

    any_g_vs_off, nd_g_vs_off = diff_rows(s13h_g, j39_off_g)
    bm_g_vs_off = sum(1 for a, b in zip(s13h_g, j39_off_g) if a[2] != b[2])
    sc_g_vs_off = sum(1 for a, b in zip(s13h_g, j39_off_g) if a[3] != b[3])

    res_sa = run_selfgame_set_with_options(b8_exe, "carbon2-job33-a", 200, None, both_s13_opts, cpu_pin=1)
    sa_rows_path = JOB42 / "P8_bundle8_S13_and_Hoist_SetA_L.rows.txt"
    sa_meta_path = JOB42 / "P8_bundle8_S13_and_Hoist_SetA_L.rows.txt.meta"
    write_v2_v3_rows(sa_rows_path, "Job 42 Part P8 bundle8 IdeaS13 + IdeaS13_Hoist Set A line L (built-in eval, PC20)", res_sa)
    write_seta_meta(sa_meta_path, b8_exe, both_s13_opts, res_sa)

    s13h_o_sum = sum(r[1] for r in s13h_o)
    s13h_g_sum = sum(r[1] for r in s13h_g)
    out_lines.extend(
        [
            f"  S13+Hoist O d12 sum_nodes                   : {s13h_o_sum} (S13 alone = 8077984, OFF = {EXP_OFF_O_SUM}, ratio vs OFF = {s13h_o_sum / EXP_OFF_O_SUM:.6f})",
            f"  S13+Hoist O d12 first 3 nodes               : {s13h_o[0][1]} / {s13h_o[1][1]} / {s13h_o[2][1]}",
            f"  S13+Hoist O d12 vs S13 alone (any/nd/bm/sc) : {any_o_vs_s13} / {nd_o_vs_s13} / {bm_o_vs_s13} / {sc_o_vs_s13} (of 200)",
            f"  S13+Hoist O d12 vs OFF O (any/nd/bm/sc)     : {any_o_vs_off} / {nd_o_vs_off} / {bm_o_vs_off} / {sc_o_vs_off} (of 200)",
            f"  S13+Hoist G d12 sum_nodes                   : {s13h_g_sum} (S13 alone = {sum(r[1] for r in j39_s13_g)}, OFF = {EXP_OFF_G_SUM}, ratio vs OFF = {s13h_g_sum / EXP_OFF_G_SUM:.6f})",
            f"  S13+Hoist G d12 vs S13 alone (any/nd/bm/sc) : {any_g_vs_s13} / {nd_g_vs_s13} / {bm_g_vs_s13} / {sc_g_vs_s13} (of 353)",
            f"  S13+Hoist G d12 vs OFF G (any/nd/bm/sc)     : {any_g_vs_off} / {nd_g_vs_off} / {bm_g_vs_off} / {sc_g_vs_off} (of 353)",
            f"  S13+Hoist Set A line L records / searches   : {res_sa.total_records} / {res_sa.total_searches} (OFF = {EXP_SETA_L_RECORDS})",
            f"  S13+Hoist Set A line L sum_nodes            : {res_sa.total_nodes} (OFF = {EXP_SETA_L_NODES}, ratio = {res_sa.total_nodes / EXP_SETA_L_NODES:.6f})",
            f"  S13+Hoist Set A line L sha256               : {res_sa.full_sha256} (OFF = {EXP_SETA_L_SHA})",
        ]
    )

    # 6. Scratch counter build (separate scratch copy, NEVER the bundle build)
    out_lines.append("")
    out_lines.append("--- 6. Scratch Counter Build (P8c) ---")
    src_cnt = WORK42 / "src_p8_counter"
    if src_cnt.exists():
        shutil.rmtree(src_cnt)
    shutil.copytree(src_b8, src_cnt)
    inject_scratch_counter(src_cnt)
    cnt_exe, cnt_sha, cnt_cf, cnt_lf = build_release_v3(src_cnt, WORK42 / "bld_p8_counter")
    out_lines.extend(
        [
            f"  scratch counter exe path                    : {cnt_exe}",
            f"  scratch counter exe sha256({cnt_exe}) : {cnt_sha}",
        ]
    )

    fens = load_fens(O_FENS_PATH)
    s13_only_opts = [(o, "true" if o == "IdeaS13" else "false") for o in EIGHT_SWITCH_NAMES]
    run_counter_o_d12(
        cnt_exe, fens, s13_only_opts,
        JOB42 / "P8_counter_S13_hoist_off_O_d12.raw.txt",
        JOB42 / "P8_counter_S13_hoist_off_O_d12.raw.txt.meta",
        cpu_pin=1,
    )
    run_counter_o_d12(
        cnt_exe, fens, both_s13_opts,
        JOB42 / "P8_counter_S13_hoist_on_O_d12.raw.txt",
        JOB42 / "P8_counter_S13_hoist_on_O_d12.raw.txt.meta",
        cpu_pin=1,
    )
    sum_res = subprocess.run(
        [sys.executable, str(JOB42 / "sum_p8_counters.py")],
        capture_output=True, text=True, check=False,
    )
    out_lines.extend(sum_res.stdout.strip().splitlines())
    if sum_res.returncode != 0:
        all_ok = False

    out_lines.append("")
    ok_ov, s_ov = fmt_cmp("PART P8 OVERALL", 1 if all_ok else 0, 1)
    out_lines.append(s_ov)
    out_lines.append(f"done_utc: {utc_now()}")

    (JOB42 / "partP8_summary.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    with open(JOB42 / "builds.txt", "a", encoding="utf-8") as bf:
        bf.write(
            "\n".join(
                [
                    "",
                    "=== PART P8 BUILDS ===",
                    f"Part P8 [bundle8 = r15d + v3 + bundle_grok7 + P8_S13_hoist.patch.txt]:",
                    f"   patch path = {patch_p8}",
                    f"   patch lines({patch_p8}) = {p8_lines}",
                    f"   patch sha256({patch_p8}) = {p8_sha}",
                    f"   exe path = {b8_exe}",
                    f"   exe sha256({b8_exe}) = {b8_sha}",
                    f"   id_name = {get_id_name(b8_exe)}",
                    f"   compile_flags = {b8_cf}",
                    f"   link_flags    = {b8_lf}",
                    "",
                    f"Part P8 [scratch counter build — NOT used for bundle rows or games]:",
                    f"   exe path = {cnt_exe}",
                    f"   exe sha256({cnt_exe}) = {cnt_sha}",
                    f"   id_name = {get_id_name(cnt_exe)}",
                    f"   compile_flags = {cnt_cf}",
                    f"   link_flags    = {cnt_lf}",
                    "",
                ]
            )
            + "\n"
        )

    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
