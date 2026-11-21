#!/usr/bin/env python3
"""
Job 50 Part L2 (`run_partL2.py`):
Liveness on `O` (`200` positions) at depth `12`, `PC20 + HindsightDepth=true` (other Idea switches false),
on `bundle12` (`/tmp/carbon2_job50/bld_bundle12/forge`):
1. `HdLowerWithheld = 2` alone (defaults `1, 100` for the other two)
2. `HdLowerDepth = 2` alone (defaults `1, 100` for the other two)
3. `HdLowerLoss = 167` alone (defaults `1, 1` for the other two)
4. All three together (`HdLowerWithheld = 2, HdLowerDepth = 2, HdLowerLoss = 167`)

Compares each row set against Step 0 (b)'s defaults row set (`step0_b_bundle12_HD_defaults_O_d12.rows.txt`):
node sum, positions whose node count differs, best moves that differ, scores that differ, and `LIVE` vs `DEAD`
status (`0/200` equal on all 200 positions -> `DEAD`).
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import pathlib
import sys

sys.dont_write_bytecode = True

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from j50_lib import (  # noqa: E402
    ALL_NINE_IDEA_FALSE,
    JOB50,
    O_FENS_PATH,
    PC20_OPTIONS,
    WORK50,
    count_row_diffs,
    read_j39_rows,
    run_epd_depth12_strict,
    sha256_file,
    utc_now,
)


def main() -> None:
    b12_p = WORK50 / "bld_bundle12/forge"
    if not b12_p.exists():
        raise RuntimeError(f"Missing {b12_p}")
    b12_exe = str(b12_p)

    ref_path = JOB50 / "step0_b_bundle12_HD_defaults_O_d12.rows.txt"
    if not ref_path.exists():
        raise RuntimeError(f"Missing Step 0 (b) defaults reference {ref_path}")
    ref_rows = read_j39_rows(ref_path)
    ref_sum = sum(r[1] for r in ref_rows)

    hd_base_extra = ALL_NINE_IDEA_FALSE + [("HindsightDepth", "true")]
    l2_cases: list[tuple[str, str, list[tuple[str, str]], str]] = [
        (
            "HdLowerWithheld=2",
            "HdLowerWithheld",
            [("HdLowerWithheld", "2"), ("HdLowerDepth", "1"), ("HdLowerLoss", "100")],
            "partL2_HdLowerWithheld2_O_d12.rows.txt",
        ),
        (
            "HdLowerDepth=2",
            "HdLowerDepth",
            [("HdLowerWithheld", "1"), ("HdLowerDepth", "2"), ("HdLowerLoss", "100")],
            "partL2_HdLowerDepth2_O_d12.rows.txt",
        ),
        (
            "HdLowerLoss=167",
            "HdLowerLoss",
            [("HdLowerWithheld", "1"), ("HdLowerDepth", "1"), ("HdLowerLoss", "167")],
            "partL2_HdLowerLoss167_O_d12.rows.txt",
        ),
        (
            "all_three (2, 2, 167)",
            "ALL_THREE",
            [("HdLowerWithheld", "2"), ("HdLowerDepth", "2"), ("HdLowerLoss", "167")],
            "partL2_all_three_2_2_167_O_d12.rows.txt",
        ),
    ]

    def _run_case(idx_case: tuple[int, tuple[str, str, list[tuple[str, str]], str]]):
        idx, (label, opt_key, sf_opts, fn) = idx_case
        rp = JOB50 / fn
        mp = JOB50 / f"{fn}.meta"
        rows = run_epd_depth12_strict(
            b12_exe,
            O_FENS_PATH,
            PC20_OPTIONS,
            hd_base_extra + sf_opts,
            rp,
            mp,
            depth=12,
            cpu_pin=idx % 4,
        )
        return label, opt_key, sf_opts, fn, rows

    raw_out = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        for label, opt_key, sf_opts, fn, rows in ex.map(_run_case, enumerate(l2_cases)):
            raw_out[opt_key] = (label, sf_opts, fn, rows)

    records: list[dict[str, object]] = []
    lines = [
        f"=== JOB 50 PART L2 LIVENESS ON O (200 POSITIONS, DEPTH 12, PC20 + HindsightDepth=true) ({utc_now()}) ===",
        f"defaults_ref_rows_path: {ref_path}",
        f"defaults_ref_rows_sha256({ref_path}): {sha256_file(ref_path)}",
        f"defaults_O_d12_sum_nodes (1, 1, 100): {ref_sum}",
        "",
        "Case                     | O_sum_nodes | Delta_vs_defaults | Nodes_diff/200 | Bestmove_diff/200 | Score_diff/200 | Status",
        "-" * 118,
    ]

    for _, opt_key, _, _ in l2_cases:
        label, sf_opts, fn, rows = raw_out[opt_key]
        rp = JOB50 / fn
        s_nodes = sum(r[1] for r in rows)
        delta = s_nodes - ref_sum
        cd = count_row_diffs(rows, ref_rows)
        nd_diff = int(cd["nodes_diff"])
        bm_diff = int(cd["bestmove_diff"])
        sc_diff = int(cd["score_diff"])
        exact_eq = int(cd["equal"])
        is_dead = exact_eq == len(ref_rows)
        status = "DEAD" if is_dead else "LIVE"
        rec_obj = {
            "label": label,
            "opt_key": opt_key,
            "sf_opts": sf_opts,
            "rows_file": f"forge-combo29/carbon2/job50/{fn}",
            "rows_sha256": sha256_file(rp),
            "sum_nodes": s_nodes,
            "delta_vs_defaults": delta,
            "nodes_diff_200": nd_diff,
            "bestmove_diff_200": bm_diff,
            "score_diff_200": sc_diff,
            "exact_equal_200": exact_eq,
            "status": status,
        }
        records.append(rec_obj)
        lines.append(
            f"{label:24s} | {s_nodes:11d} | {delta:+17d} | {nd_diff:10d}/200 | {bm_diff:13d}/200 | {sc_diff:10d}/200 | {status}"
        )

    live_single_opts: list[tuple[str, str]] = []
    dead_single_names: list[str] = []
    val_map = {"HdLowerWithheld": "2", "HdLowerDepth": "2", "HdLowerLoss": "167"}
    for r in records:
        k = str(r["opt_key"])
        if k in val_map:
            if r["status"] == "LIVE":
                live_single_opts.append((k, val_map[k]))
            else:
                dead_single_names.append(k)

    all_three_rec = [r for r in records if r["opt_key"] == "ALL_THREE"][0]
    all_three_dir = (
        "ABOVE"
        if int(all_three_rec["sum_nodes"]) > ref_sum
        else ("BELOW" if int(all_three_rec["sum_nodes"]) < ref_sum else "EQUAL")
    )
    lines.append("")
    lines.append(f"all_three_vs_defaults_direction: {all_three_dir} ({all_three_rec['sum_nodes']} vs {ref_sum}, delta={int(all_three_rec['delta_vs_defaults']):+d})")
    lines.append(f"live_single_options_for_M18_SideA: {live_single_opts}")
    lines.append(f"dead_single_options_excluded: {dead_single_names}")

    txt_out = "\n".join(lines) + "\n"
    print(txt_out, flush=True)
    (JOB50 / "partL2_summary.txt").write_text(txt_out, encoding="utf-8")
    (JOB50 / "partL2_status.json").write_text(
        json.dumps(
            {
                "utc": utc_now(),
                "defaults_ref_file": "forge-combo29/carbon2/job50/step0_b_bundle12_HD_defaults_O_d12.rows.txt",
                "defaults_sum_nodes": ref_sum,
                "records": records,
                "all_three_direction": all_three_dir,
                "live_single_opts": live_single_opts,
                "dead_single_names": dead_single_names,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
