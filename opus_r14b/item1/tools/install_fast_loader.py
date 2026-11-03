#!/usr/bin/env python3
"""install_fast_loader.py - Opus R14-B: add the --fast-loader switch to a COPY of the npt trainer (own code).

usage: python -I -B install_fast_loader.py TRAINER_COPY_DIR [--check] [--loader-dll PATH]
Edits config.py (new option `fast_loader`, default False) and train.py (make_data_loaders picks
forge_fastloader.FastSparseBatchDataset for the training and the validation stream; start-up line with the DLL path,
sha256 and version). Exact anchors, CRLF/LF kept as found; refuses a trainer that is already patched or whose anchor
text differs (exit 2). --check only reports. Never run it on the live trainer folder: the queue's trainer is not ours
to change; Engine NNUE / QA decide (it refuses F:\opus_scratch\r6\nnue-pytorch-amd except with --check). Unknown
arguments and a folder without readable config.py / train.py are exit 2 as well; nothing is changed unless every
check passed. The equivalent diff is patches/0005-fast-loader-switch.patch.
The loader files (forge_fastloader.py + forge_fastloader.dll) go next to train.py or into FORGE_FAST_LOADER_DIR;
--loader-dll PATH copies that DLL and this branch's fastloader/forge_fastloader.py next to train.py (never over an
existing file) and prints both sha256 values (the tested DLL b5 is 9eb29b7d...; fastloader/build_fastloader.sh
rebuilds it byte for byte).
"""

import hashlib
import os
import shutil
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


LIVE_TRAINER = Path(r"F:\opus_scratch\r6\nnue-pytorch-amd")  # the queue's npt trainer (2026-11-02): never ours to change


def patch(path: Path, pairs, check: bool) -> bool:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8").replace("\r\n", "\n")
    except (OSError, UnicodeDecodeError) as e:
        print(f"{path}: cannot read it as a trainer file ({type(e).__name__}: {e})")
        return False
    crlf = b"\r\n" in raw
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


def is_live(root: Path) -> bool:
    """The live trainer folder under any spelling. The path comparison alone missed the \\\\?\\ form of the same folder
    (final bug hunt 2026-11-03 04:31: shown on a stand-in, which it patched), so the file identity decides first."""
    try:
        if os.path.samefile(root, LIVE_TRAINER):
            return True
    except OSError:  # one of them missing (another PC): the paths decide
        pass
    return root.resolve() == LIVE_TRAINER.resolve()


def copy_loader(root: Path, dll: Path, check: bool, quiet: bool = False) -> bool:
    """--loader-dll: the DLL and this branch's forge_fastloader.py next to train.py; refuses to overwrite. With check
    it only validates (and says what it would copy unless quiet)."""
    py = Path(__file__).resolve().parent.parent / "fastloader" / "forge_fastloader.py"
    pairs = [(dll, root / "forge_fastloader.dll"), (py, root / "forge_fastloader.py")]
    for src, dst in pairs:
        if not src.is_file():
            print(f"{src}: not found")
            return False
        if dst.exists():
            print(f"{dst}: exists, not overwritten")
            return False
    for src, dst in pairs:
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        if check:
            if not quiet:
                print(f"would copy {src} -> {dst} (sha256 {digest})")
        else:
            shutil.copyfile(src, dst)
            print(f"copied {src} -> {dst} (sha256 {digest})")
    return True


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        return 2
    root = Path(args[0])
    check, dll, rest = False, None, args[1:]
    while rest:  # an unknown or misspelt option (e.g. --chek) must not turn a check into an install
        if rest[0] == "--check":
            check, rest = True, rest[1:]
        elif rest[0] == "--loader-dll" and len(rest) > 1:
            dll, rest = Path(rest[1]), rest[2:]
        else:
            print(f"unknown or incomplete argument {rest[0]!r}\n{__doc__}")
            return 2
    if not check and is_live(root):
        print(f"{root} is the live npt trainer: install into a COPY (HANDOFF.md step 1); --check is allowed here")
        return 2
    ok = patch(root / "config.py", CONFIG, True) and patch(root / "train.py", TRAIN, True)
    if ok and dll is not None:
        ok = copy_loader(root, dll, True, quiet=not check)  # validate first: nothing is changed unless all is fine
    if not ok:
        return 2
    if not check:
        patch(root / "config.py", CONFIG, False)
        patch(root / "train.py", TRAIN, False)
        if dll is not None:
            copy_loader(root, dll, False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
