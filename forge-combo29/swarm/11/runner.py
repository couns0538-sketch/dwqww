#!/usr/bin/env python3
"""runner.py — the one FEN harness for seat 11 (area 1).

Protocol per case (exactly as the brief demands):
  start/reuse a process for up to BATCH cases,
  send "position fen <FEN>", then "isready", read EVERY line up to "readyok",
  record the answer lines (a refusal is the measurement in area 1),
  then "go depth D", wait for "bestmove",
  count sanitizer lines from stderr.
A crash kills the process; the batch runner restarts it and counts the crash.

Every output file is beside a .meta file holding: the exe path it STARTED, its
sha256, its `id name`, every option line sent, the sanitizer/TSAN env used.

usage: runner.py --exe E --out DIR --cases TSV [--batch 500] [--depth 2]
                 [--timeout 20] [--setoption "Threads 1" ...]
cases TSV columns: id <TAB> fen-or-COMMAND <TAB> note
"""
import argparse, hashlib, json, os, queue, subprocess, sys, threading, time

SAN_PATTERNS = ("ERROR: AddressSanitizer", "runtime error:", "SUMMARY: ",
                "ERROR: LeakSanitizer", "WARNING: ThreadSanitizer")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Engine:
    def __init__(self, exe, depth, timeout, start_options):
        self.exe, self.depth, self.timeout = exe, depth, timeout
        self.start_options = start_options
        self.env = dict(os.environ)
        self.env.pop("TSAN_OPTIONS", None)
        self.env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0:symbolize=1"
        self.env["UBSAN_OPTIONS"] = "print_stacktrace=1:halt_on_error=1"
        self.env.pop("LSAN_OPTIONS", None)
        self.proc = None
        self._reader = None
        self._queue = None
        self.idname = ""
        self.stderr_path = None
        self.san_lines = []

    def start(self, stderr_path):
        self.stderr_path = stderr_path
        self.err = open(stderr_path, "a", buffering=1)
        self.proc = subprocess.Popen(
            [self.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.err, text=True, bufsize=1, env=self.env)
        self.send("uci")
        lines = self.read_until("uciok")
        self.idname = next((l[7:].strip() for l in lines if l.startswith("id name")), "")
        for opt in self.start_options:
            self.send("setoption name " + opt)
            self.drain_readyok()
        self.send("ucinewgame")
        self.drain_readyok()
        return lines

    def send(self, line):
        try:
            self.proc.stdin.write(line + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, ValueError):
            pass

    def readline(self, deadline):
        if time.monotonic() > deadline:
            raise TimeoutError("read timeout")
        # stdout.readline() blocks with no timeout, so a hung engine would hang the harness.
        # A reader thread fills a queue; we wait on the queue with the real deadline.
        if self._reader is None:
            self._queue = queue.Queue()
            def pump(stream, q):
                try:
                    for ln in iter(stream.readline, ""):
                        q.put(ln)
                except Exception:
                    pass
                q.put(None)          # EOF sentinel
            self._reader = threading.Thread(target=pump, args=(self.proc.stdout, self._queue),
                                            daemon=True)
            self._reader.start()
        remaining = max(0.0, deadline - time.monotonic())
        try:
            line = self._queue.get(timeout=remaining)
        except queue.Empty:
            raise TimeoutError("engine produced no line before the deadline (HANG)")
        if line is None:
            raise EOFError("engine closed stdout")
        return line.rstrip("\n")

    def read_until(self, token, timeout=None):
        timeout = timeout or self.timeout
        deadline = time.monotonic() + timeout
        out = []
        while True:
            line = self.readline(deadline)
            out.append(line)
            if line.strip() == token:
                return out

    def drain_readyok(self):
        self.send("isready")
        return self.read_until("readyok")

    def kill(self):
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
        try:
            self.proc.wait(timeout=5)
        except Exception:
            pass
        if self.proc:
            self.proc.stdin.close()
        self.err.close()
        self.collect_san()

    def collect_san(self):
        if not self.stderr_path or not os.path.exists(self.stderr_path):
            return
        with open(self.stderr_path, errors="replace") as f:
            for line in f:
                if any(p in line for p in SAN_PATTERNS):
                    if line.rstrip() not in self.san_lines:
                        self.san_lines.append(line.rstrip())

    def case(self, fen):
        """Returns dict: answer lines, bestmove, refused reason, elapsed."""
        t0 = time.monotonic()
        if fen.startswith("!"):          # raw command instead of a FEN (control cases)
            self.send(fen[1:])
        else:
            self.send("position fen " + fen)
        answer = self.drain_readyok()
        refused = None
        for line in answer:
            s = line.strip()
            for tag in ("invalid FEN", "unknown option", "invalid value", "illegal move"):
                if tag in s:
                    refused = s
        rec = {"fen": fen, "answer": answer, "refused": refused, "bestmove": None}
        if refused is None:
            self.send("go depth %d" % self.depth)
            try:
                lines = self.read_until_bestmove()
                bm = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
                rec["bestmove"] = bm
            except (TimeoutError, EOFError) as e:
                rec["bestmove"] = "TIMEOUT" if isinstance(e, TimeoutError) else "EOF"
        else:
            # a refused position: still confirm the engine answers
            rec["bestmove"] = "refused"
        rec["elapsed"] = round(time.monotonic() - t0, 4)
        self.collect_san()
        rec["san"] = list(self.san_lines)
        return rec

    def read_until_bestmove(self):
        deadline = time.monotonic() + self.timeout
        out = []
        while True:
            line = self.readline(deadline)
            out.append(line)
            if line.startswith("bestmove"):
                return out


def write_meta(path, eng, exe, options, depth, extra):
    meta = {
        "exe_started": os.path.abspath(exe),
        "sha256": sha256(exe),
        "id_name": eng.idname,
        "option_lines_sent": ["setoption name " + o for o in options],
        "go_line": "go depth %d" % depth,
        "env_sanitizer": {k: eng.env.get(k) for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")},
        "nm_asan": extra.get("nm_asan"),
        "nm_ubsan": extra.get("nm_ubsan"),
    }
    with open(path, "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")


def nm_count(exe, sym):
    try:
        out = subprocess.run(["nm", "-C", exe], capture_output=True, text=True, timeout=300).stdout
        return sum(1 for l in out.splitlines() if sym in l)
    except Exception:
        return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cases", required=True)
    ap.add_argument("--batch", type=int, default=500)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--setoption", action="append", default=[])
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    cases = []
    with open(args.cases) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            cid, fen = parts[0], parts[1]
            note = parts[2] if len(parts) > 2 else ""
            cases.append({"id": cid, "fen": fen, "note": note})

    exe_abs = os.path.abspath(args.exe)
    extra = {"nm_asan": nm_count(exe_abs, "__asan_"), "nm_ubsan": nm_count(exe_abs, "__ubsan_")}
    if "asan" in exe_abs and extra["nm_asan"] <= 0:
        print("REFUSING: exe named asan has 0 __asan_ symbols", file=sys.stderr)
        return 2

    results = []
    crashes = 0
    starts = 0
    stderr_path = os.path.join(args.out, "engine.stderr")
    open(stderr_path, "w").close()

    def new_engine():
        nonlocal starts
        e = Engine(exe_abs, args.depth, args.timeout, args.setoption)
        e.start(stderr_path)
        starts += 1
        if starts == 1:
            write_meta(os.path.join(args.out, "runner.meta"), e, exe_abs, args.setoption, args.depth, extra)
        return e

    eng = new_engine()
    used_in_batch = 0
    for c in cases:
        if used_in_batch >= args.batch:
            eng.kill()
            eng = new_engine()
            used_in_batch = 0
        try:
            rec = eng.case(c["fen"])
        except (EOFError, TimeoutError) as exc:
            crashes += 1
            rec = {"fen": c["fen"], "answer": [], "refused": None,
                   "bestmove": "CRASH:" + type(exc).__name__, "san": list(eng.san_lines)}
            try:
                eng.kill()
            except Exception:
                pass
            eng = new_engine()
            used_in_batch = 0
        rec.update({"id": c["id"], "note": c["note"]})
        results.append(rec)
        used_in_batch += 1
        if rec.get("san"):
            # a sanitizer line means this process is not trustworthy; restart it
            try:
                eng.kill()
            except Exception:
                pass
            eng = new_engine()
            used_in_batch = 0
    try:
        eng.send("quit")
        eng.proc.wait(timeout=5)
    except Exception:
        pass
    try:
        eng.kill()
    except Exception:
        pass

    with open(os.path.join(args.out, "results.jsonl"), "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    summary = {
        "cases": len(results),
        "process_starts": starts,
        "crashes": crashes,
        "sanitizer_lines": sum(len(r.get("san") or []) for r in results),
        "nm_asan": extra["nm_asan"], "nm_ubsan": extra["nm_ubsan"],
        "exe": exe_abs, "depth": args.depth,
    }
    with open(os.path.join(args.out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    sys.exit(main())
