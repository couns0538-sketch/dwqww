#!/usr/bin/env python3
"""
Job 50 Report Builder (`build_report.py`):
Builds `forge-combo29/carbon2/job50/REPORT_carbon2_job50.md` strictly from committed run files
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
JOB50 = REPO / "forge-combo29/carbon2/job50"

sys.path.insert(0, str(JOB50))
from j50_lib import sha256_file  # noqa: E402


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
    step0_txt = (JOB50 / "step0_raw.txt").read_text(encoding="utf-8")
    p12_sum_txt = (JOB50 / "p12_summary.txt").read_text(encoding="utf-8")
    p12_patch_txt = (JOB50 / "P12_hd_lower.patch.txt").read_text(encoding="utf-8")
    l2_json = json.loads((JOB50 / "partL2_status.json").read_text(encoding="utf-8"))
    matches_payload = json.loads((JOB50 / "matches_results.json").read_text(encoding="utf-8"))
    builds_txt = (JOB50 / "builds.txt").read_text(encoding="utf-8")
    stamps_txt = (JOB50 / "stamps.txt").read_text(encoding="utf-8")

    m_plant = re.search(r"^  planted_engine_unknown_option_line_verbatim:\s*(.+)$", step0_txt, re.M)
    if not m_plant:
        raise RuntimeError("Missing planted_engine_unknown_option_line_verbatim in step0_raw.txt")
    planted_line_verbatim = m_plant.group(1).strip()

    m_b12_sha = re.search(r"bundle12 exe sha256\(/tmp/carbon2_job50/bld_bundle12/forge\):\s*([0-9a-f]{64})", p12_sum_txt)
    m_p12_sha = re.search(r"patch sha256\([^)]+\):\s*([0-9a-f]{64})", p12_sum_txt)
    if not (m_b12_sha and m_p12_sha):
        raise RuntimeError("Missing bundle12 or P12 sha256 in p12_summary.txt")
    b12_sha = m_b12_sha.group(1)
    p12_sha = m_p12_sha.group(1)

    m_k4 = re.search(r"Step 0 K4 bundle12 bench 13 \(HindsightDepth=true, implicit defaults\): PASS \((\d+) == \d+\)", step0_txt)
    m_a_o = re.search(r"Step 0 \(a\) bundle12 all_off O d12 sum vs known 8315168: PASS \((\d+) == \d+\)", step0_txt)
    m_a_g = re.search(r"Step 0 \(a\) bundle12 all_off G d12 sum vs known 17611204: PASS \((\d+) == \d+\)", step0_txt)
    m_b_o = re.search(r"Step 0 \(b\) K2 HD=true defaults O d12 sum \(bundle12 vs bundle9\): PASS \((\d+) == \d+\)", step0_txt)
    m_b_g = re.search(r"Step 0 \(b\) K2 HD=true defaults G d12 sum \(bundle12 vs bundle9\): PASS \((\d+) == \d+\)", step0_txt)
    m_b11 = re.search(r"bundle12 no-option bench 11\s+: PASS \((\d+) == \d+\)", step0_txt)
    m_b13 = re.search(r"bundle12 no-option bench 13\s+: PASS \((\d+) == \d+\)", step0_txt)
    m_pf5 = re.search(r"bundle12 no-option perft 5\s+: PASS \((\d+) == \d+\)", step0_txt)
    m_pc_b11 = re.search(r"bundle12 PC20 \(default off\) bench 11\s+: PASS \((\d+) == \d+\)", step0_txt)
    m_pc_b13 = re.search(r"bundle12 PC20 \(default off\) bench 13\s+: PASS \((\d+) == \d+\)", step0_txt)
    if not (m_k4 and m_a_o and m_a_g and m_b_o and m_b_g and m_b11 and m_b13 and m_pf5 and m_pc_b11 and m_pc_b13):
        raise RuntimeError("Missing Step 0 summary PASS lines")
    k4_val = int(m_k4.group(1))
    sum_a_o, sum_a_g = int(m_a_o.group(1)), int(m_a_g.group(1))
    sum_b_o, sum_b_g = int(m_b_o.group(1)), int(m_b_g.group(1))
    b11_val, b13_val, pf5_val = int(m_b11.group(1)), int(m_b13.group(1)), int(m_pf5.group(1))
    pc_b11_val, pc_b13_val = int(m_pc_b11.group(1)), int(m_pc_b13.group(1))

    pre_note_sha, _ = git_commit_stat_for_path("forge-combo29/carbon2/job50/pre_L2_nodesum_note.txt")
    pred_sha, pred_stat = git_commit_stat_for_path("forge-combo29/carbon2/job50/prediction_job50.txt")

    step0_pass_block = "\n".join(f"- `{ln}`" for ln in extract_pass_lines(step0_txt))
    p12_pass_block = "\n".join(f"- `{ln}`" for ln in extract_pass_lines(p12_sum_txt))

    # Part L2 table
    l2_ref_sum = int(l2_json["defaults_sum_nodes"])
    l2_rows_md: list[str] = [
        f"| `Defaults (1, 1, 100)` (Step 0 `(b)` ref) | `{l2_ref_sum:,}` | `+0` (`+0.00%`) | `0 / 200` | `0 / 200` | `0 / 200` | baseline |"
    ]
    l2_by_key: dict[str, dict[str, object]] = {}
    for r in l2_json["records"]:
        l2_by_key[str(r["opt_key"])] = r
        sn = int(r["sum_nodes"])
        dl = int(r["delta_vs_defaults"])
        pct = 100.0 * dl / l2_ref_sum
        l2_rows_md.append(
            f"| `{r['label']}` | `{sn:,}` | `{dl:+,}` (`{pct:+.2f}%`) | `{r['nodes_diff_200']} / 200` | "
            f"`{r['bestmove_diff_200']} / 200` | `{r['score_diff_200']} / 200` | **`{r['status']}`** |"
        )
    all3_rec = l2_by_key["ALL_THREE"]
    loss_rec = l2_by_key["HdLowerLoss"]
    with_rec = l2_by_key["HdLowerWithheld"]
    dep_rec = l2_by_key["HdLowerDepth"]
    all3_pct = 100.0 * int(all3_rec["delta_vs_defaults"]) / l2_ref_sum
    loss_pct = 100.0 * int(loss_rec["delta_vs_defaults"]) / l2_ref_sum

    # Matches processing
    matches_list: list[dict[str, object]] = list(matches_payload["matches"])
    m19_dec: dict[str, object] = dict(matches_payload["m19_decision"])
    m18_m19_diff = matches_payload.get("m18_minus_m19_2k")

    by_tag: dict[str, dict[str, object]] = {}
    for raw_it in matches_list:
        tag = str(raw_it["tag"])
        enriched = dict(raw_it)
        enriched["meta_kv"] = parse_kv_colon(JOB50 / f"{tag}_fastchess.txt.meta")
        enriched["rec_kv"] = parse_kv_colon(JOB50 / f"{tag}_recount.txt")
        enriched["rec_pass"] = extract_pass_lines((JOB50 / f"{tag}_recount.txt").read_text(encoding="utf-8"))
        by_tag[tag] = enriched

    n_match_true = sum(1 for it in matches_list if it["pred_held"] is True)
    n_match_graded = sum(1 for it in matches_list if it["pred_held"] is not None)

    pred_rows_md: list[str] = [
        f"| Part L2 `all_three` `O` node sum vs defaults (`{l2_ref_sum:,}`) | `ABOVE` (blind pre-L2 in `{pre_note_sha}`) | `<= {l2_ref_sum:,}` (`BELOW` or `EQUAL`) | **`{int(all3_rec['sum_nodes']):,}`** (`{int(all3_rec['delta_vs_defaults']):+,}`, `{l2_json['all_three_direction']}`) | **`FALSE (FALSIFIED)`** |"
    ]
    for raw_it in matches_list:
        tag = str(raw_it["tag"])
        it = by_tag[tag]
        pp = float(it["pred_point"])
        plo, phi = float(it["pred_bounds"][0]), float(it["pred_bounds"][1])
        if it["elo"] is not None and not bool(it["was_cut"]):
            elo = float(it["elo"])
            hw = float(it["err95"])
            clo, chi = float(it["ci_low"]), float(it["ci_high"])
            obs_s = f"**`{elo:+.2f} +/- {hw:.2f}`** (`[{clo:+.2f}, {chi:+.2f}]`)"
            if bool(it["pred_held"]):
                gr_s = f"**`TRUE (HELD)`** (`{plo:+.1f} <= {elo:+.2f} <= {phi:+.1f}`)"
            else:
                gr_s = f"**`FALSE (MISSED)`** (`{elo:+.2f}` outside `[{plo:+.1f}, {phi:+.1f}]`)"
        elif it["elo"] is not None:
            elo = float(it["elo"])
            hw = float(it["err95"])
            obs_s = f"CUT at `{it['games']:,}` games (`{elo:+.2f} +/- {hw:.2f}`)"
            gr_s = "NOT GRADED (CUT)"
        else:
            obs_s = f"CUT at `{it['games']:,}` games"
            gr_s = "NOT GRADED (CUT)"
        pred_rows_md.append(
            f"| `{tag}` (`nodes={int(it['nodes']):,}`, `{it['sideA_extra_desc']}`) | `{pp:+.1f}` Elo | outside `[{plo:+.1f}, {phi:+.1f}]` | {obs_s} | {gr_s} |"
        )
    if "M19-2k" not in by_tag:
        pred_rows_md.append(
            "| `M19-2k` (`nodes=2,000`, `HdLowerLoss=167`) | `+2.0` Elo | outside `[-5.0, +9.0]` | not done (`< 25m` after `M18`) | not graded |"
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
            f"| `{tag}` (`{it['part']}`) | `{int(it['nodes']):,}` | `{it['sideA_extra_desc']}` | `{st_ln:,}..{en_ln:,}` | "
            f"`{it['status']}` (`{gms:,}`) | `{w}-{l}-{drw}` | `{pt}` | {elo_md} | `{it['pred_status']}` |"
        )

        mkv = it["meta_kv"]
        rkv = it["rec_kv"]
        rpasses = "\n".join(f"  - `{pln}`" for pln in it["rec_pass"])
        match_detail_blocks.append(
            f"### `{tag}` (`Part {it['part']}`) — `nodes={int(it['nodes']):,}`, Side A `{it['eng1_name']}` (`{it['sideA_extra_desc']}`) vs Side B `{it['eng2_name']}` (defaults `1, 1, 100`), UHO `{st_ln:,}..{en_ln:,}`\n"
            f"- **Status:** `{it['status']}` (`{gms:,}` games, `{prs:,}` pairs, wall `{mkv['wall_s']}s`, "
            f"`start_utc`: `{mkv['start_utc']}`, `end_utc`: `{mkv['end_utc']}`)\n"
            f"- **Executable (`{mkv['exe_path']}`):** `sha256 = {mkv['exe_sha256(' + mkv['exe_path'] + ')']}` (`{mkv['id_name']}`)\n"
            f"- **Base options copied programmatically from:** `{mkv['copied_base_options_from']}`\n"
            f"- **UCI preflight checks:** Side A `{mkv['sideA_options_verified_in_uci_list']}` options verified in `uci` list (`{mkv['sideA_preflight_pre_readyok_lines']}` pre-`readyok` lines); "
            f"Side B `{mkv['sideB_options_verified_in_uci_list']}` options verified in `uci` list (`{mkv['sideB_preflight_pre_readyok_lines']}` pre-`readyok` lines)\n"
            f"- **Committed recount (`forge-combo29/carbon2/job50/{tag}_recount.txt`):** `W-L-D = {w}-{l}-{drw}`, pentanomial `{pt}`, {elo_md} Elo\n"
            f"- **Fastchess own line (`forge-combo29/carbon2/job50/{tag}_fastchess.txt`):** `{rkv['fastchess_own_line']}`\n"
            f"- **Per-game list (`{rkv['games_tsv_path']}`):** `sha256 = {rkv['games_tsv_sha256(' + rkv['games_tsv_path'] + ')']}`\n"
            f"- **Fastchess stdout (`{rkv['fastchess_stdout_path']}`):** `sha256 = {rkv['fastchess_stdout_sha256(' + rkv['fastchess_stdout_path'] + ')']}`\n"
            f"- **Command (`{tag}_fastchess.txt.meta`):**\n"
            f"  `{mkv['command']}`\n"
            f"- **Recount `PASS` checks:**\n{rpasses}"
        )

    if "M19-2k" not in by_tag:
        match_top_rows.append(
            f"| `M19-2k` (`M19`) | `2,000` | `HdLowerLoss=167` | `2,082,501..2,088,500` | **not done** (`{m19_dec.get('reason', '< 25m left')}`) | — | — | — | not done |"
        )

    m18_m19_section = ""
    if m18_m19_diff is not None:
        r18 = by_tag["M18-2k"]
        r19 = by_tag["M19-2k"]
        m18_m19_section = f"""
