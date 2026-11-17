#!/usr/bin/env python3
"""Compact the per-ply JSONL to short keys so the evidence stays small enough to commit.

Rewrites each file in place. A companion .map.json records the key meanings.
"""
import json, os

MAP = [("game", "g"), ("ply", "p"), ("bm", "m"), ("score", "s"), ("nodes", "n"),
       ("depth", "d"), ("sd", "e"), ("hf", "h"), ("pv0", "v"), ("npv", "w"),
       ("wall_ms", "t")]


def compact(src):
    n = 0
    tmp = src + ".tmp"
    with open(src, encoding="utf-8") as fh, open(tmp, "w", encoding="utf-8") as o:
        for line in fh:
            r = json.loads(line)
            if "g" in r and "game" not in r:
                o.write(line)
                n += 1
                continue
            c = {}
            for long, short in MAP:
                if long in r and r[long] is not None:
                    c[short] = r[long]
            if r.get("bail"):
                c["b"] = 1
            # KEEP the diagnostics: a refused FEN is only visible here, and dropping the
            # field would make the "zero refusals" scan a dead control.
            if r.get("diag"):
                c["i"] = " | ".join(r["diag"])
            o.write(json.dumps(c, separators=(",", ":")) + "\n")
            n += 1
    os.replace(tmp, src)
    print(f"{src}: {n} rows, {os.path.getsize(src)/1e6:.2f} MB")


for f in ["session", "fresh", "unc", "clearhash", "hashresend", "uncgame", "session_rev",
          "startpos_session", "startpos_fresh"]:
    p = f"evidence/{f}.jsonl"
    if os.path.exists(p):
        compact(p)

json.dump({s: l for l, s in MAP} | {"b": "bail(1=true)"},
          open("evidence/keys.json", "w", encoding="utf-8"), indent=0)
print(open("evidence/keys.json", encoding="utf-8").read())
