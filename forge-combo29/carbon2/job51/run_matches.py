#!/usr/bin/env python3
"""
Job 51 Matches Runner (`run_matches.py`):
- Programmatically copies Side B (`all_off_PC20`) and `-each` options from
  `forge-combo29/carbon2/job49/M17-2k_fastchess.txt.meta` (never retyped).
- Side B adds nothing; Side A adds ONE option:
  * `M20-2k`: `HistReworkCorrection=0`, `nodes=2000`, `12,000`g, lines `2,088,501..2,094,500`
  * `M21-2k`: `HistReworkQuiet=0`,      `nodes=2000`, `12,000`g, lines `2,094,501..2,100,500`
  * `M22-2k`: `HistReworkQuiet=3`,      `nodes=2000`, `12,000`g, lines `2,100,501..2,106,500`
  * `M23-2k`: `HistReworkCorrection=3`, `nodes=2000`, `12,000`g, lines `2,106,501..2,112,500`
- Commits and pushes after every match with a `date -u` stamp in `stamps.txt`.
- After `M23-2k`: checks remaining time before Minute 80 (`03:17:57 UTC` = `2026-11-21T03:17:57Z`).
  If `>= 25.0` minutes remain:
  * `M20-20k`: `HistReworkCorrection=0`, `nodes=20000`, `3,000`g, lines `2,112,501..2,114,000`
  * `M21-20k`: `HistReworkQuiet=0`,      `nodes=20000`, `3,000`g, lines `2,114,001..2,115,500`
  with a graceful cutoff at Minute 71.5 (`03:09:27 UTC`) so if `M21-20k` runs long, its finished pairs
  are cleanly recounted and pushed with >= 8 minutes left for the report.
- Programmatically reads `M17-2k` from `forge-combo29/carbon2/job49/M17-2k_recount.txt` and computes
  `M20-2k + M21-2k - M17-2k` with 95% interval (`se = sqrt(se_20^2 + se_21^2 + se_17^2)`).
"""
from __future__ import annotations

import calendar
import json
import pathlib
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from j51_lib import (  # noqa: E402
    JOB49,
    JOB51,
    REPO,
    WORK51,
    diff_elo_interval,
    parse_m17_2k_sideB_options_from_meta,
    run_match_strict_j51,
    three_way_additivity_interval,
    utc_now,
)

# Clock started when FABLE_TO_carbon2_51.md was read: Sat Nov 21 01:57:57 AM UTC 2026
JOB51_START_EPOCH = float(calendar.timegm((2026, 11, 21, 1, 57, 57, 0, 0, 0)))
MINUTE_80_EPOCH = JOB51_START_EPOCH + 80.0 * 60.0        # 03:17:57 UTC
MATCH_CUTOFF_EPOCH = MINUTE_80_EPOCH - 8.5 * 60.0        # 03:09:27 UTC (8.5 min buffer for report)

PREDICTIONS = {
    "M20-2k": (-7.0, -14.5, -0.5),
    "M21-2k": (-5.5, -13.0, +1.0),
    "M22-2k": (-1.5, -8.0, +5.0),
    "M23-2k": (-2.0, -8.5, +4.5),
    "M20-20k": (-5.0, -15.0, +4.0),
    "M21-20k": (-4.0, -14.0, +5.0),
}


def append_stamp_and_push(stamp_key: str, commit_msg: str) -> None:
    st = subprocess.check_output(["date", "-u"], text=True).strip()
    stamps_p = JOB51 / "stamps.txt"
    with open(stamps_p, "a", encoding="utf-8") as sf:
        sf.write(f"{stamp_key}: {st}\n")
    subprocess.run(["git", "add", "forge-combo29/carbon2/job51"], cwd=str(REPO), check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(REPO), check=True)
    for delay in (0, 4, 8, 16, 32):
        if delay:
            time.sleep(delay)
        r = subprocess.run(
            ["git", "push", "-u", "origin", "for-fable-and-opus/carbon2-work"],
            cwd=str(REPO),
        )
        if r.returncode == 0:
            break
    else:
        raise RuntimeError(f"git push failed after retries for {commit_msg}")


def read_m17_2k_from_job49() -> dict[str, object]:
    rec_p = JOB49 / "M17-2k_recount.txt"
    txt = rec_p.read_text(encoding="utf-8")
    m = re.search(r"^recounted_Elo:\s*([+-]?\d+\.\d+)\s*\+/-\s*(\d+\.\d+)", txt, re.MULTILINE)
    if not m:
        raise RuntimeError(f"Could not parse recounted_Elo from {rec_p}")
    return {
        "recount_path": str(rec_p),
        "elo": float(m.group(1)),
        "hw95": float(m.group(2)),
    }


