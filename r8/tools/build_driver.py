"""R8: build r8/forge_selfplay_fast.cpp with Forge's Board (src/board.cpp, src/bitboard.cpp of this tree).
Run under run_pinned.py (CPU mask + BelowNormal are inherited by g++):
  python -I -B run_pinned.py --mask 0x000F -- r8/tools/build_driver.py <repo_root> <out.exe>
v5: links psapi (RSS report) and puts r8/tools/dedup_against_db.py next to the exe (the driver's default
--post-script); an existing copy there is never replaced (a different one is reported)."""
import hashlib
import os
import shutil
import subprocess
import sys

root, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
gxx = r"C:\msys64\ucrt64\bin\g++.exe"
env = dict(os.environ)
env["PATH"] = r"C:\msys64\ucrt64\bin;" + env.get("PATH", "")
cmd = [gxx, "-std=c++20", "-O2", "-DNDEBUG", "-march=znver5", "-static", "-pthread", "-Wall", "-Wextra",
       "-I" + os.path.join(root, "include"), os.path.join(root, "r8", "forge_selfplay_fast.cpp"),
       os.path.join(root, "src", "board.cpp"), os.path.join(root, "src", "bitboard.cpp"), "-lpsapi", "-o", out]
rc = subprocess.call(cmd, env=env)
if rc != 0:
    sys.exit(rc)
print(f"built {out} sha256 {hashlib.sha256(open(out, 'rb').read()).hexdigest()}")
tool = os.path.join(root, "r8", "tools", "dedup_against_db.py")
dest = os.path.join(os.path.dirname(out), "dedup_against_db.py")
if not os.path.exists(dest):
    shutil.copyfile(tool, dest)
    print(f"copied {tool} -> {dest}")
elif open(dest, "rb").read() != open(tool, "rb").read():
    print(f"WARNING: {dest} differs from {tool} (not replaced): the driver's default --post-script is the old copy")
else:
    print(f"{dest} is up to date")
