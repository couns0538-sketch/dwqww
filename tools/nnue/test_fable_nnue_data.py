#!/usr/bin/env python3
"""Unit test of fable_nnue_data.py split on synthetic shards (job FB2-J1). Run:
    python -I -B tools/nnue/test_fable_nnue_data.py <scratch dir>
Checks, against an independent Python-set reference: (1) the kept training rows are exactly the distinct
(board, stm) keys of the training shards minus the keys that occur in the holdout shards (first copy kept);
(2) holdout and training rows are disjoint and the holdout rows are distinct; (3) every output row's
(board, score, meta, hce) tuple occurs in the inputs (the shuffle moves rows, never alters them); (4) the FPOS /
FHCE files round-trip exactly (header, rows, bytes); (5) the holdout phase histogram equals the largest-remainder
rounding of the training phase fractions; (6) the manifest sha256s verify (`check`); (7) a second run with the same
seed is byte-identical (deterministic)."""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fable_nnue_data as fd  # noqa: E402

PY = sys.executable


def synth_shard(rng, rows, dup_from=None, dup_count=0):
    """Random rows; `dup_count` rows copied from `dup_from` (board + meta identical, other fields new)."""
    boards = rng.integers(0, 256, size=(rows, 32), dtype=np.uint8).astype(np.uint8)
    # keep the piece codes valid-ish (0..12 per nibble) so the phase function sees plausible counts
    boards = ((boards & 15) % 13 | (((boards >> 4) % 13) << 4)).astype(np.uint8)
    score = rng.integers(-3000, 3000, size=rows).astype("<i2")
    meta = rng.integers(0, 6, size=rows).astype(np.uint8)
    hce = rng.integers(-2000, 2000, size=rows).astype("<i2")
    if dup_from is not None and dup_count:
        src = rng.choice(len(dup_from[0]), size=dup_count, replace=False)
        dst = rng.choice(rows, size=dup_count, replace=False)
        boards[dst] = dup_from[0][src]
        meta[dst] = dup_from[2][src]
    return boards, score, meta, hce


def key_of(board, meta):
    return board.tobytes() + bytes([int(meta) & 1])