def load_completed_match_if_present(tag: str) -> dict[str, object] | None:
    rec_p = JOB51 / f"{tag}_recount.txt"
    meta_p = JOB51 / f"{tag}_fastchess.txt.meta"
    tsv_p = JOB51 / f"{tag}_games.tsv"
    if not (rec_p.exists() and meta_p.exists() and tsv_p.exists()):
        return None
    txt = rec_p.read_text(encoding="utf-8")
    if "status: COMPLETE" not in txt:
        return None
    m_wld = re.search(r"^recounted_WLD .*?:\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)", txt, re.MULTILINE)
    m_ptn = re.search(r"^recounted_pentanomial .*?:\s*\[([0-9,\s]+)\]\s*\(pairs=(\d+)\)", txt, re.MULTILINE)
    m_elo = re.search(r"^recounted_Elo:\s*([+-]?\d+\.\d+)\s*\+/-\s*(\d+\.\d+)", txt, re.MULTILINE)
    m_fc = re.search(r"^fastchess_own_elo_ptnml:\s*Elo=([+-]?\d+\.\d+)\s*\+/-\s*(\d+\.\d+)", txt, re.MULTILINE)
    meta_txt = meta_p.read_text(encoding="utf-8")
    m_wall = re.search(r"^wall_s:\s*([\d.]+)", meta_txt, re.MULTILINE)
    assert m_wld and m_ptn and m_elo and m_fc and m_wall
    w, l, d = int(m_wld.group(1)), int(m_wld.group(2)), int(m_wld.group(3))
    ptnml = [int(x.strip()) for x in m_ptn.group(1).split(",")]
    pairs = int(m_ptn.group(2))
    elo = float(m_elo.group(1))
    hw95 = float(m_elo.group(2))
    gr = grade_pred(tag, elo)
    return {
        "games": w + l + d,
        "pairs": pairs,
        "w": w,
        "l": l,
        "d": d,
        "W": w,
        "L": l,
        "D": d,
        "ptnml": ptnml,
        "elo": elo,
        "err95": hw95,
        "hw95": hw95,
        "ci_lo": round(elo - hw95, 2),
        "ci_hi": round(elo + hw95, 2),
        "fc_elo": float(m_fc.group(1)),
        "fc_hw95": float(m_fc.group(2)),
        "wall_s": float(m_wall.group(1)),
        "was_cut": False,
        "prediction": gr,
    }


def grade_pred(tag: str, elo: float) -> dict[str, object]:
    p_elo, lo, hi = PREDICTIONS[tag]
    ok = lo <= elo <= hi
    return {
        "pred_elo": p_elo,
        "pred_lo": lo,
        "pred_hi": hi,
        "actual_elo": round(elo, 2),
        "grade": "TRUE" if ok else "FALSE",
    }


