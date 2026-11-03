#!/usr/bin/env python3
"""fl_equal.py - Opus R14-B: hash and time the batches of the old npt loader DLL or the fast loader (own code).

stdlib only (no torch, so no HIP runtime next to the live npt line). Each run sets its own priority class and CPU
mask first; the loader threads inherit both.

usage:
  python -I -B fl_equal.py dump --loader old  --dll <copy of libtraining_data_loader.dll> --workers 1 \
         --data <file.binpack> --batches 1000 --out old_w1.tsv [--mask 0xC] [--priority BelowNormal]
  python -I -B fl_equal.py dump --loader fast --dll <forge_fastloader.dll> --workers 2 --data ... --out fast_t2.tsv
  python -I -B fl_equal.py compare A.tsv B.tsv

Skip settings = the live npt line (--no-filtered --no-wld-filtered, other DataloaderSkipConfig defaults), feature
set K32H3, batch 16384, window 1,048,576 unless given. Output TSV: one line per batch (index, size, num_inputs,
max_active, white / black active counts, sha256 of the float block, sha256 of the int block), then '#' summary lines
(seconds, kept positions per second after the warm-up, preskip / total, peak working set).
"""

import argparse
import ctypes
import hashlib
import os
import sys
import time
from ctypes import POINTER, byref, c_bool, c_char_p, c_double, c_float, c_int, c_size_t, c_uint64, c_void_p

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "fastloader"))
import forge_fastloader as ffl  # noqa: E402


class SkipCfg:  # the npt line: --no-filtered --no-wld-filtered, everything else default
    filtered = False
    wld_filtered = False
    random_fen_skipping = 0
    early_fen_skipping = -1
    soft_early_fen_skipping = 20
    simple_eval_skipping = -1
    param_index = 0
    pc_y0, pc_y1, pc_y2, pc_y3, pc_y4 = 0.0, 0.4, 1.0, 1.0, 0.75
    ply_x1, ply_y1, ply_x2, ply_y2 = 0.0, 0.1, 6.0, 0.15
    ply_x3, ply_y3, ply_x4, ply_y4 = 10.0, 0.25, 18.0, 0.75


# C structs of the old loader's API (layout as its Python bindings declare them).
class CSkip(ctypes.Structure):
    _fields_ = [("filtered", c_bool), ("random_fen_skipping", c_int), ("wld_filtered", c_bool),
                ("early_fen_skipping", c_int), ("soft_early_fen_skipping", c_int),
                ("simple_eval_skipping", c_int), ("param_index", c_int)] + [
        (n, c_double) for n in ("pc_y0", "pc_y1", "pc_y2", "pc_y3", "pc_y4", "ply_x1", "ply_y1", "ply_x2",
                                "ply_y2", "ply_x3", "ply_y3", "ply_x4", "ply_y4")]


class CDdp(ctypes.Structure):
    _fields_ = [("rank", c_int), ("world_size", c_int)]


class CHll(ctypes.Structure):
    _fields_ = [("initial_hll", c_void_p), ("initial_hll_size", c_size_t), ("initial_total", c_uint64),
                ("initial_preskip", c_uint64)]


class CIo(ctypes.Structure):
    _fields_ = [("balance_window_mb", c_int), ("shuffle_buffer_entries", c_int)]


def fail(msg, code=2):
    """One clear line and exit (2 = bad usage or input); these used to end in tracebacks (bug hunt #16)."""
    print(f"{os.path.basename(sys.argv[0])}: {msg}", file=sys.stderr)
    sys.exit(code)


def need_new_output(path: str) -> None:
    """Checked BEFORE the work: an existing output used to be refused only when written, after the whole run."""
    if os.path.exists(path) or not os.path.isdir(os.path.dirname(os.path.abspath(path))):
        fail(f"{path}: exists or its folder is missing (outputs are never overwritten)")


def set_low(mask: str, priority: str) -> None:
    try:
        m = int(mask, 16)
    except ValueError:
        m = 0
    if m <= 0:
        fail(f"--mask {mask!r} is not a hexadecimal CPU mask naming at least one CPU")
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.GetCurrentProcess.restype = c_void_p
    h = k32.GetCurrentProcess()
    cls = {"BelowNormal": 0x4000, "Idle": 0x40}[priority]
    if not k32.SetPriorityClass(c_void_p(h), cls):
        fail(f"SetPriorityClass({priority}) failed: Windows error {ctypes.get_last_error()}")
    if not k32.SetProcessAffinityMask(c_void_p(h), c_size_t(m)):
        fail(f"SetProcessAffinityMask({mask}) failed: Windows error {ctypes.get_last_error()} (CPUs beyond this PC?)")


