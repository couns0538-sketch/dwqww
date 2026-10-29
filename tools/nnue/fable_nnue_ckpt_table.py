#!/usr/bin/env python3
"""Markdown table of the checkpoints in a training run's status.json (job FB2-J1).

    fable_nnue_ckpt_table.py <run dir or status.json> [--al1 0.014417] [--hce 0.017141]
"""
import json
import os
import sys


def main():
    path = sys.argv[1]
    if os.path.isdir(path):
        path = os.path.join(path, "status.json")
    al1 = float(sys.argv[sys.argv.index("--al1") + 1]) if "--al1" in sys.argv else 0.014417
    st = json.load(open(path))
    print(f"run {st.get('out')} step {st['step']} / {st.get('horizon_steps')} seen {st['seen']} train_s {st['train_seconds']:.0f} "
          f"best {st.get('best_exact')} (step {st.get('best_step')}) plateau {st.get('plateau')} stop {st.get('stop_reason')}")
    print("| ckpt | step | positions | train min | lr | blend | exact b0.6 | b0.8 | b1.0 | per-phase b0.6 (few pieces -> many) | vs AL1 | parity 10k |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in st["checkpoints"]:
        ph = " ".join(f"{x:.4f}" if x is not None else "-" for x in c.get("phase_mse_b0.6", []))
        par = c.get("parity", {})
        pstr = f"{'PASS' if par.get('pass') else 'FAIL'} {par.get('positions', 0) - par.get('int_mismatches', 0)}/{par.get('positions', 0)}, max {par.get('max_abs_float_minus_int')} cp" if par else "-"
        e = c.get("exact_b0.6")
        print(f"| {c['index']} | {c['step']:,} | {c['seen'] / 1e6:.1f}M | {c['train_seconds'] / 60:.0f} | {c['lr']:.2e} | {c['blend']:.3f} | "
              f"{e:.6f} | {c.get('exact_b0.8', 0):.6f} | {c.get('exact_b1.0', 0):.6f} | {ph} | {e - al1:+.6f} | {pstr} |")


if __name__ == "__main__":
    main()