def main() -> None:
    b13_exe = WORK51 / "bld_bundle13/forge"
    if not b13_exe.exists():
        raise RuntimeError(f"Missing {b13_exe}")

    # Record prediction_committed stamp before first game
    stamps_txt = (JOB51 / "stamps.txt").read_text(encoding="utf-8")
    if "prediction_verified_before_games:" not in stamps_txt:
        st_now = subprocess.check_output(["date", "-u"], text=True).strip()
        with open(JOB51 / "stamps.txt", "a", encoding="utf-8") as sf:
            sf.write(f"prediction_verified_before_games: {st_now}\n")

    sideB_opts, each_opts, m17_cmd = parse_m17_2k_sideB_options_from_meta()

    matches_2k = [
        ("M20-2k", "hr_corr0", [("HistReworkCorrection", "0")], 2000, 2088501, 6000),
        ("M21-2k", "hr_quiet0", [("HistReworkQuiet", "0")], 2000, 2094501, 6000),
        ("M22-2k", "hr_quiet3", [("HistReworkQuiet", "3")], 2000, 2100501, 6000),
        ("M23-2k", "hr_corr3", [("HistReworkCorrection", "3")], 2000, 2106501, 6000),
    ]

    results: dict[str, dict[str, object]] = {}
    summary_lines: list[str] = [
        f"=== JOB 51 MATCHES SUMMARY (started {utc_now()}) ===",
        f"copied_sideB_from: {JOB49 / 'M17-2k_fastchess.txt.meta'}",
    ]

    for tag, eng1_name, add_opt, nodes, start_ln, rounds in matches_2k:
        existing = load_completed_match_if_present(tag)
        if existing is not None:
            rec = existing
            gr = rec["prediction"]  # type: ignore[assignment]
            results[tag] = rec
            summary_lines.append(
                f"{tag}: {rec['games']}g (COMPLETE, loaded), "
                f"WLD={rec['W']}-{rec['L']}-{rec['D']}, ptnml={rec['ptnml']}, "
                f"Elo={rec['elo']:+.2f} +/- {rec['hw95']:.2f} "
                f"[{rec['ci_lo']:+.2f}, {rec['ci_hi']:+.2f}], wall={rec['wall_s']:.1f}s, pred={gr['grade']}"
            )
            stamps_cur = (JOB51 / "stamps.txt").read_text(encoding="utf-8")
            if f"{tag}_done:" not in stamps_cur:
                (JOB51 / "matches_partial_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
                append_stamp_and_push(f"{tag}_done", f"carbon2 job51: {tag} complete and recounted")
            continue
        e1_sw = list(sideB_opts) + list(add_opt)
        e2_sw = list(sideB_opts)
        rec = run_match_strict_j51(
            tag=tag,
            out_dir=JOB51,
            exe_path=b13_exe,
            eng1_name=eng1_name,
            eng2_name="all_off_PC20",
            e1_switches=e1_sw,
            e2_switches=e2_sw,
            each_base_opts=each_opts,
            nodes=nodes,
            start_line=start_ln,
            rounds=rounds,
            cutoff_epoch=MATCH_CUTOFF_EPOCH,
        )
        gr = grade_pred(tag, float(rec["elo"]))
        rec["prediction"] = gr
        with open(JOB51 / f"{tag}_recount.txt", "a", encoding="utf-8") as rf:
            rf.write(
                f"prediction_check: {gr['grade']} "
                f"(pred {gr['pred_elo']:+.1f}, [{gr['pred_lo']:+.1f}, {gr['pred_hi']:+.1f}])\n"
            )
        results[tag] = rec
        summary_lines.append(
            f"{tag}: {rec['games']}g ({'CUT' if rec['was_cut'] else 'COMPLETE'}), "
            f"WLD={rec['W']}-{rec['L']}-{rec['D']}, ptnml={rec['ptnml']}, "
            f"Elo={rec['elo']:+.2f} +/- {rec['hw95']:.2f} "
            f"[{rec['ci_lo']:+.2f}, {rec['ci_hi']:+.2f}], wall={rec['wall_s']:.1f}s, pred={gr['grade']}"
        )
        (JOB51 / "matches_partial_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        append_stamp_and_push(f"{tag}_done", f"carbon2 job51: {tag} complete and recounted")

    # Compute M20-2k + M21-2k - M17-2k
    m17_info = read_m17_2k_from_job49()
    add_val, add_hw95, add_lo, add_hi = three_way_additivity_interval(
        float(results["M20-2k"]["elo"]),
        float(results["M20-2k"]["hw95"]),
        float(results["M21-2k"]["elo"]),
        float(results["M21-2k"]["hw95"]),
        float(m17_info["elo"]),
        float(m17_info["hw95"]),
    )
    actual_sign = "NEGATIVE" if add_val < 0 else ("POSITIVE" if add_val > 0 else "ZERO")
    sign_grade = "TRUE" if actual_sign == "NEGATIVE" else "FALSE"
    summary_lines.append(
        f"M20-2k + M21-2k - M17-2k = ({results['M20-2k']['elo']:+.2f}) + ({results['M21-2k']['elo']:+.2f}) "
        f"- ({m17_info['elo']:+.2f}) = {add_val:+.2f} +/- {add_hw95:.2f} "
        f"(95% CI [{add_lo:+.2f}, {add_hi:+.2f}]), sign={actual_sign}, pred_sign=NEGATIVE -> {sign_grade}"
    )

    # Check 25-minute gate before Minute 80 after M23-2k!
    rem_min_after_m23 = (MINUTE_80_EPOCH - time.time()) / 60.0
    check_u = utc_now()
    run_20k = rem_min_after_m23 >= 25.0
    summary_lines.append(
        f"post_M23-2k_gate_check ({check_u}): remaining_minutes_before_Minute80 = {rem_min_after_m23:.2f} "
        f"(threshold >= 25.00) -> run_20k_pair = {run_20k}"
    )
    print(summary_lines[-1], flush=True)

    if run_20k:
        matches_20k = [
            ("M20-20k", "hr_corr0", [("HistReworkCorrection", "0")], 20000, 2112501, 1500),
            ("M21-20k", "hr_quiet0", [("HistReworkQuiet", "0")], 20000, 2114001, 1500),
        ]
        for tag, eng1_name, add_opt, nodes, start_ln, rounds in matches_20k:
            if time.time() >= MATCH_CUTOFF_EPOCH - 30.0:
                summary_lines.append(f"{tag}: SKIPPED (reached report buffer before launch)")
                continue
            e1_sw = list(sideB_opts) + list(add_opt)
            e2_sw = list(sideB_opts)
            rec = run_match_strict_j51(
                tag=tag,
                out_dir=JOB51,
                exe_path=b13_exe,
                eng1_name=eng1_name,
                eng2_name="all_off_PC20",
                e1_switches=e1_sw,
                e2_switches=e2_sw,
                each_base_opts=each_opts,
                nodes=nodes,
                start_line=start_ln,
                rounds=rounds,
                cutoff_epoch=MATCH_CUTOFF_EPOCH,
            )
            gr = grade_pred(tag, float(rec["elo"]))
            rec["prediction"] = gr
            with open(JOB51 / f"{tag}_recount.txt", "a", encoding="utf-8") as rf:
                rf.write(
                    f"prediction_check: {gr['grade']} "
                    f"(pred {gr['pred_elo']:+.1f}, [{gr['pred_lo']:+.1f}, {gr['pred_hi']:+.1f}])\n"
                )
            results[tag] = rec
            summary_lines.append(
                f"{tag}: {rec['games']}g ({'CUT' if rec['was_cut'] else 'COMPLETE'}), "
                f"WLD={rec['W']}-{rec['L']}-{rec['D']}, ptnml={rec['ptnml']}, "
                f"Elo={rec['elo']:+.2f} +/- {rec['hw95']:.2f} "
                f"[{rec['ci_lo']:+.2f}, {rec['ci_hi']:+.2f}], wall={rec['wall_s']:.1f}s, pred={gr['grade']}"
            )
            (JOB51 / "matches_partial_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
            append_stamp_and_push(f"{tag}_done", f"carbon2 job51: {tag} recounted")

    # Save final matches_results.json and matches_summary.txt
    final_payload = {
        "minute_80_utc": "Sat Nov 21 03:17:57 AM UTC 2026",
        "rem_min_after_m23": round(rem_min_after_m23, 3),
        "ran_20k_pair": run_20k,
        "m17_2k_job49": m17_info,
        "additivity_2k": {
            "formula": "M20-2k + M21-2k - M17-2k",
            "val": round(add_val, 2),
            "hw95": round(add_hw95, 2),
            "ci_lo": round(add_lo, 2),
            "ci_hi": round(add_hi, 2),
            "actual_sign": actual_sign,
            "predicted_sign": "NEGATIVE",
            "sign_grade": sign_grade,
        },
        "matches": results,
    }
    if "M20-20k" in results and "M21-20k" in results:
        m17_20k_txt = (JOB49 / "M17-20k_recount.txt").read_text(encoding="utf-8")
        mm20 = re.search(r"^recounted_Elo:\s*([+-]?\d+\.\d+)\s*\+/-\s*(\d+\.\d+)", m17_20k_txt, re.MULTILINE)
        if mm20:
            m17_20k_elo, m17_20k_hw = float(mm20.group(1)), float(mm20.group(2))
            v20, hw20, lo20, hi20 = three_way_additivity_interval(
                float(results["M20-20k"]["elo"]),
                float(results["M20-20k"]["hw95"]),
                float(results["M21-20k"]["elo"]),
                float(results["M21-20k"]["hw95"]),
                m17_20k_elo,
                m17_20k_hw,
            )
            final_payload["m17_20k_job49"] = {
                "recount_path": str(JOB49 / "M17-20k_recount.txt"),
                "elo": m17_20k_elo,
                "hw95": m17_20k_hw,
            }
            final_payload["additivity_20k"] = {
                "formula": "M20-20k + M21-20k - M17-20k",
                "val": round(v20, 2),
                "hw95": round(hw20, 2),
                "ci_lo": round(lo20, 2),
                "ci_hi": round(hi20, 2),
            }

    (JOB51 / "matches_results.json").write_text(json.dumps(final_payload, indent=2) + "\n", encoding="utf-8")
    (JOB51 / "matches_summary.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    append_stamp_and_push("matches_all_done", "carbon2 job51: matches summary and additivity check")
    print(f"[{utc_now()}] ALL JOB 51 MATCHES COMPLETE!", flush=True)


if __name__ == "__main__":
    main()
