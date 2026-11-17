"""Experiment H - the transient of a same-size resize, measured so it cannot be missed.

`TranspositionTable::resize` (search.cpp:362-370) is:

    auto new_clusters = std::make_unique<TTCluster[]>(new_count);   // ALLOC
    clusters_ = std::move(new_clusters);                           // old freed HERE
    cluster_count_ = new_count;
    generation_ = 0; ++epoch_;

so the new block exists while the old one is still owned.  For a same-size
resize that is 2x the table alive at one instant.

Measured naively, that transient is easy to MISS, and miss for a reason worth
naming: `new TTCluster[n]` over a zero-initialised type can be served by
calloc, and a large calloc'd block is backed by zero pages that are only made
resident on first write.  So a freshly allocated table has near-zero RSS until
it is touched, and a page-fault-driven sampler sees nothing.

Three instruments, in increasing order of resolution:

  1. VmSize before/after  - virtual size must step by the table size.
  2. VmHWM                - the kernel's monotonic peak, which cannot miss a
                            resident peak that actually happened.
  3. a dedicated sampler  - VmRSS/VmSize at ~5 kHz across the resize.

And one direct, non-inferential instrument: /proc/<pid>/smaps_rollup is read
BEFORE and AFTER, and the test is repeated with the OLD table FULLY TOUCHED
(a long search that fills it) versus EMPTY.  If the transient is real and
page-backed, the FULL old table is the case where HWM must jump by ~the table
size; if HWM jumps equally in both cases, the peak is not the table.

Controls:
  * 32 -> 64 must step VmSize by 32 MB (a resize that does not move memory is
    not being measured at all);
  * 32 -> 32 must NOT step VmSize after the resize completes, so a VmSize step
    is diagnostic of a size CHANGE and not of resizing per se;
  * repeated 32 -> 32 must not ratchet HWM upward once per round, which is what
    a leak would look like.
"""

import argparse
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import Engine, ENGINE, proc_mem

FILL_POS = "position fen r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8"


class Sampler(threading.Thread):
    """Tight-loop sampler. Records every (t, VmRSS, VmHWM, VmSize)."""

    def __init__(self, pid):
        super().__init__(daemon=True)
        self.pid = pid
        self.rows = []
        self.stop_flag = threading.Event()

    def run(self):
        path = "/proc/%d/status" % self.pid
        while not self.stop_flag.is_set():
            try:
                with open(path) as fh:
                    rss = hwm = vsz = None
                    for line in fh:
                        if line.startswith("VmRSS"):
                            rss = int(line.split()[1])
                        elif line.startswith("VmHWM"):
                            hwm = int(line.split()[1])
                        elif line.startswith("VmSize"):
                            vsz = int(line.split()[1])
                    self.rows.append((time.perf_counter(), rss, hwm, vsz))
            except OSError:
                break

    def stop(self):
        self.stop_flag.set()
        self.join(timeout=2)
        return self.rows


def smaps_rollup(pid):
    out = {}
    try:
        with open("/proc/%d/smaps_rollup" % pid) as fh:
            for line in fh:
                if line.startswith(("Rss", "Pss", "Anonymous", "Private_Dirty", "Private_Clean")):
                    k, v = line.split(":", 1)
                    out[k] = int(v.split()[0])
    except OSError:
        pass
    return out


