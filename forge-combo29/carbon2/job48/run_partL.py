#!/usr/bin/env python3
"""
Job 48 Part L (`run_partL.py`): LIVENESS OF EACH OF THE PC'S FIVE SWITCHES (Leave-One-Out).
Bases L1..L5 = PC20 with ONE switch set to its S14 value, every Idea switch and HindsightDepth off:
  L1: CuckooRep false
  L2: HistRework 0
  L3: TtPruneV2 false
  L4: CorrHistV2 false
  L5: MateAlphaGuard false
Runs each on O (200) and G (353) at depth 12 (Threads 1, Hash 16, ucinewgame before every position).
Compares against Job 46 Step 0 PC20 all-off rows (`step0_bundle9_all_off_O_d12.rows.txt`, `step0_bundle9_all_off_G_d12.rows.txt`).
Marks any base equal on all 553 positions as DEAD (so its match in M15 is skipped).
Also verifies the whole-set known answer: all five at S14 values = S14 all off = O 9,500,069.
"""
from __future__ import annotations

import concurrent.futures
import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j48_lib import (  # noqa: E402
    ALL_TEN_FALSE,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_S14_OFF_O_SUM,
    G_EPD_PATH,
    JOB46,
    JOB48,
    LEAVE_ONE_OUT_SPECS,
    O_FENS_PATH,
    S14_EXPLICIT_OPTIONS,
    count_row_diffs,
    ensure_bundle9_exe,
    fmt_cmp,
    make_leave_one_out_options,
    read_j39_rows,
    run_epd_depth12_strict,
    utc_now,
)


