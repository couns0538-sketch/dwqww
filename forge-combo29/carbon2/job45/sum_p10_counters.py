#!/usr/bin/env python3
"""
Job 45 Committed Counter Summing Script (`sum_p10_counters.py`):
Reads per-search counter rows from `P10a_B8b_counters_O_d12.raw.txt` (scratch counter build
on a copy of `bundle8` with `IdeaB8b=true` alone on across all 200 `O` positions at depth 12,
`PC20`, built-in eval), verifies `200 == 200` searches summed and `200 == 200` row-identity
(`nodes`, `bestmove`, `score`) against the clean `bundle8` `IdeaB8b`-alone `O` rows (`8,483,711`
nodes), and prints every counter summed over ALL 200 searches.
"""
from __future__ import annotations

import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j45_lib import EXP_B8B_O_SUM, JOB41, JOB45, diff_breakdown_with_samples, fmt_cmp, read_j39_rows, sha256_file, utc_now  # noqa: E402

COUNTER_COLS = [
    "threat_calls",
    "threat_computes",
    "cache_hits",
    "compute_present",
    "call_present",
    "trob_calls",
    "trob_from_bonus",
    "trob_from_update",
    "role_0",
    "role_1",
    "role_2",
    "role_3",
    "role_4",
    "swing_runs",
    "swing_gained_ge_40",
    "total_table_updates",
]


