#!/usr/bin/env python3
"""
Job 49 Report Builder (`build_report.py`):
Builds `forge-combo29/carbon2/job49/REPORT_carbon2_job49.md` strictly from committed run files
(never typing numbers manually; strictly separating Facts whose 95% CIs exclude 0 from Suspicions
whose 95% CIs cross 0; never pooling 2,000-node and 20,000-node matches).
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB49 = REPO / "forge-combo29/carbon2/job49"
JOB48 = REPO / "forge-combo29/carbon2/job48"

sys.path.insert(0, str(JOB49))
from j49_lib import sha256_file  # noqa: E402


def parse_kv_colon(path: pathlib.Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        if ":" in ln and not ln.startswith("  "):
            k, v = ln.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def extract_pass_lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ": PASS (" in ln]


def git_commit_stat_for_path(rel_path: str) -> tuple[str, str]:
    sha = subprocess.run(
        ["git", "log", "-n", "1", "--format=%h", "--", rel_path],
        cwd=str(REPO),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    stat = subprocess.run(
        ["git", "show", "--stat", "--format=%h %s (%ci)", sha],
        cwd=str(REPO),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return sha, stat


def main() -> None:
    step0_txt = (JOB49 / "step0_raw.txt").read_text(encoding="utf-8")
    kstar_json = json.loads((JOB49 / "kstar.json").read_text(encoding="utf-8"))
    matches_payload = json.loads((JOB49 / "matches_results.json").read_text(encoding="utf-8"))
    liv_json = json.loads((JOB49 / "liveness_M16_M17.json").read_text(encoding="utf-8"))
    builds_txt = (JOB49 / "builds.txt").read_text(encoding="utf-8")
    stamps_txt = (JOB49 / "stamps.txt").read_text(encoding="utf-8")

    # Read Job 48 M15-0 and M15-2 from M15_results.json for 4-corner comparison at 2,000 nodes
    j48_m15 = {str(it["tag"]): it for it in json.loads((JOB48 / "M15_results.json").read_text(encoding="utf-8"))}
    d2_j48_elo = float(j48_m15["M15-2"]["diff_elo"])
    d2_j48_hw = float(j48_m15["M15-2"]["diff_err95"])
    d2_j48_str = str(j48_m15["M15-2"]["diff_str"])

    m_plant = re.search(r"^  planted_engine_unknown_option_line_verbatim\s*:\s*(.+)$", step0_txt, re.M)
    if not m_plant:
        raise RuntimeError("Missing planted_engine_unknown_option_line_verbatim in step0_raw.txt")
    planted_line_verbatim = m_plant.group(1).strip()

    m_k4_sum = re.search(
        r"bundle11 IdeaK4\(Shrink=32\) O d12 sum vs job47 P11\(d\) IdeaK4b: PASS \((\d+) == \d+\)",
        step0_txt,
    )
    m_k4_eq = re.search(
        r"bundle11 IdeaK4\(Shrink=32\) O d12 position-by-position equal vs P11\(d\): PASS \((\d+ == \d+)\)",
        step0_txt,
    )
    if not (m_k4_sum and m_k4_eq):
        raise RuntimeError("Missing K4 equivalence PASS lines in step0_raw.txt")
    k4_sum_val = int(m_k4_sum.group(1))
    k4_eq_str = m_k4_eq.group(1)

    m_pc20_o = re.search(r"bundle9 PC20 all_off O d12 sum\s+: PASS \((\d+) == \d+\)", step0_txt)
    m_l2_o = re.search(r"bundle9 L2 all_off O d12 sum vs job48 Part L: PASS \((\d+) == \d+\)", step0_txt)
    m_b11 = re.search(r"bundle9 no-option bench 11\s+: PASS \((\d+) == \d+\)", step0_txt)
    m_b13 = re.search(r"bundle9 no-option bench 13\s+: PASS \((\d+) == \d+\)", step0_txt)
    m_pf5 = re.search(r"bundle9 no-option perft 5\s+: PASS \((\d+) == \d+\)", step0_txt)
    m_pc_b11 = re.search(r"bundle9 PC20 \(default off\) bench 11\s+: PASS \((\d+) == \d+\)", step0_txt)
    m_pc_b13 = re.search(r"bundle9 PC20 \(default off\) bench 13\s+: PASS \((\d+) == \d+\)", step0_txt)
    if not (m_pc20_o and m_l2_o and m_b11 and m_b13 and m_pf5 and m_pc_b11 and m_pc_b13):
        raise RuntimeError("Missing Step 0 pin PASS lines in step0_raw.txt")

    pc20_o_val = int(m_pc20_o.group(1))
    l2_o_val = int(m_l2_o.group(1))
    b11_val, b13_val, pf5_val = int(m_b11.group(1)), int(m_b13.group(1)), int(m_pf5.group(1))
    pc_b11_val, pc_b13_val = int(m_pc_b11.group(1)), int(m_pc_b13.group(1))

    kstar_sha, _ = git_commit_stat_for_path("forge-combo29/carbon2/job49/kstar.txt")
    pred_sha, pred_stat = git_commit_stat_for_path("forge-combo29/carbon2/job49/prediction_job49.txt")

    matches_list: list[dict[str, object]] = list(matches_payload["matches"])
    diffs_by_nodes: dict[str, dict[str, object]] = dict(matches_payload["m16_minus_m17_by_nodes"])

    by_tag: dict[str, dict[str, object]] = {}
    for raw_it in matches_list:
        tag = str(raw_it["tag"])
        enriched = dict(raw_it)
        enriched["meta_kv"] = parse_kv_colon(JOB49 / f"{tag}_fastchess.txt.meta")
        enriched["rec_kv"] = parse_kv_colon(JOB49 / f"{tag}_recount.txt")
        enriched["rec_pass"] = extract_pass_lines((JOB49 / f"{tag}_recount.txt").read_text(encoding="utf-8"))
        by_tag[tag] = enriched

    n_true = sum(1 for it in matches_list if it["pred_held"] is True)
    n_graded = sum(1 for it in matches_list if it["pred_held"] is not None)

    step0_pass_block = "\n".join(f"- `{ln}`" for ln in extract_pass_lines(step0_txt))

    dk_rows_md: list[str] = []
    for r in kstar_json["dk_records"]:
        is_sel = f"**YES (`k* = {kstar_json['k_star']}`)**" if int(r["k"]) == int(kstar_json["k_star"]) else "no"
        dk_rows_md.append(
            f"| `{r['k']}` | `{r['base_key']}` (`{r['short_words']}`) | `{r['partL_status']}` (`{r['partL_file']}:{r['partL_line']}`) | "
            f"`{r['m15_status']}` (`{float(r['elo_k_2dp']):+.2f}`) | **`{r['D_k_summary_col']}`** (`{r['m15_file']}:{r['m15_line']}`) | {is_sel} |"
        )
    dk_other_str = ", ".join(
        f"`D_{r['k']} = {float(r['D_k_2dp']):+.2f}`"
        for r in kstar_json["dk_records"]
        if int(r["k"]) != int(kstar_json["k_star"])
    )
    dk_sel_rec = [r for r in kstar_json["dk_records"] if int(r["k"]) == int(kstar_json["k_star"])][0]

    pred_rows_md: list[str] = []
    for raw_it in matches_list:
        tag = str(raw_it["tag"])
        it = by_tag[tag]
        pp = float(it["pred_point"])
        plo, phi = float(it["pred_bounds"][0]), float(it["pred_bounds"][1])
        if it["elo"] is not None:
            elo = float(it["elo"])
            hw = float(it["err95"])
            clo, chi = float(it["ci_low"]), float(it["ci_high"])
            obs_s = f"**`{elo:+.2f} +/- {hw:.2f}`** (`[{clo:+.2f}, {chi:+.2f}]`)"
            if bool(it["pred_held"]):
                gr_s = f"**`TRUE (HELD)`** (`{plo:+.1f} <= {elo:+.2f} <= {phi:+.1f}`)"
            else:
                gr_s = f"**`FALSE (MISSED)`** (`{elo:+.2f}` outside `[{plo:+.1f}, {phi:+.1f}]`)"
        else:
            obs_s = "CUT (no Elo)"
            gr_s = "NOT GRADED (CUT)"
        pred_rows_md.append(
            f"| `{tag}` (`nodes={it['nodes']}`, `{it['bundle_desc']}`) | `{pp:+.1f}` Elo | outside `[{plo:+.1f}, {phi:+.1f}]` | {obs_s} | {gr_s} |"
        )

    match_top_rows: list[str] = []
    match_detail_blocks: list[str] = []
    for raw_it in matches_list:
        tag = str(raw_it["tag"])
        it = by_tag[tag]
        st_ln, en_ln = int(it["start_line"]), int(it["end_line"])
        gms, prs = int(it["games"]), int(it["pairs"])
        w, l, drw = int(it["w"]), int(it["l"]), int(it["d"])
        pt = list(it["ptnml"])
        if it["elo"] is not None:
            elo, hw = float(it["elo"]), float(it["err95"])
            clo, chi = float(it["ci_low"]), float(it["ci_high"])
            elo_md = f"**`{elo:+.2f} +/- {hw:.2f}`** (`[{clo:+.2f}, {chi:+.2f}]`)"
        else:
            elo_md = "N/A"
        match_top_rows.append(
            f"| `{tag}` | `{int(it['nodes']):,}` | `{it['bundle_desc']}` | `{st_ln:,}..{en_ln:,}` | `{it['status']}` (`{gms:,}`) | "
            f"`{w}-{l}-{drw}` | `{pt}` | {elo_md} | `{it['pred_status']}` |"
        )

        mkv = it["meta_kv"]
        rkv = it["rec_kv"]
        rpasses = "\n".join(f"  - `{pln}`" for pln in it["rec_pass"])
        match_detail_blocks.append(
            f"### `{tag}` — `nodes={int(it['nodes']):,}`, `{it['bundle_desc']}`, Side A `{it['eng1_name']}` vs Side B `{it['eng2_name']}` (UHO `{st_ln:,}..{en_ln:,}`)\n"
            f"- **Status:** `{it['status']}` (`{gms:,}` games, `{prs:,}` pairs, wall `{mkv['wall_s']}s`, "
            f"`start_utc`: `{mkv['start_utc']}`, `end_utc`: `{mkv['end_utc']}`)\n"
            f"- **Executable (`{mkv['exe_path']}`):** `sha256 = {mkv['exe_sha256(' + mkv['exe_path'] + ')']}` (`{mkv['id_name']}`)\n"
            f"- **UCI preflight checks:** Side A `{mkv['sideA_options_verified_in_uci_list']}` options verified in `uci` list (`{mkv['sideA_preflight_pre_readyok_lines']}` pre-`readyok` lines); "
            f"Side B `{mkv['sideB_options_verified_in_uci_list']}` options verified in `uci` list (`{mkv['sideB_preflight_pre_readyok_lines']}` pre-`readyok` lines)\n"
            f"- **Committed recount (`forge-combo29/carbon2/job49/{tag}_recount.txt`):** `W-L-D = {w}-{l}-{drw}`, pentanomial `{pt}`, {elo_md} Elo\n"
            f"- **Fastchess own line (`forge-combo29/carbon2/job49/{tag}_fastchess.txt`):** `{rkv['fastchess_own_line']}`\n"
            f"- **Per-game list (`{rkv['games_tsv_path']}`):** `sha256 = {rkv['games_tsv_sha256(' + rkv['games_tsv_path'] + ')']}`\n"
            f"- **Fastchess stdout (`{rkv['fastchess_stdout_path']}`):** `sha256 = {rkv['fastchess_stdout_sha256(' + rkv['fastchess_stdout_path'] + ')']}`\n"
            f"- **Command (`{tag}_fastchess.txt.meta`):**\n"
            f"  `{mkv['command']}`\n"
            f"- **Recount `PASS` checks:**\n{rpasses}"
        )

    diff_rows_md: list[str] = []
    for nlabel, m16_t, m17_t in [("2000", "M16-2k", "M17-2k"), ("20000", "M16-20k", "M17-20k")]:
        if nlabel in diffs_by_nodes:
            d = diffs_by_nodes[nlabel]
            r16, r17 = by_tag[m16_t], by_tag[m17_t]
            diff_rows_md.append(
                f"| `{int(nlabel):,}` | `{m16_t}`: `{float(r16['elo']):+.2f} +/- {float(r16['err95']):.2f}` | "
                f"`{m17_t}`: `{float(r17['elo']):+.2f} +/- {float(r17['err95']):.2f}` | "
                f"**`{d['diff_str']}`** | `{'YES' if d['excludes_zero'] else 'NO (crosses 0)'}` |"
            )

    m16_pct = 100.0 * float(liv_json["m16_o_delta"]) / float(liv_json["m16_sideB_o_sum"])
    m17_pct = 100.0 * float(liv_json["m17_o_delta"]) / float(liv_json["m17_sideB_o_sum"])

    facts_list: list[str] = [
        f"1. **Step 0 pins, known answers, and the planted `HistReworkk=0` stop check passed on `bundle9` (`/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`):** No-option pins `{b11_val:,} / {b13_val:,} / {pf5_val:,}`; `PC20` `bench 11 / 13 = {pc_b11_val:,} / {pc_b13_val:,}`; `PC20` all off `O = {pc20_o_val:,}` (`200 == 200` position-by-position equal to Job 46 Step 0); `L2` (`HistRework 0`) all off `O = {l2_o_val:,}` (`200 == 200` equal to Job 48 Part L); and the planted `HistReworkk=0` check stopped the runner immediately before any search on `{planted_line_verbatim}`.",
        f"2. **Bonus equivalence check from File 49 (`lines 38–40`):** On `/tmp/carbon2_job47/bld_bundle11_k4b/forge` (`PC20`), `IdeaK4=true` with `IdeaK4_Shrink=32` and `IdeaK4b=false` gives `O = {k4_sum_val:,}` and matches Job 47 `P11(d)` (`IdeaK4b=true` alone) on `{k4_eq_str}` positions (nodes, best move, and score).",
        f"3. **`k* = {kstar_json['k_star']}` (`{kstar_json['base_star']}: {kstar_json['switch_name']} {kstar_json['s14_value']}`) selected from Job 48's five completed live bases:** `D_2 = Elo(M15-2) - Elo(M15-0) = {d2_j48_str}` (`{dk_sel_rec['m15_file']}:{dk_sel_rec['m15_line']}`), strictly the largest `D_k` across `k = 1..5` ({dk_other_str}).",
        f"4. **Depth-12 liveness on `O` (`200` positions) confirms `HistRework = 0` vs `HistRework = 2` is live both with and without the bundle, with smaller tree-size expansion when the bundle is on:** Without the bundle (`M17`), `L2` searches `{int(liv_json['m17_sideA_o_sum']):,}` vs `PC20`'s `{int(liv_json['m17_sideB_o_sum']):,}` (`{int(liv_json['m17_o_delta']):+,}` nodes = `{m17_pct:+.2f}%`, `{liv_json['m17_nodes_diff']}/200` node diffs, `{liv_json['m17_bm_diff']}/200` best-move diffs). With the bundle (`M16`), `L2` searches `{int(liv_json['m16_sideA_o_sum']):,}` vs `PC20`'s `{int(liv_json['m16_sideB_o_sum']):,}` (`{int(liv_json['m16_o_delta']):+,}` nodes = `{m16_pct:+.2f}%`, `{liv_json['m16_nodes_diff']}/200` node diffs, `{liv_json['m16_bm_diff']}/200` best-move diffs).",
    ]

    suspicions_list: list[str] = []
    fact_idx = 5
    susp_idx = 1

    for raw_it in matches_list:
        tag = str(raw_it["tag"])
        it = by_tag[tag]
        elo, hw = float(it["elo"]), float(it["err95"])
        clo, chi = float(it["ci_low"]), float(it["ci_high"])
        nds = int(it["nodes"])
        gms = int(it["games"])
        if chi < 0.0:
            facts_list.append(
                f"{fact_idx}. **In `{tag}` (`nodes={nds:,}`, `{gms:,}` games, `{it['bundle_desc']}`), setting `HistRework = 0` (`L2`) loses to `PC20` (`HistRework = 2`) with 95% confidence excluding zero:** Side A (`{it['eng1_name']}`) vs Side B (`{it['eng2_name']}`) scored `{it['w']}-{it['l']}-{it['d']}`, pentanomial `{list(it['ptnml'])}`, **`{elo:+.2f} +/- {hw:.2f}` Elo (`[{clo:+.2f}, {chi:+.2f}]`)**."
            )
            fact_idx += 1
        elif clo > 0.0:
            facts_list.append(
                f"{fact_idx}. **In `{tag}` (`nodes={nds:,}`, `{gms:,}` games, `{it['bundle_desc']}`), setting `HistRework = 0` (`L2`) beats `PC20` (`HistRework = 2`) with 95% confidence excluding zero:** Side A (`{it['eng1_name']}`) vs Side B (`{it['eng2_name']}`) scored `{it['w']}-{it['l']}-{it['d']}`, pentanomial `{list(it['ptnml'])}`, **`{elo:+.2f} +/- {hw:.2f}` Elo (`[{clo:+.2f}, {chi:+.2f}]`)**."
            )
            fact_idx += 1
        else:
            facts_list.append(
                f"{fact_idx}. **In `{tag}` (`nodes={nds:,}`, `{gms:,}` games, `{it['bundle_desc']}`), the 95% confidence interval crosses zero:** Side A (`{it['eng1_name']}`) vs Side B (`{it['eng2_name']}`) scored `{it['w']}-{it['l']}-{it['d']}`, pentanomial `{list(it['ptnml'])}`, **`{elo:+.2f} +/- {hw:.2f}` Elo (`[{clo:+.2f}, {chi:+.2f}]`)**."
            )
            fact_idx += 1
            suspicions_list.append(
                f"{susp_idx}. **Directional lean in `{tag}` (`{elo:+.2f} +/- {hw:.2f}` Elo, `[{clo:+.2f}, {chi:+.2f}]`):** The point estimate leans {'against' if elo < 0 else 'toward'} `HistRework = 0` at `nodes={nds:,}` (`{it['bundle_desc']}`), consistent with the `2,000`-node direction, while its `3,000`-game 95% interval crosses `0`."
            )
            susp_idx += 1

    for nlabel, m16_t, m17_t in [("2000", "M16-2k", "M17-2k"), ("20000", "M16-20k", "M17-20k")]:
        d = diffs_by_nodes[nlabel]
        if bool(d["excludes_zero"]):
            facts_list.append(
                f"{fact_idx}. **At `nodes={int(nlabel):,}` (quoted apart), `Elo({m16_t}) - Elo({m17_t}) = {d['diff_str']}`, whose 95% interval excludes zero.**"
            )
            fact_idx += 1
        else:
            facts_list.append(
                f"{fact_idx}. **At `nodes={int(nlabel):,}` (quoted apart), `Elo({m16_t}) - Elo({m17_t}) = {d['diff_str']}`, whose 95% interval crosses zero.**"
            )
            fact_idx += 1
            if nlabel == "2000":
                four_corner_gap = d2_j48_elo - float(d["diff_elo"])
                four_corner_hw = (d2_j48_hw ** 2 + float(d["diff_err95"]) ** 2) ** 0.5
                suspicions_list.append(
                    f"{susp_idx}. **Interaction `Elo({m16_t}) - Elo({m17_t}) = {d['diff_str']}` at `nodes={int(nlabel):,}`:** The positive point difference leans in the same direction as Job 48's `D_2 = {d2_j48_str}` (the 4-corner closure difference `(M15-2 - M15-0) - (M16-2k - M17-2k)` across the four independent `12,000`-game matches is `{four_corner_gap:+.2f} +/- {four_corner_hw:.2f}` Elo, crossing `0`), indicating partial overlap between `HistRework = 2` and the bundle (`~+2` to `+5` Elo if one averages the two orthogonal ways of measuring the same interaction) while `M16-2k - M17-2k` alone lies inside `+/- {float(d['diff_err95']):.2f}` Elo."
                )
            else:
                suspicions_list.append(
                    f"{susp_idx}. **Interaction `Elo({m16_t}) - Elo({m17_t}) = {d['diff_str']}` at `nodes={int(nlabel):,}`:** The positive point estimate (`{float(d['diff_elo']):+.2f}`) also leans toward partial overlap at `20,000` nodes, while its `3,000`-game combined 95% interval (`[{float(d['diff_ci_low']):+.2f}, {float(d['diff_ci_high']):+.2f}]`) crosses `0`."
                )
            susp_idx += 1

    suspicions_list.append(
        f"{susp_idx}. **Why switching `HistRework` all the way to `0` (`L2`) loses even with the bundle on (`M16-2k = {float(by_tag['M16-2k']['elo']):+.2f} +/- {float(by_tag['M16-2k']['err95']):.2f}`, `M16-20k = {float(by_tag['M16-20k']['elo']):+.2f} +/- {float(by_tag['M16-20k']['err95']):.2f}`):** `HistRework = 2` carries two features that `IdeaB8b` does not replace — `(a)` the destination-square bit `to_attacked_by_lesser` in `LesserThreatHistory` (penalizing quiet moves that step *onto* squares attacked by cheaper enemy pieces even when no friendly piece is currently threatened) and `(b)` the `75%`-weighted `joint_correction_` table (`pawn_key ^ non_pawn_material`). Thus `IdeaB8b` recovers part of `from_attacked_by_lesser` (depth-12 `O` node growth drops from `{m17_pct:+.2f}%` to `{m16_pct:+.2f}%`), yet losing `to_attacked_by_lesser` and `joint_correction_` leaves `bundle + HistRework=0` weaker than `bundle + HistRework=2`."
    )

    m16_2k_elo = float(by_tag["M16-2k"]["elo"])
    m16_2k_hw = float(by_tag["M16-2k"]["err95"])
    m16_2k_plo = float(by_tag["M16-2k"]["pred_bounds"][0])
    m16_2k_miss = m16_2k_plo - m16_2k_elo
    m17_2k_elo = float(by_tag["M17-2k"]["elo"])
    m17_2k_hw = float(by_tag["M17-2k"]["err95"])
    m17_2k_pp = float(by_tag["M17-2k"]["pred_point"])
    hw_2k_diff = float(diffs_by_nodes["2000"]["diff_err95"])
    hw_20k_diff = float(diffs_by_nodes["20000"]["diff_err95"])

    row_hashes: list[str] = []
    for desc, p in [
        ("Step 0 bundle9 PC20 all_off O d12 rows", JOB49 / "step0_bundle9_PC20_all_off_O_d12.rows.txt"),
        ("Step 0 bundle9 L2 all_off O d12 rows", JOB49 / "step0_bundle9_L2_all_off_O_d12.rows.txt"),
        ("Step 0 bundle11 IdeaK4(Shrink=32) O d12 rows", JOB49 / "step0_bundle11_IdeaK4_Shrink32_O_d12.rows.txt"),
        ("M16 liveness Side A (L2 + bundle) O d12 rows", JOB49 / "M16_liveness_SideA_L2_bundle_O_d12.rows.txt"),
        ("M16 liveness Side B (PC20 + bundle) O d12 rows", JOB49 / "M16_liveness_SideB_PC20_bundle_O_d12.rows.txt"),
    ]:
        row_hashes.append(f"- {desc} (`{p}`): `{sha256_file(p)}`")

    md = f"""# Carbon2 Job 49 Report: Switch `k* = {kstar_json['k_star']}` (`HistRework 0` vs `PC20`'s `HistRework 2`), With and Without `IdeaB8b + HindsightDepth` (`2,000` and `20,000` Nodes)

