#!/usr/bin/env python
"""pilot_table.py - JOB E: one row per checkpoint of every run folder given (metrics.jsonl), as a Markdown table. Own code."""
import json, os, sys
rows = []
for d in sys.argv[1:]:
    p = os.path.join(d, "metrics.jsonl")
    if not os.path.isfile(p):
        continue
    for line in open(p, encoding="utf-8"):
        e = json.loads(line)
        s, f = e["scores"]["select_2m"], e["scores"]["fb2_200k"]
        rows.append((os.path.basename(d.rstrip("/\\")), e["seen"], e["reason"], e["lr"], e["alpha"], s["mse_b0.6"], s["mse_b1.0"], s["mse_b0.75"],
                     s["mse_b0.5"], s["mse_b0.0"], f["mse_b0.6"], e["train_loss_ema"], e["pos_per_s"], e["hold_seconds"]))
print("| run | presentations | at | lr | alpha | select b0.6 (rank) | select b1.0 | select b0.75 | select b0.5 | select b0.0 | fb2_200k b0.6 | train loss ema | pos/s | hold s |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    print("| %s | %d | %s | %.1e | %.3f | %.6f | %.6f | %.6f | %.6f | %.6f | %.6f | %.6f | %.0f | %.0f |" % r)
