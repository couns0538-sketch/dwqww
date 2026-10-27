#!/usr/bin/env python3
"""S-A4 cross-width check: the H512 widened-lock net (`widen_net_sa4.py --mode split`) against the H256 lock net, on the
same FENs, from two nnue_int16_dump outputs (columns: idx float_cp int_cp hce sigW sigB inc_int_bad inc_float_bad).

  python -I -B cross_width_check.py --h256 dump_lock_h256.tsv --h512 dump_split_h512.tsv --out cross.json

Pass: NnueInt16 cp identical on every position (the split is exact in integer arithmetic), the HCE column identical
(same engine evaluation), no incremental mismatches. Reported (not required): float-path differences, which come only
from the float summation order over 512 instead of 256 units."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np


def load(path: Path) -> np.ndarray:
    rows = [[int(x) for x in line.split()] for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    return np.asarray(rows, np.int64)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--h256", type=Path, required=True)
    ap.add_argument("--h512", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.out.exists():
        ap.error("--out must be a new file")
    s, w = load(a.h256), load(a.h512)
    if s.shape != w.shape or not np.array_equal(s[:, 0], w[:, 0]):
        raise SystemExit(f"dumps differ in shape/index: {s.shape} vs {w.shape}")
    n = len(s)
    fd = w[:, 1] - s[:, 1]
    res = {"h256": str(a.h256), "h256_sha256": hashlib.sha256(a.h256.read_bytes()).hexdigest(),
           "h512": str(a.h512), "h512_sha256": hashlib.sha256(a.h512.read_bytes()).hexdigest(), "positions": n,
           "int16_identical": int((w[:, 2] == s[:, 2]).sum()), "hce_identical": int((w[:, 3] == s[:, 3]).sum()),
           "incremental_mismatch_plies_h512": int(w[:, 6].sum() + w[:, 7].sum()),
           "float_h512_vs_h256": {"max_abs_cp": int(np.abs(fd).max()), "mean_abs_cp": float(np.abs(fd).mean()),
                                  "different": int((fd != 0).sum()),
                                  "histogram": {str(k): int(v) for k, v in zip(*np.unique(fd, return_counts=True))}}}
    res["pass"] = res["int16_identical"] == n and res["hce_identical"] == n and res["incremental_mismatch_plies_h512"] == 0
    a.out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"int16 H512(split) == H256 lock {res['int16_identical']}/{n}; hce identical {res['hce_identical']}/{n}; "
          f"incremental mismatches {res['incremental_mismatch_plies_h512']}; float H512 vs H256: max {res['float_h512_vs_h256']['max_abs_cp']} cp, "
          f"{res['float_h512_vs_h256']['different']} differ")
    print("CROSS-WIDTH PASS" if res["pass"] else "CROSS-WIDTH FAIL")
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