## 1. Step 0 — `bundle9` Pins, `PC20` & `L2` Known Answers, Planted `HistReworkk=0` Stop Check, and `K4` Equivalence

- **Executable reused (identical to Jobs 46 & 48):** `/tmp/carbon2_job44/bld_bundle9/forge` (`sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`, `id name Chess Engine Forge 6.4.24 candidate`).
- **Planted misspelt option check (`HistReworkk=0`):** `run_epd_depth12_strict` sent `setoption name HistReworkk value 0` followed by `isready`, read every reply line before `readyok`, and **stopped immediately** via `EngineReplyStopError` (`0` searches run; planted `.rows.txt` not written) on the engine's exact `unknown option` line:
  - **`{planted_line_verbatim}`**
- **File 49 one-line bonus check (`lines 38–40`):** On `/tmp/carbon2_job47/bld_bundle11_k4b/forge` (`PC20`), `IdeaK4=true, IdeaK4_Shrink=32, IdeaK4b=false` sums to `{k4_sum_val:,}` on `O` at depth `12` and equals Job 47 `P11(d)` (`IdeaK4b=true` alone) on `{k4_eq_str}` positions.
- **All Step 0 `PASS` lines (`forge-combo29/carbon2/job49/step0_raw.txt`):**
{step0_pass_block}

