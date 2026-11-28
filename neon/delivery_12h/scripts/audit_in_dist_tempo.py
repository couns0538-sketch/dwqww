"""Measure exact in-distribution side-to-move tempo M = (eval(pos, stm) + eval(pos, opp)) / 2
across 600 quiet legal positions from runs/forge/val/val.plain for r0067, r0202, G3_e24, G3_e40.
Answers Opus Point 2 (OPUS-2711-G3-READINGS): distinguishes out-of-distribution startpos/1.e4
S2 M = -17.1 cp from true in-distribution tempo across middlegame and endgame positions!
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import chess
import numpy as np

EXE = r"C:\nnue-lab\neon\forge_fixes\builds\v3p_fused_v3_engine.exe"
NETS = {
    "r0067": r"C:\nnue-lab\runs\forge\r0067\train\cand.fnn3",
    "r0202": r"C:\nnue-lab\runs\forge\r0202\train\cand.fnn3",
    "G3_e24": r"C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e24\cand.fnn3",
    "G3_e40": r"C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\cand.fnn3",
}
OUT = Path(r"C:\nnue-lab\neon\forge_fixes\G3_INDIST_TEMPO_AUDIT.json")


def main() -> int:
    pairs = []
    with open(r"C:\nnue-lab\runs\forge\val\val.plain", "r", encoding="ascii", errors="replace") as fh:
        for ln in fh:
            if ln.startswith("fen "):
                f = ln[4:].strip()
                b = chess.Board(f)
                if b.is_check():
                    continue
                b2 = b.copy()
                b2.turn = not b.turn
                b2.ep_square = None
                if b2.is_valid() and not b2.is_check():
                    pairs.append((f, b2.fen(), len(b.piece_map())))
                    if len(pairs) >= 600:
                        break
    pcs = np.array([p[2] for p in pairs])
    res = {"n_pairs": len(pairs), "nets": {}}
    for name, net in NETS.items():
        net_posix = net.replace("\\", "/")
        lines = [
            "uci",
            f"setoption name NNUEArchFile value {net_posix}",
            "setoption name NNUEArch value true",
            "isready",
        ]
        for f1, f2, _ in pairs:
            lines += [f"position fen {f1}", "eval", f"position fen {f2}", "eval"]
        lines.append("quit")
        r = subprocess.run([EXE], input="\n".join(lines) + "\n", capture_output=True, text=True, check=True)
        vals = [
            int(ln.split()[ln.split().index("total") + 1])
            for ln in r.stdout.splitlines()
            if ln.startswith("info string eval")
        ]
        e1 = np.array(vals[0::2], dtype=float)
        e2 = np.array(vals[1::2], dtype=float)
        tempo = 0.5 * (e1 + e2)
        res["nets"][name] = {
            "mean_M_raw": round(float(tempo.mean()), 2),
            "median_M_raw": round(float(np.median(tempo)), 2),
            "pct_positive_M": round(100.0 * float((tempo > 0).mean()), 1),
            "mg_ge20_mean_M_raw": round(float(tempo[pcs >= 20].mean()), 2),
            "mid_11_19_mean_M_raw": round(float(tempo[(pcs >= 11) & (pcs < 20)].mean()), 2),
            "eg_le10_mean_M_raw": round(float(tempo[pcs <= 10].mean()), 2),
        }
        print(f"{name:7s}: {res['nets'][name]}")
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
