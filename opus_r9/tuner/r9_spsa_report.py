"""R9: report of an r9_spsa.py run (read only on the run folder; writes into --out).
usage: python -I -B r9_spsa_report.py <run_dir> --out <dir> [--exe <forge.exe as QA names it>] [--title TEXT]
Per tuned parameter: start, end (theta, float) and end as the engine integer, the move in units and in c_end, the
noise level and z = move / noise, and whether both halves of the run moved the same way.
Noise level = the spread the same run would have shown with NO true gradient: under that null every batch adds
a_k/c_k * R * delta with R = wins - losses of plus, E[R] = 0 and Var[R] = games * v, where v = (W + L) / G -
((W - L) / G)^2 is the per-game variance of the observed results. So sigma_i = sqrt(sum_b (a_k/c_k)_bi^2 * games_b * v).
|z| >= 2 is called "likely real" (beyond the null spread); with many parameters about 1 in 20 passes by chance.
Writes <out>/R9_RESULTS.md, r9_tuned.ini, r9_tuned_options.txt (fastchess option string), r9_params.json."""
import json
import math
import sys
from pathlib import Path

run_dir = Path(sys.argv[1])
out = Path(sys.argv[sys.argv.index("--out") + 1])
exe = sys.argv[sys.argv.index("--exe") + 1] if "--exe" in sys.argv else None
title = sys.argv[sys.argv.index("--title") + 1] if "--title" in sys.argv else f"SPSA run {run_dir.name}"
cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
recs = [json.loads(x) for x in (run_dir / "iterations.jsonl").read_text(encoding="ascii").splitlines()
        if x.strip().startswith("{")]
recs = [r for r in recs if "theta_after" in r]
if not recs:
    raise SystemExit("no finished batches")
params = cfg["params"]
names = [p["name"] for p in params]
W = sum(r["W"] for r in recs)
L = sum(r["L"] for r in recs)
D = sum(r["D"] for r in recs)
G = W + L + D
v = (W + L) / G - ((W - L) / G) ** 2
half = len(recs) // 2
rows = []
for i, p in enumerate(params):
    n = p["name"]
    start = recs[0]["theta_before"][n]
    end = recs[-1]["theta_after"][n]
    mid = recs[half - 1]["theta_after"][n] if half > 0 else start
    sigma = math.sqrt(sum(r["a_over_c"][i] ** 2 * 2 * r["pairs"] * v for r in recs))
    move = end - start
    z = move / sigma if sigma > 0 else 0.0
    first, second = mid - start, end - mid
    same_way = first * second > 0
    end_int = int(round(min(max(end, p["min"]), p["max"])))
    rows.append({"name": n, "start": start, "end": round(end, 3), "end_int": end_int, "move": round(move, 3),
                 "move_c_end": round(move / p["c_end"], 2), "sigma": round(sigma, 3), "z": round(z, 2),
                 "first_half": round(first, 3), "second_half": round(second, 3), "same_way": same_way,
                 "likely_real": abs(z) >= 2, "c_end": p["c_end"], "min": p["min"], "max": p["max"],
                 "lock_default": p.get("lock_default", start)})
out.mkdir(parents=True, exist_ok=True)
changed = [r for r in rows if r["end_int"] != int(round(r["start"]))]
real = [r for r in rows if r["likely_real"]]
opt_all = " ".join(["option.R9Tune=true"] + [f"option.{r['name']}={r['end_int']}" for r in changed])
opt_real = " ".join(["option.R9Tune=true"] + [f"option.{r['name']}={r['end_int']}" for r in real])
first_t, last_t = recs[0]["time"], recs[-1]["time"]
pairs = recs[-1]["k_after"] - recs[0]["k_before"]
terms = {}
for r in recs:
    for t, c in r["terminations"].items():
        terms[t] = terms.get(t, 0) + c
lines = [f"# {title}", "",
         f"Run `{run_dir}`: {len(recs)} batches, {pairs} game pairs = {G} games ({first_t} .. {last_t}), tc {cfg['tc']},"
         f" engine `{cfg['engine']}`, planned pairs {cfg['pairs_planned']}, {cfg['pairs_per_batch']} pairs per batch.",
         f"Results of plus vs minus: +{W} -{L} ={D} (draws {100 * D / G:.1f}%), per-game result variance v = {v:.3f};"
         f" terminations {terms}.", "",
         "| parameter | start | end | end (int) | move | move / c_end | noise sigma | z | halves | verdict |",
         "|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    verdict = "likely real" if r["likely_real"] else "noise"
    halves = "same way" if r["same_way"] else "mixed"
    lines.append(f"| {r['name']} | {r['start']:g} | {r['end']:.2f} | {r['end_int']} | {r['move']:+.2f} | {r['move_c_end']:+.2f} |"
                 f" {r['sigma']:.2f} | {r['z']:+.2f} | {halves} | {verdict} |")
lines += ["", f"{len(real)} of {len(rows)} parameters moved beyond 2 sigma (expected by chance: about {len(rows) / 20:.1f}).",
          f"Changed integers: {len(changed)}.", "", "Fastchess options of the tuned side (all changed parameters):", "",
          f"`{opt_all}`", "", "Only the likely-real ones:", "", f"`{opt_real}`", ""]
if exe:
    lines += ["QA gate line (tuned options vs the same exe at defaults):", "",
              f"`-engine name=r9_tuned cmd={exe} {opt_all} -engine name=r9_default cmd={exe}`", ""]
(out / "R9_RESULTS.md").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
ini = ["; R9 SPSA result: tuned values of the R9Tune options (" + f"{pairs} pairs, {first_t} .. {last_t})",
       "; set R9Tune=true and these options; every other tunable stays at the lock value", "[forge_r9]", "R9Tune=true"]
ini += [f"{r['name']}={r['end_int']}" for r in changed]
(out / "r9_tuned.ini").write_bytes(("\n".join(ini) + "\n").encode("ascii"))
(out / "r9_tuned_options.txt").write_bytes((opt_all + "\n").encode("ascii"))
(out / "r9_params.json").write_bytes((json.dumps({"run": str(run_dir), "batches": len(recs), "pairs": pairs, "W": W, "L": L,
                                                   "D": D, "v": v, "params": rows}, indent=1) + "\n").encode("ascii"))
print("\n".join(lines))