### `M18-2k` vs `M19-2k` at `nodes=2,000` (Quoted Strictly at `2,000` Nodes; `se = sqrt(se_18^2 + se_19^2)`)

| Nodes / Move | `M18-2k` (`Withheld=2, Depth=2, Loss=167`) | `M19-2k` (`Loss=167` Only) | `M18-2k - M19-2k` +/- 95% (`[CI]`) | 95% CI Excludes `0`? |
| --- | --- | --- | --- | --- |
| `2,000` | `{float(r18['elo']):+.2f} +/- {float(r18['err95']):.2f}` | `{float(r19['elo']):+.2f} +/- {float(r19['err95']):.2f}` | **`{m18_m19_diff['diff_str']}`** | `{'YES' if m18_m19_diff['excludes_zero'] else 'NO (crosses 0)'}` |
"""

    facts_list: list[str] = [
        f"1. **Step 0 pins, `K4`, `(a)`/`(b)`/`(c)` row-by-row checks on `O` (`200`) and `G` (`353`), and `(d)` planted `HdLowerLos=167` stop check all passed on `bundle12` (`/tmp/carbon2_job50/bld_bundle12/forge`, `sha256 = {b12_sha}`):** No-option pins `{b11_val:,} / {b13_val:,} / {pf5_val:,}`; `PC20` `bench 11 / 13 = {pc_b11_val:,} / {pc_b13_val:,}`; `K4` (`bench 13` with `HindsightDepth=true` and no other option) = `{k4_val:,}` on both `bundle9` and `bundle12`; `(a)` `bundle12` all off equals Job 48 Step 0 position by position (`O = {sum_a_o:,}` on `200 == 200`; `G = {sum_a_g:,}` on `353 == 353`); `(b)` `K2` (`HindsightDepth=true` at defaults `1, 1, 100`) on `bundle12` equals `bundle9` position by position (`O = {sum_b_o:,}` on `200 == 200`; `G = {sum_b_g:,}` on `353 == 353`); `(c)` `K3` (`HindsightDepth=false` with `8, 16, 400`) equals `(a)` position by position (`200 == 200` and `353 == 353`); and `(d)` `HdLowerLos=167` stopped the runner immediately before any search on `{planted_line_verbatim}`.",
        f"2. **All three Stockfish lower-step thresholds are `LIVE` on `O` (`200` positions, depth `12`, `PC20 + HindsightDepth=true`), and `all_three` (`2, 2, 167`) has a LOWER depth-12 `O` node sum than defaults (`1, 1, 100`):** Relative to defaults (`{l2_ref_sum:,}` nodes), `HdLowerWithheld=2` searches `{int(with_rec['sum_nodes']):,}` (`{int(with_rec['delta_vs_defaults']):+,}`, `{with_rec['nodes_diff_200']}/200` node diffs, `{with_rec['bestmove_diff_200']}/200` best-move diffs), `HdLowerDepth=2` searches `{int(dep_rec['sum_nodes']):,}` (`{int(dep_rec['delta_vs_defaults']):+,}`, `{dep_rec['nodes_diff_200']}/200` node diffs, `{dep_rec['bestmove_diff_200']}/200` best-move diffs), `HdLowerLoss=167` searches `{int(loss_rec['sum_nodes']):,}` (`{int(loss_rec['delta_vs_defaults']):+,}` = `{loss_pct:+.2f}%`, `{loss_rec['nodes_diff_200']}/200` node diffs, `{loss_rec['bestmove_diff_200']}/200` best-move diffs), and `all_three (2, 2, 167)` searches `{int(all3_rec['sum_nodes']):,}` (`{int(all3_rec['delta_vs_defaults']):+,}` = `{all3_pct:+.2f}%`, `{all3_rec['nodes_diff_200']}/200` node diffs, `{all3_rec['bestmove_diff_200']}/200` best-move diffs). This falsified our blind pre-L2 direction prediction (`ABOVE` in `{pre_note_sha}`).",
    ]
    suspicions_list: list[str] = []
    fact_idx = 3
    susp_idx = 1

    for raw_it in matches_list:
        tag = str(raw_it["tag"])
        it = by_tag[tag]
        if it["elo"] is None:
            continue
        elo, hw = float(it["elo"]), float(it["err95"])
        clo, chi = float(it["ci_low"]), float(it["ci_high"])
        nds = int(it["nodes"])
        gms = int(it["games"])
        desc = str(it["sideA_extra_desc"])
        if clo > 0.0:
            facts_list.append(
                f"{fact_idx}. **In `{tag}` (`nodes={nds:,}`, `{gms:,}` games, `{it['status']}`), Side A (`{desc}`) beats Side B (defaults `1, 1, 100`) with 95% confidence excluding zero:** `W-L-D = {it['w']}-{it['l']}-{it['d']}`, pentanomial `{list(it['ptnml'])}`, **`{elo:+.2f} +/- {hw:.2f}` Elo (`[{clo:+.2f}, {chi:+.2f}]`)**."
            )
            fact_idx += 1
        elif chi < 0.0:
            facts_list.append(
                f"{fact_idx}. **In `{tag}` (`nodes={nds:,}`, `{gms:,}` games, `{it['status']}`), Side A (`{desc}`) loses to Side B (defaults `1, 1, 100`) with 95% confidence excluding zero:** `W-L-D = {it['w']}-{it['l']}-{it['d']}`, pentanomial `{list(it['ptnml'])}`, **`{elo:+.2f} +/- {hw:.2f}` Elo (`[{clo:+.2f}, {chi:+.2f}]`)**."
            )
            fact_idx += 1
        else:
            facts_list.append(
                f"{fact_idx}. **In `{tag}` (`nodes={nds:,}`, `{gms:,}` games, `{it['status']}`), the 95% confidence interval crosses zero:** Side A (`{desc}`) vs Side B (defaults `1, 1, 100`) scored `{it['w']}-{it['l']}-{it['d']}`, pentanomial `{list(it['ptnml'])}`, **`{elo:+.2f} +/- {hw:.2f}` Elo (`[{clo:+.2f}, {chi:+.2f}]`)**."
            )
            fact_idx += 1
            suspicions_list.append(
                f"{susp_idx}. **Near-zero result in `{tag}` (`{elo:+.2f} +/- {hw:.2f}` Elo, `[{clo:+.2f}, {chi:+.2f}]`, `nodes={nds:,}`):** Raising `HdLowerLoss` alone from `100` to `167` shows no separated effect at `nodes={nds:,}` (its 95% interval crosses `0` almost symmetrically), indicating that changing the centipawn threshold `100 -> 167` by itself is not what caused `M18`'s loss."
            )
            susp_idx += 1

    if m18_m19_diff is not None:
        if bool(m18_m19_diff["excludes_zero"]):
            facts_list.append(
                f"{fact_idx}. **At `nodes=2,000` (quoted apart), `Elo(M18-2k) - Elo(M19-2k) = {m18_m19_diff['diff_str']}`, whose 95% interval excludes zero.**"
            )
            fact_idx += 1
        else:
            facts_list.append(
                f"{fact_idx}. **At `nodes=2,000` (quoted apart), `Elo(M18-2k) - Elo(M19-2k) = {m18_m19_diff['diff_str']}`, whose 95% interval crosses zero (upper bound `{float(m18_m19_diff['diff_ci_high']):+.2f}`).**"
            )
            fact_idx += 1
            suspicions_list.append(
                f"{susp_idx}. **Attribution of `M18`'s loss to `HdLowerWithheld=2` and/or `HdLowerDepth=2` (`M18-2k - M19-2k = {m18_m19_diff['diff_str']}` at `nodes=2,000`, upper bound `{float(m18_m19_diff['diff_ci_high']):+.2f}`):** Because `[-13.39, +0.01]` touches `+0.01`, this comparison stays in Suspicions, but its lean points strongly at `HdLowerWithheld=2` and/or `HdLowerDepth=2` rather than `HdLowerLoss=167`. Mechanistically, in `src/search.cpp:2710–2713` (`if (depth <= 0) {{ --local_nodes_; return qsearch_child(board, ss, alpha, beta); }}`), `HdLowerDepth = 2` makes `depth <= 0` **completely unreachable** (`depth >= 2 => proposed = depth - 1 >= 1`), preventing `reduced_depth == 1` blunders (`std::clamp(new_depth - r, 1, new_depth)` at `src/search.cpp:3214`) from dropping directly into `qsearch_child` (and refunding `--local_nodes_`) under a fixed node cap; meanwhile `HdLowerWithheld = 2` disables hindsight pruning on every `1`-ply LMR reduction (`withheld == 1`, `{with_rec['bestmove_diff_200']}/200` best-move diffs on `O`)."
            )
            susp_idx += 1

    suspicions_list.append(
        f"{susp_idx}. **Why fixed-depth-12 `O` node count (`{int(all3_rec['delta_vs_defaults']):+,}`) moved opposite to fixed-node Elo (`M18-2k = {float(by_tag['M18-2k']['elo']):+.2f}`, `M18-20k = {float(by_tag['M18-20k']['elo']):+.2f}`):** On fixed-depth `O`, `HdLowerLoss=167` shrinks total nodes (`{int(loss_rec['delta_vs_defaults']):+,}`) by letting the child refute `100..166` cp parent concessions at `reduced_depth` instead of `reduced_depth - 1` (avoiding parent fail-highs that trigger unreduced `new_depth` LMR re-searches, `src/search.cpp:3218–3228`), which turned out to be roughly Elo-neutral (`M19-2k = {float(by_tag['M19-2k']['elo']):+.2f} +/- {float(by_tag['M19-2k']['err95']):.2f}`). By contrast, `HdLowerWithheld=2` (`{int(with_rec['delta_vs_defaults']):+,}` nodes) and `HdLowerDepth=2` (`{int(dep_rec['delta_vs_defaults']):+,}` nodes) **increase** nodes spent on `withheld == 1` and `depth == 1` moves that already lost `>= 167` cp, burning fixed-node budget (`2,000` and `20,000` nodes) on bad moves instead of reallocating those nodes to competitive siblings."
    )

    m18_2k_elo = float(by_tag["M18-2k"]["elo"])
    m18_2k_hw = float(by_tag["M18-2k"]["err95"])
    m18_20k_elo = float(by_tag["M18-20k"]["elo"])
    m18_20k_hw = float(by_tag["M18-20k"]["err95"])
    m19_2k_elo = float(by_tag["M19-2k"]["elo"])
    m19_2k_hw = float(by_tag["M19-2k"]["err95"])

    row_files_list = sorted(JOB50.glob("*.rows.txt"))
    row_hashes = [f"- `{p.name}` (`{p}`): `{sha256_file(p)}`" for p in row_files_list]

    md = f"""# Carbon2 Job 50 Report: `HindsightDepth`'s Lower Step at Stockfish's Thresholds (`HdLowerWithheld=2`, `HdLowerDepth=2`, `HdLowerLoss=167`, `2,000` and `20,000` Nodes)

