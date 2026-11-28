"""Verify live SHA-256s, git apply --check, sequential combined stack apply, and pairwise
orthogonality matrix for Round 12-14 (SF34-SF40), SF17+SF18 (SF37 composition), and
V3P_pairwise_psqt_fused_v3.patch against C:\\nnue-lab\\forge\\r15dsg.

All mutable git apply tests run on isolated temporary copies under:
  C:\\Users\\Administrator\\.gemini\\antigravity\\scratch\\teamwork_tmp\\381561d5-1d53-45e6-8dc4-a66b94b99e74
and are cleaned up unconditionally in finally:. C:\\nnue-lab\\forge\\r15dsg is NEVER modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
SRC = LAB / "forge" / "r15dsg"
FIX = LAB / "neon" / "forge_fixes"
PATCHES_DIR = FIX / "patches"
BUILDS_DIR = FIX / "builds"
DEFAULT_OUT = Path(__file__).resolve().parent / "round12_14_orthogonality.json"
TEMP_PARENT = Path(
    r"C:\Users\Administrator\.gemini\antigravity\scratch\teamwork_tmp\381561d5-1d53-45e6-8dc4-a66b94b99e74"
)

PATCH_SPECS: dict[str, Path] = {
    "V3P": PATCHES_DIR / "V3P_pairwise_psqt_fused_v3.patch",
    "SF34": PATCHES_DIR / "SF34_tactical_cutoff_quiet_malus_and_prior_refute.patch",
    "SF35": PATCHES_DIR / "SF35_razoring_d3_quadratic_and_nmp_minply.patch",
    "SF36": PATCHES_DIR / "SF36_threat_quiet_move_ordering.patch",
    "SF38": PATCHES_DIR / "SF38_corrhist_major.patch",
    "SF39": PATCHES_DIR / "SF39_corrhist_minor_plus_major.patch",
    "SF40": PATCHES_DIR / "SF40_tt_recency_pv_admit_and_pv_conthist.patch",
    "SF17": PATCHES_DIR / "SF17_tm_bestmove_avg_eval.patch",
    "SF18": PATCHES_DIR / "SF18_tm_ply_curve.patch",
}

SF37_EXE = BUILDS_DIR / "SF37_tm_combined_SF17_plus_SF18.exe"
PAIRWISE_KEYS = ["V3P", "SF34", "SF35", "SF36", "SF38", "SF39", "SF40"]
EXPECTED_CONFLICTS = {("SF38", "SF39"), ("SF39", "SF38")}

HUNK_RE = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def verify_r15dsg_baseline() -> dict:
    manifest_path = SRC / "SOURCE_INPUTS.sha256"
    expected_map: dict[str, str] = {}
    for raw in manifest_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            digest, rel = parts[0].lower(), parts[1].strip().lstrip("*").replace("\\", "/")
            expected_map[rel] = digest

    target_files = [
        "include/forge/search.hpp",
        "src/search.cpp",
        "include/forge/nnue_v3.hpp",
        "src/nnue_v3.cpp",
        "src/uci.cpp",
    ]
    entries = {}
    all_ok = True
    for rel in target_files:
        fp = SRC / rel
        live_sha = sha256_file(fp)
        exp_sha = expected_map.get(rel)
        matched = exp_sha is not None and live_sha == exp_sha
        if not matched:
            all_ok = False
        entries[rel] = {
            "path": str(fp),
            "bytes": fp.stat().st_size,
            "lines": line_count(fp),
            "expected_sha256": exp_sha,
            "live_sha256": live_sha,
            "match": matched,
        }
    return {
        "manifest_path": str(manifest_path),
        "manifest_entries": len(expected_map),
        "all_target_files_match": all_ok,
        "files": entries,
    }


def parse_patch_hunks(patch_path: Path) -> dict[str, list[dict]]:
    per_file: dict[str, list[dict]] = {}
    cur_file: str | None = None
    for raw in patch_path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("+++ "):
            tok = raw[4:].strip().split("\t", 1)[0]
            if tok.startswith("b/"):
                tok = tok[2:]
            cur_file = tok
            per_file.setdefault(cur_file, [])
        elif raw.startswith("@@ ") and cur_file is not None:
            m = HUNK_RE.match(raw)
            if m:
                old_s = int(m.group(1))
                old_c = int(m.group(2)) if m.group(2) is not None else 1
                new_s = int(m.group(3))
                new_c = int(m.group(4)) if m.group(4) is not None else 1
                old_e = old_s + max(old_c, 1) - 1
                per_file[cur_file].append(
                    {
                        "header": raw,
                        "old_start": old_s,
                        "old_count": old_c,
                        "old_end": old_e,
                        "new_start": new_s,
                        "new_count": new_c,
                    }
                )
    return per_file


def compute_overlap_matrix(parsed: dict[str, dict[str, list[dict]]]) -> dict:
    keys = list(parsed.keys())
    matrix: dict[str, dict[str, dict]] = {}
    for a in keys:
        matrix[a] = {}
        files_a = set(parsed[a].keys())
        for b in keys:
            if a == b:
                continue
            files_b = set(parsed[b].keys())
            shared_files = sorted(files_a & files_b)
            hunk_overlaps = []
            min_gap_by_file = {}
            for fn in shared_files:
                gaps = []
                for ha in parsed[a][fn]:
                    for hb in parsed[b][fn]:
                        if ha["old_start"] <= hb["old_end"] and hb["old_start"] <= ha["old_end"]:
                            hunk_overlaps.append(
                                {
                                    "file": fn,
                                    "hunk_a": ha["header"],
                                    "hunk_b": hb["header"],
                                    "overlap_lines": [
                                        max(ha["old_start"], hb["old_start"]),
                                        min(ha["old_end"], hb["old_end"]),
                                    ],
                                }
                            )
                            gaps.append(0)
                        else:
                            gap = (
                                hb["old_start"] - ha["old_end"]
                                if ha["old_end"] < hb["old_start"]
                                else ha["old_start"] - hb["old_end"]
                            )
                            gaps.append(gap)
                if gaps:
                    min_gap_by_file[fn] = min(gaps)
            matrix[a][b] = {
                "file_disjoint": len(shared_files) == 0,
                "shared_files": shared_files,
                "hunk_context_overlaps": hunk_overlaps,
                "min_line_gap_by_file": min_gap_by_file,
            }
    return matrix


def run_git_apply(repo_dir: Path, patch_path: Path, check_only: bool) -> dict:
    cmd = ["git", "-C", str(repo_dir), "apply"]
    if check_only:
        cmd.append("--check")
    cmd.append(str(patch_path))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "cmd": " ".join(cmd),
        "rc": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    out_path = Path(args.out)

    baseline = verify_r15dsg_baseline()

    artifacts: dict[str, dict] = {}
    parsed_hunks: dict[str, dict[str, list[dict]]] = {}
    standalone_checks: dict[str, dict] = {}

    for key, p in PATCH_SPECS.items():
        if not p.exists():
            raise FileNotFoundError(f"Missing patch: {p}")
        artifacts[key] = {
            "path": str(p),
            "bytes": p.stat().st_size,
            "lines": line_count(p),
            "sha256": sha256_file(p),
        }
        parsed_hunks[key] = parse_patch_hunks(p)
        standalone_checks[key] = run_git_apply(SRC, p, check_only=True)

    sf37_patches = sorted(str(x) for x in PATCHES_DIR.glob("*SF37*"))
    sf37_gates = sorted(str(x) for x in FIX.rglob("*SF37*gate*"))
    sf37_info = {
        "standalone_patch_exists": len(sf37_patches) > 0,
        "standalone_patch_matches": sf37_patches,
        "standalone_gate_matches": sf37_gates,
        "exe_path": str(SF37_EXE),
        "exe_exists": SF37_EXE.exists(),
        "exe_bytes": SF37_EXE.stat().st_size if SF37_EXE.exists() else 0,
        "exe_sha256": sha256_file(SF37_EXE) if SF37_EXE.exists() else None,
        "composition": "SF17_tm_bestmove_avg_eval.patch + SF18_tm_ply_curve.patch (NO standalone SF37*.patch exists)",
    }

    overlap_matrix = compute_overlap_matrix(parsed_hunks)
    v3p_disjoint_all = all(
        overlap_matrix["V3P"][k]["file_disjoint"]
        for k in ["SF34", "SF35", "SF36", "SF38", "SF39", "SF40", "SF17", "SF18"]
    )

    run_id = f"r12_14_ortho_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    work_root = TEMP_PARENT / run_id
    stacks: dict[str, dict] = {}
    pairwise_results: dict[str, dict[str, dict]] = {a: {} for a in PAIRWISE_KEYS}

    try:
        work_root.mkdir(parents=True, exist_ok=False)

        stack_defs = {
            "stack_sf38": ["V3P", "SF34", "SF35", "SF36", "SF38", "SF40"],
            "stack_sf39": ["V3P", "SF34", "SF35", "SF36", "SF39", "SF40"],
            "stack_sf38_with_tm": ["V3P", "SF17", "SF18", "SF34", "SF35", "SF36", "SF38", "SF40"],
        }
        for sname, order in stack_defs.items():
            sdir = work_root / sname
            shutil.copytree(SRC, sdir)
            steps = []
            passed = True
            for key in order:
                res = run_git_apply(sdir, PATCH_SPECS[key], check_only=False)
                res["patch"] = key
                steps.append(res)
                if res["rc"] != 0:
                    passed = False
                    break
            stacks[sname] = {
                "order": order,
                "passed": passed,
                "steps": steps,
            }
            shutil.rmtree(sdir)

        for a in PAIRWISE_KEYS:
            for b in PAIRWISE_KEYS:
                if a == b:
                    continue
                pdir = work_root / f"pair_{a}_{b}"
                shutil.copytree(SRC, pdir)
                res_a = run_git_apply(pdir, PATCH_SPECS[a], check_only=False)
                res_b = run_git_apply(pdir, PATCH_SPECS[b], check_only=False)
                shutil.rmtree(pdir)
                expect_conflict = (a, b) in EXPECTED_CONFLICTS
                ok = (res_a["rc"] == 0) and ((res_b["rc"] != 0) if expect_conflict else (res_b["rc"] == 0))
                pairwise_results[a][b] = {
                    "first": a,
                    "second": b,
                    "first_rc": res_a["rc"],
                    "second_rc": res_b["rc"],
                    "expected_conflict": expect_conflict,
                    "actual_conflict": res_b["rc"] != 0,
                    "second_stderr": res_b["stderr"],
                    "passed": ok,
                }
    finally:
        if work_root.exists():
            shutil.rmtree(work_root, ignore_errors=True)
        if TEMP_PARENT.exists() and not any(TEMP_PARENT.iterdir()):
            TEMP_PARENT.rmdir()

    standalone_all_ok = all(v["rc"] == 0 for v in standalone_checks.values())
    stacks_all_ok = all(v["passed"] for v in stacks.values())
    pairwise_all_ok = all(
        pairwise_results[a][b]["passed"]
        for a in PAIRWISE_KEYS
        for b in PAIRWISE_KEYS
        if a != b
    )
    sf37_ok = (
        (not sf37_info["standalone_patch_exists"])
        and sf37_info["exe_exists"]
        and (sf37_info["exe_sha256"] is not None)
    )

    overall_pass = (
        baseline["all_target_files_match"]
        and standalone_all_ok
        and v3p_disjoint_all
        and stacks_all_ok
        and pairwise_all_ok
        and sf37_ok
    )

    report = {
        "schema": "round12_14_orthogonality_v1",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overall_pass": overall_pass,
        "checks": {
            "baseline_r15dsg_sha256_match": baseline["all_target_files_match"],
            "standalone_git_apply_check_all_rc0": standalone_all_ok,
            "v3p_100pct_file_disjoint_with_all_sf": v3p_disjoint_all,
            "sequential_stacks_all_pass": stacks_all_ok,
            "pairwise_matrix_all_pass": pairwise_all_ok,
            "sf37_provenance_verified": sf37_ok,
        },
        "baseline_r15dsg": baseline,
        "artifacts": artifacts,
        "sf37_provenance": sf37_info,
        "standalone_apply_check": standalone_checks,
        "parsed_patch_hunks": parsed_hunks,
        "overlap_matrix": overlap_matrix,
        "sequential_stacks": stacks,
        "pairwise_sequential_apply_matrix": pairwise_results,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"OVERALL_PASS={overall_pass} standalone={standalone_all_ok} "
        f"v3p_disjoint={v3p_disjoint_all} stacks={stacks_all_ok} "
        f"pairwise={pairwise_all_ok} sf37={sf37_ok}"
    )
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