def peak_working_set_mb() -> float:
    class PMC(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
            (n, c_size_t) for n in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                                    "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                                    "PagefileUsage", "PeakPagefileUsage")]
    pmc = PMC()
    pmc.cb = ctypes.sizeof(PMC)
    k32 = ctypes.WinDLL("kernel32")
    k32.GetCurrentProcess.restype = c_void_p
    ctypes.WinDLL("psapi").GetProcessMemoryInfo(c_void_p(k32.GetCurrentProcess()), byref(pmc), pmc.cb)
    return pmc.PeakWorkingSetSize / 2**20


def batch_line(k: int, b) -> str:
    n, m = b.size, b.max_active_features
    floats = ctypes.string_at(ctypes.cast(b.is_white, c_void_p), 3 * n * 4)
    ints = ctypes.string_at(ctypes.cast(b.white, c_void_p), (2 * n * m + 2 * n) * 4)
    return (f"{k}\t{n}\t{b.num_inputs}\t{m}\t{b.num_active_white_features}\t{b.num_active_black_features}\t"
            f"{hashlib.sha256(floats).hexdigest()}\t{hashlib.sha256(ints).hexdigest()}")


def make_skip(overrides: str):
    """SkipCfg with 'name=value,...' overrides (type taken from the default)."""
    import types

    fields = {k: v for k, v in vars(SkipCfg).items() if not k.startswith("_")}
    for item in filter(None, (x.strip() for x in overrides.split(","))):
        k, v = item.split("=", 1)
        if k not in fields:
            raise SystemExit(f"unknown skip field {k}")
        d = fields[k]
        fields[k] = (v.lower() in ("1", "true")) if isinstance(d, bool) else type(d)(v)
    return types.SimpleNamespace(**fields)


class OldStream:
    def __init__(self, dll_path, data, batch, workers, cyclic, window, s):
        self.dll = dll = ctypes.CDLL(os.path.abspath(dll_path))
        dll.create_sparse_batch_stream.restype = c_void_p
        dll.create_sparse_batch_stream.argtypes = [c_char_p, c_int, c_int, POINTER(c_char_p), c_int, c_bool,
                                                   CSkip, CDdp, CHll, CIo]
        dll.fetch_next_sparse_batch.restype = POINTER(ffl.BatchView)
        dll.fetch_next_sparse_batch.argtypes = [c_void_p]
        dll.destroy_sparse_batch.argtypes = [POINTER(ffl.BatchView)]
        dll.destroy_sparse_batch_stream.argtypes = [c_void_p]
        dll.get_unique_position_stats.argtypes = [c_void_p] + [POINTER(c_uint64)] * 3
        skip = CSkip(s.filtered, s.random_fen_skipping, s.wld_filtered, s.early_fen_skipping,
                     s.soft_early_fen_skipping, s.simple_eval_skipping, s.param_index, s.pc_y0, s.pc_y1, s.pc_y2,
                     s.pc_y3, s.pc_y4, s.ply_x1, s.ply_y1, s.ply_x2, s.ply_y2, s.ply_x3, s.ply_y3, s.ply_x4,
                     s.ply_y4)
        names = (c_char_p * 1)(os.fsencode(os.path.abspath(data)))
        self.h = dll.create_sparse_batch_stream(b"K32H3", workers, 1, names, batch, cyclic, skip, CDdp(0, 1),
                                                CHll(None, 0, 0, 0), CIo(400, window))
        if not self.h:
            raise RuntimeError("old loader: create_sparse_batch_stream failed")

    def next(self):
        p = self.dll.fetch_next_sparse_batch(self.h)
        return p if p else None

    def release(self, p):
        self.dll.destroy_sparse_batch(p)

    def stats(self):
        a, b, c = c_uint64(0), c_uint64(0), c_uint64(0)
        self.dll.get_unique_position_stats(self.h, byref(a), byref(b), byref(c))
        return a.value, b.value

    def close(self):
        self.dll.destroy_sparse_batch_stream(self.h)


class NewStream:
    def __init__(self, dll_path, data, batch, workers, cyclic, window, s):
        self.s = ffl.FastStream(data, batch, threads=workers, cyclic=cyclic, skip_config=s,
                                window_entries=window, lib_path=dll_path)

    def next(self):
        return self.s.next_raw()

    def release(self, p):
        self.s.release(p)

    def stats(self):
        return self.s.stats()[:2]

    def close(self):
        self.s.close()


def cmd_dump(a) -> int:
    if a.batches < 1 or a.warmup < 0 or a.warmup >= a.batches:  # CR fix 2: else kept_per_s=0 from an empty timing
        fail(f"--warmup {a.warmup} / --batches {a.batches}: need 0 <= warmup < batches")
    need_new_output(a.out)
    for path, what in ((a.dll, "--dll"), (a.data, "--data")):
        if not os.path.isfile(path):
            fail(f"{what} {path}: file not found")
    set_low(a.mask, a.priority)
    cls = OldStream if a.loader == "old" else NewStream
    t0 = time.perf_counter()
    st = cls(a.dll, a.data, a.batch, a.workers, not a.finite, a.window, make_skip(a.skip))
    lines, kept_timed, t_warm = [], 0, None
    for k in range(a.batches):
        p = st.next()
        if p is None:
            break
        b = p.contents
        if k == a.warmup:
            t_warm = time.perf_counter()
        if k >= a.warmup:
            kept_timed += b.size
        lines.append(batch_line(k, b) if not a.no_hash else f"{k}\t{b.size}")
        st.release(p)
    t1 = time.perf_counter()
    preskip, total = st.stats()
    st.close()
    timed = (t1 - t_warm) if t_warm else float("nan")
    with open(a.out, "x", encoding="utf-8", newline="\n") as f:
        if lines:  # a stream with no batch writes no row (an empty row would count as one "batch" in compare)
            f.write("\n".join(lines) + "\n")
        f.write(f"# loader={a.loader} dll={os.path.abspath(a.dll)} workers={a.workers}\n")
        f.write(f"# settings batch={a.batch} window={a.window} cyclic={not a.finite} data={os.path.abspath(a.data)} "
                f"skip={a.skip or 'npt-default'}\n")
        f.write(f"# batches={len(lines)} seconds_total={t1 - t0:.3f} warmup={a.warmup} seconds_timed={timed:.3f} "
                f"kept_per_s={kept_timed / timed if timed == timed and timed > 0 else 0:.0f}\n")
        f.write(f"# preskip={preskip} total={total} peak_working_set_mb={peak_working_set_mb():.1f} "
                f"mask={a.mask} priority={a.priority} hashed={not a.no_hash}\n")
    print(f"{a.loader} w{a.workers}: {len(lines)} batches, {t1 - t0:.1f} s, "
          f"{kept_timed / timed if timed == timed and timed > 0 else 0:,.0f} kept/s after warm-up, "
          f"peak WS {peak_working_set_mb():.0f} MB -> {a.out}")
    return 0


def read_tsv(path):
    rows, meta = [], []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue  # dumps written before 14:25 have one empty row when the stream had no batch
                (meta if line.startswith("#") else rows).append(line.rstrip("\n"))
    except (OSError, UnicodeDecodeError) as e:
        fail(f"{path}: cannot read ({e})")
    return rows, meta


def cmd_compare(a) -> int:
    ra, ma = read_tsv(a.a)
    rb, mb = read_tsv(a.b)
    for path, meta in ((a.a, ma), (a.b, mb)):
        if not any("hashed=True" in m for m in meta):
            print(f"{path}: not a hashed dump (made with --no-hash): no equality claim possible")
            return 2
    sa = [m for m in ma if m.startswith("# settings")]
    sb = [m for m in mb if m.startswith("# settings")]
    if sa != sb and not (a.legacy and not sa and not sb):
        print(f"settings differ or are missing:\n  {sa}\n  {sb}")
        return 2
    n = min(len(ra), len(rb))
    if not ra and not rb:  # two dumps without a batch used to compare as identical (bug hunt #16)
        print(f"{a.a} vs {a.b}: no batch in either dump - nothing compared, no equality claim possible")
        return 2
    same = sum(1 for i in range(n) if ra[i] == rb[i])
    first = next((i for i in range(n) if ra[i] != rb[i]), None)
    print(f"{a.a} vs {a.b}: compared {n} batches (lengths {len(ra)} / {len(rb)}), identical {same}, "
          f"first difference {first}")
    if first is not None:
        print("  A:", ra[first])
        print("  B:", rb[first])
    return 0 if same == n == len(ra) == len(rb) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dump")
    d.add_argument("--loader", choices=["old", "fast"], required=True)
    d.add_argument("--dll", required=True)
    d.add_argument("--data", required=True)
    d.add_argument("--workers", type=int, default=1)
    d.add_argument("--batch", type=int, default=16384)
    d.add_argument("--window", type=int, default=1048576)
    d.add_argument("--batches", type=int, default=1000)
    d.add_argument("--warmup", type=int, default=0)
    d.add_argument("--finite", action="store_true", help="non-cyclic stream")
    d.add_argument("--no-hash", action="store_true", help="speed runs: skip the sha256")
    d.add_argument("--skip", default="", help="skip-config overrides, e.g. random_fen_skipping=3,pc_y1=0")
    d.add_argument("--out", required=True)
    d.add_argument("--mask", default="0xC")
    d.add_argument("--priority", default="BelowNormal", choices=["BelowNormal", "Idle"])
    c = sub.add_parser("compare")
    c.add_argument("a")
    c.add_argument("b")
    c.add_argument("--legacy", action="store_true", help="dumps from before the '# settings' line (12:35-12:40 runs)")
    a = ap.parse_args()
    return cmd_dump(a) if a.cmd == "dump" else cmd_compare(a)


if __name__ == "__main__":
    sys.exit(main())