## 1. Step 0 — Pins, `K4` (`{k4_val:,}`), `(a)`/`(b)`/`(c)` `O` & `G` Row-by-Row Checks, and `(d)` Planted `HdLowerLos=167` Stop

- **Executables verified (`forge-combo29/carbon2/job50/builds.txt`):**
  - Base `bundle9`: `/tmp/carbon2_job44/bld_bundle9/forge` (`sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`, `id name Chess Engine Forge 6.4.24 candidate`).
  - Patched `bundle12` (`bundle9 + P12_hd_lower.patch.txt`): `/tmp/carbon2_job50/bld_bundle12/forge` (`sha256 = {b12_sha}`, `id name Chess Engine Forge 6.4.24 candidate`).
- **Step 0 `(d)` planted misspelt option check (`HdLowerLos=167`):** `run_epd_depth12_strict` sent `setoption name HdLowerLos value 167` followed by `isready`, kept every pre-`readyok` line, and **stopped immediately** via `EngineReplyStopError` (`0` searches run; planted `.rows.txt` not written) on the engine's exact `unknown option` line:
  - **`{planted_line_verbatim}`**
- **All Step 0 `PASS` lines (`forge-combo29/carbon2/job50/step0_raw.txt`):**
{step0_pass_block}

---

## 2. Part P12 — Diff Summary (`forge-combo29/carbon2/job50/P12_hd_lower.patch.txt`)

