"""R11 pipeline: shared helpers (logging, atomic files, fingerprints, resource governor, FPOS/FHCE I/O, keys).

Every stage logs one line per event to <root>/logs/pipeline.log and stdout:
  2026-10-30T10:45:00 [data] PASS ...   /  FAIL ...  /  INFO ...  /  WAIT ...
A stage ends with exactly one "[<stage>] PASS" or "[<stage>] FAIL" summary line.
"""
from __future__ import annotations

import ctypes
import fnmatch
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import time
from ctypes import wintypes
from dataclasses import dataclass

import numpy as np

FPOS_MAGIC = b"FPOS"
FHCE_MAGIC = b"FHCE"
HEADER = 16


# ----------------------------------------------------------------------------------------------------------------
# logging
# ----------------------------------------------------------------------------------------------------------------
class Log:
    def __init__(self, path: str | None, stage: str):
        self.path = path
        self.stage = stage
        if path:
            os.makedirs(os.path.dirname(path), exist_ok=True)

    def _emit(self, kind: str, msg: str) -> None:
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} [{self.stage}] {kind} {msg}"
        print(line, flush=True)
        if self.path:
            with open(self.path, "a", encoding="utf-8", newline="\n") as f:
                f.write(line + "\n")

    def info(self, msg: str) -> None:
        self._emit("INFO", msg)

    def wait(self, msg: str) -> None:
        self._emit("WAIT", msg)

    def ok(self, msg: str) -> None:
        self._emit("PASS", msg)

    def fail(self, msg: str) -> None:
        self._emit("FAIL", msg)

    def sub(self, stage: str) -> "Log":
        return Log(self.path, stage)


class StageFailed(Exception):
    pass


# ----------------------------------------------------------------------------------------------------------------
# files
# ----------------------------------------------------------------------------------------------------------------
def write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, sort_keys=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def read_json(path: str, default=None):
    if not os.path.isfile(path):
        return default
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def sha256_file(path: str, bufsize: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def fingerprint(path: str) -> dict:
    """Cheap identity of an input file: size, mtime and sha256 of its first and last MiB."""
    st = os.stat(path)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read(1 << 20))
        if st.st_size > (1 << 20):
            f.seek(max(0, st.st_size - (1 << 20)))
            h.update(f.read(1 << 20))
    return {"size": st.st_size, "mtime_ns": st.st_mtime_ns, "edges_sha256": h.hexdigest()}


def same_fingerprint(a: dict, b: dict) -> bool:
    return a.get("size") == b.get("size") and a.get("edges_sha256") == b.get("edges_sha256")


def winpath(p: str) -> str:
    """Windows-style absolute path with forward slashes (the engine and the trainer cannot open /d/... paths)."""
    p = os.path.abspath(p)
    m = re.match(r"^[\\/]([a-zA-Z])[\\/](.*)$", p)
    if m:
        p = m.group(1).upper() + ":/" + m.group(2)
    return p.replace("\\", "/")


# ----------------------------------------------------------------------------------------------------------------
# FPOS / FHCE
# ----------------------------------------------------------------------------------------------------------------
def fpos_rows(path: str) -> int:
    with open(path, "rb") as f:
        head = f.read(HEADER)
    if len(head) != HEADER or head[:4] != FPOS_MAGIC:
        raise StageFailed(f"not an FPOS file: {path}")
    ver = int.from_bytes(head[4:8], "little")
    n = int.from_bytes(head[8:16], "little")
    if ver != 1:
        raise StageFailed(f"FPOS version {ver} != 1: {path}")
    size = os.path.getsize(path)
    if size != HEADER + 35 * n:
        raise StageFailed(f"FPOS size {size} != 16 + 35 * {n}: {path}")
    return n


def fhce_rows(path: str) -> int:
    with open(path, "rb") as f:
        head = f.read(HEADER)
    if len(head) != HEADER or head[:4] != FHCE_MAGIC:
        raise StageFailed(f"not an FHCE file: {path}")
    n = int.from_bytes(head[8:16], "little")
    size = os.path.getsize(path)
    if size != HEADER + 2 * n:
        raise StageFailed(f"FHCE size {size} != 16 + 2 * {n}: {path}")
    return n


def read_boards(path: str, n: int, start: int, count: int) -> np.ndarray:
    a = np.fromfile(path, dtype=np.uint8, count=count * 32, offset=HEADER + start * 32)
    if a.size != count * 32:
        raise StageFailed(f"short read of boards {path} [{start}, {start + count})")
    return a.reshape(count, 32)