def main() -> int:
    raw_path = JOB45 / "P10a_B8b_counters_O_d12.raw.txt"
    clean_b8b_path = JOB45 / "step0_bundle8_only_IdeaB8b_O_d12.rows.txt"
    j41_b8b_path = JOB41 / "P7_bundle7_only_B8b_O_d12.rows.txt"

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

    clean_rows = read_j39_rows(clean_b8b_path)
    j41_rows = read_j39_rows(j41_b8b_path)
    d_clean, _ = diff_breakdown_with_samples(cmp_rows, clean_rows, "counter_B8b", "bundle8_B8b")
    d_j41, _ = diff_breakdown_with_samples(cmp_rows, j41_rows, "counter_B8b", "J41_P7_B8b")

    role_sum = (
        totals["role_0"]
        + totals["role_1"]
        + totals["role_2"]
        + totals["role_3"]
        + totals["role_4"]
    )
    node_sum = sum(r[1] for r in cmp_rows)

    all_ok = True
    checks: list[str] = []
    for lbl, got, exp in [
        ("P10a searches_summed", len(cmp_rows), 200),
        ("P10a counter node_sum vs IdeaB8b O known answer", node_sum, EXP_B8B_O_SUM),
        ("P10a counter equal_pos vs clean bundle8 IdeaB8b O", d_clean["equal"], 200),
        ("P10a counter equal_pos vs Job 41 P7 IdeaB8b O", d_j41["equal"], 200),
        ("P10a threat_calls == threat_computes + cache_hits", totals["threat_calls"], totals["threat_computes"] + totals["cache_hits"]),
        ("P10a trob_calls == call_present", totals["trob_calls"], totals["call_present"]),
        ("P10a trob_calls == trob_from_bonus + trob_from_update", totals["trob_calls"], totals["trob_from_bonus"] + totals["trob_from_update"]),
        ("P10a trob_calls == sum(role_0..role_4)", totals["trob_calls"], role_sum),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok
        checks.append(s)

    cache_hit_pct = 100.0 * totals["cache_hits"] / max(1, totals["threat_calls"])
    compute_present_pct = 100.0 * totals["compute_present"] / max(1, totals["threat_computes"])
    call_present_pct = 100.0 * totals["call_present"] / max(1, totals["threat_calls"])

    lines = [
        "=== JOB 45 PART P10a: IdeaB8b (028) COUNTER SUMMATION OVER ALL 200 O DEPTH-12 SEARCHES (sum_p10_counters.py) ===",
        f"utc: {utc_now()}",
        f"counter_raw_path: {raw_path}",
        f"counter_raw_sha256({raw_path}): {sha256_file(raw_path)}",
        f"clean_bundle8_b8b_rows_path: {clean_b8b_path}",
        f"clean_bundle8_b8b_rows_sha256({clean_b8b_path}): {sha256_file(clean_b8b_path)}",
        "",
        f"searches_summed = {len(cmp_rows)}",
        f"total_nodes     = {node_sum} (mean {node_sum / len(cmp_rows):.1f} nodes/search)",
        "",
        "--- 1. role_b8b_threat Calls, Computations, One-Key Cache Hits, and threat.present ---",
        f"  role_b8b_threat total calls                  : {totals['threat_calls']} ({totals['threat_calls'] / node_sum:.3f} / node)",
        f"  role_b8b_threat computations (cache misses)  : {totals['threat_computes']} ({100.0 - cache_hit_pct:.2f}% of calls; {totals['threat_computes'] / node_sum:.3f} / node)",
        f"  one-key cache hits (answered from cache)     : {totals['cache_hits']} ({cache_hit_pct:.2f}% of calls; {totals['cache_hits'] / node_sum:.3f} / node)",
        f"  threat.present == true on computations       : {totals['compute_present']} ({compute_present_pct:.2f}% of {totals['threat_computes']} computations)",
        f"  threat.present == true across all calls      : {totals['call_present']} ({call_present_pct:.2f}% of {totals['threat_calls']} calls)",
        "",
        "--- 2. threat_role_b8b_of Calls & Returned Roles 0..4 (called whenever threat.present == true) ---",
        f"  threat_role_b8b_of total calls               : {totals['trob_calls']} ({totals['trob_calls'] / node_sum:.3f} / node)",
        f"    from threat_role_b8b_bonus (order + qhist) : {totals['trob_from_bonus']} ({100.0 * totals['trob_from_bonus'] / max(1, totals['trob_calls']):.2f}%)",
        f"    from update_threat_role_b8b (updates)      : {totals['trob_from_update']} ({100.0 * totals['trob_from_update'] / max(1, totals['trob_calls']):.2f}%)",
        f"  role = 0 (none / other quiet under threat)   : {totals['role_0']} ({100.0 * totals['role_0'] / max(1, totals['trob_calls']):.2f}%)",
        f"  role = 1 (victim steps away: from==victim)   : {totals['role_1']} ({100.0 * totals['role_1'] / max(1, totals['trob_calls']):.2f}%)",
        f"  role = 2 (another piece blocks slider ray)   : {totals['role_2']} ({100.0 * totals['role_2'] / max(1, totals['trob_calls']):.2f}%)",
        f"  role = 3 (quiet attacks the attacker)        : {totals['role_3']} ({100.0 * totals['role_3'] / max(1, totals['trob_calls']):.2f}%)",
        f"  role = 4 (creates greater threat / check)    : {totals['role_4']} ({100.0 * totals['role_4'] / max(1, totals['trob_calls']):.2f}%)",
        "",
        "--- 3. note_role_b8b_swing & ThreatRoleHistoryB Updates ---",
        f"  note_role_b8b_swing total calls              : {totals['swing_runs']} ({totals['swing_runs'] / node_sum:.3f} / node)",
        f"  note_role_b8b_swing gained >= Swing(40)      : {totals['swing_gained_ge_40']} ({100.0 * totals['swing_gained_ge_40'] / max(1, totals['swing_runs']):.2f}% of swing calls)",
        f"  total ThreatRoleHistoryB table updates       : {totals['total_table_updates']} (cutoff + maluses + PV + swing)",
        "",
        "--- 4. Verification Checks ---",
        *checks,
    ]
    ok_ov, s_ov = fmt_cmp("P10a COUNTER SUMMATION OVERALL", 1 if all_ok else 0, 1)
    lines.append(s_ov)

    out_path = JOB45 / "P10a_counter_summary.txt"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
