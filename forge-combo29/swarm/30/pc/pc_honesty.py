#!/usr/bin/env python3
"""pc_honesty.py -- the PC r15 build's known answers, three settings regimes, one fresh process per line.

File 5's table (measured on the PC's own exe):
    none                    bench 11 312866 | bench 13 862329 | bench 16 3024920 | perft 5 4865609
    S14 (14 setoptions)                  242796 |          656517
    PC20 (S14 + 6 more)                  278024 |          587276

Every option name is taken from the exe's OWN `uci` list first; the script stops on `unknown option`,
`invalid value` or `ERROR`. Nothing is piped: each command is written, then stdout is read until its
terminal line arrives, and only then is the next command written (19-F12).

usage: pc_honesty.py EXE OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

EXPECT = {
    "none": {"bench 11": 312866, "bench 13": 862329, "bench 16": 3024920,
             "go perft 5": 4865609},
    "S14": {"bench 11": 242796, "bench 13": 656517},
    "PC20": {"bench 11": 278024, "bench 13": 587276},
}
BAD = ("unknown option", "invalid value", "ERROR")


def uci_options(exe):
    p = subprocess.run([exe], input="uci\nisready\nquit\n", capture_output=True, text=True,
                       timeout=120)
    names = set()
    for l in p.stdout.splitlines():
        if l.startswith("option name "):
            rest = l[len("option name "):]
            names.add(rest.split(" type ")[0].strip())
    return names


def one(exe, settings, cmd, timeout=900.0):
    """Fresh process; settings applied one at a time with readyok read after every one."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1, env=env,
                         start_new_session=True)
    out = []
    lock = threading.Lock()

    def pump():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=pump, daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait_until(pred, timeout):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            with lock:
                hit = pred(list(out))
            if hit:
                return hit
            if p.poll() is not None:
                break
            time.sleep(0.004)
        return None

    def ready():
        with lock:
            mark = len(out)
        send("isready")
        return wait_until(lambda o: bool(o[mark:]) and any(
            x.strip() == "readyok" for x in o[mark:]), 120)

    send("uci")
    wait_until(lambda o: any(x.strip() == "uciok" for x in o), 60)
    ready()
    # THREADS 1 + HASH 16 explicitly: the owner's rule is that every score comes from Threads 1,
    # and the pins/sums are quoted at Threads 1, Hash 16. Sent BEFORE the job's own settings.
    for name, value in (("Threads", 1), ("Hash", 16)):
        send("setoption name %s value %s" % (name, value))
        ready()
    bad = []
    for name, value in settings:
        with lock:
            mark = len(out)
        send("setoption name %s value %s" % (name, value))
        ready()
        with lock:
            blk = out[mark:]
        for l in blk:
            if any(b in l for b in BAD):
                bad.append(l)
    with lock:
        mark = len(out)
    send(cmd)
    total = None
    if cmd.startswith("bench"):
        line = wait_until(lambda o: next((x for x in o[mark:]
                                         if x.startswith("info string bench")), None), timeout)
        if line:
            t = line.split()
            if "nodes" in t:
                total = int(t[t.index("nodes") + 1])
    else:
        # `go perft N` prints "nodes <total>" and NO bestmove -- waiting for bestmove hung
        wait_until(lambda o: any(x.startswith("nodes ") for x in o[mark:]), timeout)
        with lock:
            blk = out[mark:]
        for l in blk:
            if l.startswith("nodes "):
                total = int(l.split()[1])
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:
        pass
    return total, bad


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    opts = uci_options(exe)
    report = {"exe": os.path.realpath(exe),
              "sha256": subprocess.run(["sha256sum", exe], capture_output=True,
                                       text=True).stdout.split()[0],
              "option_count": len(opts), "results": {}, "option_missing": []}
    wanted = [n for n, _ in S14 + PC20_EXTRA]
    report["option_missing"] = [n for n in wanted if n not in opts]
    print("exe:", report["exe"], "options:", len(opts))
    print("missing option names:", report["option_missing"] or "none")
    if report["option_missing"]:
        print("FAIL: an option we must set does not exist in this exe; stopping.")
        raise SystemExit(3)

    for regime in ("none", "S14", "PC20"):
        settings = [] if regime == "none" else (S14 if regime == "S14" else S14 + PC20_EXTRA)
        report["results"][regime] = {}
        for cmd, expect in EXPECT[regime].items():
            got, bad = one(exe, settings, cmd)
            ok = got == expect
            report["results"][regime][cmd] = {"expected": expect, "got": got, "match": ok,
                                              "bad_option_lines": bad}
            print("%-6s %-11s expected %-9d got %-9s %s%s" % (
                regime, cmd, expect, got, "MATCH" if ok else "MISMATCH",
                "  BAD:" + bad[0][:50] if bad else ""))
            if bad:
                print("FAIL: the engine refused one of the settings; stopping.")
                raise SystemExit(3)

    allok = all(v["match"] for r in report["results"].values() for v in r.values())
    report["all_match"] = allok
    with open(os.path.join(outdir, "pc_honesty.json"), "w") as f:
        json.dump(report, f, indent=1)
    print()
    print("ALL KNOWN ANSWERS MATCH:", allok)


if __name__ == "__main__":
    main()
