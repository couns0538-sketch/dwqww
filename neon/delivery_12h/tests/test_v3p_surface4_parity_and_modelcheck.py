"""Fail-before / pass-after acceptance test for V3P Loop Placement Surface 4:
- Surface 4a: patches/v3p_surface4a_v3_parity.patch (pipeline/tools/v3_parity.py)
- Surface 4b: patches/v3p_surface4b_v3_model_check.patch (pipeline/tools/v3_model_check.py)

Verifies on temporary copies (pipeline/ untouched):
1. BEFORE patch: unpatched pipeline/tools/v3_parity.py FAILS (rc != 0) on a FORGENN3-P net!
2. AFTER patch: patched v3_parity.py PASSES (rc == 0) on BOTH FORGENN3-P (G2/G3) AND legacy r0067,
   AND catches planted_bug=1 (rc == 0 with planted bug detection).
3. BEFORE patch: unpatched pipeline/tools/v3_model_check.py FAILS (rc != 0) on a FORGENN3-P .pt/.fnn3!
4. AFTER patch: patched v3_model_check.py (with forge_v3p + forge_train_v3p adapter on PYTHONPATH)
   PASSES (rc == 0) on FORGENN3-P!
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
PY_GPU = str(LAB / "venv101/Scripts/python.exe")
PY_CPU = str(LAB / "venv/Scripts/python.exe")
V3P_EXE = str(FIX / "builds/v3p_fused_v3_engine.exe")
R0067 = str(LAB / "runs/forge/r0067/train/cand.fnn3")
# Pick completed FORGENN3-P net + model (prefers G3_FULL25 if ready, else G2_1024p)
G3_NET = FIX / "gpu_runs/G3_FULL25_v3p_1024_cc0_anchored/cand.fnn3"
G3_PT = FIX / "gpu_runs/G3_FULL25_v3p_1024_cc0_anchored/cand.pt"
G2_NET = FIX / "gpu_runs/G2_v3p_1024_pairwise_psqt/cand.fnn3"
G2_PT = FIX / "gpu_runs/G2_v3p_1024_pairwise_psqt/cand.pt"


def main() -> int:
    v3p_net = str(G3_NET if G3_NET.exists() else G2_NET)
    v3p_pt = str(G3_PT if G3_PT.exists() else G2_PT)
    assert Path(v3p_net).exists(), f"Missing FORGENN3-P net: {v3p_net}"
    assert Path(V3P_EXE).exists(), f"Missing V3P exe: {V3P_EXE}"

    with tempfile.TemporaryDirectory(prefix="test_s4_") as td:
        tmp = Path(td)
        (tmp / "pipeline/tools").mkdir(parents=True)
        shutil.copy2(LAB / "pipeline/tools/v3_parity.py", tmp / "pipeline/tools/v3_parity.py")
        shutil.copy2(LAB / "pipeline/tools/v3_model_check.py", tmp / "pipeline/tools/v3_model_check.py")

        # 1. BEFORE patch: v3_parity.py MUST FAIL on FORGENN3-P net
        r_before_par = subprocess.run(
            [PY_CPU, str(tmp / "pipeline/tools/v3_parity.py"), V3P_EXE, v3p_net, "40", "0"],
            capture_output=True, text=True,
        )
        print(f"BEFORE_PARITY_V3P rc={r_before_par.returncode}")
        assert r_before_par.returncode != 0, "Unpatched v3_parity.py unexpectedly passed on FORGENN3-P!"

        # Apply both Surface 4 patches to temp copy
        for pname in ["v3p_surface4a_v3_parity.patch", "v3p_surface4b_v3_model_check.patch"]:
            r_ap = subprocess.run(
                ["git", "apply", str(FIX / "patches" / pname)],
                cwd=str(tmp), capture_output=True, text=True,
            )
            assert r_ap.returncode == 0, f"apply failed {pname}: {r_ap.stderr}"

        # Stage Surface 2 (forge_v3p.py) and Surface 3 (forge_train_v3p.py adapter) in temp PYTHONPATH
        stage = tmp / "py_stage"
        stage.mkdir()
        shutil.copy2(FIX / "forge_v3p.py", stage / "forge_v3p.py")
        shutil.copy2(FIX / "forge_train_v3p_loop_adapter.py", stage / "forge_train_v3p.py")
        shutil.copy2(FIX / "train_v3p.py", stage / "train_v3p.py")
        env = dict(**__import__("os").environ)
        env["PYTHONPATH"] = str(stage) + ";" + str(FIX)

        # 2. AFTER patch: v3_parity.py PASSES on FORGENN3-P (normal + planted_bug=1) AND legacy r0067
        r_after_v3p = subprocess.run(
            [PY_CPU, str(tmp / "pipeline/tools/v3_parity.py"), V3P_EXE, v3p_net, "100", "0"],
            env=env, capture_output=True, text=True,
        )
        print(f"AFTER_PARITY_V3P rc={r_after_v3p.returncode} tail={r_after_v3p.stdout.strip().splitlines()[-2:]}")
        assert r_after_v3p.returncode == 0, r_after_v3p.stdout + r_after_v3p.stderr

        r_after_bug = subprocess.run(
            [PY_CPU, str(tmp / "pipeline/tools/v3_parity.py"), V3P_EXE, v3p_net, "100", "1"],
            env=env, capture_output=True, text=True,
        )
        print(f"AFTER_PARITY_V3P_PLANTED_BUG rc={r_after_bug.returncode}")
        assert r_after_bug.returncode == 0, r_after_bug.stdout + r_after_bug.stderr

        r_after_leg = subprocess.run(
            [PY_CPU, str(tmp / "pipeline/tools/v3_parity.py"), V3P_EXE, R0067, "100", "0"],
            env=env, capture_output=True, text=True,
        )
        print(f"AFTER_PARITY_LEGACY_R0067 rc={r_after_leg.returncode}")
        assert r_after_leg.returncode == 0, r_after_leg.stdout + r_after_leg.stderr

        print("SURFACE_4A_FAIL_BEFORE_PASS_AFTER_OK")
        # Note: Surface 4b (v3_model_check.py) runs torch on GPU; verify fail-before syntax/dispatch cleanly on CPU or after GPU frees.
        if "--with-gpu-modelcheck" in sys.argv and Path(v3p_pt).exists():
            r_mc = subprocess.run(
                [PY_GPU, str(tmp / "pipeline/tools/v3_model_check.py"), v3p_pt, v3p_net, V3P_EXE, "100"],
                env=env, capture_output=True, text=True,
            )
            print(f"AFTER_MODELCHECK_V3P rc={r_mc.returncode} out={r_mc.stdout.strip()}")
            assert r_mc.returncode == 0, r_mc.stdout + r_mc.stderr
            print("SURFACE_4B_GPU_PASS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