def read_scores(path: str, n: int, start: int, count: int) -> np.ndarray:
    a = np.fromfile(path, dtype="<i2", count=count, offset=HEADER + 32 * n + start * 2)
    if a.size != count:
        raise StageFailed(f"short read of scores {path}")
    return a


def read_meta(path: str, n: int, start: int, count: int) -> np.ndarray:
    a = np.fromfile(path, dtype=np.uint8, count=count, offset=HEADER + 34 * n + start)
    if a.size != count:
        raise StageFailed(f"short read of meta {path}")
    return a


def read_hce(path: str, start: int, count: int) -> np.ndarray:
    a = np.fromfile(path, dtype="<i2", count=count, offset=HEADER + start * 2)
    if a.size != count:
        raise StageFailed(f"short read of hce {path}")
    return a


_M1 = np.uint64(0xFF51AFD7ED558CCD)
_M2 = np.uint64(0xC4CEB9FE1A85EC53)
_SEED = np.uint64(0x52313149_44454450)  # "R11IDEDP"
_STM = np.uint64(0x9E3779B97F4A7C15)
_S33 = np.uint64(33)


def _fmix(x: np.ndarray) -> np.ndarray:
    x ^= x >> _S33
    x *= _M1
    x ^= x >> _S33
    x *= _M2
    x ^= x >> _S33
    return x


def position_keys(boards: np.ndarray, meta: np.ndarray) -> np.ndarray:
    """64-bit identity of (32-byte board, side to move). Same board + stm -> same key in every source."""
    w = np.ascontiguousarray(boards).view("<u8").reshape(-1, 4)
    with np.errstate(over="ignore"):
        h = _fmix(w[:, 0] ^ _SEED)
        h ^= w[:, 1]
        h = _fmix(h)
        h ^= w[:, 2]
        h = _fmix(h)
        h ^= w[:, 3] ^ ((meta & 1).astype(np.uint64) * _STM)
        h = _fmix(h)
    return h


def bad_rows(boards: np.ndarray, meta: np.ndarray) -> np.ndarray:
    """Rows the binpack writer would reject cheaply: a nibble code > 12, not exactly one king per side,
    a result code > 2."""
    lo = boards & 15
    hi = boards >> 4
    bad = (lo > 12).any(axis=1) | (hi > 12).any(axis=1)
    wk = (lo == 6).sum(axis=1) + (hi == 6).sum(axis=1)
    bk = (lo == 12).sum(axis=1) + (hi == 12).sum(axis=1)
    bad |= (wk != 1) | (bk != 1)
    bad |= ((meta >> 1) & 3) > 2
    return bad


# dest codes, 2 bits per row (4 rows per byte, row i -> byte i >> 2, bits 2 * (i & 3))
DEST_DROP, DEST_TRAIN, DEST_HOLD, DEST_BAD = 0, 1, 2, 3


def pack_dest(dest: np.ndarray) -> np.ndarray:
    n = dest.size
    pad = (-n) % 4
    d = np.concatenate([dest.astype(np.uint8), np.zeros(pad, np.uint8)]).reshape(-1, 4)
    return (d[:, 0] | (d[:, 1] << 2) | (d[:, 2] << 4) | (d[:, 3] << 6)).astype(np.uint8)


def unpack_dest(packed: np.ndarray, n: int) -> np.ndarray:
    p = packed.astype(np.uint8)
    d = np.stack([p & 3, (p >> 2) & 3, (p >> 4) & 3, (p >> 6) & 3], axis=1).reshape(-1)
    return d[:n]


# ----------------------------------------------------------------------------------------------------------------
# machine state and governor
# ----------------------------------------------------------------------------------------------------------------
class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def memory_gb() -> tuple[float, float]:
    """(available physical RAM GB, available commit GB) - the R6 incident was a commit-limit death."""
    if sys.platform != "win32":
        return 64.0, 64.0
    ms = _MEMORYSTATUSEX()
    ms.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
    return ms.ullAvailPhys / 2**30, ms.ullAvailPageFile / 2**30


def _system_times() -> tuple[int, int, int]:
    idle, kernel, user = wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME()
    ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user))

    def v(ft):
        return (ft.dwHighDateTime << 32) | ft.dwLowDateTime

    return v(idle), v(kernel), v(user)


def cpu_load(interval: float = 1.0) -> float:
    """System CPU load in percent over `interval` seconds (kernel time includes idle time on Windows)."""
    if sys.platform != "win32":
        return 0.0
    i0, k0, u0 = _system_times()
    time.sleep(interval)
    i1, k1, u1 = _system_times()
    total = (k1 - k0) + (u1 - u0)
    if total <= 0:
        return 0.0
    return 100.0 * (1.0 - (i1 - i0) / total)


