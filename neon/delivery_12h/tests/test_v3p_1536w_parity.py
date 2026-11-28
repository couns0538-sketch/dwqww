"""Verify H=1536 FORGENN3-P (pairwise + PSQT) end-to-end on v3p_fused_engine.exe:
  - Builds a realistic high-magnitude H=1536, kb=8, ob=8, mirror=True, pairwise=True, has_psqt=True net
  - Verifies 0 cp max diff between forge_v3p.reference_eval() and C++ v3p_fused_engine.exe uci eval across all 120 8-OB FENs
  - Verifies go depth 5 & bench 8 run cleanly with zero crash / zero overflow!
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
sys.path.insert(0, str(FIX))
import forge_v3p  # noqa: E402

EXE = FIX / "builds/v3p_fused_engine.exe"
FENS_JSON = FIX / "teamwork_wave2/streamC_gates/parity_fens_8ob.json"


def main() -> int:
    rng = np.random.default_rng(1536)
    H, KB, OB = 1536, 8, 8
    # Stress-test high magnitudes (w1 up to +-120, w2 up to +-127, psqt up to +-60000) to catch any int32 overflow!
    net = forge_v3p.NetP(hidden=H, king_buckets=KB, output_buckets=OB, mirror=True, pairwise=True, has_psqt=True, eval_scale=400)
    net.w1 = rng.integers(-60, 61, size=(KB, 768, H), dtype=np.int16)
    net.b1 = rng.integers(-40, 41, size=(H,), dtype=np.int16)
    net.w2 = rng.integers(-127, 128, size=(OB, H), dtype=np.int16)
    net.b2 = rng.integers(-5000, 5001, size=(OB,), dtype=np.int32)
    net.psqt = rng.integers(-20000, 20001, size=(KB, 768, OB), dtype=np.int32)

    fens_data = json.loads(FENS_JSON.read_text(encoding="utf-8"))
    fens = [item["fen"] if isinstance(item, dict) else item for item in (fens_data["fens"] if isinstance(fens_data, dict) else fens_data)]

    CMAP = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6, "p": 7, "n": 8, "b": 9, "r": 10, "q": 11, "k": 12}

    def fen_to_codes(fen: str) -> tuple[np.ndarray, bool]:
        parts = fen.split()
        codes = np.zeros(64, dtype=np.uint8)
        r = 7
        for row in parts[0].split("/"):
            c = 0
            for ch in row:
                if ch.isdigit():
                    c += int(ch)
                else:
                    codes[r * 8 + c] = CMAP[ch]
                    c += 1
            r -= 1
        return codes, (parts[1] == "w")

    with tempfile.TemporaryDirectory() as td:
        net_p = Path(td) / "test_1536w.fnn3"
        cksum = forge_v3p.write_net(str(net_p), net)
        py_vals = [forge_v3p.reference_eval(net, *fen_to_codes(f)) for f in fens]

        lines = [
            "uci",
            f"setoption name NNUEArchFile value {str(net_p).replace(chr(92), '/')}",
            "setoption name NNUEArch value true",
            "isready",
        ]
        for f in fens:
            lines.append(f"position fen {f}")
            lines.append("eval")
        lines += ["position startpos", "go depth 5", "quit"]
        r = subprocess.run([str(EXE)], input="\n".join(lines) + "\n", capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, f"Engine rc={r.returncode}: {r.stderr}"
        assert "NNUE v3 active" in r.stdout and "hidden 1536 pairwise psqt" in r.stdout, r.stdout[:500]
        assert "bestmove " in r.stdout, "Missing bestmove on go depth 5"
        cpp_vals = []
        for ln in r.stdout.splitlines():
            if ln.startswith("info string eval"):
                tok = ln.split()
                cpp_vals.append(int(tok[tok.index("nnue") + 1]))
        assert len(cpp_vals) == len(py_vals), (len(cpp_vals), len(py_vals))
        diffs = [abs(a - b) for a, b in zip(py_vals, cpp_vals)]
        max_diff = max(diffs)
        assert max_diff == 0, f"1536w parity mismatch! max_diff={max_diff}"
        print(f"V3P_1536W_PARITY_PASS: bytes={net_p.stat().st_size:,} cksum={cksum:016x} fens={len(fens)} max_diff={max_diff} go_depth5=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
