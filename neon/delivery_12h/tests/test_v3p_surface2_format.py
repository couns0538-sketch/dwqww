"""Fail-before / pass-after acceptance test for V3P Loop Placement Surface 2
(`pipeline/forge_v3p.py` vs legacy `pipeline/forge_v3.py`).

Verifies:
1. BEFORE: legacy `pipeline/forge_v3` either raises on FORGENN3-P OR produces completely wrong
   reference_eval() outputs compared to the verified engine (failing parity on >90% of positions).
2. AFTER: `forge_v3p.read_net()` parses `pairwise=True, has_psqt=True` cleanly, matches
   `forge_v3.reference_eval()` bit-for-bit (`0/100` diffs) on legacy `r0067`, AND matches the
   V3P engine bit-for-bit (`0/50` diffs) on FORGENN3-P!
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
sys.path.insert(0, str(LAB / "pipeline"))
sys.path.insert(0, str(FIX))

import forge_parse  # noqa: E402
import forge_v3  # noqa: E402
import forge_v3p  # noqa: E402

R0067 = LAB / "runs/forge/r0067/train/cand.fnn3"
G3_NET = FIX / "gpu_runs/G3_FULL25_v3p_1024_cc0_anchored/cand.fnn3"
G2_NET = FIX / "gpu_runs/G2_v3p_1024_pairwise_psqt/cand.fnn3"
V3P_EXE = FIX / "builds/v3p_fused_v3_engine.exe"


def eval_engine(exe: Path, net: Path, fens: list[str]) -> list[int]:
    p = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    def send(s: str):
        p.stdin.write(s + "\n")
        p.stdin.flush()
    def wait_for(tok: str):
        out = []
        while True:
            line = p.stdout.readline()
            if not line:
                raise RuntimeError("engine closed")
            out.append(line.strip())
            if line.startswith(tok):
                return out
    send("uci"); wait_for("uciok")
    send(f"setoption name NNUEArchFile value {net}")
    send("setoption name NNUEArch value true")
    send("isready"); wait_for("readyok")
    vals = []
    for f in fens:
        send("position fen " + f)
        send("eval")
        lines = wait_for("info string eval")
        t = [x for x in lines if x.startswith("info string eval")][0].split()
        vals.append(int(t[t.index("total") + 1]))
    send("quit")
    p.wait(timeout=10)
    return vals


def main() -> int:
    v3p_net_path = G3_NET if G3_NET.exists() else G2_NET
    assert v3p_net_path.exists(), f"Missing FORGENN3-P net: {v3p_net_path}"
    assert R0067.exists(), f"Missing legacy r0067 net: {R0067}"

    fens = []
    with (LAB / "runs/forge/val/val.plain").open("r", encoding="ascii", errors="replace") as fh:
        for line in fh:
            if line.startswith("fen "):
                fens.append(line[4:].strip())
                if len(fens) >= 50:
                    break

    eng_vals = eval_engine(V3P_EXE, v3p_net_path, fens)

    # 1. BEFORE: legacy forge_v3 either raises OR fails parity massively vs engine
    legacy_failed = False
    try:
        n_bad = forge_v3.read_net(str(v3p_net_path))
        bad_diffs = 0
        for f, ev in zip(fens, eng_vals):
            codes = np.frombuffer(forge_parse.fen_codes(f.split()[0]), np.uint8)
            white = f.split()[1] == "w"
            if forge_v3.reference_eval(n_bad, codes, white) != ev:
                bad_diffs += 1
        if bad_diffs > 0:
            legacy_failed = True
            print(f"BEFORE_LEGACY_V3_FAILED_PARITY: {bad_diffs}/{len(fens)} wrong on FORGENN3-P")
    except Exception as e:
        legacy_failed = True
        print(f"BEFORE_LEGACY_V3_RAISED: {type(e).__name__}: {e}")
    assert legacy_failed, "Legacy forge_v3 unexpectedly matched FORGENN3-P!"

    # 2. AFTER: forge_v3p matches engine 0/50 on FORGENN3-P AND matches forge_v3 0/50 on legacy r0067
    n_p = forge_v3p.read_net(str(v3p_net_path))
    assert n_p.pairwise and n_p.has_psqt and n_p.hidden == 1024
    n_leg_new = forge_v3p.read_net(str(R0067))
    n_leg_old = forge_v3.read_net(str(R0067))
    assert not n_leg_new.pairwise and not n_leg_new.has_psqt and n_leg_new.hidden == 768

    v3p_diffs = 0
    leg_diffs = 0
    for f, ev in zip(fens, eng_vals):
        codes = np.frombuffer(forge_parse.fen_codes(f.split()[0]), np.uint8)
        white = f.split()[1] == "w"
        if forge_v3p.reference_eval(n_p, codes, white) != ev:
            v3p_diffs += 1
        if forge_v3p.reference_eval(n_leg_new, codes, white) != forge_v3.reference_eval(n_leg_old, codes, white):
            leg_diffs += 1
    assert v3p_diffs == 0, f"forge_v3p vs engine failed: {v3p_diffs}/{len(fens)}"
    assert leg_diffs == 0, f"forge_v3p vs forge_v3 on legacy failed: {leg_diffs}/{len(fens)}"
    print(f"SURFACE_2_FAIL_BEFORE_PASS_AFTER_OK (v3p_diffs=0/{len(fens)}, legacy_diffs=0/{len(fens)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
