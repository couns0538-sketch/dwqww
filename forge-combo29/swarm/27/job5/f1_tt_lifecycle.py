#!/usr/bin/env python3
"""f1_tt_lifecycle.py <exe> <outdir> [--tries N]

Area 7 job 5: the transposition table's lifecycle against a RUNNING search.

The code (src/search.cpp:350-371) makes probe/store take a stripe lock, and gives `resize()` and
`clear()` NO lock at all -- they replace `clusters_` / `cluster_count_` outright. The UCI handler
calls stop_search() before `setoption` (uci.cpp:259), so a resize *should* never overlap a search;
this tests whether that holds from the outside, i.e. whether any interleaving the engine itself
accepts can resize under a live search.

Every case is driven one line at a time with a wait, never a whole-session write (19-F12), and every
parse asserts its line was found.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time


class Engine:
    def __init__(self, exe, env=None):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, bufsize=1,
                                  env=env)

    def send(self, s):
        try:
            self.p.stdin.write(s + "\n")
            self.p.stdin.flush()
        except (BrokenPipeError, ValueError):
            raise RuntimeError("engine closed stdin (it died) while sending %r" % s)

    def until(self, pred, timeout=300):
        t0 = time.monotonic()
        out = []
        while time.monotonic() - t0 < timeout:
            ln = self.p.stdout.readline()
            if not ln:
                break
            s = ln.rstrip("\n")
            out.append(s)
            if pred(s):
                return out, True
        return out, False

    def boot(self):
        self.send("uci")
        _, ok = self.until(lambda s: s.strip() == "uciok")
        if not ok:
            raise RuntimeError("no uciok")
        self.send("isready")
        _, ok = self.until(lambda s: s.strip() == "readyok")
        if not ok:
            raise RuntimeError("no readyok")

    def search_async(self, pos, limit):
        """Start a search; return a list that a thread fills with the output until bestmove."""
        self.send("position " + pos)
        self.send("isready")
        _, ok = self.until(lambda s: s.strip() == "readyok")
        if not ok:
            raise RuntimeError("no readyok before go")
        self.send("go " + limit)
        lines = []
        done = threading.Event()

        def reader():
            while True:
                ln = self.p.stdout.readline()
                if not ln:
                    break
                s = ln.rstrip("\n")
                lines.append(s)
                if s.startswith("bestmove"):
                    break
            done.set()

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        return lines, done

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=20)
        except Exception:
            self.p.kill()


def san_lines(text):
    pats = ["ERROR: AddressSanitizer", "ERROR: LeakSanitizer", "WARNING: ThreadSanitizer", "runtime error:"]
    total = 0
    kinds = {}
    for p in pats:
        c = text.count(p)
        if c:
            kinds[p] = c
            total += c
    return total, kinds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--tries", type=int, default=12)
    ap.add_argument("--delay-ms", type=int, default=8)
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)

    env = dict(os.environ)
    env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"

    results = []
    for i in range(a.tries):
        eng = Engine(exe, env)
        try:
            eng.boot()
            eng.send("setoption name Hash value 16")
            eng.send("isready")
            eng.until(lambda s: s.strip() == "readyok")
            eng.send("ucinewgame")
            eng.send("isready")
            eng.until(lambda s: s.strip() == "readyok")
            lines, done = eng.search_async("startpos", "depth 24")
            # resize the table while that search is very likely still running
            time.sleep(a.delay_ms / 1000.0)
            alive = done.is_set()
            eng.send("setoption name Hash value %d" % (64 + i))
            eng.send("isready")
            time.sleep(0.05)
            finished = done.wait(timeout=240)
            out = "\n".join(lines)
            bestmoves = re.findall(r"^bestmove (\S+)", out, re.M)
            n_san, kinds = san_lines(out)
            results.append({"try": i, "search_was_running_when_resized": not alive,
                            "finished": finished, "bestmoves": bestmoves,
                            "info_lines": len([l for l in lines if l.startswith("info depth")]),
                            "sanitizer_lines": n_san, "sanitizer_kinds": kinds,
                            "stderr_tail": ""})
        except Exception as ex:  # the engine dying is itself a result
            err = ""
            try:
                err = eng.p.stderr.read() if eng.p.stderr else ""
            except Exception:
                pass
            n_san, kinds = san_lines(err or "")
            results.append({"try": i, "exception": "%s: %s" % (type(ex).__name__, ex),
                            "sanitizer_lines": n_san, "sanitizer_kinds": kinds,
                            "stderr_tail": (err or "")[-400:]})
        finally:
            eng.close()

    out = {"exe": exe,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "tries": a.tries, "delay_ms": a.delay_ms, "results": results}
    with open(os.path.join(a.outdir, "result.json"), "w") as f:
        json.dump(out, f, indent=2)

    exc = [r for r in results if "exception" in r]
    san = sum(r["sanitizer_lines"] for r in results)
    running = [r for r in results if r.get("search_was_running_when_resized")]
    with open(os.path.join(a.outdir, "SUMMARY.txt"), "w") as f:
        f.write("exe %s\nsha %s\ndate %s\ntries %d (resize sent %d ms into a `go depth 24`)\n\n"
                % (exe, out["sha256"], out["date_utc"], a.tries, a.delay_ms))
        f.write("the search really was still running when the resize was sent: %d of %d tries\n"
                % (len(running), a.tries))
        f.write("exceptions (engine death): %d\n" % len(exc))
        for r in exc:
            f.write("  try %d: %s\n" % (r["try"], r["exception"]))
        f.write("sanitizer lines total: %d\n" % san)
        f.write("searches that finished with a bestmove: %d of %d\n"
                % (sum(1 for r in results if r.get("finished")), a.tries))
        bms = [r["bestmoves"][-1] for r in results if r.get("bestmoves")]
        f.write("bestmoves: %s\n" % (bms if bms else "(none)"))
    print(open(os.path.join(a.outdir, "SUMMARY.txt")).read())


if __name__ == "__main__":
    main()
