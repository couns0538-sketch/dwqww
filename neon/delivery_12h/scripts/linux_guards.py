"""Portable RAM and GPU thermal guard module for Linux Server-Day & Windows.

Drop-in compatible with pipeline/forge_train.py's RamGuard, GpuHeatGuard, and
free_ram_gb() interfaces, while adding:
  - /proc/meminfo parsing on Linux/POSIX (MemAvailable, fallback MemFree+Buffers+Cached)
  - GlobalMemoryStatusEx on Windows (os.name == "nt")
  - nvidia-smi & rocm-smi GPU temperature readers with NNLOOP_FAKE_GPU_FILE and
    graceful dry-run / missing-tool None fallback
  - Built-in --selftest, --status, --dry-run, and --check-ram-gb CLI modes

All selftest scratch directories are created locally inside this module's
parent directory and cleaned up in finally: (never /tmp or system temp).
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Callable

GIB = float(1024**3)
_MEMINFO_LINE_RE = re.compile(r"^([A-Za-z0-9_()]+):\s*(\d+)\s*kB\b", re.MULTILINE)
_ROCM_TEXT_TEMP_RE = re.compile(r"(?:Temperature|Temp)[^:\n]*:\s*([-+]?\d+(?:\.\d+)?)", re.IGNORECASE)


def parse_meminfo(text: str) -> float | None:
    """Parse Linux /proc/meminfo text and return free/available RAM in GiB.

    Prefers MemAvailable; if absent (older kernels or minimal containers),
    falls back to MemFree + Buffers + Cached (requires MemFree to be present).
    """
    if not text or not isinstance(text, str):
        return None
    fields: dict[str, int] = {}
    for match in _MEMINFO_LINE_RE.finditer(text):
        fields[match.group(1)] = int(match.group(2))
    if "MemAvailable" in fields:
        return fields["MemAvailable"] / (1024.0 * 1024.0)
    if "MemFree" in fields:
        kb = fields["MemFree"] + fields.get("Buffers", 0) + fields.get("Cached", 0)
        return kb / (1024.0 * 1024.0)
    return None


def _win32_mem_status() -> tuple[float, float] | None:
    """Return (avail_phys_gb, avail_pagefile_gb) on Windows, or None on error."""
    if os.name != "nt":
        return None
    try:
        class _MemStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        ms = _MemStatusEx()
        ms.dwLength = ctypes.sizeof(_MemStatusEx)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
            return None
        return (ms.ullAvailPhys / GIB, ms.ullAvailPageFile / GIB)
    except Exception:  # noqa: BLE001
        return None


def free_ram_gb(meminfo_path: Path | str = "/proc/meminfo") -> float | None:
    """Return available physical RAM in GiB, or None if unavailable.

    Checks FORGE_FAKE_FREE_RAM_GB first for deterministic testing. On Windows
    (when using the default /proc/meminfo path), queries GlobalMemoryStatusEx;
    on Linux/POSIX (or when a custom meminfo_path is supplied), parses meminfo.
    """
    fake_raw = os.environ.get("FORGE_FAKE_FREE_RAM_GB", "").strip()
    if fake_raw:
        try:
            return float(fake_raw)
        except ValueError:
            return None

    is_default_proc = str(meminfo_path) == "/proc/meminfo"
    if os.name == "nt" and is_default_proc:
        st = _win32_mem_status()
        return st[0] if st is not None else None

    try:
        text = Path(meminfo_path).read_text(encoding="utf-8")
    except OSError:
        return None
    return parse_meminfo(text)


def mem_room_ok(
    need_gb: float,
    keep_gb: float = 5.0,
    meminfo_path: Path | str = "/proc/meminfo",
) -> tuple[bool, str]:
    """Check whether sufficient RAM headroom exists for a job needing need_gb GiB."""
    fake_raw = os.environ.get("FORGE_FAKE_FREE_RAM_GB", "").strip()
    is_default_proc = str(meminfo_path) == "/proc/meminfo"

    if not fake_raw and os.name == "nt" and is_default_proc:
        st = _win32_mem_status()
        if st is None:
            return False, "NO_READING: GlobalMemoryStatusEx failed"
        phys_free, page_room = st
        ok = (page_room - need_gb) >= keep_gb and (phys_free - need_gb) >= 1.0
        msg = (
            f"{'GO' if ok else 'WAIT'}: phys_free={phys_free:.2f}GiB "
            f"commit_room={page_room:.2f}GiB need={need_gb:.2f}GiB keep={keep_gb:.2f}GiB"
        )
        return ok, msg

    avail = free_ram_gb(meminfo_path=meminfo_path)
    if avail is None:
        return False, f"NO_READING: unable to read RAM from {meminfo_path}"
    ok = (avail - need_gb) >= keep_gb
    msg = (
        f"{'GO' if ok else 'WAIT'}: avail={avail:.2f}GiB "
        f"need={need_gb:.2f}GiB keep={keep_gb:.2f}GiB"
    )
    return ok, msg


def parse_nvidia_smi_temps(stdout: str) -> float | None:
    """Parse `nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits`."""
    if not stdout:
        return None
    vals: list[float] = []
    for line in stdout.splitlines():
        tok = line.strip().split(",")[0].strip()
        if not tok:
            continue
        try:
            vals.append(float(tok))
        except ValueError:
            continue
    return max(vals) if vals else None


def _collect_json_temps(obj: Any, out: list[float]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                _collect_json_temps(v, out)
            elif "temp" in str(k).lower():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    out.append(float(v))
                elif isinstance(v, str):
                    try:
                        out.append(float(v.strip()))
                    except ValueError:
                        pass
    elif isinstance(obj, list):
        for item in obj:
            _collect_json_temps(item, out)


def parse_rocm_smi_temps(stdout: str) -> float | None:
    """Parse `rocm-smi --showtemp --json` or plain-text `rocm-smi --showtemp`."""
    if not stdout or not stdout.strip():
        return None
    stripped = stdout.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            data = json.loads(stripped)
            vals: list[float] = []
            _collect_json_temps(data, vals)
            if vals:
                return max(vals)
        except json.JSONDecodeError:
            pass
    vals_txt: list[float] = []
    for match in _ROCM_TEXT_TEMP_RE.finditer(stdout):
        try:
            vals_txt.append(float(match.group(1)))
        except ValueError:
            continue
    return max(vals_txt) if vals_txt else None


def gpu_temp_c(dry_run: bool = False, timeout_s: float = 3.0) -> float | None:
    """Read hottest GPU temperature in Celsius, or None on dry-run / unavailable sensor.

    Priority:
      1. NNLOOP_FAKE_GPU_FILE (ASCII float, matching forge_train.py test hook)
      2. dry_run=True or FORGE_GPU_TEMP_DRY_RUN=1 -> None
      3. nvidia-smi (if found on PATH)
      4. rocm-smi (if found on PATH)
      5. Graceful None fallback
    """
    fake = os.environ.get("NNLOOP_FAKE_GPU_FILE", "").strip()
    if fake:
        try:
            return float(Path(fake).read_text(encoding="ascii").strip())
        except (OSError, ValueError):
            return None

    if dry_run or os.environ.get("FORGE_GPU_TEMP_DRY_RUN", "").strip() == "1":
        return None

    nv = shutil.which("nvidia-smi")
    if nv:
        try:
            r = subprocess.run(
                [nv, "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            if r.returncode == 0:
                t = parse_nvidia_smi_temps(r.stdout)
                if t is not None:
                    return t
        except (OSError, subprocess.SubprocessError):
            pass

    rocm = shutil.which("rocm-smi")
    if rocm:
        for cmd in ([rocm, "--showtemp", "--json"], [rocm, "--showtemp"]):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
                if r.returncode == 0:
                    t = parse_rocm_smi_temps(r.stdout)
                    if t is not None:
                        return t
            except (OSError, subprocess.SubprocessError):
                pass

    return None


class RamGuard:
    """Drop-in RAM guard matching pipeline/forge_train.py's RamGuard API."""

    def __init__(
        self,
        floor_gb: float = 1.5,
        every_s: float = 2.0,
        *,
        timeout_s: float = 120.0,
        poll_s: float = 5.0,
        sleep_fn: Callable[[float], None] = time.sleep,
        reader: Callable[[], float | None] | None = None,
    ) -> None:
        self.floor = float(floor_gb)
        self.every_s = float(every_s)
        self.last = 0.0
        self.lowest: float | None = None
        self.timeout_s = float(timeout_s)
        self.poll_s = float(poll_s)
        self._sleep = sleep_fn
        self._reader = reader

    def _read_gb(self) -> float | None:
        if self._reader is not None:
            return self._reader()
        return free_ram_gb()

    def tick(self) -> None:
        now = time.time()
        if self.floor <= 0 or (self.last > 0.0 and now - self.last < self.every_s):
            return
        self.last = now
        f = self._read_gb()
        if f is None:
            return
        self.lowest = f if self.lowest is None else min(self.lowest, f)
        if f >= self.floor:
            return
        print(
            f"MEMORY GUARD: {f:.1f} GB free (floor {self.floor:.1f} GB). Training waits.",
            flush=True,
        )
        t0 = time.monotonic()
        sim_elapsed = 0.0
        while max(time.monotonic() - t0, sim_elapsed) < self.timeout_s:
            self._sleep(self.poll_s)
            sim_elapsed += self.poll_s
            f = self._read_gb()
            if f is not None:
                self.lowest = f if self.lowest is None else min(self.lowest, f)
            if f is None or f >= self.floor:
                elapsed = max(time.monotonic() - t0, sim_elapsed)
                print(
                    f"MEMORY GUARD: {'unknown' if f is None else format(f, '.1f') + ' GB'} "
                    f"free again after {elapsed:.0f} s. Training resumes.",
                    flush=True,
                )
                self.last = time.time()
                return
        raise SystemExit(
            f"MEMORY GUARD: still only {f:.1f} GB free after {self.timeout_s:.0f} s; "
            f"refusing to continue to protect host stability."
        )


