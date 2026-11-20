#!/usr/bin/env python3
"""Record the uci option list and check IdeaS27 defaults."""
import hashlib
import subprocess
import sys

exe, raw_path, meta_path = sys.argv[1:]
digest = hashlib.sha256(open(exe, "rb").read()).hexdigest()
proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
out, _ = proc.communicate("uci\nquit\n", timeout=30)
open(raw_path, "w").write(out)
name = ""
for line in out.splitlines():
    if line.startswith("id name "):
        name = line[len("id name "):]
with open(meta_path, "w") as handle:
    handle.write("exe " + exe + "\n")
    handle.write("sha256 " + digest + "\n")
    handle.write("id_name " + name + "\n")
    handle.write("options none\n")
need = [
    "option name IdeaS27 type check default false",
    "option name IdeaS27_DeadZone type spin default 128 min 0 max 16384",
]
for item in need:
    print(("OK" if item in out else "MISSING"), item)
