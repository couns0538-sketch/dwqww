#!/usr/bin/env python3
"""S20: aggregate the per-chunk statistics of an opus_rescore.py run (progress.json) and hash the joined output.

usage: python -I -B opus_rescore_summary.py --run <rescore out dir> --out <new json file>
Prints a short table; writes the totals, the merged |new - old| histogram (100 cp bins), the merged sign counts,
the per-chunk sha256 and seconds, and the sha256/size of <run>/rescored.txt. Read-only on the run directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.out.exists():
        raise SystemExit(f"refusing to overwrite {a.out}")
    prog = json.loads((a.run / "progress.json").read_text(encoding="utf-8"))
    chunks = prog["chunks"]
    names = sorted(chunks)
    tot = Counter()
    hist = Counter()
    sign = Counter()
    seconds = 0.0
    delta_abs_max = 0
    per_chunk = []
    for n in names:
        c = chunks[n]
        for k in ("lines", "lines_in", "bad_lines", "clipped", "mates", "delta_sum", "delta_abs_sum"):
            tot[k] += c[k]
        delta_abs_max = max(delta_abs_max, c["delta_abs_max"])
        hist.update({int(k): v for k, v in c["hist_100cp"].items()})
        sign.update(c["sign"])
        seconds += c["seconds"]
        per_chunk.append({"chunk": n, "lines": c["lines"], "seconds": c["seconds"], "sha256": c["sha256"],
                          "first_input_line": c["first_input_line"]})
    joined = a.run / "rescored.txt"
    out = {
        "params": prog["params"], "engine_id": prog.get("engine_id"),
        "chunks": len(names), "lines": tot["lines"], "lines_in": tot["lines_in"], "bad_lines": tot["bad_lines"],
        "clipped": tot["clipped"], "mates": tot["mates"],
        "delta_mean": tot["delta_sum"] / max(1, tot["lines"]), "delta_abs_mean": tot["delta_abs_sum"] / max(1, tot["lines"]),
        "delta_abs_max": delta_abs_max, "hist_100cp": dict(sorted(hist.items())), "sign": dict(sign),
        "engine_seconds_sum": seconds, "positions_per_second": tot["lines"] / seconds if seconds else None,
        "per_chunk": per_chunk,
        "rescored_txt": ({"bytes": joined.stat().st_size, "sha256": sha256_file(joined)} if joined.exists() else None),
    }
    a.out.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"chunks {out['chunks']}, lines {out['lines']:,} (in {out['lines_in']:,}), bad {out['bad_lines']}, "
          f"clipped {out['clipped']}, mates {out['mates']:,}")
    print(f"new - old: mean {out['delta_mean']:+.2f} cp, mean |d| {out['delta_abs_mean']:.2f} cp, max |d| {delta_abs_max}")
    print(f"sign: {out['sign']}")
    print(f"time: {seconds:,.0f} s summed over chunks = {out['positions_per_second']:.1f} positions/s")
    if out["rescored_txt"]:
        print(f"rescored.txt: {out['rescored_txt']['bytes']:,} bytes, sha256 {out['rescored_txt']['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
