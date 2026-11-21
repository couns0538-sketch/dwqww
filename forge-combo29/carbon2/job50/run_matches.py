#!/usr/bin/env python3
"""
Job 50 Parts M18 and M19 Match Runner (`run_matches.py`):
- Copies base options programmatically from `forge-combo29/carbon2/job48/M15-0_fastchess.txt.meta`
  (`bundle_on_PC20` Side A options, never retyped by hand).
- Reads `partL2_status.json` to include only `LIVE` options in Side A (`all 3` are `LIVE`).
- Runs:
  1. `M18-2k`:  `nodes=2000`,  UHO lines `2,075,001..2,081,000` (`12,000` games, `6,000` pairs)
  2. `M18-20k`: `nodes=20000`, UHO lines `2,081,001..2,082,500` (`3,000` games, `1,500` pairs)
  Commits & pushes after each match (and stamps `stamps.txt`).
- Checks remaining clock until Minute 80 (`2026-11-21 01:10:30 UTC + 80m = 02:30:30 UTC`):
  ONLY if `>= 25` minutes (`1500` seconds) remain after `M18` completes, runs:
  3. `M19-2k`:  `nodes=2000`,  UHO lines `2,082,501..2,088,500` (`12,000` games, `6,000` pairs),
     Side A adds `HdLowerLoss=167` only, Side B adds nothing.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import pathlib
import subprocess
import sys
import time

sys.dont_write_bytecode = True

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from j50_lib import (  # noqa: E402
    JOB50,
    REPO,
    WORK50,
    diff_elo_interval,
    parse_m15_0_sideA_options_from_meta,
    run_match_strict_j50,
    utc_now,
)

# File 50 was fetched & read at 2026-11-21 01:10:30 UTC -> Minute 80 = 02:30:30 UTC
READ_FILE50_EPOCH = datetime(2026, 11, 21, 1, 10, 30, tzinfo=timezone.utc).timestamp()
MINUTE_80_EPOCH = READ_FILE50_EPOCH + 80 * 60
CUTOFF_SAFETY_EPOCH = MINUTE_80_EPOCH - 180  # 3m before Minute 80 for clean report + push


def append_stamp(label: str) -> None:
    st = subprocess.run(["date", "-u"], check=True, capture_output=True, text=True).stdout.strip()
    with open(JOB50 / "stamps.txt", "a", encoding="utf-8") as sf:
        sf.write(f"{label}: {st}\n")


def git_commit_and_push_job50(msg: str) -> None:
    subprocess.run(
        ["find", "forge-combo29/carbon2/job50", "-name", "__pycache__", "-exec", "rm", "-rf", "{}", "+"],
        cwd=str(REPO),
        check=True,
    )
    subprocess.run(["git", "add", "forge-combo29/carbon2/job50/"], cwd=str(REPO), check=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=str(REPO), check=True)
    subprocess.run(["git", "push", "-u", "origin", "for-fable-and-opus/carbon2-work"], cwd=str(REPO), check=True)


def write_matches_summary(
    matches_records: list[dict[str, object]],
    m19_decision: dict[str, object],
) -> None:
    by_tag = {str(r["tag"]): r for r in matches_records}
    m18_minus_m19_2k = None
    if "M18-2k" in by_tag and "M19-2k" in by_tag:
        r18 = by_tag["M18-2k"]
        r19 = by_tag["M19-2k"]
        if r18["elo"] is not None and r19["elo"] is not None:
            d_elo, d_hw, d_lo, d_hi = diff_elo_interval(
                float(r18["elo"]), float(r18["err95"]), float(r19["elo"]), float(r19["err95"])
            )
            m18_minus_m19_2k = {
                "diff_elo": round(d_elo, 2),
                "diff_err95": round(d_hw, 2),
                "diff_ci_low": round(d_lo, 2),
                "diff_ci_high": round(d_hi, 2),
                "excludes_zero": bool(d_lo > 0.0 or d_hi < 0.0),
                "diff_str": f"{d_elo:+.2f} +/- {d_hw:.2f} [{d_lo:+.2f}, {d_hi:+.2f}]",
            }

    lines = [
        f"=== JOB 50 MATCHES SUMMARY ({utc_now()}) ===",
        f"m19_gate_check: {json.dumps(m19_decision)}",
        "",
        "Match   | Nodes | Side_A_Extra                    | UHO_Lines           | Status   | Games | W-L-D            | Pentanomial                 | Elo +/- 95% [CI]                  | Pred",
        "-" * 188,
    ]
    for r in matches_records:
        elo_s = (
            f"{float(r['elo']):+.2f} +/- {float(r['err95']):.2f} [{float(r['ci_low']):+.2f}, {float(r['ci_high']):+.2f}]"
            if r["elo"] is not None
            else "CUT (no Elo)"
        )
        lines.append(
            f"{str(r['tag']):7s} | {int(r['nodes']):5d} | {str(r['sideA_extra_desc']):31s} | "
            f"{int(r['start_line']):,}..{int(r['end_line']):,} | {str(r['status']):8s} | {int(r['games']):5d} | "
            f"{int(r['w'])}-{int(r['l'])}-{int(r['d']):4d} | {str(r['ptnml']):27s} | {elo_s:33s} | {r['pred_status']}"
        )
    if m18_minus_m19_2k is not None:
        lines.append("")
        lines.append(f"M18-2k minus M19-2k (nodes=2000, effect of adding Withheld=2 & Depth=2 on top of Loss=167): {m18_minus_m19_2k['diff_str']}")

    (JOB50 / "matches_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (JOB50 / "matches_results.json").write_text(
        json.dumps(
            {
                "utc": utc_now(),
                "m19_decision": m19_decision,
                "matches": matches_records,
                "m18_minus_m19_2k": m18_minus_m19_2k,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def enrich_match_record(
    *,
    tag: str,
    part: str,
    nodes: int,
    start_line: int,
    rounds: int,
    eng1_name: str,
    eng2_name: str,
    sideA_extra_opts: list[tuple[str, str]],
    sideA_extra_desc: str,
    pred_point: float,
    pred_bounds: tuple[float, float],
    rec: dict[str, object],
) -> dict[str, object]:
    elo_val = rec.get("elo")
    err_val = rec.get("err95")
    was_cut = bool(rec.get("was_cut", False))
    status = "CUT" if was_cut else "COMPLETE"
    pred_held = None
    pred_status = "NOT_GRADED_CUT"
    ci_lo = None
    ci_hi = None
    if elo_val is not None and err_val is not None:
        elo_f = float(elo_val)
        hw_f = float(err_val)
        ci_lo = round(elo_f - hw_f, 2)
        ci_hi = round(elo_f + hw_f, 2)
        if not was_cut:
            pred_held = bool(pred_bounds[0] <= elo_f <= pred_bounds[1])
            pred_status = (
                f"{'TRUE' if pred_held else 'FALSE'} "
                f"(pred {pred_point:+.1f}, [{pred_bounds[0]:+.1f}, {pred_bounds[1]:+.1f}])"
            )
            with open(JOB50 / f"{tag}_recount.txt", "a", encoding="utf-8") as rf:
                rf.write(f"prediction_check: {pred_status}\n")

    return {
        "tag": tag,
        "part": part,
        "nodes": nodes,
        "start_line": start_line,
        "end_line": start_line + rounds - 1,
        "target_rounds": rounds,
        "target_games": rounds * 2,
        "eng1_name": eng1_name,
        "eng2_name": eng2_name,
        "sideA_extra_opts": sideA_extra_opts,
        "sideA_extra_desc": sideA_extra_desc,
        "status": status,
        "was_cut": was_cut,
        "games": int(rec["games"]),
        "pairs": int(rec["pairs"]),
        "w": int(rec["w"]),
        "l": int(rec["l"]),
        "d": int(rec["d"]),
        "ptnml": list(rec["ptnml"]),
        "elo": round(float(elo_val), 2) if elo_val is not None else None,
        "err95": round(float(err_val), 2) if err_val is not None else None,
        "ci_low": ci_lo,
        "ci_high": ci_hi,
        "pred_point": pred_point,
        "pred_bounds": list(pred_bounds),
        "pred_held": pred_held,
        "pred_status": pred_status,
        "wall_s": round(float(rec["wall_s"]), 3),
    }


def main() -> None:
    b12_exe = WORK50 / "bld_bundle12/forge"
    if not b12_exe.exists():
        raise RuntimeError(f"Missing {b12_exe}")

    l2_status = json.loads((JOB50 / "partL2_status.json").read_text(encoding="utf-8"))
    live_m18_opts: list[tuple[str, str]] = [(str(k), str(v)) for k, v in l2_status["live_single_opts"]]
    if not live_m18_opts:
        raise RuntimeError("All 3 options DEAD in Part L2 — stopping before matches!")

    sideA_base_eng_opts, each_base_opts, _ = parse_m15_0_sideA_options_from_meta()

    matches_records: list[dict[str, object]] = []
    m19_decision: dict[str, object] = {"checked": False, "run_m19": False, "reason": "pending M18 completion"}

    # 1. M18-2k
    m18_desc = ", ".join(f"{k}={v}" for k, v in live_m18_opts)
    rec_18_2k = run_match_strict_j50(
        tag="M18-2k",
        out_dir=JOB50,
        exe_path=b12_exe,
        eng1_name="sf_hd_lower_bundle_PC20",
        eng2_name="ours_hd_lower_bundle_PC20",
        e1_switches=sideA_base_eng_opts + live_m18_opts,
        e2_switches=sideA_base_eng_opts,
        each_base_opts=each_base_opts,
        nodes=2000,
        start_line=2075001,
        rounds=6000,
        cutoff_epoch=CUTOFF_SAFETY_EPOCH,
        concurrency=4,
    )
    matches_records.append(
        enrich_match_record(
            tag="M18-2k",
            part="M18",
            nodes=2000,
            start_line=2075001,
            rounds=6000,
            eng1_name="sf_hd_lower_bundle_PC20",
            eng2_name="ours_hd_lower_bundle_PC20",
            sideA_extra_opts=live_m18_opts,
            sideA_extra_desc=m18_desc,
            pred_point=2.0,
            pred_bounds=(-5.0, 9.0),
            rec=rec_18_2k,
        )
    )
    write_matches_summary(matches_records, m19_decision)
    append_stamp("M18-2k_done")
    git_commit_and_push_job50("carbon2 job50: complete M18-2k (12,000 games at nodes=2000)")

    if bool(rec_18_2k.get("was_cut", False)) or time.time() >= CUTOFF_SAFETY_EPOCH:
        m19_decision = {"checked": True, "run_m19": False, "reason": "stopped at cutoff during/after M18-2k"}
        write_matches_summary(matches_records, m19_decision)
        git_commit_and_push_job50("carbon2 job50: record cutoff after M18-2k")
        return

    # 2. M18-20k
    rec_18_20k = run_match_strict_j50(
        tag="M18-20k",
        out_dir=JOB50,
        exe_path=b12_exe,
        eng1_name="sf_hd_lower_bundle_PC20",
        eng2_name="ours_hd_lower_bundle_PC20",
        e1_switches=sideA_base_eng_opts + live_m18_opts,
        e2_switches=sideA_base_eng_opts,
        each_base_opts=each_base_opts,
        nodes=20000,
        start_line=2081001,
        rounds=1500,
        cutoff_epoch=CUTOFF_SAFETY_EPOCH,
        concurrency=4,
    )
    matches_records.append(
        enrich_match_record(
            tag="M18-20k",
            part="M18",
            nodes=20000,
            start_line=2081001,
            rounds=1500,
            eng1_name="sf_hd_lower_bundle_PC20",
            eng2_name="ours_hd_lower_bundle_PC20",
            sideA_extra_opts=live_m18_opts,
            sideA_extra_desc=m18_desc,
            pred_point=2.5,
            pred_bounds=(-8.0, 13.0),
            rec=rec_18_20k,
        )
    )

    now_after_m18 = time.time()
    rem_min_to_80 = (MINUTE_80_EPOCH - now_after_m18) / 60.0
    loss_is_live = any(k == "HdLowerLoss" for k, _ in live_m18_opts)
    run_m19 = (not bool(rec_18_20k.get("was_cut", False))) and (rem_min_to_80 >= 25.0) and loss_is_live
    m19_decision = {
        "checked": True,
        "utc_checked": utc_now(),
        "remaining_minutes_to_minute_80": round(rem_min_to_80, 2),
        "threshold_minutes": 25.0,
        "HdLowerLoss_live": loss_is_live,
        "run_m19": run_m19,
        "reason": (
            f"{rem_min_to_80:.2f} minutes remaining before Minute 80 (>= 25.0 required) and HdLowerLoss=167 LIVE"
            if run_m19
            else f"{rem_min_to_80:.2f} minutes remaining before Minute 80 (< 25.0 required) or M18 cut"
        ),
    }
    write_matches_summary(matches_records, m19_decision)
    append_stamp("M18-20k_done")
    git_commit_and_push_job50("carbon2 job50: complete Part M18 (M18-20k 3,000 games at nodes=20000)")

    if not run_m19:
        print(f"Skipping Part M19: {m19_decision}", flush=True)
        return

    # 3. Part M19: M19-2k (HdLowerLoss=167 alone)
    m19_opts = [("HdLowerLoss", "167")]
    rec_19_2k = run_match_strict_j50(
        tag="M19-2k",
        out_dir=JOB50,
        exe_path=b12_exe,
        eng1_name="sf_hd_loss167_bundle_PC20",
        eng2_name="ours_hd_lower_bundle_PC20",
        e1_switches=sideA_base_eng_opts + m19_opts,
        e2_switches=sideA_base_eng_opts,
        each_base_opts=each_base_opts,
        nodes=2000,
        start_line=2082501,
        rounds=6000,
        cutoff_epoch=CUTOFF_SAFETY_EPOCH,
        concurrency=4,
    )
    matches_records.append(
        enrich_match_record(
            tag="M19-2k",
            part="M19",
            nodes=2000,
            start_line=2082501,
            rounds=6000,
            eng1_name="sf_hd_loss167_bundle_PC20",
            eng2_name="ours_hd_lower_bundle_PC20",
            sideA_extra_opts=m19_opts,
            sideA_extra_desc="HdLowerLoss=167",
            pred_point=2.0,
            pred_bounds=(-5.0, 9.0),
            rec=rec_19_2k,
        )
    )
    write_matches_summary(matches_records, m19_decision)
    append_stamp("M19-2k_done")
    git_commit_and_push_job50("carbon2 job50: complete Part M19 (M19-2k 12,000 games at nodes=2000)")


if __name__ == "__main__":
    main()
