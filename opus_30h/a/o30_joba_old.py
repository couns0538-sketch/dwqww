#!/usr/bin/env python3
"""o30_joba_old.py <out dir> - Opus 30-h job: the jobA val positions (the same 8,821 non-mate rows as
D:\\o30\\data\\jobA_val.pos) with their ORIGINAL 5k-node self-play scores instead of the 20k-node relabels, as FPOS / FHCE
(jobA_val_old.pos / .hce). Scoring a net on both files separates "fits the shallow labels" from "worse on these
positions". Reads the FPOS / FHCE shards and jobA's rows.tsv / labels.tsv read-only; refuses existing outputs."""
import csv
import json
import os
import sys

import numpy as np

MATE = 30000


def main():
    out = sys.argv[1]
    joba = r'D:\o14b\r2\proof\jobA'
    pos_dir = r'D:\grok-pc-data\forge_push\nnue_data\pos'
    hce_dir = r'D:\grok-pc-data\forge_push\nnue_data\hce'
    for f in ('jobA_val_old.pos', 'jobA_val_old.hce'):
        if os.path.exists(os.path.join(out, f)):
            sys.exit(f'refusing: {f} exists')
    prep = json.load(open(os.path.join(joba, 'prepare.json')))
    src = {str(i['index']): os.path.splitext(os.path.basename(i['path']))[0] for i in prep['inputs']}
    rows_src = {}
    with open(os.path.join(joba, 'rows.tsv'), newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            rows_src[int(r['row_id'])] = (src[r['source']], int(r['source_row']) - 1)
    want = []   # (shard, idx) of val rows in labels.tsv order, non-mate by the NEW label (as jobA_val.pos)
    with open(os.path.join(joba, 'final', 'labels.tsv'), newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['split'] == 'val' and abs(int(r['score_stm'])) < MATE:
                want.append(rows_src[int(r['row_id'])])
    boards, scores, metas, hces = [], [], [], []
    cache = {}
    for shard, idx in want:
        if shard not in cache:
            p = os.path.join(pos_dir, shard + '.pos')
            n = int.from_bytes(open(p, 'rb').read(16)[8:16], 'little')
            cache[shard] = (np.fromfile(p, np.uint8, count=32 * n, offset=16).reshape(n, 32),
                            np.fromfile(p, '<i2', count=n, offset=16 + 32 * n), np.fromfile(p, np.uint8, count=n, offset=16 + 34 * n),
                            np.fromfile(os.path.join(hce_dir, shard + '.hce'), '<i2', count=n, offset=16))
        b, s, m, h = cache[shard]
        boards.append(b[idx]); scores.append(s[idx]); metas.append(m[idx]); hces.append(h[idx])
    n = len(want)
    head = lambda magic: magic + (1).to_bytes(4, 'little') + n.to_bytes(8, 'little')
    with open(os.path.join(out, 'jobA_val_old.pos'), 'xb') as f:
        f.write(head(b'FPOS') + np.array(boards, np.uint8).tobytes() + np.array(scores, '<i2').tobytes() + np.array(metas, np.uint8).tobytes())
    with open(os.path.join(out, 'jobA_val_old.hce'), 'xb') as f:
        f.write(head(b'FHCE') + np.array(hces, '<i2').tobytes())
    new_b = np.fromfile(os.path.join(out, 'jobA_val.pos'), np.uint8, count=32 * n, offset=16).reshape(n, 32)
    print(f'{n} rows; boards equal to jobA_val.pos: {bool(np.array_equal(new_b, np.array(boards, np.uint8)))}')


if __name__ == '__main__':
    main()
