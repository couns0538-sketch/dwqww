"""R10: build a test tool against the engine core with the box recipe's flags (the engine's sources minus uci.cpp).
usage: python -I -B run_pinned.py --mask 0x0FF0 -- build_tool.py <repo root> <tool.cpp> <out.exe> [extra g++ flags]"""
import hashlib
import os
import subprocess
import sys

root, tool, out, extra = os.path.abspath(sys.argv[1]), sys.argv[2], os.path.abspath(sys.argv[3]), sys.argv[4:]
env = dict(os.environ)
env["PATH"] = r"C:\msys64\ucrt64\bin;" + env.get("PATH", "")
srcs = [os.path.join(root, "src", s) for s in ("bitboard.cpp", "board.cpp", "book.cpp", "eval.cpp", "eval_params.cpp",
                                                "nnue.cpp", "nnue_halfka.cpp", "search.cpp")]
cmd = [r"C:\msys64\ucrt64\bin\g++.exe", "-std=c++20", "-O3", "-DNDEBUG", "-DFORGE_NNUE_HIDDEN=256", "-ffp-contract=off",
       "-fno-fast-math", "-march=znver5", "-static", "-pthread", "-Wall", "-Wextra", "-I" + os.path.join(root, "include")]
cmd += extra + [tool] + srcs + ["-o", out]
rc = subprocess.call(cmd, env=env)
if rc:
    sys.exit(rc)
print(f"built {out} sha256 {hashlib.sha256(open(out, 'rb').read()).hexdigest()}")
