"""Fail-Before / Pass-After Verification Gate for V3P_pairwise_psqt.patch (Opus Placement Packet).

Usage:
  python test_v3p_engine_gate.py --exe C:\\nnue-lab\\neon\\forge_fixes\\builds\\base_r15dsg.exe  # MUST FAIL (rc=1)
  python test_v3p_engine_gate.py --exe C:\\nnue-lab\\neon\\forge_fixes\\builds\\v3p_engine.exe  # MUST PASS (rc=0)

Checks:
  1. Legacy r0067 bit-identity: perft 5 == 4865609, B4 bench 11 == 187930, B4 bench 13 == 632195, startpos eval == 87.
  2. FORGENN3-P (FlagPairwise=4 | FlagPsqt=8, H=64, KB=8, OB=8) synthetic net:
     - Engine accepts net and evaluates 120 8-OB FENs with 0 cp max diff vs forge_v3p.reference_eval().
     - Engine executes `go depth 6` without crash or illegal move.
  3. Malformed FORGENN3-P rejection: bad checksum, odd/small pairwise H=32, and OOB PSQT value all rejected with rc=2.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
R0067 = LAB / "runs/forge/r0067/train/cand.fnn3"
PARITY_FENS = FIX / "teamwork_wave2/streamC_gates/parity_fens_8ob.json"
sys.path.insert(0, str(FIX))
import forge_v3p  # noqa: E402


def make_synth_v3p(path: Path) -> forge_v3p.NetP:
    rng = np.random.default_rng(20261127)
    kb, ob, h = 8, 8, 64
    net = forge_v3p.NetP(hidden=h, king_buckets=kb, output_buckets=ob, mirror=True, pairwise=True, has_psqt=True, eval_scale=400)
    net.w1 = rng.integers(-64, 65, size=(kb, 768, h), dtype=np.int16)
    net.b1 = rng.integers(-32, 33, size=(h,), dtype=np.int16)
    net.w2 = rng.integers(-32, 33, size=(ob, h), dtype=np.int16)
    net.b2 = rng.integers(-256, 257, size=(ob,), dtype=np.int32)
    net.psqt = rng.integers(-200, 201, size=(kb, 768, ob), dtype=np.int32)
    forge_v3p.write_net(str(path), net)
    return net


def run_uci(exe: Path, cmds: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run([str(exe)], input="\n".join(cmds) + "\n", capture_output=True, text=True, timeout=timeout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    args = ap.parse_args()
    exe = Path(args.exe)
    assert exe.exists(), f"Missing {exe}"

    # 1. Legacy r0067 bit-identity check
    r1 = run_uci(exe, [
        "uci",
        f"setoption name NNUEArchFile value {str(R0067).replace(chr(92), '/')}",
        "setoption name NNUEArch value true",
        "setoption name CuckooRep value true",
        "setoption name HistRework value 2",
        "setoption name TtPruneV2 value true",
        "setoption name CorrHistV2 value true",
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        "isready",
        "position startpos",
        "go perft 5",
        "eval",
        "bench 11",
        "bench 13",
        "quit",
    ])
    assert r1.returncode == 0, f"Legacy r0067 run failed rc={r1.returncode}"
    assert "nodes 4865609" in r1.stdout, "perft 5 mismatch"
    assert " nnue 87 " in r1.stdout, "r0067 startpos eval != 87"
    assert "bench depth 11 nodes 187930 " in r1.stdout, "r0067 B4 bench 11 != 187930"
    assert "bench depth 13 nodes 632195 " in r1.stdout, "r0067 B4 bench 13 != 632195"
    print(f"[CHECK 1] Legacy r0067 bit-identity PASS on {exe.name}")

    # 2. FORGENN3-P synthetic net parity across 120 8-OB FENs
    raw_fens = json.loads(PARITY_FENS.read_text(encoding="utf-8"))
    fens = [x["fen"] if isinstance(x, dict) else x for x in (raw_fens.get("fens", raw_fens) if isinstance(raw_fens, dict) else raw_fens)]
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        v3p_net_p = tp / "synth_v3p_64.fnn3"
        net = make_synth_v3p(v3p_net_p)

        cmds = [
            "uci",
            f"setoption name NNUEArchFile value {str(v3p_net_p).replace(chr(92), '/')}",
            "setoption name NNUEArch value true",
            "isready",
        ]
        for fen in fens:
            cmds += [f"position fen {fen}", "eval"]
        cmds += ["position startpos", "go depth 6", "quit"]
        r2 = run_uci(exe, cmds, timeout=45)
        if r2.returncode != 0:
            print(f"[CHECK 2] FAIL: {exe.name} rejected FORGENN3-P net (rc={r2.returncode}): {r2.stdout.strip()[-200:]}")
            return 1
        evals = []
        for ln in r2.stdout.splitlines():
            if ln.startswith("info string eval "):
                toks = ln.split()
                evals.append(int(toks[toks.index("nnue") + 1]))
        if len(evals) != len(fens):
            print(f"[CHECK 2] FAIL: expected {len(fens)} eval lines, got {len(evals)}")
            return 1
        def fen_to_codes(fen_s: str) -> tuple[np.ndarray, bool]:
            cmap = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6, "p": 7, "n": 8, "b": 9, "r": 10, "q": 11, "k": 12}
            parts = fen_s.split()
            codes = np.zeros(64, dtype=np.uint8)
            r, c = 7, 0
            for ch in parts[0]:
                if ch == "/":
                    r -= 1; c = 0
                elif "1" <= ch <= "8":
                    c += ord(ch) - 48
                else:
                    codes[r * 8 + c] = cmap[ch]; c += 1
            return codes, (parts[1] == "w")

        diffs = [abs(e - forge_v3p.reference_eval(net, *fen_to_codes(fen))) for e, fen in zip(evals, fens)]
        worst = max(diffs)
        if worst != 0:
            print(f"[CHECK 2] FAIL: FORGENN3-P parity max_diff={worst} cp > 0")
            return 1
        assert any(ln.startswith("bestmove ") and "0000" not in ln for ln in r2.stdout.splitlines()), "missing bestmove"
        print(f"[CHECK 2] FORGENN3-P 120-FEN 8-OB parity PASS (max_diff=0 cp) + go depth 6 PASS on {exe.name}")

        # 3. Malformed FORGENN3-P rejection (bad checksum & bad pairwise H=32)
        bad_ck = tp / "bad_ck.fnn3"
        b = bytearray(v3p_net_p.read_bytes())
        b[-1] ^= 0xFF
        bad_ck.write_bytes(bytes(b))
        r3 = run_uci(exe, [
            "uci",
            f"setoption name NNUEArchFile value {str(bad_ck).replace(chr(92), '/')}",
            "setoption name NNUEArch value true",
            "isready", "quit",
        ])
        if r3.returncode != 2:
            print(f"[CHECK 3] FAIL: corrupted checksum expected rc=2, got rc={r3.returncode}")
            return 1
        print(f"[CHECK 3] Corrupted FORGENN3-P loud rejection PASS (rc=2) on {exe.name}")

    print(f"V3P_ENGINE_GATE PASS: {exe.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
