#!/usr/bin/env python
"""make_test2.py - JOB E phase 2 (2026-11-11): a second, untouched test set from the two shards no set has used.

Own code; reuses make_splits.py (same folder) and FB2's reader, writer, row hash and phase function.

  test set 2 = N rows from shards 037 + 039 (first copy of each position kept), minus every position (board + side to
               move) that occurs in the training set, anywhere in 013/014 (selection pool) or anywhere in 036/038
               (pool of the phase-1 final test), proportional per phase bin, seeded.

The original shards are opened read-only. The phase-1 final-test files are not opened: its pool is re-read from the
source shards 036/038 only to compute position hashes for the exclusion.
"""
import argparse
import glob
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fable_nnue_data as fd   # noqa: E402
import make_splits as ms       # noqa: E402


def pool_hashes(pos_dir, shards):
    out = []
    for s in shards:
        out.append(ms.hash_file(os.path.join(pos_dir, f"forge_selfplay_{s}.pos")))
    return np.sort(np.concatenate(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-glob", default="F:/opus_scratch/fable/data/train/fb2_train_*.pos")
    ap.add_argument("--pos-dir", default="D:/grok-pc-data/forge_push/nnue_data/pos")
    ap.add_argument("--hce-dir", default="D:/grok-pc-data/forge_push/nnue_data/hce")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--test-shards", default="037,039")
    ap.add_argument("--select-shards", default="013,014")
    ap.add_argument("--test1-shards", default="036,038")
    ap.add_argument("--rows", type=int, default=2_000_000)
    ap.add_argument("--seed", type=int, default=2026111103)
    ap.add_argument("--threads", type=int, default=3)
    ap.add_argument("--name", default="final_test2_2m", help="output file stem (test set 3: final_test3_2m)")
    ap.add_argument("--label", default="test_set_2", help="manifest key")
    ap.add_argument("--use", default="scored once, at the end of all phase-2 training, for every frozen candidate and the references")
    ap.add_argument("--exclude-idx", nargs="*", default=[], help="index files (.npy) of earlier samples from the same pool; "
                    "their rows are not eligible")
    a = ap.parse_args()
    t0 = time.time()
    out_pos = os.path.join(a.out_dir, a.name + ".pos")
    if os.path.exists(out_pos) or os.path.exists(a.manifest):
        sys.exit("refused: test set 2 or its manifest already exists")
    files = sorted(glob.glob(a.train_glob))
    with ThreadPoolExecutor(a.threads) as ex:
        hashes = list(ex.map(ms.hash_file, files))
    train = np.concatenate(hashes)
    del hashes
    train.sort()
    print(f"training: {len(files)} files, {len(train)} rows hashed ({time.time() - t0:.0f}s)", flush=True)
    sel_sorted = pool_hashes(a.pos_dir, a.select_shards.split(","))
    t1_sorted = pool_hashes(a.pos_dir, a.test1_shards.split(","))
    print(f"exclusion pools: 013/014 {len(sel_sorted)} rows, 036/038 {len(t1_sorted)} rows ({time.time() - t0:.0f}s)", flush=True)

    tb, ts, tm, th, tinfo = ms.load_pool(a.pos_dir, a.hce_dir, a.test_shards.split(","))
    thash = fd.row_hash(tb, tm)
    first = ms.first_copies(thash)
    in_train = ms.in_sorted(train, thash)
    in_sel = ms.in_sorted(sel_sorted, thash)
    in_t1 = ms.in_sorted(t1_sorted, thash)
    used = np.zeros(len(tb), bool)
    for f in a.exclude_idx:
        used[np.load(f)] = True
    eligible = np.nonzero(first & ~in_train & ~in_sel & ~in_t1 & ~used)[0]
    phase = fd.phase_of(tb)
    idx, pool_hist, take_hist = ms.stratified(eligible, phase, a.rows, a.seed)
    fd.write_shard(out_pos, out_pos[:-4] + ".hce", tb[idx], ts[idx], tm[idx], th[idx])
    np.save(os.path.join(a.out_dir, a.name + ".idx.npy"), idx)
    man = {"job": "JOB E standalone H512, phase 2", "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "position_identity": "FB2 row_hash: 64-bit hash of (32 board bytes, side to move)",
           "tool_md5": hashlib.md5(open(__file__, "rb").read()).hexdigest(),
           a.label: {
               "excluded_earlier_samples": [{"idx": f, "rows": int(len(np.load(f)))} for f in a.exclude_idx],
               "sources": tinfo, "pool_rows": int(len(tb)), "duplicates_inside_removed": int((~first).sum()),
               "removed_because_in_training": int((first & in_train).sum()),
               "removed_because_in_013_014": int((first & ~in_train & in_sel).sum()),
               "removed_because_in_036_038": int((first & ~in_train & ~in_sel & in_t1).sum()),
               "eligible_rows": int(len(eligible)), "rows": int(len(idx)), "seed": a.seed,
               "sampling": "proportional per phase bin, without replacement, numpy PCG64",
               "pool_phase_hist": pool_hist, "phase_hist": take_hist,
               "index_sha256": hashlib.sha256(idx.astype("<i8").tobytes()).hexdigest(),
               "index_meaning": "row numbers in the concatenation of the source shards in the listed order",
               "pos": out_pos, "pos_sha256": fd.sha256_file(out_pos), "hce_sha256": fd.sha256_file(out_pos[:-4] + ".hce"),
               "use": a.use,
               "prior_exposure": "shards 037 and 039 were in no set of phase 1; not in the FB2 warm start's training data "
                                 "(its manifest: shards 001-035)"},
           "training_rows_hashed": int(len(train)),
           "separation": "FPOS rows carry no game id. Sets are separated by whole self-play shard files and by position-level "
                         "dedup across sets; plies of one game are assumed to stay inside one shard file.",
           "elapsed_s": round(time.time() - t0, 1)}
    with open(a.manifest, "w", encoding="utf-8", newline="\n") as f:
        json.dump(man, f, indent=1, sort_keys=True)
    t = man[a.label]
    print(f"{a.label}: pool {t['pool_rows']}, inside dups {t['duplicates_inside_removed']}, in training "
          f"{t['removed_because_in_training']}, in 013/014 {t['removed_because_in_013_014']}, in 036/038 "
          f"{t['removed_because_in_036_038']}, eligible {t['eligible_rows']}, taken {t['rows']} ({man['elapsed_s']}s)")


if __name__ == "__main__":
    main()
