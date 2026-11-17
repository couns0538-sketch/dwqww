"""Check the numeric claims in FINDINGS.md against the evidence JSON.

This exists because the failure mode is not a missing measurement, it is a
number that was true when it was typed and then drifted, or a row that came
from a different cell than the sentence implies (forge-findings.md 6: "a true
number, in a true sentence, can imply an experiment nobody ran").

It checks three kinds of claim, and reports UNKNOWN rather than PASS for a
claim it cannot evaluate:

  A. every `hit -> best` figure quoted in the §1 table matches its evidence row
  B. the counts ("n of m", "18 of 18", "12 of 12", "0 of 16") match their arrays
  C. the qualitative thresholds the prose leans on are actually satisfied
     (max over hard, no zero rows, identical node counts, CPU/regime signs)

Exit 1 on any FAIL. Exit 0 only when every check ran and passed; a check that
could not be evaluated prints UNKNOWN and also exits 1, because a check that
declines to evaluate has not cleared anything.
"""

import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVIDENCE = os.path.join(ROOT, "evidence")
FINDINGS = os.path.join(ROOT, "FINDINGS.md")

results = []


def check(kind, name, ok, detail=""):
    results.append((kind, name, ok, detail))


def unknown(name, detail):
    results.append(("UNKNOWN", name, None, detail))


def load():
    data = {}
    for path in sorted(glob.glob(os.path.join(EVIDENCE, "probe*_results.json"))):
        with open(path) as fh:
            data.update(json.load(fh))
    return data


