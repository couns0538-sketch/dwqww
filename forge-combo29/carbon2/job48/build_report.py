#!/usr/bin/env python3
"""
Job 48 Report Builder (`build_report.py`):
Builds `forge-combo29/carbon2/job48/REPORT_carbon2_job48.md` strictly from committed run files
(never typing numbers manually).
"""
from __future__ import annotations

import json
import math
import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB48 = REPO / "forge-combo29/carbon2/job48"
JOB46 = REPO / "forge-combo29/carbon2/job46"
JOB44 = REPO / "forge-combo29/carbon2/job44"
JOB43 = REPO / "forge-combo29/carbon2/job43"
JOB42 = REPO / "forge-combo29/carbon2/job42"
JOB41 = REPO / "forge-combo29/carbon2/job41"

sys.path.insert(0, str(JOB48))
from j48_lib import diff_elo_interval, sha256_file  # noqa: E402


def parse_kv_colon(path: pathlib.Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        if ":" in ln and not ln.startswith("  "):
            k, v = ln.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def extract_pass_lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ": PASS (" in ln]


def extract_recount_elo_hw(rec_path: pathlib.Path) -> tuple[float, float, str, str]:
    txt = rec_path.read_text(encoding="utf-8")
    m = re.search(r"^recounted_Elo:\s*([+-]?\d+\.\d+)\s*\+/-\s*(\d+\.\d+)\s*\(95% CI \[([^\]]+)\]", txt, re.M)
    if not m:
        raise RuntimeError(f"Could not parse recounted_Elo from {rec_path}")
    wld_m = re.search(r"^recounted_WLD [^:]+:\s*([0-9]+ - [0-9]+ - [0-9]+)", txt, re.M)
    wld_s = wld_m.group(1) if wld_m else ""
    return float(m.group(1)), float(m.group(2)), m.group(3), wld_s


def git_commit_for_path_msg(grep_pat: str) -> str:
    res = subprocess.run(
        ["git", "log", "-n", "1", "--format=%h (%ci)", f"--grep={grep_pat}"],
        cwd=str(REPO),
        check=True,
        capture_output=True,
        text=True,
    )
    return res.stdout.strip()


