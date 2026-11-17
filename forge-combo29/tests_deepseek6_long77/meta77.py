#!/usr/bin/env python3
"""meta77.py -- write the .meta record for an exe a runner starts (file 17 (a)):
path, sha256, the engine's `id name`, the sanitizer symbol counts, and the build line.
Usage: meta77.py <exe> <outfile> [cmake-line]"""
import hashlib
import re
import subprocess
import sys

exe, out = sys.argv[1], sys.argv[2]
cmake = sys.argv[3] if len(sys.argv) > 3 else ""
sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
p.stdin.write("uci\n"); p.stdin.flush()
idname = ""
for _ in range(100):
    l = p.stdout.readline()
    if not l or l.startswith("uciok"): break
    if l.startswith("id name "): idname = l.strip()
p.stdin.write("quit\n"); p.stdin.flush(); p.terminate()
asan = subprocess.run(["nm", "-C", exe], capture_output=True, text=True).stdout
n_asan = len(re.findall(r"__asan_", asan))
n_ubsan = len(re.findall(r"__ubsan_", asan))
with open(out, "w") as f:
    f.write(f"path {exe}\nsha256 {sha}\n{idname}\n"
            f"asan_symbols {n_asan}\nubsan_symbols {n_ubsan}\n"
            f"cmake {cmake}\n")
print(open(out).read())
