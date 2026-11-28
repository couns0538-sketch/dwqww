"""Post-G3_FULL25 Automated Evaluation, SWA, True-PGO Build, Clean NPS & Equal-Time Confirmation.

Run ONLY after GPU G3_FULL25 finishes (and when GPU is idle for clean NPS / clock match!).
Steps:
  1. Build V3P SWA candidates from G3_FULL25 cycle checkpoints (cand_e24 + cand_e40, and cand_e12 + cand_e24 + cand_e40).
  2. Score cand.fnn3 and both SWA .fnn3 nets with:
       - eval_net_full.py (S1..S7, M4 WDL MSE, OLS piece values, ob0<->ob1 cliff)
       - Opus net_sanity.py v2 (S1..S8 classical cp via --exe-cmd)
       - eval_sf19_blunder_check.py (6,000-row SF19 M4 Task-1 slice)
       - Stream C run_master_gates.py --full (on cand.fnn3)
  3. Optionally build true PGO engine with build_fast.py --pgo --pgo-net <chosen_net>.
  4. Run clean GPU+CPU-idle 3x interleaved bench 13 NPS (setting neon/CLOCK_MATCH_RUNNING) comparing:
       - live PGO v3-r15dsg-sp-clang/forge.exe + r0067
       - v3p_engine.exe (non-PGO) + chosen_net
       - v3p_pgo.exe (if built) + chosen_net
  5. Optionally launch formal pre-declared 2,000g @ 6+0.06 equal-time confirmation match!
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
G3_DIR = FIX / "gpu_runs/G3_FULL25_v3p_1024_cc0_anchored"
PY = str(LAB / "venv/Scripts/python.exe")
PY101 = str(LAB / "venv101/Scripts/python.exe")

LIVE_PGO_EXE = LAB / "runs/forge/engines/v3-r15dsg-sp-clang/forge.exe"
V3P_EXE = FIX / "builds/v3p_fused_v3_engine.exe"
R0067_NET = LAB / "runs/forge/r0067/train/cand.fnn3"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(cmd: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def bench13_nps(exe: Path, net: Path, v3_opts: dict, extra_opts: dict | None = None) -> dict:
    opts = dict(v3_opts)
    if extra_opts:
        opts.update(extra_opts)
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
    lines += ["isready", "bench 13", "quit"]
    r = subprocess.run([str(exe)], input="\n".join(lines) + "\n", capture_output=True, text=True, timeout=90)
    assert r.returncode == 0, f"bench13 failed rc={r.returncode}: {r.stderr}"
    for ln in r.stdout.splitlines():
        if ln.startswith("info string bench depth 13 "):
            m = re.search(r"nodes (\d+) time (\d+) nps (\d+)", ln)
            if m:
                return {"nodes": int(m.group(1)), "time_ms": int(m.group(2)), "nps": int(m.group(3))}
    raise RuntimeError(f"bench 13 line missing for {exe}")


def eval_one_net(tag: str, net_path: Path, exe_path: Path, out_dir: Path, run_full_gates: bool = False) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    rec: dict = {"tag": tag, "net": str(net_path), "sha256": sha256_file(net_path), "bytes": net_path.stat().st_size}

    r1 = run_cmd([PY, str(FIX / "eval_net_full.py"), str(net_path), "--out", str(out_dir / f"eval_full_{tag}.json")], timeout=180)
    if r1.returncode == 0 and (out_dir / f"eval_full_{tag}.json").exists():
        rec["eval_full"] = json.loads((out_dir / f"eval_full_{tag}.json").read_text(encoding="utf-8"))
    else:
        rec["eval_full_err"] = r1.stderr[-400:]

    r2 = run_cmd([
        PY101, "-I", "-B", str(LAB / "tmp/opus_scratch/netcheck/net_sanity.py"),
        str(net_path), "--exe-cmd", json.dumps([str(exe_path)]),
    ], timeout=180)
    (out_dir / f"net_sanity_v2_{tag}.txt").write_text(r2.stdout + ("\nSTDERR:\n" + r2.stderr if r2.stderr else ""), encoding="utf-8")
    flags = [ln.strip() for ln in r2.stdout.splitlines() if "FLAG" in ln]
    rec["net_sanity_flags"] = flags

    r3 = run_cmd([
        PY, str(FIX / "eval_sf19_blunder_check.py"),
        str(net_path), "--exe", str(exe_path), "--out", str(out_dir / f"sf19_slice_{tag}.json"),
    ], timeout=180)
    if r3.returncode == 0 and (out_dir / f"sf19_slice_{tag}.json").exists():
        rec["sf19_slice"] = json.loads((out_dir / f"sf19_slice_{tag}.json").read_text(encoding="utf-8"))

    # Opus Point 3(b): strictly disjoint 4,000-pos Held-Out Syzygy Benchmark + per-pos TSV for Opus recount
    hs_script = FIX / "eval_heldout_syzygy.py"
    if hs_script.exists():
        r3b = run_cmd([
            PY, str(hs_script), str(net_path), "--exe", str(exe_path),
            "--out", str(out_dir / f"heldout_syzygy_4k_{tag}.json"),
            "--dump-tsv", str(out_dir / f"heldout_perpos_{tag}.tsv"),
        ], timeout=180)
        if r3b.returncode == 0 and (out_dir / f"heldout_syzygy_4k_{tag}.json").exists():
            rec["heldout_syzygy_4k"] = json.loads((out_dir / f"heldout_syzygy_4k_{tag}.json").read_text(encoding="utf-8"))
            rec["heldout_perpos_tsv"] = str(out_dir / f"heldout_perpos_{tag}.tsv")

    if run_full_gates:
        mg = FIX / "teamwork_wave2/streamC_gates/run_master_gates.py"
        if mg.exists():
            r4 = run_cmd([
                PY, str(mg), "--exe", str(exe_path), "--net", str(net_path),
                "--full", "--json-out", str(out_dir / f"master_gate_full_{tag}.json"),
            ], timeout=300)
            rec["master_gates_rc"] = r4.returncode
            if (out_dir / f"master_gate_full_{tag}.json").exists():
                rec["master_gates_ok"] = json.loads((out_dir / f"master_gate_full_{tag}.json").read_text(encoding="utf-8")).get("hard_pass")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default=str(G3_DIR))
    ap.add_argument("--exe", default=str(V3P_EXE))
    ap.add_argument("--build-pgo-src", default="", help="Optional source dir to build true PGO exe with build_fast.py --pgo --pgo-net")
    ap.add_argument("--pgo-out-name", default="v3p_final_pgo.exe")
    ap.add_argument("--skip-swa", action="store_true")
    ap.add_argument("--skip-nps", action="store_true")
    ap.add_argument("--rounds-nps", type=int, default=3)
    ap.add_argument("--run-clock-match", action="store_true", help="Run formal 2000g @ 6+0.06 equal-time match vs live PGO r0067")
    ap.add_argument("--clock-games", type=int, default=2000)
    ap.add_argument("--clock-tc", default="6+0.06")
    ap.add_argument("--clock-concurrency", type=int, default=10)
    ap.add_argument("--clock-name", default="G3_FULL25_pgo_vs_live_r0067_2000g_6p006")
    ap.add_argument("--cand-opt", action="append", default=[])
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    cand_net = run_dir / "cand.fnn3"
    assert cand_net.exists(), f"Missing {cand_net}"
    exe_path = Path(args.exe)
    assert exe_path.exists(), f"Missing {exe_path}"

    summary: dict = {"run_dir": str(run_dir), "nets": {}}

    # 1. Build SWA nets from cycle checkpoints if present
    swa_targets: list[tuple[str, list[Path]]] = []
    e12, e24, e40 = run_dir / "cand_e12.pt", run_dir / "cand_e24.pt", run_dir / "cand_e40.pt"
    if not args.skip_swa:
        if e24.exists() and e40.exists():
            swa_targets.append(("swa_e24_40", [e24, e40]))
        if e12.exists() and e24.exists() and e40.exists():
            swa_targets.append(("swa_e12_24_40", [e12, e24, e40]))
        for tag, ckpts in swa_targets:
            swa_dir = run_dir / tag
            r = run_cmd([
                PY101, str(FIX / "make_swa_v3p.py"),
                "--ckpts", *[str(c) for c in ckpts],
                "--out-dir", str(swa_dir),
            ], timeout=120)
            print(f"SWA {tag} rc={r.returncode}\n{r.stdout.strip()}", flush=True)
            if r.returncode != 0:
                print(r.stderr, flush=True)
            else:
                import shutil as _sh
                if (swa_dir / "cand.fnn3").exists():
                    _sh.copy2(swa_dir / "cand.fnn3", run_dir / f"cand_{tag}.fnn3")
                if (swa_dir / "cand.pt").exists():
                    _sh.copy2(swa_dir / "cand.pt", run_dir / f"cand_{tag}.pt")

    # 2. Score cand + SWA nets
    print("=== Evaluating cand.fnn3 (with --full Master Gates) ===", flush=True)
    summary["nets"]["cand"] = eval_one_net("cand", cand_net, exe_path, run_dir, run_full_gates=True)
    for tag, _ in swa_targets:
        fnn3 = run_dir / f"cand_{tag}.fnn3"
        if fnn3.exists():
            print(f"=== Evaluating {tag} ===", flush=True)
            summary["nets"][tag] = eval_one_net(tag, fnn3, exe_path, run_dir, run_full_gates=False)

    # Pick lowest final_eval / m4_wdl_mse net for PGO & match (default cand)
    best_tag = "cand"
    best_mse = 999.0
    for tag, rec in summary["nets"].items():
        mse = rec.get("eval_full", {}).get("m4_wdl_mse")
        if isinstance(mse, (int, float)) and mse < best_mse:
            best_mse = mse
            best_tag = tag
    best_net = Path(summary["nets"][best_tag]["net"])
    summary["selected_best_tag"] = best_tag
    summary["selected_best_net"] = str(best_net)
    print(f"SELECTED BEST NET BY M4 WDL MSE: {best_tag} ({best_mse:.6f}) -> {best_net}", flush=True)

    # 3. Optional true PGO build profiled on best_net
    match_exe = exe_path
    if args.build_pgo_src:
        pgo_out = FIX / "builds" / args.pgo_out_name
        r_pgo = subprocess.run([
            PY, str(FIX / "build_fast.py"),
            "--src", args.build_pgo_src,
            "--out", str(pgo_out),
            "--pgo", "--pgo-net", str(best_net),
        ], text=True)
        assert r_pgo.returncode == 0 and pgo_out.exists(), f"PGO build failed rc={r_pgo.returncode}"
        match_exe = pgo_out
        summary["pgo_exe"] = str(pgo_out)
        summary["pgo_exe_sha256"] = sha256_file(pgo_out)

    # 4. Clean GPU+CPU-idle 3x interleaved bench 13 NPS
    if not args.skip_nps:
        cfg = tomllib.loads((LAB / "pipeline/config.forge.toml").read_text(encoding="utf-8"))
        v3_opts = dict(cfg["engine"]["v3_uci_options"])
        extra_opts = {}
        for item in args.cand_opt:
            k, v = item.split("=", 1)
            extra_opts[k.strip()] = v.strip()
        clock_flag = LAB / "neon/CLOCK_MATCH_RUNNING"
        nps_runs: dict[str, list[dict]] = {"live_pgo_r0067": [], "cand_best": []}
        try:
            clock_flag.write_text(f"Post-G3 clean GPU-idle bench 13 NPS ({best_tag})\n", encoding="utf-8")
            for _ in range(args.rounds_nps):
                nps_runs["live_pgo_r0067"].append(bench13_nps(LIVE_PGO_EXE, R0067_NET, v3_opts))
                nps_runs["cand_best"].append(bench13_nps(match_exe, best_net, v3_opts, extra_opts))
        finally:
            if clock_flag.exists():
                clock_flag.unlink()
        med = {k: sorted(x["nps"] for x in v)[len(v) // 2] for k, v in nps_runs.items()}
        med_ms = {k: sorted(x["time_ms"] for x in v)[len(v) // 2] for k, v in nps_runs.items()}
        summary["nps_clean_idle"] = {
            "runs": nps_runs,
            "median_nps": med,
            "median_time_ms": med_ms,
            "nps_ratio_vs_live_pgo": round(med["cand_best"] / max(1, med["live_pgo_r0067"]), 4),
            "wall_time_ratio_vs_live_pgo": round(med_ms["cand_best"] / max(1, med_ms["live_pgo_r0067"]), 4),
        }
        print("=== CLEAN NPS SUMMARY ===\n" + json.dumps(summary["nps_clean_idle"], indent=2), flush=True)

    (run_dir / "post_g3_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"WROTE {run_dir / 'post_g3_summary.json'}", flush=True)

    # 5. Optional formal equal-time confirmation match
    if args.run_clock_match:
        cmd = [
            PY, str(FIX / "run_net_match.py"),
            "--name", args.clock_name,
            "--cand-exe", str(match_exe), "--base-exe", str(LIVE_PGO_EXE),
            "--cand-net", str(best_net), "--base-net", str(R0067_NET),
            "--games", str(args.clock_games), "--nodes", "0", "--tc", args.clock_tc,
            "--concurrency", str(args.clock_concurrency), "--seed", "202611500",
            "--rule", f"Equal-time confirmation {args.clock_games}g @ {args.clock_tc}: {match_exe.name} + {best_tag} vs live PGO r0067",
        ]
        for item in args.cand_opt:
            cmd += ["--cand-opt", item]
        r_m = subprocess.run(cmd, text=True)
        print(f"CLOCK MATCH rc={r_m.returncode}", flush=True)
        return r_m.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
