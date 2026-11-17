"""Print a case's wire transcript in a compact, greppable form."""
from __future__ import annotations

import json
import sys


def main() -> int:
    path = sys.argv[1]
    want = sys.argv[2:] if len(sys.argv) > 2 else None
    with open(path) as f:
        data = json.load(f)
    for c in data["cases"]:
        if want and c["case"] not in want:
            continue
        print(f"===== {c['case']} =====")
        if c.get("note"):
            print(f"note: {c['note']}")
        for ev in c.get("events", []):
            print(f"  EVENT {ev}")
        for s in c.get("sent", []):
            print(f">>> [{s['t']:.3f}] {s['text']}")
        # skip the handshake option block unless asked
        lines = c.get("lines", [])
        shown = 0
        for ln in lines:
            t = ln["text"]
            if t.startswith("option name ") and shown < 3:
                shown += 1
                print(f"<<< [{ln['t']:.3f}] {t[:60]}...")
                continue
            print(f"<<< [{ln['t']:.3f}] {t}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
