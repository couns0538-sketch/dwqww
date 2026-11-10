r"""spd_rip_sampler.py - self-time profile of one `bench N` of a Forge exe (standard library only, own code).

Method: start the engine as a pinned child, and while the bench runs read the instruction pointer of its
threads (SuspendThread / GetThreadContext / ResumeThread). A sample is taken only when the thread's own
CPU-cycle counter (QueryThreadCycleTime) has advanced by at least --quantum cycles since its last sample,
so samples are spread evenly over the thread's CPU time and not over wall time. That matters here: the lane
is shared, and a preempted thread would otherwise be counted again and again at the same address.
Only this job's own child is ever suspended, for microseconds, and always resumed.

Addresses are stored as RVAs (address - runtime image base) and symbolised afterwards with llvm-symbolizer
--inlines against the exe's PDB, so time inside inlined code is attributed to the function it was written in.
The lock recipe's exe also carries DWARF sections of the static runtime libraries, and llvm-symbolizer then
ignores the PDB; pass --symexe a copy made with `llvm-objcopy --strip-debug` (same RVAs, PDB still referenced).

usage: spd_rip_sampler.py --exe X --out DIR [--depth 20] [--net on|off] [--quantum 1500000]
                          [--symexe COPY_WITHOUT_DWARF.exe] [--symbolizer PATH\llvm-symbolizer.exe] [--repeat 1]
"""
import argparse
import collections
import ctypes
import ctypes.wintypes as wt
import json
import os
import queue
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)

TH32CS_SNAPTHREAD = 0x00000004
THREAD_ACCESS = 0x0002 | 0x0008 | 0x0040          # SUSPEND_RESUME | GET_CONTEXT | QUERY_INFORMATION
CONTEXT_CONTROL = 0x00100001
CONTEXT_SIZE = 1232
OFF_FLAGS = 0x30
OFF_RIP = 0xF8


class THREADENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ThreadID", wt.DWORD),
                ("th32OwnerProcessID", wt.DWORD), ("tpBasePri", wt.LONG), ("tpDeltaPri", wt.LONG),
                ("dwFlags", wt.DWORD)]


k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
k32.Thread32First.argtypes = [wt.HANDLE, ctypes.POINTER(THREADENTRY32)]
k32.Thread32Next.argtypes = [wt.HANDLE, ctypes.POINTER(THREADENTRY32)]
k32.OpenThread.restype = wt.HANDLE
k32.OpenThread.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.SuspendThread.argtypes = [wt.HANDLE]
k32.SuspendThread.restype = wt.DWORD
k32.ResumeThread.argtypes = [wt.HANDLE]
k32.ResumeThread.restype = wt.DWORD
k32.GetThreadContext.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.GetThreadContext.restype = wt.BOOL
k32.QueryThreadCycleTime.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_uint64)]
k32.QueryThreadCycleTime.restype = wt.BOOL
psapi.EnumProcessModules.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_void_p), wt.DWORD, ctypes.POINTER(wt.DWORD)]
psapi.EnumProcessModules.restype = wt.BOOL


class MODULEINFO(ctypes.Structure):
    _fields_ = [("lpBaseOfDll", ctypes.c_void_p), ("SizeOfImage", wt.DWORD), ("EntryPoint", ctypes.c_void_p)]


psapi.GetModuleInformation.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.POINTER(MODULEINFO), wt.DWORD]
psapi.GetModuleInformation.restype = wt.BOOL


def thread_ids(pid: int) -> list[int]:
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    out = []
    te = THREADENTRY32()
    te.dwSize = ctypes.sizeof(THREADENTRY32)
    ok = k32.Thread32First(snap, ctypes.byref(te))
    while ok:
        if te.th32OwnerProcessID == pid:
            out.append(te.th32ThreadID)
        ok = k32.Thread32Next(snap, ctypes.byref(te))
    k32.CloseHandle(snap)
    return out


