"""forge_fastloader.py - Opus R14-B: Python side of the fast npt data loader (own code, 2026-11-02).

Two layers:
- FastStream: stdlib-only ctypes wrapper of forge_fastloader.dll (raw SparseBatch-layout batches). Used by the
  equality / speed tools without torch, so no HIP runtime is loaded next to the live npt line.
- FastSparseBatchDataset: drop-in for the trainer's data_loader.SparseBatchDataset (same constructor arguments,
  same cyclic caching, same tensors via the trainer's own SparseBatch.get_tensors). Selected by --fast-loader.

The DLL is found via FORGE_FAST_LOADER_LIB, else next to this file. Behaviour: ../LOADER_SPEC.md. Anything outside
the proven scope (chained binpack, more than one file, filtered / wld_filtered / simple-eval skipping, DDP with
more than one rank, a feature set other than K32H3) raises instead of silently differing from the old loader.
"""

from __future__ import annotations

import ctypes
import os
import threading
from ctypes import POINTER, byref, c_char_p, c_double, c_float, c_int, c_uint64, c_void_p

SUPPORTED_FEATURE_SET = "K32H3"


class FflConfig(ctypes.Structure):
    _fields_ = [
        ("batch_size", c_int),
        ("threads", c_int),
        ("cyclic", c_int),
        ("window_entries", c_int),
        ("random_fen_skipping", c_int),
        ("early_fen_skipping", c_int),
        ("soft_early_fen_skipping", c_int),
        ("filtered", c_int),
        ("wld_filtered", c_int),
        ("simple_eval_skipping", c_int),
        ("max_live_windows", c_int),
        ("ring_batches", c_int),
        ("pc_y", c_double * 5),
        ("ply_x", c_double * 4),
        ("ply_y", c_double * 4),
    ]


class BatchView(ctypes.Structure):
    """Same field layout as the trainer's data_loader._native.SparseBatch."""

    _fields_ = [
        ("num_inputs", c_int),
        ("size", c_int),
        ("is_white", POINTER(c_float)),
        ("outcome", POINTER(c_float)),
        ("score", POINTER(c_float)),
        ("num_active_white_features", c_int),
        ("num_active_black_features", c_int),
        ("max_active_features", c_int),
        ("white", POINTER(c_int)),
        ("black", POINTER(c_int)),
        ("piece_count", POINTER(c_int)),
        ("queen_bucket", POINTER(c_int)),
    ]


_LIBS: dict[str, ctypes.CDLL] = {}
_LIBS_LOCK = threading.Lock()


def load_library(path: str | None = None) -> ctypes.CDLL:
    path = path or os.environ.get("FORGE_FAST_LOADER_LIB", "").strip() or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "forge_fastloader.dll"
    )
    path = os.path.abspath(path)
    with _LIBS_LOCK:
        if path in _LIBS:
            return _LIBS[path]
        lib = ctypes.CDLL(path)
        lib.ffl_version.restype = c_char_p
        lib.ffl_config_size.restype = c_int
        lib.ffl_create.restype = c_void_p
        lib.ffl_create.argtypes = [POINTER(FflConfig), c_char_p]
        lib.ffl_create_error.restype = c_char_p
        lib.ffl_next.restype = POINTER(BatchView)
        lib.ffl_next.argtypes = [c_void_p]
        lib.ffl_release.restype = None
        lib.ffl_release.argtypes = [c_void_p, POINTER(BatchView)]
        lib.ffl_stats.restype = None
        lib.ffl_stats.argtypes = [c_void_p, POINTER(c_uint64), POINTER(c_uint64), POINTER(c_uint64)]
        lib.ffl_error.restype = c_int
        lib.ffl_error.argtypes = [c_void_p, c_char_p, c_int]
        lib.ffl_destroy.restype = None
        lib.ffl_destroy.argtypes = [c_void_p]
        if lib.ffl_config_size() != ctypes.sizeof(FflConfig):
            raise RuntimeError(f"{path}: FflConfig size {lib.ffl_config_size()} != {ctypes.sizeof(FflConfig)}")
        _LIBS[path] = lib
        return lib