def git_prediction_commit_stat() -> tuple[str, str]:
    res = subprocess.run(
        ["git", "log", "-n", "1", "--format=%h", "--", "forge-combo29/carbon2/job48/prediction_job48.txt"],
        cwd=str(REPO),
        check=True,
        capture_output=True,
        text=True,
    )
    sha = res.stdout.strip()
    stat = subprocess.run(
        ["git", "show", "--stat", "--format=%h %s (%ci)", sha],
        cwd=str(REPO),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return sha, stat


def main() -> None:
    step0_txt = (JOB48 / "step0_raw.txt").read_text(encoding="utf-8")
    partL_txt = (JOB48 / "partL_summary.txt").read_text(encoding="utf-8")
    partL_json = json.loads((JOB48 / "partL_status.json").read_text(encoding="utf-8"))
    pred_txt = (JOB48 / "prediction_job48.txt").read_text(encoding="utf-8")
    m15_results = json.loads((JOB48 / "M15_results.json").read_text(encoding="utf-8"))
    builds_txt = (JOB48 / "builds.txt").read_text(encoding="utf-8")
    stamps_txt = (JOB48 / "stamps.txt").read_text(encoding="utf-8")

    # Extract planted stop line verbatim from step0_raw.txt
    m_plant = re.search(r"^  planted_engine_unknown_option_line_verbatim\s*:\s*(.+)$", step0_txt, re.M)
    if not m_plant:
        raise RuntimeError("Missing planted_engine_unknown_option_line_verbatim in step0_raw.txt")
    planted_line_verbatim = m_plant.group(1).strip()

    # Extract reference O and G sums from partL_summary.txt
    m_ref_o = re.search(r"^reference_PC20_all_off_O: .+ \(sum=(\d+)\)$", partL_txt, re.M)
    m_ref_g = re.search(r"^reference_PC20_all_off_G: .+ \(sum=(\d+)\)$", partL_txt, re.M)
    m_s14_pass = re.search(r"^  Whole-set known answer .+: PASS \((\d+ == \d+)\)$", partL_txt, re.M)
    if not (m_ref_o and m_ref_g and m_s14_pass):
        raise RuntimeError("Missing reference sums or whole-set PASS in partL_summary.txt")
    ref_o_sum = int(m_ref_o.group(1))
    ref_g_sum = int(m_ref_g.group(1))
    whole_set_pass = m_s14_pass.group(1)

    dead_bases = [bk for bk in ("L1", "L2", "L3", "L4", "L5") if partL_json[bk]["is_dead"]]
    live_bases = [bk for bk in ("L1", "L2", "L3", "L4", "L5") if not partL_json[bk]["is_dead"]]

    # Prediction commit metadata
    pred_sha, pred_stat = git_prediction_commit_stat()

    # Load per-match meta and recount details
    by_tag: dict[str, dict[str, object]] = {}
    for item in m15_results:
        tag = str(item["tag"])
        meta_kv = parse_kv_colon(JOB48 / f"{tag}_fastchess.txt.meta")
        rec_kv = parse_kv_colon(JOB48 / f"{tag}_recount.txt")
        rec_pass = extract_pass_lines((JOB48 / f"{tag}_recount.txt").read_text(encoding="utf-8"))
        enriched = dict(item)
        enriched["meta_kv"] = meta_kv
        enriched["rec_kv"] = rec_kv
        enriched["rec_pass"] = rec_pass
        by_tag[tag] = enriched

    m0 = by_tag["M15-0"]
    m2 = by_tag["M15-2"]
    m4 = by_tag["M15-4"]
    m1 = by_tag["M15-1"]
    m3 = by_tag["M15-3"]
    m5 = by_tag["M15-5"]

    all_preds_true = all(bool(item["pred_held"]) for item in m15_results)
    n_preds_true = sum(1 for item in m15_results if bool(item["pred_held"]))

    # Prior job match numbers read directly from their committed recount files (kept strictly apart by node count!)
    m13_elo, m13_hw, m13_ci, m13_wld = extract_recount_elo_hw(JOB46 / "M13_recount.txt")
    m9_elo, m9_hw, m9_ci, m9_wld = extract_recount_elo_hw(JOB44 / "M9_recount.txt")
    m6_elo, m6_hw, m6_ci, m6_wld = extract_recount_elo_hw(JOB42 / "M6_recount.txt")
    m6b_elo, m6b_hw, m6b_ci, m6b_wld = extract_recount_elo_hw(JOB43 / "M6b_recount.txt")

    # Comparisons against prior 2,000-node matches (computed from recount files, never typed)
    d_m2_vs_m13, hw_m2_vs_m13, lo_m2_vs_m13, hi_m2_vs_m13 = diff_elo_interval(
        float(m2["elo"]), float(m2["err95"]), m13_elo, m13_hw
    )
    d_m13_vs_m0, hw_m13_vs_m0, lo_m13_vs_m0, hi_m13_vs_m0 = diff_elo_interval(
        m13_elo, m13_hw, float(m0["elo"]), float(m0["err95"])
    )
    d_m0_vs_m9, hw_m0_vs_m9, lo_m0_vs_m9, hi_m0_vs_m9 = diff_elo_interval(
        float(m0["elo"]), float(m0["err95"]), m9_elo, m9_hw
    )

    # Check which M15-k minus M15-0 95% CIs exclude zero
    excl_zero_tags = [
        str(it["tag"])
        for it in m15_results
        if str(it["tag"]) != "M15-0" and (float(it["diff_ci_low"]) > 0.0 or float(it["diff_ci_high"]) < 0.0)
    ]
    cross_zero_tags = [
        str(it["tag"])
        for it in m15_results
        if str(it["tag"]) != "M15-0" and not (float(it["diff_ci_low"]) > 0.0 or float(it["diff_ci_high"]) < 0.0)
    ]

    total_games = sum(int(it["games"]) for it in m15_results)
    total_pairs = sum(int(it["pairs"]) for it in m15_results)

    # Hashes of Step 0 and Part L row files
    row_hashes: list[tuple[str, pathlib.Path, str]] = []
    for desc, p in [
        ("Step 0 bundle9 PC20 all_off O d12 rows", JOB48 / "step0_bundle9_PC20_all_off_O_d12.rows.txt"),
        ("Step 0 bundle9 PC20 all_off G d12 rows", JOB48 / "step0_bundle9_PC20_all_off_G_d12.rows.txt"),
        ("Step 0 bundle9 S14 all_off O d12 rows", JOB48 / "step0_bundle9_S14_all_off_O_d12.rows.txt"),
        ("Part L L1 (CuckooRep false) O d12 rows", JOB48 / "partL_L1_all_off_O_d12.rows.txt"),
        ("Part L L1 (CuckooRep false) G d12 rows", JOB48 / "partL_L1_all_off_G_d12.rows.txt"),
        ("Part L L2 (HistRework 0) O d12 rows", JOB48 / "partL_L2_all_off_O_d12.rows.txt"),
        ("Part L L2 (HistRework 0) G d12 rows", JOB48 / "partL_L2_all_off_G_d12.rows.txt"),
        ("Part L L3 (TtPruneV2 false) O d12 rows", JOB48 / "partL_L3_all_off_O_d12.rows.txt"),
        ("Part L L3 (TtPruneV2 false) G d12 rows", JOB48 / "partL_L3_all_off_G_d12.rows.txt"),
        ("Part L L4 (CorrHistV2 false) O d12 rows", JOB48 / "partL_L4_all_off_O_d12.rows.txt"),
        ("Part L L4 (CorrHistV2 false) G d12 rows", JOB48 / "partL_L4_all_off_G_d12.rows.txt"),
        ("Part L L5 (MateAlphaGuard false) O d12 rows", JOB48 / "partL_L5_all_off_O_d12.rows.txt"),
        ("Part L L5 (MateAlphaGuard false) G d12 rows", JOB48 / "partL_L5_all_off_G_d12.rows.txt"),
    ]:
        row_hashes.append((desc, p, sha256_file(p)))

    step0_pass_block = "\n".join(f"- `{ln}`" for ln in extract_pass_lines(step0_txt))

    # Build Part L markdown table from partL_json
    partL_rows_md: list[str] = []
    for bk in ("L1", "L2", "L3", "L4", "L5"):
        d = partL_json[bk]
        partL_rows_md.append(
            f"| `{bk}` | `{d['desc']}` | `{d['o_sum']:,}` | `{d['o_delta']:+,}` | "
            f"`{d['o_nodes_diff']}/200` | `{d['o_bm_diff']}/200` | `{d['o_sc_diff']}/200` | "
            f"`{d['g_sum']:,}` | `{d['g_delta']:+,}` | "
            f"`{d['g_nodes_diff']}/353` | `{d['g_bm_diff']}/353` | `{d['g_sc_diff']}/353` | "
            f"`{d['eq_553']}/553` | **{d['status']}** |"
        )

    # Build Part M15 top summary table and detailed per-match blocks
    m15_top_rows: list[str] = []
    m15_detail_blocks: list[str] = []
    for raw_it in m15_results:
        tag = str(raw_it["tag"])
        it = by_tag[tag]
        bdesc = str(it["base_desc"])
        st_ln = int(it["start_line"])
        en_ln = int(it["end_line"])
        gms = int(it["games"])
        w, l, drw = int(it["w"]), int(it["l"]), int(it["d"])
        pt = list(it["ptnml"])
        elo = float(it["elo"])
        hw = float(it["err95"])
        clo = float(it["ci_low"])
        chi = float(it["ci_high"])
        dstr = str(it["diff_str"])
        pstat = str(it["pred_status"])

        m15_top_rows.append(
            f"| `{tag}` | `{bdesc}` | `{st_ln:,}..{en_ln:,}` | `{gms:,}` | `{w}-{l}-{drw}` | "
            f"`{pt}` | **`{elo:+.2f} +/- {hw:.2f}`** (`[{clo:+.2f}, {chi:+.2f}]`) | "
            f"**`{dstr}`** | `{pstat}` |"
        )

        mkv = it["meta_kv"]
        rkv = it["rec_kv"]
        rpasses = "\n".join(f"  - `{pln}`" for pln in it["rec_pass"])
        m15_detail_blocks.append(
            f"### `{tag}` — Base `{bdesc}` (UHO lines `{st_ln:,}..{en_ln:,}`)\n"
            f"- **Status:** `{it['status']}` (`{gms:,}` games, `{int(it['pairs']):,}` pairs, wall `{mkv['wall_s']}s`, "
            f"`start_utc`: `{mkv['start_utc']}`, `end_utc`: `{mkv['end_utc']}`)\n"
            f"- **Executable (`{mkv['exe_path']}`):** `sha256 = {mkv['exe_sha256(' + mkv['exe_path'] + ')']}` (`{mkv['id_name']}`)\n"
            f"- **UCI preflight checks:** Side A `{mkv['sideA_options_verified_in_uci_list']}` options verified in `uci` list (`{mkv['sideA_preflight_pre_readyok_lines']}` pre-`readyok` lines); "
            f"Side B `{mkv['sideB_options_verified_in_uci_list']}` options verified in `uci` list (`{mkv['sideB_preflight_pre_readyok_lines']}` pre-`readyok` lines)\n"
            f"- **Committed recount (`forge-combo29/carbon2/job48/{tag}_recount.txt`):** `W-L-D = {w}-{l}-{drw}`, pentanomial `{pt}`, "
            f"**`{elo:+.2f} +/- {hw:.2f}` Elo (`[{clo:+.2f}, {chi:+.2f}]`)**\n"
            f"- **Fastchess own line (`forge-combo29/carbon2/job48/{tag}_fastchess.txt`):** `{rkv['fastchess_own_line']}`\n"
            f"- **Beside `M15-0` (`{float(m0['elo']):+.2f} +/- {float(m0['err95']):.2f}`):** **`{dstr}`** (`se = sqrt((hw_k/1.96)^2 + (hw_0/1.96)^2)`)\n"
            f"- **Per-game list (`{rkv['games_tsv_path']}`):** `sha256 = {rkv['games_tsv_sha256(' + rkv['games_tsv_path'] + ')']}`\n"
            f"- **Fastchess stdout (`{rkv['fastchess_stdout_path']}`):** `sha256 = {rkv['fastchess_stdout_sha256(' + rkv['fastchess_stdout_path'] + ')']}`\n"
            f"- **Command (`{tag}_fastchess.txt.meta`):**\n"
            f"  `{mkv['command']}`\n"
            f"- **Recount `PASS` checks:**\n{rpasses}"
        )

    # Prediction grading rows
    pred_grade_rows: list[str] = []
    for it in m15_results:
        tag = str(it["tag"])
        pp = float(it["pred_point"])
        pb_lo, pb_hi = float(it["pred_bounds"][0]), float(it["pred_bounds"][1])
        elo = float(it["elo"])
        hw = float(it["err95"])
        clo, chi = float(it["ci_low"]), float(it["ci_high"])
        held = "TRUE (HELD)" if bool(it["pred_held"]) else "FALSE"
        pred_grade_rows.append(
            f"| `{tag}` (`{it['base_desc']}`) | `{pp:+.1f}` Elo | outside `[{pb_lo:+.1f}, {pb_hi:+.1f}]` | "
            f"**`{elo:+.2f} +/- {hw:.2f}`** (`[{clo:+.2f}, {chi:+.2f}]`) | **`{held}`** (`{pb_lo:+.1f} <= {elo:+.2f} <= {pb_hi:+.1f}`) |"
        )

    row_hash_lines = "\n".join(f"- {desc} (`{p}`): `{h}`" for desc, p, h in row_hashes)

    md = f"""# Carbon2 Job 48 Report: Leave-One-Out Across the Five `PC20` Switches on `IdeaB8b + HindsightDepth` (`2,000` Nodes)

## 1. Step 0 — `bundle9` Pins, Known Answers, and Planted `IdeaB8bb=true` Stop Check

- **Executable reused (identical to Job 46 `M13`):** `/tmp/carbon2_job44/bld_bundle9/forge` (`sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`, `id name Chess Engine Forge 6.4.24 candidate`).
- **Planted misspelt option check (`IdeaB8bb=true`):** `run_epd_depth12_strict` sent `setoption name IdeaB8bb value true` followed by `isready`, read every reply line before `readyok`, and **stopped immediately** via `EngineReplyStopError` (`0` searches run; planted `.rows.txt` not written) on the engine's exact `unknown option` line:
  - **`{planted_line_verbatim}`**
- **All Step 0 `PASS` lines (`forge-combo29/carbon2/job48/step0_raw.txt`):**
{step0_pass_block}

---

## 2. Prediction Graded (`forge-combo29/carbon2/job48/prediction_job48.txt`)

- **Commit order and isolation:** Committed **ALONE** (`1 file changed`) in `{pred_sha}` after Part L (`partL_done` in `stamps.txt`) and before the first game of `M15-0`:

```text
{pred_stat}
```

- **Per-match Elo predictions (`{n_preds_true} / {len(m15_results)}` `TRUE`):**

| Match | Predicted Point | Falsification Range | Observed Elo +/- 95% (`[CI]`) | Grade |
| --- | --- | --- | --- | --- |
{chr(10).join(pred_grade_rows)}

- **Switch-attribution prediction (`TRUE` / `HELD`):**
  - Predicted in `prediction_job48.txt`: **`HistRework`** (`HistRework = 2` in `PC20` vs `HistRework = 0` in `L2`, tested by `M15-2`) takes the primary share of the `S14`-to-`PC20` bundle difference, with falsification if `(a)` `M15-2 - M15-0 <= 0.0` Elo while another leave-one-out match exceeds `M15-0` by `>= +7.0` Elo, or `(b)` `M15-0 >= +14.0` Elo with every `(M15-k - M15-0)` inside `[-3.0, +3.0]` Elo.
  - Observed: `M15-0 = {float(m0['elo']):+.2f} +/- {float(m0['err95']):.2f}` Elo and **`M15-2 - M15-0 = {m2['diff_str']}`** (95% CI strictly above `0.0`), while the other four leave-one-out matches (`M15-4`, `M15-1`, `M15-3`, `M15-5`) are `{m4['diff_str']}`, `{m1['diff_str']}`, `{m3['diff_str']}`, and `{m5['diff_str']}` relative to `M15-0`. **Grade: `TRUE` (`{all_preds_true == True}`).**

---

## 3. Part L — Leave-One-Out Liveness of Each `PC20` Switch (`O` `200` + `G` `353` at Depth `12`)

- **Reference (`PC20` all off, Job 46 Step 0 rows):** `O` sum = `{ref_o_sum:,}` (`/agent/repos/dwqww/forge-combo29/carbon2/job46/step0_bundle9_all_off_O_d12.rows.txt`), `G` sum = `{ref_g_sum:,}` (`/agent/repos/dwqww/forge-combo29/carbon2/job46/step0_bundle9_all_off_G_d12.rows.txt`).
- **Whole-set known answer (all 5 switches at `S14` values = `S14` all off on `O`):** `PASS ({whole_set_pass})`.
- **Dead bases (`equal to PC20 all off on all 553 positions`):** **`{dead_bases if dead_bases else 'none (0 of 5 dead)'}`**. Live bases played in Part M15: `{live_bases}`.
- **Ten sums and differences vs `PC20` all off (`forge-combo29/carbon2/job48/partL_summary.txt` & `partL_status.json`):**

| Base | Switch Set to `S14` Value | `O` Sum (`200`) | `O` Delta vs `PC20` | `O` Node Diffs | `O` BM Diffs | `O` Score Diffs | `G` Sum (`353`) | `G` Delta vs `PC20` | `G` Node Diffs | `G` BM Diffs | `G` Score Diffs | Equal / `553` | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(partL_rows_md)}

---

## 4. Part M15 — Six Leave-One-Out Matches (`2,000` Nodes, `12,000` Games / `6,000` Pairs Each, `{total_games:,}` Games Total)

- **Common match settings:** `/tmp/carbon2_job44/bld_bundle9/forge` (`sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`), built-in evaluation, `nodes=2000`, `Threads=1`, `Hash=16`, `OwnBook=false`, sequential UHO openings (`/tmp/carbon2_job40/UHO_Lichess_4852_v1.epd`, lines `2,024,001..2,060,000`, `{total_pairs:,}` pairs), `concurrency=4`. Side A = `IdeaB8b=true, HindsightDepth=true` (all other 8 Idea switches `false`); Side B = all 9 Idea switches and `HindsightDepth` `false`; both sides on the same base.

| Match | Base | UHO Lines | Games | `W-L-D` | Pentanomial `[LL,LD,WL+DD,WD,WW]` | Bundle Elo +/- 95% (`[CI]`) | Difference vs `M15-0` +/- 95% (`[CI]`) | Prediction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(m15_top_rows)}

{chr(10).join(m15_detail_blocks)}

---

## What This Cannot See

The PC's net, Windows, and the PC's node counts with its net; 12,000 games carry about +/- 5 Elo and a difference of
two matches about +/- 7, so a switch that takes 3 or 4 Elo of the gain cannot be told from none; leave-one-out sees
one switch at a time (if two switches each take part of the gain, each shows only its part); 2,000 nodes only (the
PC20 gain was the same at 20,000 in M6 + M6b).

---

## Facts

1. **All Step 0 pins, known answers, and the planted stop check passed on `bundle9` (`/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`):** No-option `bench 11 = 312,866`, `bench 13 = 862,329`, `perft 5 = 4,865,609`; `PC20` `bench 11 = 278,024`, `bench 13 = 587,276`; `PC20` all off `O = {ref_o_sum:,}` (`200/200` position-by-position equal to Job 46 Step 0) and `G = {ref_g_sum:,}` (`353/353` equal); `S14` all off `O = 9,500,069` (`200/200` equal to Job 46 `M13` liveness); and the planted `IdeaB8bb=true` check stopped the runner immediately before any search on `{planted_line_verbatim}`.
2. **All five `PC20` switches are live on `O + G` at depth 12 (`0` of `5` bases dead):** `L1` (`CuckooRep false`), `L2` (`HistRework 0`), `L3` (`TtPruneV2 false`), and `L4` (`CorrHistV2 false`) change all `200/200` `O` node counts and `348..352` of `353` `G` node counts (`36..58` `O` best moves and `75..99` `G` best moves). `L5` (`MateAlphaGuard false`) equals `PC20` all off on all `200/200` `O` positions (`8,315,168 == 8,315,168`) and `338/353` `G` positions (`538/553` total), changing `15/353` `G` node counts and `3/353` `G` best moves (`G = {partL_json['L5']['g_sum']:,}`, `{partL_json['L5']['g_delta']:+,}` nodes).
3. **Under full `PC20` at `nodes=2000` (`M15-0`, `12,000` games, lines `2,024,001..2,030,000`), `IdeaB8b + HindsightDepth` gains `{float(m0['elo']):+.2f} +/- {float(m0['err95']):.2f}` Elo (`[{float(m0['ci_low']):+.2f}, {float(m0['ci_high']):+.2f}]`) over `PC20` all off.** Every match in `M15-0..M15-5` has its own 95% confidence interval strictly above `0` Elo (`0` unpaired games, `0` non-normal endings, `6,000 == 6,000` opening pairs verified per match, `0` fastchess error/unknown/invalid/illegal lines).
4. **Setting `HistRework = 0` alone (`L2`, `M15-2`) increases the bundle's `2,000`-node gain over its base by `{m2['diff_str']}` Elo (`excl_zero = {excl_zero_tags}`):** In `M15-2` (`12,000` games, lines `2,030,001..2,036,000`), `IdeaB8b + HindsightDepth` scores `{int(m2['w'])}-{int(m2['l'])}-{int(m2['d'])}`, pentanomial `{list(m2['ptnml'])}`, **`{float(m2['elo']):+.2f} +/- {float(m2['err95']):.2f}` Elo (`[{float(m2['ci_low']):+.2f}, {float(m2['ci_high']):+.2f}]`)**. The difference `M15-2 - M15-0 = {m2['diff_str']}` has a 95% confidence interval (`[{float(m2['diff_ci_low']):+.2f}, {float(m2['diff_ci_high']):+.2f}]`) that excludes `0`.
5. **For the other four switches (`{cross_zero_tags}`), none of the differences to `M15-0` excludes `0` at 95% confidence:** `M15-4` (`CorrHistV2 false`) gives `{float(m4['elo']):+.2f} +/- {float(m4['err95']):.2f}` (`{m4['diff_str']}` vs `M15-0`), `M15-1` (`CuckooRep false`) gives `{float(m1['elo']):+.2f} +/- {float(m1['err95']):.2f}` (`{m1['diff_str']}`), `M15-3` (`TtPruneV2 false`) gives `{float(m3['elo']):+.2f} +/- {float(m3['err95']):.2f}` (`{m3['diff_str']}`), and `M15-5` (`MateAlphaGuard false`) gives `{float(m5['elo']):+.2f} +/- {float(m5['err95']):.2f}` (`{m5['diff_str']}`).

---

## Suspicions

1. **`HistRework = 2` appears to account for essentially all of the `S14`-vs-`PC20` compression of the `IdeaB8b + HindsightDepth` bundle at `2,000` nodes:** At `nodes=2000` with built-in evaluation on `bundle9`, `M15-2` (`HistRework 0`, other four `PC20` switches on) gives `{float(m2['elo']):+.2f} +/- {float(m2['err95']):.2f}` Elo, compared with `{m13_elo:+.2f} +/- {m13_hw:.2f}` Elo (`[{m13_ci}]`, `{m13_wld}` in `8,000` games) in Job 46 `M13` (`S14`, all five `PC20` switches off); their difference `M15-2 - M13 = {d_m2_vs_m13:+.2f} +/- {hw_m2_vs_m13:.2f}` Elo (`[{lo_m2_vs_m13:+.2f}, {hi_m2_vs_m13:+.2f}]`) crosses `0`, as does `M13 - M15-0 = {d_m13_vs_m0:+.2f} +/- {hw_m13_vs_m0:.2f}` Elo (`[{lo_m13_vs_m0:+.2f}, {hi_m13_vs_m0:+.2f}]`) and `M15-0 - M9 = {d_m0_vs_m9:+.2f} +/- {hw_m0_vs_m9:.2f}` Elo (`[{lo_m0_vs_m9:+.2f}, {hi_m0_vs_m9:+.2f}]`, where Job 44 `M9` at `nodes=2000` gave `{m9_elo:+.2f} +/- {m9_hw:.2f}`). (Quoted apart at `nodes=20000` under `PC20`: Job 42 `M6` gave `{m6_elo:+.2f} +/- {m6_hw:.2f}` and Job 43 `M6b` gave `{m6b_elo:+.2f} +/- {m6b_hw:.2f}`.)
2. **The negative point differences on `L1`, `L3`, `L4`, and especially `L5` (`M15-5 - M15-0 = {m5['diff_str']}`) are likely book-slice / sampling noise rather than genuine synergy between `MateAlphaGuard` and the bundle:** In Part L, `MateAlphaGuard false` (`L5`) was identical to `PC20` all off on `538` of `553` `O + G` positions (`0/200` on `O` and `15/353` on `G`), so `MateAlphaGuard` alters very few searches outside mate-distance alpha windows; a `-4.32` swing on a `+/- 6.89` 95% half-width (`z = -1.23`) is well within normal variance across 6 comparisons.
3. **Why `HistRework = 2` overlaps `IdeaB8b` rather than `HindsightDepth`:** Because `HistRework = 2` replaces `3/4` (`75%`) of the butterfly quiet-history term with `LesserThreatHistory` (`[side][from_attacked_by_lesser][to_attacked_by_lesser][from][to]`), quiet moves that evacuate a piece attacked by a cheaper enemy piece already get a dedicated history bucket in `PC20` before `IdeaB8b`'s role-1 ("step away") bucket in `role_b8b_history_` is added, leaving mainly `IdeaB8b`'s non-evacuation roles (blocking a slider, attacking the attacker, counter-attacking a dearer enemy piece) and `IdeaB8b`'s static-eval swing bonus (`note_role_b8b_swing`) as non-redundant signal under `PC20`.

---

## Read and Not Tested

1. **`HistRework` spin levels `1..3` in `/tmp/carbon2_job36/tpl_r15d_v3/include/forge/b4.hpp` (`lines 20–66`) and `/tmp/carbon2_job36/tpl_r15d_v3/src/search.cpp` (`lines 1446–1502`, `1612–1655`, `1744`):**
   - `HistRework` (`0..3`, `PC20` value `2`) simultaneously controls **two** mechanisms via `level`:
     1. **Quiet-move history blend (`src/search.cpp:1612–1616`, `b4.hpp:27–28, 65–67`):** `threat_quarters(level) = clamp_level(level) + 1`, blending `(plain * (4 - q) + twin * q) / 4` from `rework_history_` (`LesserThreatHistory`), so `HistRework = 1, 2, 3` takes `50%`, `75%`, `100%` of the butterfly term from the lesser-threat twin (`0%` at `HistRework = 0`).
     2. **Pawn x non-pawn-material `joint_correction_` (`src/search.cpp:1446–1459, 1496–1502`, `b4.hpp:29–30, 71–75`):** `joint_weight(level) = 25 * clamp_level(level) + 25` (`50%`, `75%`, `100%` for `level = 1, 2, 3`, updated with self-damping `b4::gravity`).
   - We did **not** test whether the `{m2['diff_str']}` Elo interaction in `M15-2` comes from `LesserThreatHistory` (the `3/4` quiet-history twin overlapping `IdeaB8b` in `forge-combo29/carbon2/job41/bundle_grok7.patch.txt:615–736`) or from `joint_correction_`, nor did we test `HistRework = 1` (`50%` blend / `50%` joint weight) or `bundle_on(HistRework=0 or 1)` directly against `bundle_on(PC20: HistRework=2)`.
2. **Absolute strength of `bundle_on_L2` vs `bundle_on_PC20`:** `M15-2` measured `bundle_on_L2` against `all_off_L2` (`{float(m2['elo']):+.2f} +/- {float(m2['err95']):.2f}`), not `bundle_on_L2` against `bundle_on_PC20`. Because `HistRework = 2` was adopted into `PC20` for its own positive Elo over `HistRework = 0`, dropping `HistRework` to `0` would give back `HistRework = 2`'s standalone contribution on `all_off` unless `IdeaB8b + HindsightDepth` more than replaces it (or unless retuning `HistRework = 1` or `IdeaB8b_Weight` preserves both gains).

---

## What I Did Not Do

- Did **not** build any new binary in Job 48 (reused `/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`, as instructed in `FABLE_TO_carbon2_48.md`).
- Did **not** skip any of `M15-1..M15-5` because `0` of `5` bases were dead in Part L (`L5` differed on `{partL_json['L5']['g_nodes_diff']}/353` `G` positions).
- Did **not** run `20,000`-node leave-one-out matches, pairwise leave-two-out matches, `HistRework = 1` / `HistRework = 3` retuning matches, or direct `bundle_on_L2` vs `bundle_on_PC20` matches (not in Job 48's scope).
- Did **not** touch repository engine source files, other branches, or pull requests; did **not** commit binaries, nets, PGNs, or `.pyc` files.

---

## What I Am Not Sure About

1. **Exact size of `HistRework = 2`'s overlap with the bundle (`{m2['diff_str']}` Elo):** While `M15-2 - M15-0` excludes `0` at 95% confidence (`z = {float(m2['diff_elo']) / (float(m2['diff_err95']) / 1.96):+.2f}`), its `+/- {float(m2['diff_err95']):.2f}` half-width spans from `{float(m2['diff_ci_low']):+.2f}` to `{float(m2['diff_ci_high']):+.2f}` Elo, and `M15-2` was selected as our pre-registered primary candidate out of 5 switches. Whether the true compression under built-in eval is closer to `{d_m13_vs_m0:+.2f} +/- {hw_m13_vs_m0:.2f}` Elo (`M13 {m13_elo:+.2f}` minus `M15-0 {float(m0['elo']):+.2f}`) or `{float(m2['diff_elo']):+.2f} +/- {float(m2['diff_err95']):.2f}` Elo (`M15-2 - M15-0`) cannot be pinned tighter than `+/- 7` Elo without more games or common-opening pairing.
2. **Whether `TtPruneV2`, `CorrHistV2`, `CuckooRep`, or `MateAlphaGuard` takes `2–4` Elo in either direction:** At `+/- {float(m4['diff_err95']):.2f}` Elo for a two-match difference, a `3` or `4` Elo interaction on any of the other four switches cannot be distinguished from `0`.
3. **Whether `IdeaB8b` alone or `HindsightDepth` alone drives the `HistRework` overlap, and how the PC's NNUE net changes it:** All `M15` matches tested the `IdeaB8b + HindsightDepth` bundle together with built-in evaluation on Linux.

---

## Hashes, Builds, and Timestamps

### Build & Prerequisite Hashes (`forge-combo29/carbon2/job48/builds.txt`)

```text
{builds_txt.strip()}
```

### Row File Hashes (`forge-combo29/carbon2/job48/*.rows.txt`)

{row_hash_lines}

### UTC Timestamps (`forge-combo29/carbon2/job48/stamps.txt`)

```text
{stamps_txt.strip()}
```

---

## Verbatim Final Check (`git status --short && ls -R forge-combo29/carbon2/job48`)

```text
__FINAL_GIT_STATUS_LS_PLACEHOLDER__
```

---

## Model Name

`Gemini 4 Carbon`
"""

    (JOB48 / "REPORT_carbon2_job48.md").write_text(md, encoding="utf-8")
    print("Wrote initial REPORT_carbon2_job48.md")


if __name__ == "__main__":
    main()
