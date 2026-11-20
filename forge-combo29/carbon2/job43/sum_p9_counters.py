#!/usr/bin/env python3
"""
Job 43 Committed Counter Summing Script (`sum_p9_counters.py`):
Reads per-search counter rows from `P9a_B8_counters_O_d12.raw.txt` (scratch counter build
with `IdeaB8=true` alone on across all 200 `O` positions at depth 12, `PC20`, built-in eval),
verifies `200 == 200` searches summed and `200 == 200` row-identity (`nodes`, `bestmove`, `score`)
against the clean `bundle8` `IdeaB8`-alone `O` rows (`8,262,696` nodes), and prints every counter
summed over ALL 200 searches.
"""
from __future__ import annotations

import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j43_lib import JOB39, JOB43, diff_breakdown_with_samples, fmt_cmp, read_j39_rows, sha256_file, utc_now  # noqa: E402

COUNTER_COLS = [
    "ensure_calls",
    "find_runs",
    "find_present",
    "cache_hits",
    "qtr_runs",
    "qtr_from_bonus",
    "qtr_from_update",
    "role_m1",
    "role_0",
    "role_1",
    "role_2",
    "role_3",
    "role_4",
    "swing_runs",
    "swing_gained_ge_thr",
    "swing_table_updates",
    "total_table_updates",
]


