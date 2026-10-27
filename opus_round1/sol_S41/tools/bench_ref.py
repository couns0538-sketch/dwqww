#!/usr/bin/env python3
"""Drive a Forge exe over UCI: options, bench at given depths (nodes, time, nps), optional perft5 startpos/kiwipete,
compared with given references. Waits for real output (no sleeps). The exe runs at Idle priority on Windows.

  bench_ref.py <exe> [--ref 312866,862329,3024920,12389307,34048354] [--depths 11,13,16,20,22]
               [--opt NAME=VALUE ...] [--perft] [--uci-out options.txt] [--json out.json] [--label TEXT]
Exit 0 only if every reference given matches (no --ref: always 0 after a complete run).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
PERFT_REF = {"startpos": 4865609, "kiwipete": 193690690}
IDLE_PRIORITY_CLASS = 0x00000040


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--ref")
    ap.add_argument("--depths", default="11,13,16,20,22")
    ap.add_argument("--opt", action="append", default=[])
    ap.add_argument("--perft", action="store_true")
    ap.add_argument("--uci-out")
    ap.add_argument("--json")
    ap.add_argument("--label", default="")
    a = ap.parse_args(argv)
    depths = [int(d) for d in a.depths.split(",")]
    refs = [int(r) for r in a.ref.split(",")] if a.ref else None
    if refs is not None and len(refs) != len(depths):
        ap.error("--ref needs one value per depth")
    flags = IDLE_PRIORITY_CLASS if os.name == "nt" else 0
    p = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, creationflags=flags)

    def send(s: str) -> None:
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(pat: str, collect: list[str] | None = None) -> re.Match:
        rx = re.compile(pat)
        for line in p.stdout:
            if collect is not None:
                collect.append(line.rstrip("\n"))
            m = rx.search(line)
            if m:
                return m
        raise SystemExit("engine exited before matching " + pat)

    uci: list[str] = []
    send("uci")
    wait(r"^uciok", uci)
    if a.uci_out:
        with open(a.uci_out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(l for l in uci if l.startswith("option ")) + "\n")
    for o in ("Threads value 1", "Hash value 16", "OwnBook value false"):
        send("setoption name " + o)
    for o in a.opt:
        name, value = o.split("=", 1)
        send(f"setoption name {name} value {value}")
    send("isready")
    info: list[str] = []
    wait(r"^readyok", info)
    bad_opts = [l for l in info if "invalid value" in l or "unknown" in l.lower()]
    ok = not bad_opts
    rows = []
    head = f"# {a.label} exe={os.path.basename(a.exe)} opts={' '.join(a.opt) or '(defaults)'}"
    print(head, flush=True)
    for l in bad_opts:
        print("OPTION ERROR: " + l, flush=True)
    for i, d in enumerate(depths):
        send(f"bench {d}")
        m = wait(rf"bench depth {d} nodes (\d+) time (\d+) nps (\d+)")
        nodes, ms, nps = int(m.group(1)), int(m.group(2)), int(m.group(3))
        row = {"depth": d, "nodes": nodes, "time_ms": ms, "nps": nps}
        line = f"bench d{d} nodes {nodes} time {ms} ms nps {nps}"
        if refs is not None:
            good = nodes == refs[i]
            ok &= good
            row["ref"] = refs[i]
            row["match"] = good
            row["delta_pct"] = 100.0 * (nodes - refs[i]) / refs[i]
            line += f" ref {refs[i]} {'OK' if good else 'DIFF'} ({row['delta_pct']:+.2f}%)"
        rows.append(row)
        print(line, flush=True)
    perft = {}
    if a.perft:
        for name, pos in (("startpos", "position startpos"), ("kiwipete", "position fen " + KIWI)):
            send(pos)
            send("go perft 5")
            m = wait(r"^nodes (\d+)")
            got = int(m.group(1))
            good = got == PERFT_REF[name]
            ok &= good
            perft[name] = got
            print(f"perft5 {name} {got} ref {PERFT_REF[name]} {'OK' if good else 'FAIL'}", flush=True)
    send("quit")
    p.wait(timeout=60)
    print("ALL OK" if ok else ("DONE (no refs)" if refs is None and not bad_opts else "MISMATCH"), flush=True)
    if a.json:
        with open(a.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"label": a.label, "exe": a.exe, "opts": a.opt, "bench": rows, "perft": perft, "ok": ok,
                       "option_errors": bad_opts}, f, indent=2)
            f.write("\n")
    return 0 if ok or refs is None and not bad_opts else 1


if __name__ == "__main__":
    sys.exit(main())
