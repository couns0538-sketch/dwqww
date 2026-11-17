"""Regenerate every table in FINDINGS.md from the evidence JSON.

Run from anywhere: the paths are anchored to this file, so the verdict does not
depend on the working directory (forge-findings.md 6: "a verdict that depends on
where you stand is not a verdict").

  python3 scripts/make_tables.py            # print all tables
  python3 scripts/make_tables.py --write    # rewrite the TABLES block in FINDINGS.md

Every table asserts the number of rows it consumed, so a silently truncated
parse fails loudly instead of printing a plausible partial table.
"""

import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVIDENCE = os.path.join(ROOT, "evidence")
FINDINGS = os.path.join(ROOT, "FINDINGS.md")

BEGIN = "<!-- BEGIN GENERATED TABLES -->"
END = "<!-- END GENERATED TABLES -->"


def load_all():
    data = {}
    for path in sorted(glob.glob(os.path.join(EVIDENCE, "probe*_results.json"))):
        with open(path) as fh:
            data.update(json.load(fh))
    if not data:
        sys.exit("FAIL: no evidence JSON found in %s" % EVIDENCE)
    return data


def need(data, key, n):
    """Fetch a result list and assert its length. A short list is a failure."""
    if key not in data:
        sys.exit("FAIL: missing evidence key %r" % key)
    rows = data[key]
    if isinstance(rows, dict):
        rows = rows.get("rows", rows)
    if not isinstance(rows, list):
        sys.exit("FAIL: %r is not a list" % key)
    if len(rows) != n:
        sys.exit("FAIL: %r has %d rows, expected %d" % (key, len(rows), n))
    return rows


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join("" if c is None else str(c) for c in r) + " |")
    return "\n".join(out)


