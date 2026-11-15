#!/usr/bin/env python3
"""Turn a run_engine.py result into a compact per-case TSV (one row per case,
the engine's own final bestmove, score and last info line) so the evidence file
stays readable and small while still holding every case.
"""

import json
import sys

src = sys.argv[1]
dst = sys.argv[2]
d = json.load(open(src))
with open(dst, "w") as f:
    f.write(f"# engine={d['engine']} mode={d['mode']} limit={d['limit']} hash={d['hash']} "
            f"cases_file={d['cases_file']}\n")
    f.write("# i\ts0\tmoves\twant\tscore\tbestmove\tplayed_k\n")
    for r in d["records"]:
        last = r["searches"][-1] if r.get("searches") else {}
        info = last.get("info") or ""
        sc = ""
        if " score " in info:
            t = info.split()
            i = t.index("score")
            sc = t[i + 1] + " " + t[i + 2]
        f.write(f"{r['i']}\t{r['s0']}\t{' '.join(r['moves'])}\t{r['want']}\t{sc}\t"
                f"{last.get('best')}\t{r.get('played_k')}\n")
print("wrote", dst)
