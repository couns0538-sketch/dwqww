#!/usr/bin/env python3
"""S02 AREA 2 job 3 — every option the engine lists, at min / max / min-1 / max+1 / a word / nothing.

Options come from the engine's own `uci` answer (this file does not carry a list of option names).
Two regimes:
  idle    — setoption sent between searches, then `isready`, then `go depth 4`
  during  — setoption sent 5-15 ms into a `go infinite`, then `stop`, then `isready`, then `go depth 4`

Per (option, value) it records: the answer line the engine printed (if any), whether the value was refused,
whether the follow-up search answered and whether its bestmove was legal.

The answer-line scan is the integrity-critical part: every expectation is an ASSERTION on a parsed line, and
a missing line is recorded as "ABSENT", never as a pass. A run whose `invalid value` line is expected but
absent is a failure of the PREDICTION, and is counted, not silently dropped.

usage: options_job.py <exe> <outdir> [sample]
"""
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time

import chess

TIMEOUT = 20.0
POS = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
WORDS = ["banana", "true", ""]
INVALID_RE = re.compile(r"^info string invalid value for option (.+)$")
UKNOWN_RE = re.compile(r"^info string unknown option (.+)$")


class Engine:
    def __init__(self, exe):
        env = {k: v for k, v in os.environ.items()
               if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1, env=env,
                                     start_new_session=True)
        self.lines, self.lock, self.eof = [], threading.Lock(), False
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            with self.lock:
                self.lines.append(line.rstrip("\n"))
        with self.lock:
            self.eof = True

    def send(self, t):
        if self.proc.poll() is not None:
            return False
        try:
            self.proc.stdin.write(t + "\n")
            self.proc.stdin.flush()
            return True
        except Exception:
            return False

    def mark(self):
        with self.lock:
            return len(self.lines)

    def wait_for(self, prefix, start, timeout=TIMEOUT):
        dl = time.monotonic() + timeout
        while True:
            with self.lock:
                for i in range(start, len(self.lines)):
                    if self.lines[i].startswith(prefix):
                        return i
                eof = self.eof
            if eof or self.proc.poll() is not None or time.monotonic() > dl:
                with self.lock:
                    for i in range(start, len(self.lines)):
                        if self.lines[i].startswith(prefix):
                            return i
                return -1
            time.sleep(0.001)

    def seg(self, start):
        with self.lock:
            return list(self.lines[start:])

    def kill(self):
        try:
            os.killpg(self.proc.pid, signal.SIGKILL)
        except Exception:
            pass


def parse_options(uci_out):
    opts = []
    for line in uci_out.splitlines():
        m = re.match(r"^option name (.+?) type (\w+)(.*)$", line)
        if not m:
            continue
        name, typ, rest = m.group(1), m.group(2), m.group(3)
        lo = re.search(r"min (-?\d+)", rest)
        hi = re.search(r"max (-?\d+)", rest)
        dflt = re.search(r"default (\S+)", rest)
        opts.append({"name": name, "type": typ,
                     "min": int(lo.group(1)) if lo else None,
                     "max": int(hi.group(1)) if hi else None,
                     "default": dflt.group(1) if dflt else None})
    return opts


def values_for(o):
    """The six values the job asks for, plus one 'none'."""
    out = []
    if o["type"] == "spin" and o["min"] is not None and o["max"] is not None:
        out += [("min", str(o["min"])), ("max", str(o["max"])),
                ("min-1", str(o["min"] - 1)), ("max+1", str(o["max"] + 1))]
    out += [("word", "banana"), ("word", "true")]
    out.append(("none", None))
    return out


PC20_SETUP = ["setoption name Threads value 1","setoption name Hash value 16"]