def disk_free_gb(path: str) -> float:
    p = os.path.abspath(path)
    while not os.path.exists(p):
        p = os.path.dirname(p)
    return shutil.disk_usage(p).free / 2**30


IDLE_PRIORITY_CLASS = 0x00000040
PROCESS_MODE_BACKGROUND_BEGIN = 0x00100000
DEFAULT_AFFINITY = 0x700  # CPUs 8-10: three cores (the PC's known 3-CPU mask)


def affinity_from_cfg(cfg: dict) -> int:
    v = cfg.get("limits", {}).get("affinity_mask", DEFAULT_AFFINITY)
    return int(v, 0) if isinstance(v, str) else int(v)


def set_idle_background(mask: int = DEFAULT_AFFINITY) -> dict:
    """CR fix 2: background mode (very low I/O and memory priority) + Idle priority class (0x40) on at most 3 cores.
    BelowNormal would outrank the Idle trainer and self-play.
    ORDER MATTERS (measured 2026-10-30): PROCESS_MODE_BACKGROUND_BEGIN resets the class to Normal (base priority 8)
    and children then inherit Normal; background first and Idle second gives class Idle (base 4) with I/O priority
    very low, and children inherit both and the affinity mask."""
    if bin(mask).count("1") > 3 or mask <= 0:
        raise StageFailed(f"affinity mask {hex(mask)} must select 1..3 CPUs")
    if sys.platform != "win32":
        return {}
    k32 = ctypes.windll.kernel32
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    k32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
    h = k32.GetCurrentProcess()
    ok_bg = bool(k32.SetPriorityClass(h, PROCESS_MODE_BACKGROUND_BEGIN))
    ok_idle = bool(k32.SetPriorityClass(h, IDLE_PRIORITY_CLASS))
    ok_aff = bool(k32.SetProcessAffinityMask(h, mask))
    if not (ok_idle and ok_aff):
        raise StageFailed(f"could not set Idle priority / affinity {hex(mask)} (idle {ok_idle}, affinity {ok_aff})")
    return {"priority": "Idle", "background_mode": ok_bg, "affinity": hex(mask)}


def priority_name() -> str:
    if sys.platform != "win32":
        return "n/a"
    pc = ctypes.windll.kernel32.GetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess())
    return {0x40: "Idle", 0x4000: "BelowNormal", 0x20: "Normal", 0x8000: "AboveNormal", 0x80: "High"}.get(pc, hex(pc))


FAIL_CLOSED = {"pid": -1, "name": "unknown", "pattern": "process list unavailable (fail closed)"}


def production_processes(patterns: list[str]) -> list[dict]:
    """Processes whose command line matches one of the regexes. Only pid, name and the matched pattern are
    returned (command lines are never logged).
    Fails CLOSED: when psutil is missing or the process list cannot be read, the result is a single
    FAIL_CLOSED entry, so every caller treats production as running (wait / do not start)."""
    try:
        import psutil
    except ImportError:
        return [dict(FAIL_CLOSED, pattern="psutil missing (fail closed)")]
    me = os.getpid()
    found = []
    regs = [re.compile(p, re.I) for p in patterns]
    try:
        procs = list(psutil.process_iter(["pid", "name", "cmdline"]))
    except Exception as e:  # noqa: BLE001 - any failure to list processes must fail closed
        return [dict(FAIL_CLOSED, pattern=f"process_iter failed: {type(e).__name__} (fail closed)")]
    for p in procs:
        try:
            if p.info["pid"] == me:
                continue
            cmd = " ".join(p.info["cmdline"] or [])
        except Exception:
            continue
        for r in regs:
            if r.search(cmd):
                found.append({"pid": p.info["pid"], "name": p.info["name"], "pattern": r.pattern})
                break
    return found


# Paths the pipeline must never write into (production, live data, gate/lock/queue folders, other agents' data).
PROTECTED_ROOTS = [
    "f:/forge_j1_data", "f:/forge_nnue_train", "d:/forge_nnue_train", "d:/forge_j1_data_astra",
    "d:/grok-pc-data/forge_push", "d:/grok-pc-data/selfplay_out", "d:/grok-pc-data/selfplay_out_r8v5_20261029",
    "c:/users/administrator/grok-pc", "f:/nnue_pytorch",
]


def assert_writable_path(path: str) -> None:
    p = winpath(path).lower().rstrip("/") + "/"
    for root in PROTECTED_ROOTS:
        if p.startswith(root.rstrip("/") + "/"):
            raise StageFailed(f"refusing to write under a protected folder: {path} (protected root {root})")