def _get(cfg, name, default):
    return getattr(cfg, name, default) if cfg is not None else default


def make_config(batch_size, threads, cyclic, skip_config=None, window_entries=0) -> FflConfig:
    """Translate a DataloaderSkipConfig-like object (attributes as in the trainer) into FflConfig."""
    c = FflConfig()
    c.batch_size = int(batch_size)
    c.threads = max(1, int(threads))
    c.cyclic = 1 if cyclic else 0
    c.window_entries = int(window_entries)
    c.filtered = 1 if _get(skip_config, "filtered", True) else 0
    c.wld_filtered = 1 if _get(skip_config, "wld_filtered", True) else 0
    c.random_fen_skipping = int(_get(skip_config, "random_fen_skipping", 0))
    c.early_fen_skipping = int(_get(skip_config, "early_fen_skipping", -1))
    c.soft_early_fen_skipping = int(_get(skip_config, "soft_early_fen_skipping", 20))
    c.simple_eval_skipping = int(_get(skip_config, "simple_eval_skipping", -1))
    c.max_live_windows = 0
    c.ring_batches = 0
    pc_defaults = (0.0, 0.4, 1.0, 1.0, 0.75)
    for i in range(5):
        c.pc_y[i] = float(_get(skip_config, f"pc_y{i}", pc_defaults[i]))
    ply_defaults = ((0.0, 0.1), (6.0, 0.15), (10.0, 0.25), (18.0, 0.75))
    for i in range(4):
        c.ply_x[i] = float(_get(skip_config, f"ply_x{i + 1}", ply_defaults[i][0]))
        c.ply_y[i] = float(_get(skip_config, f"ply_y{i + 1}", ply_defaults[i][1]))
    if c.filtered or c.wld_filtered or c.simple_eval_skipping > 0:
        raise ValueError(
            "--fast-loader supports --no-filtered --no-wld-filtered without simple-eval skipping only"
        )
    return c


class FastStream:
    """One fast-loader stream over one binpack file (raw batches, no torch)."""

    def __init__(self, filename, batch_size, threads=1, cyclic=True, skip_config=None, window_entries=0,
                 lib_path=None):
        self.lib = load_library(lib_path)
        self.config = make_config(batch_size, threads, cyclic, skip_config, window_entries)
        self.handle = self.lib.ffl_create(byref(self.config), os.fsencode(os.path.abspath(filename)))
        if not self.handle:
            raise RuntimeError(f"fast loader: {self.lib.ffl_create_error().decode('utf-8', 'replace')}")

    def error(self) -> str:
        buf = ctypes.create_string_buffer(1024)
        n = self.lib.ffl_error(self.handle, buf, len(buf))
        return buf.value.decode("utf-8", "replace") if n else ""

    def next_raw(self):
        """Pointer to the next batch, or None at the end of a finite stream. Raises on a loader error."""
        p = self.lib.ffl_next(self.handle)
        if not p:
            err = self.error()
            if err:
                raise RuntimeError(f"fast loader: {err}")
            return None
        return p

    def release(self, p) -> None:
        self.lib.ffl_release(self.handle, p)

    def stats(self) -> tuple[int, int, int]:
        preskip, total, batches = c_uint64(0), c_uint64(0), c_uint64(0)
        self.lib.ffl_stats(self.handle, byref(preskip), byref(total), byref(batches))
        return preskip.value, total.value, batches.value

    def close(self) -> None:
        if getattr(self, "handle", None):
            self.lib.ffl_destroy(self.handle)
            self.handle = None

    def __del__(self):
        self.close()