def image_range(hproc) -> tuple[int, int]:
    mods = (ctypes.c_void_p * 8)()
    need = wt.DWORD()
    if not psapi.EnumProcessModules(hproc, mods, ctypes.sizeof(mods), ctypes.byref(need)):
        raise RuntimeError(f"EnumProcessModules failed ({ctypes.get_last_error()})")
    info = MODULEINFO()
    if not psapi.GetModuleInformation(hproc, mods[0], ctypes.byref(info), ctypes.sizeof(info)):
        raise RuntimeError(f"GetModuleInformation failed ({ctypes.get_last_error()})")
    return info.lpBaseOfDll, info.SizeOfImage


def profile_once(a, run_index: int, hist: collections.Counter, stats: dict):
    proc = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            cwd=os.path.dirname(os.path.abspath(a.exe)), text=True, bufsize=1)
    mask, prio = pinguard.read(wt.HANDLE(int(proc._handle)))
    if mask == 0 or (mask & ~pinguard.LANE) != 0 or prio != pinguard.IDLE_PRIORITY_CLASS:
        proc.stdin.close()
        raise SystemExit(f"engine not pinned (mask {mask:#x}, class {prio:#x})")
    q: queue.Queue = queue.Queue()

    def pump():
        for line in proc.stdout:
            q.put(line.rstrip("\r\n"))
        q.put(None)

    threading.Thread(target=pump, daemon=True).start()

    def send(s):
        proc.stdin.write(s + "\n")
        proc.stdin.flush()

    def until(pred, timeout):
        end = time.monotonic() + timeout
        while True:
            line = q.get(timeout=max(0.1, end - time.monotonic()))
            if line is None:
                raise RuntimeError("engine closed its output")
            if pred(line):
                return line

    send("uci")
    until(lambda s: s == "uciok", 60)
    for kv in ("Threads value 1", "Hash value 16", "OwnBook value false",
               "UseNNUE value " + ("true" if a.net == "on" else "false")):
        send("setoption name " + kv)
    send("isready")
    until(lambda s: s == "readyok", 120)
    send("bench 11")                                   # warm-up: tables, weights and code pages touched
    until(lambda s: "bench depth 11 nodes" in s, 600)

    base, size = image_range(wt.HANDLE(int(proc._handle)))
    handles = {}
    for tid in thread_ids(proc.pid):
        h = k32.OpenThread(THREAD_ACCESS, False, tid)
        if h:
            handles[tid] = h
    last = {}
    cyc = ctypes.c_uint64()
    for tid, h in handles.items():
        k32.QueryThreadCycleTime(h, ctypes.byref(cyc))
        last[tid] = cyc.value
    raw = ctypes.create_string_buffer(CONTEXT_SIZE + 16)
    ctx = (ctypes.addressof(raw) + 15) & ~15
    done = threading.Event()
    result = {}

    def waiter():
        try:
            result["line"] = until(lambda s: f"bench depth {a.depth} nodes" in s, 3600)
        finally:
            done.set()

    send(f"bench {a.depth}")
    threading.Thread(target=waiter, daemon=True).start()
    taken = outside = polls = 0
    t0 = time.perf_counter()
    while not done.is_set():
        time.sleep(0.0005)
        polls += 1
        for tid, h in handles.items():
            if not k32.QueryThreadCycleTime(h, ctypes.byref(cyc)):
                continue
            if cyc.value - last[tid] < a.quantum:
                continue
            last[tid] = cyc.value
            if k32.SuspendThread(h) == 0xFFFFFFFF:
                continue
            try:
                ctypes.c_uint32.from_address(ctx + OFF_FLAGS).value = CONTEXT_CONTROL
                ok = k32.GetThreadContext(h, ctx)
                rip = ctypes.c_uint64.from_address(ctx + OFF_RIP).value if ok else 0
            finally:
                k32.ResumeThread(h)
            if not ok:
                continue
            taken += 1
            if base <= rip < base + size:
                hist[rip - base] += 1
            else:
                outside += 1
    wall = time.perf_counter() - t0
    for h in handles.values():
        k32.CloseHandle(h)
    send("quit")
    proc.stdin.close()
    proc.wait(timeout=60)
    stats.setdefault("runs", []).append({"run": run_index, "bench_line": result.get("line"), "wall_s": round(wall, 2),
                                         "samples": taken, "outside_image": outside, "polls": polls,
                                         "image_base": hex(base), "image_size": size, "threads": len(handles)})
    print(f"run {run_index}: {taken} samples ({outside} outside the image) in {wall:.1f}s; {result.get('line')}", flush=True)


