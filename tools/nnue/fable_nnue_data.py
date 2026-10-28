#!/usr/bin/env python3
"""Training-data preparation for the NNUE v3 trainer (job FB2-J1): deduplicated, shuffled, phase-balanced
train / holdout split of the Forge self-play shards (FPOS/FHCE v1), written as read-only copies.

split  --pos-glob G --hce-dir D --out DIR [--holdout-shards _013,_014] [--holdout-rows 200000]
       [--train-shards 64] [--seed 1] [--partitions 32] [--max-rows-per-shard N]
  1. hash pass: every row -> 64-bit hash of (32 board bytes, side to move); the hashes are written into
     `--partitions` partition files (by the top hash bits) together with the global row id, in global order
     (holdout shards first, then the training shards in name order).
  2. dedup pass: per partition, the first occurrence of every hash is kept (np.unique over the partition in global
     order).  Because the holdout shards come first, a training row that repeats a holdout position is dropped
     (the S16 overlap), and duplicates inside the training set keep their earliest copy.
  3. scatter pass: every kept training row goes to one of `--train-shards` output shards chosen uniformly at
     random; 4. each output shard is permuted in memory and rewritten (a global shuffle: consecutive rows of an
     output shard come from different games).
  5. holdout: `--holdout-rows` rows drawn from the deduplicated holdout shards, stratified by phase so that the
     holdout's phase histogram equals the training set's (phase = output bucket by piece count, 8 bins, the same
     map as the net's output buckets).  Nothing else of the holdout shards is used anywhere.
  Output: DIR/train/fb2_train_NNN.pos|.hce, DIR/holdout/fb2_holdout_<rows>.pos|.hce, DIR/MANIFEST.json (rows,
  dedup statistics, phase histograms, sha256 of every output), all files read-only.
check  --out DIR     re-verifies the sha256 of every file in the manifest and the row counts.
stats  --pos FILE    phase histogram of one FPOS file.

Hash collisions: a 64-bit hash over about 3e8 rows loses an expected 0.002 distinct rows, which is harmless.
"""
import argparse
import glob
import hashlib
import json
import os
import struct
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fable_nnue_v3 as v3  # noqa: E402

ROW_BYTES = 32
HEADER = 16


# ---------------- FPOS / FHCE ----------------

def fpos_rows(path):
    with open(path, "rb") as f:
        head = f.read(HEADER)
    if head[:4] != b"FPOS":
        raise SystemExit(f"{path}: not an FPOS file")
    return struct.unpack("<IQ", head[4:16])[1]


def fhce_rows(path):
    with open(path, "rb") as f:
        head = f.read(HEADER)
    if head[:4] != b"FHCE":
        raise SystemExit(f"{path}: not an FHCE file")
    return struct.unpack("<IQ", head[4:16])[1]


def read_shard(pos_path, hce_path, max_rows=None):
    """Whole shard as arrays: boards (n, 32) u8, score (n,) i2, meta (n,) u8, hce (n,) i2."""
    total = fpos_rows(pos_path)
    n = total if max_rows is None else min(total, max_rows)
    boards = np.array(np.memmap(pos_path, np.uint8, "r", HEADER, (n, ROW_BYTES)))
    score = np.array(np.memmap(pos_path, "<i2", "r", HEADER + ROW_BYTES * total, (n,)))
    meta = np.array(np.memmap(pos_path, np.uint8, "r", HEADER + 34 * total, (n,)))
    hce = None
    if hce_path is not None:
        if fhce_rows(hce_path) != total:
            raise SystemExit(f"{hce_path}: row count differs from {pos_path}")
        hce = np.array(np.memmap(hce_path, "<i2", "r", HEADER, (n,)))
    return boards, score, meta, hce


