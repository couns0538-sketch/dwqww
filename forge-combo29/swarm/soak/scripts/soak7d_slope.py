"""P7d: the decisive test of the alternate-table sizing -- a SLOPE, not a cliff.

The cliff was the wrong instrument (see P7, which failed numerically). The sizing question --
"is the alternate table the same MB as the main table?" -- is answered directly by how peak
RSS grows with Hash at fixed MultiPV:

  if the alternate table is the SAME size as the main table, peak RSS grows at 2 MB per MB
  of Hash at MultiPV 2, and at 1 MB per MB at MultiPV 1.
  if it were a fixed ~105 MB auxiliary table, peak would grow at 1 MB per MB at BOTH.

So: measure VmHWM (exact kernel peak, no sampling) at Hash 32/64/128/256 for MPV 1 and
MPV 2, and fit the slope. Predicted slopes: **1.00 (MPV1), 2.00 (MPV2)**.

The 32 MB default table is allocated at construction before `setoption name Hash` runs, so
the MPV-1 peak also carries a transient of the default size; that is a constant offset, not a
slope, and the fit reports the intercept separately so the two cannot be confused.

Every cell runs the same 6 positions at depth 10, so the number of stored entries -- and
therefore how much of each table is actually touched -- is held constant across Hash.
"""
import json
import subprocess
import sys

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine  # noqa: E402

EXE = "/tmp/soak/build/forge"
FENS = [l.strip() for l in open("/tmp/soak/positions_R.fens") if l.strip()][10:16]
HASHES = (32, 64, 128, 256)


def peak(hash_mb, multipv):
    e = Engine(EXE, options={"Hash": hash_mb, "Threads": 1, "MultiPV": multipv})
    for f in FENS:
        e.position_fen(f)
        e.go("go depth 10")
    vm = e.vm_kb()
    e.quit()
    return vm


def fit(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    slope = (sum((x - mx) * (y - my) for x, y in zip(xs, ys))
             / sum((x - mx) ** 2 for x in xs))
    return slope, my - slope * mx


out = {}
print("%4s %4s %10s %10s %10s %10s" %
      ("Hash", "MPV", "VmHWM_MB", "VmPeak_MB", "VmSize_MB", "RSS_MB"))
for mpv in (1, 2, 4):
    xs, ys = [], []
    for h in HASHES:
        vm = peak(h, mpv)
        xs.append(h)
        ys.append(vm["VmHWM"] / 1024.0)
        out.setdefault(str(mpv), []).append(
            {"hash": h, "vmhwm_mb": round(vm["VmHWM"] / 1024.0, 1),
             "vmpeak_mb": round(vm["VmPeak"] / 1024.0, 1),
             "vmsize_mb": round(vm["VmSize"] / 1024.0, 1),
             "rss_mb": round(vm["VmRSS"] / 1024.0, 1)})
        print("%4d %4d %10.1f %10.1f %10.1f %10.1f"
              % (h, mpv, vm["VmHWM"] / 1024.0, vm["VmPeak"] / 1024.0,
                 vm["VmSize"] / 1024.0, vm["VmRSS"] / 1024.0))
    slope, intercept = fit(xs, ys)
    out[str(mpv) + "_slope"] = round(slope, 3)
    out[str(mpv) + "_intercept_mb"] = round(intercept, 1)
    print("  -> MPV %d: peak RSS slope %.3f MB per MB of Hash, intercept %.1f MB"
          % (mpv, slope, intercept))
    print()

json.dump(out, open("/tmp/soak/ev/soak7d_slope.json", "w"), indent=1)

print("VERDICT on the sizing question:")
s1 = out["1_slope"]
s2 = out["2_slope"]
print("  MPV1 slope %.2f (predicted 1.00), MPV2 slope %.2f (predicted 2.00)" % (s1, s2))
if s2 > 1.7:
    print("  The alternate table grows WITH Hash at ~the same rate as the main table:")
    print("  it is a full-size second table, not a fixed auxiliary allocation.")
elif s2 < 1.3:
    print("  The alternate table does NOT grow with Hash: it is a fixed-size auxiliary")
    print("  table and the cluster_count sizing reading is WRONG.")
else:
    print("  Intermediate slope: needs a third model, reported as unresolved.")
