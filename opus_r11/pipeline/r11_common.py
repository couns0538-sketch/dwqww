"""R11 pipeline: shared helpers (logging, atomic files, full-sha256 sealed inputs, resource governor, FPOS/FHCE I/O, keys).

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
            require_disk(path, 16 << 20, "the pipeline log")  # CR fix 8 (log lines are tiny: checked per log)
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
# disk (CR fix 8: free space is checked before every write, download and extract)
# ----------------------------------------------------------------------------------------------------------------
SMALL_WRITE_FLOOR_GB = 1.0  # JSON / logs / decision files (a few MB): the drive must keep at least this much
_FLOORS: dict[str, float] = {"D:": 40.0, "F:": 40.0}  # bulk-write floors per drive; set from limits.disk_floor_gb


def set_disk_floors(floors: dict | None) -> None:
    if floors:
        _FLOORS.update({k.upper().rstrip("\\/"): float(v) for k, v in floors.items()})


def _drive(path: str) -> str:
    p = winpath(path)
    return p[:2].upper() if len(p) > 1 and p[1] == ":" else p


def disk_floor_gb(path: str, default: float = 40.0) -> float:
    """Bulk-write floor of the drive that holds `path` (QA 2026-10-30: D: keeps >= 40 GB free)."""
    return _FLOORS.get(_drive(path), default)


def disk_free_gb(path: str) -> float:
    p = os.path.abspath(path)
    while not os.path.exists(p):
        p = os.path.dirname(p)
    return shutil.disk_usage(p).free / 2**30


SMALL_WRITE_MAX_BYTES = 64 << 20


def require_disk(path: str, need_bytes: int, what: str, floor_gb: float | None = None) -> None:
    """Raise StageFailed unless writing need_bytes under `path` keeps the drive above its floor: writes under 64 MiB
    (state JSON, decisions, .hce side-cars, logs) keep SMALL_WRITE_FLOOR_GB, bulk writes the drive's floor."""
    if floor_gb is None:
        floor_gb = SMALL_WRITE_FLOOR_GB if need_bytes < SMALL_WRITE_MAX_BYTES else disk_floor_gb(path)
    floor = floor_gb
    free = disk_free_gb(path)
    if free - need_bytes / 2**30 < floor:
        raise StageFailed(f"disk: {what} needs {need_bytes / 2**30:.3f} GB on {_drive(path)}; {free:.1f} GB free would "
                          f"drop below the {floor:.0f} GB floor")


# ----------------------------------------------------------------------------------------------------------------
# files
# ----------------------------------------------------------------------------------------------------------------
def write_json(path: str, obj) -> None:
    require_disk(path, 1 << 20, f"state file {os.path.basename(path)}", SMALL_WRITE_FLOOR_GB)
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
    require_disk(path, len(text.encode("utf-8")) + (1 << 20), f"text file {os.path.basename(path)}", SMALL_WRITE_FLOOR_GB)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def sha256_file(path: str, bufsize: int = 1 << 23) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


class SealedInputs:
    """CR fix 10: sealed inputs are identified by their FULL sha256 (never a first/last-MiB fingerprint). Each file is
    hashed at most once per run; verify() raises StageFailed when a file differs from its registered sha256."""

    def __init__(self):
        self.cache: dict[str, str] = {}

    def sha256(self, path: str) -> str:
        key = winpath(path).lower()
        if key not in self.cache:
            self.cache[key] = sha256_file(path)
        return self.cache[key]

    def verify(self, path: str, expected: str, what: str) -> None:
        if not os.path.isfile(path):
            raise StageFailed(f"sealed input missing: {what} {path}")
        got = self.sha256(path)
        if got != expected:
            raise StageFailed(f"input changed since registration: {what} {path} sha256 {got} != registered {expected}")


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


IDLE_PRIORITY_CLASS = 0x00000040
DEFAULT_AFFINITY = 0x700  # CPUs 8-10: three cores (the PC's known 3-CPU mask)


def affinity_from_cfg(cfg: dict) -> int:
    v = cfg.get("limits", {}).get("affinity_mask", DEFAULT_AFFINITY)
    return int(v, 0) if isinstance(v, str) else int(v)


MEMORY_PRIORITY_LOW = 2
_PROCESS_MEMORY_PRIORITY = 0  # PROCESS_INFORMATION_CLASS ProcessMemoryPriority