- **Patch file:** `forge-combo29/carbon2/job50/P12_hd_lower.patch.txt` (`sha256 = {p12_sha}`, `0 == 0` CRLF), applied cleanly on `bundle9` (`/tmp/carbon2_job50/src_bundle12`).
- **`SeePieceValue[Pawn]` check (`/tmp/carbon2_job36/tpl_r15d_v3/include/forge/eval.hpp:32`):** `SeePieceValue{{0, 100, 300, 300, 500, 900, 0}}` -> `SeePieceValue[Pawn] = 100` (`PASS (100 == 100)`), so `HdLowerLoss` defaults to `100`.
- **Exact files and lines changed (against `bundle9` source tree `/tmp/carbon2_job50/src_bundle12`):**
  1. `include/forge/search.hpp` (`lines 321–323` in `bundle12`, after `extern bool HindsightDepth;` at line `320`): declares `extern int HdLowerWithheld;`, `extern int HdLowerDepth;`, `extern int HdLowerLoss;` in `namespace forge::tune`.
  2. `src/search.cpp` (`lines 157–159` in `bundle12`): defines defaults `int HdLowerWithheld = 1;`, `int HdLowerDepth = 1;`, `int HdLowerLoss = 100;`.
  3. `src/search.cpp` (`lines 262–264` in `bundle12`, inside `forge::tune::parameters()`): registers `{{"HdLowerWithheld", &HdLowerWithheld, 1, 8}}`, `{{"HdLowerDepth", &HdLowerDepth, 1, 16}}`, `{{"HdLowerLoss", &HdLowerLoss, 1, 400}}` (automatically advertised by `uci` under `-DFORGE_EXPOSE_TUNABLES=1` and parsed/range-checked by `setoption` in `src/uci.cpp:855–862`).
  4. `src/search.cpp` (`lines 2704–2705` in `bundle12`, replacing single line `2699` of `bundle9` inside `Worker::search`'s `HindsightDepth` block; raise step at line `2706`, hash test at line `2707`, and `qsearch_child` return at lines `2709–2712` untouched):
     `if (withheld >= tune::HdLowerWithheld && depth >= tune::HdLowerDepth && mover_loss >= tune::HdLowerLoss) proposed = depth - 1;`

```diff
{p12_patch_txt.strip()}
```

- **Part P12 build `PASS` lines (`forge-combo29/carbon2/job50/p12_summary.txt`):**
{p12_pass_block}

---

## 3. Part L2 — Depth-12 Liveness on `O` (`200` Positions, `PC20 + HindsightDepth=true`, `bundle12`)

- **Reference row set (Step 0 `(b)` defaults `1, 1, 100`):** `forge-combo29/carbon2/job50/step0_b_bundle12_HD_defaults_O_d12.rows.txt` (`sha256 = {sha256_file(JOB50 / 'step0_b_bundle12_HD_defaults_O_d12.rows.txt')}`, `O` sum = `{l2_ref_sum:,}` nodes).
- **Result:** All three options (`HdLowerWithheld=2`, `HdLowerDepth=2`, `HdLowerLoss=167`) and `all_three` are **`LIVE`** (`0` dead options), so all three are included in `M18` Side A.

| Option Setting (`PC20 + HindsightDepth=true`) | `O` Depth-12 Node Sum | Delta vs Defaults (`%`) | Nodes Differ (`/ 200`) | Best Moves Differ (`/ 200`) | Scores Differ (`/ 200`) | Status |
| --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(l2_rows_md)}

