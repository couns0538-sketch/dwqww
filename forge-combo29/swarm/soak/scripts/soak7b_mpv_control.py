"""P7b: why the MPV-2 cliff is not 2*Hash + 44, with the control that separates the models.

Measured (soak7):
  Hash  64 MPV1 cliff 108, MPV2 cliff 152   (predicted 168-176  -> FAILED low)
  Hash 256 MPV1 cliff 300, MPV2 cliff 598   (predicted 548-564  -> FAILED high)

A single linear model cannot produce both, so the question is what the cliff actually tracks.
Two candidate models, and this file tests the one that decides between them:

  M1 "the cliff is touched memory + a fixed virtual overhead": then VmHWM at the successful
     cap should be close to the cap at every cell, and the residual should be constant.
  M2 "the cliff is a VIRTUAL-memory threshold that the allocator's arena reservation
     straddles": then the *untouched* part of VmSize (VmSize - RSS) should switch between two
     regimes, as it did in probe_cliff.py (64 MB reservation at Hash 32 succeeded above 170 MB
     and failed below).

The decisive control is MultiPV 4 against MultiPV 2: `search.cpp:2502` clears ONE alternate
table per secondary line rather than allocating one per line, so if the alternate table is the
only extra structure, **MPV 4 must have the SAME cliff as MPV 2**. If MPV 4's cliff is higher,
something allocates per line and the §3 cost model needs re-reading.

Every cell also records VmSize/VmPeak/VmHWM/VmRSS at the highest cap that completed, so the
untouched-virtual component is visible instead of inferred.
"""
import json
import subprocess
import sys

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine, EngineError  # noqa: E402

FENS = [l.strip() for l in open("/tmp/soak/positions_R.fens") if l.strip()][10:16]
EXE = "/tmp/soak/build/forge"


def one(cap_mb, hash_mb, multipv, depth=10):
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
    ok = 0
    keys = []
    vm = None
    try:
        e._handshake({"Hash": hash_mb, "Threads": 1, "MultiPV": multipv})
        for f in FENS:
            e.position_fen(f)
            r = e.go("go depth %d" % depth, deadline_s=300)
            import re
            m = re.search(r"score (cp|mate) (-?\d+)", r["last"] or "")
            n = re.search(r"\bnodes (\d+)", r["last"] or "")
            keys.append((r["bestmove"], m.group(0) if m else None,
                         int(n.group(1)) if n else None))
            ok += 1
        vm = e.vm_kb()
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
    return {"cap_mb": cap_mb, "hash": hash_mb, "multipv": multipv, "completed": ok,
            "n_expected": len(FENS), "rc": p.returncode,
            "signal": -p.returncode if p.returncode and p.returncode < 0 else None,
            "vm": vm, "keys": keys}


def bisect(hash_mb, multipv, lo, hi, step=2):
    good = bad = None
    for cap in range(lo, hi + 1, step):
        r = one(cap, hash_mb, multipv)
        if r["completed"] == r["n_expected"]:
            good = r
            return good, bad
        bad = r
    return None, bad


out = []
print("== P7b  MPV 2 vs MPV 4 (must be equal if one alternate table is reused) ==")
for hash_mb, multipv, lo, hi in ((64, 2, 144, 200), (64, 4, 144, 200),
                                 (256, 2, 560, 620), (256, 4, 560, 620),
                                 (256, 3, 560, 620)):
    good, bad = bisect(hash_mb, multipv, lo, hi)
    rec = {"hash": hash_mb, "multipv": multipv,
           "lowest_complete_mb": good["cap_mb"] if good else None,
           "highest_dead_mb": bad["cap_mb"] if bad else None,
           "vm": good["vm"] if good else None,
           "keys": good["keys"] if good else None}
    if rec["vm"]:
        rec["untouched_virtual_mb"] = round(
            (rec["vm"]["VmSize"] - rec["vm"]["VmRSS"]) / 1024.0, 1)
        rec["peak_over_cap_mb"] = round(
            (good["cap_mb"] * 1024 - rec["vm"]["VmHWM"]) / 1024.0, 1)
    print(json.dumps({k: v for k, v in rec.items() if k != "keys"}))
    out.append(rec)

# reference answer key at MultiPV 2 / Hash 64, unconstrained, to check the capped runs agree
ref = one(0, 64, 2)
print("\n== answer stability at the MPV-2 cliff ==")
for r in out:
    if r["hash"] != 64 or not r["keys"]:
        continue
    same = (r["keys"] == ref["keys"])
    diff = sum(1 for a, b in zip(r["keys"], ref["keys"]) if a != b)
    print("Hash 64 MPV %d at cap %d MB: %d of %d rows differ from the uncapped run"
          % (r["multipv"], r["lowest_complete_mb"], diff, len(ref["keys"])))
    r["diff_vs_uncapped"] = diff

json.dump(out, open("/tmp/soak/ev/soak7b_mpv_control.json", "w"), indent=1)
