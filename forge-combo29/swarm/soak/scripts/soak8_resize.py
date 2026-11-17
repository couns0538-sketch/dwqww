"""P8: the resize transient, measured with VmHWM instead of a sampler.

`TranspositionTable::resize` (search.cpp:362-370) does
    auto new_clusters = std::make_unique<TTCluster[]>(new_count);
    clusters_ = std::move(new_clusters);
so the OLD array is still alive while the NEW one is allocated, then freed by the move's
destructor. The transient therefore holds old + new.

Instrument choice matters and this is the point of the file: an earlier arm (soak2 arm R)
used a 2 ms polling sampler and reported 23.7 MB above max(from,to) for 16 -> 256, where the
OLD table alone is 16 MB. A sampler can miss a transient shorter than its period. `VmHWM`
in /proc/<pid>/status is the kernel's exact peak-RSS high-water mark and cannot miss it, so
every number here is VmHWM, and VmHWM is read BEFORE the process quits.

Cases:
  16  -> 256   predicted 16 + 256 + B = ~280 MB     (B = non-table resident ~8-10 MB)
  256 -> 256   predicted 256 + 256 + B = ~520 MB    (the control: same size, still doubles)
  16  -> 1024  predicted 16 + 1024 + B = ~1050 MB
  256 -> 16    predicted 256 + 16 + B  = ~280 MB    (shrinking also holds both)
  1024 -> 1024 predicted 1024 + 1024 + B = ~2060 MB

KILLED IF 16->256 peaks near 264 MB (256 + B): that is what reusing the old block would give,
and it would make the doubling theoretical rather than real.
"""
import json
import subprocess
import sys
import time

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine  # noqa: E402

CASES = [(16, 256), (256, 256), (16, 1024), (256, 16), (1024, 1024)]
EXE = "/tmp/soak/build/forge"
FEN = [l.strip() for l in open("/tmp/soak/positions_R.fens") if l.strip()][10]

rows = []
print("%6s %6s %10s %10s %10s %10s %8s" %
      ("from", "to", "RSS_before", "VmHWM_after", "VmPeak_after", "peak_MB", "over_sum"))
for a, b in CASES:
    e = Engine(EXE, options={"Hash": a, "Threads": 1})
    # make the old table real: search so it is fully touched and resident
    e.position_fen(FEN)
    e.go("go depth 10")
    before = e.vm_kb()
    e.setoption("Hash", b)
    time.sleep(0.05)
    after = e.vm_kb()
    # and confirm the engine still works after the resize, at the new size
    e.position_fen(FEN)
    r = e.go("go depth 8")
    post = e.vm_kb()
    e.quit()
    over = (after["VmHWM"] - (a + b) * 1024) / 1024.0
    rec = {"from": a, "to": b,
           "rss_before_kb": before["VmRSS"], "vmhwm_before_kb": before["VmHWM"],
           "vmhwm_after_kb": after["VmHWM"], "vmpeak_after_kb": after["VmPeak"],
           "rss_after_kb": after["VmRSS"],
           "peak_mb": round(after["VmHWM"] / 1024.0, 1),
           "over_old_plus_new_mb": round(over, 1),
           "rss_after_search_kb": post["VmRSS"],
           "best_after_resize": r["bestmove"], "nodes_after_resize": r["nodes"]}
    rows.append(rec)
    print("%6d %6d %10d %10d %10d %10.1f %8.1f"
          % (a, b, before["VmRSS"], after["VmHWM"], after["VmPeak"],
             rec["peak_mb"], rec["over_old_plus_new_mb"]))

json.dump(rows, open("/tmp/soak/ev/soak8_resize.json", "w"), indent=1)

print("\ninterpretation rows:")
for r in rows:
    print("  %4d -> %4d : peak %.1f MB vs old+new %d MB, excess %+.1f MB"
          % (r["from"], r["to"], r["peak_mb"], r["from"] + r["to"],
             r["over_old_plus_new_mb"]))