def build(data):
    """Tables in the order the prose numbers them (T1..T14)."""
    parts = []

    # T1 — hit->best across clocks, fixed 2 s ponder, plus the duration sweep.
    def plan(clock):
        usable = clock - 10
        soft = usable // 22
        return soft, min(usable * 60 // 100, soft * 5)

    t1 = []
    for r in need(data, "f_three_clocks", 3):
        t1.append([r["clock"], r["planned_soft_ms"], r["planned_hard_ms"],
                   int(r["ponder_s"] * 1000), f"**{r['t_hit_to_best_ms']}**"])
    for key in ("a_ponder_duration_sweep_2000", "a_ponder_duration_sweep_10000"):
        for r in need(data, key, 4):
            soft, hard = plan(r["clock"])
            t1.append([r["clock"], soft, hard, int(r["ponder_s"] * 1000),
                       r["t_hit_to_best_ms"]])
    parts.append("#### T1 — wall time from `ponderhit` to `bestmove`\n\n"
                 "The first three rows are the apples-to-apples comparison (fixed 2 s "
                 "ponder). The rest sweep the ponder length at one clock: if the budget "
                 "were measured from `go`, these would fall as the ponder grows.\n\n" +
                 table(["clock (ms)", "soft", "hard", "ponder (ms)", "hit → bestmove (ms)"], t1))

    # T2 — the 16-offset upper bound. The discriminator.
    q = data["q_budget_upper_bound"]
    t2 = []
    for r in need(data, "q_budget_upper_bound", 16):
        t2.append([r["clock"], r["soft_ms"], r["hard_ms"], int(r["ponder_s"] * 1000),
                   f"**{r['t_hit_to_best_ms']}**", r["over_hard_ms"],
                   r["iterations_after_hit"]])
    s = q["summary"]
    parts.append("#### T2 — the budget-origin discriminator (16 offsets)\n\n"
                 "If the budget were measured from the original `go`, any ponder longer "
                 "than `hard` would leave nothing and `hit→best` would be ~0 ms. The "
                 "`hit→best − hard` column is the test; the last column shows most rows "
                 "stop at the end of an iteration, well below the cap.\n\n" +
                 table(["clock", "soft", "hard", "ponder (ms)", "hit→best (ms)",
                        "hit→best − hard (ms)", "iterations after hit"], t2) +
                 "\n\n"
                 f"**n = {s['n']}. Max `hit→best − hard` = {s['max_over_hard_ms']} ms. "
                 f"Rows that stopped at ~0 ms (the 'budget already spent' prediction): "
                 f"{s['n_zero_ms']}.**")

    # T3 — the extreme offsets: ponder far past the whole budget.
    t3 = []
    for r in need(data, "n1_node_growth_after_hit", 4):
        t3.append([r["clock"], r["planned_hard_ms"], r["ponder_ms"], r["ponder_over_hard"],
                   f"**{r['t_hit_to_best_ms']}**", r["hit_to_best_over_hard"]])
    parts.append("#### T3 — ponder far past the whole planned budget\n\n"
                 "A 6 s ponder against a 225 ms hard limit is 26.7× over at the hit. "
                 "The prediction of a `go`-based budget is `hit→best ≈ 0`.\n\n" +
                 table(["clock", "hard", "ponder (ms)", "ponder / hard", "hit→best (ms)",
                        "hit→best / hard"], t3))

    # T4 — the no-ponder control.
    t4 = []
    for r in need(data, "p1_control_no_ponder", 6):
        t4.append([r["clock"][0], r["t_go_to_best_ms"], r["depth_at_best"],
                   r["last_info_time_ms"], r["bestmove"], r["bestmove_count"]])
    parts.append("#### T4 — control: the same clocks with no ponder at all\n\n" +
                 table(["clock", "go→best (ms)", "depth", "last info `time` (ms)",
                        "bestmove", "bestmove lines"], t4))

    # T5 — stop without ponderhit.
    t5 = []
    for r in need(data, "p2_stop_without_hit", 4):
        t5.append([f"`{r['case']}`", r["depth_before_stop"], r["info_before_stop"],
                   r["bestmove"], r["bestmove_is_0000"], r["t_stop_to_best_ms"],
                   r["bestmove_equals_last_pv"]])
    parts.append("#### T5 — `go ponder` then `stop`, no `ponderhit`\n\n" +
                 table(["case", "depth before stop", "info lines", "bestmove", "is `0000`",
                        "stop→best (ms)", "= last info PV"], t5))

    # T6 — stop returns the found move.
    n2 = data["n2_stop_returns_found_move"]
    parts.append("#### T6 — is the `stop` reply the move the search had found?\n\n"
                 f"**{n2['agree']} of {n2['total']}** stop replies equal the PV head of the "
                 "last info line before the `bestmove` (6 positions × 3 ponder lengths). "
                 "The comparison is against the last info line that arrived *before the "
                 "bestmove*, not the last one the harness had read when it sent `stop`: an "
                 "iteration can complete in that gap, and the first version of this probe "
                 "scored one such case (endgame, 400 ms) as a disagreement.")

    # T7 — the two unbounded regimes.
    t7 = []
    for r in need(data, "p_regime", 4):
        t7.append([f"`{r['go_line']}`", f"**{r['regime']}**", r["cpu_at_horizon"],
                   r["depth_rose_after_8s"], r["bestmoves_during_horizon"],
                   r["stop_returns_bestmove"], r["t_stop_to_best_ms"]])
    parts.append("#### T7 — is a clocked ponder bounded? (20 s horizon, no `ponderhit`)\n\n" +
                 table(["go", "regime", "CPU% at horizon", "depth still rising",
                        "bestmoves emitted", "`stop` returns", "stop→best (ms)"], t7))

    # T8 — the stray ponderhit, with its control.
    t8 = []
    for r in need(data, "p4_stray_ponderhit", 5):
        if r.get("case", "").startswith("CONTROL"):
            t8.append(["**control: live ponder**", "—", "—",
                       f"**converted, {r['t_hit_to_best_ms']} ms**", "—"])
            continue
        t8.append([f"`{r['case']}`", r["said_anything"], r["quiet_within_2s"],
                   "responsive (`readyok`)" if r["alive_after"] else "NOT RESPONSIVE",
                   r.get("second_ponderhit_output")])
    parts.append("#### T8 — `ponderhit` when no ponder search is running\n\n"
                 "The last row is the control that makes the other four meaningful.\n\n" +
                 table(["state", "emitted anything", "silent within 2 s", "after",
                        "second `ponderhit`"], t8))

    # T9 — the Ponder option.
    t9 = []
    for r in need(data, "d_ponder_option_path", 2):
        t9.append([r["Ponder"], f"`{r['bestmove_line']}`",
                   "**present**" if r["suffix_present"] else "absent",
                   f"**{r['nodes']}**", "not tested", r["depth"]])
    for r in need(data, "g_self_ponder", 2):
        # Suffix presence is read from the line itself, not restated.
        has_suffix = " ponder " in r["bestmove_line"]
        t9.append([f"{r['Ponder']}, then 3 s silence",
                   f"`{r['bestmove_line']}`",
                   "**present**" if has_suffix else "absent",
                   "—",
                   "**yes**" if r["lines_after_bestmove"] else "no",
                   f"{r['t_bestmove_ms']} ms"])
    # Does the option gate the `go ponder` TOKEN? (null, with both arms run)
    tok = {r["case"]: r for r in need(data, "p6_output_shape", 7)
           if r["case"].startswith("go_ponder_token")}
    t9.append(["false, `go ponder` cycle", "—", "—", "—", "no",
               f"**{tok['go_ponder_token_with_Ponder_false']['t_hit_to_best_ms']}**"])
    t9.append(["true, `go ponder` cycle", "—", "—", "—", "no",
               f"**{tok['go_ponder_token_with_Ponder_true']['t_hit_to_best_ms']}**"])
    parts.append("#### T9 — what the `Ponder` option changes\n\n"
                 "Rows 1–2 are the same depth-8 search under both settings: the node "
                 "counts are identical, so the null on \"does it change the search\" is a "
                 "measured equality. Rows 3–4 test self-pondering — after `bestmove`, "
                 "3 s of silence was required, so an engine that began pondering on its "
                 "own would have shown info lines there. Rows 5–6 show the `go ponder` "
                 "token behaving identically with the option off, so the option does not "
                 "gate the protocol.\n\n" +
                 table(["Ponder", "bestmove line", "` ponder` suffix", "nodes",
                        "self-ponder after bestmove", "depth / hit→best (ms)"], t9))

    # T10 — output shape.
    t10 = []
    for r in need(data, "p6_output_shape", 7):
        if "bestmove_count_total" in r:
            t10.append([f"`{r['case']}`",
                        f"{r['info_lines_before_hit']} in {r['info_ms_before_hit']} ms "
                        f"({r['info_per_s']}/s)",
                        r["bestmove_count_total"], len(r["lines_after_bestmove"])])
        elif "bestmove_count" in r:
            t10.append([f"`{r['case']}`", "—", r["bestmove_count"],
                        len(r.get("lines_after_last_bestmove") or [])])
    parts.append("#### T10 — output shape while pondering, and `bestmove` uniqueness\n\n"
                 "The four command-race cases are the ones that could plausibly emit twice.\n\n" +
                 table(["case", "info while pondering", "bestmove lines", "lines after"], t10))

    # T11 — the two clocks.
    t11 = []
    for r in need(data, "p_time_disagreement", 3):
        t11.append([r["clock"], int(r["ponder_s"] * 1000), r["planned_hard_ms"],
                    f"**{r['info_time_at_best_ms']}**",
                    f"**{r['wall_from_ponderhit_ms']}**",
                    r["info_time_at_best_ms"] - int(r["wall_from_ponderhit_ms"])])
    parts.append("#### T11 — two clocks in one process\n\n"
                 "The `info` `time` field counts from `go`; the stop decision counts from "
                 "`ponderhit`. The last column is the gap, which equals the ponder length.\n\n" +
                 table(["clock", "ponder (ms)", "hard", "info `time` at best (ms)",
                        "wall from `ponderhit` (ms)", "`time` − wall (ms)"], t11))

    # T12 — zero-ms stop vs the EOF artifact.
    t12 = []
    for r in need(data, "n4_zero_stop_vs_eof", 2):
        t12.append([r["pos"], r["perft1_first_legal"], f"`{r['zero_ms_stop']}`",
                    f"`{r['immediate_eof']}`", f"`{r['eof_after_300ms']}`",
                    f"**{r['zero_stop_equals_immediate_eof']}**", r["zero_stop_is_0000"]])
    parts.append("#### T12 — the zero-ms `stop` reply, against the piped-abort artifact\n\n" +
                 table(["position", "first legal (perft 1)", "`stop` at 0 ms",
                        "immediate EOF", "EOF after 300 ms", "identical", "is `0000`"], t12))

    # T13 — suffix legality.
    rows7 = need(data, "o_ponder_suffix", 14)
    legal = sum(1 for r in rows7 if r.get("suffix") == "LEGAL")
    parts.append("#### T13 — the `ponder` suffix is load-bearing, so it is checked\n\n"
                 f"{legal} of {len(rows7)} bestmove lines carried a suffix, and every one was "
                 f"legal in the position after the best move (verified against the engine's own "
                 f"`go perft 1` move list, not an external library). "
                 f"{data['suffix_absent']} had no suffix — both on a mate-in-one root, where "
                 f"the PV has length 1. {data['illegal_or_zero']} were illegal or `0000`.")

    # T14 — the desync.
    t14 = []
    for r in need(data, "m_desync", 2):
        moves = ", ".join(f"`{b['move']}` @ {b['t_rel_second_go_ms']:.1f}" for b in r["bestmoves"])
        t14.append(["yes" if r["stop_first"] else "**no**", r["bestmove_count"], moves,
                    "no" if r["stop_first"] else "**yes**"])
    parts.append("#### T14 — runner desync when the next ponder starts without `stop`\n\n"
                 "Timestamps are ms relative to the second `go ponder`; a negative value "
                 "means the line arrived before it.\n\n" +
                 table(["`stop` before restart", "bestmove lines", "moves @ ms",
                        "ambiguous to a runner"], t14))

    # T15 — terminal root info flood.
    t15 = []
    for r in need(data, "n5_terminal_root", 1):
        t15.append([r["info_lines_during_ponder"], f"1 → {r['max_depth_during_ponder']}",
                    r["nodes_reported_at_max_depth"], "within 0.5 ms of `go`",
                    r["bestmove_withheld_during_ponder"], r["bestmove_line"]])
    parts.append("#### T15 — a drawn root under ponder floods `info` at zero cost\n\n" +
                 table(["info lines", "depths", "nodes reported", "arrival",
                        "bestmove withheld", "then"], t15))

    return "\n\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    data = load_all()
    body = build(data)
    if not args.write:
        print(body)
        return
    with open(FINDINGS) as fh:
        text = fh.read()
    if BEGIN not in text or END not in text:
        sys.exit("FAIL: FINDINGS.md has no generated-table markers")
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    with open(FINDINGS, "w") as fh:
        fh.write(head + BEGIN + "\n\n" + body + "\n\n" + END + tail)
    print("rewrote tables in", FINDINGS)


if __name__ == "__main__":
    main()
