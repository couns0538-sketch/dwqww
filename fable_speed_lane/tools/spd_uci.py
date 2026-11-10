"""spd_uci.py - pinned UCI driver for the fable2 speed lane (standard library only).

Start it through tools/pin.ps1 (mask 0x78 or a subset, Idle); pinguard re-checks before any engine starts.
The engine is never given a book. Children are never killed: on trouble the driver sends quit, closes
stdin, waits, and reports a survivor (job rule).

Sub-commands
  pins      bench d11/13/16/20/22 net on and net off + perft 5 startpos / kiwipete against the lock pins.
  cold      per FEN: ucinewgame, isready, position fen, go depth D -> rows "i<TAB>depth<TAB>score<TAB>nodes<TAB>bestmove"
            (the row format of QA's bitexact_check L3 / identity_check cold). --first/--count select a slice so
            several pinned workers can share one FEN file; `merge` joins the slices in order.
  merge     join slice files into one TSV and write its sha256.
  warm      one session with the table kept warm: bench 1, go perft 1, then per FEN position + go nodes N with a
            state change every 25 FENs (Hash 1, Hash 64, Clear Hash, UseNNUE false, UseNNUE true, Hash 16,
            ucinewgame, the same position searched twice); bench 13 last. Writes the normalised transcript.
  soak      Threads 2-4 go movetime on 60 FENs (Hash changes, Clear Hash), every bestmove checked against the
            reference exe's own legal-move list; then a Threads 1 depth tail compared with the reference; bench 13.
  perftset  startpos d6, kiwipete d5 and standard positions 3-6 against published counts.
  abba      INDICATIVE timing: A B B A blocks, fresh engine per arm, warm bench 13, timed bench D.
"""
import argparse
import ctypes
import ctypes.wintypes
import hashlib
import json
import os
import queue
import random
import re
import shutil
import statistics
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
PINS_ON = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
PINS_OFF = {11: 375354, 13: 907205, 16: 2448617, 20: 13573040, 22: 24506465}
PERFT5 = {"startpos": 4865609, "kiwipete": 193690690}
PERFT_SET = [
    ("startpos", "startpos", 6, 119060324),
    ("kiwipete", KIWIPETE, 5, 193690690),
    ("pos3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 6, 11030083),
    ("pos4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 5, 15833292),
    ("pos5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 5, 89941194),
    ("pos6", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 5, 164075551),
]
INFO_RX = re.compile(r"^info depth (\d+) .*? score (cp -?\d+|mate -?\d+)(?: (?:lowerbound|upperbound))? nodes (\d+)")
STRIP_RX = re.compile(r" (nps|time) \d+")


def now_vienna() -> str:
    # Vienna = UTC+1 in November (CET); the job runs 2026-11-10/11, no DST change in that window.
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 3600)) + " Vienna"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def six_field(line: str) -> str:
    f = line.split()
    defaults = ["w", "-", "-", "0", "1"]
    if not 1 <= len(f) <= 6 or len(f[0].split("/")) != 8:
        raise ValueError(f"not a FEN: {line!r}")
    while len(f) < 6:
        f.append(defaults[len(f) - 1])
    return " ".join(f)


def read_fens(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return [six_field(x.strip()) for x in f if x.strip() and not x.startswith("#")]


class Survivor(RuntimeError):
    pass


class Engine:
    def __init__(self, exe: str, log_path: str | None = None):
        self.exe = exe
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     cwd=os.path.dirname(os.path.abspath(exe)), text=True, bufsize=1,
                                     encoding="utf-8", errors="replace")
        self.q: queue.Queue = queue.Queue()
        self.log = open(log_path, "a", encoding="utf-8", newline="\n") if log_path else None
        threading.Thread(target=self._pump, daemon=True).start()
        # the child inherits this process's mask and class: read both back before its first command (fail closed)
        mask, prio = pinguard.read(ctypes.wintypes.HANDLE(int(self.proc._handle)))
        if mask == 0 or (mask & ~pinguard.LANE) != 0 or prio != pinguard.IDLE_PRIORITY_CLASS:
            self.close()
            raise SystemExit(f"engine not pinned (mask {mask:#x}, class {prio:#x})")

    def _pump(self):
        for line in self.proc.stdout:
            self.q.put(line.rstrip("\r\n"))
        self.q.put(None)

    def send(self, line: str):
        if self.log:
            self.log.write(f"> {line}\n")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def until(self, pred, timeout_s: float, collect: list | None = None) -> str:
        deadline = time.monotonic() + timeout_s
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"engine silent for {timeout_s}s")
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError(f"engine silent for {timeout_s}s")
            if line is None:
                raise RuntimeError("engine closed its output")
            if self.log:
                self.log.write(line + "\n")
            if collect is not None:
                collect.append(line)
            if pred(line):
                return line

    def handshake(self, options: list[str]):
        self.send("uci")
        self.until(lambda s: s == "uciok", 60)
        for kv in ["Threads=1", "Hash=16"] + options:
            name, _, value = kv.partition("=")
            self.send(f"setoption name {name} value {value}")
        self.sync()

    def sync(self, timeout_s: float = 120):
        self.send("isready")
        self.until(lambda s: s == "readyok", timeout_s)

    def cpu_seconds(self) -> float:
        """CPU cycles the engine process has used so far (QueryProcessCycleTime), in units of 1e9 cycles.
        Cycles are counted only while the process runs, so preemption by other jobs does not add to them
        (cache and SMT pressure from other jobs still does)."""
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.QueryProcessCycleTime.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(ctypes.c_uint64)]
        k.QueryProcessCycleTime.restype = ctypes.wintypes.BOOL
        cycles = ctypes.c_uint64()
        if not k.QueryProcessCycleTime(ctypes.wintypes.HANDLE(int(self.proc._handle)), ctypes.byref(cycles)):
            return float("nan")
        return cycles.value / 1e9

    def faults_and_times(self) -> tuple[int, float, float]:
        """(page faults so far, kernel seconds, user seconds) of the engine process. Read before and after a
        timed section, the differences tell a memory-management cost (faults, kernel time) from a plain slowdown
        of the engine's own code. Kernel and user time advance in steps of one clock tick (about 16 ms)."""
        class PMC(ctypes.Structure):
            _fields_ = [("cb", ctypes.wintypes.DWORD), ("PageFaultCount", ctypes.wintypes.DWORD)] + \
                       [(n, ctypes.c_size_t) for n in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                                                       "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                                                       "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
        h = ctypes.wintypes.HANDLE(int(self.proc._handle))
        ps = ctypes.WinDLL("psapi", use_last_error=True)
        ps.GetProcessMemoryInfo.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(PMC), ctypes.wintypes.DWORD]
        ps.GetProcessMemoryInfo.restype = ctypes.wintypes.BOOL
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        faults = pmc.PageFaultCount if ps.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb) else -1
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.GetProcessTimes.argtypes = [ctypes.wintypes.HANDLE] + [ctypes.POINTER(ctypes.c_uint64)] * 4
        k.GetProcessTimes.restype = ctypes.wintypes.BOOL
        t = [ctypes.c_uint64() for _ in range(4)]
        if not k.GetProcessTimes(h, *[ctypes.byref(v) for v in t]):
            return faults, float("nan"), float("nan")
        return faults, t[2].value / 1e7, t[3].value / 1e7

    def image_base(self) -> int:
        """Address the exe image is loaded at in the engine process (0 if it cannot be read)."""
        ps = ctypes.WinDLL("psapi", use_last_error=True)
        ps.EnumProcessModules.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(ctypes.c_void_p), ctypes.wintypes.DWORD,
                                          ctypes.POINTER(ctypes.wintypes.DWORD)]
        ps.EnumProcessModules.restype = ctypes.wintypes.BOOL
        mods = (ctypes.c_void_p * 4)()
        need = ctypes.wintypes.DWORD()
        for _ in range(50):                      # the module list is empty until the loader has run
            if ps.EnumProcessModules(ctypes.wintypes.HANDLE(int(self.proc._handle)), mods, ctypes.sizeof(mods), ctypes.byref(need)):
                return int(mods[0] or 0)
            time.sleep(0.02)
        return 0

    def bench(self, depth: int, timeout_s: float = 1800) -> tuple[int, int, float]:
        t0 = time.perf_counter()
        self.send(f"bench {depth}")
        line = self.until(lambda s: f"bench depth {depth} nodes " in s, timeout_s)
        wall = time.perf_counter() - t0
        tok = line.split()
        return int(tok[tok.index("nodes") + 1]), int(tok[tok.index("time") + 1]), wall

    def perft(self, fen: str, depth: int, timeout_s: float = 1800, moves: list | None = None) -> int:
        self.send("position startpos" if fen == "startpos" else f"position fen {fen}")
        self.send(f"go perft {depth}")
        lines: list[str] = []
        last = self.until(lambda s: s.startswith("nodes "), timeout_s, lines)
        if moves is not None:
            moves.extend(x.split(":")[0] for x in lines if ": " in x and not x.startswith("info"))
        return int(last.split()[1])

    def close(self):
        try:
            self.send("quit")
        except (OSError, ValueError):
            pass
        try:
            self.proc.stdin.close()
        except OSError:
            pass
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            raise Survivor(f"engine survivor PID {self.proc.pid} ({self.exe}); left running, not killed")
        finally:
            if self.log:
                self.log.close()
        if self.proc.returncode != 0:
            raise RuntimeError(f"engine exit code {self.proc.returncode}")


