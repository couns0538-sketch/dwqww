"""P9 + P7: the cliff at fine resolution, and the MultiPV-2 cliff.

P9  Hash 16, MPV 1, caps 57/58/59/60 -- resolves whether the prior boundary table's
    "59 fails" is right, or whether my 2 MB bisect's "58 fails" was the coarse reading.
P7  Cliff bisect at MultiPV 1 vs MultiPV 2, Hash 64 and Hash 256.

Why the protocol has to change for MultiPV 2: `search.cpp:2384-2386` builds the alternate
table only `if (multipv > 1 && is_main())`, and it is a `unique_ptr` inside the search frame.
So the second table is resident only WHILE a search runs -- an idle process at Hash 256 +
MultiPV 2 has one table, not two. The cliff therefore has to be probed by running searches
under the cap, which is what this does.

`VmHWM` is read after a successful run as well as RSS, because VmHWM is the kernel's exact
peak high-water mark and cannot be missed by sampling: it is what says the two tables were
both resident at once rather than sequentially.
"""
import json
import subprocess
import sys

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine, EngineError  # noqa: E402

FENS = [l.strip() for l in open("/tmp/soak/positions_R.fens") if l.strip()][10:16]
REF = "/tmp/soak/build/forge"


def one(cap_mb, hash_mb, multipv, depth=10):
    """One fresh engine under `ulimit -v cap_mb`; returns searches completed + peak stats."""
    if cap_mb:
        cmd = ["bash", "-c", 'ulimit -v %d; exec "%s"' % (cap_mb * 1024, REF)]
    else:
        cmd = [REF]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, bufsize=0)
    e = Engine.__new__(Engine)
    e.exe = REF
    e.proc = p
    e.buf = b""
    e.sent = []
    e.id_name = None
    ok = 0
    vm = None
    try:
        e._handshake({"Hash": hash_mb, "Threads": 1, "MultiPV": multipv})
        for f in FENS:
            e.position_fen(f)
            e.go("go depth %d" % depth, deadline_s=300)
            ok += 1
        vm = e.vm_kb()
    except EngineError:
        pass
    except (BrokenPipeError, OSError):
        pass
    rc = p.poll()
    if rc is None:
        try:
            p.stdin.write(b"quit\n")
            p.stdin.flush()
            p.wait(timeout=10)
        except Exception:
            p.kill()
    err = b""
    try:
        err = p.stderr.read() or b""
    except Exception:
        pass
    return {"cap_mb": cap_mb, "hash": hash_mb, "multipv": multipv,
            "completed": ok, "n_expected": len(FENS),
            "rc": p.returncode, "signal": -p.returncode if p.returncode and p.returncode < 0 else None,
            "vm": vm, "stderr_tail": err.decode("utf-8", "replace")[-160:]}


def bisect(hash_mb, multipv, lo, hi, step=2):
    """Lowest cap that completes every search, and the highest that dies."""
    good = None
    bad = None
    for cap in range(lo, hi + 1, step):
        r = one(cap, hash_mb, multipv)
        if r["completed"] == r["n_expected"]:
            good = r
            break
        bad = r
    return good, bad


out = {"P9": [], "P7": []}

# ---- P9: fine resolution at Hash 16, MPV 1 ----
print("== P9  Hash 16, MPV 1, single-MB caps ==")
for cap in (57, 58, 59, 60):
    r = one(cap, 16, 1)
    out["P9"].append(r)
    print(json.dumps({k: r[k] for k in ("cap_mb", "completed", "rc", "signal")}))

# ---- P7: the cliff vs MultiPV ----
print("\n== P7  cliff, MPV 1 vs MPV 2 ==")
for hash_mb, multipv, lo, hi in ((64, 1, 96, 120), (64, 2, 130, 200),
                                 (256, 1, 280, 310), (256, 2, 480, 620)):
    good, bad = bisect(hash_mb, multipv, lo, hi)
    rec = {"hash": hash_mb, "multipv": multipv,
           "lowest_complete_mb": good["cap_mb"] if good else None,
           "highest_dead_mb": bad["cap_mb"] if bad else None,
           "vmhwm_at_complete": good["vm"]["VmHWM"] if good else None,
           "rss_at_complete": good["vm"]["VmRSS"] if good else None,
           "cliff_minus_table": (good["cap_mb"] - hash_mb * multipv) if good else None,
           "good_stderr": good["stderr_tail"] if good else None,
           "bad_stderr": bad["stderr_tail"] if bad else None}
    out["P7"].append(rec)
    print(json.dumps({k: v for k, v in rec.items()
                      if k not in ("good_stderr", "bad_stderr")}))

json.dump(out, open("/tmp/soak/ev/soak7_cliff_mpv.json", "w"), indent=1)
print("\nwrote /tmp/soak/ev/soak7_cliff_mpv.json")