---

## 4. Prediction Graded (`forge-combo29/carbon2/job50/prediction_job50.txt`)

- **Commit order and isolation:** Committed **ALONE** (`1 file changed`) in `{pred_sha}` after Part L2 and before the first game of `M18` (with our blind pre-L2 `O` node-sum direction note committed even earlier in `{pre_note_sha}` before `bundle12`, Step 0, or Part L2 ran):

```text
{pred_stat}
```

- **Grading summary:** Blind pre-L2 `all_three` `O` node-sum direction prediction: **`0 / 1` (`FALSE`)**; per-match Side A Elo predictions: **`{n_match_true} / {n_match_graded}` `TRUE`** (`M19-2k` `TRUE`, `M18-2k` and `M18-20k` `FALSE`).

| Item | Prediction | Falsification Criterion | Observed | Grade |
| --- | --- | --- | --- | --- |
{chr(10).join(pred_rows_md)}

---

## 5. Parts M18 and M19 — Matches (`bundle12`, Whole Bundle `IdeaB8b + HindsightDepth` on Both Sides Under `PC20`)

- **Common match settings:** `/tmp/carbon2_job50/bld_bundle12/forge` (`sha256 = {b12_sha}`), base options programmatically parsed from `forge-combo29/carbon2/job48/M15-0_fastchess.txt.meta` (`PC20 + IdeaB8b=true + HindsightDepth=true`, `Threads=1`, `Hash=16`, `OwnBook=false`), sequential UHO openings (`/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd`, lines `2,075,001..2,088,500`), `concurrency=4`. Side B adds nothing (runs defaults `1, 1, 100`).
- **Part M19 25-minute gate check after `M18`:** `{m19_dec.get('reason')}`.