def search_row(eng: Engine, fen: str, go: str, timeout_s: float, newgame: bool) -> tuple[str, str, str, str]:
    if newgame:
        eng.send("ucinewgame")
        eng.sync()
    lines: list[str] = []
    eng.send("position fen " + fen)
    eng.send("go " + go)
    best = eng.until(lambda s: s.startswith("bestmove"), timeout_s, lines)
    bad = [s for s in lines if s.startswith("info string") and "invalid" in s]
    if bad:
        raise RuntimeError(f"engine rejected FEN ({fen}): {bad[0]}")
    infos = [s for s in lines if s.startswith("info depth ")]
    m = INFO_RX.match(infos[-1]) if infos else None
    d, sc, n = m.groups() if m else ("", "", "")
    return d, sc, n, best.split()[1]


# ---------------------------------------------------------------------------------------------------------------
def cmd_pins(a) -> int:
    res = {"exe": a.exe, "sha256": sha256_file(a.exe), "pin": pinguard.ensure(), "when": now_vienna(),
           "bench": {}, "perft5": {}, "ok": True}
    for label, net, pins in (("net_on", "true", PINS_ON), ("net_off", "false", PINS_OFF)):
        eng = Engine(a.exe, a.log)
        eng.handshake(["OwnBook=false", f"UseNNUE={net}"])
        for d in (11, 13, 16, 20, 22):
            nodes, ms, _ = eng.bench(d)
            good = nodes == pins[d]
            res["bench"][f"{label}_d{d}"] = {"nodes": nodes, "want": pins[d], "match": good,
                                             "nps": nodes * 1000 // max(ms, 1)}
            res["ok"] &= good
            print(f"bench {label} d{d}: {nodes} want {pins[d]} {'OK' if good else 'MISMATCH'}", flush=True)
        eng.close()
    eng = Engine(a.exe, a.log)
    eng.handshake(["OwnBook=false"])
    for name, fen in (("startpos", "startpos"), ("kiwipete", KIWIPETE)):
        nodes = eng.perft(fen, 5)
        good = nodes == PERFT5[name]
        res["perft5"][name] = {"nodes": nodes, "want": PERFT5[name], "match": good}
        res["ok"] &= good
        print(f"perft5 {name}: {nodes} want {PERFT5[name]} {'OK' if good else 'MISMATCH'}", flush=True)
    eng.close()
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1)
    print("PINS " + ("MATCH 12/12" if res["ok"] else "MISMATCH"), flush=True)
    return 0 if res["ok"] else 3


