#!/usr/bin/env python3
"""fl_dataset_equal.py - Opus R14-B: tensor-level equality through the trainer's own data path (own code).

Builds the training (and validation) stream exactly like the patched train.py make_data_loaders does -
SparseBatchDataset or FastSparseBatchDataset -> FixedNumBatchesDataset -> DataLoader(batch_size=None) - and hashes
every tensor of every batch (dtype, shape, bytes). CPU path only (GPU hidden; pinned memory needs the HIP runtime,
which must not be loaded next to the live npt line: that path is covered by the GPU window).

Run inside the trainer copy with its venv, GPU hidden (see RESULTS.md for the exact command):
  python -B fl_dataset_equal.py --loader old|fast --workers N --batches 200 --val-batches 61 --out FILE
  python -B fl_dataset_equal.py --compare A B
"""

import argparse
import hashlib
import os
import sys

TRAIN = r"F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack"
VAL = r"F:\forge_j1_data\forge_holdout_013-014_j2.binpack"


def tensor_digest(t) -> str:
    t = t.detach().contiguous().cpu()
    h = hashlib.sha256()
    h.update(f"{t.dtype}|{tuple(t.shape)}|".encode())
    h.update(t.numpy().tobytes())
    return h.hexdigest()[:24]


def dump(a) -> int:
    import torch
    from torch.utils.data import DataLoader

    sys.path.insert(0, os.getcwd())
    import data_loader
    from data_loader.config import DataloaderDDPConfig, DataloaderIOConfig, DataloaderSkipConfig

    if a.loader == "old":
        cls = data_loader.SparseBatchDataset
    else:
        import importlib.util

        fl_dir = os.environ["FORGE_FAST_LOADER_DIR"]
        spec = importlib.util.spec_from_file_location("forge_fastloader", os.path.join(fl_dir, "forge_fastloader.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "library_info"):  # b4 and older: no library_info (seen: D:\o14b\npt holds the b4 files)
            raise SystemExit(f"{fl_dir}: forge_fastloader.py predates the b5 candidate (no library_info): install the "
                             f"b5 files (install_fast_loader.py --loader-dll) or give the b5 folder")
        print("fast loader:", mod.library_info(), flush=True)
        cls = mod.FastSparseBatchDataset
    skip = DataloaderSkipConfig(filtered=False, wld_filtered=False)
    lines = []
    for name, path, n in (("train", TRAIN, a.batches), ("val", VAL, a.val_batches)):
        if n <= 0:
            continue
        ds = cls("K32H3", [path], 16384, num_workers=a.workers, config=skip,
                 ddp_config=DataloaderDDPConfig(rank=0, world_size=1), io_config=DataloaderIOConfig())
        loader = DataLoader(data_loader.FixedNumBatchesDataset(ds, n, pin_memory=False, queue_size_limit=10,
                                                               device=None), batch_size=None, batch_sampler=None,
                            num_workers=0)
        k = 0
        for batch in loader:
            lines.append(f"{name}\t{k}\t" + "\t".join(tensor_digest(t) for t in batch))
            k += 1
        if k != n:
            raise SystemExit(f"{name}: got {k} batches, wanted {n}")
        print(f"{a.loader} {name}: {k} batches, {len(batch)} tensors each", flush=True)
        del loader, ds, batch  # stop this stream's loader threads before the next stream starts
        import gc

        gc.collect()
    with open(a.out, "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
        f.write(f"# loader={a.loader} workers={a.workers} torch={torch.__version__} batches={a.batches} "
                f"val_batches={a.val_batches}\n")
    return 0


def compare(pa, pb) -> int:
    ra = [x for x in open(pa, encoding="utf-8").read().splitlines() if not x.startswith("#")]
    rb = [x for x in open(pb, encoding="utf-8").read().splitlines() if not x.startswith("#")]
    same = sum(1 for x, y in zip(ra, rb) if x == y)
    first = next((i for i, (x, y) in enumerate(zip(ra, rb)) if x != y), None)
    print(f"{pa} vs {pb}: {len(ra)} / {len(rb)} batches, identical {same}, first difference {first}")
    if first is not None:
        print("  A:", ra[first])
        print("  B:", rb[first])
    return 0 if len(ra) == len(rb) == same else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--loader", choices=["old", "fast"])
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--batches", type=int, default=200)
    ap.add_argument("--val-batches", type=int, default=61)
    ap.add_argument("--out")
    ap.add_argument("--compare", nargs=2)
    a = ap.parse_args()
    if a.compare:
        return compare(*a.compare)
    return dump(a)


if __name__ == "__main__":
    sys.exit(main())
