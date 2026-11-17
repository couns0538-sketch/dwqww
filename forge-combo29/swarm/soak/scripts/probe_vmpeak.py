"""Where does VmPeak come from at Hash 32?

The ulimit sweep survived at an 80 MB cap while a Hash-32 process reports VmPeak ~180 MB,
so the peak and the working set are different objects. Poll VmSize/VmPeak/RSS through one
process's life and print the sample where VmSize jumps, so the allocation that caused it can
be attributed to the command that was running.
"""
import json
import sys
import threading
import time

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine  # noqa: E402

fens = [l.strip() for l in open("/tmp/soak/positions_R.fens") if l.strip()][10:20]

eng = Engine("/tmp/soak/build/forge", options={"Hash": 32, "Threads": 1})
samples = []
cur = {"cmd": "handshake"}


def poll():
    while True:
        try:
            vm = eng.vm_kb()
            samples.append({"t": round(time.monotonic(), 3), "cmd": cur["cmd"], **vm})
        except Exception:
            return
        time.sleep(0.002)


threading.Thread(target=poll, daemon=True).start()
time.sleep(0.05)
for i, fen in enumerate(fens):
    cur["cmd"] = "position %d" % i
    eng.position_fen(fen)
    cur["cmd"] = "go depth 12 #%d" % i
    eng.go("go depth 12")
cur["cmd"] = "setoption Hash 64"
eng.setoption("Hash", 64)
cur["cmd"] = "go depth 12 after resize"
eng.position_fen(fens[0])
eng.go("go depth 12")
cur["cmd"] = "quit"
eng.quit()

prev = None
print("cmd                      VmSize  VmPeak  VmRSS")
for s in samples:
    if prev is None or s["VmSize"] != prev["VmSize"] or s["VmPeak"] != prev["VmPeak"]:
        print("%-24s %7d %7d %7d" % (s["cmd"], s["VmSize"], s["VmPeak"], s["VmRSS"]))
        prev = s
peak = max(samples, key=lambda s: s["VmPeak"])
print("\nmax VmPeak %d at cmd=%s" % (peak["VmPeak"], peak["cmd"]))
