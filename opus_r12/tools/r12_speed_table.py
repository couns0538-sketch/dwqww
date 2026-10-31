#!/usr/bin/env python3
"""r12_speed_table.py - markdown table from r12_speed.py summary.json files (no hand-copied numbers in the report).

  r12_speed_table.py SUMMARY.json [SUMMARY.json ...] [--metric engine_nps] [--names A=v2t1,B=v2t1pt,...]
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--metric", default="engine_nps")
    ap.add_argument("--names", default="")
    a = ap.parse_args()
    names = dict(x.split("=", 1) for x in a.names.split(",") if x)
    nm = lambda t: names.get(t, t)
    print("| net | depth | exe | vs | n blocks | median gain | bootstrap 95% lower bound (1-sided) | 95% CI | per block (%) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for f in a.files:
        s = json.load(open(f, encoding="utf-8"))
        net = "none" if not s["net"] else ("e9_best" if "e9" in s["net"] else "e19_final" if "e19" in s["net"] else s["net"])
        for c in s["comparisons"]:
            if c["metric"] != a.metric:
                continue
            if c["ref"].endswith("'"):
                print("| %s | d%d | %s | its byte copy (A/A) | %d | %+.2f%% | - | - | %s |" % (
                    net, c["depth"], nm(c["x"]), c["n"], 100 * c["median"], " ".join("%+.2f" % (100 * g) for g in c["gains"])))
            else:
                print("| %s | d%d | %s | %s | %d | %+.2f%% | %+.2f%% | [%+.2f%%, %+.2f%%] | %s |" % (
                    net, c["depth"], nm(c["x"]), nm(c["ref"]), c["n"], 100 * c["median"], 100 * c["lb95_one_sided"],
                    100 * c["ci95"][0], 100 * c["ci95"][1], " ".join("%+.2f" % (100 * g) for g in c["gains"])))


if __name__ == "__main__":
    main()
