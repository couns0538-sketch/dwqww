"""Clean GPU+CPU-Idle Per-Patch NPS Isolation Benchmark (Opus 04:48 PC Point 3).

Measures the exact clean idle bench-15 NPS (5x interleaved) of each individual patch from
FORGE_OWNER_BUNDLE_PGO.exe on r0067 + all 45 live v3_uci_options (each built with identical
Clang 23.1.5 ThinLTO + PGO profiled on r0067 + all 45 live opts!):
  1. live_pgo_r0067            (v3-r15dsg-sp-clang/forge.exe, baseline)
  2. live_pgo_LmrDeeper        (same live exe + LmrDeeperShallower=true, zero C++ diff)
  3. SF13_alone_pgo            (SF13_qs_evasion_pruning.patch alone)
  4. SF8_alone_pgo             (SF8_conthist_6ply.patch alone)
  5. W2_proto_1_alone_pgo      (proto_1_corrhist_minor.patch alone)
  6. V3Pv3_alone_r0067_pgo     (V3P_pairwise_psqt_fused_v3.patch alone, PGO-profiled on r0067!)
  7. FORGE_OWNER_BUNDLE_PGO    (full 4-patch dual-net PGO bundle + LmrDeeperShallower=true)

MUST ONLY RUN BENCHMARKING WHEN GPU AND CPU ARE 100% IDLE (sets neon/CLOCK_MATCH_RUNNING).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import statistics
import subprocess
import time
import tomllib
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
SRC_BASE = LAB / "forge/r15dsg"
FIX = LAB / "neon/forge_fixes"
PY = str(LAB / "venv/Scripts/python.exe")
LIVE_PGO_EXE = LAB / "runs/forge/engines/v3-r15dsg-sp-clang/forge.exe"
BUNDLE_EXE = FIX / "builds/FORGE_OWNER_BUNDLE_PGO.exe"
R0067 = LAB / "runs/forge/r0067/train/cand.fnn3"
OUT_JSON = FIX / "CLEAN_IDLE_PER_PATCH_NPS.json"

SINGLE_PATCHES = [
    ("SF13_alone_pgo", FIX / "patches/SF13_qs_evasion_pruning.patch"),
    ("SF8_alone_pgo", FIX / "patches/SF8_conthist_6ply.patch"),
    ("W2_proto_1_alone_pgo", FIX / "teamwork_wave2/streamA_search/patches/proto_1_corrhist_minor.patch"),
    ("V3Pv3_alone_r0067_pgo", FIX / "patches/V3P_pairwise_psqt_fused_v3.patch"),
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def load_v3_opts() -> dict:
    cfg = tomllib.loads((LAB / "pipeline/config.forge.toml").read_text(encoding="utf-8"))
    return dict(cfg["engine"]["v3_uci_options"])


def build_single_pgo(name: str, patch_path: Path, jobs: int = 8) -> Path:
    out_exe = FIX / f"builds/{name}.exe"
    if out_exe.exists():
        return out_exe
    work = FIX / f"_perpatch_{name}"
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(SRC_BASE, work)
    try:
        subprocess.run(["git", "-C", str(work), "apply", str(patch_path)], check=True, capture_output=True, text=True)
        subprocess.run([
            PY, str(FIX / "build_fast.py"),
            "--src", str(work), "--out", str(out_exe),
            "--pgo", "--pgo-net", str(R0067), "--jobs", str(jobs),
        ], check=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return out_exe


def bench_once(exe: Path, net: Path, opts: dict, depth: int = 15) -> dict:
    lines = [
        "uci",
        f"setoption name NNUEArchFile value {str(net).replace(chr(92), '/')}",
        "setoption name NNUEArch value true",
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        "setoption name OwnBook value false",
        "setoption name MateAlphaGuard value true",
    ]
    for k, v in opts.items():
        sv = "true" if v is True else ("false" if v is False else str(v))
        lines.append(f"setoption name {k} value {sv}")
    lines += ["isready", f"bench {depth}", "quit"]
    r = subprocess.run([str(exe)], input="\n".join(lines) + "\n", capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, f"bench {depth} failed on {exe}: {r.stderr}"
    for ln in r.stdout.splitlines():
        m = re.search(rf"info string bench depth {depth} nodes (\d+) time (\d+) nps (\d+)", ln)
        if m:
            return {"nodes": int(m.group(1)), "time_ms": int(m.group(2)), "nps": int(m.group(3))}
    raise RuntimeError(f"bench {depth} missing for {exe}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--depth", type=int, default=15)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--build-only", action="store_true")
    args = ap.parse_args()

    exes: dict[str, Path] = {"live_pgo_r0067": LIVE_PGO_EXE, "live_pgo_LmrDeeper": LIVE_PGO_EXE}
    for nm, pp in SINGLE_PATCHES:
        exes[nm] = build_single_pgo(nm, pp, jobs=args.jobs)
    if BUNDLE_EXE.exists():
        exes["FORGE_OWNER_BUNDLE_PGO"] = BUNDLE_EXE

    if args.build_only:
        print("BUILT_ALL_PER_PATCH_PGO:", {k: str(v) for k, v in exes.items()})
        return 0

    v3_opts = load_v3_opts()
    deeper_opts = dict(v3_opts, LmrDeeperShallower=True)
    order = list(exes.keys())
    runs: dict[str, list[dict]] = {k: [] for k in order}
    clock_flag = LAB / "neon/CLOCK_MATCH_RUNNING"
    try:
        clock_flag.write_text("Per-patch clean idle NPS benchmark\n", encoding="utf-8")
        for r_idx in range(args.rounds):
            seq = order if (r_idx % 2 == 0) else list(reversed(order))
            for k in seq:
                opts = deeper_opts if k in ("live_pgo_LmrDeeper", "FORGE_OWNER_BUNDLE_PGO") else v3_opts
                runs[k].append(bench_once(exes[k], R0067, opts, depth=args.depth))
    finally:
        if clock_flag.exists():
            clock_flag.unlink()

    base_nps = statistics.median(x["nps"] for x in runs["live_pgo_r0067"])
    summary = {}
    for k in order:
        mn = statistics.median(x["nps"] for x in runs[k])
        mt = statistics.median(x["time_ms"] for x in runs[k])
        summary[k] = {
            "exe": str(exes[k]),
            "exe_sha256": sha256_file(exes[k]),
            "nodes": runs[k][0]["nodes"],
            "median_ms": mt,
            "median_nps": mn,
            "ratio_vs_live_pgo": round(mn / max(1.0, base_nps), 4),
            "pct_delta_vs_live_pgo": round((mn / max(1.0, base_nps) - 1.0) * 100.0, 2),
        }
    out = {
        "written": time.strftime("%Y-%m-%d %H:%M:%S PC"),
        "depth": args.depth,
        "rounds": args.rounds,
        "net": str(R0067),
        "summary": summary,
        "runs": runs,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
