"""R8 v5: run a command, sample the working set of it AND its child processes every 0.25 s (psutil; the venv's
python.exe is a launcher that runs the real interpreter as a child), print the peak of the tree and the wall time.
usage: python -I -B peak_rss.py <cmd> [args...]   (the command's own output passes through)"""
import subprocess
import sys
import time

import psutil

t0 = time.time()
p = subprocess.Popen(sys.argv[1:])
proc = psutil.Process(p.pid)
peak_ws = peak_private = 0
while p.poll() is None:
    try:
        tree = [proc] + proc.children(recursive=True)
        ws = priv = 0
        for q in tree:
            try:
                m = q.memory_info()
                ws += m.rss
                priv += getattr(m, "private", 0)
            except psutil.Error:
                pass
        peak_ws, peak_private = max(peak_ws, ws), max(peak_private, priv)
    except psutil.Error:
        pass
    time.sleep(0.25)
print(f"peak_rss: exit {p.returncode}, {time.time() - t0:.1f} s, peak working set {peak_ws / 2**20:.1f} MB, "
      f"peak private {peak_private / 2**20:.1f} MB", flush=True)
sys.exit(p.returncode)
