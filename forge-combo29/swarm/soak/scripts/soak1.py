"""Soak 1: 5,000 `go depth 12` searches in ONE process, RSS sampled every 50.

Position order is a fixed shuffle (seed 6901) over positions_R.fens, so the run is
reproducible and the position mix is the same across arms.

Writes one CSV row per sample: search_index, rss_kb, vm_kb, elapsed_s, cumulative_nodes.
Also writes a per-search log (search index, fen hash, nodes, bestmove) so a changing
answer or a stalled search would show up.
"""
import argparse
import hashlib
import json
import random
import sys
import time

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--searches", type=int, default=5000)
    ap.add_argument("--every", type=int, default=50)
    ap.add_argument("--hash", type=int, default=32)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--multipv", type=int, default=1)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--reset", choices=["none", "ucinewgame", "clearhash"], default="none")
    ap.add_argument("--reset-every", type=int, default=1)
    ap.add_argument("--positions", default="/tmp/soak/positions_R.fens")
    ap.add_argument("--seed", type=int, default=6901)
    ap.add_argument("--env", default="")
    args = ap.parse_args()

    fens = [l.strip() for l in open(args.positions) if l.strip()]
    rng = random.Random(args.seed)
    order = list(range(len(fens)))
    rng.shuffle(order)

    env = {}
    for kv in args.env.split(";"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            env[k.strip()] = v.strip()

    eng = Engine(args.exe, env=env or None,
                 options={"Hash": args.hash, "Threads": args.threads,
                          "MultiPV": args.multipv})

    base_vm = eng.vm_kb()
    t0 = time.monotonic()
    with open(args.out + ".csv", "w") as csv, open(args.out + ".log", "w") as log:
        csv.write("search,rss_kb,vmpeak_kb,elapsed_s,cum_nodes\n")
        csv.write("0,%d,%d,0.0,0\n" % (base_vm["VmRSS"], base_vm["VmPeak"]))
        log.write(json.dumps({"event": "start", "pid": eng.proc.pid, "vm": base_vm,
                              "options": eng.sent, "id": eng.id_name,
                              "hash": args.hash, "threads": args.threads,
                              "multipv": args.multipv, "depth": args.depth,
                              "reset": args.reset}) + "\n")
        cum = 0
        for i in range(1, args.searches + 1):
            fen = fens[order[(i - 1) % len(order)]]
            if args.reset != "none" and i % args.reset_every == 0:
                if args.reset == "ucinewgame":
                    eng.newgame()
                else:
                    eng.setoption("Clear Hash", "")
            eng.position_fen(fen)
            r = eng.go("go depth %d" % args.depth)
            cum += r["nodes"] or 0
            if r["nodes"] is None:
                log.write(json.dumps({"search": i, "ERROR": "no info depth line",
                                      "fen": fen}) + "\n")
            if i % args.every == 0 or i <= 10:
                vm = eng.vm_kb()
                el = time.monotonic() - t0
                csv.write("%d,%d,%d,%.2f,%d\n" % (i, vm["VmRSS"], vm["VmPeak"], el, cum))
                csv.flush()
            log.write(json.dumps({"search": i, "nodes": r["nodes"],
                                  "best": r["bestmove"],
                                  "fen_sha": hashlib.sha1(fen.encode()).hexdigest()[:12]}) + "\n")
            if not eng.alive():
                log.write(json.dumps({"search": i, "ERROR": "engine died",
                                      "rc": eng.proc.returncode}) + "\n")
                break
    vm = eng.vm_kb()
    eng.quit()
    print("done %d searches, rss %d vmpeak %d elapsed %.1f"
          % (args.searches, vm["VmRSS"], vm["VmPeak"], time.monotonic() - t0))


if __name__ == "__main__":
    main()
