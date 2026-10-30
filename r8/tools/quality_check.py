"""R8 quality check of self-play text output ("FEN | cp | result"; result = White's), read only.
usage: python -I -B quality_check.py <name>=<file.txt>[,<file2.txt>] [<name>=...] [--json out.json]
Per data set: records; side to move share; score mean / std / median |cp| and the share in |cp| bands
(<=50, <=200, <=600, <=1500, <=3000); White-result shares (game outcome of each record), and the score sign vs
result agreement; full-move number mean and quartiles; duplicate rate on the first four FEN fields (inside the set
after its own de-duplication, so ~0 is expected) and the overlap between data sets. Sets are compared side by side."""
import json
import math
import statistics
import sys

sets = []
for a in sys.argv[1:]:
    if a.startswith("--"):
        break
    name, _, files = a.partition("=")
    sets.append((name, files.split(",")))
out_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else ""
keysets = {}
report = {}
for name, files in sets:
    cps, results, fulls, stm_black = [], [], [], 0
    keys = set()
    dups = 0
    agree = 0
    for fn in files:
        with open(fn, encoding="ascii") as f:
            for line in f:
                fen, cp, res = (x.strip() for x in line.split("|"))
                parts = fen.split()
                k = " ".join(parts[:4])
                if k in keys:
                    dups += 1
                keys.add(k)
                c = int(cp)
                r = float(res)
                cps.append(c)
                results.append(r)
                fulls.append(int(parts[5]))
                black = parts[1] == "b"
                stm_black += black
                white_cp = -c if black else c
                if (white_cp > 0 and r == 1.0) or (white_cp < 0 and r == 0.0) or (white_cp == 0 and r == 0.5):
                    agree += 1
    n = len(cps)
    a = [abs(c) for c in cps]
    bands = {f"<={b}": sum(1 for x in a if x <= b) / n for b in (50, 200, 600, 1500, 3000)}
    q = statistics.quantiles(fulls, n=4)
    rep = {
        "records": n, "black_to_move": stm_black / n,
        "cp_mean": statistics.mean(cps), "cp_std": statistics.pstdev(cps), "abs_cp_median": statistics.median(a),
        "abs_cp_bands": bands,
        "white_win": results.count(1.0) / n, "draw": results.count(0.5) / n, "white_loss": results.count(0.0) / n,
        "score_sign_agrees_with_result": agree / n,
        "fullmove_mean": statistics.mean(fulls), "fullmove_quartiles": q,
        "duplicates_inside": dups, "duplicate_rate_inside": dups / n,
    }
    report[name] = rep
    keysets[name] = keys
names = [s[0] for s in sets]
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        inter = len(keysets[names[i]] & keysets[names[j]])
        report[f"overlap {names[i]}~{names[j]}"] = {"shared_positions": inter,
                                                     f"share_of_{names[i]}": inter / len(keysets[names[i]]),
                                                     f"share_of_{names[j]}": inter / len(keysets[names[j]])}
w = 34
print("metric".ljust(w) + "".join(n.rjust(18) for n in names))
for key in ("records", "black_to_move", "cp_mean", "cp_std", "abs_cp_median", "white_win", "draw", "white_loss",
            "score_sign_agrees_with_result", "fullmove_mean", "duplicate_rate_inside"):
    print(key.ljust(w) + "".join(f"{report[n][key]:18.4f}" if isinstance(report[n][key], float) else f"{report[n][key]:18d}" for n in names))
for b in ("<=50", "<=200", "<=600", "<=1500", "<=3000"):
    print(f"abs_cp {b}".ljust(w) + "".join(f"{report[n]['abs_cp_bands'][b]:18.4f}" for n in names))
print("fullmove quartiles".ljust(w) + "".join(("/".join(f"{x:.0f}" for x in report[n]["fullmove_quartiles"])).rjust(18) for n in names))
for k, v in report.items():
    if k.startswith("overlap"):
        print(k, v)
if out_json:
    with open(out_json, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=1)
