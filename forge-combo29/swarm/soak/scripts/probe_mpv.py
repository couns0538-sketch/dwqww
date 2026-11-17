"""Probe: wall time of one MultiPV-4 search at Hash 64, to size the 1,000-search churn."""
import sys
import time

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine  # noqa: E402

fens = [l.strip() for l in open("/tmp/soak/positions_R.fens") if l.strip()][10:22]
for mpv in (1, 4):
    eng = Engine("/tmp/soak/build/forge", options={"Hash": 64, "Threads": 1, "MultiPV": mpv})
    t0 = time.monotonic()
    tot = 0
    for fen in fens:
        eng.position_fen(fen)
        r = eng.go("go depth 9")
        tot += r["nodes"] or 0
    el = time.monotonic() - t0
    print("mpv %d: %.2f s for %d searches (%.3f s each), nodes %d, rss %d"
          % (mpv, el, len(fens), el / len(fens), tot, eng.rss_kb()))
    eng.quit()
