#!/usr/bin/env python3
"""install_fast_loader.py - Opus R14-B: add the --fast-loader switch to a COPY of the npt trainer (own code).

usage: python -I -B install_fast_loader.py TRAINER_COPY_DIR [--check]
Edits config.py (new option `fast_loader`, default False) and train.py (make_data_loaders picks
forge_fastloader.FastSparseBatchDataset for the training and the validation stream; start-up line with the DLL path,
sha256 and version). Exact anchors, CRLF/LF kept as found; refuses a trainer that is already patched or whose anchor
text differs (exit 2). --check only reports. Never run it on the live trainer folder: the queue's trainer is not ours
to change; Engine NNUE / QA decide. The equivalent diff is patches/0005-fast-loader-switch.patch.
The loader files (forge_fastloader.py + forge_fastloader.dll) go next to train.py or into FORGE_FAST_LOADER_DIR.
"""

import sys
from pathlib import Path

CONFIG = [(
    '''    num_workers: int = 1
    """Number of worker threads to use for data loading. Currently only works well for binpack."""
''',
    '''    num_workers: int = 1
    """Number of worker threads to use for data loading. Currently only works well for binpack."""

    fast_loader: bool = False
    """Opus R14-B: read the binpacks with forge_fastloader (forge_fastloader.py + .dll next to train.py, or
    FORGE_FAST_LOADER_DIR). Same batches as --num-workers 1 of the default loader at any --num-workers; unchained
    binpack, one file per stream, --no-filtered --no-wld-filtered, feature set K32H3 only. Off by default."""
''')]

TRAIN = [
    ('''    rank=0,
    world_size=1,
):
    # Epoch and validation sizes are global; shard across DDP ranks.
    features_name = feature_name
''', '''    rank=0,
    world_size=1,
    fast_loader=False,
):
    # Epoch and validation sizes are global; shard across DDP ranks.
    features_name = feature_name
    sparse_dataset = data_loader.SparseBatchDataset
    if fast_loader:  # Opus R14-B --fast-loader: forge_fastloader.py + .dll from FORGE_FAST_LOADER_DIR or next to train.py
        import importlib.util

        fl_dir = os.environ.get("FORGE_FAST_LOADER_DIR", os.path.dirname(os.path.abspath(__file__)))
        spec = importlib.util.spec_from_file_location("forge_fastloader", os.path.join(fl_dir, "forge_fastloader.py"))
        forge_fastloader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(forge_fastloader)
        info = forge_fastloader.library_info()
        print(f"Fast loader: ON ({info['version']}, {info['path']}, sha256 {info['sha256']})", flush=True)
        sparse_dataset = forge_fastloader.FastSparseBatchDataset
    else:
        print("Fast loader: off", flush=True)
'''),
    ('''    train_infinite = data_loader.SparseBatchDataset(
''', '''    train_infinite = sparse_dataset(
'''),
    ('''        val_infinite = data_loader.SparseBatchDataset(
''', '''        val_infinite = sparse_dataset(
'''),
    ('''        rank=rank,
        world_size=world_size,
    )

    optimizer_and_schedulers''', '''        rank=rank,
        world_size=world_size,
        fast_loader=args.fast_loader,
    )

    optimizer_and_schedulers'''),
]


def patch(path: Path, pairs, check: bool) -> bool:
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8").replace("\r\n", "\n")
    if "fast_loader" in text:
        print(f"{path}: already patched")
        return False
    for old, _ in pairs:
        if text.count(old) != 1:
            print(f"{path}: anchor not found exactly once: {old.splitlines()[0]!r}")
            return False
    if check:
        print(f"{path}: anchors OK")
        return True
    for old, new in pairs:
        text = text.replace(old, new)
    path.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))
    print(f"{path}: patched ({'CRLF' if crlf else 'LF'})")
    return True


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    root = Path(sys.argv[1])
    check = "--check" in sys.argv[2:]
    ok = patch(root / "config.py", CONFIG, True) and patch(root / "train.py", TRAIN, True)
    if not ok:
        return 2
    if not check:
        patch(root / "config.py", CONFIG, False)
        patch(root / "train.py", TRAIN, False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
