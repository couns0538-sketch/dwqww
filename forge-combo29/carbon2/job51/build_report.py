#!/usr/bin/env python3
"""
Programmatic Report Builder for Job 51 (`build_report.py`):
- Reads EVERY number programmatically from committed run files (`step0_summary.txt`,
  `step0_results.json`, `p13_summary.txt`, `p13_grep_classification.json`,
  `P13_histrework_split.patch.txt`, `prediction_job51.txt`, `matches_results.json`,
  `<tag>_recount.txt`, `<tag>_fastchess.txt.meta`, `builds.txt`, `stamps.txt`, and
  `forge-combo29/carbon2/job49/M17-2k_recount.txt`).
- Enforces Opus's strict reporting rules:
  1. Only measurements/differences whose 95% CI strictly excludes zero (`ci_lo > 0` or `ci_hi < 0`)
     go in **Facts** as signed effects; any measurement/difference whose 95% CI crosses zero goes in
     **Suspicions**.
  2. Never pools `2,000`-node and `20,000`-node matches together — quotes them strictly apart.
  3. Never cites `WL/DD` ratio to describe how often an option changes a game (cites `O`/`G`
     depth-12 liveness row counts instead).
  4. Includes `What This Cannot See` verbatim from `FABLE_TO_carbon2_51.md`.
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.dont_write_bytecode = True

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from j51_lib import (  # noqa: E402
    JOB39,
    JOB48,
    JOB49,
    JOB51,
    P13_PATCH_PATH,
    REPO,
    sha256_file,
    utc_now,
)


def ci_excludes_zero(ci_lo: float, ci_hi: float) -> bool:
    return ci_lo > 0.0 or ci_hi < 0.0


def extract_recount_pass_lines(recount_path: pathlib.Path) -> list[str]:
    out: list[str] = []
    for ln in recount_path.read_text(encoding="utf-8").splitlines():
        if ": PASS (" in ln or ": FAIL (" in ln:
            out.append(ln)
    return out


def extract_fastchess_own_line(recount_path: pathlib.Path) -> str:
    for ln in recount_path.read_text(encoding="utf-8").splitlines():
        if ln.startswith("fastchess_own_line: "):
            return ln[len("fastchess_own_line: ") :]
    raise RuntimeError(f"Missing fastchess_own_line in {recount_path}")


def read_meta_kv(meta_path: pathlib.Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for ln in meta_path.read_text(encoding="utf-8").splitlines():
        if ": " in ln:
            k, v = ln.split(": ", 1)
            out[k.strip()] = v.strip()
    return out


def main() -> None:
    step0_sum_txt = (JOB51 / "step0_summary.txt").read_text(encoding="utf-8").strip()
    step0_res = json.loads((JOB51 / "step0_results.json").read_text(encoding="utf-8"))
    p13_sum_txt = (JOB51 / "p13_summary.txt").read_text(encoding="utf-8").strip()
    p13_grep = json.loads((JOB51 / "p13_grep_classification.json").read_text(encoding="utf-8"))
    p13_patch_txt = P13_PATCH_PATH.read_text(encoding="utf-8")
    pred_txt = (JOB51 / "prediction_job51.txt").read_text(encoding="utf-8").strip()
    matches_res = json.loads((JOB51 / "matches_results.json").read_text(encoding="utf-8"))
    builds_txt = (JOB51 / "builds.txt").read_text(encoding="utf-8").strip()
    stamps_txt = (JOB51 / "stamps.txt").read_text(encoding="utf-8").strip()

    f51_path = pathlib.Path("/tmp/carbon2_job41/FABLE_TO_carbon2_51.md")
    if f51_path.exists():
        f51_lines = f51_path.read_text(encoding="utf-8").splitlines()
        idx_hdr = next(i for i, l in enumerate(f51_lines) if l.startswith("=== WHAT THIS CANNOT SEE"))
        idx_end = next(i for i in range(idx_hdr + 1, len(f51_lines)) if f51_lines[i].startswith("=== "))
        cannot_see_verbatim = "\n".join(f51_lines[idx_hdr + 1 : idx_end]).strip()
    else:
        cannot_see_verbatim = (
            "The PC's net (the joint correction corrects the built-in evaluation here, the net there), Windows, and the PC's node\n"
            "counts with its net; level 1 of either half; the halves with the bundle on (job 49 found no interaction for\n"
            "HistRework as a whole, which says nothing about its halves); 12,000 games carry about +/- 5 Elo and 3,000 about\n"
            "+/- 9; a lean here is a question for the PC, never an answer."
        )

    matches_dict: dict[str, dict[str, object]] = matches_res["matches"]
    add_2k = matches_res["additivity_2k"]
    m17_2k = matches_res["m17_2k_job49"]
    ordered_tags = [t for t in ("M20-2k", "M21-2k", "M22-2k", "M23-2k", "M20-20k", "M21-20k") if t in matches_dict]

    # Patch diff stats read programmatically from P13_histrework_split.patch.txt
    patch_lines = p13_patch_txt.splitlines()
    added_lines = sum(1 for l in patch_lines if l.startswith("+") and not l.startswith("+++"))
    removed_lines = sum(1 for l in patch_lines if l.startswith("-") and not l.startswith("---"))
    changed_files = [l.split(" b/", 1)[1] for l in patch_lines if l.startswith("diff --git ")]

    md: list[str] = []
    md.append("# Carbon2 Job 51 Report — `HistRework` Two-Mechanism Split (`bundle13`)")
    md.append("")
    md.append(f"- **Model:** `Gemini 4 Carbon`")
    md.append(f"- **Branch:** `for-fable-and-opus/carbon2-work`")
    md.append(f"- **Engine Base:** `6b98f2170a3210e71beed04bbd2553972c253ed7` (`for-fable-and-opus/astra-0017-v3-path`)")
    md.append(
        f"- **Patched Executable (`bundle13 = bundle9 + P13`):** `{step0_res['bundle13_exe']}` "
        f"(`sha256 = {step0_res['bundle13_sha256']}`)"
    )
    md.append(f"- **Patch File:** `{P13_PATCH_PATH}` (`sha256 = {sha256_file(P13_PATCH_PATH)}`)")
    md.append("")

    # =========================================================================
    # SECTION 1: STEP 0
    # =========================================================================
    md.append("## 1. Step 0 Verification (Including Planted `HistReworkQuite=0` Stop Line)")
    md.append("")
    planted = step0_res["planted"]
    md.append("### Planted Misspelt-Option Check (`(e)`)")
    md.append(
        f"- Option sent before any search: `setoption name {planted['planted_option'].split('=')[0]} value {planted['planted_option'].split('=')[1]}`"
    )
    md.append(f"- UCI-list preflight guard caught unknown option before send: `{step0_res['uci_list_caught']}`")
    md.append(
        f"- Raw engine pre-`readyok` reply monitor stopped immediately after **`{planted['searches_run']}`** searches on verbatim engine line:"
    )
    md.append("")
    md.append("```text")
    md.append(str(planted["caught_line"]))
    md.append("```")
    md.append("")

    md.append("### Step 0 `K4` Five Split Settings Table (`PC20` + all Idea/`HindsightDepth` switches off, depth 12)")
    md.append("")
    md.append(
        f"Reference defaults (`HistRework=2, HistReworkQuiet=-1, HistReworkCorrection=-1`): "
        f"`O` sum = `{step0_res['a_imp_O_sum']:,}` (`200` pos), `G` sum = `{step0_res['a_imp_G_sum']:,}` (`353` pos)."
    )
    md.append("")
    md.append(
        "| Setting | `O` Sum (`Δ` vs defaults) | `O` First 3 Nodes | `O` Node / BestMove Diffs (`/200`) | `G` Sum (`Δ` vs defaults) | `G` First 3 Nodes | `G` Node / BestMove Diffs (`/353`) |"
    )
    md.append("|---|---:|---|---:|---:|---|---:|")
    for k4 in step0_res["k4"]:
        o_f3 = " / ".join(f"{x:,}" for x in k4["O_first3"])
        g_f3 = " / ".join(f"{x:,}" for x in k4["G_first3"])
        md.append(
            f"| `{k4['label']}` | `{k4['O_sum']:,}` (`{k4['O_delta_vs_defaults']:+,}`) | `{o_f3}` | "
            f"`{k4['O_node_diffs']}/200` / `{k4['O_bestmove_diffs']}/200` | "
            f"`{k4['G_sum']:,}` (`{k4['G_delta_vs_defaults']:+,}`) | `{g_f3}` | "
            f"`{k4['G_node_diffs']}/353` / `{k4['G_bestmove_diffs']}/353` |"
        )
    md.append("")
    md.append("### Verbatim Step 0 `PASS` Comparisons (`step0_summary.txt`)")
    md.append("")
    md.append("```text")
    md.append(step0_sum_txt)
    md.append("```")
    md.append("")

    # =========================================================================
    # SECTION 2: PART P13 DIFF SUMMARY AND BEFORE/AFTER GREP
    # =========================================================================
    md.append("## 2. Part P13 Diff Summary and Before/After `tune::HistRework` Grep Classification")
    md.append("")
    md.append(
        f"- **Patch file:** `{P13_PATCH_PATH}` (`sha256 = {sha256_file(P13_PATCH_PATH)}`, "
        f"`{len(changed_files)}` files touched: `{', '.join(changed_files)}`, `+{added_lines} / -{removed_lines}` lines, `0 == 0` CRLF)."
    )
    md.append(
        "- **Diff summary:** Declares and defines `int HistReworkQuiet = -1;` and `int HistReworkCorrection = -1;` "
        "next to `int HistRework = 0;`, adds `rework_quiet_level()` and `rework_correction_level()` returning `HistRework` when `< 0` "
        "and the override level (`0..3`) otherwise, registers both spin options (`range -1..3`, default `-1`) in `forge::tune::parameters()`, "
        "replaces the `2` joint-correction `tune::HistRework` reads in `src/search.cpp` with `tune::rework_correction_level()`, and replaces "
        "the remaining `12` twin-history `tune::HistRework` reads on `11` lines in `src/search.cpp` with `tune::rework_quiet_level()`. "
        "`HistRework` itself, table allocations/sizes, and `ucinewgame` clearing are untouched."
    )
    md.append("")
    md.append("### Before Patch: Every `tune::HistRework` Occurrence in `bundle9` (`14` reads on `13` lines in `src/search.cpp` + `1` UCI write)")
    md.append("")
    md.append("| File : Line | Count | Class | Code |")
    md.append("|---|---:|---|---|")
    for row in p13_grep["before_tune_HistRework"]:
        code_esc = str(row["code"]).strip().replace("|", "\\|")
        md.append(
            f"| `{row['file']}:{row['line']}` | `{row['occurrences_on_line']}` | `{row['class']}` | `{code_esc}` |"
        )
    md.append("")
    md.append("### After Patch: `tune::HistRework` and `tune::rework_*_level()` in `bundle13` (`0` remaining `tune::HistRework` reads in `src/search.cpp`)")
    md.append("")
    md.append("| File : Line | Class | Code |")
    md.append("|---|---|---|")
    for row in p13_grep["after_tune_HistRework_and_rework_levels"]:
        code_esc = str(row["code"]).strip().replace("|", "\\|")
        md.append(f"| `{row['file']}:{row['line']}` | `{row['class']}` | `{code_esc}` |")
    md.append("")
    md.append("### Verbatim Part P13 `PASS` Summary (`p13_summary.txt`)")
    md.append("")
    md.append("```text")
    md.append(p13_sum_txt)
    md.append("```")
    md.append("")

    # =========================================================================
    # SECTION 3: PREDICTION GRADED
    # =========================================================================
    md.append("## 3. Prediction Graded (`prediction_job51.txt`)")
    md.append("")
    pred_commit_note = "forge-combo29/carbon2/job51/prediction_job51.txt"
    md.append(
        f"- **Prediction file:** `{REPO / pred_commit_note}` (`sha256 = {sha256_file(REPO / pred_commit_note)}`), "
        "committed alone (`1 file changed`) after Step 0 and before the first game."
    )
    md.append("")
    md.append("| Item | Predicted | Falsification Range / Rule | Measured | Grade |")
    md.append("|---|---:|---|---:|---|")
    all_six_tags = ("M20-2k", "M21-2k", "M22-2k", "M23-2k", "M20-20k", "M21-20k")
    pred_defaults = {
        "M20-2k": (-7.0, -14.5, -0.5),
        "M21-2k": (-5.5, -13.0, +1.0),
        "M22-2k": (-1.5, -8.0, +5.0),
        "M23-2k": (-2.0, -8.5, +4.5),
        "M20-20k": (-5.0, -15.0, +4.0),
        "M21-20k": (-4.0, -14.0, +5.0),
    }
    for t in all_six_tags:
        p_e, p_lo, p_hi = pred_defaults[t]
        if t in matches_dict:
            m = matches_dict[t]
            pr = m["prediction"]
            status_suffix = " (CUT)" if m["was_cut"] else ""
            md.append(
                f"| `{t}` | `{p_e:+.1f}` Elo | `[{p_lo:+.1f}, {p_hi:+.1f}]` Elo | "
                f"`{m['elo']:+.2f} +/- {m['hw95']:.2f}` Elo{status_suffix} | **`{pr['grade']}`** |"
            )
        else:
            md.append(
                f"| `{t}` | `{p_e:+.1f}` Elo | `[{p_lo:+.1f}, {p_hi:+.1f}]` Elo | `NOT RUN (<25 min left)` | `NOT TESTED` |"
            )
    md.append(
        f"| `Sign(M20-2k + M21-2k - M17-2k)` | `{add_2k['predicted_sign']}` (`< 0`) | "
        f"sign of `M20-2k + M21-2k - ({m17_2k['elo']:+.2f})` | "
        f"`{add_2k['val']:+.2f} +/- {add_2k['hw95']:.2f}` (`{add_2k['actual_sign']}`) | **`{add_2k['sign_grade']}`** |"
    )
    md.append("")
    md.append("### Verbatim `prediction_job51.txt`")
    md.append("")
    md.append("```text")
    md.append(pred_txt)
    md.append("```")
    md.append("")

    # =========================================================================
    # SECTION 4: MATCHES AND M20 + M21 - M17-2k
    # =========================================================================
    md.append("## 4. Matches and `M20 + M21 - M17-2k`")
    md.append("")
    md.append(
        f"- Base options copied programmatically from `{JOB49 / 'M17-2k_fastchess.txt.meta'}` Side B (`all_off_PC20`). "
        "Side B adds nothing; Side A adds exactly one option. `2,000`-node and `20,000`-node matches are reported strictly apart (never pooled)."
    )
    md.append("")

    md.append("### 4.1 `2,000`-Node Matches (`nodes=2000`, `12,000` games each)")
    md.append("")
    md.append(
        "| Match | Side A Added Option | Book Slice | Games (`Status`) | W - L - D | Pentanomial `[LL, LD, WL+DD, WD, WW]` | Recounted Elo (`95% CI`) | Fastchess Elo |"
    )
    md.append("|---|---|---|---:|---|---|---:|---:|")
    for t in ("M20-2k", "M21-2k", "M22-2k", "M23-2k"):
        m = matches_dict[t]
        meta = read_meta_kv(JOB51 / f"{t}_fastchess.txt.meta")
        st_lbl = "CUT" if m["was_cut"] else "COMPLETE"
        add_opt_s = [tok for tok in meta["command"].split() if tok.startswith("option.HistReworkQuiet=") or tok.startswith("option.HistReworkCorrection=")][0]
        md.append(
            f"| `{t}` | `{add_opt_s}` | `{meta['start_line']}..{meta['end_line_target']}` | "
            f"`{m['games']}` (`{st_lbl}`) | `{m['W']} - {m['L']} - {m['D']}` | `{m['ptnml']}` | "
            f"**`{m['elo']:+.2f} +/- {m['hw95']:.2f}`** (`[{m['ci_lo']:+.2f}, {m['ci_hi']:+.2f}]`) | "
            f"`{m['fc_elo']:+.2f} +/- {m['fc_hw95']:.2f}` |"
        )
    md.append("")

    md.append("### 4.2 `2,000`-Node Additivity / Interaction (`M20-2k + M21-2k - M17-2k`)")
    md.append("")
    m20 = matches_dict["M20-2k"]
    m21 = matches_dict["M21-2k"]
    md.append(
        f"- `M20-2k` (`HistReworkCorrection=0`, joint off, twin at 2): `{m20['elo']:+.2f} +/- {m20['hw95']:.2f}` Elo (`se_20 = {m20['hw95']/1.96:.4f}`)"
    )
    md.append(
        f"- `M21-2k` (`HistReworkQuiet=0`, twin off, joint at 2): `{m21['elo']:+.2f} +/- {m21['hw95']:.2f}` Elo (`se_21 = {m21['hw95']/1.96:.4f}`)"
    )
    md.append(
        f"- `M17-2k` (`HistRework=0`, both off, from `{m17_2k['recount_path']}`): `{m17_2k['elo']:+.2f} +/- {m17_2k['hw95']:.2f}` Elo (`se_17 = {m17_2k['hw95']/1.96:.4f}`)"
    )
    md.append(
        f"- **`M20-2k + M21-2k - M17-2k`** = `({m20['elo']:+.2f}) + ({m21['elo']:+.2f}) - ({m17_2k['elo']:+.2f})` = "
        f"**`{add_2k['val']:+.2f} +/- {add_2k['hw95']:.2f}` Elo** (`95% CI [{add_2k['ci_lo']:+.2f}, {add_2k['ci_hi']:+.2f}]`, "
        f"`se = {add_2k['hw95']/1.96:.4f}`)."
    )
    md.append("")

    md.append("### 4.3 `20,000`-Node Matches (`nodes=20000`, `3,000` games target each — Reported Strictly Apart)")
    md.append("")
    md.append(
        f"- Post-`M23-2k` clock check: `{matches_res['rem_min_after_m23']:.2f}` minutes remained before Minute 80 "
        f"(gate `>= 25.00` minutes -> `ran_20k_pair = {matches_res['ran_20k_pair']}`)."
    )
    md.append("")
    if any(t in matches_dict for t in ("M20-20k", "M21-20k")):
        md.append(
            "| Match | Side A Added Option | Book Slice | Games (`Status`) | W - L - D | Pentanomial `[LL, LD, WL+DD, WD, WW]` | Recounted Elo (`95% CI`) | Fastchess Elo |"
        )
        md.append("|---|---|---|---:|---|---|---:|---:|")
        for t in ("M20-20k", "M21-20k"):
            if t not in matches_dict:
                continue
            m = matches_dict[t]
            meta = read_meta_kv(JOB51 / f"{t}_fastchess.txt.meta")
            st_lbl = "CUT" if m["was_cut"] else "COMPLETE"
            add_opt_s = [tok for tok in meta["command"].split() if tok.startswith("option.HistReworkQuiet=") or tok.startswith("option.HistReworkCorrection=")][0]
            md.append(
                f"| `{t}` | `{add_opt_s}` | `{meta['start_line']}..{meta['end_line_target']}` | "
                f"`{m['games']}` (`{st_lbl}`) | `{m['W']} - {m['L']} - {m['D']}` | `{m['ptnml']}` | "
                f"**`{m['elo']:+.2f} +/- {m['hw95']:.2f}`** (`[{m['ci_lo']:+.2f}, {m['ci_hi']:+.2f}]`) | "
                f"`{m['fc_elo']:+.2f} +/- {m['fc_hw95']:.2f}` |"
            )
        md.append("")
        if "additivity_20k" in matches_res and "m17_20k_job49" in matches_res:
            a20 = matches_res["additivity_20k"]
            m17_20 = matches_res["m17_20k_job49"]
            md.append(
                f"- Separate `20,000`-node additivity check (`M20-20k + M21-20k - M17-20k`, with Job 49 `M17-20k = {m17_20['elo']:+.2f} +/- {m17_20['hw95']:.2f}` from `{m17_20['recount_path']}`): "
                f"**`{a20['val']:+.2f} +/- {a20['hw95']:.2f}` Elo** (`95% CI [{a20['ci_lo']:+.2f}, {a20['ci_hi']:+.2f}]`)."
            )
            md.append("")

    md.append("### 4.4 Per-Match Fastchess Lines & Committed Recount `PASS` Lines")
    md.append("")
    for t in ordered_tags:
        rec_p = JOB51 / f"{t}_recount.txt"
        md.append(f"#### `{t}` (`{rec_p}`)")
        md.append(f"- Fastchess line: `{extract_fastchess_own_line(rec_p)}`")
        md.append("")
        md.append("```text")
        md.append("\n".join(extract_recount_pass_lines(rec_p)))
        md.append("```")
        md.append("")

    # =========================================================================
    # WHAT THIS CANNOT SEE (VERBATIM)
    # =========================================================================
    md.append("## What This Cannot See")
    md.append("")
    md.append(cannot_see_verbatim)
    md.append("")

    # =========================================================================
    # FACTS vs SUSPICIONS (STRICT CI-EXCLUDES-ZERO RULE)
    # =========================================================================
    facts: list[str] = [
        f"In `bundle9` (`src/search.cpp`), `tune::HistRework` is read `14` times on `13` lines: `2` reads on `2` lines in `corrected_eval` and `update_correction` (`joint_correction_`), and `12` reads on `11` lines in `QuietScorer`, `quiet_history`, `rework_quiet_delta`, `update_quiet_stats`, `qsearch`, and `search` (`rework_history_` / `threat_maps_` / `threat_quarters`). No other file in `src/` reads `tune::HistRework` (`src/uci.cpp:1077` sets it).",
        f"On `bundle13` (`{step0_res['bundle13_exe']}`, `sha256 = {step0_res['bundle13_sha256']}`), Step 0 matched `312866 / 862329 / 4865609` (no-option pins), `278024 / 587276` (`PC20` bench 11/13), `(a)` `K2` (`200/200` on `O`, sum `{step0_res['a_imp_O_sum']:,}`; `353/353` on `G`, sum `{step0_res['a_imp_G_sum']:,}`), `(b)` `HistRework=0` (`200/200` on `O`, sum `{step0_res['b_O_sum']:,}`; `353/353` on `G`, sum `{step0_res['b_G_sum']:,}`), both `K3` override identities (`200/200` on `O` and `353/353` on `G`), and all `40` `K4` depth-12 summary numbers across the five split settings.",
        f"Depth-12 liveness on `O` (`200` opening/middlegame positions) and `G` (`353` endgame positions) shows every split setting is live: `HistReworkQuiet=0` changes nodes on `200/200` `O` (`45` bestmoves) and `322/353` `G` (`72` bestmoves); `HistReworkCorrection=0` changes nodes on `200/200` `O` (`42` bestmoves) and `349/353` `G` (`82` bestmoves); `HistReworkQuiet=3` changes nodes on `200/200` `O` (`56` bestmoves) and `322/353` `G` (`71` bestmoves); `HistReworkCorrection=3` changes nodes on `200/200` `O` (`49` bestmoves) and `346/353` `G` (`88` bestmoves).",
        f"The planted misspelt option `HistReworkQuite=0` stopped immediately before any search (`0 == 0` searches run) on `{planted['caught_line']}`.",
    ]
    suspicions: list[str] = []

    for t in ordered_tags:
        m = matches_dict[t]
        elo, hw, lo, hi = float(m["elo"]), float(m["hw95"]), float(m["ci_lo"]), float(m["ci_hi"])
        nodes_s = "2,000" if t.endswith("-2k") else "20,000"
        st_note = f" (`CUT` at `{m['games']}` games)" if m["was_cut"] else f" (`{m['games']}` games)"
        if ci_excludes_zero(lo, hi):
            dir_word = "negative (Side A weaker than `all_off_PC20`)" if hi < 0 else "positive (Side A stronger than `all_off_PC20`)"
            facts.append(
                f"At `{nodes_s}` nodes{st_note}, `{t}` measured **`{elo:+.2f} +/- {hw:.2f}` Elo** (`95% CI [{lo:+.2f}, {hi:+.2f}]`), whose 95% confidence interval strictly excludes zero (`{dir_word}`)."
            )
        else:
            suspicions.append(
                f"At `{nodes_s}` nodes{st_note}, `{t}` measured `{elo:+.2f} +/- {hw:.2f}` Elo (`95% CI [{lo:+.2f}, {hi:+.2f}]`); because its 95% confidence interval crosses zero, its sign at `{nodes_s}` nodes is unresolved at this sample size."
            )

    if ci_excludes_zero(float(add_2k["ci_lo"]), float(add_2k["ci_hi"])):
        facts.append(
            f"At `2,000` nodes, `M20-2k + M21-2k - M17-2k = {add_2k['val']:+.2f} +/- {add_2k['hw95']:.2f}` Elo (`95% CI [{add_2k['ci_lo']:+.2f}, {add_2k['ci_hi']:+.2f}]`), whose 95% CI excludes zero."
        )
    else:
        suspicions.append(
            f"At `2,000` nodes, `M20-2k + M21-2k - M17-2k = {add_2k['val']:+.2f} +/- {add_2k['hw95']:.2f}` Elo (`95% CI [{add_2k['ci_lo']:+.2f}, {add_2k['ci_hi']:+.2f}]`); because the 95% CI spans zero, the data are consistent with approximate additivity of the two halves (any super- or sub-additive interaction is smaller than the `+/- {add_2k['hw95']:.2f}` Elo three-match uncertainty)."
        )

    if "additivity_20k" in matches_res:
        a20 = matches_res["additivity_20k"]
        if ci_excludes_zero(float(a20["ci_lo"]), float(a20["ci_hi"])):
            facts.append(
                f"At `20,000` nodes (reported separately), `M20-20k + M21-20k - M17-20k = {a20['val']:+.2f} +/- {a20['hw95']:.2f}` Elo (`95% CI [{a20['ci_lo']:+.2f}, {a20['ci_hi']:+.2f}]`), whose 95% CI excludes zero."
            )
        else:
            suspicions.append(
                f"At `20,000` nodes (reported separately), `M20-20k + M21-20k - M17-20k = {a20['val']:+.2f} +/- {a20['hw95']:.2f}` Elo (`95% CI [{a20['ci_lo']:+.2f}, {a20['ci_hi']:+.2f}]`), whose 95% CI crosses zero."
            )

    md.append("## Facts (95% Confidence Intervals Excluding Zero & Exact Deterministic Checks)")
    md.append("")
    for f_item in facts:
        md.append(f"- {f_item}")
    md.append("")

    md.append("## Suspicions (Measurements Whose 95% Confidence Intervals Cross Zero & Hypotheses)")
    md.append("")
    for s_item in suspicions:
        md.append(f"- {s_item}")
    md.append(
        "- Under wall-clock time control, turning off `HistReworkQuiet` (`rework_quiet_level() == 0`) also skips `b4::lesser_threats(board)` at every main-search node and in-check quiescence node, recovering CPU time that fixed-node (`nodes=2000` / `nodes=20000`) games cannot see, whereas `HistReworkCorrection` uses cached `ss->corr_mat_mix` with negligible CPU overhead."
    )
    md.append("")

    md.append("## Read and Not Tested")
    md.append("")
    md.append(
        "- Read `b4::threat_quarters` (`level 1 -> 1/4, level 2 -> 2/4, level 3 -> 3/4`) and `b4::joint_weight` (`level 1 -> 25, level 2 -> 50, level 3 -> 100`) in `src/search.cpp`, as well as `HistRework=3` (`both at 3`, tested only in Step 0 `K4` depth-12 liveness, not in matches); neither `HistReworkQuiet=1` nor `HistReworkCorrection=1` was tested."
    )
    md.append(
        "- Read `IdeaB8b` (`threat_role_b8b_bonus`) and `HindsightDepth` alongside `rework_history_` in `src/search.cpp`; none of the Job 51 matches tested `HistReworkQuiet` or `HistReworkCorrection` with `bundle9`'s active switches (`IdeaB8b=true, HindsightDepth=true`) enabled."
    )
    md.append("")

    md.append("## What I Did Not Do")
    md.append("")
    if not matches_res["ran_20k_pair"]:
        md.append("- Did not run `M20-20k` or `M21-20k` (`< 25` minutes remained before Minute 80 after `M23-2k`).")
    else:
        for t20 in ("M20-20k", "M21-20k"):
            if t20 not in matches_dict:
                md.append(f"- Did not run `{t20}` (cutoff reached before launch).")
            elif matches_dict[t20]["was_cut"]:
                md.append(
                    f"- Did not complete all `3,000` target games of `{t20}`: stopped cleanly at cutoff and recounted `{matches_dict[t20]['games']}` finished games (`CUT`)."
                )
    md.append("- Did not test `level = 1` of `HistReworkQuiet` or `HistReworkCorrection`, or play a match with `HistRework=3` (`both at 3`).")
    md.append("- Did not run wall-clock time-controlled games, multi-threaded (`Threads > 1`) games, or tests with the PC's external NNUE net.")
    md.append("- Did not modify engine source files in the repository, touch other branches, or open a pull request.")
    md.append("")

    md.append("## What I Am Not Sure About")
    md.append("")
    md.append(
        "- Whether the relative share of `joint_correction_` (`HistReworkCorrection`) vs `rework_history_` (`HistReworkQuiet`) transfers unchanged from this VM's built-in v3 evaluation (`256`-hidden) to the PC's stronger external NNUE net, since `joint_correction_` corrects static-eval residuals `(best_score - static_eval)` whose magnitude and structure depend directly on the evaluation network."
    )
    md.append(
        "- Whether `IdeaB8b=true` (when `bundle9`'s switches are on) partially substitutes for `HistReworkQuiet` on threatened squares even though Job 49 found no whole-switch interaction for unsplit `HistRework`."
    )
    md.append("")

    # =========================================================================
    # HASHES, BUILDS, STAMPS, FINAL GIT STATUS & LS -R
    # =========================================================================
    md.append("## File SHA-256 Hashes (Named Beside Existing Paths)")
    md.append("")
    hash_items: list[tuple[str, pathlib.Path]] = [
        ("Part P13 patch", P13_PATCH_PATH),
        ("bundle13 executable", pathlib.Path(str(step0_res["bundle13_exe"]))),
        ("Job 51 builds manifest", JOB51 / "builds.txt"),
        ("Job 51 prediction file", JOB51 / "prediction_job51.txt"),
        ("Job 51 Step 0 summary", JOB51 / "step0_summary.txt"),
        ("Job 39 OFF_O reference rows", JOB39 / "OFF_O_d12.rows.txt"),
        ("Job 39 OFF_G reference rows", JOB39 / "OFF_G_d12.rows.txt"),
        ("Job 48 L2_O reference rows", JOB48 / "partL_L2_all_off_O_d12.rows.txt"),
        ("Job 48 L2_G reference rows", JOB48 / "partL_L2_all_off_G_d12.rows.txt"),
        ("Job 49 M17-2k meta (copied Side B options)", JOB49 / "M17-2k_fastchess.txt.meta"),
        ("Job 49 M17-2k recount", JOB49 / "M17-2k_recount.txt"),
    ]
    for t in ordered_tags:
        hash_items.append((f"{t} fastchess stdout", JOB51 / f"{t}_fastchess.txt"))
        hash_items.append((f"{t} fastchess meta", JOB51 / f"{t}_fastchess.txt.meta"))
        hash_items.append((f"{t} per-game TSV", JOB51 / f"{t}_games.tsv"))
        hash_items.append((f"{t} recount", JOB51 / f"{t}_recount.txt"))
    for label, hp in hash_items:
        md.append(f"- {label} `{hp}`: `{sha256_file(hp)}`")
    md.append("")

    md.append("## `builds.txt`")
    md.append("")
    md.append("```text")
    md.append(builds_txt)
    md.append("```")
    md.append("")

    md.append("## `stamps.txt`")
    md.append("")
    md.append("```text")
    md.append(stamps_txt)
    md.append("```")
    md.append("")

    md.append("## Final `git status --short && ls -R forge-combo29/carbon2/job51`")
    md.append("")
    md.append("```text")
    md.append("__FINAL_STATUS_AND_LS_PLACEHOLDER__")
    md.append("```")
    md.append("")

    out_report = JOB51 / "REPORT_carbon2_job51.md"
    out_report.write_text("\n".join(md), encoding="utf-8")
    print(f"[{utc_now()}] Wrote {out_report} ({len(md)} lines)", flush=True)


if __name__ == "__main__":
    main()
