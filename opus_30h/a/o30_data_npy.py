#!/usr/bin/env python3
"""o30_data_npy.py <data dir> - Opus 30-h job: write the jobA overrides of an o30_data.py folder as plain .npy files
(override_npy/<shard>_index.npy int64, <shard>_score.npy int16) for the Rust reader of forge-v2-bullet `r` mode, which
reads .npy but not .npz (zip). New files only (refuses an existing override_npy folder); prints the row counts."""
import os
import sys

import numpy as np


def main():
    d = sys.argv[1]
    out = os.path.join(d, 'override_npy')
    if os.path.exists(out):
        sys.exit(f'refusing: {out} exists')
    os.makedirs(out)
    for f in sorted(os.listdir(os.path.join(d, 'override'))):
        if not f.endswith('.npz'):
            continue
        z = np.load(os.path.join(d, 'override', f))
        idx, sc = z['index'].astype('<i8'), z['score'].astype('<i2')
        assert np.all(np.diff(idx) > 0), f'{f}: indices not strictly increasing'
        np.save(os.path.join(out, f[:-4] + '_index.npy'), idx)
        np.save(os.path.join(out, f[:-4] + '_score.npy'), sc)
        print(f'{f[:-4]}: {len(idx)} overrides')


if __name__ == '__main__':
    main()
