#!/usr/bin/env python3
"""net_training_json.py <run dir> <net file used> <out TRAINING.json> - Opus 30-h job: the training record of a packed net
(config of the o30_fit.py run, the checkpoint that became the net, its holdout numbers, the run's whole val.csv),
for D:\\o30\\nets\\<name>\\TRAINING.json (make_net_index.py shows its `summary`). Refuses an existing output."""
import csv
import json
import os
import sys


def main():
    run, net, out = sys.argv[1:4]
    if os.path.exists(out):
        sys.exit(f'refusing: {out} exists')
    cfg = json.load(open(os.path.join(run, 'config.json')))
    rows = list(csv.DictReader(open(os.path.join(run, 'val.csv'))))
    base = os.path.basename(net).lower()
    used = next((r for r in rows if os.path.basename(r['net']).lower() == base), None)
    if used is None and base == 'best.nnue2':
        used = min(rows, key=lambda r: float(r['s16_b06']))
    summary = (f"o30_fit.py CPU fine-tune from the lock net (warm start = the lock function), king map {cfg['kb_map']}"
               f"{' mirrored' if cfg.get('mirror') else ''}, output buckets {cfg['ob']}, residual (b = {cfg['blend']}), lr {cfg['lr']} "
               f"(output layer x{cfg.get('lr_out_mult', 1.0)}) cosine to {cfg['lr_end']} over {float(cfg['positions']):.3g} positions, "
               f"batch {cfg['batch']}, {cfg.get('mix', 1)} shards per chunk, seed {cfg['seed']}; data D:\\o30\\data (skip lists, jobA "
               f"overrides); net = checkpoint at {float(used['positions']):.3g} positions ({used['time']})" if used else 'checkpoint not found')
    rec = {'run': run, 'config': cfg, 'net_checkpoint': used, 'val_history': rows, 'summary': summary}
    with open(out, 'x', newline='\n') as f:
        json.dump(rec, f, indent=1)
    print(summary)


if __name__ == '__main__':
    main()
