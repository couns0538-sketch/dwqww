#!/usr/bin/env python3
"""check_s11f8.py -- MY OWN check of seat 11's S-F8: `setoption` without `value` is silently a no-op.

Written from their finding sentence. Each case is one fresh process, fully synchronised:
uci/isready/readyok, then the setoption UNDER TEST, then isready/readyok again (so any answer line
is captured between the two readyoks), then a measurement, then quit.

Measurements used:
  * `eval` -> the engine prints `hce ... nnue ... total ...`, so UseNNUE can be observed directly;
  * `bench 11` -> 312,866 is the honesty number, so a Hash change is observable only through an
    answer line, not through nodes (recorded, not guessed);
  * `go depth 4` node counts to see whether Ponder/Threads changed anything.

usage: check_s11f8.py EXE OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

CASES = [
    # (label, setoption line or None, probe command)
    ("baseline_eval", None, "eval"),
    ("no_value_word_UseNNUE_false", "setoption name UseNNUE false", "eval"),
    ("with_value_word_UseNNUE_false", "setoption name UseNNUE value false", "eval"),
    ("no_value_word_Hash_64", "setoption name Hash 64", "eval"),
    ("with_value_word_Hash_64", "setoption name Hash value 64", "eval"),
    ("bad_value_Hash_0", "setoption name Hash value 0", "eval"),
    ("no_value_word_Hash_0", "setoption name Hash 0", "eval"),
    ("unknown_name_typo_Thread", "setoption name Thread value 4", "eval"),
    ("no_value_word_Ponder", "setoption name Ponder", "eval"),
    ("with_value_word_Ponder_true", "setoption name Ponder value true", "eval"),
    ("unknown_option_Bogus", "setoption name BogusOption value 64", "eval"),
    ("garbage_line", "garbage line", "eval"),
    # node-count probes: does any of these change the search?
    ("baseline_bench11", None, "bench 11"),
    ("no_value_word_Hash_64_bench11", "setoption name Hash 64", "bench 11"),
    ("with_value_Hash_64_bench11", "setoption name Hash value 64", "bench 11"),
    ("no_value_Threads_4_bench11", "setoption name Threads 4", "bench 11"),
    ("with_value_Threads_4_bench11", "setoption name Threads value 4", "bench 11"),
]


def run_case(exe, setopt, probe):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1, env=env,
                         start_new_session=True)
    out, err = [], []
    lock = threading.Lock()

    def pump(stream, sink):
        try:
            for l in stream:
                with lock:
                    sink.append(l.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=pump, args=(p.stdout, out), daemon=True).start()
    threading.Thread(target=pump, args=(p.stderr, err), daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait_ready(mark, timeout=180.0):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            with lock:
                if any(x.strip() == "readyok" for x in out[mark:]):
                    return True
            if p.poll() is not None:
                return False
            time.sleep(0.003)
        return False

    def sync():
        with lock:
            mark = len(out)
        send("isready")
        return mark, wait_ready(mark)

    send("uci")
    time.sleep(0.05)
    sync()
    rec = {"setoption": setopt, "probe": probe, "answer_lines": [], "result_lines": []}
    if setopt:
        with lock:
            mark = len(out)
        send(setopt)
        ok = wait_ready(mark)
        with lock:
            rec["answer_lines"] = [x for x in out[mark:] if x.strip() != "readyok"]
        rec["ready_after_setoption"] = ok
    with lock:
        mark = len(out)
    send(probe)
    t0 = time.monotonic()
    while time.monotonic() - t0 < 300:
        with lock:
            block = out[mark:]
            done = any(x.startswith("ready") for x in block) if probe == "eval" else \
                any(x.startswith("info string bench") for x in block)
        if done and probe == "bench 11":
            # bench prints one line; a short grace lets the line land
            time.sleep(0.05)
            break
        if probe == "eval" and done:
            break
        if p.poll() is not None:
            break
        time.sleep(0.003)
    with lock:
        rec["result_lines"] = [x for x in out[mark:] if x.strip() not in ("readyok",)]
    rec["san"] = [l for l in err if "Sanitizer" in l or "runtime error" in l][:3]
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        pass
    return rec


def summarise(rec):
    s = " ".join(rec["result_lines"])
    if rec["probe"] == "eval":
        for tok in ("hce", "nnue", "total"):
            i = s.find(tok + " ")
            if i >= 0:
                rest = s[i:].split()
                rec[tok] = rest[1] if len(rest) > 1 else None
    else:
        for l in rec["result_lines"]:
            if l.startswith("info string bench"):
                rec["bench_line"] = l
                parts = l.split()
                if "nodes" in parts:
                    rec["nodes"] = parts[parts.index("nodes") + 1]
    return rec


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    print("%-34s %-22s %-12s %-28s %s" % ("case", "setoption sent", "answer?", "probe result", "verdict"))
    for label, setopt, probe in CASES:
        r = run_case(exe, setopt, probe)
        r = summarise(r)
        r["case"] = label
        rows.append(r)
        ans = "NONE" if not r["answer_lines"] else r["answer_lines"][0][:40]
        if probe == "eval":
            res = "hce=%s nnue=%s total=%s" % (r.get("hce"), r.get("nnue"), r.get("total"))
        else:
            res = "nodes=%s" % r.get("nodes")
        print("%-34s %-22s %-12s %-28s" % (label, (setopt or "-")[:22], ans, res))
    base = next(r for r in rows if r["case"] == "baseline_eval")
    for r in rows:
        if r["probe"] == "eval" and r["case"] != "baseline_eval":
            r["changed_vs_baseline"] = (r.get("nnue") != base.get("nnue")
                                        or r.get("total") != base.get("total"))
    bb = next(r for r in rows if r["case"] == "baseline_bench11")
    for r in rows:
        if r["probe"] == "bench 11" and r["case"] != "baseline_bench11":
            r["nodes_equal_baseline"] = (r.get("nodes") == bb.get("nodes"))
    unparsed = [r["case"] for r in rows
                if r["probe"] == "eval" and (r.get("nnue") is None or r.get("hce") is None)]
    if unparsed:
        print("FAIL: the eval line was not parsed for: %s" % ", ".join(unparsed))
        print("(a missing value must not be compared -- None != None would look like a change)")
        raise SystemExit(3)
    with open(os.path.join(outdir, "results.json"), "w") as f:
        json.dump({"exe": os.path.realpath(exe), "rows": rows}, f, indent=1)
    print()
    print("verdicts:")
    for r in rows:
        if "changed_vs_baseline" in r:
            print("  %-34s changed something: %s" % (r["case"], r["changed_vs_baseline"]))
        if "nodes_equal_baseline" in r:
            print("  %-34s nodes equal to baseline: %s (%s)" % (
                r["case"], r["nodes_equal_baseline"], r.get("nodes")))


if __name__ == "__main__":
    main()