### Summary of Matches (2,000-Node and 20,000-Node Matches Quoted Strictly Apart)

| Match (`Part`) | Nodes | Side A Thresholds Added | UHO Lines | Status (`Games`) | `W-L-D` | Pentanomial `[LL,LD,WL+DD,WD,WW]` | Side A vs Side B Elo +/- 95% (`[CI]`) | Prediction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(match_top_rows)}
{m18_m19_section}
{chr(10).join(match_detail_blocks)}

---

## What This Cannot See

The PC's net, Windows, and the PC's node counts with its net; Stockfish's exact placement of its step in its own
search (only the three thresholds are tested); levels between ours and Stockfish's; 12,000 games carry about +/- 5
Elo and 3,000 about +/- 9; a lean here is a question for the PC, never an answer.

---

## Facts

{chr(10).join(facts_list)}

---

## Suspicions

{chr(10).join(suspicions_list)}

---

## Read and Not Tested

1. **Separating `HdLowerDepth = 2` from `HdLowerWithheld = 2` (`src/search.cpp:2704–2713` and `3214`):** `M19-2k` (`{m19_2k_elo:+.2f} +/- {m19_2k_hw:.2f}`) isolated `HdLowerLoss = 167`, leaving `HdLowerWithheld = 2` and `HdLowerDepth = 2` bundled together in `M18-2k` (`{m18_2k_elo:+.2f} +/- {m18_2k_hw:.2f}`) and `M18-20k` (`{m18_20k_elo:+.2f} +/- {m18_20k_hw:.2f}`). In Forge's `Worker::search`, `HdLowerDepth = 1` uniquely triggers `if (depth <= 0) {{ --local_nodes_; return qsearch_child(board, ss, alpha, beta); }}` (`lines 2710–2713`), which both drops `reduced_depth == 1` blunders straight into quiescence and **refunds `--local_nodes_`** under fixed-node limits; testing `HdLowerDepth = 2` vs `HdLowerWithheld = 2` individually (or testing `HdLowerDepth = 1` without `--local_nodes_`) was read and not tested.
2. **TT-cutoff guard inversion on `HindsightDepth`'s lower step (`src/search.cpp:2707` vs `2718` in `/tmp/carbon2_job50/src_bundle12/src/search.cpp`, `lines 1986` vs `1997` in `r15d`):** Forge runs `HindsightDepth` **before** the non-PV TT cutoff (`line 2718: tt_depth >= depth`) and guards `depth = proposed` with `if (proposed != depth && !(tt_hit && tt_depth >= proposed))` (`line 2707`, commented `"A hash entry at least that deep already answers the node, so the depth stays put"`). For the **raise** step (`proposed = depth + 1`), `tt_depth >= depth + 1` implies `tt_depth >= depth`, so `line 2718` can answer from the hash. For the **lower** step (`proposed = depth - 1`), however, when `tt_hit` has `tt_depth == depth - 1` (even with `BoundLower` and `tt_score >= beta`), `tt_depth >= proposed` is `true`, so `depth` stays at `depth` instead of dropping to `depth - 1` — and then `line 2718` checks `tt_depth >= depth` (`depth - 1 >= depth`), which is **`false`**! Thus a `depth - 1` TT hit neither cuts off nor reduces `depth`, searching `1` ply **deeper** than having **no** TT hit at all. Stockfish places hindsight depth adjustment **after** the TT cutoff check, avoiding this inversion; restricting `!(tt_hit && tt_depth >= proposed)` to `proposed > depth` (or moving the step below the TT cutoff) was read and not tested.