def set_idle_background(mask: int = DEFAULT_AFFINITY) -> dict:
    """CR fix 2 (amended 2026-10-30): Idle priority class (0x40) + I/O priority very low + memory priority low, on at
    most 3 cores; all four are inherited by child processes (measured: nice 64, ionice 0, memory priority 2).
    BelowNormal would outrank the Idle trainer and self-play.
    NOT PROCESS_MODE_BACKGROUND_BEGIN: measured on this PC it caps the process working set at 32 MB - a 300 MB array
    stayed at a 32 MB working set with 4.8x the page faults, writes 6x and re-reads 14x slower; the real data stage and
    the trainer entry ran at ~90 % kernel time (445k page faults/s). The amendment keeps the same resource classes
    (CPU idle, I/O very low, memory low) without that cap."""
    if bin(mask).count("1") > 3 or mask <= 0:
        raise StageFailed(f"affinity mask {hex(mask)} must select 1..3 CPUs")
    if sys.platform != "win32":
        return {}
    try:
        import psutil
    except ImportError as e:
        raise StageFailed("psutil is missing: cannot set the I/O priority (fail)") from e
    k32 = ctypes.windll.kernel32
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    k32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
    k32.SetProcessInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    h = k32.GetCurrentProcess()
    ok_idle = bool(k32.SetPriorityClass(h, IDLE_PRIORITY_CLASS))
    try:
        psutil.Process().ionice(psutil.IOPRIO_VERYLOW)
        ok_io = True
    except (OSError, psutil.Error):
        ok_io = False
    low = wintypes.ULONG(MEMORY_PRIORITY_LOW)
    ok_mem = bool(k32.SetProcessInformation(h, _PROCESS_MEMORY_PRIORITY, ctypes.byref(low), 4))
    ok_aff = bool(k32.SetProcessAffinityMask(h, mask))
    if not (ok_idle and ok_io and ok_mem and ok_aff):
        raise StageFailed(f"could not lower this process (Idle {ok_idle}, I/O very low {ok_io}, memory low {ok_mem}, "
                          f"affinity {hex(mask)} {ok_aff})")
    return {"priority": "Idle", "io": "very low", "memory": "low", "affinity": hex(mask)}


def priority_name() -> str:
    if sys.platform != "win32":
        return "n/a"
    pc = ctypes.windll.kernel32.GetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess())
    return {0x40: "Idle", 0x4000: "BelowNormal", 0x20: "Normal", 0x8000: "AboveNormal", 0x80: "High"}.get(pc, hex(pc))


UNREADABLE = "command line unreadable (AccessDenied): treated as a production trainer"


def production_processes(patterns: list[str]) -> list[dict]:
    """Processes whose command line matches one of the regexes. Only pid, name and the matched pattern are
    returned (command lines are never logged).
    CR fix 4: psutil missing or no process list -> StageFailed (the stage fails, nothing starts); a python process
    whose command line cannot be read (AccessDenied) counts as a match (the caller waits), never as "no match".
    Non-python processes with an unreadable command line (System, services) and kernel processes without a readable
    name (parent PID 0 or 4: Registry, Memory Compression, Secure System) cannot be a trainer and are skipped."""
    try:
        import psutil
    except ImportError as e:
        raise StageFailed("psutil is missing: cannot check for production trainers (fail)") from e
    me = os.getpid()
    try:  # this process and its own launcher chain (venv launcher, shell) are never "production"
        own = {me} | {a.pid for a in psutil.Process(me).parents()}
    except Exception:  # noqa: BLE001
        own = {me}
    found = []
    regs = [re.compile(p, re.I) for p in patterns]
    try:
        procs = list(psutil.process_iter(["pid", "ppid", "name", "cmdline"]))  # unreadable attributes come back as None
    except Exception as e:  # noqa: BLE001
        raise StageFailed(f"process list unavailable ({type(e).__name__}): cannot check for production trainers") from e
    for p in procs:
        info = p.info
        if info.get("pid") in own:
            continue
        name = info.get("name") or ""
        cmdline = info.get("cmdline")
        if cmdline is None:
            kernel = not name and info.get("ppid") in (0, 4)
            if not kernel and (not name or name.lower().startswith("python")):
                found.append({"pid": info.get("pid"), "name": name or "?", "pattern": UNREADABLE})
            continue
        cmd = " ".join(cmdline)
        for r in regs:
            if r.search(cmd):
                found.append({"pid": info.get("pid"), "name": name, "pattern": r.pattern})
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
    min_disk_free_gb: float = 40.0
    poll_seconds: float = 30.0
    affinity_mask: str | int = "0x700"
    disk_floor_gb: dict | None = None  # per drive, e.g. {"D:": 40, "F:": 40, "C:": 10}; default min_disk_free_gb


def limits_from(cfg: dict) -> Limits:
    """Limits from cfg["limits"]: keys starting with "comment" are notes; any other unknown key is an error (typos)."""
    raw = {k: v for k, v in cfg.get("limits", {}).items() if not k.startswith("comment")}
    known = set(Limits.__dataclass_fields__)
    unknown = sorted(set(raw) - known)
    if unknown:
        raise StageFailed(f"unknown keys in limits: {unknown}")
    return Limits(**raw)


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
        set_disk_floors(limits.disk_floor_gb)

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
            floor = disk_floor_gb(disk_path, self.limits.min_disk_free_gb)
            if free - need_disk_gb < floor:
                reasons.append(f"disk {free:.1f} GB - need {need_disk_gb:.1f} < floor {floor:.0f}")
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
