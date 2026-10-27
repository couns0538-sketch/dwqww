"""Markdown tables for the S44 report from s44_results.json (usage: make_s44_tables.py <s44_results.json>)."""
import json
import sys


def f(x, digits=2):
    return "—" if x is None else f"{x:+.{digits}f}"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    pts, bias = d["points"], d["bias"]
    order = {"h256_e12 conc5": 0, "h256_e12 conc7": 1, "AL1 conc8": 2}
    pts = sorted(pts, key=lambda g: (order.get(g["group"], 9), g["family"] != "b06", g["epochs"], g["gate"]))
    print("### Gate points (one per gate, unpooled)\n")
    print("| gate | group | net run (epochs, data) | holdout b0.6 | dL vs opp (1e-4) | games | verdict | Elo ± 95% | "
          "bias-adjusted Elo ± SE | verdict-cond. bias at adj | citation |")
    print("|---|---|---|---:|---:|---:|---|---:|---:|---:|---|")
    for g in pts:
        b = bias[g["gate"]]
        snap = g["snapshot_1335"]
        parts = []
        if snap.get("GATE_RESULTS.csv"):
            parts.append(f"snapshot csv:{snap['GATE_RESULTS.csv']} md:{snap['GATE_RESULTS.md']} html:{snap['GATE_RESULTS.html']}")
        if g["lgf_line"]:
            parts.append(f"LGF:{g['lgf_line']}")
        parts.append(f"RESULT.md {g['result_md_sha256'][:8]}")
        cite = "; ".join(parts)
        fam = "" if g["family"] == "b06" else f" ({g['family']}, not fitted)"
        run = g["run"].replace("resid_h256_", "")
        print(f"| {g['gate']} | {g['group']} | {run} (e{g['epochs']}, {g['train_positions'] / 1e6:.1f}M){fam} | "
              f"{g['holdout_b06']:.6f} | {g['dL_1e4']:+.2f} | {g['games']} | {g['verdict']} | "
              f"{g['elo']:+.2f} ± {g['elo_err']:.2f} | "
              + (f"{b['adj']:+.2f} ± {b['adj_se']:.2f}" if b.get("adj") is not None else "—")
              + f" | {f(b.get('cond_bias_at_adj'))} | {cite} |")
    print("\n### Stopping-rule simulation checks\n")
    print("| gate | reps per Elo | Elo grid | exact LLR rows | max crossing-hiding drift (band 0.3) | degenerate rows | "
          "cap-cond. bias at true +10 |")
    print("|---|---:|---|---:|---:|---:|---:|")
    for g in pts:
        b = bias[g["gate"]]
        st = b["exact_llr_stats"]
        th = b["thetas"]
        print(f"| {g['gate']} | {b['reps']} | {th[0]:+.0f}..{th[-1]:+.0f} ({len(th)}) | {st['exact_rows']:,} | "
              f"{st['max_unsafe_drift']:.3f} | {st['degenerate_rows']} | {f(b.get('cond_bias_at_true10'))} |")
    print("\n### Fits: Elo = (c +) k * dL, dL in 1e-4 holdout b0.6 (b0.6 family only)\n")
    print("| group | Elo used | model | n | k (Elo per 1e-4) ± SE | c ± SE | chi2/dof | SE inflation |")
    print("|---|---|---|---:|---:|---:|---:|---:|")
    for name, r in sorted(d["fits"].items()):
        group, used, model = [s.strip() for s in name.split("|")]
        print(f"| {group} | {used} | {model} | {r['n']} | {r['k']:+.2f} ± {r['k_se']:.2f} | "
              f"{r['c']:+.2f} ± {r['c_se']:.2f} | {r['chi2']:.1f}/{r['dof']} | {r['inflation']:.2f} |")
    print("\n### Next-run options (projections from the adjusted-Elo fits)\n")
    for name, p in sorted(d["projections"].items()):
        print(f"**{name}**\n")
        print("| option | compute vs e48 on same data | holdout gain (1e-4) | Elo central | Elo p10 / p50 / p90 | Elo 95% |")
        print("|---|---:|---|---:|---|---|")
        for opt, o in p["options"].items():
            gain = (f"{o['dL_1e4_central']:.3f} (range {o['dL_1e4_range'][0]:.3f}..{o['dL_1e4_range'][1]:.3f})"
                    if "dL_1e4_range" in o else
                    f"{o['dL_1e4_central']:.3f} (95% {o['dL_1e4_ci95'][0]:.3f}..{o['dL_1e4_ci95'][1]:.3f})")
            q = o["elo_p10_p50_p90"]
            r = o["elo_p2.5_p97.5"]
            print(f"| {opt} | x{o['compute_vs_e48']:.2f} | {gain} | {o['elo_central']:+.2f} | "
                  f"{q[0]:+.2f} / {q[1]:+.2f} / {q[2]:+.2f} | {r[0]:+.2f} .. {r[1]:+.2f} |")
        print()
    chk = d["s30_epoch_fit_check"]
    print(f"S30 epoch-curve refit: L64 {chk['L64_refit']:.12f} vs S30 {chk['L64_s30']:.12f}")


if __name__ == "__main__":
    main()
