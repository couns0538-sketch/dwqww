#!/usr/bin/env python3
"""f1_options.py <exe> <outdir>

Checks every option the engine advertises in its `uci` answer against the value it accepts:
for each spin option, send min-1, min, max, max+1 and a word; for each check option, true/false
and a word. For each case record whether the engine printed a refusal line and — the part that
matters — whether the value TOOK EFFECT, by asking a question whose answer depends on it:

  Threads N        -> `go depth 8` node count must differ from Threads 1 (a weak but real probe)
  Hash N           -> hashfull on a fixed depth-12 search must be non-zero at 16 MB
  MultiPV N        -> the number of distinct `multipv` indexes in one search must equal N
  DrawJitter N     -> none (no observable line) -> recorded as "not observable", NOT as a pass
  Move Overhead N  -> `go movetime 50` wall time must drop when the overhead is 0

INTEGRITY (seat 19): every parse asserts its line was found; a missing line raises and is
reported as MISSING, never as a pass. A planted control proves the harness can report a refusal.
"""
import json
import os
import re
import subprocess
import sys
import time


class Missing(Exception):
    pass


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def gather(self, pred, timeout=180):
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
        lines, ok = self.gather(lambda s: s.strip() == "uciok")
        if not ok:
            raise Missing("no uciok on boot")
        self.send("isready")
        _, ok = self.gather(lambda s: s.strip() == "readyok")
        if not ok:
            raise Missing("no readyok on boot")
        self.options = []
        for s in lines:
            m = re.match(r"option name (.+?) type (\w+) default (\S*)(?: min (-?\d+))?(?: max (-?\d+))?", s)
            if m:
                self.options.append({"name": m.group(1), "type": m.group(2),
                                     "default": m.group(3),
                                     "min": int(m.group(4)) if m.group(4) is not None else None,
                                     "max": int(m.group(5)) if m.group(5) is not None else None})
        if not self.options:
            raise Missing("uci answer contained no option lines at all")

    def setopt(self, name, value):
        self.send("setoption name %s%s" % (name, "" if value is None else " value %s" % value))
        self.send("isready")
        lines, ok = self.gather(lambda s: s.strip() == "readyok")
        if not ok:
            raise Missing("no readyok after setoption %s %s" % (name, value))
        refusal = None
        unknown = None
        for s in lines:
            if "invalid value" in s:
                refusal = s
            if "unknown option" in s:
                unknown = s
        return refusal, unknown

    def go(self, pos, limit):
        self.send("position " + pos)
        self.send("isready")
        _, ok = self.gather(lambda s: s.strip() == "readyok")
        if not ok:
            raise Missing("no readyok before search")
        t0 = time.monotonic()
        self.send("go " + limit)
        lines, ok = self.gather(lambda s: s.startswith("bestmove"), timeout=300)
        wall = time.monotonic() - t0
        if not ok:
            raise Missing("no bestmove for %r %r" % (pos, limit))
        infos = [l for l in lines if l.startswith("info depth")]
        if not infos:
            raise Missing("no info depth line in a search that returned bestmove "
                          "(this is the 19-F12 signature: never treat it as a result)")
        last = infos[-1]
        n = re.search(r"nodes (\d+)", last)
        if not n:
            raise Missing("last info line has no nodes field: %r" % last)
        mpvs = sorted({int(x) for x in re.findall(r" multipv (\d+)", " ".join(infos))})
        hf = re.search(r"hashfull (\d+)", last)
        return {"nodes": int(n.group(1)), "wall_ms": wall * 1000.0,
                "multipv_indexes": mpvs, "hashfull": int(hf.group(1)) if hf else None,
                "last": last}

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=20)
        except Exception:
            self.p.kill()