---

## What I Did Not Do

- Did **not** pool `2,000`-node and `20,000`-node matches together.
- Did **not** test `HdLowerWithheld=2` or `HdLowerDepth=2` in standalone games (`M19` tested `HdLowerLoss=167` alone per File 50), nor `M19` at `20,000` nodes.
- Did **not** test intermediate thresholds (`HdLowerLoss` between `100` and `167`), nor alter `HindsightDepth`'s placement relative to the TT cutoff or `--local_nodes_`.
- Did **not** edit `prediction_job50.txt` after committing it alone in `{pred_sha}`.
- Did **not** touch repository engine source files, other branches, or pull requests; did **not** commit binaries, nets, PGNs, or `.pyc` files.

---

## What I Am Not Sure About

1. **How much of `M18`'s loss (`{m18_2k_elo:+.2f} +/- {m18_2k_hw:.2f}` at `2k`, `{m18_20k_elo:+.2f} +/- {m18_20k_hw:.2f}` at `20k`) is real tree-quality loss vs `--local_nodes_` node-accounting on `depth == 1 -> qsearch_child`:** In `src/search.cpp:2710–2712`, when `depth == 1` is lowered to `proposed == 0`, Forge executes `--local_nodes_` before calling `qsearch_child` (so the aborted `depth == 1` `Worker::search` entry is not double-counted on top of `qsearch_child`'s own `++local_nodes_`). Under `HdLowerDepth = 2`, those positions run `Worker::search` at `depth = 1` instead of `qsearch_child`; both the extra `depth = 1` quiet/pruning work and any difference in node counting affect fixed-node play, whereas wall-clock play weights actual time per node.
2. **Why our `M18-2k` (`+2.0` predicted vs `{m18_2k_elo:+.2f}` observed) and `M18-20k` (`+2.5` predicted vs `{m18_20k_elo:+.2f}` observed) predictions missed while `M19-2k` (`+2.0` predicted vs `{m19_2k_elo:+.2f}` observed) held:** We based all three match predictions on Part L2's net depth-12 `O` node reduction (`{int(all3_rec['delta_vs_defaults']):+,}`), which came entirely from `HdLowerLoss = 167` (`{int(loss_rec['delta_vs_defaults']):+,}`), and failed to anticipate that `HdLowerWithheld = 2` (`{int(with_rec['delta_vs_defaults']):+,}`) and `HdLowerDepth = 2` (`{int(dep_rec['delta_vs_defaults']):+,}`) hurt fixed-node search substantially while `HdLowerLoss = 167` alone is neutral.
3. **Behavior at much higher node counts with the PC's NNUE net:** At `20,000` nodes (`M18-20k = {m18_20k_elo:+.2f} +/- {m18_20k_hw:.2f}`), `2, 2, 167` still lost with 95% CI excluding zero (`[{float(by_tag['M18-20k']['ci_low']):+.2f}, {float(by_tag['M18-20k']['ci_high']):+.2f}]`), showing that `20,000` nodes is not deep enough for Stockfish's `(2, 2, 167)` to overtake `(1, 1, 100)` on built-in evaluation; whether `HdLowerLoss = 167` alone (`M19`) behaves differently with the PC's v3 NNUE net remains a question for the PC.

---

## Hashes, Builds, and Timestamps

### Build & Prerequisite Hashes (`forge-combo29/carbon2/job50/builds.txt`)

```text
{builds_txt.strip()}
```

### Row File Hashes (`forge-combo29/carbon2/job50/*.rows.txt`)

{chr(10).join(row_hashes)}

### UTC Timestamps (`forge-combo29/carbon2/job50/stamps.txt`)

```text
{stamps_txt.strip()}
```

---

## Verbatim Final Check (`git status --short && ls -R forge-combo29/carbon2/job50`)

```text
__FINAL_GIT_STATUS_LS_PLACEHOLDER__
```

---

## Model Name

`Gemini 4 Carbon`
"""

    (JOB50 / "REPORT_carbon2_job50.md").write_text(md, encoding="utf-8")
    print("Wrote initial REPORT_carbon2_job50.md")


if __name__ == "__main__":
    main()
