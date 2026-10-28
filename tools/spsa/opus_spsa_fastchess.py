"""fastchess side of the Forge SPSA tuner (R3-4): command line, output parsing, child processes, free RAM.

Standard library only, Python 3.10+. Written against fastchess 1.8.2 (alpha, f618e34): the result block

    Results of spsa_plus vs spsa_minus (0.5+0.005, 1t, 16MB, forge-10000.epd):
    ...
    Games: 4, Wins: 2, Losses: 1, Draws: 1, Points: 2.5 (62.50 %)
    Ptnml(0-2): [0, 0, 1, 1, 0], WL/DD Ratio: inf

and one 'Finished game N (A vs B): 1-0 {White mates}' line per game. The last result block is authoritative; the
Finished lines must agree with it (W/L/D and, pairing games 2j-1 and 2j, the pentanomial), else the iteration
fails closed.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass

from opus_spsa_core import MatchResult

PLUS_NAME = "spsa_plus"
MINUS_NAME = "spsa_minus"

_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_HEADER = re.compile(r"^Results of (\S+) vs (\S+) \((.*)\):\s*$")
_GAMES = re.compile(r"^Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+), Points: ([0-9.]+) \(")
_PTNML = re.compile(r"^Ptnml\(0-2\): \[(\d+), (\d+), (\d+), (\d+), (\d+)\]")
_FINISHED = re.compile(r"^Finished game (\d+) \((\S+) vs (\S+)\): (1-0|0-1|1/2-1/2|\*)\s*(?:\{(.*)\})?\s*$")


def build_command(cfg: dict, plus: dict[str, int], minus: dict[str, int], srand: int, pgn_path: str) -> list[str]:
    """fastchess argv for one mini-match: theta+ (engine 1) against theta- (engine 2), cfg['pairs_per_iteration']
    game pairs with reversed colours on the same opening, random opening order seeded by srand."""
    fastchess = cfg["fastchess"]
    argv = list(fastchess) if isinstance(fastchess, list) else [fastchess]
    argv += ["-engine", f"cmd={cfg['engine']}", f"name={PLUS_NAME}"] + [f"option.{n}={v}" for n, v in plus.items()]
    argv += ["-engine", f"cmd={cfg['engine']}", f"name={MINUS_NAME}"] + [f"option.{n}={v}" for n, v in minus.items()]
    each = ["proto=uci"]
    if cfg.get("tc"):
        each.append(f"tc={cfg['tc']}")
    if cfg.get("nodes"):
        each.append(f"nodes={int(cfg['nodes'])}")
    if cfg.get("timemargin_ms") is not None:
        each.append(f"timemargin={int(cfg['timemargin_ms'])}")
    each += [f"option.Threads={int(cfg['threads'])}", f"option.Hash={int(cfg['hash'])}"]
    each += [f"option.{n}={v}" for n, v in cfg.get("engine_options", {}).items()]
    argv += ["-each"] + each
    book = cfg["book"]
    argv += ["-rounds", str(int(cfg["pairs_per_iteration"])), "-games", "2", "-repeat",
             "-concurrency", str(int(cfg["concurrency"])),
             "-openings", f"file={book['file']}", f"format={book.get('format', 'epd')}",
             f"order={book.get('order', 'random')}",
             "-srand", str(int(srand)),
             "-pgnout", f"file={pgn_path}",
             "-autosaveinterval", "0",
             "-report", "penta=true"]
    if cfg.get("strict", True):
        argv.append("-strict")
    argv += [str(x) for x in cfg.get("extra_args", [])]
    return argv


def _termination_kind(result: str, reason: str) -> str:
    """normal (by the rules) | time | adjudication (incl. resign) | abnormal (illegal move, disconnect, stall,
    crash: the iteration fails) | unfinished | other (unknown text: counted only)."""
    r = reason.lower()
    if result == "*":
        return "unfinished"
    if any(word in r for word in ("illegal", "disconnect", "stall", "crash")):
        return "abnormal"
    if "on time" in r or "timeout" in r or "time forfeit" in r:
        return "time"
    if "adjudicat" in r or "resign" in r:
        return "adjudication"
    if any(word in r for word in ("mate", "repetition", "fifty", "stalemate", "insufficient")):
        return "normal"
    return "other"


def parse_output(text: str, pairs: int) -> MatchResult:
    """theta+'s result from fastchess's console output (ANSI colours and CR tolerated); raises ValueError when the
    output is incomplete or inconsistent."""
    lines = [_ANSI.sub("", line).rstrip("\r") for line in text.split("\n")]
    block = None
    for i, line in enumerate(lines):
        m = _HEADER.match(line.strip())
        if m:
            block = (i, m)
    if block is None:
        raise ValueError("no 'Results of ... vs ...' block in the fastchess output")
    start, header = block
    if (header.group(1), header.group(2)) != (PLUS_NAME, MINUS_NAME):
        raise ValueError(f"unexpected engines in the result block: {header.group(1)} vs {header.group(2)}")
    games = ptnml = None
    for line in lines[start + 1:start + 12]:
        line = line.strip()
        if games is None and (m := _GAMES.match(line)):
            games = tuple(int(m.group(j)) for j in range(1, 5))
        if ptnml is None and (m := _PTNML.match(line)):
            ptnml = tuple(int(m.group(j)) for j in range(1, 6))
    if games is None or ptnml is None:
        raise ValueError("the result block has no 'Games:' or no 'Ptnml(0-2):' line")
    n, wins, losses, draws = games
    if n != wins + losses + draws:
        raise ValueError(f"Games {n} != W+L+D {wins + losses + draws}")
    # Cross-check with the per-game lines (theta+'s points per game number).
    points: dict[int, int] = {}
    kinds: dict[str, int] = {}
    for line in lines:
        m = _FINISHED.match(line.strip())
        if not m:
            continue
        number, white, black, result, reason = int(m.group(1)), m.group(2), m.group(3), m.group(4), m.group(5) or ""
        if {white, black} != {PLUS_NAME, MINUS_NAME}:
            raise ValueError(f"game {number}: unexpected engines {white} vs {black}")
        if number in points:
            raise ValueError(f"game {number} reported twice")
        kind = _termination_kind(result, reason)
        kinds[kind] = kinds.get(kind, 0) + 1
        if result == "*":
            raise ValueError(f"game {number} unfinished")
        white_points = {"1-0": 2, "0-1": 0, "1/2-1/2": 1}[result]
        points[number] = white_points if white == PLUS_NAME else 2 - white_points
    if sorted(points) != list(range(1, 2 * pairs + 1)):
        raise ValueError(f"finished games {sorted(points)} are not 1..{2 * pairs}")
    by_lines = (sum(1 for p in points.values() if p == 2), sum(1 for p in points.values() if p == 0),
                sum(1 for p in points.values() if p == 1))
    if by_lines != (wins, losses, draws):
        raise ValueError(f"W/L/D {wins}/{losses}/{draws} disagree with the Finished lines {by_lines}")
    pair_counts = [0] * 5
    for j in range(1, pairs + 1):
        pair_counts[points[2 * j - 1] + points[2 * j]] += 1
    if tuple(pair_counts) != ptnml:
        raise ValueError(f"Ptnml {list(ptnml)} disagrees with the Finished lines {pair_counts}")
    return MatchResult(wins, losses, draws, ptnml,  # type: ignore[arg-type]
                       time_losses=kinds.get("time", 0),
                       abnormal=kinds.get("abnormal", 0) + kinds.get("unfinished", 0),
                       terminations=tuple(sorted(kinds.items())))


# ---------------------------------------------------------------------------------------------------------------
# Child processes: low priority, own process group / job object, killed (with every descendant) on timeout.

IDLE_PRIORITY_CLASS = 0x00000040
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
PRIORITIES = ("idle", "below_normal", "normal")

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _k32.CreateJobObjectW.restype = wintypes.HANDLE
    _k32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    _k32.SetInformationJobObject.restype = wintypes.BOOL
    _k32.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
    _k32.AssignProcessToJobObject.restype = wintypes.BOOL
    _k32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    _k32.TerminateJobObject.restype = wintypes.BOOL
    _k32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    _k32.CloseHandle.restype = wintypes.BOOL
    _k32.CloseHandle.argtypes = (wintypes.HANDLE,)

    class _IoCounters(ctypes.Structure):
        _fields_ = [(n, ctypes.c_ulonglong) for n in ("ReadOperationCount", "WriteOperationCount",
                                                       "OtherOperationCount", "ReadTransferCount",
                                                       "WriteTransferCount", "OtherTransferCount")]

    class _BasicLimits(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class _ExtendedLimits(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", _BasicLimits), ("IoInfo", _IoCounters),
                    ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    class _MemoryStatus(ctypes.Structure):
        _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    def _new_job(priority: str):
        """A job object whose processes die with it (KILL_ON_JOB_CLOSE) and, below normal priority, are held at
        the requested priority class (descendants included)."""
        job = _k32.CreateJobObjectW(None, None)
        if not job:
            return None
        limits = _ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if priority != "normal":
            limits.BasicLimitInformation.LimitFlags |= 0x20  # JOB_OBJECT_LIMIT_PRIORITY_CLASS
            limits.BasicLimitInformation.PriorityClass = (IDLE_PRIORITY_CLASS if priority == "idle"
                                                          else BELOW_NORMAL_PRIORITY_CLASS)
        if not _k32.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            _k32.CloseHandle(job)
            return None
        return job


def free_ram_gib() -> float | None:
    """Available physical memory in GiB, or None where unknown."""
    if os.name == "nt":
        status = _MemoryStatus()
        status.dwLength = ctypes.sizeof(status)
        if _k32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return status.ullAvailPhys / 2 ** 30
        return None
    try:
        with open("/proc/meminfo", "rb") as f:
            for line in f.read().decode().splitlines():
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) / 2 ** 20
    except OSError:
        pass
    return None


@dataclass
class RunOutcome:
    returncode: int | None
    output: str
    seconds: float
    timed_out: bool


def run_child(argv: list[str], cwd: str, out_path: str, timeout_s: float, priority: str) -> RunOutcome:
    """Run argv in cwd at the given priority with stdout+stderr to out_path; on timeout (or Ctrl+C) kill it and
    every process it started (Windows job object / POSIX process group). Returns the captured output."""
    if priority not in PRIORITIES:
        raise ValueError(f"priority must be one of {PRIORITIES}")
    start = time.monotonic()
    timed_out = False
    with open(out_path, "wb") as out:
        if os.name == "nt":
            flags = {"idle": IDLE_PRIORITY_CLASS, "below_normal": BELOW_NORMAL_PRIORITY_CLASS, "normal": 0}[priority]
            proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
                                    creationflags=flags)
            job = _new_job(priority)
            if job is not None and not _k32.AssignProcessToJobObject(job, int(proc._handle)):  # noqa: SLF001
                _k32.CloseHandle(job)
                job = None
            try:
                try:
                    proc.wait(timeout=timeout_s)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    if job is not None:
                        _k32.TerminateJobObject(job, 1)
                    else:
                        proc.kill()
                    proc.wait(timeout=60)
                except KeyboardInterrupt:
                    if job is not None:
                        _k32.TerminateJobObject(job, 1)
                    else:
                        proc.kill()
                    proc.wait(timeout=60)
                    raise
            finally:
                if job is not None:
                    _k32.CloseHandle(job)
        else:
            import signal
            nice = {"idle": 19, "below_normal": 10, "normal": 0}[priority]

            def lower():
                if nice:
                    os.nice(nice)
            proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
                                    preexec_fn=lower, start_new_session=True)
            try:
                proc.wait(timeout=timeout_s)
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                timed_out = isinstance(exc, subprocess.TimeoutExpired)
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait(timeout=60)
                if not timed_out:
                    raise
    with open(out_path, "rb") as f:
        text = f.read().decode("utf-8", errors="replace")
    return RunOutcome(None if timed_out else proc.returncode, text, time.monotonic() - start, timed_out)


def sha256_file(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":  # parse a saved fastchess output: opus_spsa_fastchess.py <output file> <pairs>
    with open(sys.argv[1], "rb") as fh:
        print(parse_output(fh.read().decode("utf-8", errors="replace"), int(sys.argv[2])))
