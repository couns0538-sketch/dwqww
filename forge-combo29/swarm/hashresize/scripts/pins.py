"""Honesty pins: the four numbers every measurement in this seat rests on.

Run before any experiment and again at the end, so a wrong binary cannot
silently underwrite the verdicts.
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import ENGINE

NET_ON = [312866, 862329, 3024920, 12389307, 34048354]
NET_OFF = [375354, 907205, 2448617, 13573040, 24506465]
PERFT5 = 4865609
DEPTHS = [11, 13, 16, 20, 22]


def run(engine=ENGINE):
    lines = []
    lines.append("uci")
    lines.append("isready")
    for d in DEPTHS:
        lines.append("bench %d" % d)
    lines.append("setoption name UseNNUE value false")
    for d in DEPTHS:
        lines.append("bench %d" % d)
    lines.append("position startpos")
    lines.append("go perft 5")
    payload = "\n".join(lines) + "\nquit\n"
    proc = subprocess.run([engine], input=payload, capture_output=True, text=True, timeout=1800)
    out = proc.stdout.splitlines()
    benches = []
    for line in out:
        if line.startswith("info string bench depth"):
            toks = line.split()
            benches.append(int(toks[toks.index("nodes") + 1]))
    perft = None
    for line in out:
        if line.startswith("nodes "):
            perft = int(line.split()[1])
    got_on, got_off = benches[:5], benches[5:10]
    return {
        "engine": engine,
        "bench_on": got_on,
        "bench_off": got_off,
        "perft5": perft,
        "want_on": NET_ON,
        "want_off": NET_OFF,
        "want_perft5": PERFT5,
        "match": got_on == NET_ON and got_off == NET_OFF and perft == PERFT5,
        "uci_name": next((l for l in out if l.startswith("id name")), None),
    }


if __name__ == "__main__":
    engine = sys.argv[1] if len(sys.argv) > 1 else ENGINE
    result = run(engine)
    dest = sys.argv[2] if len(sys.argv) > 2 else None
    print(json.dumps(result, indent=2))
    if dest:
        with open(dest, "w") as fh:
            json.dump(result, fh, indent=2)
    raise SystemExit(0 if result["match"] else 1)
