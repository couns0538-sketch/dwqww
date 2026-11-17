"""Quick probe: cost of one `go depth 12` search, and the RSS baseline."""
import sys
import time

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine  # noqa: E402

EXE = "/tmp/soak/build/forge"
fens = [l.strip() for l in open("/tmp/soak/positions_R.fens") if l.strip()]

eng = Engine(EXE, options={"Hash": 32, "Threads": 1})
t0 = time.monotonic()
for i, fen in enumerate(fens[10:30]):
    eng.position_fen(fen)
    r = eng.go("go depth 12")
    print(i, r["nodes"], r["bestmove"], eng.rss_kb())
print("total s", round(time.monotonic() - t0, 2))
eng.quit()
