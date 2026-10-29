"""R6 J3: run one short nnue-pytorch training and measure positions/s per epoch.

Usage: python bench_train.py NAME [VAR=VALUE ...] -- <train.py args>
Runs train.py (cwd = the R6 clone) as a child, timestamps every epoch-end line
("Epoch N (Train): [train_loss_epoch=...") and reports positions/s per epoch
= epoch_size / time between consecutive epoch ends (epoch 0 = warm-up, compile).
Output: F:/opus_scratch/r6/bench/NAME/{train.log, result.json}
"""

import json
import os
import re
import subprocess
import sys
import time

CLONE = "F:/opus_scratch/r6/nnue-pytorch-amd"
OUT_ROOT = "F:/opus_scratch/r6/bench"


def free_ram_gb() -> float:
    import ctypes

    class MEMSTAT(ctypes.Structure):
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

    st = MEMSTAT()
    st.dwLength = ctypes.sizeof(MEMSTAT)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
    return st.ullAvailPhys / 2**30


def ram_gate(min_gb=6.0, wait_s=120):
    """PC rule: no torch work below 6 GB free RAM. Wait a little, else give up."""
    t0 = time.time()
    while True:
        f = free_ram_gb()
        if f >= min_gb:
            return f
        if time.time() - t0 > wait_s:
            print(f"RAM GATE: only {f:.1f} GB free after {wait_s}s, not starting", flush=True)
            sys.exit(3)
        time.sleep(5)


def main():
    name = sys.argv[1]
    print(f"{name}: free RAM {ram_gate():.1f} GB", flush=True)
    rest = sys.argv[2:]
    split = rest.index("--")
    env_kv, train_args = rest[:split], rest[split + 1 :]
    env = dict(os.environ)
    for kv in env_kv:
        k, v = kv.split("=", 1)
        env[k] = v
    out_dir = os.path.join(OUT_ROOT, name)
    os.makedirs(out_dir, exist_ok=True)
    epoch_size = int(train_args[train_args.index("--epoch-size") + 1])
    cmd = [sys.executable, "-B", "train.py", *train_args, "--default-root-dir", out_dir]
    t_start = time.perf_counter()
    marks = []  # (epoch, t)
    rates = []
    pat = re.compile(r"Epoch\s+(\d+)\s+\(Train\):\s+\[train_loss_epoch=([0-9.]+)")
    with open(os.path.join(out_dir, "train.log"), "w", encoding="utf-8", newline="\n") as log:
        log.write("CMD " + " ".join(cmd) + "\n")
        log.write("ENV " + " ".join(env_kv) + "\n")
        p = subprocess.Popen(
            cmd,
            cwd=CLONE,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        buf = ""
        while True:
            ch = p.stdout.read(1)
            if not ch:
                break
            if ch in "\r\n":
                line = buf
                buf = ""
                if not line.strip():
                    continue
                now = time.perf_counter() - t_start
                log.write(f"[{now:8.2f}] {line}\n")
                m = pat.search(line)
                if m:
                    marks.append((int(m.group(1)), now, float(m.group(2))))
                    if len(marks) >= 2:
                        dt = marks[-1][1] - marks[-2][1]
                        rates.append(epoch_size / dt)
                        print(f"{name}: epoch {marks[-1][0]} {epoch_size / dt:,.0f} pos/s "
                              f"loss {marks[-1][2]:.5f}", flush=True)
            else:
                buf += ch
        rc = p.wait()
    total = time.perf_counter() - t_start
    steady = rates[1:] if len(rates) > 2 else rates
    res = {
        "name": name,
        "env": env_kv,
        "args": train_args,
        "exit_code": rc,
        "wall_s": round(total, 2),
        "epoch_marks": marks,
        "pos_per_s_epochs": [round(r) for r in rates],
        "pos_per_s_median_steady": round(sorted(steady)[len(steady) // 2]) if steady else None,
    }
    with open(os.path.join(out_dir, "result.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: res[k] for k in ("name", "exit_code", "wall_s", "pos_per_s_epochs",
                                         "pos_per_s_median_steady")}), flush=True)


if __name__ == "__main__":
    main()