def main():
    scratch = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "test_data_scratch")
    src = os.path.join(scratch, "src")
    os.makedirs(os.path.join(src, "pos"), exist_ok=True)
    os.makedirs(os.path.join(src, "hce"), exist_ok=True)
    rng = np.random.default_rng(7)
    shards = {}
    names = ["forge_selfplay_001", "forge_selfplay_013", "forge_selfplay_014", "forge_selfplay_020", "forge_selfplay_021"]
    sizes = {"forge_selfplay_001": 3001, "forge_selfplay_013": 2500, "forge_selfplay_014": 1700,
             "forge_selfplay_020": 4000, "forge_selfplay_021": 2200}
    prev = None
    for name in names:
        data = synth_shard(rng, sizes[name], prev, 150 if prev is not None else 0)
        # also duplicate a few rows inside the shard itself
        b, s, m, h = data
        same = rng.choice(len(b), size=40, replace=False)
        b[same[20:]] = b[same[:20]]
        m[same[20:]] = m[same[:20]]
        shards[name] = (b, s, m, h)
        fd.write_shard(os.path.join(src, "pos", name + ".pos"), os.path.join(src, "hce", name + ".hce"), b, s, m, h)
        prev = (b, s, m, h)
    # round trip of the writer/reader
    for name in names:
        b, s, m, h = fd.read_shard(os.path.join(src, "pos", name + ".pos"), os.path.join(src, "hce", name + ".hce"))
        assert np.array_equal(b, shards[name][0]) and np.array_equal(s, shards[name][1])
        assert np.array_equal(m, shards[name][2]) and np.array_equal(h, shards[name][3])
    print("round trip OK")

    def run_split(out, seed=1):
        cmd = [PY, "-I", "-B", os.path.join(HERE, "fable_nnue_data.py"), "split", "--pos-glob", os.path.join(src, "pos", "forge_selfplay_*.pos"),
               "--hce-dir", os.path.join(src, "hce"), "--out", out, "--holdout-shards", "_013,_014", "--holdout-rows", "500",
               "--train-shards", "5", "--seed", str(seed), "--partitions", "4"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout, r.stderr)
            raise SystemExit("split failed")
        return r.stdout

    out1 = os.path.join(scratch, "out1")
    run_split(out1)
    man = json.load(open(os.path.join(out1, "MANIFEST.json")))

    # reference dedup with Python sets, holdout keys first
    hold_names = ["forge_selfplay_013", "forge_selfplay_014"]
    train_names = [n for n in names if n not in hold_names]
    hold_keys = set()
    hold_rows = {}
    for n in hold_names:
        b, s, m, h = shards[n]
        for i in range(len(b)):
            k = key_of(b[i], m[i])
            if k not in hold_keys:
                hold_keys.add(k)
                hold_rows[k] = (b[i].tobytes(), int(s[i]), int(m[i]), int(h[i]))
    seen = set(hold_keys)
    expected_train = {}
    for n in train_names:
        b, s, m, h = shards[n]
        for i in range(len(b)):
            k = key_of(b[i], m[i])
            if k in seen:
                continue
            seen.add(k)
            expected_train[k] = (b[i].tobytes(), int(s[i]), int(m[i]), int(h[i]))
    got_train = {}
    for rel, info in man["files"].items():
        if rel.startswith("train/") and rel.endswith(".pos"):
            b, s, m, h = fd.read_shard(os.path.join(out1, rel), os.path.join(out1, rel[:-4] + ".hce"))
            assert len(b) == info["rows"]
            for i in range(len(b)):
                k = key_of(b[i], m[i])
                assert k not in got_train, "duplicate key in the training output"
                got_train[k] = (b[i].tobytes(), int(s[i]), int(m[i]), int(h[i]))
    assert set(got_train) == set(expected_train), (len(got_train), len(expected_train))
    assert got_train == expected_train, "a kept training row is not the first copy of its key"
    assert man["train_rows"] == len(expected_train)
    print(f"dedup OK: {len(expected_train)} training rows kept of {sum(sizes[n] for n in train_names)}")

    # holdout: distinct keys, disjoint from training, rows unaltered, phase histogram as targeted
    hp = os.path.join(out1, "holdout", "fb2_holdout_0k.pos")
    b, s, m, h = fd.read_shard(hp, hp[:-4] + ".hce")
    keys = [key_of(b[i], m[i]) for i in range(len(b))]
    assert len(set(keys)) == len(keys) == 500
    assert not (set(keys) & set(got_train))
    for i, k in enumerate(keys):
        assert k in hold_rows and hold_rows[k] == (b[i].tobytes(), int(s[i]), int(m[i]), int(h[i]))
    hist = np.bincount(fd.phase_of(b), minlength=8).tolist()
    assert hist == man["holdout_phase_hist"] == man["holdout_phase_target"], (hist, man["holdout_phase_hist"], man["holdout_phase_target"])
    frac = np.asarray(man["train_phase_hist"], np.float64) / sum(man["train_phase_hist"])
    raw = frac * 500
    tgt = np.floor(raw).astype(np.int64)
    for i in np.argsort(-(raw - tgt))[:500 - int(tgt.sum())]:
        tgt[i] += 1
    assert tgt.tolist() == hist
    print(f"holdout OK: phases {hist}")

    # manifest check command
    r = subprocess.run([PY, "-I", "-B", os.path.join(HERE, "fable_nnue_data.py"), "check", "--out", out1], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    print("check OK")

    # determinism
    out2 = os.path.join(scratch, "out2")
    run_split(out2)
    for rel, info in man["files"].items():
        assert fd.sha256_file(os.path.join(out2, rel)) == info["sha256"], rel
    print("determinism OK")
    print("PASS")


if __name__ == "__main__":
    main()
