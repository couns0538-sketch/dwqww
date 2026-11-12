#!/usr/bin/env python
"""make_splits.py - JOB E (2026-11-11): freeze the training / selection / final-test sets and write their manifest.

Own code; reuses FB2's reader, writer, row hash and phase function (fable_nnue_data.py, same folder).
Nothing is written into the source folders; the original shards are opened read-only.

  training   = FB2's 64 shuffled shards as they are (shards 001-035 without 013/014, deduplicated by FB2)
  selection  = N rows from shards 013 + 014 (first copy of each position kept), proportional per phase bin, seeded
  final test = N rows from shards 036 + 038, minus every position (board + side to move) that occurs in the training
               set or anywhere in 013/014, proportional per phase bin, seeded

Position identity is FB2's 64-bit row hash of (32 board bytes, side to move). A hash collision can only remove an
extra row from the selection or final-test pool, never let a duplicate through.
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


def hash_file(path):
    n = fd.fpos_rows(path)
    boards = np.fromfile(path, np.uint8, n * 32, offset=16).reshape(n, 32)
    meta = np.fromfile(path, np.uint8, n, offset=16 + 34 * n)
    return fd.row_hash(boards, meta)


def in_sorted(sorted_arr, x):
    pos = np.searchsorted(sorted_arr, x)
    pos[pos >= len(sorted_arr)] = len(sorted_arr) - 1
    return sorted_arr[pos] == x


def load_pool(pos_dir, hce_dir, shards):
    parts = []
    info = []
    for s in shards:
        p = os.path.join(pos_dir, f"forge_selfplay_{s}.pos")
        h = os.path.join(hce_dir, f"forge_selfplay_{s}.hce")
        boards, score, meta, hce = fd.read_shard(p, h)
        parts.append((boards, score, meta, hce))
        info.append({"shard": s, "pos": p, "hce": h, "rows": int(len(boards)), "pos_sha256": fd.sha256_file(p),
                     "hce_sha256": fd.sha256_file(h), "pos_bytes": os.path.getsize(p)})
    boards = np.concatenate([x[0] for x in parts])
    score = np.concatenate([x[1] for x in parts])
    meta = np.concatenate([x[2] for x in parts])
    hce = np.concatenate([x[3] for x in parts])
    return boards, score, meta, hce, info


def first_copies(h):
    """Boolean mask: True for the first occurrence of each hash, in row order."""
    order = np.argsort(h, kind="stable")
    hs = h[order]
    first = np.ones(len(h), bool)
    first[1:] = hs[1:] != hs[:-1]
    mask = np.zeros(len(h), bool)
    mask[order[first]] = True
    return mask


def stratified(eligible_idx, phase, rows, seed):
    """`rows` indices out of eligible_idx, proportional to the phase-bin sizes (largest remainder), seeded."""
    rng = np.random.Generator(np.random.PCG64(seed))
    ph = phase[eligible_idx]
    counts = np.bincount(ph, minlength=8).astype(np.int64)
    exact = counts * rows / counts.sum()
    take = np.floor(exact).astype(np.int64)
    rest = rows - int(take.sum())
    for k in np.argsort(-(exact - take), kind="stable")[:rest]:
        take[k] += 1
    chosen = []
    for b in range(8):
        cand = eligible_idx[ph == b]
        chosen.append(rng.choice(cand, size=int(take[b]), replace=False))
    out = np.sort(np.concatenate(chosen))
    return out, counts.tolist(), take.tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-glob", default="F:/opus_scratch/fable/data/train/fb2_train_*.pos")
    ap.add_argument("--fb2-manifest", default="F:/opus_scratch/fable/data/MANIFEST.json")
    ap.add_argument("--pos-dir", default="D:/grok-pc-data/forge_push/nnue_data/pos")
    ap.add_argument("--hce-dir", default="D:/grok-pc-data/forge_push/nnue_data/hce")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--select-shards", default="013,014")
    ap.add_argument("--test-shards", default="036,038")
    ap.add_argument("--rows", type=int, default=2_000_000)
    ap.add_argument("--seed-select", type=int, default=2026111101)
    ap.add_argument("--seed-test", type=int, default=2026111102)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out_dir, exist_ok=True)
    man = {"job": "JOB E standalone H512", "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "position_identity":
           "FB2 row_hash: 64-bit hash of (32 board bytes, side to move)", "tool_md5": hashlib.md5(open(__file__, "rb").read()).hexdigest()}

    # ---- training set: hash every row
    files = sorted(glob.glob(a.train_glob))
    with ThreadPoolExecutor(8) as ex:
        hashes = list(ex.map(hash_file, files))
    counts = [int(len(h)) for h in hashes]
    train = np.concatenate(hashes)
    del hashes
    train.sort()
    dup_inside = int((train[1:] == train[:-1]).sum())
    fb2 = json.load(open(a.fb2_manifest, "r", encoding="utf-8"))
    man["training"] = {
        "glob": a.train_glob, "files": len(files), "rows": int(len(train)), "rows_per_file": counts,
        "duplicate_hashes_inside": dup_inside, "fb2_manifest": a.fb2_manifest,
        "fb2_manifest_sha256": fd.sha256_file(a.fb2_manifest), "fb2_manifest_train_rows": fb2.get("train_rows"),
        "file_hashes": "per-file sha256 are in the FB2 manifest; all 130 files verified on 2026-11-11 (results/step1/fb2_data_check.log)",
        "source": "production shards 001-035 without 013/014, deduplicated and globally shuffled by FB2 (seed 1)",
        "prior_exposure": "these are the rows the FB2 warm-start checkpoint was trained on"}
    print(f"training: {len(files)} files, {len(train)} rows, duplicate hashes inside {dup_inside} ({time.time() - t0:.0f}s)", flush=True)

    # ---- selection: 013 + 014
    sb, ss, sm, sh, sinfo = load_pool(a.pos_dir, a.hce_dir, a.select_shards.split(","))
    shash = fd.row_hash(sb, sm)
    first = first_copies(shash)
    in_train = in_sorted(train, shash)
    eligible = np.nonzero(first & ~in_train)[0]
    phase = fd.phase_of(sb)
    sel_idx, pool_hist, take_hist = stratified(eligible, phase, a.rows, a.seed_select)
    sel_pos = os.path.join(a.out_dir, "select_2m.pos")
    fd.write_shard(sel_pos, sel_pos[:-4] + ".hce", sb[sel_idx], ss[sel_idx], sm[sel_idx], sh[sel_idx])
    np.save(os.path.join(a.out_dir, "select_2m.idx.npy"), sel_idx)
    man["selection"] = {
        "sources": sinfo, "pool_rows": int(len(sb)), "duplicates_inside_removed": int((~first).sum()),
        "rows_also_in_training": int((first & in_train).sum()), "eligible_rows": int(len(eligible)),
        "rows": int(len(sel_idx)), "seed": a.seed_select, "sampling": "proportional per phase bin, without replacement, numpy PCG64",
        "pool_phase_hist": pool_hist, "phase_hist": take_hist,
        "index_sha256": hashlib.sha256(sel_idx.astype("<i8").tobytes()).hexdigest(),
        "index_meaning": "row numbers in the concatenation of the source shards in the listed order",
        "pos": sel_pos, "pos_sha256": fd.sha256_file(sel_pos), "hce_sha256": fd.sha256_file(sel_pos[:-4] + ".hce"),
        "use": "every recipe, stage, plateau and checkpoint decision",
        "prior_exposure": "FB2 chose its best checkpoint on 200,000 rows of the same pool; s198 was selected on 013/014 by its owners; "
                          "no net of this job is trained on these shards"}
    sel_hash_sorted = np.sort(shash)
    print(f"selection: pool {len(sb)}, inside dups {(~first).sum()}, also in training {(first & in_train).sum()}, "
          f"eligible {len(eligible)}, taken {len(sel_idx)} ({time.time() - t0:.0f}s)", flush=True)
    del sb, ss, sm, sh

    # ---- final test: 036 + 038
    tb, ts, tm, th, tinfo = load_pool(a.pos_dir, a.hce_dir, a.test_shards.split(","))
    thash = fd.row_hash(tb, tm)
    first = first_copies(thash)
    in_train = in_sorted(train, thash)
    in_sel = in_sorted(sel_hash_sorted, thash)
    eligible = np.nonzero(first & ~in_train & ~in_sel)[0]
    phase = fd.phase_of(tb)
    test_idx, pool_hist, take_hist = stratified(eligible, phase, a.rows, a.seed_test)
    test_pos = os.path.join(a.out_dir, "final_test_2m.pos")
    fd.write_shard(test_pos, test_pos[:-4] + ".hce", tb[test_idx], ts[test_idx], tm[test_idx], th[test_idx])
    np.save(os.path.join(a.out_dir, "final_test_2m.idx.npy"), test_idx)
    man["final_test"] = {
        "sources": tinfo, "pool_rows": int(len(tb)), "duplicates_inside_removed": int((~first).sum()),
        "removed_because_in_training": int((first & in_train).sum()),
        "removed_because_in_013_014": int((first & ~in_train & in_sel).sum()),
        "eligible_rows": int(len(eligible)), "rows": int(len(test_idx)), "seed": a.seed_test,
        "sampling": "proportional per phase bin, without replacement, numpy PCG64",
        "pool_phase_hist": pool_hist, "phase_hist": take_hist,
        "index_sha256": hashlib.sha256(test_idx.astype("<i8").tobytes()).hexdigest(),
        "index_meaning": "row numbers in the concatenation of the source shards in the listed order",
        "pos": test_pos, "pos_sha256": fd.sha256_file(test_pos), "hce_sha256": fd.sha256_file(test_pos[:-4] + ".hce"),
        "use": "scored once, after the recipe and checkpoint are frozen",
        "prior_exposure": "not in the FB2 warm start's training data (its manifest: shards 001-035) and not used for any selection in this job"}
    print(f"final test: pool {len(tb)}, inside dups {(~first).sum()}, in training {(first & in_train).sum()}, "
          f"in 013/014 {(first & ~in_train & in_sel).sum()}, eligible {len(eligible)}, taken {len(test_idx)} ({time.time() - t0:.0f}s)", flush=True)
    man["unused"] = {"shards": ["037", "039"], "note": "not in any set of this job"}
    man["separation"] = ("FPOS rows carry no game id. Sets are separated by whole self-play shard files and by position-level "
                         "dedup across sets; plies of one game are assumed to stay inside one shard file.")
    man["elapsed_s"] = round(time.time() - t0, 1)
    with open(a.manifest, "w", encoding="utf-8", newline="\n") as f:
        json.dump(man, f, indent=1, sort_keys=True)
    print(f"manifest {a.manifest} ({man['elapsed_s']}s)")


if __name__ == "__main__":
    main()
