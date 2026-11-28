"""Owner's Bundle Clock Test (OPUS-2811-OWNER-BUNDLE-TEST, 01:18 PC).

Builds FORGE_OWNER_BUNDLE_PGO.exe with:
  1. V3P_pairwise_psqt_fused_v3.patch  (FORGENN3-P pairwise+PSQT AVX-512 kernel + 15/15 loader safety + legacy r0067)
  2. SF13_qs_evasion_pruning.patch     (+20.87 screen / +8.34 1000g confirm, perft 5 PASS)
  3. SF8_conthist_6ply.patch           (+17.97 screen / +4.86 1000g confirm, perft 5 PASS)
  4. proto_1_corrhist_minor.patch      (+11.01 screen / +7.64 1000g confirm, perft 5 PASS)
  + UCI option LmrDeeperShallower=true (+8.34 1000g confirm, already in forge/r15dsg)

Explicitly EXCLUDED (declared before game 1):
  - SF4b1_v3_endgame_scale (-4.52 in 1000g confirm)
  - SF15_rfp_failsoft_blend (-0.35 in 1000g confirm)
  - All negative patches (SF7, SF4b2, SF5a, EvasionOrdering, W2_proto_3/4, etc.)
  - All unscreened Wave 4-6 patches (SF17..SF40, proto_9/10)
  (Note: obm4 is a training recipe already incorporated via G3_FULL25's anchor mix, not a C++ search patch.)

Uses Dual-Net Clang ThinLTO+PGO profiling (profiling BOTH G3_FULL25 and r0067 with all 45 live v3_uci_options
+ LmrDeeperShallower=true) so BOTH Arm A (G3_FULL25) and Arm B (r0067) run hot-PGO!

MUST ONLY RUN WHEN GPU AND CPU ARE 100% IDLE (zero training, zero subagents, zero other matches)!
Sets C:\\nnue-lab\\neon\\CLOCK_MATCH_RUNNING for NPS and both 2,000g @ 6+0.06 (concurrency=7) matches.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
SRC_BASE = LAB / "forge/r15dsg"
FIX = LAB / "neon/forge_fixes"
PY = str(LAB / "venv/Scripts/python.exe")
MG = FIX / "teamwork_wave2/streamC_gates/run_master_gates.py"

LLVM = LAB / "tools/llvm/llvm-mingw-20261104-ucrt-x86_64/bin"
CXX = str(LLVM / "clang++.exe")
PROFDATA = str(LLVM / "llvm-profdata.exe")
MINGW = str(LAB / "tools/mingw64")

LIVE_PGO_EXE = LAB / "runs/forge/engines/v3-r15dsg-sp-clang/forge.exe"
G3_NET = FIX / "gpu_runs/G3_FULL25_v3p_1024_cc0_anchored/cand.fnn3"
R0067_NET = LAB / "runs/forge/r0067/train/cand.fnn3"

BUNDLE_NAME = "FORGE_OWNER_BUNDLE_PGO"
BUNDLE_EXE = FIX / f"builds/{BUNDLE_NAME}.exe"
BUNDLE_PATCH = FIX / f"patches/{BUNDLE_NAME}.patch"
DECL_PATH = FIX / "OWNER_BUNDLE_DECLARATION.json"
SUMMARY_PATH = FIX / "OWNER_BUNDLE_RESULTS.json"

PATCHES = [
    FIX / "patches/V3P_pairwise_psqt_fused_v3.patch",
    FIX / "patches/SF13_qs_evasion_pruning.patch",
    FIX / "patches/SF8_conthist_6ply.patch",
    FIX / "teamwork_wave2/streamA_search/patches/proto_1_corrhist_minor.patch",
]

BASE_FLAGS = [
    "-std=c++20", "-O3", "-DNDEBUG",
    "-DFORGE_NNUE_HIDDEN=256", "-DFORGE_EXPOSE_TUNABLES=1",
    "-DFORGE_SPD_TT_NOTLS=1", "-DFORGE_SPD_NO_ZERO_MOVELISTS=2",
    "-DFORGE_SEARCH_SPEED2=1", "-DFORGE_SPD_PREFETCH_EARLY=1",
    "-DFORGE_SPD_SLIDER_PEXT=1", "-DFORGE_SPD_NNUE_ZMM=1",
    "-DFORGE_MATE_ALPHA_GUARD=1", "-DFORGE_NNUE_V3=1",
    "-ffp-contract=off", "-fno-fast-math", "-march=znver5", "-pthread",
    f"--sysroot={MINGW}", "-stdlib=libstdc++", "-rtlib=libgcc", "-unwindlib=libgcc",
    "-flto=thin",
]
LINK_FLAGS = ["-fuse-ld=lld", "-static", "-Wl,--no-insert-timestamp", "-Wl,--thinlto-jobs=8"]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def load_v3_opts() -> dict:
    cfg = tomllib.loads((LAB / "pipeline/config.forge.toml").read_text(encoding="utf-8"))
    return dict(cfg["engine"]["v3_uci_options"])


def _compile_one(args_t):
    cpp, obj, inc, extra = args_t
    cmd = [CXX, *BASE_FLAGS, f"-I{inc}", *extra, "-c", str(cpp), "-o", str(obj)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return cpp.name, r.returncode, r.stdout + r.stderr


def build_dual_pgo_bundle(work: Path, out_exe: Path, v3_opts: dict, jobs: int = 8) -> float:
    t0 = time.time()
    out_exe.parent.mkdir(parents=True, exist_ok=True)
    bdir = out_exe.parent / f"_build_{out_exe.stem}"
    if bdir.exists():
        shutil.rmtree(bdir)
    bdir.mkdir(parents=True)
    cpps = sorted((work / "src").glob("*.cpp"))
    inc = str(work / "include")

    def compile_and_link(sub: str, extra: list[str], exe_path: Path):
        sdir = bdir / sub
        sdir.mkdir(parents=True, exist_ok=True)
        objs = [sdir / f"{c.stem}.o" for c in cpps]
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
            futs = [ex.submit(_compile_one, (c, o, inc, extra)) for c, o in zip(cpps, objs)]
            for f in futs:
                name, rc, log = f.result()
                if rc != 0:
                    raise RuntimeError(f"Compile failed on {name}:\n{log}")
        cmd = [CXX, *BASE_FLAGS, *extra, *(str(o) for o in objs), *LINK_FLAGS, "-o", str(exe_path)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"Link failed:\n{r.stdout}\n{r.stderr}")

    gen_exe = bdir / "gen/forge_gen.exe"
    compile_and_link("gen", ["-fprofile-instr-generate"], gen_exe)

    opt_lines = [
        "setoption name NNUEArch value true",
        "setoption name MateAlphaGuard value true",
    ]
    for k, v in v3_opts.items():
        sv = "true" if v is True else ("false" if v is False else str(v))
        opt_lines.append(f"setoption name {k} value {sv}")
    opt_lines.append("setoption name LmrDeeperShallower value true")

    # Profile BOTH G3_FULL25 (1024w V3P) and r0067 (768w V3) so both Arm A and Arm B are PGO-hot!
    profraws = []
    for tag, net_p, depths in [
        ("g3", G3_NET, [11, 13, 16]),
        ("r0067", R0067_NET, [11, 13, 15]),
    ]:
        pr = str(bdir / f"gen/forge_{tag}.profraw")
        uci_in = (
            "uci\n"
            f"setoption name NNUEArchFile value {str(net_p).replace(chr(92), '/')}\n"
            + "\n".join(opt_lines) + "\n"
            "isready\n"
            + "\n".join(f"bench {d}" for d in depths) + "\n"
            "isready\nquit\n"
        )
        env = dict(os.environ, LLVM_PROFILE_FILE=pr)
        r = subprocess.run([str(gen_exe)], input=uci_in, capture_output=True, text=True, env=env, timeout=240)
        if r.returncode != 0:
            raise RuntimeError(f"PGO profile run ({tag}) failed:\n{r.stdout}\n{r.stderr}")
        profraws.append(pr)

    profdata = str(bdir / "forge_dual.profdata")
    r = subprocess.run([PROFDATA, "merge", "-o", profdata, *profraws], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"profdata merge failed:\n{r.stderr}")

    compile_and_link("use", [f"-fprofile-instr-use={profdata}"], out_exe)
    shutil.rmtree(bdir, ignore_errors=True)
    return round(time.time() - t0, 1)


def run_uci_bench(exe: Path, net: Path | None, opts: dict | None, depths: list[int]) -> dict:
    lines = ["uci"]
    if net is not None:
        lines += [
            f"setoption name NNUEArchFile value {str(net).replace(chr(92), '/')}",
            "setoption name NNUEArch value true",
        ]
    if opts:
        lines += [
            "setoption name Threads value 1",
            "setoption name Hash value 16",
            "setoption name OwnBook value false",
            "setoption name MateAlphaGuard value true",
        ]
        for k, v in opts.items():
            sv = "true" if v is True else ("false" if v is False else str(v))
            lines.append(f"setoption name {k} value {sv}")
    lines += ["isready"] + [f"bench {d}" for d in depths] + ["quit"]
    r = subprocess.run([str(exe)], input="\n".join(lines) + "\n", capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, f"bench failed rc={r.returncode}: {r.stderr}"
    out = {}
    for ln in r.stdout.splitlines():
        m = re.search(r"info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)", ln)
        if m:
            out[f"d{m.group(1)}"] = {
                "nodes": int(m.group(2)),
                "time_ms": int(m.group(3)),
                "nps": int(m.group(4)),
            }
    return out


def run_perft5(exe: Path) -> int:
    r = subprocess.run([str(exe)], input="uci\nisready\nposition startpos\ngo perft 5\nquit\n", capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"go perft 5 failed: {r.stderr}"
    for ln in r.stdout.splitlines():
        if "4865609" in ln:
            return 4865609
    raise RuntimeError(f"go perft 5 != 4865609 in output:\n{r.stdout}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--games", type=int, default=2000)
    ap.add_argument("--tc", default="6+0.06")
    ap.add_argument("--concurrency", type=int, default=7)
    args = ap.parse_args()

    v3_opts = load_v3_opts()
    bundle_opts = dict(v3_opts)
    bundle_opts["LmrDeeperShallower"] = True

    applied_meta = []
    build_sec = 0.0
    if not args.skip_build or not BUNDLE_EXE.exists():
        work = FIX / f"_compose_{BUNDLE_NAME}"
        if work.exists():
            shutil.rmtree(work)
        shutil.copytree(SRC_BASE, work)
        try:
            for pp in PATCHES:
                assert pp.exists(), f"Missing patch: {pp}"
                chk = subprocess.run(["git", "-C", str(work), "apply", "--check", str(pp)], capture_output=True, text=True)
                assert chk.returncode == 0, f"Conflict applying {pp.name}: {chk.stderr}"
                ap_r = subprocess.run(["git", "-C", str(work), "apply", str(pp)], capture_output=True, text=True)
                assert ap_r.returncode == 0, f"Apply failed {pp.name}: {ap_r.stderr}"
                applied_meta.append({"patch": str(pp), "name": pp.name, "sha256": sha256_file(pp)})
                print(f"APPLIED OK: {pp.name}", flush=True)

            # Export combined patch
            diffs: list[str] = []
            for wf in sorted(work.rglob("*")):
                if not wf.is_file():
                    continue
                rel = wf.relative_to(work)
                orig = SRC_BASE / rel
                if not orig.exists():
                    continue
                ob, wb = orig.read_bytes(), wf.read_bytes()
                if ob == wb:
                    continue
                diffs.extend(
                    difflib.unified_diff(
                        ob.decode("utf-8").replace("\r\n", "\n").splitlines(keepends=True),
                        wb.decode("utf-8").replace("\r\n", "\n").splitlines(keepends=True),
                        fromfile=f"a/{rel.as_posix()}",
                        tofile=f"b/{rel.as_posix()}",
                    )
                )
            BUNDLE_PATCH.write_text("".join(diffs), encoding="utf-8", newline="\n")
            chk_all = subprocess.run(["git", "-C", str(SRC_BASE), "apply", "--check", str(BUNDLE_PATCH)], capture_output=True, text=True)
            assert chk_all.returncode == 0, f"Combined patch check failed: {chk_all.stderr}"
            print(f"COMBINED PATCH OK: {BUNDLE_PATCH} ({len(diffs)} lines)", flush=True)

            build_sec = build_dual_pgo_bundle(work, BUNDLE_EXE, v3_opts, jobs=args.jobs)
            print(f"BUILT {BUNDLE_EXE} in {build_sec}s (dual-net ThinLTO+PGO)", flush=True)
        finally:
            shutil.rmtree(work, ignore_errors=True)
    else:
        for pp in PATCHES:
            applied_meta.append({"patch": str(pp), "name": pp.name, "sha256": sha256_file(pp)})

    # Master Gates (--full on G3_FULL25 + --quick on r0067)
    gate_g3 = FIX / f"builds/{BUNDLE_NAME}_gate_g3_full.json"
    gate_r67 = FIX / f"builds/{BUNDLE_NAME}_gate_r0067_quick.json"
    if not gate_g3.exists():
        rg = subprocess.run([PY, str(MG), "--exe", str(BUNDLE_EXE), "--net", str(G3_NET), "--full", "--json-out", str(gate_g3)], capture_output=True, text=True)
        assert rg.returncode == 0, f"G3 full gates failed: {rg.stdout}\n{rg.stderr}"
    if not gate_r67.exists():
        rl = subprocess.run([PY, str(MG), "--exe", str(BUNDLE_EXE), "--net", str(R0067_NET), "--quick", "--json-out", str(gate_r67)], capture_output=True, text=True)
        assert rl.returncode == 0, f"r0067 quick gates failed: {rl.stdout}\n{rl.stderr}"
    g3_hp = json.loads(gate_g3.read_text(encoding="utf-8")).get("hard_pass")
    r67_hp = json.loads(gate_r67.read_text(encoding="utf-8")).get("hard_pass")
    assert g3_hp and r67_hp, f"Gate failure: g3={g3_hp} r0067={r67_hp}"

    # Verify perft 5 & bench signatures (built-in, r0067+B4 live opts, r0067+B4+LmrDeeper, G3+B4+LmrDeeper)
    p5 = run_perft5(BUNDLE_EXE)
    b_builtin = run_uci_bench(BUNDLE_EXE, None, None, [11, 13])
    b_r67_b4_live = run_uci_bench(BUNDLE_EXE, R0067_NET, v3_opts, [11, 13])
    b_r67_b4 = run_uci_bench(BUNDLE_EXE, R0067_NET, bundle_opts, [11, 13])
    b_g3_b4 = run_uci_bench(BUNDLE_EXE, G3_NET, bundle_opts, [11, 13])

    # Clean GPU+CPU-idle 3x interleaved bench 13 NPS
    clock_flag = LAB / "neon/CLOCK_MATCH_RUNNING"
    nps_runs: dict[str, list[dict]] = {"live_pgo_r0067": [], "bundle_pgo_r0067": [], "bundle_pgo_G3": []}
    if not args.build_only:
        try:
            clock_flag.write_text("Owner Bundle clean idle 3x bench 13 NPS\n", encoding="utf-8")
            for _ in range(3):
                nps_runs["live_pgo_r0067"].append(run_uci_bench(LIVE_PGO_EXE, R0067_NET, v3_opts, [13])["d13"])
                nps_runs["bundle_pgo_r0067"].append(run_uci_bench(BUNDLE_EXE, R0067_NET, bundle_opts, [13])["d13"])
                nps_runs["bundle_pgo_G3"].append(run_uci_bench(BUNDLE_EXE, G3_NET, bundle_opts, [13])["d13"])
        finally:
            if clock_flag.exists():
                clock_flag.unlink()
        med_nps = {k: sorted(x["nps"] for x in v)[1] for k, v in nps_runs.items()}
        nps_summary = {
            "runs": nps_runs,
            "median_nps": med_nps,
            "ratio_bundle_r0067_vs_live": round(med_nps["bundle_pgo_r0067"] / max(1, med_nps["live_pgo_r0067"]), 4),
            "ratio_bundle_G3_vs_live": round(med_nps["bundle_pgo_G3"] / max(1, med_nps["live_pgo_r0067"]), 4),
        }
    else:
        nps_summary = None

    decl = {
        "written": time.strftime("%Y-%m-%d %H:%M:%S"),
        "request_ref": "OPUS-2811-OWNER-BUNDLE-TEST (01:18 PC)",
        "bundle_exe": str(BUNDLE_EXE),
        "bundle_exe_sha256": sha256_file(BUNDLE_EXE),
        "bundle_exe_bytes": BUNDLE_EXE.stat().st_size,
        "bundle_patch": str(BUNDLE_PATCH),
        "bundle_patch_sha256": sha256_file(BUNDLE_PATCH),
        "live_pgo_exe": str(LIVE_PGO_EXE),
        "live_pgo_exe_sha256": sha256_file(LIVE_PGO_EXE),
        "g3_net": str(G3_NET),
        "g3_net_sha256": sha256_file(G3_NET),
        "r0067_net": str(R0067_NET),
        "r0067_net_sha256": sha256_file(R0067_NET),
        "pgo_profile": "Dual-Net Clang ThinLTO+PGO (G3_FULL25 d11/13/16 + r0067 d11/13/15, all 45 live v3_uci_options + LmrDeeperShallower=true)",
        "build_seconds": build_sec,
        "patches_included": applied_meta,
        "extra_uci_options_on_bundle": {"LmrDeeperShallower": True},
        "explicitly_excluded": [
            "SF4b1_v3_endgame_scale (-4.52 in 1000g confirm)",
            "SF15_rfp_failsoft_blend (-0.35 in 1000g confirm)",
            "All negative patches (SF7, SF4b2, SF5a, EvasionOrdering, W2_proto_3, W2_proto_4)",
            "All unscreened Wave 4-6 patches (SF17..SF40, proto_9, proto_10)",
            "obm4 (training recipe, not a C++ search patch; already represented via G3_FULL25 anchors)",
        ],
        "gates": {"perft5": p5, "g3_full_hard_pass": g3_hp, "r0067_quick_hard_pass": r67_hp},
        "benches": {
            "builtin_default_11_13": b_builtin,
            "r0067_plus_B4_live_opts_11_13": b_r67_b4_live,
            "r0067_plus_B4_plus_LmrDeeper_11_13": b_r67_b4,
            "G3_plus_B4_plus_LmrDeeper_11_13": b_g3_b4,
        },
        "clean_idle_nps": nps_summary,
        "arms": {
            "ARM_A_owners": {
                "name": "OWNER_BUNDLE_ARMA_bundleG3_vs_liveR0067_2000g_6p006",
                "cand": "FORGE_OWNER_BUNDLE_PGO.exe (LmrDeeperShallower=true) + G3_FULL25/cand.fnn3",
                "base": "v3-r15dsg-sp-clang/forge.exe + r0067/train/cand.fnn3",
                "games": args.games, "tc": args.tc, "concurrency": args.concurrency, "seed": 202611901,
            },
            "ARM_B_control": {
                "name": "OWNER_BUNDLE_ARMB_bundleR0067_vs_liveR0067_2000g_6p006",
                "cand": "FORGE_OWNER_BUNDLE_PGO.exe (LmrDeeperShallower=true) + r0067/train/cand.fnn3",
                "base": "v3-r15dsg-sp-clang/forge.exe + r0067/train/cand.fnn3",
                "games": args.games, "tc": args.tc, "concurrency": args.concurrency, "seed": 202611902,
            },
        },
        "decision_rule": "Evaluate each arm on its own 95% pentanomial Elo CI; any placement still goes by lab-place-a-change.",
    }
    DECL_PATH.write_text(json.dumps(decl, indent=2), encoding="utf-8")
    print("WROTE DECLARATION:", DECL_PATH, flush=True)
    print(json.dumps({"benches": decl["benches"], "clean_idle_nps": nps_summary}, indent=2), flush=True)

    if args.build_only:
        return 0

    results = {"declaration": decl, "arms": {}}
    runner = str(FIX / "run_net_match.py")
    for arm_key, name, cand_net, seed, rule in [
        (
            "ARM_A_owners",
            "OWNER_BUNDLE_ARMA_bundleG3_vs_liveR0067_2000g_6p006",
            G3_NET,
            202611901,
            "Owner Bundle Arm A: FORGE_OWNER_BUNDLE_PGO (V3Pv3+SF13+SF8+W2P1 + LmrDeeperShallower=true) + G3_FULL25 vs live PGO + r0067, 2000g @ 6+0.06 conc=7",
        ),
        (
            "ARM_B_control",
            "OWNER_BUNDLE_ARMB_bundleR0067_vs_liveR0067_2000g_6p006",
            R0067_NET,
            202611902,
            "Owner Bundle Arm B (Attribution Control): FORGE_OWNER_BUNDLE_PGO (V3Pv3+SF13+SF8+W2P1 + LmrDeeperShallower=true) + r0067 vs live PGO + r0067, 2000g @ 6+0.06 conc=7",
        ),
    ]:
        sum_p = FIX / "matches" / name / "summary.json"
        if not sum_p.exists():
            print(f"=== LAUNCH {arm_key}: {name} ===", flush=True)
            cmd = [
                PY, runner,
                "--name", name,
                "--cand-exe", str(BUNDLE_EXE),
                "--base-exe", str(LIVE_PGO_EXE),
                "--cand-net", str(cand_net),
                "--base-net", str(R0067_NET),
                "--games", str(args.games), "--nodes", "0", "--tc", args.tc,
                "--concurrency", str(args.concurrency), "--seed", str(seed),
                "--cand-opt", "LmrDeeperShallower=true",
                "--rule", rule,
            ]
            r = subprocess.run(cmd, text=True)
            assert r.returncode == 0 and sum_p.exists(), f"{name} failed rc={r.returncode}"
        results["arms"][arm_key] = json.loads(sum_p.read_text(encoding="utf-8"))

    SUMMARY_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("OWNER_BUNDLE_CLOCK_TEST_COMPLETE:", SUMMARY_PATH, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