def _check_scope(feature_set, filenames, ddp_config):
    name = feature_set.decode() if isinstance(feature_set, bytes) else str(feature_set)
    if name != SUPPORTED_FEATURE_SET:
        raise ValueError(f"--fast-loader supports feature set {SUPPORTED_FEATURE_SET} only, got {name!r}")
    if len(filenames) != 1:
        raise ValueError(f"--fast-loader reads exactly one binpack per stream, got {len(filenames)}")
    if ddp_config is not None and int(getattr(ddp_config, "world_size", 1)) != 1:
        raise ValueError("--fast-loader does not support DDP (world_size > 1)")


class FastSparseBatchProvider:
    """Iterator with the interface of the trainer's SparseBatchProvider."""

    def __init__(self, feature_set, filenames, batch_size, cyclic=True, num_workers=1, config=None,
                 ddp_config=None, io_config=None, use_pinned_memory=False, device="cpu"):
        _check_scope(feature_set, filenames, ddp_config)
        window = int(getattr(io_config, "shuffle_buffer_entries", 0)) if io_config is not None else 0
        self.stream = FastStream(filenames[0], batch_size, threads=num_workers, cyclic=cyclic,
                                 skip_config=config, window_entries=window)
        self.use_pinned_memory = use_pinned_memory
        self.device = device
        from data_loader._native import SparseBatch  # the trainer's own tensor conversion

        self._batch_ptr_type = POINTER(SparseBatch)

    def __iter__(self):
        return self

    def __next__(self):
        p = self.stream.next_raw()
        if p is None:
            raise StopIteration
        try:
            batch = ctypes.cast(p, self._batch_ptr_type).contents
            return batch.get_tensors(self.device, use_pinned_memory=self.use_pinned_memory)
        finally:
            self.stream.release(p)

    def get_unique_stats(self) -> tuple[int, int, int]:
        """(preskip, total, unique): exact read / kept counts; unique is not tracked (0)."""
        preskip, total, _ = self.stream.stats()
        return preskip, total, 0

    def get_hll_state(self) -> bytes:
        return b""  # no HyperLogLog: the trainer then skips its unique-position metrics

    def get_io_stats(self) -> list[dict]:
        return []

    def __del__(self):
        stream = getattr(self, "stream", None)
        if stream is not None:
            stream.close()


def _make_dataset_class():
    import torch  # only the trainer path needs torch; the raw layer above does not

    class FastSparseBatchDataset(torch.utils.data.IterableDataset):
        """Drop-in for data_loader.SparseBatchDataset (same arguments; hll_config is accepted and ignored)."""

        def __init__(self, feature_set, filenames, batch_size, cyclic=True, num_workers=1, config=None,
                     ddp_config=None, hll_config=None, io_config=None, use_pinned_memory=False):
            super().__init__()
            _check_scope(feature_set, filenames, ddp_config)
            self.feature_set = feature_set
            self.filenames = filenames
            self.batch_size = batch_size
            self.cyclic = cyclic
            self.num_workers = num_workers
            self.config = config
            self.ddp_config = ddp_config
            self.io_config = io_config
            self.use_pinned_memory = use_pinned_memory
            self.device = "cpu"
            self._cached_iter = None
            self._iter_lock = threading.Lock()

        def _new_provider(self):
            return FastSparseBatchProvider(self.feature_set, self.filenames, self.batch_size, cyclic=self.cyclic,
                                           num_workers=self.num_workers, config=self.config,
                                           ddp_config=self.ddp_config, io_config=self.io_config,
                                           use_pinned_memory=self.use_pinned_memory, device=self.device)

        def __iter__(self):
            # Same rule as the trainer: a cyclic stream is created once and shared, a finite one per iteration.
            if not self.cyclic:
                return self._new_provider()
            with self._iter_lock:
                if self._cached_iter is None:
                    self._cached_iter = self._new_provider()
                else:
                    self._cached_iter.use_pinned_memory = self.use_pinned_memory
                    self._cached_iter.device = self.device
                return self._cached_iter

    return FastSparseBatchDataset


def __getattr__(name):  # PEP 562: build the torch dataset class on first use
    if name == "FastSparseBatchDataset":
        cls = _make_dataset_class()
        globals()[name] = cls
        return cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
