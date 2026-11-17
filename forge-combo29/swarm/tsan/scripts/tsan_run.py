#!/usr/bin/env python3
"""The TSan search run: drives `Threads 4` through the shared-state cases.

Records RACES ONLY.  No wall-clock, no nps, no node-rate is written to the
output JSON.  Elapsed time appears solely as a watchdog (did the run finish?),
never as a measurement of the engine.

Cases (per audit assignment):
  A  go depth 12        x 40 positions, ucinewgame between every search
  B  go nodes 200000    x 40 positions, ucinewgame between every search
  C  setoption Hash mid-session, interleaved with searches
  D  Clear Hash, interleaved with searches
  E  MultiPV 4          control: documented to run single-threaded
  F  drawn-root bail    control: documented thread-invariant
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from tsan_driver import Engine, races  # noqa: E402
from pathsafe import resolve_exe, resolve_in, resolve_out  # noqa: E402


def thread_count(pid):
    """Live proof the process really has N OS threads."""
    try:
        with open("/proc/%d/status" % pid) as f:
            for line in f:
                if line.startswith("Threads:"):
                    return int(line.split()[1])
    except OSError:
        return -1
    return -1


class Sampler:
    """Samples /proc/<pid>/status Threads while a search runs."""

    def __init__(self, pid):
        self.pid = pid
        self.peak = 0
        self.samples = []
        self._stop = False
        self.t = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop:
            n = thread_count(self.pid)
            self.samples.append(n)
            self.peak = max(self.peak, n)
            time.sleep(0.01)

    def __enter__(self):
        self.t.start()
        return self

    def __exit__(self, *a):
        self._stop = True
        self.t.join(timeout=2)


def run_case(e, name, cmd_seq, timeout, limit, sample_threads=False):
    """Run one case.  cmd_seq is a callable that performs the UCI traffic."""
    rec = {"case": name, "commands": limit}
    t0 = time.time()
    if sample_threads:
        with Sampler(e.proc.pid) as s:
            r = cmd_seq()
            rec["peak_os_threads"] = s.peak
            rec["os_thread_samples"] = sorted(set(s.samples))
    else:
        r = cmd_seq()
    rec["watchdog_elapsed_s"] = round(time.time() - t0, 1)
    rec.update(r)
    return rec


def search(e, limit, timeout):
    bm, info = e.go(limit, timeout)
    last = info[-1] if info else ""
    return {
        "limit": limit,
        "bestmove": bm,
        "info_lines": len(info),
        # Node count is a determinism datum, NOT a timing.
        "last_info": last,
    }


def _sha256(path, chunk=1 << 20):
    """Record the binary's digest in the run output, so a result names its tool."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cases", default="ABCDEF")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--depth", default="12")
    args = ap.parse_args()

    exe = resolve_exe(args.exe, "engine")
    corpus_path = resolve_in(args.corpus, "corpus")
    out_path = resolve_out(args.out, "run output")
    corpus = json.load(open(corpus_path, encoding="utf-8"))["corpus"]
    # A drawn root for case F: kings only, insufficient material -> the bail.
    drawn_root = "8/8/4k3/8/8/4K3/8/8 w - - 0 60"

    e = Engine(str(exe))
    results = []
    cases = args.cases

    # --- Case A: go depth N, ucinewgame between searches -------------------
    if "A" in cases:
        e.cmd("setoption name Threads value 4")
        e.cmd("setoption name Hash value 32")
        e.cmd("setoption name MultiPV value 1")
        e.sync()
        per = []
        for i, c in enumerate(corpus):
            e.cmd("ucinewgame")
            e.cmd("position fen " + c["fen"])
            r = run_case(e, "A", lambda: search(e, "go depth " + args.depth, args.timeout),
                         args.timeout, "go depth " + args.depth,
                         sample_threads=(i == 0))
            r["fen"] = c["fen"]
            per.append(r)
        results.append({"case": "A", "what": "go depth %s over 40 positions, ucinewgame between" % args.depth,
                        "threads_setting": 4, "runs": per})

    # --- Case B: go nodes 200000, ucinewgame between searches --------------
    if "B" in cases:
        e.cmd("setoption name Threads value 4")
        e.sync()
        per = []
        for i, c in enumerate(corpus):
            e.cmd("ucinewgame")
            e.cmd("position fen " + c["fen"])
            r = run_case(e, "B", lambda: search(e, "go nodes 200000", args.timeout),
                         args.timeout, "go nodes 200000",
                         sample_threads=(i == 0))
            r["fen"] = c["fen"]
            per.append(r)
        results.append({"case": "B", "what": "go nodes 200000 over 40 positions, ucinewgame between",
                        "threads_setting": 4, "runs": per})

    # --- Case C: setoption Hash mid-session -------------------------------
    if "C" in cases:
        e.cmd("setoption name Threads value 4")
        e.sync()
        per = []
        for i, c in enumerate(corpus[:20]):
            e.cmd("position fen " + c["fen"])
            e.go("go depth 10", args.timeout)
            # Alternate the value: unchanged-value setoption is the known
            # cold-table defect, so both forms get exercised.
            val = 32 if i % 2 == 0 else 64
            e.cmd("setoption name Hash value %d" % val)
            e.sync()
            r = run_case(e, "C", lambda: search(e, "go depth 10", args.timeout),
                         args.timeout, "go depth 10 after Hash=%d" % val)
            r["fen"] = c["fen"]
            r["hash_after"] = val
            per.append(r)
        results.append({"case": "C", "what": "setoption Hash mid-session, search before and after",
                        "threads_setting": 4, "runs": per})

    # --- Case D: Clear Hash ----------------------------------------------
    if "D" in cases:
        e.cmd("setoption name Threads value 4")
        e.sync()
        per = []
        for i, c in enumerate(corpus[:20]):
            e.cmd("position fen " + c["fen"])
            e.go("go depth 10", args.timeout)
            e.cmd("setoption name Clear Hash")
            e.sync()
            r = run_case(e, "D", lambda: search(e, "go depth 10", args.timeout),
                         args.timeout, "go depth 10 after Clear Hash")
            r["fen"] = c["fen"]
            per.append(r)
        results.append({"case": "D", "what": "Clear Hash between searches", "threads_setting": 4,
                        "runs": per})

    # --- Case E: MultiPV, the single-threaded control ---------------------
    if "E" in cases:
        e.cmd("setoption name Threads value 4")
        e.cmd("setoption name MultiPV value 4")
        e.sync()
        per = []
        for i, c in enumerate(corpus[:10]):
            e.cmd("position fen " + c["fen"])
            r = run_case(e, "E", lambda: search(e, "go depth 10", args.timeout),
                         args.timeout, "go depth 10 MultiPV 4",
                         sample_threads=(i == 0))
            r["fen"] = c["fen"]
            per.append(r)
        e.cmd("setoption name MultiPV value 1")
        results.append({"case": "E", "what": "MultiPV 4 control (documented single-threaded)",
                        "threads_setting": 4, "runs": per})

    # --- Case F: drawn-root bail, the thread-invariant control ------------
    if "F" in cases:
        e.cmd("setoption name Threads value 4")
        e.cmd("setoption name MultiPV value 1")
        e.cmd("setoption name DrawJitter value 0")
        e.cmd("position fen " + drawn_root)
        e.sync()
        r = run_case(e, "F", lambda: search(e, "go depth 12", args.timeout),
                     args.timeout, "go depth 12 on a KvK drawn root",
                     sample_threads=True)
        r["fen"] = drawn_root
        results.append({"case": "F", "what": "drawn-root bail control (KvK, thread-invariant)",
                        "threads_setting": 4, "runs": [r]})
        e.cmd("setoption name DrawJitter value 0")

    # --- Case G: go infinite then stop, helpers live when 'stop' arrives ------
    if "G" in cases:
        e.cmd("setoption name Threads value 4")
        e.cmd("setoption name MultiPV value 1")
        e.sync()
        per = []
        for i, c in enumerate(corpus[:8]):
            e.cmd("ucinewgame")
            e.cmd("position fen " + c["fen"])
            e.sync()
            t0 = time.time()
            e.cmd("go infinite")
            time.sleep(1.5)          # let the helpers get into the tree
            e.cmd("stop")
            # 'stop' is answered by the bestmove from the running search.
            try:
                bm, info = e._wait_bestmove(args.timeout)
            except Exception as ex:  # noqa: BLE001
                bm, info = "ERROR:" + str(ex), []
            per.append({"case": "G", "limit": "go infinite + stop",
                        "fen": c["fen"], "bestmove": bm, "info_lines": len(info),
                        "watchdog_elapsed_s": round(time.time() - t0, 1)})
        results.append({"case": "G",
                        "what": "go infinite then stop while 4 workers are live (stop flag + joins)",
                        "threads_setting": 4, "runs": per})

    # --- Case H: resize Threads mid-session --------------------------------
    if "H" in cases:
        per = []
        for i, c in enumerate(corpus[:8]):
            th = [1, 4, 2, 8][i % 4]
            e.cmd("setoption name Threads value %d" % th)
            e.sync()
            e.cmd("ucinewgame")
            e.cmd("position fen " + c["fen"])
            r = run_case(e, "H", lambda: search(e, "go depth 11", args.timeout),
                         args.timeout, "go depth 11 with Threads=%d after resize" % th)
            r["fen"] = c["fen"]
            r["threads_after_resize"] = th
            per.append(r)
        results.append({"case": "H",
                        "what": "setoption Threads mid-session (worker vector grows and shrinks)",
                        "threads_setting": "1/4/2/8 cycle", "runs": per})

    log = e.close()

    all_races = races(log)
    out = {
        "exe": str(exe),
        "exe_sha256": _sha256(exe),
        "note": "TSan run. Races only; no timing is recorded as a measurement. "
                "watchdog_elapsed_s only proves the run completed.",
        "cases": results,
        "race_count": len(all_races),
        "races": [{"kind": x["kind"], "summary": x["summary"],
                   "first_frames": [l.strip() for l in x["lines"]
                                    if l.strip().startswith("#0") or l.strip().startswith("#1")][:6]}
                  for x in all_races],
    }
    json.dump(out, open(out_path, "w", encoding="utf-8"), indent=1)
    rawlog_path = out_path.with_suffix(".rawlog")
    with open(rawlog_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log))
    print("races:", len(all_races))
    print("wrote", out_path, "and", rawlog_path)


if __name__ == "__main__":
    main()
