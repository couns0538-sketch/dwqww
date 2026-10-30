"""R11: build r11_pos2binpack.exe against the R6 clone's data-loader headers (GPL-3.0 tool tree).

The exe name carries the first 12 hex digits of the source sha256, so a rebuild never overwrites an older tool:
  <out_dir>/r11_pos2binpack_<srcsha12>.exe  (+ .json with compiler, flags and exe sha256)
Usage: build_r11_tools.py [--clone F:/opus_scratch/r6/nnue-pytorch-amd] [--out-dir D:/grok-pc-data/r11_nnue/bin]
Prints the exe path on the last line. Runs the compiler at BelowNormal priority with one job.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MINGW = "C:/msys64/ucrt64/bin"
FLAGS = ["-std=c++20", "-O2", "-DNDEBUG", "-march=x86-64-v3", "-DHAS_BMI2", "-static", "-pthread"]


def sha256(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clone", default="F:/opus_scratch/r6/nnue-pytorch-amd")
    ap.add_argument("--out-dir", default="D:/grok-pc-data/r11_nnue/bin")
    ap.add_argument("--affinity", default="0x700", help="at most 3 CPUs (CR fix 2); default CPUs 8-10")
    a = ap.parse_args()
    if sys.platform == "win32":
        # CR fix 2: Idle (0x40) + background mode, at most 3 cores; the compiler inherits Idle and the mask
        from ctypes import wintypes
        mask = int(a.affinity, 0)
        if bin(mask).count("1") > 3:
            print("FAIL --affinity must select at most 3 CPUs")
            return 2
        k32 = ctypes.windll.kernel32
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        k32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
        h = k32.GetCurrentProcess()
        k32.SetPriorityClass(h, 0x00100000)  # background mode first: it resets the class to Normal
        k32.SetPriorityClass(h, 0x00000040)  # then Idle (inherited by the compiler with the very low I/O priority)
        k32.SetProcessAffinityMask(h, mask)
    src = os.path.join(HERE, "r11_pos2binpack.cpp")
    inc = os.path.join(a.clone, "data_loader", "cpp")
    if not os.path.isfile(os.path.join(inc, "lib", "binpack.h")):
        print(f"FAIL no lib/binpack.h under {inc}")
        return 2
    # the source text with normalised line endings decides the name (CRLF checkouts give the same name)
    with open(src, "rb") as f:
        text = f.read().replace(b"\r\n", b"\n")
    src_sha = hashlib.sha256(text).hexdigest()
    os.makedirs(a.out_dir, exist_ok=True)
    exe = os.path.join(a.out_dir, f"r11_pos2binpack_{src_sha[:12]}.exe")
    meta_path = exe[:-4] + ".json"
    if os.path.isfile(exe) and os.path.isfile(meta_path):
        print(f"exists: {exe}")
        print(exe)
        return 0
    if os.path.exists(exe):
        print(f"FAIL {exe} exists without its .json (incomplete earlier build?); not overwriting")
        return 2
    env = dict(os.environ)
    env["PATH"] = MINGW + os.pathsep + env.get("PATH", "")
    gxx = os.path.join(MINGW, "g++.exe")
    tmp = exe + ".part.exe"
    if os.path.exists(tmp):
        print(f"FAIL leftover {tmp}; not overwriting")
        return 2
    cmd = [gxx] + FLAGS + ["-I", inc, src, "-o", tmp]
    print("build:", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    if r.returncode != 0:
        print(f"FAIL compiler exit {r.returncode}")
        return 1
    os.replace(tmp, exe)
    ver = subprocess.run([gxx, "--version"], env=env, capture_output=True, text=True).stdout.splitlines()[0]
    clone_head = subprocess.run(["git", "-C", a.clone, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    meta = {"exe": exe, "exe_sha256": sha256(exe), "source": src, "source_sha256_lf": src_sha, "compiler": ver,
            "flags": FLAGS, "include": inc, "clone_head": clone_head, "warnings": r.stderr.count("warning")}
    with open(meta_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=1)
    print(json.dumps(meta))
    print(exe)
    return 0


if __name__ == "__main__":
    sys.exit(main())
