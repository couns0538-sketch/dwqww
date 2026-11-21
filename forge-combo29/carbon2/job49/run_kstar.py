#!/usr/bin/env python3
"""
Job 49 Step k* (`run_kstar.py`):
Reads `D_k = Elo(M15-k) - Elo(M15-0)` for k = 1..5 directly from Job 48's committed
`M15_summary.txt` and `partL_summary.txt` (with exact file paths and 1-based line numbers,
cross-checked against `M15_results.json` and `partL_status.json`), chooses `k*`, and writes
`forge-combo29/carbon2/job49/kstar.txt` + `kstar.json`.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB48 = REPO / "forge-combo29/carbon2/job48"
JOB49 = REPO / "forge-combo29/carbon2/job49"

sys.path.insert(0, str(JOB48))
from j48_lib import LEAVE_ONE_OUT_SPECS, utc_now  # noqa: E402


def main() -> None:
    m15_sum_path = JOB48 / "M15_summary.txt"
    m15_json_path = JOB48 / "M15_results.json"
    partL_sum_path = JOB48 / "partL_summary.txt"
    partL_json_path = JOB48 / "partL_status.json"

    m15_lines = m15_sum_path.read_text(encoding="utf-8").splitlines()
    partL_lines = partL_sum_path.read_text(encoding="utf-8").splitlines()
    m15_json = {str(it["tag"]): it for it in json.loads(m15_json_path.read_text(encoding="utf-8"))}
    partL_json = json.loads(partL_json_path.read_text(encoding="utf-8"))

    # Parse M15_summary.txt summary table lines with exact 1-based line numbers
    row_re = re.compile(
        r"^\s*(M15-[0-5])\s*\|\s*([^|]+?)\s*\|\s*(COMPLETE|CUT)\s*\|\s*(\d+)\s*\|\s*([0-9-]+)\s*\|"
        r"\s*(\[[^\]]+\])\s*\|\s*([+-]?\d+\.\d+)\s*\+/-\s*(\d+\.\d+)\s*\[([^\]]+)\]\s*\|"
        r"\s*([^|]+?)\s*\|\s*(.+?)\s*$"
    )
    parsed_m15: dict[str, dict[str, object]] = {}
    for lineno, ln in enumerate(m15_lines, start=1):
        m = row_re.match(ln)
        if m:
            tag = m.group(1)
            parsed_m15[tag] = {
                "tag": tag,
                "file": str(m15_sum_path.relative_to(REPO)),
                "line": lineno,
                "raw_line": ln,
                "base_desc": m.group(2).strip(),
                "status": m.group(3).strip(),
                "games": int(m.group(4)),
                "wld": m.group(5).strip(),
                "ptnml": m.group(6).strip(),
                "elo_2dp": float(m.group(7)),
                "hw95_2dp": float(m.group(8)),
                "ci_str": m.group(9).strip(),
                "diff_col": m.group(10).strip(),
            }

    # Parse partL_summary.txt liveness lines with exact 1-based line numbers
    partL_re = re.compile(r"^\s*(L[1-5])\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|.+?\|\s*(LIVE|DEAD)\s*$")
    parsed_L: dict[str, dict[str, object]] = {}
    for lineno, ln in enumerate(partL_lines, start=1):
        m = partL_re.match(ln)
        if m:
            bkey = m.group(1)
            parsed_L[bkey] = {
                "base_key": bkey,
                "file": str(partL_sum_path.relative_to(REPO)),
                "line": lineno,
                "desc": m.group(2).strip(),
                "o_sum": int(m.group(3)),
                "status": m.group(4).strip(),
            }

    if "M15-0" not in parsed_m15:
        raise RuntimeError("M15-0 not found in M15_summary.txt")

    m0_row = parsed_m15["M15-0"]
    m0_json = m15_json["M15-0"]
    elo_0_exact = float(m0_json["elo"])

    dk_records: list[dict[str, object]] = []
    for k in range(1, 6):
        tag = f"M15-{k}"
        bkey = f"L{k}"
        if tag not in parsed_m15 or bkey not in parsed_L:
            raise RuntimeError(f"Missing {tag} or {bkey} in Job 48 summary files")
        mk_row = parsed_m15[tag]
        lk_row = parsed_L[bkey]
        mk_json = m15_json[tag]
        lk_json = partL_json[bkey]

        # Extract numeric D_k from diff_col in M15_summary.txt (e.g. "+8.01 +/- 6.96 [+1.05, +14.97]")
        dm = re.match(r"^([+-]?\d+\.\d+)\s*\+/-\s*(\d+\.\d+)\s*\[([^\]]+)\]$", str(mk_row["diff_col"]))
        if not dm:
            raise RuntimeError(f"Unexpected diff_col for {tag}: {mk_row['diff_col']!r}")
        dk_2dp = float(dm.group(1))
        dk_hw_2dp = float(dm.group(2))
        dk_ci_str = dm.group(3)
        dk_exact = float(mk_json["elo"]) - elo_0_exact

        eligible = (mk_row["status"] == "COMPLETE") and (lk_row["status"] == "LIVE") and (not bool(lk_json["is_dead"]))
        opt_name, s14_val, short_words = LEAVE_ONE_OUT_SPECS[bkey]

        dk_records.append(
            {
                "k": k,
                "tag": tag,
                "base_key": bkey,
                "switch_name": opt_name,
                "s14_value": s14_val,
                "short_words": short_words,
                "m15_file": mk_row["file"],
                "m15_line": mk_row["line"],
                "partL_file": lk_row["file"],
                "partL_line": lk_row["line"],
                "partL_status": lk_row["status"],
                "partL_o_sum": lk_row["o_sum"],
                "m15_status": mk_row["status"],
                "elo_k_2dp": mk_row["elo_2dp"],
                "elo_k_exact": float(mk_json["elo"]),
                "elo_0_2dp": m0_row["elo_2dp"],
                "elo_0_exact": elo_0_exact,
                "D_k_2dp": dk_2dp,
                "D_k_exact": dk_exact,
                "D_k_hw95_2dp": dk_hw_2dp,
                "D_k_ci_str": dk_ci_str,
                "D_k_summary_col": mk_row["diff_col"],
                "eligible": eligible,
            }
        )

    eligible_recs = [r for r in dk_records if bool(r["eligible"])]
    if m0_row["status"] == "COMPLETE" and len(eligible_recs) >= 2:
        best = max(eligible_recs, key=lambda r: float(r["D_k_exact"]))
        selection_rule_note = (
            f"M15-0 COMPLETE and {len(eligible_recs)} leave-one-out matches COMPLETE & LIVE (>= 2); "
            f"selected k* = argmax_k D_k = {best['k']} ({best['base_key']}: {best['short_words']})."
        )
    else:
        best = [r for r in dk_records if int(r["k"]) == 2][0]
        selection_rule_note = "Fallback k* = 2."

    k_star = int(best["k"])
    base_star = str(best["base_key"])
    sw_name = str(best["switch_name"])
    sw_s14 = str(best["s14_value"])
    base_in_words = (
        f"{base_star} ({best['short_words']}): PC20 with that ONE switch set to its S14 value "
        f"({sw_name} = {sw_s14} instead of PC20's HistRework = 2), every other PC20 option unchanged."
        if k_star == 2
        else f"{base_star} ({best['short_words']}): PC20 with that ONE switch set to its S14 value "
        f"({sw_name} = {sw_s14}), every other PC20 option unchanged."
    )

    out_lines = [
        "=== CARBON2 JOB 49: SELECTION OF k* FROM COMMITTED JOB 48 NUMBERS ===",
        f"generated_utc: {utc_now()}",
        "",
        "Baseline M15-0 read from:",
        f"  - {m0_row['file']}:{m0_row['line']} -> M15-0 | status={m0_row['status']} | games={m0_row['games']} | "
        f"Elo={m0_row['elo_2dp']:+.2f} +/- {m0_row['hw95_2dp']:.2f} [{m0_row['ci_str']}] (exact {elo_0_exact:+.6f} in forge-combo29/carbon2/job48/M15_results.json:21)",
        "",
        "D_k = Elo(M15-k) - Elo(M15-0) for k = 1 to 5 (each with exact file and line):",
    ]
    for r in dk_records:
        out_lines.append(
            f"  - k = {r['k']} ({r['base_key']}: {r['short_words']}): "
            f"D_{r['k']} = {r['D_k_summary_col']} (exact {float(r['D_k_exact']):+.6f} = {float(r['elo_k_exact']):+.6f} - ({elo_0_exact:+.6f})) | "
            f"Elo({r['tag']}) = {float(r['elo_k_2dp']):+.2f} ({r['m15_status']}) from {r['m15_file']}:{r['m15_line']} | "
            f"Part L status = {r['partL_status']} (O_sum={r['partL_o_sum']}) from {r['partL_file']}:{r['partL_line']}"
        )

    out_lines.extend(
        [
            "",
            f"Selection rule check: {selection_rule_note}",
            f"k* = {k_star}",
            f"L_k* = {base_in_words}",
            f"Job 48 Part L reference O rows for L_k*: forge-combo29/carbon2/job48/partL_{base_star}_all_off_O_d12.rows.txt (sum = {best['partL_o_sum']})",
        ]
    )

    (JOB49 / "kstar.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    (JOB49 / "kstar.json").write_text(
        json.dumps(
            {
                "k_star": k_star,
                "base_star": base_star,
                "switch_name": sw_name,
                "s14_value": sw_s14,
                "base_in_words": base_in_words,
                "m15_0_file": m0_row["file"],
                "m15_0_line": m0_row["line"],
                "m15_0_elo_2dp": m0_row["elo_2dp"],
                "m15_0_hw95_2dp": m0_row["hw95_2dp"],
                "m15_0_elo_exact": elo_0_exact,
                "dk_records": dk_records,
                "partL_Lk_star_o_sum": best["partL_o_sum"],
                "partL_Lk_star_o_rows_path": f"forge-combo29/carbon2/job48/partL_{base_star}_all_off_O_d12.rows.txt",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("\n".join(out_lines))


if __name__ == "__main__":
    main()