def one(engine, size, target, fill):
    """Populate the table (optionally), then one resize, sampled."""
    e = Engine(engine)
    try:
        e.handshake()
        e.setoption("Hash", size)
        e.newgame()
        if fill:
            e.search(FILL_POS, "go depth 20", timeout=900)
        pre = proc_mem(e.p.pid)
        pre_smaps = smaps_rollup(e.p.pid)
        s = Sampler(e.p.pid)
        s.start()
        time.sleep(0.03)
        t0 = time.perf_counter()
        e.setoption("Hash", target)
        dt = time.perf_counter() - t0
        time.sleep(0.03)
        rows = s.stop()
        post = proc_mem(e.p.pid)
        post_smaps = smaps_rollup(e.p.pid)
        rss = [r[1] for r in rows if r[1] is not None]
        vsz = [r[3] for r in rows if r[3] is not None]
        hwm = [r[2] for r in rows if r[2] is not None]
        post_rss = post.get("VmRSS") or 0
        peak = max(rss) if rss else None
        return {
            "size": size, "target": target, "fill": fill,
            "pre_rss": pre.get("VmRSS"), "post_rss": post.get("VmRSS"),
            "pre_hwm": pre.get("VmHWM"), "post_hwm": post.get("VmHWM"),
            "hwm_delta_kb": (post.get("VmHWM") or 0) - (pre.get("VmHWM") or 0),
            "pre_vsz": pre.get("VmSize"), "post_vsz": post.get("VmSize"),
            "vsz_delta_kb": (post.get("VmSize") or 0) - (pre.get("VmSize") or 0),
            "sampled_rss_max": peak,
            "peak_over_post_kb": (peak - post_rss) if peak else None,
            "sampled_vsz_max": max(vsz) if vsz else None,
            "sampled_vsz_min": min(vsz) if vsz else None,
            "sampled_hwm_max": max(hwm) if hwm else None,
            "samples": len(rows),
            "resize_ms": round(dt * 1000, 2),
            "pre_smaps_anonymous_kb": pre_smaps.get("Anonymous"),
            "post_smaps_anonymous_kb": post_smaps.get("Anonymous"),
        }
    finally:
        e.close()


def ratchet(engine, size, rounds):
    """Repeated same-size resizes: does HWM climb once per round?"""
    e = Engine(engine)
    rec = []
    try:
        e.handshake()
        e.setoption("Hash", size)
        e.newgame()
        e.search(FILL_POS, "go depth 18", timeout=600)
        for i in range(rounds):
            pre = proc_mem(e.p.pid)
            e.setoption("Hash", size)
            post = proc_mem(e.p.pid)
            rec.append({
                "round": i,
                "rss": post.get("VmRSS"),
                "hwm": post.get("VmHWM"),
                "vsz": post.get("VmSize"),
                "hwm_delta": (post.get("VmHWM") or 0) - (pre.get("VmHWM") or 0),
            })
    finally:
        e.close()
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=ENGINE)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = {"engine": args.engine, "cases": [], "repeats": {}}
    cases = [
        (32, 32, False, "same size, EMPTY table"),
        (32, 32, True, "same size, FULL table (depth 20)"),
        (64, 64, True, "same size 64, FULL table"),
        (128, 128, True, "same size 128, FULL table"),
        (32, 64, True, "size change 32->64, FULL table  [control: must step VSZ]"),
        (64, 32, True, "size change 64->32, FULL table  [control: must step VSZ]"),
    ]
    print("== single-resize transient ==")
    print("%-42s %9s %9s %9s %8s %9s %7s" % (
        "case", "HWMd_kb", "RSSpeak-P", "VSZd_kb", "n", "resize_ms", "tableMB"))
    for size, target, fill, label in cases:
        r = one(args.engine, size, target, fill)
        r["label"] = label
        out["cases"].append(r)
        print("%-42s %9s %9s %9s %8d %9s %7d" % (
            label, r["hwm_delta_kb"], r["peak_over_post_kb"], r["vsz_delta_kb"],
            r["samples"], r["resize_ms"], target))

    # Repeats: the transient is a peak, so it needs a distribution, not one draw.
    print("\n== same-size transient, 7 repeats each (KB) ==")
    for size in (16, 32, 64, 128, 256):
        vals = []
        for _ in range(7):
            r = one(args.engine, size, size, True)
            vals.append(r["peak_over_post_kb"])
        clean = [v for v in vals if v is not None]
        out["repeats"][str(size)] = vals
        if clean:
            print("  %4d MB: peak-post %s  median %.0f  (table = %d KB)" % (
                size, clean, sorted(clean)[len(clean) // 2], size * 1024))

    print("\n== repeated same-size resize (ratchet / leak check), Hash 32 ==")
    rr = ratchet(args.engine, 32, 8)
    out["ratchet32"] = rr
    print("  round   RSS     HWM     VSZ   HWM_delta")
    for r in rr:
        print("  %5d %7s %7s %7s %10s" % (r["round"], r["rss"], r["hwm"], r["vsz"], r["hwm_delta"]))

    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nwrote", args.out)


if __name__ == "__main__":
    main()
