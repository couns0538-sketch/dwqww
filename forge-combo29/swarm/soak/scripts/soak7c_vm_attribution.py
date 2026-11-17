"""P7c: what the cliff actually tracks, per (Hash, MultiPV) cell.

The cliff numbers (soak7) fail a single linear model:
  Hash  64 MPV1 108  MPV2 152     (2*Hash+44 = 172 predicted)
  Hash 256 MPV1 300  MPV2 598     (2*Hash+44 = 556 predicted)
so this measures, in each cell, the quantities a virtual-memory cap could be tracking:

  VmHWM   kernel's exact peak RSS      -> is the second table really resident?
  VmSize  address space at rest        -> table + arena + code
  VmPeak  address space high-water     -> what `ulimit -v` actually refuses to exceed

And it takes each cell twice: UNCAPPED (to see what the allocator does when space is free)
and AT the lowest cap that completes (to see what it does when space is scarce). The
difference between those two is the whole explanation for a cliff that is not a clean
function of table size.

Answer keys are compared only within one (Hash, MultiPV) configuration -- the first version of
this comparison used an MPV-2 reference for MPV-4 runs and reported 6 of 6 rows differing,
which was the harness comparing two different searches, not an engine effect.
"""
import json
import re
import subprocess
import sys

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine, EngineError  # noqa: E402

FENS = [l.strip() for l in open("/tmp/soak/positions_R.fens") if l.strip()][10:16]
EXE = "/tmp/soak/build/forge"
CAPS = {(64, 1): 108, (64, 2): 152, (64, 4): 152,
        (256, 1): 300, (256, 2): 598, (256, 4): 598}


def key_of(last, best):
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    n = re.search(r"\bnodes (\d+)", last or "")
    return (best, m.group(0) if m else None, int(n.group(1)) if n else None)


def run(hash_mb, multipv, cap_mb=None, depth=10):
    if cap_mb:
        cmd = ["bash", "-c", 'ulimit -v %d; exec "%s"' % (cap_mb * 1024, EXE)]
    else:
        cmd = [EXE]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, bufsize=0)
    e = Engine.__new__(Engine)
    e.exe = EXE
    e.proc = p
    e.buf = b""
    e.sent = []
    e.id_name = None
    keys = []
    vm = None
    try:
        e._handshake({"Hash": hash_mb, "Threads": 1, "MultiPV": multipv})
        vm = {"after_handshake": e.vm_kb()}
        for f in FENS:
            e.position_fen(f)
            r = e.go("go depth %d" % depth, deadline_s=300)
            keys.append(key_of(r["last"], r["bestmove"]))
        vm["after_search"] = e.vm_kb()
    except (EngineError, BrokenPipeError, OSError):
        pass
    rc = p.poll()
    if rc is None:
        try:
            p.stdin.write(b"quit\n")
            p.stdin.flush()
            p.wait(timeout=10)
        except Exception:
            p.kill()
    return {"hash": hash_mb, "multipv": multipv, "cap_mb": cap_mb, "keys": keys,
            "vm": vm, "rc": p.returncode}


rows = []
print("%4s %4s %6s %10s %10s %10s %10s %8s" %
      ("Hash", "MPV", "cap", "VmHWM_MB", "VmSize_MB", "VmPeak_MB", "VmRSS_MB", "untch"))
for (h, mpv), cap in CAPS.items():
    for label, c in (("uncapped", None), ("at_cliff", cap)):
        r = run(h, mpv, c)
        if not r["vm"] or "after_search" not in r["vm"]:
            print("%4d %4d %6s  DIED at cap %s" % (h, mpv, label, c))
            rows.append({"hash": h, "multipv": mpv, "cap_mb": c, "died": True})
            continue
        vm = r["vm"]["after_search"]
        rec = {"hash": h, "multipv": mpv, "cap_mb": c, "died": False,
               "vmhwm_mb": round(vm["VmHWM"] / 1024.0, 1),
               "vmsize_mb": round(vm["VmSize"] / 1024.0, 1),
               "vmpeak_mb": round(vm["VmPeak"] / 1024.0, 1),
               "rss_mb": round(vm["VmRSS"] / 1024.0, 1),
               "untouched_mb": round((vm["VmSize"] - vm["VmRSS"]) / 1024.0, 1),
               "keys": r["keys"]}
        rows.append(rec)
        print("%4d %4d %6s %10.1f %10.1f %10.1f %10.1f %8.1f"
              % (h, mpv, label, rec["vmhwm_mb"], rec["vmsize_mb"], rec["vmpeak_mb"],
                 rec["rss_mb"], rec["untouched_mb"]))

# answer stability, WITHIN each configuration
print("\nanswer stability: capped vs uncapped, same (Hash, MultiPV)")
for (h, mpv) in CAPS:
    ref = [r for r in rows if r["hash"] == h and r["multipv"] == mpv
           and r["cap_mb"] is None and not r["died"]]
    cap = [r for r in rows if r["hash"] == h and r["multipv"] == mpv
           and r["cap_mb"] is not None and not r["died"]]
    if ref and cap:
        d = sum(1 for a, b in zip(cap[0]["keys"], ref[0]["keys"]) if a != b)
        print("  Hash %3d MPV %d: %d of %d rows differ"
              % (h, mpv, d, len(ref[0]["keys"])))
        cap[0]["diff_vs_uncapped"] = d

json.dump(rows, open("/tmp/soak/ev/soak7c_vm.json", "w"), indent=1)
