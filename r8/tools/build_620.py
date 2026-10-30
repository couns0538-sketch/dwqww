"""R8: build a Forge 6.2.0 tree like the PC lock recipe (MSYS2 ucrt64 g++, -O3 -DNDEBUG -ffp-contract=off
-fno-fast-math -march=znver5, static), JOBS units in parallel. Run it under run_pinned.py so the compiler inherits
the CPU mask and BelowNormal priority:
  python -I -B run_pinned.py --mask 0x00FF -- build_620.py <src_dir> <out.exe> [--jobs 2] [--units "a b"] [-- extra flags]
Prints the exe sha256 and the FMA instruction count (must be 0 for the lock recipe)."""
import hashlib
import os
import subprocess
import sys

args = sys.argv[1:]
src, out = os.path.abspath(args[0]), os.path.abspath(args[1])
jobs = int(args[args.index("--jobs") + 1]) if "--jobs" in args else 2
units = (args[args.index("--units") + 1].split() if "--units" in args
         else ["bitboard", "board", "eval", "eval_params", "search", "uci"])
extra = args[args.index("--") + 1:] if "--" in args else []
gxx = r"C:\msys64\ucrt64\bin\g++.exe"
objdump = r"C:\msys64\ucrt64\bin\objdump.exe"
env = dict(os.environ)
env["PATH"] = r"C:\msys64\ucrt64\bin;" + env.get("PATH", "")
flags = ["-std=c++20", "-O3", "-DNDEBUG", "-ffp-contract=off", "-fno-fast-math", "-march=znver5", "-pthread"] + extra
objdir = out[:-4] + ".obj"
os.makedirs(objdir, exist_ok=True)
pending = list(units)
running = []
failed = False
while pending or running:
    while pending and len(running) < jobs:
        u = pending.pop(0)
        cmd = [gxx] + flags + ["-I" + os.path.join(src, "include"), "-c", os.path.join(src, "src", u + ".cpp"),
                               "-o", os.path.join(objdir, u + ".o")]
        running.append((u, subprocess.Popen(cmd, env=env)))
    u, p = running.pop(0)
    if p.wait() != 0:
        print(f"compile failed: {u}", flush=True)
        failed = True
if failed:
    sys.exit(1)
link = [gxx] + flags + ["-static"] + [os.path.join(objdir, u + ".o") for u in units] + ["-o", out]
if subprocess.call(link, env=env) != 0:
    sys.exit("link failed")
digest = hashlib.sha256(open(out, "rb").read()).hexdigest()
dis = subprocess.run([objdump, "-d", out], capture_output=True, text=True, env=env).stdout
fma = sum(1 for line in dis.splitlines() if any(t in line for t in ("vfmadd", "vfmsub", "vfnmadd", "vfnmsub")))
print(f"built {out} sha256 {digest}")
print("flags: g++ " + " ".join(flags) + " -static")
print(f"FMA (vfmadd/vfmsub/vfnmadd) count: {fma}")