def symbolize(a, rvas: list[int]) -> dict:
    cmd = [a.symbolizer, f"--obj={a.symexe or a.exe}", "--relative-address", "--inlines", "--functions=linkage",
           "--demangle", "--output-style=JSON"]
    inp = "\n".join(hex(r) for r in rvas) + "\n"
    r = subprocess.run(cmd, input=inp, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = {}
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            o = json.loads(line)
        except ValueError:
            continue
        frames = [(f.get("FunctionName") or "??", os.path.basename(f.get("FileName") or ""), f.get("Line") or 0)
                  for f in o.get("Symbol", [])]
        out[int(o["Address"], 16)] = frames
    if r.returncode != 0 or not out:
        print("symbolizer stderr:", r.stderr[:400], flush=True)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--exe", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--depth", type=int, default=20)
    p.add_argument("--net", choices=["on", "off"], default="on")
    p.add_argument("--quantum", type=int, default=1_500_000)
    p.add_argument("--repeat", type=int, default=1)
    p.add_argument("--symexe", default=None)
    p.add_argument("--symbolizer", default=r"C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin\llvm-symbolizer.exe")
    a = p.parse_args()
    print(pinguard.ensure(), flush=True)
    os.makedirs(a.out, exist_ok=True)
    hist: collections.Counter = collections.Counter()
    stats = {"exe": a.exe, "net": a.net, "depth": a.depth, "quantum_cycles": a.quantum}
    for i in range(a.repeat):
        profile_once(a, i, hist, stats)
    total = sum(hist.values())
    with open(os.path.join(a.out, "rva_hist.tsv"), "w", encoding="utf-8", newline="\n") as f:
        for rva, n in sorted(hist.items()):
            f.write(f"{rva:#x}\t{n}\n")
    sym = symbolize(a, sorted(hist))
    inner: collections.Counter = collections.Counter()
    outer: collections.Counter = collections.Counter()
    lines: collections.Counter = collections.Counter()
    unresolved = 0
    for rva, n in hist.items():
        frames = sym.get(rva) or []
        if not frames or frames[0][0] in ("??", ""):
            unresolved += n
            inner["?? (unresolved)"] += n
            outer["?? (unresolved)"] += n
            continue
        inner[frames[0][0]] += n
        outer[frames[-1][0]] += n
        lines[f"{frames[0][1]}:{frames[0][2]} [{frames[0][0][:60]}]"] += n
    stats.update({"samples_in_image": total, "unresolved": unresolved, "distinct_rvas": len(hist)})
    with open(os.path.join(a.out, "stats.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, indent=1)
    for name, table in (("self_by_source_function.tsv", inner), ("self_by_emitted_function.tsv", outer),
                        ("self_by_line.tsv", lines)):
        with open(os.path.join(a.out, name), "w", encoding="utf-8", newline="\n") as f:
            f.write("share_pct\tsamples\tname\n")
            for key, n in table.most_common():
                f.write(f"{100.0 * n / max(total, 1):.2f}\t{n}\t{key}\n")
    print(f"TOTAL {total} samples in the image, {unresolved} unresolved, {len(hist)} distinct addresses", flush=True)
    for key, n in inner.most_common(25):
        print(f"{100.0 * n / max(total, 1):6.2f} %  {n:6d}  {key[:150]}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
