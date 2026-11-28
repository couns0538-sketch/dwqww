"""Wave 7 Automated Freeze-Readiness & Live-Delivery Pre-Flight Audit.

Strictly read-only & CPU-only (`CUDA_VISIBLE_DEVICES=""`, `python -B`).
Writes ONLY the output JSON report (`--out`, defaulting to `freeze_readiness_w7.json`
in the script's directory) and never modifies any files in `C:\\nnue-lab\\`.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

LAB = Path(r"C:\nnue-lab")
NEON = LAB / "neon"
FF = NEON / "forge_fixes"
FQ = NEON / "filter_quest"
W6_STAGER = FF / "teamwork_wave6" / "streamC_final_delivery_w6" / "stage_teamwork_delivery_w6.py"
W6_INDEX = FF / "teamwork_wave6" / "streamC_final_delivery_w6" / "DEBATE_EVIDENCE_INDEX_W6.md"
LIVE_DELIVERY_DEST = LAB / "teamwork" / "neon_12h_quest_delivery"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_handoff_md(handoff_path: Path, live_sb_count: int) -> dict[str, Any]:
    if not handoff_path.exists():
        return {"exists": False, "error": f"Missing {handoff_path}"}
    text = handoff_path.read_text(encoding="utf-8", errors="replace")
    marker_re = re.compile(r"\[(?:PENDING|TRAINING|TESTING)[^\]]*(?:\]|$)")
    marker_hits: list[dict[str, Any]] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        for m in marker_re.finditer(line):
            marker_hits.append(
                {
                    "line": idx,
                    "marker": m.group(0),
                    "line_excerpt": line.strip()[:220],
                }
            )

    stale_findings: list[dict[str, Any]] = []
    # Detect stale counts / stale phase notes dynamically
    stale_patterns = [
        ("stale_wave5_banner", re.compile(r"Wave 5 running in parallel")),
        ("stale_43_match_ledger", re.compile(r"Complete 43-match ledger")),
        ("stale_51_completed_matches", re.compile(r"`51` completed matches")),
        ("stale_pending_g3_row", re.compile(r"\*\*`G3 250k`, `G3 PGO 6\+0\.06`, Stage-2 `12` matches`\*\*")),
        ("stale_13_stage2_arms", re.compile(r"All `13/13` Stage-2 GPU arms trained")),
        ("stale_testing_g3ab", re.compile(r"Does keeping noisy \(`bit0`\) positions \(`G3a`\) outperform skipping them \(`G3b`\).*\[TESTING NEXT\]")),
    ]
    for idx, line in enumerate(text.splitlines(), start=1):
        for tag, pat in stale_patterns:
            if pat.search(line):
                stale_findings.append(
                    {
                        "tag": tag,
                        "line": idx,
                        "line_excerpt": line.strip()[:220],
                    }
                )

    return {
        "exists": True,
        "path": str(handoff_path),
        "bytes": handoff_path.stat().st_size,
        "sha256": sha256_file(handoff_path),
        "marker_count": len(marker_hits),
        "unique_markers": sorted({h["marker"] for h in marker_hits}),
        "marker_hits": marker_hits,
        "stale_findings_count": len(stale_findings),
        "stale_findings": stale_findings,
        "live_scoreboard_md_count_for_comparison": live_sb_count,
    }


def _is_md_alignment_cell(cell: str) -> bool:
    return bool(re.fullmatch(r":?-{3,}:?", cell.strip()))


def parse_scoreboard_md(sb_md: Path) -> tuple[int | None, list[str]]:
    text = sb_md.read_text(encoding="utf-8", errors="replace")
    hdr_m = re.search(r"Total completed matches:\s*\*\*(\d+)\*\*", text)
    declared_total = int(hdr_m.group(1)) if hdr_m else None
    names: list[str] = []
    for ln in text.splitlines():
        stripped = ln.lstrip()
        if not stripped.startswith("|"):
            continue
        cols = [c.strip() for c in stripped.strip("|").split("|")]
        if (
            len(cols) >= 9
            and cols[0] != "Group"
            and not _is_md_alignment_cell(cols[0])
            and not _is_md_alignment_cell(cols[1])
        ):
            names.append(cols[1].strip("`"))
    return declared_total, names


def parse_w6_index_scoreboard(idx_path: Path) -> list[str]:
    if not idx_path.exists():
        return []
    text = idx_path.read_text(encoding="utf-8", errors="replace")
    if "## 4. Unpooled Fastchess Scoreboard" not in text or "## 5. Open Debate Questions" not in text:
        return []
    sec4 = text.split("## 4. Unpooled Fastchess Scoreboard")[1].split("## 5. Open Debate Questions")[0]
    names: list[str] = []
    for ln in sec4.splitlines():
        if re.match(r"^\|\s*\d+\s*\|", ln):
            cols = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cols) >= 9:
                names.append(cols[2].strip("`"))
    return names


def _is_summary_completed(sdata: Any) -> bool:
    if not isinstance(sdata, dict):
        return False
    if "finished" in sdata:
        return bool(sdata.get("finished"))
    if sdata.get("rc") != 0:
        return False
    verdict = str(sdata.get("verdict") or "").strip()
    if not verdict or verdict.upper() in {"ERROR", "INCOMPLETE", "ABORTED", "FAILED", "CANCELLED", "CANCELED"}:
        return False
    try:
        games = int(sdata.get("games") or 0)
    except (TypeError, ValueError):
        return False
    return games > 0


def collect_completed_disk_matches(roots: tuple[Path, ...] | None = None) -> list[str]:
    if roots is None:
        roots = (FF / "matches", FQ / "matches")
    completed: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for d in root.iterdir():
            if not d.is_dir():
                continue
            sp = d / "summary.json"
            if sp.exists():
                try:
                    sdata = json.loads(sp.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError, ValueError):
                    continue
                if _is_summary_completed(sdata):
                    completed.add(d.name)
    return sorted(completed)


def audit_scoreboards(completed_disk_names: list[str] | set[str] | None = None) -> dict[str, Any]:
    sb_md_path = FF / "ALL_MATCHES_SCOREBOARD.md"
    sb_json_path = FF / "ALL_MATCHES_SCOREBOARD.json"

    md_declared, md_names = parse_scoreboard_md(sb_md_path)
    sb_json = json.loads(sb_json_path.read_text(encoding="utf-8"))
    json_names = [e.get("name") or e.get("match") for e in sb_json]
    w6_names = parse_w6_index_scoreboard(W6_INDEX)

    if completed_disk_names is None:
        completed_disk_names = collect_completed_disk_matches()

    md_set = set(md_names)
    json_set = set(json_names)
    w6_set = set(w6_names)
    completed_disk_set = set(completed_disk_names)

    return {
        "scoreboard_md_path": str(sb_md_path),
        "scoreboard_md_bytes": sb_md_path.stat().st_size,
        "scoreboard_md_sha256": sha256_file(sb_md_path),
        "scoreboard_md_declared_total": md_declared,
        "scoreboard_md_row_count": len(md_names),
        "scoreboard_md_header_matches_rows": (md_declared == len(md_names)),
        "scoreboard_json_path": str(sb_json_path),
        "scoreboard_json_bytes": sb_json_path.stat().st_size,
        "scoreboard_json_sha256": sha256_file(sb_json_path),
        "scoreboard_json_entry_count": len(json_names),
        "w6_debate_index_path": str(W6_INDEX),
        "w6_debate_index_row_count": len(w6_names),
        "completed_disk_count": len(completed_disk_set),
        "missing_completed_disk_from_scoreboard_md": sorted(completed_disk_set - md_set),
        "extra_in_scoreboard_md_vs_disk": sorted(md_set - completed_disk_set),
        "drift_md_minus_json": len(md_names) - len(json_names),
        "missing_from_scoreboard_json": sorted(md_set - json_set),
        "extra_in_scoreboard_json": sorted(json_set - md_set),
        "drift_md_minus_w6_index": len(md_names) - len(w6_names),
        "missing_from_w6_index": sorted(md_set - w6_set),
        "extra_in_w6_index": sorted(w6_set - md_set),
    }


def extract_s2q_match_names(runner_path: Path) -> list[str]:
    text = runner_path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text, filename=str(runner_path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "pairs" and isinstance(node.value, ast.List):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Tuple) and elt.elts:
                            first = elt.elts[0]
                            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                                names.append(first.value)
    return names


def audit_stage2() -> dict[str, Any]:
    s2q_gpu_path = FQ / "STAGE2_QUIET_GPU_SUMMARY.json"
    s2_legacy_path = FQ / "STAGE2_FILTER_QUEST_SUMMARY.json"
    s2q_runner_path = FQ / "run_stage2_clean_skipnoisy_matches.py"
    matches_root = FF / "matches"

    s2q_gpu = json.loads(s2q_gpu_path.read_text(encoding="utf-8"))
    arms = s2q_gpu.get("arms", {})
    arm_checks: list[dict[str, Any]] = []
    for arm_name, info in arms.items():
        net_path = Path(info["net"])
        arm_checks.append(
            {
                "arm": arm_name,
                "net_exists": net_path.exists(),
                "ols_Q": info.get("ols_Q"),
                "syz_draw_med_cp": info.get("syz_draw_med_cp"),
                "syz_win_ok_pct": info.get("syz_win_ok_pct"),
            }
        )

    s2_legacy = json.loads(s2_legacy_path.read_text(encoding="utf-8"))
    legacy_matches = s2_legacy.get("matches", [])
    legacy_disk_drift: list[dict[str, Any]] = []
    for item in legacy_matches:
        mname = item["match"]
        reported_done = bool(item.get("done"))
        mdir = matches_root / mname
        has_summary = (mdir / "summary.json").exists()
        if has_summary != reported_done or mdir.exists():
            legacy_disk_drift.append(
                {
                    "match": mname,
                    "legacy_json_done": reported_done,
                    "dir_exists_on_disk": mdir.exists(),
                    "summary_json_exists": has_summary,
                }
            )

    declared_s2q = extract_s2q_match_names(s2q_runner_path)
    s2q_statuses: list[dict[str, Any]] = []
    completed_cnt = 0
    in_progress_cnt = 0
    not_started_cnt = 0
    for mname in declared_s2q:
        mdir = matches_root / mname
        sum_path = mdir / "summary.json"
        if sum_path.exists():
            try:
                sdata = json.loads(sum_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                in_progress_cnt += 1
                s2q_statuses.append(
                    {
                        "match": mname,
                        "status": "summary_corrupt",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            finished = _is_summary_completed(sdata)
            status = "completed" if finished else "summary_unfinished"
            if finished:
                completed_cnt += 1
            else:
                in_progress_cnt += 1
            s2q_statuses.append(
                {
                    "match": mname,
                    "status": status,
                    "games": sdata.get("games"),
                    "elo": sdata.get("elo"),
                    "elo_err": sdata.get("elo_err"),
                    "time_losses": sdata.get("time_losses"),
                    "illegal_moves": sdata.get("illegal_moves"),
                }
            )
        elif mdir.exists():
            in_progress_cnt += 1
            files = sorted(f.name for f in mdir.iterdir())
            s2q_statuses.append(
                {
                    "match": mname,
                    "status": "in_progress_no_summary",
                    "files_present": files,
                }
            )
        else:
            not_started_cnt += 1
            s2q_statuses.append(
                {
                    "match": mname,
                    "status": "not_started",
                }
            )

    ols_q_vals = [float(a["ols_Q"]) for a in arms.values() if "ols_Q" in a]
    syz_win_vals = [float(a["syz_win_ok_pct"]) for a in arms.values() if "syz_win_ok_pct" in a]

    return {
        "stage2_quiet_gpu_summary": {
            "path": str(s2q_gpu_path),
            "timestamp": s2q_gpu.get("timestamp"),
            "f1_quiet_kept": s2q_gpu.get("f1_quiet_kept"),
            "arms_count": len(arms),
            "all_nets_present": all(a["net_exists"] for a in arm_checks),
            "ols_Q_min": min(ols_q_vals) if ols_q_vals else None,
            "ols_Q_max": max(ols_q_vals) if ols_q_vals else None,
            "syz_win_ok_pct_min": min(syz_win_vals) if syz_win_vals else None,
            "syz_win_ok_pct_max": max(syz_win_vals) if syz_win_vals else None,
            "has_matches_block": "matches" in s2q_gpu,
            "arms": arm_checks,
        },
        "stage2_legacy_summary": {
            "path": str(s2_legacy_path),
            "timestamp": s2_legacy.get("timestamp"),
            "reported_arms_done": s2_legacy.get("arms_done"),
            "reported_arms_total": s2_legacy.get("arms_total"),
            "reported_matches_done": s2_legacy.get("matches_done"),
            "reported_matches_total": s2_legacy.get("matches_total"),
            "disk_drift_entries": legacy_disk_drift,
        },
        "s2q_declared_matches": {
            "runner_path": str(s2q_runner_path),
            "total_declared": len(declared_s2q),
            "completed": completed_cnt,
            "in_progress_no_summary": in_progress_cnt,
            "not_started": not_started_cnt,
            "opus_250k_confirmation_note": "Per OPUS_TO_NEON.md:3022, Stage-2 50k matches are filters only; any winning arm requires 250k confirmation.",
            "matches": s2q_statuses,
        },
    }


def scan_match_directories(root: Path, known_excluded: dict[str, str]) -> dict[str, Any]:
    if not root.exists():
        return {"exists": False, "path": str(root)}
    dirs = sorted([d for d in root.iterdir() if d.is_dir()], key=lambda p: p.name)
    incomplete: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []
    completed_dir_names: list[str] = []
    unfinished_summaries: list[str] = []
    corrupt_summaries: list[str] = []
    completed = 0
    for d in dirs:
        sp = d / "summary.json"
        if not sp.exists():
            is_known_excluded = d.name in known_excluded
            if is_known_excluded:
                classification = known_excluded[d.name]
            elif d.name.startswith("S2Q_"):
                classification = "active_in_progress"
            else:
                classification = "incomplete_no_summary"
            incomplete.append(
                {
                    "dir_name": d.name,
                    "path": str(d),
                    "classification": classification,
                    "is_known_excluded": is_known_excluded,
                    "files": sorted(f.name for f in d.iterdir()),
                }
            )
            continue
        try:
            sdata = json.loads(sp.read_text(encoding="utf-8"))
            if not isinstance(sdata, dict):
                raise ValueError("summary.json root is not a JSON object")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            corrupt_summaries.append(d.name)
            unfinished_summaries.append(d.name)
            anomalies.append(
                {
                    "dir_name": d.name,
                    "finished": False,
                    "corrupt_summary": True,
                    "error": f"{type(exc).__name__}: {exc}",
                    "time_losses": 0,
                    "illegal_moves": 0,
                }
            )
            continue
        completed += 1
        tl = int(sdata.get("time_losses", 0) or 0)
        il = int(sdata.get("illegal_moves", 0) or 0)
        fin = _is_summary_completed(sdata)
        if fin:
            completed_dir_names.append(d.name)
        else:
            unfinished_summaries.append(d.name)
        if not fin or tl > 0 or il > 0:
            anomalies.append(
                {
                    "dir_name": d.name,
                    "finished": fin,
                    "time_losses": tl,
                    "illegal_moves": il,
                }
            )
    return {
        "exists": True,
        "root": str(root),
        "total_subdirs": len(dirs),
        "completed_with_summary": completed,
        "completed_dir_names": completed_dir_names,
        "unfinished_summaries": unfinished_summaries,
        "corrupt_summaries": corrupt_summaries,
        "missing_summary_count": len(incomplete),
        "missing_summary_dirs": incomplete,
        "non_excluded_missing_dirs": [x["dir_name"] for x in incomplete if not x["is_known_excluded"]],
        "completed_anomalies": anomalies,
    }


def audit_r1_and_sprt() -> dict[str, Any]:
    r1_dir = FF / "gpu_runs" / "OPUS_R1_live768_skipnoisy"
    r1_runner = FF / "run_opus_r1_live768_skipnoisy.py"
    r1_files = sorted(f.name for f in r1_dir.iterdir()) if r1_dir.exists() else []
    r1_decl = None
    if (r1_dir / "declaration.json").exists():
        r1_decl = json.loads((r1_dir / "declaration.json").read_text(encoding="utf-8"))

    # Search for any R1-keep twin runner or GPU run dir
    twin_scripts = sorted(
        str(p)
        for p in FF.glob("*r1*")
        if p.is_file() and "keep" in p.name.lower()
    ) + sorted(
        str(p)
        for p in FF.glob("*R1*")
        if p.is_file() and "keep" in p.name.lower()
    )
    gpu_runs_dir = FF / "gpu_runs"
    twin_gpu_dir_objs = sorted(
        [
            d
            for d in gpu_runs_dir.iterdir()
            if d.is_dir() and ("r1" in d.name.lower() and "keep" in d.name.lower())
        ],
        key=lambda p: p.name,
    ) if gpu_runs_dir.exists() else []
    twin_gpu_dirs = [d.name for d in twin_gpu_dir_objs]
    twin_completed_dirs = [
        d.name
        for d in twin_gpu_dir_objs
        if (d / "cand.fnn3").exists()
    ]

    matches_dir = FF / "matches"
    r1_match_dir_objs = sorted(
        [
            d
            for d in matches_dir.iterdir()
            if d.is_dir() and ("opus_r1" in d.name.lower() or d.name.lower().startswith("r1_"))
        ],
        key=lambda p: p.name,
    ) if matches_dir.exists() else []
    r1_match_dirs = [d.name for d in r1_match_dir_objs]
    r1_completed_matches: list[dict[str, Any]] = []
    for md in r1_match_dir_objs:
        sp = md / "summary.json"
        if not sp.exists():
            continue
        try:
            sdata = json.loads(sp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(sdata, dict):
            continue
        fin = _is_summary_completed(sdata)
        tl = int(sdata.get("time_losses", 0) or 0)
        il = int(sdata.get("illegal_moves", 0) or 0)
        decl = sdata.get("declaration") if isinstance(sdata.get("declaration"), dict) else {}
        if not decl:
            for decl_path in sorted(md.glob("declaration*.json")):
                try:
                    parsed_decl = json.loads(decl_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if isinstance(parsed_decl, dict) and parsed_decl:
                    decl = parsed_decl
                    break

        nodes_raw = decl.get("nodes")
        try:
            nodes = int(nodes_raw) if nodes_raw is not None else None
        except (TypeError, ValueError):
            nodes = None
        tc = str(decl.get("tc") or "").strip() or None
        cand_net = str(decl.get("cand_net") or "").lower()
        base_net = str(decl.get("base_net") or "").lower()

        dname_l = md.name.lower()
        has_50k_name = bool(re.search(r"(?:^|_)50k(?:_|$)", dname_l))
        has_250k_name = bool(re.search(r"(?:^|_)250k(?:_|$)", dname_l))
        if tc is not None or (nodes is not None and nodes >= 250000):
            is_250k_or_clock = True
        elif nodes is not None and nodes < 250000:
            is_250k_or_clock = False
        elif has_50k_name:
            is_250k_or_clock = False
        else:
            is_250k_or_clock = has_250k_name

        def _refs_r1_skip(net_s: str) -> bool:
            return bool(net_s) and (("r1" in net_s and "skip" in net_s) or str(r1_dir).lower() in net_s)

        def _refs_r1_keep(net_s: str) -> bool:
            return bool(net_s) and (
                ("r1" in net_s and "keep" in net_s)
                or any(td.lower() in net_s for td in twin_gpu_dirs)
            )

        name_is_skip_vs_keep = "skip" in dname_l and "keep" in dname_l
        nets_is_skip_vs_keep = (
            (_refs_r1_skip(cand_net) and _refs_r1_keep(base_net))
            or (_refs_r1_keep(cand_net) and _refs_r1_skip(base_net))
        )
        is_skip_vs_keep = name_is_skip_vs_keep or nets_is_skip_vs_keep

        if fin and tl == 0 and il == 0 and is_250k_or_clock and is_skip_vs_keep:
            r1_completed_matches.append(
                {
                    "dir_name": md.name,
                    "games": sdata.get("games"),
                    "elo": sdata.get("elo"),
                    "elo_err": sdata.get("elo_err"),
                    "nodes": nodes,
                    "tc": tc,
                }
            )

    if twin_completed_dirs:
        twin_status = "complete"
    elif twin_scripts or twin_gpu_dirs:
        twin_status = "present"
    else:
        twin_status = "missing_not_started"

    sprt_runner = FF / "run_lmr_deeper_sprt.py"
    sprt_dirs = sorted(
        d.name
        for d in matches_dir.iterdir()
        if d.is_dir() and "SPRT_LmrDeeperShallower" in d.name
    ) if matches_dir.exists() else []
    sprt_details: list[dict[str, Any]] = []
    for sd in sprt_dirs:
        mdir = matches_dir / sd
        sp = mdir / "summary.json"
        if sp.exists():
            try:
                sdata = json.loads(sp.read_text(encoding="utf-8"))
                if not isinstance(sdata, dict):
                    raise ValueError("summary.json root is not a JSON object")
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                sprt_details.append(
                    {
                        "dir": sd,
                        "has_summary": True,
                        "finished": False,
                        "clean_completed": False,
                        "corrupt_summary": True,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            fin = _is_summary_completed(sdata)
            tl = int(sdata.get("time_losses", 0) or 0)
            il = int(sdata.get("illegal_moves", 0) or 0)
            sprt_details.append(
                {
                    "dir": sd,
                    "has_summary": True,
                    "finished": fin,
                    "clean_completed": fin and tl == 0 and il == 0,
                    "rc": sdata.get("rc"),
                    "verdict": sdata.get("verdict"),
                    "games": sdata.get("games"),
                    "elo": sdata.get("elo"),
                    "llr": sdata.get("llr"),
                    "time_losses": tl,
                    "illegal_moves": il,
                }
            )
        else:
            sprt_details.append({"dir": sd, "has_summary": False, "finished": False, "clean_completed": False, "files": sorted(f.name for f in mdir.iterdir())})

    if not sprt_details:
        sprt_status = "not_started"
    elif all(d["has_summary"] and d.get("clean_completed", d["finished"]) for d in sprt_details):
        sprt_status = "completed"
    elif any(d["has_summary"] for d in sprt_details):
        sprt_status = "in_progress"
    else:
        sprt_status = "in_progress_no_summary"

    cand_fnn3_exists = (r1_dir / "cand.fnn3").exists()
    eval_full_exists = (r1_dir / "eval_full.json").exists()
    r1_summary_exists = (r1_dir / "r1_summary.json").exists()

    return {
        "opus_r1_live768_skipnoisy": {
            "runner_exists": r1_runner.exists(),
            "runner_path": str(r1_runner),
            "out_dir": str(r1_dir),
            "out_dir_exists": r1_dir.exists(),
            "files_present": r1_files,
            "cand_fnn3_exists": cand_fnn3_exists,
            "eval_full_exists": eval_full_exists,
            "r1_summary_exists": r1_summary_exists,
            "status": "complete" if (cand_fnn3_exists and (r1_summary_exists or eval_full_exists)) else "training_in_progress",
            "declaration_written": r1_decl.get("written") if r1_decl else None,
        },
        "opus_r1_keep_twin": {
            "twin_scripts_found": sorted(set(twin_scripts)),
            "twin_gpu_dirs_found": twin_gpu_dirs,
            "twin_completed_dirs": twin_completed_dirs,
            "twin_cand_fnn3_exists": bool(twin_completed_dirs),
            "r1_match_dirs_found": r1_match_dirs,
            "r1_completed_matches": r1_completed_matches,
            "status": twin_status,
            "required_protocol": "OPUS_TO_NEON.md:3016-3020 requires same-runner --keep-noisy twin, then R1-skip vs R1-keep at 250k (1,000g); if positive, 2nd seed + R1-skip vs r0067 at 250k and 6+0.06 (concurrency<=7).",
        },
        "lmr_deeper_shallower_sprt": {
            "runner_exists": sprt_runner.exists(),
            "runner_path": str(sprt_runner),
            "matching_dirs": sprt_dirs,
            "status": sprt_status,
            "details": sprt_details,
        },
    }


def run_w6_stager_checks() -> dict[str, Any]:
    if not W6_STAGER.exists():
        return {"exists": False, "path": str(W6_STAGER)}
    env = dict(os.environ)
    env["CUDA_VISIBLE_DEVICES"] = ""

    dry = subprocess.run(
        [sys.executable, "-B", str(W6_STAGER), "--dry-run"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    vdi = subprocess.run(
        [sys.executable, "-B", str(W6_STAGER), "--verify-debate-index"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    vdi_strict = subprocess.run(
        [sys.executable, "-B", str(W6_STAGER), "--verify-debate-index", "--strict-living"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    freeze_line = ""
    dry_summary_line = ""
    for ln in dry.stdout.splitlines():
        if ln.startswith("FREEZE_CHECK:"):
            freeze_line = ln.strip()
        elif ln.startswith("DRY_RUN_SUMMARY:"):
            dry_summary_line = ln.strip()

    vdi_summary_line = ""
    vdi_drift_lines: list[str] = []
    for ln in (vdi.stdout + "\n" + vdi.stderr).splitlines():
        if ln.startswith("VERIFY_DEBATE_INDEX:"):
            vdi_summary_line = ln.strip()
        elif ln.startswith("[LIVING_DRIFT]"):
            vdi_drift_lines.append(ln.strip())

    # Check post-W6 / Wave 7 artifacts not in W6 217-file manifest
    stager_src = W6_STAGER.read_text(encoding="utf-8", errors="replace")
    post_w6_candidates = [
        str(FF / "CC0_NOISY_VS_QUIET_FORENSIC.json"),
        str(FF / "G3AB_DISTILL_REGIME_CHECK.json"),
        str(FF / "CLEAN_IDLE_SPEED_2BUILDS.json"),
        str(FF / "CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json"),
        str(FQ / "STAGE2_QUIET_GPU_SUMMARY.json"),
        str(FQ / "run_stage2_clean_skipnoisy_gpu.py"),
        str(FQ / "run_stage2_clean_skipnoisy_matches.py"),
        str(FF / "run_opus_r1_live768_skipnoisy.py"),
        str(FF / "run_lmr_deeper_sprt.py"),
        str(FF / "bench_serverday_4archs_pgo.py"),
        str(FF / "matches" / "G3_FULL25_PGO_vs_live_r0067_2000g_6p006" / "summary.json"),
        str(FF / "matches" / "OPUS_r0202_vs_r0067_1000g_250k" / "summary.json"),
    ]
    missing_from_w6_manifest = []
    for cand in post_w6_candidates:
        if Path(cand).exists():
            escaped = cand.replace("\\", "\\\\")
            if cand not in stager_src and escaped not in stager_src:
                missing_from_w6_manifest.append(cand)

    w7_root = FF / "teamwork_wave7"
    w7_deliverables = sorted(
        str(p)
        for p in w7_root.rglob("*")
        if p.is_file()
    ) if w7_root.exists() else []

    return {
        "stager_path": str(W6_STAGER),
        "live_delivery_dest": str(LIVE_DELIVERY_DEST),
        "live_delivery_dest_exists": LIVE_DELIVERY_DEST.exists(),
        "dry_run": {
            "returncode": dry.returncode,
            "freeze_check": freeze_line,
            "summary": dry_summary_line,
        },
        "verify_debate_index": {
            "returncode": vdi.returncode,
            "summary": vdi_summary_line,
            "living_drift_lines": vdi_drift_lines,
        },
        "verify_debate_index_strict_living": {
            "returncode": vdi_strict.returncode,
            "blocks_strict_freeze": vdi_strict.returncode != 0,
        },
        "post_w6_verified_artifacts_not_in_w6_manifest": missing_from_w6_manifest,
        "wave7_files_not_in_w6_manifest": w7_deliverables,
    }


def build_report() -> dict[str, Any]:
    ff_match_scan = scan_match_directories(
        FF / "matches",
        known_excluded={
            "SF32_qs_see1_futility_pruning_600g_50k": "incomplete_explicitly_excluded_in_w6",
            "SF5b_corrhist_plus_minor": "incomplete_explicitly_excluded_in_w6",
            "G4a_losspow25_vs_G3a_losspow20_1000g_50k": "incomplete_superseded_keepnoisy_arm",
        },
    )
    fq_match_scan = scan_match_directories(
        FQ / "matches",
        known_excluded={
            "M_SWA_ctrl_swa24_40_vs_ctrl_n50k": "quarantined_v3_model_check_3.02cp_gt_3cp",
        },
    )
    completed_disk_names = sorted(
        set(ff_match_scan.get("completed_dir_names", []))
        | set(fq_match_scan.get("completed_dir_names", []))
    )
    sb_audit = audit_scoreboards(completed_disk_names=completed_disk_names)
    handoff_audit = audit_handoff_md(
        FQ / "HANDOFF_12H_DATA_QUALITY.md",
        live_sb_count=sb_audit["scoreboard_md_row_count"],
    )
    stage2_audit = audit_stage2()
    r1_sprt_audit = audit_r1_and_sprt()
    w6_audit = run_w6_stager_checks()

    blocking_items: list[dict[str, Any]] = []

    if handoff_audit.get("marker_count", 0) > 0:
        blocking_items.append(
            {
                "id": "HANDOFF_PENDING_MARKERS",
                "severity": "BLOCKER",
                "summary": f"HANDOFF_12H_DATA_QUALITY.md contains {handoff_audit['marker_count']} open [PENDING*]/[TESTING*] markers across lines {[h['line'] for h in handoff_audit['marker_hits']]}.",
                "stage_teamwork_delivery_w6_blocks_live": True,
            }
        )
    if handoff_audit.get("stale_findings_count", 0) > 0:
        blocking_items.append(
            {
                "id": "HANDOFF_STALE_TEXT_AND_COUNTS",
                "severity": "BLOCKER",
                "summary": f"HANDOFF_12H_DATA_QUALITY.md has {handoff_audit['stale_findings_count']} stale ledger/status statements (e.g. '43-match ledger', '51 completed matches' vs live {sb_audit['scoreboard_md_row_count']}, stale [PENDING] row for completed G3 250k/6+0.06).",
            }
        )
    scoreboard_drift = (
        sb_audit["drift_md_minus_json"] != 0
        or sb_audit["drift_md_minus_w6_index"] != 0
        or bool(sb_audit["missing_from_scoreboard_json"])
        or bool(sb_audit["extra_in_scoreboard_json"])
        or bool(sb_audit["missing_from_w6_index"])
        or bool(sb_audit["extra_in_w6_index"])
        or bool(sb_audit["missing_completed_disk_from_scoreboard_md"])
        or bool(sb_audit["extra_in_scoreboard_md_vs_disk"])
        or (
            sb_audit["scoreboard_md_declared_total"] is not None
            and not sb_audit["scoreboard_md_header_matches_rows"]
        )
    )
    if scoreboard_drift:
        blocking_items.append(
            {
                "id": "SCOREBOARD_DRIFT",
                "severity": "BLOCKER",
                "summary": (
                    f"Scoreboard drift: disk_completed={sb_audit['completed_disk_count']}, "
                    f"ALL_MATCHES_SCOREBOARD.md={sb_audit['scoreboard_md_row_count']} "
                    f"(missing_from_md={len(sb_audit['missing_completed_disk_from_scoreboard_md'])}: {sb_audit['missing_completed_disk_from_scoreboard_md']}, "
                    f"extra_vs_disk={len(sb_audit['extra_in_scoreboard_md_vs_disk'])}: {sb_audit['extra_in_scoreboard_md_vs_disk']}), "
                    f"ALL_MATCHES_SCOREBOARD.json={sb_audit['scoreboard_json_entry_count']} "
                    f"(missing={len(sb_audit['missing_from_scoreboard_json'])}, extra={len(sb_audit['extra_in_scoreboard_json'])}), "
                    f"DEBATE_EVIDENCE_INDEX_W6.md={sb_audit['w6_debate_index_row_count']} "
                    f"(missing={len(sb_audit['missing_from_w6_index'])}, extra={len(sb_audit['extra_in_w6_index'])})."
                ),
            }
        )
    s2q = stage2_audit["s2q_declared_matches"]
    if s2q["completed"] < s2q["total_declared"]:
        blocking_items.append(
            {
                "id": "STAGE2_S2Q_MATCHES_INCOMPLETE",
                "severity": "BLOCKER",
                "summary": (
                    f"Clean quiet Stage-2 matches: {s2q['completed']}/{s2q['total_declared']} completed "
                    f"({s2q['in_progress_no_summary']} in progress, {s2q['not_started']} not started), "
                    "plus any 50k winner requires 250k confirmation."
                ),
            }
        )
    if stage2_audit["stage2_legacy_summary"]["disk_drift_entries"]:
        blocking_items.append(
            {
                "id": "STAGE2_LEGACY_SUMMARY_STALE",
                "severity": "WARNING_STALE_SNAPSHOT",
                "summary": "STAGE2_FILTER_QUEST_SUMMARY.json still reports matches_done=0/12 despite 2 completed matches (G3b vs G3a eq-raw/eq-ret) and 9 superseded quiet Stage-2 arms.",
            }
        )
    ff_missing = ff_match_scan.get("missing_summary_dirs", [])
    fq_missing = fq_match_scan.get("missing_summary_dirs", [])
    non_excluded_incomplete_ff = [d for d in ff_missing if not d.get("is_known_excluded", False)]
    non_excluded_incomplete_fq = [d for d in fq_missing if not d.get("is_known_excluded", False)]
    ff_anomalies = ff_match_scan.get("completed_anomalies", [])
    fq_anomalies = fq_match_scan.get("completed_anomalies", [])
    has_incomplete_or_anomaly_blocker = bool(
        non_excluded_incomplete_ff
        or non_excluded_incomplete_fq
        or ff_anomalies
        or fq_anomalies
    )
    if ff_missing or fq_missing or ff_anomalies or fq_anomalies:
        blocking_items.append(
            {
                "id": "INCOMPLETE_MATCH_DIRS",
                "severity": "BLOCKER" if has_incomplete_or_anomaly_blocker else "INFO_EXCLUDED_ONLY",
                "summary": (
                    f"forge_fixes/matches has {ff_match_scan.get('missing_summary_count', 0)} dirs without summary.json "
                    f"({[d['dir_name'] for d in ff_missing]}; non_excluded={[d['dir_name'] for d in non_excluded_incomplete_ff]}), "
                    f"anomalies={ff_anomalies}; "
                    f"filter_quest/matches has {fq_match_scan.get('missing_summary_count', 0)} "
                    f"({[d['dir_name'] for d in fq_missing]}; non_excluded={[d['dir_name'] for d in non_excluded_incomplete_fq]}), "
                    f"anomalies={fq_anomalies}."
                ),
            }
        )
    r1_skip = r1_sprt_audit["opus_r1_live768_skipnoisy"]
    r1_twin = r1_sprt_audit["opus_r1_keep_twin"]
    r1_skip_ok = r1_skip["status"] == "complete"
    r1_twin_ok = r1_twin["status"] == "complete"
    r1_match_ok = bool(r1_twin.get("r1_completed_matches"))
    if not (r1_skip_ok and r1_twin_ok and r1_match_ok):
        missing_parts: list[str] = []
        if not r1_skip_ok:
            missing_parts.append(f"OPUS_R1_live768_skipnoisy status={r1_skip['status']}")
        if not r1_twin_ok:
            missing_parts.append(f"opus_r1_keep_twin status={r1_twin['status']} (same-runner --keep-noisy twin with cand.fnn3 required)")
        if not r1_match_ok:
            missing_parts.append(f"completed R1-skip vs R1-keep 250k decision match missing (found_dirs={r1_twin.get('r1_match_dirs_found', [])})")
        blocking_items.append(
            {
                "id": "OPUS_R1_TRAINING_AND_TWIN_OPEN",
                "severity": "BLOCKER",
                "summary": "; ".join(missing_parts) + ".",
            }
        )
    if r1_sprt_audit["lmr_deeper_shallower_sprt"]["status"] != "completed":
        blocking_items.append(
            {
                "id": "LMR_DEEPER_SPRT_OPEN",
                "severity": "BLOCKER",
                "summary": f"LmrDeeperShallower SPRT [0, 5] status is '{r1_sprt_audit['lmr_deeper_shallower_sprt']['status']}'.",
            }
        )
    if w6_audit.get("verify_debate_index_strict_living", {}).get("blocks_strict_freeze"):
        blocking_items.append(
            {
                "id": "W6_STAGER_AND_MANIFEST_GAPS",
                "severity": "BLOCKER",
                "summary": (
                    f"stage_teamwork_delivery_w6.py --verify-debate-index --strict-living fails RC={w6_audit['verify_debate_index_strict_living']['returncode']}; "
                    f"{len(w6_audit.get('post_w6_verified_artifacts_not_in_w6_manifest', []))} post-W6 verified artifacts and "
                    f"{len(w6_audit.get('wave7_files_not_in_w6_manifest', []))} Wave 7 file(s) are outside the W6 217-file manifest."
                ),
            }
        )

    open_debate_gates = [
        "1. Live-loop placement vs Server-Day 2.0B deferral (G3_FULL25_PGO -0.35 Elo -> V3P deferred; parity 7/8 & R1 live 768w skip-vs-keep decide interim live-loop data fix).",
        "2. Tier-2 filter policy (--skip-fqs-noisy mandatory for V3P; R1 skip vs R1-keep twin on 768w pending; 10 S2Q_* Stage-2 quiet matches -> winners to 250k).",
        "3. Server-Day net width & king buckets (1024w/kb16 at 2.941M NPS [-0.6% vs kb8] vs 1024w/kb8 vs 1536w/kb8 at 2.665M NPS on 2.0B quiet-filtered positions).",
        "4. Search/TM 1-by-1 placement stack (LmrDeeperShallower SPRT [0, 5], SF38 vs SF39 mutual exclusion, Big Tune 45-option SPSA via POST_G3_SPSA_RECIPE.md).",
        "5. Owner-gated escalation (63.43% / 503 of 793 G3_FULL25_e40 SF19 severe errors are quiet, 73.33% persist at 400n, 40.0% resolved at 16k: cross-arch self-play / random_multi_pv vs external data).",
    ]

    freeze_ready = not any(b["severity"] == "BLOCKER" for b in blocking_items)

    return {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "freeze_ready": freeze_ready,
        "live_delivery_ready": freeze_ready and (w6_audit.get("dry_run", {}).get("returncode") == 0),
        "blocking_count": sum(1 for b in blocking_items if b["severity"] == "BLOCKER"),
        "blocking_items": blocking_items,
        "handoff_audit": handoff_audit,
        "scoreboard_audit": sb_audit,
        "stage2_audit": stage2_audit,
        "match_dir_scan": {
            "forge_fixes_matches": ff_match_scan,
            "filter_quest_matches": fq_match_scan,
        },
        "opus_r1_and_sprt": r1_sprt_audit,
        "w6_stager_audit": w6_audit,
        "open_debate_gates": open_debate_gates,
    }


def main() -> int:
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    default_out = Path(__file__).resolve().parent / "freeze_readiness_w7.json"
    ap = argparse.ArgumentParser(description="Wave 7 read-only freeze-readiness & live-delivery pre-flight audit.")
    ap.add_argument("--out", type=Path, default=default_out, help="Output JSON path (default: freeze_readiness_w7.json alongside script).")
    ap.add_argument("--json", action="store_true", help="Print full JSON to stdout in addition to writing --out.")
    ap.add_argument("--fail-on-unfrozen", action="store_true", help="Exit RC=1 when freeze_ready is false.")
    args = ap.parse_args()

    report = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        status = "READY" if report["freeze_ready"] else "NOT_READY"
        print(f"FREEZE_READINESS_W7: {status} | blockers={report['blocking_count']} | out={args.out}")
        for b in report["blocking_items"]:
            print(f"  - [{b['severity']}] {b['id']}: {b['summary']}")

    if args.fail_on_unfrozen and not report["freeze_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
