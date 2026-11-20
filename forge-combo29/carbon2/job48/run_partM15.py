#!/usr/bin/env python3
"""
Job 48 Part M15 (`run_partM15.py`): SIX LEAVE-ONE-OUT MATCHES AT 2,000 NODES.
Order and UHO book slices (12,000 games = 6,000 pairs each, sequential):
  1. M15-0: base PC20 (as sent by the PC)          lines 2,024,001..2,030,000
  2. M15-2: base L2 (HistRework 0)                  lines 2,030,001..2,036,000
  3. M15-4: base L4 (CorrHistV2 false)              lines 2,036,001..2,042,000
  4. M15-1: base L1 (CuckooRep false)               lines 2,042,001..2,048,000
  5. M15-3: base L3 (TtPruneV2 false)               lines 2,048,001..2,054,000
  6. M15-5: base L5 (MateAlphaGuard false)          lines 2,054,001..2,060,000
Side A = IdeaB8b + HindsightDepth on (`BUNDLE9_SIDE_A_SWITCHES`).
Side B = every Idea switch and HindsightDepth off (`BUNDLE9_SIDE_B_SWITCHES`).
Commits and pushes on `for-fable-and-opus/carbon2-work` after EVERY match.
"""
from __future__ import annotations

import argparse
import calendar
import json
import pathlib
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j48_lib import (  # noqa: E402
    BUNDLE9_SIDE_A_SWITCHES,
    BUNDLE9_SIDE_B_SWITCHES,
    JOB48,
    LEAVE_ONE_OUT_SPECS,
    PC20_OPTIONS,
    REPO,
    diff_elo_interval,
    ensure_bundle9_exe,
    make_leave_one_out_options,
    run_match_strict_j48,
    utc_now,
)

# Claimed at Fri Nov 20 11:01:20 PM UTC 2026 -> Minute 80 = 00:21:20 UTC
CLAIM_EPOCH = calendar.timegm((2026, 11, 20, 23, 1, 20, 0, 0, 0))
DEFAULT_CUTOFF_EPOCH = float(CLAIM_EPOCH + 74 * 60)  # Minute 74 (00:15:20 UTC), leaving 6m for Report before Minute 80

MATCH_SCHEDULE: list[tuple[str, str, str, int, int, tuple[float, float]]] = [
    ("M15-0", "PC20", "PC20 (as sent by the PC)", 2024001, 6000, (2.5, 16.5)),
    ("M15-2", "L2", "L2 (HistRework 0)", 2030001, 6000, (7.5, 21.5)),
    ("M15-4", "L4", "L4 (CorrHistV2 false)", 2036001, 6000, (3.5, 17.5)),
    ("M15-1", "L1", "L1 (CuckooRep false)", 2042001, 6000, (2.5, 16.5)),
    ("M15-3", "L3", "L3 (TtPruneV2 false)", 2048001, 6000, (4.0, 18.0)),
    ("M15-5", "L5", "L5 (MateAlphaGuard false)", 2054001, 6000, (2.5, 16.5)),
]

PRED_POINT: dict[str, float] = {
    "M15-0": 9.5,
    "M15-2": 14.5,
    "M15-4": 10.5,
    "M15-1": 9.5,
    "M15-3": 11.0,
    "M15-5": 9.5,
}


def git_commit_and_push(commit_msg: str) -> None:
    pycache = JOB48 / "__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache)
    subprocess.run(["git", "-C", str(REPO), "add", "forge-combo29/carbon2/job48/"], check=True)
    subprocess.run(["git", "-C", str(REPO), "commit", "-m", commit_msg], check=True)
    for delay in (0, 4, 8, 16, 32):
        if delay > 0:
            time.sleep(delay)
        r = subprocess.run(
            ["git", "-C", str(REPO), "push", "-u", "origin", "for-fable-and-opus/carbon2-work"],
            capture_output=True,
            text=True,
        )
        if r.returncode == 0:
            return
    raise RuntimeError(f"git push failed after retries: {r.stderr}")


