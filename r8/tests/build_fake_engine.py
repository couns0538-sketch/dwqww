"""R8 v5: build the fault-injection test engine r8/tests/fake_engine.cpp (Forge Board for the move rules).
  python -I -B r8/tools/run_pinned.py --mask 0x000F -- r8/tests/build_fake_engine.py <repo_root> <out.exe>"""
import hashlib
import os
import subprocess
import sys

root, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
gxx = r"C:\msys64\ucrt64\bin\g++.exe"
env = dict(os.environ)
env["PATH"] = r"C:\msys64\ucrt64\bin;" + env.get("PATH", "")
cmd = [gxx, "-std=c++20", "-O2", "-DNDEBUG", "-march=znver5", "-static", "-Wall", "-Wextra",
       "-I" + os.path.join(root, "include"), os.path.join(root, "r8", "tests", "fake_engine.cpp"),
       os.path.join(root, "src", "board.cpp"), os.path.join(root, "src", "bitboard.cpp"), "-o", out]
rc = subprocess.call(cmd, env=env)
if rc != 0:
    sys.exit(rc)
print(f"built {out} sha256 {hashlib.sha256(open(out, 'rb').read()).hexdigest()}")