def write_shard(pos_path, hce_path, boards, score, meta, hce):
    n = len(boards)
    with open(pos_path, "wb") as f:
        f.write(b"FPOS" + struct.pack("<IQ", 1, n))
        f.write(np.ascontiguousarray(boards, np.uint8).tobytes())
        f.write(np.ascontiguousarray(score, "<i2").tobytes())
        f.write(np.ascontiguousarray(meta, np.uint8).tobytes())
    if hce_path is not None:
        with open(hce_path, "wb") as f:
            f.write(b"FHCE" + struct.pack("<IQ", 1, n))
            f.write(np.ascontiguousarray(hce, "<i2").tobytes())


def sha256_file(path, chunk=1 << 24):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def make_readonly(path):
    os.chmod(path, 0o444)


# ---------------- hashing and phases ----------------

def row_hash(boards, meta):
    """64-bit hash of (board bytes, side to move) per row; splitmix-style mixing of the four 8-byte words."""
    n = len(boards)
    words = np.ascontiguousarray(boards, np.uint8).view("<u8").reshape(n, 4)
    with np.errstate(over="ignore"):
        h = (np.asarray(meta, np.uint64) & np.uint64(1)) * np.uint64(0x9E3779B97F4A7C15) + np.uint64(0x5851F42D4C957F2D)
        for k in range(4):
            x = words[:, k].astype(np.uint64) ^ h
            x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
            x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
            x = x ^ (x >> np.uint64(31))
            h = (h * np.uint64(0x100000001B3)) ^ x
        h = (h ^ (h >> np.uint64(29))) * np.uint64(0xBF58476D1CE4E5B9)
        h = h ^ (h >> np.uint64(32))
    return h


PIECE_COUNT_LUT = np.array([bin(c & 15 != 0).count("1") + bin(c >> 4 != 0).count("1") for c in range(256)], np.uint8)


def piece_counts(boards):
    """Number of pieces per row from the packed 4-bit codes (two squares per byte)."""
    return PIECE_COUNT_LUT[np.asarray(boards, np.uint8)].sum(axis=1, dtype=np.int64)


def phase_of(boards, phases=8):
    pc = np.minimum(piece_counts(boards), 32)
    omap = np.asarray(v3.output_layout(phases), np.int64)
    return omap[pc]


# ---------------- split ----------------