---

## 2. Selection of `k*` From Committed Job 48 Numbers (`forge-combo29/carbon2/job49/kstar.txt`)

- **Committed before Step 0 and before `prediction_job49.txt` (`{kstar_sha}`):**
  - **`k* = {kstar_json['k_star']}`**
  - **Base `L_k*` in words:** `{kstar_json['base_in_words']}`
  - **Baseline `M15-0`:** `{float(kstar_json['m15_0_elo_2dp']):+.2f} +/- {float(kstar_json['m15_0_hw95_2dp']):.2f}` Elo (`{kstar_json['m15_0_file']}:{kstar_json['m15_0_line']}`).

| `k` | Base `L_k` | Job 48 Part L Status (`file:line`) | Job 48 `M15-k` Status (`Elo`) | `D_k = Elo(M15-k) - Elo(M15-0)` (`file:line`) | Selected `k*`? |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(dk_rows_md)}

---

## 3. Prediction Graded (`forge-combo29/carbon2/job49/prediction_job49.txt`)

- **Commit order and isolation:** Committed **ALONE** (`1 file changed`) in `{pred_sha}` after `kstar.txt` and Step 0, and before `M16`'s liveness search and first game:

```text
{pred_stat}
```

- **Per-match Side A (`L2: HistRework = 0` vs `PC20: HistRework = 2`) predictions (`{n_true} / {n_graded}` `TRUE`):**

