"""Experiment F - same-value resize: the wipe on an EMPTY table, and its transient cost.

Coordinator's items 1 and 2.

Item 1 - does the same-value resize wipe even when there is nothing to wipe?
  Three cold arms per process shape, each from a fresh process:
    F_silent    Hash 32 set once, never re-sent          (the baseline)
    F_resend    Hash 32 set, then sent AGAIN before any search
    F_default   never send Hash at all (the default is 32)
  On a cold table all three must agree if the wipe needs contents to matter.
  The instrument is proved live by F_warm_resend in the same script: the same
  re-send after a search must DIFFER from the warm baseline.  Without that pair
  the null in item 1 would be indistinguishable from a probe that cannot see
  anything (forge-findings.md S6, S7).

Item 2 - the transient.  `TranspositionTable::resize` builds the new array and
  only then move-assigns it over `clusters_`, so the old and new blocks are
  alive at the same instant.  For a same-size resize that is 2x the table.
  A sampler can miss that window, so the primary instrument is `VmHWM` - the
  kernel's monotonic high-water mark, which cannot miss a peak that happened.
  RSS sampling at high frequency is reported beside it as the corroborating
  reading, and its resolution limit is stated rather than hidden.
"""

import argparse
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import Engine, ENGINE, proc_mem
from corpus import select

POSITION = None  # filled from the corpus in main()


def fresh_arm(engine, position, go, ops):
    e = Engine(engine)
    try:
        e.handshake()
        for op, arg in ops:
            if op == "hash":
                e.setoption("Hash", arg)
            elif op == "resend":
                e.setoption("Hash", arg)
            elif op == "newgame":
                e.newgame()
        r = e.search(position, go)
        return {"bestmove": r["bestmove"], "nodes": r["nodes"], "score": r["score"],
                "depth": r["depth"], "seldepth": r["seldepth"], "hashfull": r["hashfull"],
                "info_depth_lines": r["info_depth_lines"]}
    finally:
        e.close()


def warm_arm(engine, position, go, hash_mb, resend):
    e = Engine(engine)
    try:
        e.handshake()
        e.setoption("Hash", hash_mb)
        e.newgame()
        r = e.search(position, go)
        warm = {"bestmove": r["bestmove"], "nodes": r["nodes"], "score": r["score"],
                "depth": r["depth"], "hashfull": r["hashfull"]}
        if resend:
            e.setoption("Hash", hash_mb)
        r2 = e.search(position, go)
        return warm, {"bestmove": r2["bestmove"], "nodes": r2["nodes"], "score": r2["score"],
                      "depth": r2["depth"], "hashfull": r2["hashfull"]}
    finally:
        e.close()


class RssSampler(threading.Thread):
    """Sample VmRSS/VmHWM as fast as the kernel will answer."""

    def __init__(self, pid, interval=0.0002):
        super().__init__(daemon=True)
        self.pid = pid
        self.interval = interval
        self.samples = []
        self.stop_flag = threading.Event()

    def run(self):
        while not self.stop_flag.is_set():
            m = proc_mem(self.pid)
            if m:
                self.samples.append((time.perf_counter(), m.get("VmRSS"), m.get("VmHWM")))
            time.sleep(self.interval)

    def stop(self):
        self.stop_flag.set()
        self.join(timeout=2)


def transient(engine, hash_mb, target_mb, do_search):
    """RSS/HWM across one resize, with and without a populated table."""
    e = Engine(engine)
    try:
        e.handshake()
        e.setoption("Hash", hash_mb)
        if do_search:
            e.setoption("Hash", hash_mb)
        e.newgame()
        if do_search:
            e.search("position fen " + POSITION, "go depth 14", timeout=300)
        before = proc_mem(e.p.pid)
        sampler = RssSampler(e.p.pid)
        sampler.start()
        time.sleep(0.05)
        t0 = time.perf_counter()
        e.setoption("Hash", target_mb)
        dt = time.perf_counter() - t0
        time.sleep(0.05)
        sampler.stop()
        after = proc_mem(e.p.pid)
        rss = [s[1] for s in sampler.samples if s[1]]
        hwm = [s[2] for s in sampler.samples if s[2]]
        return {
            "hash_mb": hash_mb,
            "target_mb": target_mb,
            "with_search": do_search,
            "before_rss": before.get("VmRSS"),
            "before_hwm": before.get("VmHWM"),
            "after_rss": after.get("VmRSS"),
            "after_hwm": after.get("VmHWM"),
            "peak_rss_sampled": max(rss) if rss else None,
            "peak_hwm_sampled": max(hwm) if hwm else None,
            "min_rss_sampled": min(rss) if rss else None,
            "samples": len(sampler.samples),
            "setoption_latency_s": round(dt, 4),
        }
    finally:
        e.close()


