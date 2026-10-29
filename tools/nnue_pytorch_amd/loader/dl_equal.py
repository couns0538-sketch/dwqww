"""R6 J4: do two data-loader DLL builds produce identical batches?

usage: python dl_equal.py DLL_DIR MODE [N]
  DLL_DIR: directory whose build/ holds exactly one *training_data_loader.dll
  MODE fens-dump OUT: write N FEN batches (4096) from the stream to OUT (one FEN per line)
  MODE fens FENFILE: sparse batches from a fixed FEN list (deterministic feature extraction)
  MODE stream N: hash of N sparse batches from small.binpack (1 thread, cyclic)
Prints a sha256 over every field of every batch, for each feature set.
"""

import ctypes
import hashlib
import os
import sys

CLONE = "F:/opus_scratch/r6/nnue-pytorch-amd"
BINPACK = CLONE + "/.pgo/small.binpack"
FEATURES = ["K32H3", "Full_Threats+PP_3Wide+K32H3"]

dll_dir, mode = sys.argv[1], sys.argv[2]
os.chdir(dll_dir)
sys.path.insert(0, CLONE)
from data_loader import stream as S  # noqa: E402
from data_loader._native import c_lib  # noqa: E402
from data_loader.config import DataloaderSkipConfig  # noqa: E402

print("loaded", c_lib.dll._name)


def raw(ptr, count, ctype):
    return ctypes.string_at(ptr, count * ctypes.sizeof(ctype))


def hash_batch(h, c):
    sz, m = c.size, c.max_active_features
    h.update(sz.to_bytes(4, "little") + m.to_bytes(4, "little") + c.num_inputs.to_bytes(4, "little"))
    for ptr in (c.is_white, c.outcome, c.score):
        h.update(raw(ptr, sz, ctypes.c_float))
    for ptr in (c.white, c.black):
        h.update(raw(ptr, sz * m, ctypes.c_int))
    for ptr in (c.piece_count, c.queen_bucket):
        h.update(raw(ptr, sz, ctypes.c_int))


if mode == "fens-dump":
    out, n = sys.argv[3], int(sys.argv[4])
    st = S.create_fen_batch_stream(1, [BINPACK], 4096, True, DataloaderSkipConfig())
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for _ in range(n):
            b = S.fetch_next_fen_batch(st)
            for fen in b.contents.get_fens():
                f.write(fen + "\n")
            S.destroy_fen_batch(b)
    S.destroy_fen_batch_stream(st)
    print("dumped", n * 4096, "fens")
elif mode == "fens":
    fens = open(sys.argv[3], encoding="utf-8").read().split("\n")[:-1]
    for feat in FEATURES:
        h = hashlib.sha256()
        for i in range(0, len(fens), 4096):
            chunk = fens[i : i + 4096]
            scores = [(j * 37) % 601 - 300 for j in range(len(chunk))]
            plies = [20 + j % 80 for j in range(len(chunk))]
            results = [(j % 3) - 1 for j in range(len(chunk))]
            b = S.get_sparse_batch_from_fens(feat, chunk, scores, plies, results)
            hash_batch(h, b.contents)
            S.destroy_sparse_batch(b)
        print(f"fens {feat}: {len(fens)} positions sha256 {h.hexdigest()}")
elif mode == "window":
    # Order-independent fingerprint of the first N batches (one shuffle window = 256 x 4096).
    import numpy as np

    n = int(sys.argv[3])
    feat = "K32H3"
    st = S.create_sparse_batch_stream(feat.encode("utf-8"), 1, [BINPACK], 4096, True, DataloaderSkipConfig())
    rows = []
    h_ordered = hashlib.sha256()
    for _ in range(n):
        b = S.fetch_next_sparse_batch(st)
        c = b.contents
        hash_batch(h_ordered, c)
        sz, m = c.size, c.max_active_features
        w = np.ctypeslib.as_array(c.white, shape=(sz * m,)).reshape(sz, m).astype(np.int64)
        bl = np.ctypeslib.as_array(c.black, shape=(sz * m,)).reshape(sz, m).astype(np.int64)
        f = np.stack([np.ctypeslib.as_array(p, shape=(sz,)).astype(np.float64)
                      for p in (c.is_white, c.outcome, c.score)], 1)
        ii = np.stack([np.ctypeslib.as_array(p, shape=(sz,)).astype(np.int64)
                       for p in (c.piece_count, c.queen_bucket)], 1)
        rec = np.concatenate([w, bl, ii, (f * 1e6).round().astype(np.int64)], 1).astype(np.uint64)
        # per-position 64-bit polynomial hash
        k = np.uint64(1099511628211)
        hv = np.zeros(sz, dtype=np.uint64)
        for j in range(rec.shape[1]):
            hv = hv * k + rec[:, j] + np.uint64(j + 1)
        rows.append(hv)
        S.destroy_sparse_batch(b)
    S.destroy_sparse_batch_stream(st)
    allh = np.sort(np.concatenate(rows))
    print(f"window {feat}: {allh.size} positions, ordered sha256 {h_ordered.hexdigest()[:16]}, "
          f"multiset sha256 {hashlib.sha256(allh.tobytes()).hexdigest()[:16]}, "
          f"distinct {np.unique(allh).size}")
elif mode == "stream":
    n = int(sys.argv[3])
    for feat in FEATURES:
        st = S.create_sparse_batch_stream(feat.encode("utf-8"), 1, [BINPACK], 4096, True, DataloaderSkipConfig())
        h = hashlib.sha256()
        for _ in range(n):
            b = S.fetch_next_sparse_batch(st)
            hash_batch(h, b.contents)
            S.destroy_sparse_batch(b)
        S.destroy_sparse_batch_stream(st)
        print(f"stream {feat}: {n} batches sha256 {h.hexdigest()}")