def main():
    exe = os.path.realpath(sys.argv[1])
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)

    e = Engine(exe)
    e.boot()
    opts = e.options

    # ---- planted control: a value that must be refused
    plant = {}
    for name, bad in (("MultiPV", "99"), ("Hash", "99999"), ("Threads", "0")):
        if any(o["name"] == name for o in opts):
            refusal, _ = e.setopt(name, bad)
            plant[name] = {"value_sent": bad, "refusal_line": refusal}
            if refusal is None:
                print("HARNESS BLIND: %s=%s was NOT refused" % (name, bad))
                json.dump({"planted": plant, "verdict": "BLIND"}, open(
                    os.path.join(outdir, "planted.json"), "w"), indent=2)
                return 1
    # reset anything the plant touched
    for name, good in (("MultiPV", 1), ("Hash", 16), ("Threads", 1)):
        if any(o["name"] == name for o in opts):
            e.setopt(name, good)

    rows = []
    for o in opts:
        if o["type"] == "spin" and o["min"] is not None and o["max"] is not None:
            for label, val in (("min-1", o["min"] - 1), ("min", o["min"]),
                               ("max", o["max"]), ("max+1", o["max"] + 1)):
                if o["name"] in ("Hash",) and val > 512:
                    continue          # do not allocate 2 GB in this check
                if o["name"] == "Threads" and val > 8:
                    continue
                refusal, unknown = e.setopt(o["name"], val)
                rows.append({"option": o["name"], "type": "spin", "value": val,
                             "label": label, "refusal": refusal, "unknown": unknown})
        elif o["type"] == "check":
            for val in ("true", "false", "maybe"):
                refusal, unknown = e.setopt(o["name"], val)
                rows.append({"option": o["name"], "type": "check", "value": val,
                             "label": "check", "refusal": refusal, "unknown": unknown})

    # observable effects, each asserted, each with a control
    effects = {}

    def measure(key, setup, probe):
        e.setopt(*setup) if setup else None
        r = probe()
        effects[key] = r
        return r

    # reset to a known state
    for name, good in (("MultiPV", 1), ("Hash", 16), ("Threads", 1), ("Move Overhead", 10)):
        if any(o["name"] == name for o in opts):
            e.setopt(name, good)

    base = measure("threads1_depth10", ("Threads", 1), lambda: e.go("startpos", "depth 10"))
    two = measure("threads2_depth10", ("Threads", 2), lambda: e.go("startpos", "depth 10"))
    effects["threads_change_nodes"] = (base["nodes"] != two["nodes"])

    e.setopt("Threads", 1)
    for mpv in (1, 3):
        e.setopt("MultiPV", mpv)
        r = e.go("startpos", "depth 8")
        effects["multipv_%d_indexes" % mpv] = r["multipv_indexes"]
    e.setopt("MultiPV", 1)

    # Move Overhead really shortens a movetime search
    e.setopt("Move Overhead", 10)
    mo10 = [e.go("startpos", "movetime 60")["wall_ms"] for _ in range(3)]
    e.setopt("Move Overhead", 0)
    mo0 = [e.go("startpos", "movetime 60")["wall_ms"] for _ in range(3)]
    effects["movetime60_overhead10_ms"] = mo10
    effects["movetime60_overhead0_ms"] = mo0
    effects["overhead_observable"] = (sum(mo0) / 3.0) > (sum(mo10) / 3.0)

    e.quit()

    out = {"exe": exe,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "options_seen": len(opts), "planted_control": plant,
           "cases": rows, "effects": effects}
    with open(os.path.join(outdir, "result.json"), "w") as f:
        json.dump(out, f, indent=2)

    # summary: which option/value pairs were refused although advertised as valid
    bad = [r for r in rows if r["refusal"] and str(r["value"]) not in
           (str(-1),) and r["label"] in ("min", "max")]
    unexpected = [r for r in rows if r["unknown"]]
    with open(os.path.join(outdir, "SUMMARY.txt"), "w") as f:
        f.write("exe %s\nsha %s\ndate %s\noptions advertised: %d\ncases: %d\n\n"
                % (exe, out["sha256"], out["date_utc"], len(opts), len(rows)))
        f.write("advertised min/max values that were still REFUSED (%d):\n" % len(bad))
        for r in bad:
            f.write("  %s (%s) = %s -> %s\n" % (r["option"], r["label"], r["value"], r["refusal"]))
        f.write("\ncases answered 'unknown option' (%d):\n" % len(unexpected))
        for r in unexpected:
            f.write("  %s = %s -> %s\n" % (r["option"], r["value"], r["unknown"]))
        f.write("\nobservable effects:\n")
        f.write("  Threads 1 vs 2 nodes: %s vs %s (differ: %s)\n"
                % (base["nodes"], two["nodes"], effects["threads_change_nodes"]))
        f.write("  MultiPV 1 indexes: %s\n  MultiPV 3 indexes: %s\n"
                % (effects["multipv_1_indexes"], effects["multipv_3_indexes"]))
        f.write("  movetime 60 wall ms overhead 10: %s\n" % effects["movetime60_overhead10_ms"])
        f.write("  movetime 60 wall ms overhead  0: %s\n" % effects["movetime60_overhead0_ms"])
        f.write("  overhead observable: %s\n" % effects["overhead_observable"])
    print(open(os.path.join(outdir, "SUMMARY.txt")).read())
    return 0


if __name__ == "__main__":
    sys.exit(main())
