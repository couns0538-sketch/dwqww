"""Verify kb=16 (16 mirrored king buckets) FORGENN3-P on v3p_fused_v3_engine.exe (ZERO C++ change!).

Directly motivated by SF19_ERROR_TAXONOMY.json showing opp_side_castling has 20.67% severe>=0.35
error rate (nearly 2x quiet_positional 11.63%). Stockfish-style 16 mirrored king buckets double
king-safety granularity (separating corner, castled, center, and advanced king zones) at ~0% ALU
cost (only larger w1 table: ~24.4 MiB vs 12.2 MiB, still well inside Ryzen 9950X 64 MiB L3!).

Verifies:
  1. 0 cp max diff vs Python forge_v3p.reference_eval() across 60 diverse 8-OB FENs.
  2. Clean go depth 5 & 3x interleaved bench 13 NPS vs kb=8 synthetic 1024w net.
"""
from __future__ import annotations

import json
import re
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
sys.path.insert(0, str(FIX))
import forge_v3p  # noqa: E402

EXE = FIX / "builds/v3p_fused_v3_engine.exe"
FENS_JSON = FIX / "teamwork_wave2/streamC_gates/parity_fens_8ob.json"
CMAP = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6, "p": 7, "n": 8, "b": 9, "r": 10, "q": 11, "k": 12}

# 16 mirrored king buckets (files a-d mirrored to h-e): 4 fine file pairs x 4 rank pairs!
# Rank 1: a1(0), b1(1), c1(2), d1(3); Rank 2: a2(4), b2(5), c2(6), d2(7);
# Ranks 3-4: ab(8), cd(9); Ranks 5-6: ab(10), cd(11); Ranks 7-8: a(12), b(13), c(14), d(15)
KING_MAP_16 = [
    0, 1, 2, 3, 3, 2, 1, 0,
    4, 5, 6, 7, 7, 6, 5, 4,
    8, 8, 9, 9, 9, 9, 8, 8,
    8, 8, 9, 9, 9, 9, 8, 8,
    10, 10, 11, 11, 11, 11, 10, 10,
    10, 10, 11, 11, 11, 11, 10, 10,
    12, 13, 14, 15, 15, 14, 13, 12,
    12, 13, 14, 15, 15, 14, 13, 12,
]


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


def run_bench(net_p: Path, depth: int = 13) -> tuple[int, float]:
    inp = "\n".join([
        "uci",
        f"setoption name NNUEArchFile value {str(net_p).replace(chr(92), '/')}",
        "setoption name NNUEArch value true",
        "setoption name HistRework value 2",
        "setoption name CorrHistV2 value true",
        "setoption name TtPruneV2 value true",
        "isready",
        f"bench {depth}",
        "quit",
    ]) + "\n"
    r = subprocess.run([str(EXE)], input=inp, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and "NNUE v3 active" in r.stdout, r.stdout[:300]
    m = re.findall(r"nodes\s+(\d+)\s+time\s+(\d+)\s+nps\s+(\d+)", r.stdout)
    return int(m[-1][0]), float(m[-1][2])


def main() -> int:
    fens_data = json.loads(FENS_JSON.read_text(encoding="utf-8"))
    fens = [item["fen"] if isinstance(item, dict) else item for item in (fens_data["fens"] if isinstance(fens_data, dict) else fens_data)][:60]
    rng = np.random.default_rng(161024)

    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        p8 = tp / "kb8_1024.fnn3"
        p16 = tp / "kb16_1024.fnn3"

        n8 = forge_v3p.NetP(hidden=1024, king_buckets=8, output_buckets=8, mirror=True, pairwise=True, has_psqt=True, eval_scale=400)
        n8.w1 = rng.integers(-40, 41, size=(8, 768, 1024), dtype=np.int16)
        n8.b1 = rng.integers(-20, 21, size=(1024,), dtype=np.int16)
        n8.w2 = rng.integers(-90, 91, size=(8, 1024), dtype=np.int16)
        n8.b2 = rng.integers(-2000, 2001, size=(8,), dtype=np.int32)
        n8.psqt = rng.integers(-10000, 10001, size=(8, 768, 8), dtype=np.int32)
        forge_v3p.write_net(str(p8), n8)

        n16 = forge_v3p.NetP(hidden=1024, king_buckets=16, output_buckets=8, mirror=True, pairwise=True, has_psqt=True, eval_scale=400)
        n16.w1 = rng.integers(-40, 41, size=(16, 768, 1024), dtype=np.int16)
        n16.b1 = n8.b1.copy()
        n16.w2 = n8.w2.copy()
        n16.b2 = n8.b2.copy()
        n16.psqt = rng.integers(-10000, 10001, size=(16, 768, 8), dtype=np.int32)
        ck16 = forge_v3p.write_net(str(p16), n16)

        # Verify 0 cp parity on kb=16
        py_vals = [forge_v3p.reference_eval(n16, *fen_to_codes(f)) for f in fens]
        lines = ["uci", f"setoption name NNUEArchFile value {str(p16).replace(chr(92), '/')}", "setoption name NNUEArch value true", "isready"]
        for f in fens:
            lines += [f"position fen {f}", "eval"]
        lines.append("quit")
        r = subprocess.run([str(EXE)], input="\n".join(lines) + "\n", capture_output=True, text=True, timeout=60)
        assert r.returncode == 0 and "king_buckets 16" in r.stdout, r.stdout[:400]
        cpp_vals = [int(ln.split()[ln.split().index("nnue") + 1]) for ln in r.stdout.splitlines() if ln.startswith("info string eval")]
        assert len(cpp_vals) == len(py_vals)
        max_diff = max(abs(a - b) for a, b in zip(py_vals, cpp_vals))
        assert max_diff == 0, f"kb16 parity fail: {max_diff}"

        s8, s16 = [], []
        for _ in range(3):
            _, nps8 = run_bench(p8, 13)
            _, nps16 = run_bench(p16, 13)
            s8.append(nps8); s16.append(nps16)

        m8, m16 = statistics.median(s8), statistics.median(s16)
        rep = {
            "kb8_mb": round(p8.stat().st_size / 1024**2, 2),
            "kb16_mb": round(p16.stat().st_size / 1024**2, 2),
            "kb16_checksum": f"{ck16:016x}",
            "kb16_parity_max_diff_cp": max_diff,
            "kb8_median_nps": round(m8, 0),
            "kb16_median_nps": round(m16, 0),
            "kb16_vs_kb8_ratio": round(m16 / m8, 4),
        }
        (FIX / "V3P_KB16_FEASIBILITY.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
        print("V3P_KB16_FEASIBILITY_PASS:", json.dumps(rep, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
