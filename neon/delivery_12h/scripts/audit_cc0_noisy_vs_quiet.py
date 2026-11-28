"""Forensic audit of cc0_shards_4k_v2_nodrawconf quiet (bit0=0) vs noisy (bit0=1) rows.
Explains why G3b_cc0_skip_noisy crushed G3a_cc0_keep_noisy by +699.72 Elo (972-21-7)
and OLS Q collapsed to 199.3 cp in G3a vs 1016.0 cp in G3b!
"""
from __future__ import annotations

import json
import zlib
from pathlib import Path

import numpy as np

FQS_DTYPE = np.dtype([
    ("packed", np.uint8, (32,)),
    ("stm", np.uint8),
    ("score16", np.int16),
    ("res8", np.int8),
    ("flags", np.uint8),
    ("weight_u8", np.uint8),
])
SHARD_DIR = Path(r"C:\nnue-lab\neon\forge_fixes\cc0_shards_4k_v2_nodrawconf")
OUT = Path(r"C:\nnue-lab\neon\forge_fixes\CC0_NOISY_VS_QUIET_FORENSIC.json")


def main() -> int:
    arrs = [np.frombuffer(zlib.decompress(p.read_bytes()), dtype=FQS_DTYPE, offset=8) for p in sorted(SHARD_DIR.glob("*.fqs.z"))]
    a = np.concatenate(arrs)
    val = np.array([0, 1, 3, 3, 5, 9, 0, -1, -3, -3, -5, -9, 0], dtype=np.int32)
    sl = a[::5]
    codes = np.empty((len(sl), 64), dtype=np.uint8)
    codes[:, 0::2] = sl["packed"] & 15
    codes[:, 1::2] = sl["packed"] >> 4
    w_mat = val[codes].sum(axis=1)
    stm_mat = np.where(sl["stm"] == 0, w_mat, -w_mat)
    sc = sl["score16"].astype(np.float64)
    res = sl["res8"].astype(np.float64)
    noisy = (sl["flags"] & 1) != 0
    chk = (sl["flags"] & 2) != 0

    rep = {
        "total_rows": int(len(a)),
        "noisy_pct": round(100.0 * float(((a["flags"] & 1) != 0).mean()), 2),
        "chk_pct": round(100.0 * float(((a["flags"] & 2) != 0).mean()), 2),
        "groups": {},
    }
    for name, m in [("quiet_bit0_0", ~noisy & ~chk), ("noisy_bit0_1", noisy & ~chk), ("all_noncheck", ~chk)]:
        eq = m & (np.abs(sc) < 100)
        hang3 = eq & (np.abs(stm_mat) >= 3)
        hang8 = eq & (np.abs(stm_mat) >= 8)
        # Also check OPPOSITE sign: stm_mat <= -3 yet sc >= +100 (down a piece statically, winning via capture!)
        opp_sign = m & (((stm_mat <= -3) & (sc >= 100)) | ((stm_mat >= 3) & (sc <= -100)))
        rep["groups"][name] = {
            "sampled_n": int(m.sum()),
            "corr_mat_sc": round(float(np.corrcoef(stm_mat[m], sc[m])[0, 1]), 4),
            "corr_mat_res": round(float(np.corrcoef(stm_mat[m], res[m])[0, 1]), 4),
            "corr_sc_res": round(float(np.corrcoef(sc[m], res[m])[0, 1]), 4),
            "mean_abs_stm_mat": round(float(np.abs(stm_mat[m]).mean()), 3),
            "pct_eq_sc_with_mat_ge3": round(100.0 * float(hang3.sum()) / max(1, int(eq.sum())), 2),
            "pct_eq_sc_with_mat_ge8": round(100.0 * float(hang8.sum()) / max(1, int(eq.sum())), 2),
            "pct_opposite_mat_vs_sc_ge3": round(100.0 * float(opp_sign.sum()) / max(1, int(m.sum())), 2),
            "mean_stm_mat": round(float(stm_mat[m].mean()), 3),
            "mean_sc": round(float(sc[m].mean()), 1),
        }
    OUT.write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
