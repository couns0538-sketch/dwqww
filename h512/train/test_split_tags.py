#!/usr/bin/env python3
"""Holdout shard tags must not swallow a longer shard id, and a repeated holdout row stays out of train."""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fable_nnue_data as data


def check_matcher():
    assert data.shard_tag_matches("fb2_013.pos", "_013")
    assert data.shard_tag_matches("fb2_014.pos", "_014")
    assert not data.shard_tag_matches("fb2_0130.pos", "_013")
    assert not data.shard_tag_matches("fb2_001.pos", "_013")
    assert not data.shard_tag_matches("fb2_013.pos", "_01")
    assert data.shard_tag_matches("fb2_013_extra.pos", "_013")
    assert not data.shard_tag_matches("fb2_013.pos", "")


def row(white_king, black_king, extra=None):
    board = np.zeros(32, np.uint8)
    board[white_king // 2] |= np.uint8(6 if white_king % 2 == 0 else 6 << 4)
    shift = 0 if black_king % 2 == 0 else 4
    board[black_king // 2] |= np.uint8(12 << shift)
    if extra is not None:
        square, code = extra
        shift = 0 if square % 2 == 0 else 4
        board[square // 2] |= np.uint8(code << shift)
    return board


def write_pos(path, boards, meta):
    n = len(boards)
    score = np.zeros(n, np.int16)
    data.write_shard(path, None, np.stack(boards), score, np.asarray(meta, np.uint8), None)


def check_split():
    # a1 white king, h8 black king. Row A is shared by the holdout and a training shard.
    shared = row(0, 63)
    other = row(0, 63, extra=(8, 1))
    only_long = row(1, 62)
    only_train = row(2, 61)
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "src")
        out = os.path.join(tmp, "out")
        os.makedirs(src)
        write_pos(os.path.join(src, "fb2_013.pos"), [shared, other], [0, 0])
        write_pos(os.path.join(src, "fb2_0130.pos"), [only_long], [0])
        write_pos(os.path.join(src, "fb2_001.pos"), [shared, only_train], [0, 0])
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fable_nnue_data.py")
        proc = subprocess.run(
            [sys.executable, script, "split", "--pos-glob", os.path.join(src, "*.pos"),
             "--out", out, "--holdout-shards", "_013,_014", "--holdout-rows", "2",
             "--train-shards", "2", "--partitions", "2", "--seed", "1"],
            check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            raise SystemExit(proc.stdout + proc.stderr)
        man = json.load(open(os.path.join(out, "MANIFEST.json")))
        hold = man["holdout_shards"]
        train = man["train_source_shards"]
        if hold != ["fb2_013.pos"]:
            raise SystemExit(f"holdout shards {hold}")
        if train != ["fb2_001.pos", "fb2_0130.pos"]:
            raise SystemExit(f"train shards {train}")
        per = man["per_shard"]
        if per["fb2_001.pos"]["kept"] != 1 or per["fb2_001.pos"]["dropped"] != 1:
            raise SystemExit(f"dedup {per['fb2_001.pos']}")
        if per["fb2_0130.pos"]["kept"] != 1 or per["fb2_0130.pos"]["role"] != "train":
            raise SystemExit(f"long id {per['fb2_0130.pos']}")
        if per["fb2_013.pos"]["role"] != "holdout" or per["fb2_013.pos"]["kept"] != 2:
            raise SystemExit(f"holdout rows {per['fb2_013.pos']}")
        if man["train_rows"] != 2:
            raise SystemExit(f"train rows {man['train_rows']}")


def main():
    check_matcher()
    check_split()
    print("split tags: matcher and tiny split agree")


if __name__ == "__main__":
    main()