def cmd_cold(a) -> int:
    print(pinguard.ensure(), flush=True)
    fens = read_fens(a.fens)
    first = a.first
    last = len(fens) if a.count <= 0 else min(len(fens), first + a.count)
    opts = ["OwnBook=false"] + [x for x in a.options.split(";") if x]
    eng = Engine(a.exe, a.log)
    eng.handshake(opts)
    t0 = time.monotonic()
    tmp = a.out + ".part"
    with open(tmp, "w", encoding="utf-8", newline="\n") as out:
        for i in range(first, last):
            d, sc, n, best = search_row(eng, fens[i], f"depth {a.depth}", 1800, True)
            out.write(f"{i}\t{d}\t{sc}\t{n}\t{best}\n")
            if (i - first) % 500 == 0:
                out.flush()
                print(f"cold {i}/{last} {time.monotonic() - t0:.0f}s", flush=True)
    eng.close()
    os.replace(tmp, a.out)
    print(f"COLD DONE {last - first} rows [{first},{last}) depth {a.depth} options {opts} in "
          f"{time.monotonic() - t0:.0f}s sha256 {sha256_file(a.out)}", flush=True)
    return 0


def cmd_merge(a) -> int:
    rows: list[str] = []
    for part in a.parts:
        with open(part, encoding="utf-8") as f:
            rows.extend(x.rstrip("\n") for x in f if x.strip())
    idx = [int(r.split("\t", 1)[0]) for r in rows]
    if idx != list(range(len(rows))):
        print(f"MERGE ERROR: indices are not 0..{len(rows) - 1} in order")
        return 3
    blank = sum(1 for r in rows if not re.search(r"\t\d+\t", r))
    distinct = len({r.split("\t", 1)[1] for r in rows})
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(rows) + "\n")
    digest = sha256_file(a.out)
    with open(a.out + ".sha256", "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{digest}  {os.path.basename(a.out)}\n")
    print(f"MERGED {len(rows)} rows, {distinct} distinct results, {blank} rows without numbers, sha256 {digest}")
    if len(rows) >= 100 and distinct < len(rows) // 10:
        print("MERGE ERROR: degenerate set")
        return 3
    return 0 if blank == 0 else 3