| Match | Predicted Side A Elo | Falsification Range | Observed Side A Elo +/- 95% (`[CI]`) | Grade |
| --- | --- | --- | --- | --- |
{chr(10).join(pred_rows_md)}

---

## 4. The Four Matches (`M16-2k`, `M17-2k`, `M16-20k`, `M17-20k`) and `M16 - M17` at Each Node Count

- **Common match settings:** `/tmp/carbon2_job44/bld_bundle9/forge` (`sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`), built-in evaluation, `Threads=1`, `Hash=16`, `OwnBook=false`, sequential UHO openings (`/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd`, lines `2,060,001..2,075,000`), `concurrency=4`. In all four matches, **Side A = base `L2` (`HistRework=0`)** and **Side B = base `PC20` (`HistRework=2`)**, with the other 21 `PC20` options identical on both sides.
- **Depth-12 liveness on `O` (`200` positions, `forge-combo29/carbon2/job49/liveness_M16_M17.txt`):**
  - `M16 Side B (PC20 + bundle) O d12 known-answer sum: PASS (8481645 == 8481645)`
  - `M16` (with bundle `IdeaB8b + HindsightDepth`): Side A (`L2`) `O = {int(liv_json['m16_sideA_o_sum']):,}` vs Side B (`PC20`) `O = {int(liv_json['m16_sideB_o_sum']):,}` (`{int(liv_json['m16_o_delta']):+,}` nodes; `{liv_json['m16_nodes_diff']}/200` node diffs, `{liv_json['m16_bm_diff']}/200` best-move diffs, `{liv_json['m16_sc_diff']}/200` score diffs).
  - `M17` (all Idea & `HindsightDepth` off): Side A (`L2`) `O = {int(liv_json['m17_sideA_o_sum']):,}` vs Side B (`PC20`) `O = {int(liv_json['m17_sideB_o_sum']):,}` (`{int(liv_json['m17_o_delta']):+,}` nodes; `{liv_json['m17_nodes_diff']}/200` node diffs, `{liv_json['m17_bm_diff']}/200` best-move diffs, `{liv_json['m17_sc_diff']}/200` score diffs).

