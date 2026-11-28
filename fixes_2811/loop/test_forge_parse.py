"""Check that the parallel .plain reader gives exactly the arrays of the one-process reader.

Compares forge_parse.parse_file() on a round's filtered.plain with the cache the old one-process
reader wrote next to it (<file>.cache.npz). Usage:
    python test_forge_parse.py <filtered.plain> [processes=16]
Exit code 0 only if every array is equal.
"""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import forge_parse  # noqa: E402


def main() -> int:
    path = sys.argv[1]
    procs = int(sys.argv[2]) if len(sys.argv) > 2 else 16
    z = np.load(path + ".cache.npz", allow_pickle=False)
    t0 = time.time()
    d = forge_parse.parse_file(path, r"C:\nnue-lab\forge\build\hce_dump.exe", True, True, procs)
    dt = time.time() - t0
    ok = True
    for k in ("codes", "stm", "score", "res", "hce"):
        same = d[k].shape == z[k].shape and d[k].dtype == z[k].dtype and np.array_equal(d[k], z[k])
        ok &= bool(same)
        print(f"{k:6s} new {d[k].shape} {d[k].dtype}  old {z[k].shape} {z[k].dtype}  equal {same}")
    print(f"records all/marked/noisy/in check: {d['counts'].tolist()}; {len(forge_parse.slices(path, procs))} slices, "
          f"{procs} processes, {dt:.1f} s")
    print("RESULT:", "IDENTICAL" if ok else "DIFFERENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