WARM_CYCLE = ["setoption name Hash value 1", "setoption name Hash value 64", "setoption name Clear Hash",
              "setoption name UseNNUE value false", "setoption name UseNNUE value true",
              "setoption name Hash value 16", "ucinewgame", "REPEAT"]


def cmd_warm(a) -> int:
    print(pinguard.ensure(), flush=True)
    fens = read_fens(a.fens)[:a.n]
    log: list[str] = []
    eng = Engine(a.exe, a.log)

    def rec(line):
        log.append(line)
        return line

    eng.send("bench 1")
    rec(STRIP_RX.sub("", eng.until(lambda s: "bench depth" in s, 600)))
    moves: list[str] = []
    rec(f"perft1 {eng.perft('startpos', 1, 600, moves)} {' '.join(sorted(moves))}")
    eng.handshake(["UseNNUE=true", "OwnBook=false"])
    repeat = False
    for i, fen in enumerate(fens):
        if i and i % 25 == 0:
            step = WARM_CYCLE[(i // 25 - 1) % len(WARM_CYCLE)]
            rec("> " + step)
            if step == "REPEAT":
                repeat = True
            else:
                eng.send(step)
                eng.sync()
        for _ in range(2 if repeat else 1):
            d, sc, n, best = search_row(eng, fen, f"nodes {a.nodes}", 600, False)
            rec(f"{i}\t{d}\t{sc}\t{n}\t{best}")
        repeat = False
    nodes, _, _ = eng.bench(13)
    rec(f"bench13 {nodes}")
    eng.close()
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(log) + "\n")
    digest = sha256_file(a.out)
    with open(a.out + ".sha256", "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{digest}  {os.path.basename(a.out)}\n")
    searches = sum(1 for x in log if re.match(r"^\d+\t", x))
    print(f"WARM DONE {len(fens)} FENs, {searches} searches, bench13 {nodes} "
          f"({'pin' if nodes == PINS_ON[13] else 'NOT THE PIN'}), sha256 {digest}", flush=True)
    return 0 if nodes == PINS_ON[13] else 3


def cmd_soak(a) -> int:
    print(pinguard.ensure(), flush=True)
    fens = read_fens(a.fens)
    os.makedirs(a.out, exist_ok=False)
    ref = Engine(a.ref)
    ref.handshake(["OwnBook=false", "UseNNUE=true"])
    legal: list[list[str]] = []
    for fen in fens[:60]:
        mv: list[str] = []
        ref.perft(fen, 1, 600, mv)
        legal.append(mv)
    tail_ref = [search_row(ref, fen, "depth 13", 600, True) for fen in fens[:50]]
    ref.close()
    receipt = {"exe": a.exe, "sha256": sha256_file(a.exe), "ref": a.ref, "ref_sha256": sha256_file(a.ref),
               "when": now_vienna(), "threads": [2, 3, 4], "searches": [], "status": "RUNNING"}
    eng = Engine(a.exe, os.path.join(a.out, "soak.uci.log"))
    ok = True
    try:
        eng.handshake(["OwnBook=false", "UseNNUE=true"])
        for i, fen in enumerate(fens[:60]):
            threads = 2 + i % 3
            eng.send(f"setoption name Threads value {threads}")
            if i % 10 == 0:
                eng.send(f"setoption name Hash value {16 if i % 20 == 0 else 32}")
            if i == 30:
                eng.send("setoption name Clear Hash")
            eng.sync()
            t0 = time.monotonic()
            eng.send("position fen " + fen)
            eng.send("go movetime 300")
            best = eng.until(lambda s: s.startswith("bestmove "), 20).split()[1]
            elapsed = time.monotonic() - t0
            good = (best in legal[i]) or (best == "0000" and not legal[i])
            ok &= good and elapsed < 10
            receipt["searches"].append({"i": i, "threads": threads, "elapsed": round(elapsed, 3), "bestmove": best,
                                        "legal": good})
        for kv in ("Threads value 1", "Hash value 16", "UseNNUE value true"):
            eng.send("setoption name " + kv)
        eng.sync()
        tail = [search_row(eng, fen, "depth 13", 600, True) for fen in fens[:50]]
        receipt["tail_matches"] = sum(1 for x, y in zip(tail, tail_ref) if x == y)
        ok &= receipt["tail_matches"] == 50
        nodes, _, _ = eng.bench(13)
        receipt["bench13"] = nodes
        ok &= nodes == PINS_ON[13]
    finally:
        eng.close()
    receipt["status"] = "PASS" if ok else "FAIL"
    with open(os.path.join(a.out, "RECEIPT.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, indent=1)
    illegal = [s for s in receipt["searches"] if not s["legal"]]
    print(f"SOAK_{receipt['status']} T2-4 legal {60 - len(illegal)}/60, max elapsed "
          f"{max(s['elapsed'] for s in receipt['searches']):.2f}s, T1 tail {receipt.get('tail_matches')}/50, "
          f"bench13 {receipt.get('bench13')}", flush=True)
    return 0 if ok else 3


def cmd_perftset(a) -> int:
    print(pinguard.ensure(), flush=True)
    res = {"exe": a.exe, "sha256": sha256_file(a.exe), "when": now_vienna(), "rows": [], "ok": True}
    eng = Engine(a.exe)
    eng.handshake(["OwnBook=false"])
    for name, fen, depth, want in PERFT_SET:
        t0 = time.monotonic()
        nodes = eng.perft(fen, depth)
        good = nodes == want
        res["rows"].append({"name": name, "fen": fen, "depth": depth, "nodes": nodes, "want": want, "match": good,
                            "seconds": round(time.monotonic() - t0, 2)})
        res["ok"] &= good
        print(f"perft {name} d{depth}: {nodes} want {want} {'OK' if good else 'MISMATCH'}", flush=True)
    eng.close()
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1)
    print("PERFTSET " + ("MATCH 6/6" if res["ok"] else "MISMATCH"), flush=True)
    return 0 if res["ok"] else 3


def cpu_times():
    class P(ctypes.Structure):
        _fields_ = [("idle", ctypes.c_int64), ("kernel", ctypes.c_int64), ("user", ctypes.c_int64),
                    ("dpc", ctypes.c_int64), ("interrupt", ctypes.c_int64), ("count", ctypes.c_uint32)]
    n = os.cpu_count()
    arr = (P * n)()
    got = ctypes.c_ulong()
    rc = ctypes.WinDLL("ntdll").NtQuerySystemInformation(8, arr, ctypes.sizeof(arr), ctypes.byref(got))
    if rc != 0:
        return None
    return [(x.idle, x.kernel + x.user) for x in arr]


def clear_dynamic_base(path: str) -> None:
    """Diagnostic copies only: clear IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE (0x40) in a PE32+ file, so that the
    image is loaded at its preferred base in every process instead of at a randomised address."""
    with open(path, "r+b") as f:
        f.seek(0x3C)
        pe = int.from_bytes(f.read(4), "little")
        f.seek(pe)
        if f.read(4) != b"PE\0\0":
            raise RuntimeError(f"not a PE file: {path}")
        f.seek(pe + 24)
        if int.from_bytes(f.read(2), "little") != 0x20B:
            raise RuntimeError(f"not a PE32+ file: {path}")
        off = pe + 24 + 70
        f.seek(off)
        flags = int.from_bytes(f.read(2), "little")
        f.seek(off)
        f.write((flags & ~0x0040).to_bytes(2, "little"))


def busy_pct(before, after):
    if not before or not after:
        return {}
    out = {}
    for i, (b, c) in enumerate(zip(before, after)):
        total = c[1] - b[1]
        out[str(i)] = round(100.0 * (total - (c[0] - b[0])) / total, 1) if total > 0 else None
    return out


def cmd_abba(a) -> int:
    pin = pinguard.ensure()
    print(pin, flush=True)
    os.makedirs(a.out, exist_ok=False)
    net = "true" if a.net == "on" else "false"
    pins = PINS_ON if a.net == "on" else PINS_OFF
    # Hash 16 is the pinned setting: node counts must equal the pins. With another --hash the tree differs from
    # the pinned one, so the rule becomes: every arm (A and B alike) must report the same node counts.
    want_warm = pins[13] if a.hash == 16 else None
    want_timed = pins[a.depth] if a.hash == 16 else None
    cfg = {"label": "INDICATIVE - not the QA quiet ABBA", "a": a.a, "b": a.b, "a_sha256": sha256_file(a.a),
           "b_sha256": sha256_file(a.b), "pin": pin, "threads": 1,
           "options": f"UseNNUE={net},Threads=1,Hash={a.hash},OwnBook=false",
           "warmup": "fresh engine each arm, bench 13 once", "timed": f"bench {a.depth}", "expected_nodes": want_timed,
           "blocks": a.blocks, "order": "ABBA, odd blocks BAAB" if a.alternate else "ABBA", "started": now_vienna(),
           "recopy": (f"a new copy of the exe for every {a.recopy_per}" if a.recopy else "none: the same two files for all blocks"),
           "fixed_base": bool(a.fixed_base)}
    samples = []
    ratios = []
    cpu_ratios = []
    cpu0 = cpu_times()
    leftovers = []
    if a.fixed_base and not a.recopy:
        raise SystemExit("--fixed-base changes a header flag and is applied to copies only: give --recopy DIR")
    if a.recopy:
        os.makedirs(a.recopy, exist_ok=True)

    def fresh(src: str, tag: str) -> str:
        dst = os.path.join(a.recopy, f"abba_{os.getpid()}_{tag}.exe")
        shutil.copyfile(src, dst)
        if a.fixed_base:
            clear_dynamic_base(dst)
        leftovers.append(dst)
        return dst

    for block in range(a.blocks):
        arms = []
        # --recopy DIR: the exes run from copies made anew (per arm, or per block with --recopy-per block). A file
        # that is run again and again keeps one load address and one set of physical memory pages for its code and
        # constants, so two fixed files are compared with one fixed draw each for the whole run: byte-identical
        # copies of one exe were measured up to 6 % apart that way (BENCH.md). With new copies the draw changes
        # from arm to arm and shows up in the spread of the block ratios instead of biasing their median.
        block_exe = {}
        if a.recopy and a.recopy_per == "block":
            block_exe = {"A": fresh(a.a, f"{block}_a"), "B": fresh(a.b, f"{block}_b")}
        # --alternate: odd blocks run B A A B, so that whatever favours the middle arms of a block cancels over
        # two blocks (lock against lock gave about +0.3 % to +0.8 % for the middle arms without it)
        order = "BAAB" if (a.alternate and block % 2 == 1) else "ABBA"
        for idx, letter in enumerate(order):
            src = a.a if letter == "A" else a.b
            exe = block_exe.get(letter) or (fresh(src, f"{block}_{idx}") if a.recopy else src)
            eng = Engine(exe)
            base = eng.image_base()
            eng.handshake(["OwnBook=false", f"UseNNUE={net}"] + ([f"Hash={a.hash}"] if a.hash != 16 else []))
            warm, _, _ = eng.bench(13)
            if want_warm is None:
                want_warm = warm
            if warm != want_warm:
                eng.close()
                raise SystemExit(f"warm bench nodes {warm} != {want_warm}")
            f0, k0, u0 = eng.faults_and_times()
            cpu_a = eng.cpu_seconds()
            nodes, ms, wall = eng.bench(a.depth)
            cpu = eng.cpu_seconds() - cpu_a
            f1, k1, u1 = eng.faults_and_times()
            eng.close()
            if want_timed is None:
                want_timed = nodes
            if nodes != want_timed:
                raise SystemExit(f"timed bench nodes {nodes} != {want_timed}")
            arm = {"block": block, "letter": letter, "slot": idx, "nodes": nodes, "wall_s": wall, "cpu_s": cpu, "engine_ms": ms,
                   "nps": nodes / wall, "nps_cpu": nodes / cpu if cpu > 0 else 0.0, "image_base": hex(base),
                   "page_faults": f1 - f0, "kernel_s": round(k1 - k0, 4), "user_s": round(u1 - u0, 4)}
            arms.append(arm)
            samples.append(arm)
        arm_a = [x for x in arms if x["letter"] == "A"]
        arm_b = [x for x in arms if x["letter"] == "B"]
        ratio = ((arm_b[0]["nps"] * arm_b[1]["nps"]) / (arm_a[0]["nps"] * arm_a[1]["nps"])) ** 0.5
        ratios.append(ratio)
        if all(x["nps_cpu"] > 0 for x in arms):
            cpu_ratios.append(((arm_b[0]["nps_cpu"] * arm_b[1]["nps_cpu"]) / (arm_a[0]["nps_cpu"] * arm_a[1]["nps_cpu"])) ** 0.5)
        print(f"ABBA block {block} ({order}) wall ratio {ratio:.5f} cpu ratio {cpu_ratios[-1] if cpu_ratios else float('nan'):.5f}", flush=True)
        for path in list(leftovers):            # this run's own copies; a file still held by the exiting engine stays for the next pass
            try:
                os.remove(path)
                leftovers.remove(path)
            except OSError:
                pass
    time.sleep(1.0)
    for path in leftovers:
        try:
            os.remove(path)
        except OSError:
            print(f"left behind (own temporary copy): {path}", flush=True)
    cpu1 = cpu_times()
    med = statistics.median(ratios)
    q = statistics.quantiles(ratios, n=4, method="inclusive") if len(ratios) >= 2 else [med, med, med]
    rng = random.Random(20261110)
    boot = sorted(statistics.median(rng.choices(ratios, k=len(ratios))) for _ in range(10000))
    summ = {"median_ratio": med, "median_delta_pct": 100 * (med - 1), "mean_delta_pct": 100 * (statistics.mean(ratios) - 1),
            "q1_pct": 100 * (q[0] - 1), "q3_pct": 100 * (q[2] - 1), "iqr_pct": 100 * (q[2] - q[0]),
            "min_pct": 100 * (min(ratios) - 1), "max_pct": 100 * (max(ratios) - 1),
            "boot95_pct": [100 * (boot[249] - 1), 100 * (boot[9749] - 1)], "blocks": len(ratios),
            "block_ratios": ratios, "a_nps_median": statistics.median(s["nps"] for s in samples if s["letter"] == "A"),
            "b_nps_median": statistics.median(s["nps"] for s in samples if s["letter"] == "B"),
            "cpu_busy_pct_during": busy_pct(cpu0, cpu1), "finished": now_vienna()}
    if cpu_ratios:
        cq = statistics.quantiles(cpu_ratios, n=4, method="inclusive") if len(cpu_ratios) >= 2 else [cpu_ratios[0]] * 3
        summ.update({"cpu_median_delta_pct": 100 * (statistics.median(cpu_ratios) - 1),
                     "cpu_q1_pct": 100 * (cq[0] - 1), "cpu_q3_pct": 100 * (cq[2] - 1),
                     "cpu_min_pct": 100 * (min(cpu_ratios) - 1), "cpu_max_pct": 100 * (max(cpu_ratios) - 1),
                     "cpu_block_ratios": cpu_ratios,
                     "note": "cpu = engine process cycle count over the timed bench (QueryProcessCycleTime), unit 1e9 cycles"})
    with open(os.path.join(a.out, "PROTOCOL.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, indent=1)
    with open(os.path.join(a.out, "SAMPLES.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(samples, f, indent=1)
    with open(os.path.join(a.out, "SUMMARY.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(summ, f, indent=1)
    print(f"ABBA INDICATIVE net {a.net} d{a.depth}: median {summ['median_delta_pct']:+.2f} % "
          f"[IQR {summ['q1_pct']:+.2f} .. {summ['q3_pct']:+.2f}; min {summ['min_pct']:+.2f}, max {summ['max_pct']:+.2f}; "
          f"boot95 {summ['boot95_pct'][0]:+.2f} .. {summ['boot95_pct'][1]:+.2f}] over {len(ratios)} blocks", flush=True)
    if cpu_ratios:
        print(f"ABBA INDICATIVE by CPU cycles: median {summ['cpu_median_delta_pct']:+.2f} % "
              f"[IQR {summ['cpu_q1_pct']:+.2f} .. {summ['cpu_q3_pct']:+.2f}; min {summ['cpu_min_pct']:+.2f}, max {summ['cpu_max_pct']:+.2f}]",
              flush=True)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("pins"); s.add_argument("--exe", required=True); s.add_argument("--out", required=True); s.add_argument("--log")
    s = sub.add_parser("cold"); s.add_argument("--exe", required=True); s.add_argument("--fens", required=True)
    s.add_argument("--out", required=True); s.add_argument("--first", type=int, default=0); s.add_argument("--count", type=int, default=0)
    s.add_argument("--depth", type=int, default=13); s.add_argument("--options", default=""); s.add_argument("--log")
    s = sub.add_parser("merge"); s.add_argument("--out", required=True); s.add_argument("parts", nargs="+")
    s = sub.add_parser("warm"); s.add_argument("--exe", required=True); s.add_argument("--fens", required=True)
    s.add_argument("--out", required=True); s.add_argument("--n", type=int, default=1000); s.add_argument("--nodes", type=int, default=20000); s.add_argument("--log")
    s = sub.add_parser("soak"); s.add_argument("--exe", required=True); s.add_argument("--ref", required=True)
    s.add_argument("--fens", required=True); s.add_argument("--out", required=True)
    s = sub.add_parser("perftset"); s.add_argument("--exe", required=True); s.add_argument("--out", required=True)
    s = sub.add_parser("abba"); s.add_argument("--a", required=True); s.add_argument("--b", required=True)
    s.add_argument("--out", required=True); s.add_argument("--blocks", type=int, default=10)
    s.add_argument("--depth", type=int, default=16); s.add_argument("--net", choices=["on", "off"], default="on")
    s.add_argument("--hash", type=int, default=16); s.add_argument("--recopy", default="")
    s.add_argument("--recopy-per", choices=["arm", "block"], default="arm"); s.add_argument("--fixed-base", action="store_true")
    s.add_argument("--alternate", action="store_true")
    a = p.parse_args()
    return {"pins": cmd_pins, "cold": cmd_cold, "merge": cmd_merge, "warm": cmd_warm, "soak": cmd_soak,
            "perftset": cmd_perftset, "abba": cmd_abba}[a.cmd](a)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Survivor as exc:
        print("SURVIVOR:", exc, flush=True)
        raise SystemExit(4)
    except (RuntimeError, TimeoutError, OSError, ValueError) as exc:
        print("ERROR:", exc, flush=True)
        raise SystemExit(1)