class GpuHeatGuard:
    """Drop-in GPU thermal guard matching pipeline/forge_train.py's GpuHeatGuard API."""

    def __init__(
        self,
        pause_c: float = 98.0,
        resume_c: float = 84.0,
        every_s: float = 10.0,
        *,
        timeout_s: float = 900.0,
        poll_s: float = 5.0,
        sleep_fn: Callable[[float], None] = time.sleep,
        reader: Callable[[], float | None] | None = None,
        dry_run: bool = False,
    ) -> None:
        self.pause_c = float(pause_c)
        self.resume_c = float(resume_c)
        self.every_s = float(every_s)
        self.last = 0.0
        self.max_seen: float | None = None
        self.pauses = 0
        self.paused_s = 0.0
        self.timeout_s = float(timeout_s)
        self.poll_s = float(poll_s)
        self._sleep = sleep_fn
        self._reader = reader
        self._dry_run = bool(dry_run)

    def _hottest(self) -> float | None:
        fake = os.environ.get("NNLOOP_FAKE_GPU_FILE", "").strip()
        if fake:
            try:
                return float(Path(fake).read_text(encoding="ascii").strip())
            except (OSError, ValueError):
                return None
        if self._reader is not None:
            return self._reader()
        return gpu_temp_c(dry_run=self._dry_run)

    def tick(self) -> None:
        now = time.time()
        if self.pause_c <= 0 or (self.last > 0.0 and now - self.last < self.every_s):
            return
        self.last = now
        t = self._hottest()
        if t is None:
            return
        self.max_seen = t if self.max_seen is None else max(self.max_seen, t)
        if t < self.pause_c:
            return
        self.pauses += 1
        t0 = time.monotonic()
        sim_elapsed = 0.0
        print(
            f"HEAT GUARD: GPU hottest sensor {t:.0f} C (limit {self.pause_c:.0f} C). "
            f"Training pauses to cool down.",
            flush=True,
        )
        while max(time.monotonic() - t0, sim_elapsed) < self.timeout_s:
            self._sleep(self.poll_s)
            sim_elapsed += self.poll_s
            t = self._hottest()
            if t is not None:
                self.max_seen = t if self.max_seen is None else max(self.max_seen, t)
            if t is None or t <= self.resume_c:
                break
        elapsed = max(time.monotonic() - t0, sim_elapsed)
        self.paused_s += elapsed
        self.last = time.time()
        print(
            f"HEAT GUARD: GPU hottest sensor {'unknown' if t is None else format(t, '.0f') + ' C'} "
            f"after {elapsed:.0f} s. Training resumes.",
            flush=True,
        )