def cmd_split(args):
    t0 = time.time()
    rng = np.random.default_rng(args.seed)
    out = args.out
    for d in ("train", "holdout", "work"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    log = open(os.path.join(out, "split_log.txt"), "a", newline="\n")

    def say(msg):
        line = f"[{time.time() - t0:7.1f}s] {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    pos_files = sorted(glob.glob(args.pos_glob))
    if not pos_files:
        raise SystemExit("no shards match --pos-glob")
    hold_tags = [x for x in args.holdout_shards.split(",") if x]
    holdout_files = [f for f in pos_files if any(t in os.path.basename(f) for t in hold_tags)]
    train_files = [f for f in pos_files if f not in holdout_files]
    if not holdout_files or not train_files:
        raise SystemExit("need at least one holdout shard and one training shard")
    ordered = holdout_files + train_files   # global order: holdout first (its rows win the dedup)

    def hce_of(f):
        return os.path.join(args.hce_dir, os.path.basename(f)[:-4] + ".hce") if args.hce_dir else None

    rows_of = []
    for f in ordered:
        total = fpos_rows(f)
        rows_of.append(total if args.max_rows_per_shard is None else min(total, args.max_rows_per_shard))
    offsets = np.concatenate([[0], np.cumsum(rows_of)]).astype(np.int64)
    n_all = int(offsets[-1])
    say(f"shards: {len(holdout_files)} holdout ({sum(rows_of[:len(holdout_files)])} rows), {len(train_files)} training "
        f"({sum(rows_of[len(holdout_files):])} rows), total {n_all}; seed {args.seed}; partitions {args.partitions}")
    say("holdout shards: " + ", ".join(os.path.basename(f) for f in holdout_files))

    # ---- pass 1: hashes into partition files (global order) ----
    P = args.partitions
    shift = np.uint64(64 - int(np.log2(P)))
    if 1 << (64 - int(shift)) != P:
        raise SystemExit("--partitions must be a power of two")
    work = os.path.join(out, "work")
    part_h = [open(os.path.join(work, f"part{p:02d}.h64"), "wb") for p in range(P)]
    part_i = [open(os.path.join(work, f"part{p:02d}.i64"), "wb") for p in range(P)]
    phase_hist_all = {}
    for k, f in enumerate(ordered):
        boards, score, meta, _ = read_shard(f, None, args.max_rows_per_shard)
        h = row_hash(boards, meta)
        gid = np.arange(offsets[k], offsets[k + 1], dtype=np.int64)
        part = (h >> shift).astype(np.int64)
        order = np.argsort(part, kind="stable")
        bounds = np.searchsorted(part[order], np.arange(P + 1))
        for p in range(P):
            sl = order[bounds[p]:bounds[p + 1]]
            if len(sl):
                part_h[p].write(h[sl].tobytes())
                part_i[p].write(gid[sl].tobytes())
        ph = np.bincount(phase_of(boards), minlength=8)
        phase_hist_all[os.path.basename(f)] = ph.tolist()
        say(f"hashed {os.path.basename(f)}: {len(h)} rows")
    for fh in part_h + part_i:
        fh.close()

    # ---- pass 2: dedup per partition ----
    keep = np.zeros(n_all, bool)
    unique_total = 0
    for p in range(P):
        h = np.fromfile(os.path.join(work, f"part{p:02d}.h64"), np.uint64)
        gid = np.fromfile(os.path.join(work, f"part{p:02d}.i64"), np.int64)
        if len(h) == 0:
            continue
        # rows were appended in global order, so the first index of each unique hash is its earliest row
        _, first = np.unique(h, return_index=True)
        keep[gid[first]] = True
        unique_total += len(first)
        say(f"partition {p:02d}: {len(h)} rows, {len(first)} unique")
    say(f"dedup: {n_all} rows -> {unique_total} unique ({n_all - unique_total} duplicates removed)")
    stats = {"shards": {}}
    for k, f in enumerate(ordered):
        kp = int(keep[offsets[k]:offsets[k + 1]].sum())
        stats["shards"][os.path.basename(f)] = {"rows": int(rows_of[k]), "kept": kp, "dropped": int(rows_of[k]) - kp,
                                                "role": "holdout" if f in holdout_files else "train",
                                                "phase_hist_raw": phase_hist_all[os.path.basename(f)]}

    # ---- pass 3: scatter the kept training rows into the output shards ----
    S = args.train_shards
    out_pos = [os.path.join(out, "train", f"fb2_train_{s:03d}.pos") for s in range(S)]
    out_hce = [os.path.join(out, "train", f"fb2_train_{s:03d}.hce") for s in range(S)] if args.hce_dir else [None] * S
    # Temporary layout per output shard: a .rec file of 37-byte records (board 32, score 2, meta 1, hce 2)
    rec_files = [open(os.path.join(work, f"shard{s:03d}.rec"), "wb") for s in range(S)]
    rec_count = np.zeros(S, np.int64)
    train_phase = np.zeros(8, np.int64)
    for k, f in enumerate(ordered):
        if f in holdout_files:
            continue
        boards, score, meta, hce = read_shard(f, hce_of(f), args.max_rows_per_shard)
        m = keep[offsets[k]:offsets[k + 1]]
        boards, score, meta = boards[m], score[m], meta[m]
        hce = hce[m] if hce is not None else np.zeros(len(boards), np.int16)
        train_phase += np.bincount(phase_of(boards), minlength=8)
        dest = rng.integers(0, S, size=len(boards))
        order = np.argsort(dest, kind="stable")
        bounds = np.searchsorted(dest[order], np.arange(S + 1))
        rec = np.zeros((len(boards), 37), np.uint8)
        rec[:, :32] = boards
        rec[:, 32:34] = np.ascontiguousarray(score, "<i2").view(np.uint8).reshape(-1, 2)
        rec[:, 34] = meta
        rec[:, 35:37] = np.ascontiguousarray(hce, "<i2").view(np.uint8).reshape(-1, 2)
        for s in range(S):
            sl = order[bounds[s]:bounds[s + 1]]
            if len(sl):
                rec_files[s].write(rec[sl].tobytes())
                rec_count[s] += len(sl)
        say(f"scattered {os.path.basename(f)}: {len(boards)} kept rows")
    for fh in rec_files:
        fh.close()
    train_rows = int(rec_count.sum())

    # ---- pass 4: shuffle every output shard in memory and write FPOS/FHCE ----
    for s in range(S):
        rec = np.fromfile(os.path.join(work, f"shard{s:03d}.rec"), np.uint8).reshape(-1, 37)
        perm = rng.permutation(len(rec))
        rec = rec[perm]
        write_shard(out_pos[s], out_hce[s], rec[:, :32], rec[:, 32:34].copy().view("<i2").reshape(-1), rec[:, 34],
                    rec[:, 35:37].copy().view("<i2").reshape(-1))
        say(f"wrote {os.path.basename(out_pos[s])}: {len(rec)} rows")

    # ---- pass 5: phase-stratified holdout from the deduplicated holdout shards ----
    pool_b, pool_s, pool_m, pool_h = [], [], [], []
    for k, f in enumerate(ordered):
        if f not in holdout_files:
            continue
        boards, score, meta, hce = read_shard(f, hce_of(f), args.max_rows_per_shard)
        m = keep[offsets[k]:offsets[k + 1]]
        pool_b.append(boards[m])
        pool_s.append(score[m])
        pool_m.append(meta[m])
        pool_h.append(hce[m] if hce is not None else np.zeros(int(m.sum()), np.int16))
    pool_b = np.concatenate(pool_b)
    pool_s = np.concatenate(pool_s)
    pool_m = np.concatenate(pool_m)
    pool_h = np.concatenate(pool_h)
    pool_phase = phase_of(pool_b)
    pool_hist = np.bincount(pool_phase, minlength=8)
    H = args.holdout_rows
    # target counts: the training phase fractions, largest-remainder rounding to exactly H rows
    frac = train_phase / max(train_phase.sum(), 1)
    raw = frac * H
    target = np.floor(raw).astype(np.int64)
    rem = H - int(target.sum())
    for i in np.argsort(-(raw - target))[:rem]:
        target[i] += 1
    chosen = []
    short = {}
    for ph in range(8):
        idx = np.flatnonzero(pool_phase == ph)
        want = int(target[ph])
        if want > len(idx):
            short[ph] = want - len(idx)
            want = len(idx)
        if want:
            chosen.append(rng.choice(idx, size=want, replace=False))
    chosen = np.sort(np.concatenate(chosen)) if chosen else np.zeros(0, np.int64)
    chosen = chosen[rng.permutation(len(chosen))]
    hold_pos = os.path.join(out, "holdout", f"fb2_holdout_{H // 1000}k.pos")
    hold_hce = os.path.join(out, "holdout", f"fb2_holdout_{H // 1000}k.hce") if args.hce_dir else None
    write_shard(hold_pos, hold_hce, pool_b[chosen], pool_s[chosen], pool_m[chosen], pool_h[chosen])
    hold_hist = np.bincount(pool_phase[chosen], minlength=8)
    say(f"holdout: pool {len(pool_b)} deduplicated rows of the holdout shards, wrote {len(chosen)} rows"
        + (f" (phases short of the target: {short})" if short else ""))

    # ---- manifest ----
    files = {}
    for p in out_pos + out_hce + [hold_pos, hold_hce]:
        if p is None:
            continue
        make_readonly(p)
        rel = os.path.relpath(p, out).replace("\\", "/")
        files[rel] = {"bytes": os.path.getsize(p), "sha256": sha256_file(p),
                      "rows": fpos_rows(p) if p.endswith(".pos") else fhce_rows(p)}
    manifest = {
        "tool": "fable_nnue_data.py split", "seed": args.seed, "pos_glob": args.pos_glob, "hce_dir": args.hce_dir,
        "holdout_shards": [os.path.basename(f) for f in holdout_files],
        "train_source_shards": [os.path.basename(f) for f in train_files],
        "max_rows_per_shard": args.max_rows_per_shard,
        "rows_total": n_all, "rows_unique": unique_total, "duplicates_removed": n_all - unique_total,
        "train_rows": train_rows, "train_shards": S, "holdout_rows": int(len(chosen)),
        "holdout_pool_rows": int(len(pool_b)),
        "phase_definition": "output bucket by piece count: (min(pieces,32)-2)*8//32, 8 bins",
        "train_phase_hist": train_phase.tolist(), "holdout_phase_hist": hold_hist.tolist(),
        "holdout_pool_phase_hist": pool_hist.tolist(), "holdout_phase_target": target.tolist(),
        "per_shard": stats["shards"], "files": files,
        "elapsed_s": round(time.time() - t0, 1),
    }
    with open(os.path.join(out, "MANIFEST.json"), "w", newline="\n") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
    make_readonly(os.path.join(out, "MANIFEST.json"))
    say(f"done: train {train_rows} rows in {S} shards, holdout {len(chosen)} rows; manifest written")
    log.close()


def cmd_check(args):
    man = json.load(open(os.path.join(args.out, "MANIFEST.json")))
    bad = 0
    for rel, info in sorted(man["files"].items()):
        p = os.path.join(args.out, rel)
        rows = fpos_rows(p) if p.endswith(".pos") else fhce_rows(p)
        digest = sha256_file(p)
        ok = digest == info["sha256"] and rows == info["rows"] and os.path.getsize(p) == info["bytes"]
        bad += not ok
        print(f"{'OK ' if ok else 'BAD'} {rel} rows {rows} sha256 {digest[:16]}")
    train_rows = sum(info["rows"] for rel, info in man["files"].items() if rel.startswith("train/") and rel.endswith(".pos"))
    print(f"train rows {train_rows} (manifest {man['train_rows']}), holdout rows {man['holdout_rows']}, files bad {bad}")
    sys.exit(1 if bad or train_rows != man["train_rows"] else 0)


def cmd_stats(args):
    boards, score, meta, _ = read_shard(args.pos, None, args.max_rows)
    hist = np.bincount(phase_of(boards), minlength=8)
    print(json.dumps({"pos": args.pos, "rows": len(boards), "phase_hist": hist.tolist(),
                      "phase_frac": [round(float(x) / max(len(boards), 1), 5) for x in hist],
                      "stm_black_frac": round(float((meta & 1).mean()), 5),
                      "result_hist": np.bincount(meta >> 1, minlength=3).tolist(),
                      "score_abs_mean": round(float(np.abs(score.astype(np.int64)).mean()), 2)}))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split")
    s.add_argument("--pos-glob", required=True)
    s.add_argument("--hce-dir")
    s.add_argument("--out", required=True)
    s.add_argument("--holdout-shards", default="_013,_014")
    s.add_argument("--holdout-rows", type=int, default=200000)
    s.add_argument("--train-shards", type=int, default=64)
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--partitions", type=int, default=32)
    s.add_argument("--max-rows-per-shard", type=int)
    c = sub.add_parser("check")
    c.add_argument("--out", required=True)
    t = sub.add_parser("stats")
    t.add_argument("--pos", required=True)
    t.add_argument("--max-rows", type=int)
    args = ap.parse_args()
    {"split": cmd_split, "check": cmd_check, "stats": cmd_stats}[args.cmd](args)


if __name__ == "__main__":
    main()
