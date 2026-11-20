#!/usr/bin/env python3
"""
Job 42 Committed Counter Summing Script (`sum_p8_counters.py`):
Reads per-position counter rows from the scratch counter build (`P8_counter_S13_hoist_off_O_d12.raw.txt`
and `P8_counter_S13_hoist_on_O_d12.raw.txt`), verifies `200 == 200` searches summed and `200 == 200`
row-identity against the clean `bundle8` `O` depth-12 rows, verifies `0 == 0` on every position when
`IdeaS13_Hoist=false`, and prints total counts summed across all searches.
"""
from __future__ import annotations

import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j42_lib import JOB39, JOB42, diff_rows, fmt_cmp, read_j39_rows, sha256_file, utc_now  # noqa: E402


def parse_counter_raw(path: pathlib.Path) -> tuple[list[tuple[int, int, str, str]], list[int], list[int]]:
    cmp_rows: list[tuple[int, int, str, str]] = []
    prep_gt0: list[int] = []
    shorten_gt0: list[int] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not ln or ln.startswith("#") or ln.startswith("position\t"):
            continue
        pos_s, nd_s, prep_s, sh_s, bm, sc = ln.split("\t")
        cmp_rows.append((int(pos_s), int(nd_s), bm, sc))
        prep_gt0.append(int(prep_s))
        shorten_gt0.append(int(sh_s))
    return cmp_rows, prep_gt0, shorten_gt0


def main() -> int:
    off_raw = JOB42 / "P8_counter_S13_hoist_off_O_d12.raw.txt"
    on_raw = JOB42 / "P8_counter_S13_hoist_on_O_d12.raw.txt"

    ref_s13_only = read_j39_rows(JOB39 / "P4_S13_016_on_O_d12.rows.txt")
    ref_s13_hoist = read_j39_rows(JOB42 / "P8_bundle8_S13_and_Hoist_O_d12.rows.txt")

    off_cmp, off_prep, off_sh = parse_counter_raw(off_raw)
    on_cmp, on_prep, on_sh = parse_counter_raw(on_raw)

    d_off, _ = diff_rows(off_cmp, ref_s13_only)
    d_on, _ = diff_rows(on_cmp, ref_s13_hoist)

    all_ok = True
    checks: list[str] = []
    for lbl, got, exp in [
        ("hoist_off searches_summed", len(off_prep), 200),
        ("hoist_on searches_summed", len(on_prep), 200),
        ("hoist_off equal_pos vs J39 P4 (S13 alone)", 200 - d_off, 200),
        ("hoist_on equal_pos vs clean bundle8 S13+Hoist", 200 - d_on, 200),
        ("hoist_off total prep_gt0", sum(off_prep), 0),
        ("hoist_off max_per_pos prep_gt0", max(off_prep), 0),
        ("hoist_off positions_with_prep_gt0", sum(1 for x in off_prep if x > 0), 0),
        ("hoist_off total shorten_gt0", sum(off_sh), 0),
        ("hoist_on prep_gt0 > 0 on >= 1 position", sum(1 for x in on_prep if x > 0) >= 1, True),
        ("hoist_on shorten_gt0 > 0 on >= 1 position", sum(1 for x in on_sh if x > 0) >= 1, True),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok
        checks.append(s)

    lines = [
        "=== JOB 42 PART P8c COUNTER SUMMATION (Committed Script sum_p8_counters.py) ===",
        f"utc: {utc_now()}",
        f"hoist_off_raw_path: {off_raw}",
        f"hoist_off_raw_sha256({off_raw}): {sha256_file(off_raw)}",
        f"hoist_on_raw_path : {on_raw}",
        f"hoist_on_raw_sha256({on_raw}) : {sha256_file(on_raw)}",
        "",
        "--- Totals Summed Over All Searches ---",
        f"  hoist_off (IdeaS13=true, IdeaS13_Hoist=false): searches_summed = {len(off_prep)} | "
        f"node_sum = {sum(r[1] for r in off_cmp)} | total_prep_gt0 = {sum(off_prep)} | "
        f"positions_with_prep_gt0 = {sum(1 for x in off_prep if x > 0)} / {len(off_prep)} | "
        f"total_shorten_gt0 (prep >= 1024) = {sum(off_sh)} | "
        f"positions_with_shorten_gt0 = {sum(1 for x in off_sh if x > 0)} / {len(off_sh)}",
        f"  hoist_on  (IdeaS13=true, IdeaS13_Hoist=true) : searches_summed = {len(on_prep)} | "
        f"node_sum = {sum(r[1] for r in on_cmp)} | total_prep_gt0 = {sum(on_prep)} | "
        f"positions_with_prep_gt0 = {sum(1 for x in on_prep if x > 0)} / {len(on_prep)} | "
        f"total_shorten_gt0 (prep >= 1024) = {sum(on_sh)} | "
        f"positions_with_shorten_gt0 = {sum(1 for x in on_sh if x > 0)} / {len(on_sh)}",
        "",
        "--- Verification Checks ---",
        *checks,
    ]
    ok_ov, s_ov = fmt_cmp("COUNTER SUMMATION OVERALL", 1 if all_ok else 0, 1)
    lines.append(s_ov)

    out_path = JOB42 / "P8_counter_summary.txt"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
