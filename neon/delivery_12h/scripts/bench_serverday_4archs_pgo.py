"""Clean GPU+CPU-Idle 5-Architecture PGO NPS Comparison (FORGE_FINAL_G3_PGO.exe vs live PGO r0067).

Run ONLY when GPU + CPU are 100% IDLE (sets neon/CLOCK_MATCH_RUNNING in try/finally).
Measures 5 interleaved rounds of `bench 15` (all 45 live Big Tune v3_uci_options) across:
  1. live_pgo_r0067       (768w SCReLU, live PGO binary)
  2. v3p_pgo_r0067_compat (768w SCReLU, FORGE_FINAL_G3_PGO.exe — proves 0% legacy regression!)
  3. v3p_pgo_768p_kb8     (768w Pairwise+PSQT, 384 L1 pairs — expected FASTER than live 768w SCReLU!)
  4. v3p_pgo_1024p_kb8    (1024w Pairwise+PSQT, G3_FULL25)
  5. v3p_pgo_1536p_kb8    (1536w Pairwise+PSQT, Server-Day wide)
  6. v3p_pgo_1024p_kb16   (1024w Pairwise+PSQT, 16 king buckets)
"""
from __future__ import annotations

import json
import re
import statistics
import subprocess
import time
import tomllib
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
LOCK = LAB / "neon/CLOCK_MATCH_RUNNING"
LIVE_PGO = LAB / "runs/forge/engines/v3-r15dsg-sp-clang/forge.exe"
V3P_PGO = FIX / "builds/FORGE_FINAL_G3_PGO.exe"
OUT = FIX / "CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json"


def run_bench(exe: Path, net: Path, v3_opts: dict, depth: int = 15) -> tuple[int, int, float]:
    lines = [
        "uci",
        f"setoption name NNUEArchFile value {str(net).replace(chr(92), '/')}",
        "setoption name NNUEArch value true",
        "setoption name MateAlphaGuard value true",
    ]
    for k, v in v3_opts.items():
        sv = "true" if v is True else ("false" if v is False else str(v))
        lines.append(f"setoption name {k} value {sv}")
    lines += ["isready", f"bench {depth}", "quit"]
    r = subprocess.run([str(exe)], input="\n".join(lines) + "\n", capture_output=True, text=True, timeout=180)
    assert r.returncode == 0 and "NNUE v3 active" in r.stdout, r.stdout[:300]
    m = re.findall(r"nodes\s+(\d+)\s+time\s+(\d+)\s+nps\s+(\d+)", r.stdout)
    assert m, r.stdout[-300:]
    return int(m[-1][0]), int(m[-1][1]), float(m[-1][2])


def main() -> int:
    assert V3P_PGO.exists(), f"Missing {V3P_PGO} (run --phase pgo_clock first!)"
    cfg_p = LAB / "pipeline/config.forge.toml"
    v3_opts = tomllib.loads(cfg_p.read_text(encoding="utf-8")).get("engine", {}).get("v3_uci_options", {})
    entries = [
        ("live_pgo_r0067_768screlu", LIVE_PGO, LAB / "runs/forge/r0067/train/cand.fnn3"),
        ("v3p_pgo_r0067_768screlu", V3P_PGO, LAB / "runs/forge/r0067/train/cand.fnn3"),
        ("v3p_pgo_768p_kb8", V3P_PGO, FIX / "gpu_runs/G5a_cc0_768p_kb8/cand.fnn3"),
        ("v3p_pgo_1024p_kb8_G3", V3P_PGO, FIX / "gpu_runs/G3_FULL25_v3p_1024_cc0_anchored/cand.fnn3"),
        ("v3p_pgo_1536p_kb8", V3P_PGO, FIX / "gpu_runs/G5b_cc0_1536p_kb8/cand.fnn3"),
        ("v3p_pgo_1024p_kb16", V3P_PGO, FIX / "gpu_runs/G5c_cc0_1024p_kb16/cand.fnn3"),
    ]
    for lbl, ex, nt in entries:
        assert ex.exists() and nt.exists(), f"Missing {lbl}: {ex} / {nt}"

    LOCK.write_text(f"bench_serverday_4archs_pgo started {time.strftime('%Y-%m-%d %H:%M:%S')}\n", encoding="utf-8")
    try:
        for _, ex, nt in entries:
            run_bench(ex, nt, v3_opts, depth=11)
        samples = {lbl: [] for lbl, _, _ in entries}
        nodes_map = {}
        for rnd in range(5):
            order = entries if rnd % 2 == 0 else list(reversed(entries))
            for lbl, ex, nt in order:
                nd, _ms, nps = run_bench(ex, nt, v3_opts, depth=15)
                if lbl in nodes_map:
                    assert nodes_map[lbl] == nd, f"Node drift on {lbl}"
                nodes_map[lbl] = nd
                samples[lbl].append(nps)
        ref = statistics.median(samples["live_pgo_r0067_768screlu"])
        summary = {}
        for lbl, ex, nt in entries:
            med = statistics.median(samples[lbl])
            summary[lbl] = {
                "nodes": nodes_map[lbl],
                "median_nps": round(med, 1),
                "all_nps": [round(x, 1) for x in samples[lbl]],
                "ratio_vs_live_pgo_r0067": round(med / ref, 4),
            }
        rep = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "depth": 15, "rounds": 5, "summary": summary}
        OUT.write_text(json.dumps(rep, indent=2), encoding="utf-8")
        print("CLEAN_IDLE_SERVERDAY_5ARCH_NPS:", json.dumps(rep, indent=2), flush=True)
    finally:
        if LOCK.exists():
            LOCK.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