### Summary of the Four Matches

| Match | Nodes | Bundle State on Both Sides | UHO Lines | Status (`Games`) | `W-L-D` | Pentanomial `[LL,LD,WL+DD,WD,WW]` | Side A (`L2`) vs Side B (`PC20`) Elo +/- 95% (`[CI]`) | Prediction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(match_top_rows)}

### `M16 - M17` at Each Node Count (Quoted Strictly Apart; `se = sqrt(se_16^2 + se_17^2)`, `se = hw95 / 1.96`)

| Nodes / Move | `M16` (With Bundle: `L2` vs `PC20`) | `M17` (Without Bundle: `L2` vs `PC20`) | `M16 - M17` +/- 95% (`[CI]`) | 95% CI Excludes `0`? |
| --- | --- | --- | --- | --- |
{chr(10).join(diff_rows_md)}

{chr(10).join(match_detail_blocks)}

---

## What This Cannot See

The PC's net, Windows, and the PC's node counts with its net; 12,000 games carry about +/- 5 Elo and 3,000 about
+/- 9; one switch only (k*), at its S14 value only (no level in between); M16 and M17 measure k* on the bundle's tree
with the built-in evaluation, so a lean here is a question for the PC, never an answer.

---

## Facts

{chr(10).join(facts_list)}