def main() -> int:
    raw_path = JOB43 / "P9a_B8_counters_O_d12.raw.txt"
    clean_b8_path = JOB43 / "P9_bundle8_only_IdeaB8_O_d12.rows.txt"
    j39_b8_path = JOB39 / "P6_B8_078_on_O_d12.rows.txt"

    cmp_rows: list[tuple[int, int, str, str]] = []
    totals = {k: 0 for k in COUNTER_COLS}

    for ln in raw_path.read_text(encoding="utf-8").splitlines():
        if not ln or ln.startswith("#") or ln.startswith("position\t"):
            continue
        parts = ln.split("\t")
        pos = int(parts[0])
        nodes = int(parts[1])
        bm = parts[2]
        sc = parts[3]
        cmp_rows.append((pos, nodes, bm, sc))
        vals = [int(x) for x in parts[4:]]
        assert len(vals) == len(COUNTER_COLS), f"Expected {len(COUNTER_COLS)} counter cols, got {len(vals)}"
        for k, v in zip(COUNTER_COLS, vals):
            totals[k] += v

    clean_rows = read_j39_rows(clean_b8_path)
    j39_rows = read_j39_rows(j39_b8_path)
    d_clean, _ = diff_breakdown_with_samples(cmp_rows, clean_rows, "counter_B8", "bundle8_B8")
    d_j39, _ = diff_breakdown_with_samples(cmp_rows, j39_rows, "counter_B8", "J39_P6_B8")

    role_sum = (
        totals["role_m1"]
        + totals["role_0"]
        + totals["role_1"]
        + totals["role_2"]
        + totals["role_3"]
        + totals["role_4"]
    )
    node_sum = sum(r[1] for r in cmp_rows)

    all_ok = True
    checks: list[str] = []
    for lbl, got, exp in [
        ("P9a searches_summed", len(cmp_rows), 200),
        ("P9a counter node_sum vs IdeaB8 O known answer", node_sum, 8262696),
        ("P9a counter equal_pos vs clean bundle8 IdeaB8 O", d_clean["equal"], 200),
        ("P9a counter equal_pos vs Job 39 P6 IdeaB8 O", d_j39["equal"], 200),
        ("P9a ensure_calls == find_runs + cache_hits", totals["ensure_calls"], totals["find_runs"] + totals["cache_hits"]),
        ("P9a qtr_runs == qtr_from_bonus + qtr_from_update", totals["qtr_runs"], totals["qtr_from_bonus"] + totals["qtr_from_update"]),
        ("P9a qtr_runs == sum(role_-1..role_4)", totals["qtr_runs"], role_sum),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok
        checks.append(s)

    cache_hit_pct = 100.0 * totals["cache_hits"] / max(1, totals["ensure_calls"])
    present_pct = 100.0 * totals["find_present"] / max(1, totals["find_runs"])

    lines = [
        "=== JOB 43 PART P9a: IdeaB8 (078) COUNTER SUMMATION OVER ALL O DEPTH-12 SEARCHES (sum_p9_counters.py) ===",
        f"utc: {utc_now()}",
        f"counter_raw_path: {raw_path}",
        f"counter_raw_sha256({raw_path}): {sha256_file(raw_path)}",
        f"clean_bundle8_b8_rows_path: {clean_b8_path}",
        f"clean_bundle8_b8_rows_sha256({clean_b8_path}): {sha256_file(clean_b8_path)}",
        "",
        f"searches_summed = {len(cmp_rows)}",
        f"total_nodes     = {node_sum} (mean {node_sum / len(cmp_rows):.1f} nodes/search)",
        "",
        "--- 1. find_role_threat & Per-Worker Cache (ensure_role_threat) ---",
        f"  ensure_role_threat total calls       : {totals['ensure_calls']} ({totals['ensure_calls'] / node_sum:.3f} / node)",
        f"  find_role_threat runs (cache misses) : {totals['find_runs']} ({100.0 - cache_hit_pct:.2f}% of ensure calls; {totals['find_runs'] / node_sum:.3f} / node)",
        f"    of which threat.present == true    : {totals['find_present']} ({present_pct:.2f}% of find_role_threat runs)",
        f"  per-Worker cache hits (answered)     : {totals['cache_hits']} ({cache_hit_pct:.2f}% of ensure calls; {totals['cache_hits'] / node_sum:.3f} / node)",
        "",
        "--- 2. quiet_threat_role Calls & Returned Role Distribution (-1, 0..4) ---",
        f"  quiet_threat_role total runs         : {totals['qtr_runs']} ({totals['qtr_runs'] / node_sum:.3f} / node)",
        f"    from threat_role_bonus             : {totals['qtr_from_bonus']} ({100.0 * totals['qtr_from_bonus'] / max(1, totals['qtr_runs']):.2f}%)",
        f"    from update_threat_role            : {totals['qtr_from_update']} ({100.0 * totals['qtr_from_update'] / max(1, totals['qtr_runs']):.2f}%)",
        f"  role = -1 (no threat)                : {totals['role_m1']} ({100.0 * totals['role_m1'] / max(1, totals['qtr_runs']):.2f}%)",
        f"  role =  0 (step away: from==victim)  : {totals['role_0']} ({100.0 * totals['role_0'] / max(1, totals['qtr_runs']):.2f}%)",
        f"  role =  1 (block slider ray)         : {totals['role_1']} ({100.0 * totals['role_1'] / max(1, totals['qtr_runs']):.2f}%)",
        f"  role =  2 (counter-attack attacker)  : {totals['role_2']} ({100.0 * totals['role_2'] / max(1, totals['qtr_runs']):.2f}%)",
        f"  role =  3 (counter-attack dearer)    : {totals['role_3']} ({100.0 * totals['role_3'] / max(1, totals['qtr_runs']):.2f}%)",
        f"  role =  4 (other quiet under threat) : {totals['role_4']} ({100.0 * totals['role_4'] / max(1, totals['qtr_runs']):.2f}%)",
        "",
        "--- 3. note_threat_swing Calls & Table Updates ---",
        f"  note_threat_swing total runs         : {totals['swing_runs']} ({totals['swing_runs'] / node_sum:.3f} / node)",
        f"  note_threat_swing gained >= Swing(48): {totals['swing_gained_ge_thr']} ({100.0 * totals['swing_gained_ge_thr'] / max(1, totals['swing_runs']):.2f}% of swing runs)",
        f"  note_threat_swing table updates      : {totals['swing_table_updates']} ({100.0 * totals['swing_table_updates'] / max(1, totals['swing_runs']):.2f}% of swing runs)",
        f"  all-callers ThreatRoleHistory updates: {totals['total_table_updates']} (cutoff/malus/PV + swing)",
        "",
        "--- 4. Verification Checks ---",
        *checks,
    ]
    ok_ov, s_ov = fmt_cmp("P9a COUNTER SUMMATION OVERALL", 1 if all_ok else 0, 1)
    lines.append(s_ov)

    out_path = JOB43 / "P9a_counter_summary.txt"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