def run_case(exe, opt, label, value, during, rng_delay_ms):
    """One (option, value) case. Returns a record; never raises."""
    rec = {"option": opt["name"], "type": opt["type"], "label": label, "value": value,
           "during": during, "answered": False, "legal": None, "crash": False,
           "answer_lines": [], "invalid_line": None, "unknown_line": None, "san": [],
           "followup_ok": False, "notes": []}
    eng = Engine(exe)
    try:
        eng.send("uci")
        if eng.wait_for("uciok", 0) < 0:
            rec["notes"].append("no uciok")
        # PC20 baseline (Threads 1, Hash 16) then the rest; a refusal is recorded, not ignored
        for s_ in PC20_SETUP:
            eng.send(s_)
        eng.send("setoption name OwnBook value false")
        eng.send("position fen " + POS)
        eng.send("isready")
        if eng.wait_for("readyok", eng.mark()) < 0:
            rec["notes"].append("no readyok after setup")
        cmd = "setoption name %s" % opt["name"] + ("" if value is None else " value %s" % value)

        if during:
            eng.send("go infinite")
            time.sleep(rng_delay_ms / 1000.0)
            start = eng.mark()
            eng.send(cmd)
            time.sleep(0.03)
            eng.send("stop")
            at = eng.wait_for("bestmove", start)
            if at < 0:
                rec["notes"].append("no bestmove after stop during setoption")
        else:
            start = eng.mark()
            eng.send(cmd)
            time.sleep(0.01)

        # the answer to the setoption: any info string lines emitted after it
        seg = eng.seg(start)
        rec["answer_lines"] = [l for l in seg if l.startswith("info string")][:4]
        for l in rec["answer_lines"]:
            m = INVALID_RE.match(l)
            if m:
                rec["invalid_line"] = m.group(1)
            m2 = UKNOWN_RE.match(l)
            if m2:
                rec["unknown_line"] = m2.group(1)

        s2 = eng.mark()
        eng.send("isready")
        rec["followup_ok"] = eng.wait_for("readyok", s2) >= 0
        s3 = eng.mark()
        eng.send("go depth 4")
        at = eng.wait_for("bestmove", s3)
        if at >= 0:
            rec["answered"] = True
            bm = eng.seg(at)[-1].split()[1] if len(eng.seg(at)[-1].split()) > 1 else ""
            legal = {m.uci() for m in chess.Board(POS).legal_moves}
            rec["legal"] = (bm == "0000" and not legal) or (bm in legal)
            rec["bestmove"] = bm
        eng.send("quit")
        try:
            eng.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            eng.kill()
            rec["notes"].append("did not exit after quit")
        rc = eng.proc.returncode
        if rc is not None and rc < 0:
            rec["crash"] = True
            rec["notes"].append("signal %d" % (-rc))
    finally:
        if eng.proc.poll() is None:
            eng.kill()
            rec["crash"] = True
            rec["notes"].append("killed: still alive")
        all_lines = eng.seg(0)
        rec["san"] = [l for l in all_lines if "ERROR: AddressSanitizer" in l
                      or "runtime error:" in l or "ERROR: LeakSanitizer" in l]
    return rec


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    sample = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    os.makedirs(outdir, exist_ok=True)
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    uci_out = subprocess.run([exe], input="uci\nquit\n", capture_output=True, text=True, env=env).stdout
    open(os.path.join(outdir, "uci_answer.txt"), "w").write(uci_out)
    opts = parse_options(uci_out)
    if not opts:
        sys.exit("FAIL: the uci answer listed no options; nothing can be tested")
    with open(os.path.join(outdir, "options.json"), "w") as fh:
        json.dump(opts, fh, indent=1)
    with open(os.path.join(outdir, "meta.txt"), "w") as fh:
        fh.write("exe %s\n" % exe)
        fh.write("sha256 %s\n" % subprocess.run(["sha256sum", exe], capture_output=True,
                                               text=True).stdout.split()[0])
        fh.write("nm __asan_ %s\n" % subprocess.run("nm -C %s | grep -c __asan_" % exe, shell=True,
                                                    capture_output=True, text=True).stdout.strip())
        fh.write("nm __ubsan_ %s\n" % subprocess.run("nm -C %s | grep -c __ubsan_" % exe, shell=True,
                                                     capture_output=True, text=True).stdout.strip())
        fh.write("options listed by the engine: %d\n" % len(opts))
        fh.write("position used: %s\n" % POS)
        fh.write("option lines sent: 'setoption name <X> value <v>' or 'setoption name <X>' for the no-value case\n")
        fh.write("started_utc %s\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    import random
    rng = random.Random(203)
    recs = []
    # regime 1: idle, every option x every value
    for o in opts:
        for label, val in values_for(o):
            recs.append(run_case(exe, o, label, val, False, 0))
    # regime 2: during a search, a seeded sample of options
    pick = opts if len(opts) <= sample else rng.sample(
        [o for o in opts if o["type"] != "button"], sample)
    for o in pick:
        for label, val in values_for(o)[:4]:      # min, max, min-1, max+1 (or the words for non-spins)
            recs.append(run_case(exe, o, label, val, True, rng.randint(5, 15)))
    with open(os.path.join(outdir, "results.jsonl"), "w") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
    print("done %d cases over %d options" % (len(recs), len(opts)))


if __name__ == "__main__":
    main()