def main() -> int:
    b9_exe, b9_sha, _ = ensure_bundle9_exe()
    j46_po = read_j39_rows(JOB46 / "step0_bundle9_all_off_O_d12.rows.txt")
    j46_pg = read_j39_rows(JOB46 / "step0_bundle9_all_off_G_d12.rows.txt")

    start_u = utc_now()
    tasks: list[tuple[str, str, pathlib.Path, list[tuple[str, str]], pathlib.Path, int]] = []
    base_keys = ["L1", "L2", "L3", "L4", "L5"]
    slot = 0
    for bk in base_keys:
        base_opts = make_leave_one_out_options(bk)
        o_out = JOB48 / f"partL_{bk}_all_off_O_d12.rows.txt"
        g_out = JOB48 / f"partL_{bk}_all_off_G_d12.rows.txt"
        tasks.append((bk, "O", O_FENS_PATH, base_opts, o_out, (slot % 4)))
        slot += 1
        tasks.append((bk, "G", G_EPD_PATH, base_opts, g_out, (slot % 4)))
        slot += 1

    results: dict[tuple[str, str], list[tuple[int, int, str, str]]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futs = {
            pool.submit(
                run_epd_depth12_strict,
                b9_exe,
                epd_p,
                b_opts,
                ALL_TEN_FALSE,
                out_p,
                pathlib.Path(str(out_p) + ".meta"),
                12,
                pin,
            ): (bk, sname)
            for bk, sname, epd_p, b_opts, out_p, pin in tasks
        }
        for fut, key in futs.items():
            results[key] = fut.result()

    # Also verify whole-set S14 all-off O known answer (9,500,069)
    s14_o_rows = read_j39_rows(JOB48 / "step0_bundle9_S14_all_off_O_d12.rows.txt")
    s14_o_sum = sum(r[1] for r in s14_o_rows)

    lines: list[str] = [
        "=== JOB 48 PART L: LEAVE-ONE-OUT LIVENESS OF EACH PC20 SWITCH ON O (200) AND G (353) AT DEPTH 12 ===",
        f"start_utc: {start_u}",
        f"exe_path: {b9_exe}",
        f"exe_sha256({b9_exe}): {b9_sha}",
        f"reference_PC20_all_off_O: {JOB46 / 'step0_bundle9_all_off_O_d12.rows.txt'} (sum={EXP_OFF_O_SUM})",
        f"reference_PC20_all_off_G: {JOB46 / 'step0_bundle9_all_off_G_d12.rows.txt'} (sum={EXP_OFF_G_SUM})",
        "",
    ]

    ok_s14, s_s14 = fmt_cmp("Whole-set known answer (all 5 switches at S14 values) O d12 sum", s14_o_sum, EXP_S14_OFF_O_SUM)
    lines.append(s_s14)
    lines.append("")
    lines.append(
        "  base | switch_left_out      |     O_sum | O_delta   | O_nd/200 | O_bm/200 | O_sc/200 |     G_sum | G_delta   | G_nd/353 | G_bm/353 | G_sc/353 | eq_553 | status"
    )
    lines.append(
        "  -----+----------------------+-----------+-----------+----------+----------+----------+-----------+-----------+----------+----------+----------+--------+-------"
    )

    status_json: dict[str, dict[str, object]] = {}
    dead_bases: list[str] = []
    live_bases: list[str] = []

    for bk in base_keys:
        _, _, desc = LEAVE_ONE_OUT_SPECS[bk]
        ro = results[(bk, "O")]
        rg = results[(bk, "G")]
        co = count_row_diffs(ro, j46_po)
        cg = count_row_diffs(rg, j46_pg)
        eq_553 = co["equal"] + cg["equal"]
        is_dead = eq_553 == 553
        st_label = "DEAD" if is_dead else "LIVE"
        if is_dead:
            dead_bases.append(bk)
        else:
            live_bases.append(bk)

        status_json[bk] = {
            "desc": desc,
            "o_sum": co["sum_a"],
            "o_delta": co["sum_a"] - co["sum_b"],
            "o_nodes_diff": co["nodes_diff"],
            "o_bm_diff": co["bestmove_diff"],
            "o_sc_diff": co["score_diff"],
            "o_equal": co["equal"],
            "g_sum": cg["sum_a"],
            "g_delta": cg["sum_a"] - cg["sum_b"],
            "g_nodes_diff": cg["nodes_diff"],
            "g_bm_diff": cg["bestmove_diff"],
            "g_sc_diff": cg["score_diff"],
            "g_equal": cg["equal"],
            "eq_553": eq_553,
            "is_dead": is_dead,
            "status": st_label,
        }

        lines.append(
            f"  {bk:<4s} | {desc:<20s} | {co['sum_a']:>9d} | {co['sum_a'] - co['sum_b']:>+9d} | "
            f"{co['nodes_diff']:>8d} | {co['bestmove_diff']:>8d} | {co['score_diff']:>8d} | "
            f"{cg['sum_a']:>9d} | {cg['sum_a'] - cg['sum_b']:>+9d} | "
            f"{cg['nodes_diff']:>8d} | {cg['bestmove_diff']:>8d} | {cg['score_diff']:>8d} | "
            f"{eq_553:>6d} | {st_label}"
        )

    lines.append("")
    lines.append(f"  LIVE bases (matches WILL be played in Part M15): {live_bases if live_bases else 'none'}")
    if dead_bases:
        for db in dead_bases:
            dinfo = status_json[db]
            lines.append(
                f"  DEAD base (match M15-{db[1]} NOT played): {db} ({dinfo['desc']}) equaled PC20 all off on 553/553 positions "
                f"(O sum = {dinfo['o_sum']} vs {EXP_OFF_O_SUM}; G sum = {dinfo['g_sum']} vs {EXP_OFF_G_SUM})."
            )
    else:
        lines.append("  DEAD bases: none (0 of 5 bases equaled PC20 all off on all 553 positions; all 6 matches M15-0..M15-5 are eligible).")

    lines.append("")
    ok_ov, s_ov = fmt_cmp("PART L OVERALL", 1 if ok_s14 else 0, 1)
    lines.append(s_ov)
    lines.append(f"done_utc: {utc_now()}")

    out_txt = "\n".join(lines) + "\n"
    (JOB48 / "partL_summary.txt").write_text(out_txt, encoding="utf-8")
    (JOB48 / "partL_status.json").write_text(json.dumps(status_json, indent=2) + "\n", encoding="utf-8")
    print(out_txt, flush=True)
    return 0 if ok_s14 else 1


if __name__ == "__main__":
    raise SystemExit(main())