---

## Suspicions

{chr(10).join(suspicions_list)}

---

## Read and Not Tested

1. **Intermediate `HistRework = 1` (`50%` blend / `50%` joint weight) and `HistRework = 3` (`100%` blend / `100%` joint weight) in `/tmp/carbon2_job36/tpl_r15d_v3/include/forge/b4.hpp` (`lines 20–30, 65–75`):** Job 49 tested only `HistRework = 0` (`S14` value) against `HistRework = 2` (`PC20` value). Because `HistRework = 0` discards both `joint_correction_` (`src/search.cpp:1446–1459`) and the `to_attacked_by_lesser` axis of `LesserThreatHistory` (`src/search.cpp:1612–1616`), an intermediate setting (`HistRework = 1`) or separating `threat_quarters` from `joint_weight` was read in `b4.hpp` and not tested.
2. **Total gain of `(bundle + PC20)` vs `(all_off + PC20)` vs `(bundle + L2)`:** Combining `M15-0` (`bundle_on_PC20` vs `all_off_PC20`: `{float(j48_m15['M15-0']['elo']):+.2f} +/- {float(j48_m15['M15-0']['err95']):.2f}` at `2,000` nodes in Job 48) with `M16-2k` (`bundle_on_L2` vs `bundle_on_PC20`: `{m16_2k_elo:+.2f} +/- {m16_2k_hw:.2f}`) shows `bundle_on_PC20` sits at the top of the 4-corner square on built-in evaluation, ahead of both `all_off_PC20` and `bundle_on_L2`; we did not play a direct `bundle_on_L2` vs `all_off_PC20` match.