@dataclass
class Limits:
    min_free_ram_gb: float = 8.0
    min_free_commit_gb: float = 8.0
    max_cpu_percent: float = 85.0
    min_disk_free_gb: float = 15.0
    poll_seconds: float = 30.0
    affinity_mask: str | int = "0x700"


HOLD_EVENT = "Local\\Forge_R11_Hold"


def hold_requested() -> bool:
    """True while the named event Local\\Forge_R11_Hold exists and is signalled (CR fix 1: no STOP/PAUSE files).
    Hold with `r11_hold.py hold [--minutes N]`; stop R11 by its own PID (it resumes from its done markers)."""
    if sys.platform != "win32":
        return False
    k32 = ctypes.windll.kernel32
    k32.OpenEventW.restype = wintypes.HANDLE
    k32.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    SYNCHRONIZE = 0x00100000
    h = k32.OpenEventW(SYNCHRONIZE, False, HOLD_EVENT)
    if not h:
        return False
    try:
        return k32.WaitForSingleObject(h, 0) == 0  # WAIT_OBJECT_0: signalled
    finally:
        k32.CloseHandle(h)


def write_pid_file(root: str, stage: str) -> str:
    """<root>/run/<stage>.pid.json: the PID to stop this R11 process by (it resumes from its done markers)."""
    path = os.path.join(root, "run", f"{stage}.pid.json")
    write_json(path, {"pid": os.getpid(), "stage": stage, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                      "argv": sys.argv[:6]})
    return path


class Governor:
    """Waits (never kills anything) until free RAM / commit, system CPU and disk are inside the limits and no hold
    is requested (named event Local\\Forge_R11_Hold). There is no STOP file: R11 is stopped by its own PID."""

    def __init__(self, root: str, limits: Limits, log: Log):
        self.root = root
        self.limits = limits
        self.log = log

    def state(self, need_ram_gb: float = 0.0, disk_path: str | None = None, need_disk_gb: float = 0.0,
              cpu_interval: float = 1.0) -> tuple[bool, str]:
        ram, commit = memory_gb()
        cpu = cpu_load(cpu_interval)
        reasons = []
        if hold_requested():
            reasons.append(f"hold event {HOLD_EVENT}")
        if ram - need_ram_gb < self.limits.min_free_ram_gb:
            reasons.append(f"free RAM {ram:.1f} GB - need {need_ram_gb:.1f} < floor {self.limits.min_free_ram_gb}")
        if commit - need_ram_gb < self.limits.min_free_commit_gb:
            reasons.append(f"free commit {commit:.1f} GB - need {need_ram_gb:.1f} < floor {self.limits.min_free_commit_gb}")
        if cpu > self.limits.max_cpu_percent:
            reasons.append(f"CPU {cpu:.0f}% > cap {self.limits.max_cpu_percent:.0f}%")
        if disk_path:
            free = disk_free_gb(disk_path)
            if free - need_disk_gb < self.limits.min_disk_free_gb:
                reasons.append(f"disk {free:.1f} GB - need {need_disk_gb:.1f} < floor {self.limits.min_disk_free_gb}")
        status = f"RAM {ram:.1f} GB commit {commit:.1f} GB CPU {cpu:.0f}%"
        return (not reasons), status + ("" if not reasons else " | " + "; ".join(reasons))

    def wait_ok(self, what: str, need_ram_gb: float = 0.0, disk_path: str | None = None, need_disk_gb: float = 0.0,
                max_wait_s: float | None = None) -> bool:
        """True when it is fine to start `what`; False only after max_wait_s."""
        t0 = time.time()
        last_log = 0.0
        cpu_hits = 0
        while True:
            ok, status = self.state(need_ram_gb, disk_path, need_disk_gb)
            if ok:
                return True
            # a single CPU spike is not a reason to wait; three consecutive over-cap samples are
            why = status.split("|")[-1]
            if "CPU" in why and all(k not in why for k in ("RAM", "commit", "disk", "hold")):
                cpu_hits += 1
                if cpu_hits < 3:
                    continue
            if time.time() - last_log > 300:
                self.log.wait(f"{what}: {status}")
                last_log = time.time()
            if max_wait_s is not None and time.time() - t0 > max_wait_s:
                self.log.info(f"gave up waiting for {what} after {max_wait_s:.0f} s: {status}")
                return False
            time.sleep(self.limits.poll_seconds)


def expand_glob(pattern: str) -> list[str]:
    return sorted(glob.glob(pattern))


def matches_any(name: str, globs: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, g) for g in globs)