def selftest() -> int:
    """Self-contained selftest inside a local _work_selftest_* directory (cleaned up in finally)."""
    base_dir = Path(__file__).resolve().parent
    work_dir = base_dir / f"_work_selftest_{uuid.uuid4().hex[:10]}"
    old_fake_gpu = os.environ.get("NNLOOP_FAKE_GPU_FILE")
    old_fake_ram = os.environ.get("FORGE_FAKE_FREE_RAM_GB")
    old_dry = os.environ.get("FORGE_GPU_TEMP_DRY_RUN")
    try:
        work_dir.mkdir(parents=True, exist_ok=True)

        # 1. /proc/meminfo parsing (MemAvailable + MemFree+Buffers+Cached fallback)
        sample_avail = "MemTotal:       65536000 kB\nMemFree:        12000000 kB\nMemAvailable:   33554432 kB\n"
        avail_gb = parse_meminfo(sample_avail)
        assert avail_gb is not None and abs(avail_gb - 32.0) < 1e-6, avail_gb

        sample_fallback = "MemTotal:       33554432 kB\nMemFree:         2097152 kB\nBuffers:         1048576 kB\nCached:          5242880 kB\n"
        fb_gb = parse_meminfo(sample_fallback)
        assert fb_gb is not None and abs(fb_gb - 8.0) < 1e-6, fb_gb

        fake_meminfo = work_dir / "meminfo"
        fake_meminfo.write_text(sample_avail, encoding="utf-8")
        os.environ.pop("FORGE_FAKE_FREE_RAM_GB", None)
        assert abs((free_ram_gb(fake_meminfo) or 0.0) - 32.0) < 1e-6
        ok_mem, _ = mem_room_ok(16.0, keep_gb=5.0, meminfo_path=fake_meminfo)
        assert ok_mem is True
        low_mem, _ = mem_room_ok(30.0, keep_gb=5.0, meminfo_path=fake_meminfo)
        assert low_mem is False

        # 2. Live host free_ram_gb()
        live_ram = free_ram_gb()
        assert live_ram is None or live_ram > 0.0, live_ram

        # 3. Dry-run gpu_temp_c() is None
        os.environ.pop("NNLOOP_FAKE_GPU_FILE", None)
        assert gpu_temp_c(dry_run=True) is None
        assert parse_nvidia_smi_temps("62\n79.5\n") == 79.5
        assert parse_rocm_smi_temps('{"card0": {"Temperature (Sensor junction) (C)": "88.0"}}') == 88.0

        # 4. NNLOOP_FAKE_GPU_FILE pause -> resume transition
        fake_gpu = work_dir / "gpu_temp.txt"
        fake_gpu.write_text("101.0\n", encoding="ascii")
        os.environ["NNLOOP_FAKE_GPU_FILE"] = str(fake_gpu)
        assert gpu_temp_c() == 101.0

        ticks = {"n": 0}

        def _cool_sleep(_dt: float) -> None:
            ticks["n"] += 1
            if ticks["n"] >= 2:
                fake_gpu.write_text("80.0\n", encoding="ascii")

        hg = GpuHeatGuard(pause_c=98.0, resume_c=84.0, every_s=0.0, timeout_s=30.0, poll_s=1.0, sleep_fn=_cool_sleep)
        hg.tick()
        assert hg.pauses == 1 and hg.max_seen == 101.0 and hg.paused_s >= 2.0 and ticks["n"] == 2, (
            hg.pauses, hg.max_seen, hg.paused_s, ticks["n"]
        )

        # 5. RamGuard pass + SystemExit refusal
        rg_ok = RamGuard(floor_gb=1.5, every_s=0.0, timeout_s=0.0, poll_s=0.0, reader=lambda: 12.0)
        rg_ok.tick()
        assert rg_ok.lowest == 12.0

        rg_low = RamGuard(floor_gb=4.0, every_s=0.0, timeout_s=0.0, poll_s=0.0, reader=lambda: 1.0)
        refused = False
        try:
            rg_low.tick()
        except SystemExit:
            refused = True
        assert refused, "RamGuard failed to raise SystemExit when RAM remained below floor"

        summary = {
            "meminfo_avail_gb": round(avail_gb, 3),
            "live_ram_gb": None if live_ram is None else round(live_ram, 2),
            "gpu_pauses": hg.pauses,
            "gpu_max_seen_c": hg.max_seen,
            "ram_refusal_ok": refused,
        }
        print("LINUX_GUARDS_SELFTEST_PASS:", json.dumps(summary), flush=True)
        return 0
    finally:
        if old_fake_gpu is None:
            os.environ.pop("NNLOOP_FAKE_GPU_FILE", None)
        else:
            os.environ["NNLOOP_FAKE_GPU_FILE"] = old_fake_gpu
        if old_fake_ram is None:
            os.environ.pop("FORGE_FAKE_FREE_RAM_GB", None)
        else:
            os.environ["FORGE_FAKE_FREE_RAM_GB"] = old_fake_ram
        if old_dry is None:
            os.environ.pop("FORGE_GPU_TEMP_DRY_RUN", None)
        else:
            os.environ["FORGE_GPU_TEMP_DRY_RUN"] = old_dry
        shutil.rmtree(work_dir, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Portable RAM & GPU thermal guards for Forge Server-Day.")
    ap.add_argument("--selftest", action="store_true", help="Run self-contained guard verification")
    ap.add_argument("--status", action="store_true", help="Print current RAM & GPU temp status as JSON")
    ap.add_argument("--dry-run", action="store_true", help="Do not invoke nvidia-smi/rocm-smi")
    ap.add_argument("--check-ram-gb", type=float, default=None, help="Verify at least N GiB RAM headroom")
    ap.add_argument("--keep-ram-gb", type=float, default=5.0, help="Reserved OS headroom GiB for --check-ram-gb")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if args.check_ram_gb is not None:
        ok, msg = mem_room_ok(args.check_ram_gb, keep_gb=args.keep_ram_gb)
        print(msg, flush=True)
        if msg.startswith("NO_READING"):
            return 2
        return 0 if ok else 1

    if args.status or args.dry_run:
        ram = free_ram_gb()
        temp = gpu_temp_c(dry_run=args.dry_run)
        print(
            json.dumps(
                {
                    "platform": sys.platform,
                    "os_name": os.name,
                    "free_ram_gb": None if ram is None else round(ram, 3),
                    "gpu_temp_c": temp,
                    "dry_run": bool(args.dry_run),
                },
                indent=2,
            ),
            flush=True,
        )
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