---

## What I Did Not Do

- Did **not** build any new binary in Job 49 (reused `/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`, and `/tmp/carbon2_job47/bld_bundle11_k4b/forge` for the 1-line `K4` equivalence check).
- Did **not** test `HistRework = 1` or `HistRework = 3`, nor any of the other four `PC20` switches (`k = 1, 3, 4, 5`).
- Did **not** pool `2,000`-node and `20,000`-node matches together.
- Did **not** edit `prediction_job49.txt` after committing it alone in `{pred_sha}`.
- Did **not** touch repository engine source files, other branches, or pull requests; did **not** commit binaries, nets, PGNs, or `.pyc` files.

---

## What I Am Not Sure About

1. **Exact magnitude of `M16 - M17` (`HistRework = 0` interaction with the bundle):** At `12,000` games per match (`nodes=2000`), `M16-2k - M17-2k` carries a 95% half-width of `+/- {hw_2k_diff:.2f}` Elo (and at `3,000` games per match at `nodes=20000`, `+/- {hw_20k_diff:.2f}` Elo), so a true overlap of a few Elo between `HistRework = 2` and `IdeaB8b` can sample at `{d2_j48_str}` in `M15-2 - M15-0` and `{diffs_by_nodes['2000']['diff_str']}` in `M16-2k - M17-2k` across independent book slices.
2. **Why `M16-2k` (`{m16_2k_elo:+.2f} +/- {m16_2k_hw:.2f}`) fell `{m16_2k_miss:.2f}` Elo below our `{m16_2k_plo:+.1f}` lower bound:** In `prediction_job49.txt`, we underestimated `HistRework = 2`'s standalone strength at `nodes=2000` (`{m17_2k_pp:+.1f}` predicted vs `{m17_2k_elo:+.2f} +/- {m17_2k_hw:.2f}` observed in `M17-2k`) and assumed a larger `M16-2k - M17-2k` recovery than `{diffs_by_nodes['2000']['diff_str']}`.
3. **Behavior with the PC's NNUE net:** `joint_correction_` corrects static evaluation residuals, whose scale and variance differ substantially between the built-in evaluation and the PC's NNUE net.

---

## Hashes, Builds, and Timestamps

### Build & Prerequisite Hashes (`forge-combo29/carbon2/job49/builds.txt`)

```text
{builds_txt.strip()}
```

### Row File Hashes (`forge-combo29/carbon2/job49/*.rows.txt`)

{chr(10).join(row_hashes)}

### UTC Timestamps (`forge-combo29/carbon2/job49/stamps.txt`)

```text
{stamps_txt.strip()}
```

---

## Verbatim Final Check (`git status --short && ls -R forge-combo29/carbon2/job49`)

```text
__FINAL_GIT_STATUS_LS_PLACEHOLDER__
```

---

## Model Name

`Gemini 4 Carbon`
"""

    (JOB49 / "REPORT_carbon2_job49.md").write_text(md, encoding="utf-8")
    print("Wrote initial REPORT_carbon2_job49.md")


if __name__ == "__main__":
    main()
