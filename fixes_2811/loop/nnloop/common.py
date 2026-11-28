"""Shared helpers: config, logging, state, subprocesses, disk guard, keep-awake."""
from __future__ import annotations

import ctypes
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path

VALUE_NONE = 32002  # score that tells the nnue-pytorch loader to skip a position

_LOG_FILE: Path | None = None


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def set_log_file(path: Path) -> None:
    global _LOG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    _LOG_FILE = path


def log(msg: str) -> None:
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    if _LOG_FILE is not None:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def load_config(path: str | Path) -> dict:
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    cfg["_config_path"] = str(Path(path).resolve())
    # Engine options found by tuning ([engine] tuned_options_file): a JSON file {"options": {name: value}}
    # that is merged into uci_options if it exists. It is written only after the tuned values have won
    # their match against the defaults (pipeline/tools/spsa_chain.py). Deleting the file switches them off.
    tuned = (cfg.get("engine") or {}).get("tuned_options_file")
    if tuned and Path(tuned).exists():
        try:
            import json
            with open(tuned, encoding="utf-8") as f:
                tuned_data = json.load(f)
            extra = tuned_data.get("options") or {}
            # the net these values were found with: engine_for_net applies them to that net only (2026-11-15)
            cfg["engine"]["tuned_for_net_sha12"] = str(tuned_data.get("tuned_with_net_sha12") or "")
            cfg["engine"]["uci_options"] = {**cfg["engine"].get("uci_options", {}), **extra}
            cfg["engine"]["tuned_options_loaded"] = len(extra)
            cfg["engine"]["tuned_option_names"] = sorted(extra)   # so that a stage can leave them out again
        except (OSError, ValueError, AttributeError):
            pass
    return cfg


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    for i in range(100):    # a reader holding the file open makes the replace fail on Windows (WinError 5): wait, 5 s at most
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if i == 99:
                raise
            time.sleep(0.05)


def atomic_write_json(path: Path, obj) -> None:
    atomic_write_text(path, json.dumps(obj, indent=1))