def main():
    global POSITION
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=ENGINE)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--hash", type=int, default=32)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    chosen, _ = select(1, 18, engine=args.engine)
    POSITION = chosen[0]["fen"]
    pos = "position fen " + POSITION
    go = "go depth %d" % args.depth

    out = {"position": POSITION, "go": go, "depth": args.depth, "hash": args.hash}
    print("position:", POSITION, flush=True)

    # --- item 1: cold table, does the re-send matter? --------------------
    f_silent = fresh_arm(args.engine, pos, go, [("hash", args.hash), ("newgame", None)])
    f_resend = fresh_arm(args.engine, pos, go, [("hash", args.hash), ("newgame", None), ("resend", args.hash)])
    f_default = fresh_arm(args.engine, pos, go, [("newgame", None)])
    f_order = fresh_arm(args.engine, pos, go, [("hash", args.hash), ("resend", args.hash), ("newgame", None)])

    # --- the same re-send AFTER a search, to prove the probe is live -----
    w_none = warm_arm(args.engine, pos, go, args.hash, resend=False)
    w_resend = warm_arm(args.engine, pos, go, args.hash, resend=True)

    out["item1"] = {
        "cold_silent": f_silent,
        "cold_resend_after_hash": f_resend,
        "cold_default_no_hash": f_default,
        "cold_resend_before_newgame": f_order,
        "warm_no_resend": w_none,
        "warm_resend": w_resend,
    }

    def same(a, b):
        return all(a[k] == b[k] for k in ("bestmove", "nodes", "score", "depth"))

    out["item1_verdict"] = {
        "cold_resend_equals_silent": same(f_resend, f_silent),
        "cold_resend_equals_default": same(f_resend, f_default),
        "cold_resend_before_newgame_equals_silent": same(f_order, f_silent),
        "warm_resend_differs_from_warm": not same(w_none[1], w_resend[1]),
    }
    print("\n== item 1: same-value resize on an EMPTY table ==")
    for name, c in (("cold silent", f_silent), ("cold resend", f_resend),
                    ("cold no Hash ever", f_default), ("cold resend then newgame", f_order)):
        print("  %-26s %s nodes %s score %s depth %s" % (name, c["bestmove"], c["nodes"], c["score"], c["depth"]))
    print("  warm, no resend        %s nodes %s" % (w_none[1]["bestmove"], w_none[1]["nodes"]))
    print("  warm, resend same      %s nodes %s" % (w_resend[1]["bestmove"], w_resend[1]["nodes"]))
    print("  verdict:", json.dumps(out["item1_verdict"]))

    # --- item 2: transient memory ---------------------------------------
    print("\n== item 2: transient memory across one resize ==")
    trans = []
    for h, t, s in ((32, 32, False), (32, 32, True), (16, 16, True), (16, 256, True),
                    (256, 16, True), (64, 64, True)):
        r = transient(args.engine, h, t, s)
        trans.append(r)
        print("  %4d -> %4d (search=%s): RSS %7s -> %7s  HWM %7s -> %7s  peak_sampled %7s  n=%d  %.1f ms" % (
            h, t, s, r["before_rss"], r["after_rss"], r["before_hwm"], r["after_hwm"],
            r["peak_rss_sampled"], r["samples"], r["setoption_latency_s"] * 1000))
    out["item2_transient"] = trans

    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nwrote", args.out)


if __name__ == "__main__":
    main()
