#!/usr/bin/env python3
"""
Job 49 Matches Runner (`run_matches.py`):
Runs in exact order on `bundle9` (`/tmp/carbon2_job44/bld_bundle9/forge`):
  1. `M16-2k`  : with bundle (`IdeaB8b + HindsightDepth`) on both sides, Side A = `L_k*` (`L2: HistRework=0`) vs Side B = `PC20` (`HistRework=2`),
                 `nodes=2000`, lines `2,060,001..2,066,000` (`12,000` games, `6,000` pairs).
  2. `M17-2k`  : without bundle (all Idea switches & `HindsightDepth` off on both sides), Side A = `L_k*` (`L2`) vs Side B = `PC20`,
                 `nodes=2000`, lines `2,066,001..2,072,000` (`12,000` games, `6,000` pairs).
  3. `M16-20k` : same as `M16`, `nodes=20000`, lines `2,072,001..2,073,500` (`3,000` games, `1,500` pairs).
  4. `M17-20k` : same as `M17`, `nodes=20000`, lines `2,073,501..2,075,000` (`3,000` games, `1,500` pairs).
Computes `M16 - M17` separately at `nodes=2000` and `nodes=20000` (`se = sqrt(se_16^2 + se_17^2)`, `se = hw95 / 1.96`),
and commits + pushes after EVERY match.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from j49_lib import (  # noqa: E402
    BUNDLE9_SIDE_A_SWITCHES,
    BUNDLE9_SIDE_B_SWITCHES,
    EXP_BUNDLE9_SHA,
    JOB49,
    O_FENS_PATH,
    PC20_OPTIONS,
    REPO,
    UHO_BOOK,
    WORK49,
    count_row_diffs,
    diff_elo_interval,
    ensure_bundle9_exe,
    fmt_cmp,
    make_leave_one_out_options,
    read_j39_rows,
    recount_games_tsv,
    run_epd_depth12_strict,
    run_match_strict_j48,
    utc_now,
)

# Minute ~76.5 cutoff (01:24:08 UTC on 2026-11-21) to guarantee clean report commit before Minute 80 (01:27:38 UTC)
CUTOFF_EPOCH = 1795224248.0
EXP_PC20_BUNDLE_O_SUM = 8481645

PREDICTIONS: dict[str, tuple[float, float, float]] = {
    "M16-2k": (-2.0, -9.5, 5.5),
    "M17-2k": (-8.5, -16.0, -1.0),
    "M16-20k": (-3.5, -13.5, 6.5),
    "M17-20k": (-10.0, -20.0, 0.0),
}


def clean_pycache() -> None:
    for p in JOB49.rglob("__pycache__"):
        if p.is_dir():
            shutil.rmtree(p)


def append_stamp(label: str, val: str | None = None) -> None:
    s = val if val is not None else utc_now()
    with open(JOB49 / "stamps.txt", "a", encoding="utf-8") as f:
        f.write(f"{label}: {s}\n")


def git_commit_and_push(msg: str) -> None:
    clean_pycache()
    subprocess.run(["git", "add", "forge-combo29/carbon2/job49/"], cwd=str(REPO), check=True)
    st = subprocess.run(["git", "status", "--porcelain", "forge-combo29/carbon2/job49/"], cwd=str(REPO), check=True, capture_output=True, text=True)
    if not st.stdout.strip():
        return
    subprocess.run(["git", "commit", "-m", msg], cwd=str(REPO), check=True)
    for delay in (0, 4, 8, 16, 32):
        if delay:
            time.sleep(delay)
        res = subprocess.run(
            ["git", "push", "-u", "origin", "for-fable-and-opus/carbon2-work"],
            cwd=str(REPO),
        )
        if res.returncode == 0:
            return
    raise RuntimeError("git push failed after 5 attempts")


def write_summary(
    *,
    b9_exe: str,
    b9_sha: str,
    base_star: str,
    sw_name: str,
    s14_val: str,
    pc20_val: str,
    start_all_utc: str,
    results: list[dict[str, object]],
) -> dict[str, object]:
    by_tag = {str(r["tag"]): r for r in results}
    diffs_by_nodes: dict[str, dict[str, object]] = {}

    for label, m16_tag, m17_tag in [("2000", "M16-2k", "M17-2k"), ("20000", "M16-20k", "M17-20k")]:
        if m16_tag in by_tag and m17_tag in by_tag:
            r16 = by_tag[m16_tag]
            r17 = by_tag[m17_tag]
            if r16["elo"] is not None and r17["elo"] is not None:
                d_elo, d_hw, d_lo, d_hi = diff_elo_interval(
                    float(r16["elo"]), float(r16["err95"]), float(r17["elo"]), float(r17["err95"])
                )
                diffs_by_nodes[label] = {
                    "nodes": int(label),
                    "m16_tag": m16_tag,
                    "m17_tag": m17_tag,
                    "m16_status": r16["status"],
                    "m17_status": r17["status"],
                    "diff_elo": d_elo,
                    "diff_err95": d_hw,
                    "diff_ci_low": d_lo,
                    "diff_ci_high": d_hi,
                    "diff_str": f"{d_elo:+.2f} +/- {d_hw:.2f} [{d_lo:+.2f}, {d_hi:+.2f}]",
                    "excludes_zero": bool(d_lo > 0.0 or d_hi < 0.0),
                }

    lines = [
        f"=== JOB 49 MATCHES M16 & M17: SWITCH k*=2 ({base_star}: {sw_name}={s14_val} vs PC20: {sw_name}={pc20_val}) ===",
        f"start_utc: {start_all_utc}",
        f"updated_utc: {utc_now()}",
        f"exe_path: {b9_exe}",
        f"exe_sha256({b9_exe}): {b9_sha}",
        "",
        "--- Four Matches Summary Table ---",
        "  match   | nodes | bundle_state                 | status   | games | W - L - D         | pentanomial [LL,LD,WL+DD,WD,WW] | Elo +/- 95% [CI]                 | pred_check",
        "  --------+-------+------------------------------+----------+-------+-------------------+---------------------------------+----------------------------------+-----------",
    ]
    for r in results:
        if r["elo"] is not None:
            elo_s = f"{float(r['elo']):+.2f} +/- {float(r['err95']):.2f} [{float(r['ci_low']):+.2f}, {float(r['ci_high']):+.2f}]"
        else:
            elo_s = "N/A"
        wld_s = f"{r['w']}-{r['l']}-{r['d']}"
        lines.append(
            f"  {str(r['tag']):<7s} | {int(r['nodes']):5d} | {str(r['bundle_desc']):<28s} | {str(r['status']):<8s} | "
            f"{int(r['games']):5d} | {wld_s:<17s} | {str(r['ptnml']):<31s} | "
            f"{elo_s:<32s} | {r['pred_status']}"
        )

    lines.append("\n--- M16 minus M17 at Each Node Count (Quoted Strictly Apart; se = sqrt(se_16^2 + se_17^2)) ---")
    for label, m16_tag, m17_tag in [("2000", "M16-2k", "M17-2k"), ("20000", "M16-20k", "M17-20k")]:
        if label in diffs_by_nodes:
            d = diffs_by_nodes[label]
            lines.append(
                f"  nodes={label:<5s}: Elo({m16_tag}) - Elo({m17_tag}) = {d['diff_str']} "
                f"(95% CI excludes 0: {d['excludes_zero']})"
            )
        else:
            lines.append(f"  nodes={label:<5s}: pending ({m16_tag} and/or {m17_tag} not yet complete)")

    lines.append("\n--- Per-Match Fastchess Own Lines & Recounts ---")
    for r in results:
        lines.append(
            f"  {r['tag']} (nodes={r['nodes']}, {r['bundle_desc']}, book {r['start_line']}..{r['end_line']}, wall={float(r['wall_s']):.1f}s):"
        )
        lines.append(
            f"    recounted : {r['w']}-{r['l']}-{r['d']}, ptnml={r['ptnml']}, "
            f"Elo={float(r['elo']):+.2f} +/- {float(r['err95']):.2f} [{float(r['ci_low']):+.2f}, {float(r['ci_high']):+.2f}]"
            if r["elo"] is not None
            else f"    recounted : {r['w']}-{r['l']}-{r['d']}, ptnml={r['ptnml']}, Elo=N/A"
        )
        lines.append(f"    fastchess : {r['fc_own_line']}")

    summary_txt = "\n".join(lines) + "\n"
    (JOB49 / "matches_summary.txt").write_text(summary_txt, encoding="utf-8")
    payload = {
        "k_star": 2,
        "base_star": base_star,
        "switch_name": sw_name,
        "s14_value": s14_val,
        "pc20_value": pc20_val,
        "matches": results,
        "m16_minus_m17_by_nodes": diffs_by_nodes,
    }
    (JOB49 / "matches_results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    WORK49.mkdir(parents=True, exist_ok=True)
    stamps_cur = (JOB49 / "stamps.txt").read_text(encoding="utf-8")
    if "prediction_committed:" not in stamps_cur:
        pred_txt = (JOB49 / "prediction_job49.txt").read_text(encoding="utf-8")
        m_pu = re.search(r"^prediction_utc:\s*(.+)$", pred_txt, re.M)
        append_stamp("prediction_committed", m_pu.group(1).strip() if m_pu else utc_now())

    kstar_data = json.loads((JOB49 / "kstar.json").read_text(encoding="utf-8"))
    base_star = str(kstar_data["base_star"])
    sw_name = str(kstar_data["switch_name"])
    s14_val = str(kstar_data["s14_value"])
    pc20_dict = dict(PC20_OPTIONS)
    pc20_val = pc20_dict[sw_name]
    common_each_opts = [(k, v) for (k, v) in PC20_OPTIONS if k != sw_name]

    b9_exe, b9_sha, _ = ensure_bundle9_exe()
    assert b9_sha == EXP_BUNDLE9_SHA

    # Liveness check for M16 (Side A vs Side B on O at depth 12) and M17 (from Step 0 O rows)
    if (JOB49 / "liveness_M16_M17.json").exists() and (JOB49 / "liveness_M16_M17.txt").exists():
        print((JOB49 / "liveness_M16_M17.txt").read_text(encoding="utf-8").strip(), flush=True)
    else:
        print(f"[{utc_now()}] Running M16 depth-12 liveness check on O (200 positions)...", flush=True)
        lk_opts = make_leave_one_out_options(base_star)
        m16_a_rows = run_epd_depth12_strict(
            b9_exe,
            O_FENS_PATH,
            lk_opts,
            BUNDLE9_SIDE_A_SWITCHES,
            JOB49 / f"M16_liveness_SideA_{base_star}_bundle_O_d12.rows.txt",
            JOB49 / f"M16_liveness_SideA_{base_star}_bundle_O_d12.rows.txt.meta",
            depth=12,
            cpu_pin=0,
        )
        m16_b_rows = run_epd_depth12_strict(
            b9_exe,
            O_FENS_PATH,
            PC20_OPTIONS,
            BUNDLE9_SIDE_A_SWITCHES,
            JOB49 / "M16_liveness_SideB_PC20_bundle_O_d12.rows.txt",
            JOB49 / "M16_liveness_SideB_PC20_bundle_O_d12.rows.txt.meta",
            depth=12,
            cpu_pin=0,
        )
        m16_a_sum = sum(r[1] for r in m16_a_rows)
        m16_b_sum = sum(r[1] for r in m16_b_rows)
        ok_m16b, s_m16b = fmt_cmp("M16 Side B (PC20 + bundle) O d12 known-answer sum", m16_b_sum, EXP_PC20_BUNDLE_O_SUM)
        if not ok_m16b:
            raise RuntimeError(s_m16b)
        c16 = count_row_diffs(m16_a_rows, m16_b_rows)
        m16_nd, m16_bm, m16_sc = int(c16["nodes_diff"]), int(c16["bestmove_diff"]), int(c16["score_diff"])

        m17_a_rows = read_j39_rows(JOB49 / f"step0_bundle9_{base_star}_all_off_O_d12.rows.txt")
        m17_b_rows = read_j39_rows(JOB49 / "step0_bundle9_PC20_all_off_O_d12.rows.txt")
        m17_a_sum = sum(r[1] for r in m17_a_rows)
        m17_b_sum = sum(r[1] for r in m17_b_rows)
        c17 = count_row_diffs(m17_a_rows, m17_b_rows)
        m17_nd, m17_bm, m17_sc = int(c17["nodes_diff"]), int(c17["bestmove_diff"]), int(c17["score_diff"])

        liv_lines = [
            f"=== JOB 49 LIVENESS OF M16 AND M17 ON O (200 POSITIONS, DEPTH 12) ===",
            f"utc: {utc_now()}",
            s_m16b,
            f"  M16 (with bundle): Side A ({base_star}) O_sum={m16_a_sum} vs Side B (PC20) O_sum={m16_b_sum} "
            f"(delta={m16_a_sum - m16_b_sum:+d}) | diffs: nodes={m16_nd}/200, bestmove={m16_bm}/200, score={m16_sc}/200",
            f"  M17 (all off)    : Side A ({base_star}) O_sum={m17_a_sum} vs Side B (PC20) O_sum={m17_b_sum} "
            f"(delta={m17_a_sum - m17_b_sum:+d}) | diffs: nodes={m17_nd}/200, bestmove={m17_bm}/200, score={m17_sc}/200",
        ]
        (JOB49 / "liveness_M16_M17.txt").write_text("\n".join(liv_lines) + "\n", encoding="utf-8")
        (JOB49 / "liveness_M16_M17.json").write_text(
            json.dumps(
                {
                    "m16_sideA_o_sum": m16_a_sum,
                    "m16_sideB_o_sum": m16_b_sum,
                    "m16_o_delta": m16_a_sum - m16_b_sum,
                    "m16_nodes_diff": m16_nd,
                    "m16_bm_diff": m16_bm,
                    "m16_sc_diff": m16_sc,
                    "m17_sideA_o_sum": m17_a_sum,
                    "m17_sideB_o_sum": m17_b_sum,
                    "m17_o_delta": m17_a_sum - m17_b_sum,
                    "m17_nodes_diff": m17_nd,
                    "m17_bm_diff": m17_bm,
                    "m17_sc_diff": m17_sc,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print("\n".join(liv_lines), flush=True)

    schedule = [
        (
            "M16-2k",
            "IdeaB8b+HindsightDepth ON",
            f"bundle_on_{base_star}",
            "bundle_on_PC20",
            [(sw_name, s14_val)] + BUNDLE9_SIDE_A_SWITCHES,
            [(sw_name, pc20_val)] + BUNDLE9_SIDE_A_SWITCHES,
            2000,
            2060001,
            6000,
        ),
        (
            "M17-2k",
            "all Idea & HindsightDepth OFF",
            f"all_off_{base_star}",
            "all_off_PC20",
            [(sw_name, s14_val)] + BUNDLE9_SIDE_B_SWITCHES,
            [(sw_name, pc20_val)] + BUNDLE9_SIDE_B_SWITCHES,
            2000,
            2066001,
            6000,
        ),
        (
            "M16-20k",
            "IdeaB8b+HindsightDepth ON",
            f"bundle_on_{base_star}",
            "bundle_on_PC20",
            [(sw_name, s14_val)] + BUNDLE9_SIDE_A_SWITCHES,
            [(sw_name, pc20_val)] + BUNDLE9_SIDE_A_SWITCHES,
            20000,
            2072001,
            1500,
        ),
        (
            "M17-20k",
            "all Idea & HindsightDepth OFF",
            f"all_off_{base_star}",
            "all_off_PC20",
            [(sw_name, s14_val)] + BUNDLE9_SIDE_B_SWITCHES,
            [(sw_name, pc20_val)] + BUNDLE9_SIDE_B_SWITCHES,
            20000,
            2073501,
            1500,
        ),
    ]

    start_all_utc = utc_now()
    results: list[dict[str, object]] = []

    for tag, bdesc, eng1_name, eng2_name, e1_sw, e2_sw, nodes, start_line, rounds in schedule:
        rec_path = JOB49 / f"{tag}_recount.txt"
        tsv_path = JOB49 / f"{tag}_games.tsv"
        fc_path = JOB49 / f"{tag}_fastchess.txt"
        meta_path = JOB49 / f"{tag}_fastchess.txt.meta"
        already_completed = (
            rec_path.exists()
            and tsv_path.exists()
            and fc_path.exists()
            and meta_path.exists()
            and "status: COMPLETE" in rec_path.read_text(encoding="utf-8")
        )

        if already_completed:
            print(f"[{utc_now()}] Resuming already-finished {tag} from disk...", flush=True)
            rec = recount_games_tsv(
                tag=tag,
                tsv_path=tsv_path,
                fc_txt_path=fc_path,
                out_recount_path=WORK49 / f"tmp_verify_{tag}_recount.txt",
                engine1=eng1_name,
                engine2=eng2_name,
                book_path=UHO_BOOK,
                start_line=start_line,
                target_rounds=rounds,
                was_cut=False,
            )
            meta_txt = meta_path.read_text(encoding="utf-8")
            m_ws = re.search(r"^wall_s:\s*([0-9.]+)", meta_txt, re.M)
            rec["wall_s"] = float(m_ws.group(1)) if m_ws else 0.0
            rec["was_cut"] = False
        else:
            if time.time() >= CUTOFF_EPOCH:
                print(f"[{utc_now()}] Reached CUTOFF_EPOCH before {tag}; stopping cleanly.", flush=True)
                break

            rec = run_match_strict_j48(
                tag=tag,
                out_dir=JOB49,
                exe_path=pathlib.Path(b9_exe),
                eng1_name=eng1_name,
                eng2_name=eng2_name,
                e1_switches=e1_sw,
                e2_switches=e2_sw,
                each_base_opts=common_each_opts,
                nodes=nodes,
                start_line=start_line,
                rounds=rounds,
                cutoff_epoch=CUTOFF_EPOCH,
            )

        rec_txt = rec_path.read_text(encoding="utf-8")
        fc_own = ""
        for ln in rec_txt.splitlines():
            if ln.startswith("fastchess_own_line: "):
                fc_own = ln[len("fastchess_own_line: ") :]
                break

        elo = rec.get("elo")
        hw95 = rec.get("err95")
        ci_low = float(elo) - float(hw95) if (elo is not None and hw95 is not None) else None
        ci_high = float(elo) + float(hw95) if (elo is not None and hw95 is not None) else None

        pp, plo, phi = PREDICTIONS[tag]
        if elo is not None:
            pred_held = bool(plo <= float(elo) <= phi)
            pred_str = f"{'TRUE' if pred_held else 'FALSE'} (pred {pp:+.1f}, [{plo:+.1f}, {phi:+.1f}])"
        else:
            pred_held = None
            pred_str = "CUT (no Elo)"

        if "prediction_check:" not in rec_txt:
            with open(rec_path, "a", encoding="utf-8") as rf:
                rf.write(f"prediction_check: {pred_str}\n")

        item = {
            "tag": tag,
            "nodes": nodes,
            "bundle_desc": bdesc,
            "eng1_name": eng1_name,
            "eng2_name": eng2_name,
            "start_line": start_line,
            "end_line": start_line + rounds - 1,
            "target_rounds": rounds,
            "target_games": rounds * 2,
            "status": "CUT" if bool(rec["was_cut"]) else "COMPLETE",
            "was_cut": bool(rec["was_cut"]),
            "games": int(rec["games"]),
            "pairs": int(rec["pairs"]),
            "w": int(rec["w"]),
            "l": int(rec["l"]),
            "d": int(rec["d"]),
            "ptnml": list(rec["ptnml"]),
            "elo": float(elo) if elo is not None else None,
            "err95": float(hw95) if hw95 is not None else None,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "fc_own_line": fc_own,
            "pred_point": pp,
            "pred_bounds": [plo, phi],
            "pred_held": pred_held,
            "pred_status": pred_str,
            "wall_s": float(rec["wall_s"]),
        }
        results.append(item)

        payload = write_summary(
            b9_exe=b9_exe,
            b9_sha=b9_sha,
            base_star=base_star,
            sw_name=sw_name,
            s14_val=s14_val,
            pc20_val=pc20_val,
            start_all_utc=start_all_utc,
            results=results,
        )
        append_stamp(f"{tag}_done")
        elo_msg = f"{float(elo):+.2f} +/- {float(hw95):.2f}" if elo is not None else "N/A"
        git_commit_and_push(f"carbon2 job49: complete {tag} ({item['status']}, {item['games']}g, Elo {elo_msg})")
        print(f"[{utc_now()}] Committed and pushed {tag}: Elo={elo_msg}", flush=True)

        if bool(rec["was_cut"]):
            break

    print((JOB49 / "matches_summary.txt").read_text(encoding="utf-8"), flush=True)


if __name__ == "__main__":
    main()