def main():
    data = load()
    with open(FINDINGS) as fh:
        text = fh.read()

    # ---- A. the §1 three-clock table -------------------------------------
    f_rows = {r["clock"]: r for r in data["f_three_clocks"]}
    for clock, want in ((2000, 176.2), (10000, 463.0), (60000, 1816.5)):
        got = f_rows.get(clock, {}).get("t_hit_to_best_ms")
        check("A", f"§1 hit->best at clock {clock} = {want}", got == want, f"evidence {got}")
        # ...and that the same figure really is in the document.
        check("A", f"§1 table shows {want} for clock {clock}",
              f"| {want} |" in text or f"**{want}**" in text, "figure present in FINDINGS.md")

    # ---- B. counts --------------------------------------------------------
    n2 = data["n2_stop_returns_found_move"]
    check("B", "T6 stop-move agreement 18/18",
          n2["agree"] == 18 and n2["total"] == 18, f"{n2['agree']}/{n2['total']}")

    rows7 = data["o_ponder_suffix"]
    legal = sum(1 for r in rows7 if r.get("suffix") == "LEGAL")
    check("B", "T13 suffix 12 legal of 14", legal == 12 and len(rows7) == 14,
          f"{legal}/{len(rows7)}, absent={data['suffix_absent']}, bad={data['illegal_or_zero']}")
    check("B", "T13 zero illegal-or-0000", data["illegal_or_zero"] == 0,
          str(data["illegal_or_zero"]))

    stop_rows = data["p2_stop_without_hit"]
    zero_zero = sum(1 for r in stop_rows if r.get("bestmove_is_0000"))
    check("B", "T5 no 0000 among stop replies", zero_zero == 0, f"{zero_zero} rows were 0000")

    p_regime = data["p_regime"]
    check("B", "T7 four regimes measured", len(p_regime) == 4, str(len(p_regime)))

    p4 = data["p4_stray_ponderhit"]
    control = [r for r in p4 if r.get("case", "").startswith("CONTROL")]
    silent = [r for r in p4 if not r.get("case", "").startswith("CONTROL")]
    check("B", "T8 stray ponderhit silent in all 4 states",
          all(r["said_anything"] is False for r in silent) and len(silent) == 4,
          f"{sum(1 for r in silent if not r['said_anything'])}/{len(silent)} silent")
    check("B", "T8 control converted (path is live)",
          len(control) == 1 and control[0]["verdict"] == "RETURNED",
          control[0]["verdict"] if control else "no control row")

    p6 = data["p6_output_shape"]
    races = [r for r in p6 if "bestmove_count" in r]
    check("B", "T10 every race emits exactly one bestmove",
          all(r["bestmove_count"] == 1 for r in races) and len(races) == 4,
          f"{[r['bestmove_count'] for r in races]}")

    d = data["d_ponder_option_path"]
    check("B", "T9 identical node counts under Ponder on/off",
          d[0]["nodes"] == d[1]["nodes"] and d[0]["nodes"] == 17804,
          f"{d[0]['nodes']} vs {d[1]['nodes']}")
    check("B", "T9 suffix present only with Ponder true",
          d[0]["suffix_present"] is False and d[1]["suffix_present"] is True,
          f"{d[0]['suffix_present']} / {d[1]['suffix_present']}")

    g = {r["Ponder"]: r for r in data["g_self_ponder"]}
    check("B", "T9 no self-ponder after bestmove (both arms)",
          not g["false"]["lines_after_bestmove"] and not g["true"]["lines_after_bestmove"],
          "no info lines in 3 s of silence")

    # ---- C. thresholds the prose depends on -------------------------------
    q = data["q_budget_upper_bound"]["summary"]
    check("C", "§1 max(hit->best - hard) under 1.5 ms", q["max_over_hard_ms"] <= 1.5,
          f"{q['max_over_hard_ms']} ms")
    check("C", "§1 zero rows stopped at ~0 ms", q["n_zero_ms"] == 0, str(q["n_zero_ms"]))
    check("C", "§1 n = 16 offsets", q["n"] == 16, str(q["n"]))

    # The 60%-of-hard figure the prose quotes must be computed, not guessed.
    below = 0
    for r in data["q_budget_upper_bound"]["rows"]:
        if r.get("verdict") != "RETURNED":
            continue
        if r["t_hit_to_best_ms"] < 0.6 * r["hard_ms"]:
            below += 1
    check("C", "§1 rows below 60% of hard", True, f"computed {below} of {q['n']}")
    # The document wraps prose across lines, so the phrase is searched with
    # whitespace collapsed -- otherwise a correct sentence fails on a newline.
    flat = re.sub(r"\s+", " ", text)
    if f"{below} of {q['n']}" not in flat:
        check("C", "§1 prose states the computed fraction", False,
              f"prose does not say '{below} of {q['n']}'")
    else:
        check("C", "§1 prose states the computed fraction", True, f"{below} of {q['n']}")

    # T3's headline ratio.
    n1 = {r["clock"]: r for r in data["n1_node_growth_after_hit"]}
    check("C", "§3 6 s ponder over a 225 ms hard limit is 26.7x",
          abs(n1[1000]["ponder_over_hard"] - 26.67) < 0.01,
          str(n1[1000]["ponder_over_hard"]))
    check("C", "§3 that case still received the full hard budget",
          abs(n1[1000]["t_hit_to_best_ms"] - 225) < 2.0,
          f"{n1[1000]['t_hit_to_best_ms']} ms vs hard 225")
    # The "5.8 s earlier" figure is a DERIVATION, not a measurement: ponder
    # minus hard. Checked so it cannot drift away from its operands.
    overshoot_s = (n1[1000]["ponder_ms"] - n1[1000]["planned_hard_ms"]) / 1000.0
    check("C", "§3 '5.8 s earlier' follows from ponder - hard",
          round(overshoot_s, 1) == 5.8, f"{overshoot_s:.1f} s")

    # T7 regime signs.
    by_case = {r["go_line"]: r for r in p_regime}
    check("C", "T7 clocked ponder is RUNAWAY at ~100% CPU",
          by_case["go ponder wtime 10000 btime 10000"]["regime"] == "RUNAWAY" and
          by_case["go ponder wtime 10000 btime 10000"]["cpu_at_horizon"] > 90,
          str(by_case["go ponder wtime 10000 btime 10000"]["cpu_at_horizon"]))
    check("C", "T7 depth-limited ponder is WITHHELD at ~0% CPU",
          by_case["go ponder depth 12"]["regime"] == "WITHHELD" and
          by_case["go ponder depth 12"]["cpu_at_horizon"] < 10,
          str(by_case["go ponder depth 12"]["cpu_at_horizon"]))
    check("C", "T7 no bestmove in any regime before a command",
          all(r["bestmoves_during_horizon"] == 0 for r in p_regime), "all zero")
    check("C", "T7 stop recovers every regime in under 5 ms",
          all((r["t_stop_to_best_ms"] or 99) < 5 for r in p_regime),
          str([r["t_stop_to_best_ms"] for r in p_regime]))

    # T11: the gap equals the ponder length, which is the whole point.
    for r in data["p_time_disagreement"]:
        gap = r["info_time_at_best_ms"] - r["wall_from_ponderhit_ms"]
        want = r["ponder_s"] * 1000
        check("C", f"§6 time-field gap equals ponder length at clock {r['clock']}",
              abs(gap - want) < 150, f"gap {gap:.0f} ms vs ponder {want:.0f} ms")

    # T12: the artifact identity claim.
    for r in data["n4_zero_stop_vs_eof"]:
        check("C", f"§2 zero-ms stop identical to immediate EOF ({r['pos']})",
              r["zero_stop_equals_immediate_eof"] is True, str(r["zero_stop_equals_immediate_eof"]))
        check("C", f"§2 zero-ms stop tracks the position ({r['pos']})",
              r["zero_stop_is_first_legal"] is True, str(r["zero_stop_is_first_legal"]))

    # T14: the desync ordering claim.
    m = {r["stop_first"]: r for r in data["m_desync"]}
    check("C", "§6 no-stop restart emits a stale bestmove after the new go",
          m[False]["bestmoves"][0]["t_rel_second_go_ms"] >= 0 and m[False]["bestmove_count"] == 2,
          f"{m[False]['bestmoves'][0]['t_rel_second_go_ms']} ms, "
          f"{m[False]['bestmove_count']} lines")
    check("C", "§6 stop-first puts the stale bestmove before the new go",
          m[True]["bestmoves"][0]["t_rel_second_go_ms"] < 0,
          f"{m[True]['bestmoves'][0]['t_rel_second_go_ms']} ms")

    # T15: the zero-cost info flood.
    n5 = data["n5_terminal_root"][0]
    check("C", "§6 drawn root floods 64 info lines at 0 nodes",
          n5["info_lines_during_ponder"] == 64 and n5["nodes_reported_at_max_depth"] == 0,
          f"{n5['info_lines_during_ponder']} lines, {n5['nodes_reported_at_max_depth']} nodes")
    check("C", "§6 drawn-root bestmove is withheld during the ponder",
          n5["bestmove_withheld_during_ponder"] is True, "withheld")

    # ---- D. cross-references --------------------------------------------
    # A dangling `Tn` or `§n` is invisible to every numeric check: each sentence
    # stays true while pointing at the wrong table. This is the arrangement
    # defect, mechanised where it actually is mechanisable.
    defined_t = set(re.findall(r"^#### (T\d+) —", text, re.MULTILINE))
    used_t = set(re.findall(r"`(T\d+)`", text))
    dangling_t = used_t - defined_t
    check("D", f"every `Tn` reference resolves ({len(defined_t)} tables defined)",
          not dangling_t, f"dangling: {sorted(dangling_t)}" if dangling_t else
          f"used: {sorted(used_t, key=lambda s: int(s[1:]))}")
    check("D", "no table is defined but never referenced",
          defined_t <= used_t, f"unreferenced: {sorted(defined_t - used_t)}")

    defined_s = set(re.findall(r"^## (\d+)\. ", text, re.MULTILINE))
    used_s = set(re.findall(r"§(\d+)", text))
    dangling_s = used_s - defined_s
    check("D", f"every `§n` reference resolves ({len(defined_s)} sections defined)",
          not dangling_s, f"dangling: {sorted(dangling_s)}" if dangling_s else
          f"used: {sorted(used_s)}")

    # ---- report ----------------------------------------------------------
    fails = [r for r in results if r[2] is False]
    unknowns = [r for r in results if r[0] == "UNKNOWN"]
    for kind, name, ok, detail in results:
        if ok is None:
            mark = "UNKNOWN"
        else:
            mark = "PASS" if ok else "FAIL"
        print(f"{mark:7} [{kind}] {name}" + (f"  ({detail})" if detail else ""))
    print()
    print(f"{len(results)} checks, {len(results) - len(fails) - len(unknowns)} pass, "
          f"{len(fails)} fail, {len(unknowns)} unknown")
    if fails or unknowns:
        sys.exit(1)
    print("VERDICT: all claims in FINDINGS.md agree with the evidence")
    sys.exit(0)


if __name__ == "__main__":
    # A crash must not read as a pass: an uncaught exception exits 1, and any
    # unexpected exit path is converted to an explicit failure line.
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - a crash is a failed check, always
        print(f"FAIL: checker crashed, which is not a pass: {exc.__class__.__name__}: {exc}")
        sys.exit(1)