def read_json(path: Path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def free_gb(path: str | Path) -> float:
    return shutil.disk_usage(str(path)).free / 2**30


def dir_size_gb(path: Path) -> float:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total / 2**30


class DiskLow(RuntimeError):
    pass


def check_disk(cfg: dict, where: str) -> float:
    root = cfg["paths"]["root"]
    need = float(cfg["limits"]["min_free_gb"])
    free = free_gb(root)
    log(f"disk check before {where}: {free:.1f} GB free (limit {need:.0f} GB)")
    if free < need:
        raise DiskLow(f"only {free:.1f} GB free before {where}; limit is {need:.0f} GB")
    return free


def keep_awake() -> None:
    """Ask Windows not to sleep while this process runs (a per-process request, not a setting)."""
    try:
        ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    except Exception as e:  # not fatal
        log(f"keep_awake failed: {e}")


_JOB_HANDLE = None


def kill_children_on_exit() -> None:
    """Put this process in a Windows job object so engines and trainers die with the pipeline."""
    global _JOB_HANDLE
    if os.name != "nt" or _JOB_HANDLE is not None:
        return
    from ctypes import wintypes

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class BASIC(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IOC(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in ("r", "w", "o", "rt", "wt", "ot")]

    class EXT(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BASIC),
            ("IoInfo", IOC),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    k32.CreateJobObjectW.restype = wintypes.HANDLE
    k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    job = k32.CreateJobObjectW(None, None)
    if not job:
        log("job object: CreateJobObject failed; children may outlive a crash")
        return
    info = EXT()
    info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    ok1 = k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
    ok2 = k32.AssignProcessToJobObject(job, k32.GetCurrentProcess())
    if not (ok1 and ok2):
        log(f"job object: setup failed (set={ok1} assign={ok2}, err={ctypes.get_last_error()})")
        return
    _JOB_HANDLE = job


class SingleInstance:
    """Lock file held for the life of the process, so two loops never run on one profile."""

    def __init__(self, path: Path):
        import msvcrt

        path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(path, "a+")
        try:
            self.f.seek(0)
            msvcrt.locking(self.f.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise SystemExit(f"another pipeline instance holds {path}; not starting a second one")
        self.f.seek(0)
        self.f.truncate()
        self.f.write(f"pid {os.getpid()} started {now()}\n")
        self.f.flush()


def child_env(cfg: dict, extra: dict | None = None) -> dict:
    env = dict(os.environ)
    tmp = cfg["paths"].get("tmp")
    if tmp:
        Path(tmp).mkdir(parents=True, exist_ok=True)
        env["TEMP"] = env["TMP"] = str(Path(tmp))
    env["PYTHONUNBUFFERED"] = "1"
    if extra:
        env.update({k: str(v) for k, v in extra.items()})
    return env


ENDED_AFTER_RESULT = -8     # run_logged's code for a command ended by its `done` test (not a time-out: that is -9)


def run_logged(cmd, log_path: Path, cwd=None, env=None, stdin_text: str | None = None,
               timeout: float | None = None, guard=None, done=None) -> int:
    """Run a command, send optional stdin, write stdout+stderr to log_path. Returns the exit code.

    guard (2026-11-15): an object with start(pid), stop() and lost_seconds(), e.g. nnloop.heat.MatchHeatGuard.
    It watches the running command. The time it says the command lost (a match given fewer processor threads
    because of heat) is added to the timeout, at most doubling it. Without a guard nothing is different.
    done (W2 of FINAL_PLAN_2311.md, 23 Nov 2026; asked only when a guard is given): a function asked every 5 s; True
    = the command's result is in but it has not exited (round 112's gate printed its SPRT verdict and hung for
    2 h 24 min). It is then ended with all its children and ENDED_AFTER_RESULT is returned.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "ab") as lf:
        lf.write(f"\n===== {now()} :: {cmd}\n".encode("utf-8", "replace"))
        lf.flush()
        p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=lf, stderr=subprocess.STDOUT,
                             stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL)
        try:
            if stdin_text is not None:
                p.stdin.write(stdin_text.encode("ascii"))
                p.stdin.close()
            if guard is None:
                return p.wait(timeout=timeout)
            guard.start(p.pid)
            t0 = time.time()
            while True:
                try:
                    return p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        result_in = done is not None and done()
                    except Exception:  # noqa: BLE001  (a failing test must not end the watch of a running command)
                        result_in = False
                    if result_in:
                        # From here the branch ALWAYS reaches the kill, the ENDED line and the return (Fable's read,
                        # 23 Nov): any error goes INTO the ENDED line. psutil 7.2.2 hands a failed process snapshot on
                        # as a plain OSError, not a psutil.Error.
                        import psutil
                        procs, errs, top = [], [], None
                        for _ in range(2):                # listed BEFORE the kill, to wait for all of it; try twice
                            try:
                                if top is None:           # fastchess itself first: it is waited for even when the
                                    top = psutil.Process(p.pid)   # listing of its children fails (Popen.kill() sets
                                    procs = [top]         # the return code before the process is gone)
                                procs = [top, *top.children(recursive=True)]
                                break
                            except Exception as e:  # noqa: BLE001  (whatever it is: the kill below must still happen)
                                errs.append(repr(e))
                                time.sleep(0.2)
                        for q in procs:                   # fastchess first, so it starts no new engines
                            try:
                                q.kill()
                            except Exception:  # noqa: BLE001
                                pass
                        p.kill()                          # in case psutil could not reach it
                        p.wait()
                        try:
                            _gone, alive = psutil.wait_procs(procs, timeout=10)
                            left = str(len(alive))
                        except Exception as e:  # noqa: BLE001
                            left = "an unknown number"
                            errs.append(repr(e))
                        failed = "; process list failed: " + " | ".join(errs) if errs else ""
                        lf.write(f"\n===== {now()} :: ENDED: its result is in and it did not exit; of its "
                                 f"{len(procs)} processes {left} still alive 10 s after the kill{failed}\n".encode())
                        return ENDED_AFTER_RESULT
                    if timeout is not None and time.time() - t0 >= timeout + min(float(guard.lost_seconds()), timeout):
                        raise
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
            lf.write(f"\n===== {now()} :: KILLED after timeout {timeout}s\n".encode())
            return -9
        finally:
            if guard is not None:
                try:
                    guard.stop()
                except Exception:  # noqa: BLE001
                    pass


def tail_text(path: Path, max_bytes: int = 20000) -> str:
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - max_bytes))
            return f.read().decode("utf-8", "replace")
    except FileNotFoundError:
        return ""


def stop_requested(cfg: dict) -> bool:
    return (Path(cfg["_config_path"]).parent / "STOP").exists()


def past_deadline(cfg: dict) -> bool:
    d = str(cfg["limits"].get("deadline", "")).strip()
    if not d:
        return False
    return dt.datetime.now() >= dt.datetime.strptime(d, "%Y-%m-%d %H:%M")


class State:
    """Round and stage bookkeeping in one JSON file; every change is written atomically."""

    def __init__(self, path: Path):
        self.path = path
        self.d = read_json(path, None) or {"best": None, "rounds": {}, "history": []}

    def save(self) -> None:
        atomic_write_json(self.path, self.d)

    def round(self, r: int) -> dict:
        return self.d["rounds"].setdefault(str(r), {"stages": {}})

    def stage(self, r: int, name: str) -> dict:
        return self.round(r)["stages"].setdefault(name, {"status": "pending"})

    def is_done(self, r: int, name: str) -> bool:
        return self.stage(r, name).get("status") == "done"

    def current_round(self) -> int:
        """First round that is not finished (1-based)."""
        r = 1
        while self.d["rounds"].get(str(r), {}).get("finished"):
            r += 1
        return r


def run_stage(state: State, r: int, name: str, fn, cfg: dict):
    """Run fn() once per round; a finished stage is skipped on restart, an interrupted one is redone."""
    st = state.stage(r, name)
    if st.get("status") == "done":
        log(f"round {r} stage {name}: already done, skipping")
        return st.get("out")
    check_disk(cfg, f"round {r} stage {name}")
    resumed = st.get("status") == "running"
    st.update({"status": "running", "started": now(), "attempts": st.get("attempts", 0) + 1})
    state.save()
    log(f"round {r} stage {name}: {'RESUMING after interruption' if resumed else 'start'}")
    t0 = time.time()
    out = fn()
    st.update({"status": "done", "finished": now(), "seconds": round(time.time() - t0, 1), "out": out})
    state.save()
    log(f"round {r} stage {name}: done in {st['seconds']} s")
    return out


def python_exe(cfg: dict) -> str:
    return cfg["paths"].get("python") or sys.executable


def count_plain_records(path: Path) -> int:
    n = 0
    with open(path, "rb") as f:
        for line in f:
            if line == b"e\n" or line == b"e\r\n":
                n += 1
    return n


# ----------------------------------------------------------------------------- CPU speed (overheating shows as slowing down)
def cpu_speed_pct(sample_seconds: float = 1.0) -> float | None:
    """Current CPU speed in percent of its nominal frequency (Windows counter "% Processor Performance").

    No admin rights needed. A CPU that gets too hot protects itself by lowering its frequency, so a
    lasting drop of this number under full load is the sign of overheating that can be read without
    a hardware-monitor driver. Returns None if the counter cannot be read (never raises).
    """
    try:
        import ctypes
        from ctypes import wintypes

        pdh = ctypes.WinDLL("pdh")

        class _Value(ctypes.Structure):
            _fields_ = [("CStatus", wintypes.DWORD), ("doubleValue", ctypes.c_double)]

        query, counter = wintypes.HANDLE(), wintypes.HANDLE()
        if pdh.PdhOpenQueryW(None, 0, ctypes.byref(query)) != 0:
            return None
        try:
            path = r"\Processor Information(_Total)\% Processor Performance"
            if pdh.PdhAddEnglishCounterW(query, path, 0, ctypes.byref(counter)) != 0:
                return None
            pdh.PdhCollectQueryData(query)
            time.sleep(max(0.2, sample_seconds))
            if pdh.PdhCollectQueryData(query) != 0:
                return None
            val = _Value()
            if pdh.PdhGetFormattedCounterValue(counter, 0x00000200, None, ctypes.byref(val)) != 0:  # PDH_FMT_DOUBLE
                return None
            return float(val.doubleValue)
        finally:
            pdh.PdhCloseQuery(query)
    except Exception:  # noqa: BLE001
        return None


# ----------------------------------------------------------------------------- temperatures from HWiNFO's log file
_HWINFO_COLUMNS = {
    "cpu_c": ("CPU (Tctl/Tdie)", "CPU Die (average)", "CPU Package"),
    "cpu_w": ("CPU Package Power",),
    "cpu_fan_rpm": ("CPU [RPM]",),
    "pump_rpm": ("PUMP SYS1 [RPM]", "PUMP"),
    "gpu_c": ("GPU Temperature",),
    "gpu_hot_c": ("GPU Hot Spot Temperature",),
    "gpu_mem_c": ("GPU Memory Junction Temperature",),
    "throttle": ("Thermal Throttling (PROCHOT CPU)", "Thermal Throttling (HTC)"),
}
_hwinfo_cache: dict = {}


def hwinfo_paths(cfg: dict | None = None) -> list[str]:
    p = []
    if cfg and (cfg.get("limits") or {}).get("hwinfo_csv"):
        p.append(str(cfg["limits"]["hwinfo_csv"]))
    root = Path(__file__).resolve().parents[2]
    for name in ("hwinfo.CSV", "hwinfo.csv", "logs/hwinfo.CSV", "logs/hwinfo.csv"):
        p.append(str(root / name))
    return p


def read_hwinfo(cfg: dict | None = None, max_age_s: float = 90.0) -> dict | None:
    """Newest readings from the sensor log that HWiNFO writes (the owner starts that logging by hand).

    Returns {"cpu_c", "cpu_w", "cpu_fan_rpm", "pump_rpm", "gpu_c", "gpu_hot_c", "throttle", "age_s", "file"}
    with None for values that are not in the file, or None if no fresh log exists (HWiNFO closed, logging
    not started, or the file older than max_age_s). Only reads the file; never raises.
    """
    try:
        import csv

        for path in hwinfo_paths(cfg):
            try:
                st = os.stat(path)
            except OSError:
                continue
            age = time.time() - st.st_mtime
            if age > max_age_s or st.st_size < 200:
                continue
            c = _hwinfo_cache.get(path)
            if c is None:
                with open(path, "rb") as fh:
                    head = fh.readline(1 << 20).decode("utf-8", errors="replace")
                names = next(csv.reader([head]))
                cols = {}
                for key, wanted in _HWINFO_COLUMNS.items():
                    for w in wanted:
                        hit = [i for i, n in enumerate(names) if n.startswith(w)]
                        if hit:
                            cols[key] = hit[0]
                            break
                # every GPU hot-spot sensor (the owner's card has a weak spot under load: watch the hottest one)
                hot = [i for i, n in enumerate(names) if n.startswith("GPU") and "hot" in n.lower() and "(avg)" not in n]
                c = _hwinfo_cache[path] = {"cols": cols, "n": len(names), "gpu_hot": hot}
            with open(path, "rb") as fh:
                fh.seek(max(0, st.st_size - 32768))
                tail = fh.read().decode("utf-8", errors="replace")
            row = None
            for line in reversed(tail.splitlines()):
                if not line or not line[:1].isdigit():
                    continue          # the footer HWiNFO writes when logging stops, or a cut first line
                r = next(csv.reader([line]))
                if len(r) >= c["n"] - 2:
                    row = r
                    break
            if row is None:
                continue
            out = {"age_s": round(age, 1), "file": path}
            for key in _HWINFO_COLUMNS:
                i = c["cols"].get(key)
                v = row[i].strip() if (i is not None and i < len(row)) else ""
                if key == "throttle":
                    out[key] = (v.lower() == "yes") if v else None
                else:
                    try:
                        out[key] = float(v)
                    except ValueError:
                        out[key] = None
            hots = []
            for i in c.get("gpu_hot", []):
                try:
                    hots.append(float(row[i]))
                except (ValueError, IndexError):
                    pass
            out["gpu_hot_max_c"] = max(hots) if hots else out.get("gpu_hot_c")
            return out
        return None
    except Exception:  # noqa: BLE001
        return None


def heat_status(cfg: dict | None = None) -> str:
    """One short phrase for log lines and for SHOW_PROGRESS."""
    h = read_hwinfo(cfg)
    if h and h.get("cpu_c") is not None:
        s = f"CPU {h['cpu_c']:.0f} C"
        if h.get("cpu_w") is not None:
            s += f", {h['cpu_w']:.0f} W"
        if h.get("cpu_fan_rpm") is not None:
            s += f", fan {h['cpu_fan_rpm']:.0f} rpm"
        if h.get("gpu_c") is not None:
            s += f", GPU {h['gpu_c']:.0f} C"
            if h.get("gpu_hot_max_c") is not None:
                s += f" (hottest spot {h['gpu_hot_max_c']:.0f} C)"
        if h.get("throttle"):
            s += ", CPU IS THROTTLING"
        return s
    sp = cpu_speed_pct(0.5)
    return f"no temperature log (HWiNFO not logging), CPU speed {sp:.0f}%" if sp is not None else "no temperature reading"