def write_m15_summary(
    records: list[dict[str, object]],
    skipped_dead: list[tuple[str, str]],
    not_done: list[tuple[str, str]],
    b9_exe: str,
    b9_sha: str,
    start_u: str,
) -> None:
    rec0 = next((r for r in records if r["tag"] == "M15-0"), None)
    lines: list[str] = [
        "=== JOB 48 PART M15: LEAVE-ONE-OUT BUNDLE MATCHES AT 2,000 NODES (12,000 GAMES / 6,000 PAIRS EACH) ===",
        f"start_utc: {start_u}",
        f"updated_utc: {utc_now()}",
        f"exe_path: {b9_exe}",
        f"exe_sha256({b9_exe}): {b9_sha}",
        "side_A: IdeaB8b=true, HindsightDepth=true (other 8 Idea switches false)",
        "side_B: all 9 Idea switches and HindsightDepth false",
        "",
        "--- Summary Table (in Execution Order, Each Beside M15-0 With Difference and 95% Interval) ---",
        "  match | base                     | status   | games | W - L - D            | pentanomial [LL,LD,WL+DD,WD,WW] | Elo +/- 95% [CI]                   | diff vs M15-0 +/- 95% [CI]         | pred_check",
        "  ------+--------------------------+----------+-------+----------------------+---------------------------------+------------------------------------+------------------------------------+-----------",
    ]

    for r in records:
        tag = str(r["tag"])
        bdesc = str(r["base_desc"])
        st = str(r["status"])
        gms = int(r["games"])
        wld = f"{r['w']}-{r['l']}-{r['d']}"
        ptn = str(r["ptnml"])
        elo = float(r["elo"])
        err95 = float(r["err95"])
        cil = float(r["ci_low"])
        cih = float(r["ci_high"])
        elo_s = f"{elo:+.2f} +/- {err95:.2f} [{cil:+.2f}, {cih:+.2f}]"
        diff_s = str(r["diff_str"])
        pchk = str(r["pred_status"])
        lines.append(
            f"  {tag:<5s} | {bdesc:<24s} | {st:<8s} | {gms:>5d} | {wld:<20s} | {ptn:<31s} | {elo_s:<34s} | {diff_s:<34s} | {pchk}"
        )

    for dtag, ddesc in skipped_dead:
        lines.append(f"  {dtag:<5s} | {ddesc:<24s} | DEAD     |     0 | not played (DEAD in Part L: 553/553 equal to PC20)")

    for ntag, ndesc in not_done:
        lines.append(f"  {ntag:<5s} | {ndesc:<24s} | NOT DONE |     0 | not started (stopped at cutoff before Minute 80)")

    if rec0 is not None:
        lines.append("")
        lines.append("--- Per-Match Fastchess Lines & Exact Recount Comparisons ---")
        for r in records:
            tag = str(r["tag"])
            fc_line = ""
            for rl in (JOB48 / f"{tag}_recount.txt").read_text(encoding="utf-8").splitlines():
                if rl.startswith("fastchess_own_line: "):
                    fc_line = rl[len("fastchess_own_line: ") :]
                    break
            lines.append(f"  {tag} ({r['base_desc']}, book {r['start_line']}..{r['end_line']}, wall={r['wall_s']:.1f}s):")
            lines.append(f"    recounted : {r['w']}-{r['l']}-{r['d']}, ptnml={r['ptnml']}, Elo={r['elo']:+.2f} +/- {r['err95']:.2f} [{r['ci_low']:+.2f}, {r['ci_high']:+.2f}]")
            lines.append(f"    fastchess : {fc_line}")
            lines.append(f"    vs M15-0  : {r['diff_str']}")

    (JOB48 / "M15_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (JOB48 / "M15_results.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff-epoch", type=float, default=DEFAULT_CUTOFF_EPOCH)
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    b9_exe, b9_sha, _ = ensure_bundle9_exe()
    partl_status = json.loads((JOB48 / "partL_status.json").read_text(encoding="utf-8"))

    start_u = utc_now()
    records: list[dict[str, object]] = []
    skipped_dead: list[tuple[str, str]] = []
    not_done: list[tuple[str, str]] = []

    rec0_elo: float | None = None
    rec0_err95: float | None = None

    for idx, (tag, base_key, base_desc, start_line, rounds, pred_bounds) in enumerate(MATCH_SCHEDULE):
        if base_key != "PC20" and bool(partl_status[base_key]["is_dead"]):
            skipped_dead.append((tag, base_desc))
            continue

        if time.time() >= args.cutoff_epoch:
            for rem_tag, rem_bk, rem_desc, _, _, _ in MATCH_SCHEDULE[idx:]:
                if rem_bk != "PC20" and bool(partl_status[rem_bk]["is_dead"]):
                    skipped_dead.append((rem_tag, rem_desc))
                else:
                    not_done.append((rem_tag, rem_desc))
            write_m15_summary(records, skipped_dead, not_done, b9_exe, b9_sha, start_u)
            with open(JOB48 / "stamps.txt", "a", encoding="utf-8") as sf:
                sf.write(f"partM15_cutoff_reached: {utc_now()}\n")
            git_commit_and_push("carbon2 job48: record M15 cutoff status before Minute 80")
            break

        base_opts = list(PC20_OPTIONS) if base_key == "PC20" else make_leave_one_out_options(base_key)
        eng1 = f"bundle_on_{base_key}"
        eng2 = f"all_off_{base_key}"

        rec = run_match_strict_j48(
            tag=tag,
            out_dir=JOB48,
            exe_path=pathlib.Path(b9_exe),
            eng1_name=eng1,
            eng2_name=eng2,
            e1_switches=BUNDLE9_SIDE_A_SWITCHES,
            e2_switches=BUNDLE9_SIDE_B_SWITCHES,
            each_base_opts=base_opts,
            nodes=2000,
            start_line=start_line,
            rounds=rounds,
            cutoff_epoch=args.cutoff_epoch,
            concurrency=args.concurrency,
        )

        elo = float(rec["elo"])
        err95 = float(rec["err95"])
        if tag == "M15-0":
            rec0_elo = elo
            rec0_err95 = err95
            diff_val, diff_hw, diff_lo, diff_hi = 0.0, 0.0, 0.0, 0.0
            diff_str = "baseline (0.00)"
        else:
            assert rec0_elo is not None and rec0_err95 is not None
            diff_val, diff_hw, diff_lo, diff_hi = diff_elo_interval(elo, err95, rec0_elo, rec0_err95)
            diff_str = f"{diff_val:+.2f} +/- {diff_hw:.2f} [{diff_lo:+.2f}, {diff_hi:+.2f}]"

        plo, phi = pred_bounds
        pred_held = plo <= elo <= phi
        pred_status = f"{'TRUE' if pred_held else 'FALSE'} (pred {PRED_POINT[tag]:+.1f}, [{plo:+.1f}, {phi:+.1f}])"

        with open(JOB48 / f"{tag}_recount.txt", "a", encoding="utf-8") as rf:
            rf.write(f"diff_vs_M15_0: {diff_str}\n")
            rf.write(f"prediction_check: {pred_status}\n")

        row_obj: dict[str, object] = {
            "tag": tag,
            "base_key": base_key,
            "base_desc": base_desc,
            "start_line": start_line,
            "end_line": start_line + rounds - 1,
            "status": str(rec["status"]),
            "was_cut": bool(rec["was_cut"]),
            "games": int(rec["games"]),
            "pairs": int(rec["pairs"]),
            "w": int(rec["w"]),
            "l": int(rec["l"]),
            "d": int(rec["d"]),
            "ptnml": list(rec["ptnml"]),
            "elo": elo,
            "err95": err95,
            "ci_low": float(rec["ci_low"]),
            "ci_high": float(rec["ci_high"]),
            "diff_elo": diff_val,
            "diff_err95": diff_hw,
            "diff_ci_low": diff_lo,
            "diff_ci_high": diff_hi,
            "diff_str": diff_str,
            "pred_point": PRED_POINT[tag],
            "pred_bounds": list(pred_bounds),
            "pred_held": pred_held,
            "pred_status": pred_status,
            "wall_s": float(rec["wall_s"]),
        }
        records.append(row_obj)

        # If this match itself was CUT at cutoff_epoch, mark remaining matches NOT DONE before committing
        if bool(rec["was_cut"]):
            for rem_tag, rem_bk, rem_desc, _, _, _ in MATCH_SCHEDULE[idx + 1 :]:
                if rem_bk != "PC20" and bool(partl_status[rem_bk]["is_dead"]):
                    skipped_dead.append((rem_tag, rem_desc))
                else:
                    not_done.append((rem_tag, rem_desc))

        write_m15_summary(records, skipped_dead, not_done, b9_exe, b9_sha, start_u)
        with open(JOB48 / "stamps.txt", "a", encoding="utf-8") as sf:
            sf.write(f"{tag}_done: {utc_now()}\n")

        git_commit_and_push(
            f"carbon2 job48: complete {tag} ({base_desc}, {rec['games']}g: {elo:+.2f} +/- {err95:.2f} Elo)"
        )
        print(f"[{utc_now()}] Committed and pushed {tag}: Elo={elo:+.2f} +/- {err95:.2f} | vs M15-0: {diff_str}", flush=True)

        if bool(rec["was_cut"]):
            break

    print((JOB48 / "M15_summary.txt").read_text(encoding="utf-8"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
