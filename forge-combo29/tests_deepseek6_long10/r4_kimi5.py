#!/usr/bin/env python3
"""r4_kimi5.py -- R4 of long 10: reproduce kimi5's job-5 settings and compare.

Usage: r4_kimi5.py [--exe PATH]
For each of kimi5's runs_O/runs_G json files it reads the exact setopts kimi5 sent and
re-runs the same set at depth 12 with the same options (plus Threads 1, Hash 16,
OwnBook false, which kimi5 also used), writing runs/<set>_<config>.rows and printing
"config | set | kimi5 sum | mine | nodes-eq | bm-eq".
"""
import argparse
import json
import os
import subprocess
import sys

CONFIGS = ["none", "smp", "pv", "chk", "mat", "pvchk", "off7", "cnt", "cntsmp",
           "mask0", "mask1", "pvmask1"]


def load_kimi(path):
    d = json.load(open(path))
    return d.get("setopts", []), {r["pos"]: r for r in d.get("records", [])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="/agent/repos/work/build-l10/forge")
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    os.makedirs("runs", exist_ok=True)
    out = open("r4_table.txt", "a", encoding="utf-8")

    for setname in ("O", "G"):
        setfile = "first200.fens" if setname == "O" else "set_G.epd"
        n = 200 if setname == "O" else 353
        for cfg in CONFIGS:
            kpath = "kimi5_rows/%s_%s.json" % (setname, cfg)
            if not os.path.exists(kpath):
                continue
            setopts, recs = load_kimi(kpath)
            # turn "setoption name X value Y" into rows.py's "X=Y" form
            pairs = []
            for line in setopts:
                parts = line.split()
                if parts[:2] == ["setoption", "name"] and "value" in parts:
                    i = parts.index("value")
                    pairs.append("%s=%s" % (" ".join(parts[2:i]), " ".join(parts[i + 1:])))
            rf = "runs/%s_%s.rows" % (setname, cfg)
            opts = ";".join(pairs)
            subprocess.run([sys.executable, "rows.py", "--exe", args.exe, "--set", setfile,
                            "--out", rf, "--opts", opts, "--depth", "12"],
                           capture_output=True, text=True)
            mine = {}
            for line in open(rf, encoding="utf-8"):
                if line.startswith("#") or not line.strip():
                    continue
                p = [x.strip() for x in line.split("|")]
                if len(p) == 3:
                    mine[int(p[0])] = (int(p[1]), p[2])
            ksum = sum(r["nodes"] for r in recs.values())
            msum = sum(v[0] for v in mine.values())
            common = sorted(set(mine) & set(recs))
            ne = sum(1 for i in common if mine[i][0] == recs[i]["nodes"])
            # kimi5's json may omit bestmove for some rows
            be = sum(1 for i in common if recs[i].get("bestmove") and mine[i][1] == recs[i]["bestmove"])
            bknown = sum(1 for i in common if recs[i].get("bestmove"))
            line = ("%s | %s | %d | %d | %d of %d | %d of %d"
                    % (cfg, setname, ksum, msum, ne, len(common), be, bknown))
            print(line, flush=True)
            out.write(line + "\n"); out.flush()
    out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
