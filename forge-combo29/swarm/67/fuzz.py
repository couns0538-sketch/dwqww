#!/usr/bin/env python3
"""Protocol-boundary fuzz harness for the Forge UCI engine, under ASan+UBSan.

Discipline (see RULES in FUZZ.md):
  * os.read() on non-blocking fds -- never select(), never readline().
  * every wait has a hard deadline; a case that overruns is killed and recorded
    as a HANG rather than being allowed to hold an engine.
  * waits are on `bestmove` (and on `readyok` / `info string`), never on
    `info depth`, which a depth-1 search may emit before doing real work.
  * every reply line is timestamped and attributed to the command write that
    most recently preceded it, so "where did the refusal appear" is measured
    from the protocol stream and not guessed from text order.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time

BESTMOVE_RE = re.compile(r"^bestmove ([a-h][1-8][a-h][1-8][qrbn]?|0000)( ponder [a-h][1-8][a-h][1-8][qrbn]?)?$")
SANITIZER_RE = re.compile(r"(AddressSanitizer|UndefinedBehaviorSanitizer|LeakSanitizer|"
                          r"runtime error:|SUMMARY: .*Sanitizer|ERROR: .*Sanitizer|"
                          r"heap-buffer-overflow|stack-buffer-overflow|use-after-free|"
                          r"SEGV|stack-overflow)")

POLL = 0.004


class Engine:
    """One engine process. Blocking-free reads on both pipes with deadlines."""

    def __init__(self, exe: str, env_extra: dict | None = None):
        env = dict(os.environ)
        env.setdefault("ASAN_OPTIONS", "detect_leaks=0:abort_on_error=0:handle_abort=1")
        env.setdefault("UBSAN_OPTIONS", "print_stacktrace=1:halt_on_error=0")
        if env_extra:
            env.update(env_extra)
        self.p = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=0, env=env,
        )
        self.out_fd = self.p.stdout.fileno()
        self.err_fd = self.p.stderr.fileno()
        os.set_blocking(self.out_fd, False)
        os.set_blocking(self.err_fd, False)
        self.out_buf = b""
        self.err_buf = b""
        self.lines: list[dict] = []      # {"t", "stream", "text"}
        self.writes: list[dict] = []     # {"t", "cmd"}
        self.t0 = time.time()
        self.dead = False

    # -- low level ---------------------------------------------------------
    def _now(self) -> float:
        return time.time() - self.t0

    def _drain(self) -> None:
        for stream, fd, key in (("stdout", self.out_fd, "out_buf"),
                                ("stderr", self.err_fd, "err_buf")):
            buf = getattr(self, key)
            while True:
                try:
                    chunk = os.read(fd, 65536)
                except BlockingIOError:
                    break
                except OSError:
                    chunk = b""
                if not chunk:
                    break
                buf += chunk
            # split complete lines only; a trailing partial line stays buffered
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                self.lines.append({
                    "t": round(self._now(), 4),
                    "stream": stream,
                    "text": raw.decode("utf-8", "replace"),
                })
            setattr(self, key, buf)

    def write(self, data: bytes, label: str | None = None) -> None:
        text = (label if label is not None else data.decode("utf-8", "replace")).rstrip("\n")
        self._drain()
        self.writes.append({"t": round(self._now(), 4), "cmd": text})
        try:
            self.p.stdin.write(data)
            self.p.stdin.flush()
        except (BrokenPipeError, OSError):
            self.dead = True

    def wait_for(self, pred, timeout: float, scan_from: int = 0) -> bool:
        """Pump both fds until pred(line) is true for a line at index>=scan_from."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            self._drain()
            for line in self.lines[scan_from:]:
                if pred(line["text"]):
                    return True
            if self.p.poll() is not None:
                self._drain()
                for line in self.lines[scan_from:]:
                    if pred(line["text"]):
                        return True
                return False
            time.sleep(POLL)
        self._drain()
        for line in self.lines[scan_from:]:
            if pred(line["text"]):
                return True
        return False

    def settle(self, seconds: float) -> None:
        deadline = time.time() + seconds
        while time.time() < deadline:
            self._drain()
            time.sleep(POLL)
        self._drain()

    # -- derived -----------------------------------------------------------
    def mark(self) -> int:
        self._drain()
        return len(self.lines)

    def attribute(self, idx: int) -> str | None:
        """Which command write was the most recent one before this line?"""
        t = self.lines[idx]["t"]
        owner = None
        for w in self.writes:
            if w["t"] <= t + 1e-9:
                owner = w["cmd"]
            else:
                break
        return owner

    def find(self, pattern: str, scan_from: int = 0) -> list[int]:
        rx = re.compile(pattern)
        self._drain()
        return [i for i, l in enumerate(self.lines)
                if i >= scan_from and rx.search(l["text"])]

    def sanitizer_lines(self) -> list[str]:
        self._drain()
        return [l["text"] for l in self.lines
                if l["stream"] == "stderr" or SANITIZER_RE.search(l["text"])]

    def close(self, grace: float = 4.0) -> int | None:
        if self.p.poll() is not None:
            self._drain()
            return self.p.returncode
        try:
            self.p.stdin.write(b"quit\n")
            self.p.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        deadline = time.time() + grace
        while time.time() < deadline:
            self._drain()
            if self.p.poll() is not None:
                self._drain()
                return self.p.returncode
            time.sleep(POLL)
        self.kill()
        return self.p.returncode

    def kill(self) -> None:
        if self.p.poll() is None:
            try:
                self.p.send_signal(signal.SIGKILL)
            except OSError:
                pass
        try:
            self.p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        self._drain()


# ---------------------------------------------------------------------------
# Case model
# ---------------------------------------------------------------------------

class Case:
    """A scripted session.

    steps: list of (bytes, kind)
        kind in {"cmd", "wait_bestmove", "wait_nodes", "wait_ready", "settle", "kill"}
    expect_bestmove: "must" | "may" | "must_not"

    Hang policy. A missing `bestmove` is NOT a hang: an unrestricted `go` is
    supposed to run until `stop`. A hang is a FAILURE OF PROTOCOL LIVENESS --
    the engine stops answering `isready` (wedged search thread, deadlock, or
    dead process). Liveness is measured after every case, and the two outcomes
    are recorded separately as `hang` and `unbounded`.
    """

    def __init__(self, cid, cls, steps, expect_bestmove="may",
                 bestmove_timeout=12.0, ready_timeout=20.0, note="", pattern=""):
        self.cid = cid
        self.cls = cls
        self.steps = steps
        self.expect_bestmove = expect_bestmove
        self.bestmove_timeout = bestmove_timeout
        self.ready_timeout = ready_timeout
        self.note = note
        self.pattern = pattern or "generic"   # harness pattern label

    def run(self, exe: str) -> dict:
        eng = Engine(exe)
        marks: dict[str, int] = {}
        hang = False
        rc = None
        try:
            for data, kind in self.steps:
                if kind == "cmd":
                    eng.write(data)
                    eng.settle(0.30)
                elif kind == "settle":
                    eng.settle(float(data or b"0.5"))
                elif kind == "wait_ready":
                    if data:
                        eng.write(data)
                    ok = eng.wait_for(lambda t: t.strip() == "readyok", self.ready_timeout)
                    marks["ready_seen"] = 1 if ok else 0
                elif kind == "wait_bestmove":
                    if data:
                        eng.write(data)
                    before = eng.mark()
                    ok = eng.wait_for(lambda t: t.startswith("bestmove"), self.bestmove_timeout)
                    marks["bestmove_seen"] = 1 if ok else 0
                    marks["bestmove_at"] = before
                elif kind == "wait_nodes":
                    # `go perft` answers with `nodes N`; it never emits bestmove.
                    if data:
                        eng.write(data)
                    ok = eng.wait_for(lambda t: t.startswith("nodes "), self.bestmove_timeout)
                    marks["nodes_seen"] = 1 if ok else 0
                elif kind == "kill":
                    eng.kill()

            # ---- liveness measurement, before quitting --------------------
            # A missing bestmove only means the search had no limit (that is a
            # legitimate `go`). A HANG is a protocol liveness failure: after
            # `stop`, the engine must still answer `isready` with `readyok`.
            eng.settle(0.35)
            if eng.p.poll() is not None:
                rc = eng.p.returncode
                marks["liveness"] = "process-exited"
            else:
                m = eng.mark()
                eng.write(b"stop\n")
                eng.settle(0.30)
                eng.write(b"isready\n")
                live = eng.wait_for(lambda t: t.strip() == "readyok", 10.0, scan_from=m)
                marks["liveness"] = "responsive" if live else "unresponsive"
                if not live:
                    hang = True
                stopped = eng.find(r"^bestmove", scan_from=m)
                marks["bestmove_after_stop"] = 1 if stopped else 0
                eng.settle(0.20)
                rc = eng.p.poll()
                if rc is None:
                    rc = eng.close()
        except Exception as exc:            # harness must never mask a crash
            rc = None
            marks["harness_error"] = repr(exc)
            eng.kill()
        finally:
            if eng.p.poll() is None:
                eng.kill()

        text_lines = [l for l in eng.lines if l["stream"] == "stdout"]
        san = eng.sanitizer_lines()
        bestmoves = [l["text"] for l in text_lines if l["text"].startswith("bestmove")]

        # placement: for every `info string` diagnostic, which command owned it
        diagnostics = []
        for i, l in enumerate(eng.lines):
            if l["stream"] != "stdout":
                continue
            if l["text"].startswith("info string"):
                diagnostics.append({
                    "text": l["text"],
                    "t": l["t"],
                    "owner": eng.attribute(i),
                    "ordinal": i,
                })

        refusal = [d for d in diagnostics
                   if "invalid FEN" in d["text"] or "illegal move" in d["text"]]

        perft_totals = [l["text"] for l in text_lines if l["text"].startswith("nodes ")]

        # A search that never terminated on its own but answers `stop` and
        # stays live is UNBOUNDED, not hung. Named so the report cannot confuse
        # a missing limit with a wedged engine.
        saw_bestmove_before_stop = marks.get("bestmove_seen") == 1
        unbounded = (marks.get("liveness") == "responsive"
                     and marks.get("bestmove_after_stop") == 1
                     and not saw_bestmove_before_stop)

        return {
            "id": self.cid,
            "cls": self.cls,
            "pattern": self.pattern,
            "note": self.note,
            "expect_bestmove": self.expect_bestmove,
            "exit": rc,
            "hang": hang,
            "liveness": marks.get("liveness"),
            "unbounded": unbounded,
            "sanitizer": san,
            "bestmoves": bestmoves,
            "perft_totals": perft_totals,
            "bestmoves_wellformed": [bool(BESTMOVE_RE.match(b)) for b in bestmoves],
            "illegal_0000": [b for b in bestmoves if b.split()[1:2] == ["0000"]],
            "diagnostics": diagnostics,
            "refusal": refusal,
            "refusal_owner": refusal[0]["owner"] if refusal else None,
            "refusal_present": bool(refusal),
            "line_count": len(text_lines),
            "marks": marks,
            "writes": eng.writes,
            "lines": eng.lines[-400:],
        }


# ---------------------------------------------------------------------------
# Post-case usability probe: a fresh perft 2 from startpos must print `nodes 400`.
# ---------------------------------------------------------------------------

def usability_probe(exe: str) -> dict:
    eng = Engine(exe)
    try:
        eng.write(b"isready\n")
        ready = eng.wait_for(lambda t: t.strip() == "readyok", 20.0)
        eng.write(b"position startpos\ngo perft 2\n")
        got = eng.wait_for(lambda t: t.startswith("nodes "), 25.0)
        rc = eng.close()
    finally:
        if eng.p.poll() is None:
            eng.kill()
    vals = [l["text"] for l in eng.lines if l["text"].startswith("nodes ")]
    return {"readyok": ready, "perft2": vals[-1] if vals else None,
            "ok": ready and bool(vals) and vals[-1].strip() == "nodes 400",
            "exit": rc, "sanitizer": eng.sanitizer_lines()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--cases", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases.py"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None, help="substring filter on class")
    ap.add_argument("--control", action="store_true",
                    help="run the planted-bad-input control instead of the corpus")
    args = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(args.cases)))
    mod = __import__(os.path.basename(args.cases)[:-3])
    cases = mod.build_cases()

    if args.control:
        cases = mod.build_control_cases()

    if args.only:
        cases = [c for c in cases if args.only in c.cls or args.only in c.cid]

    # A duplicate id silently makes two cases indistinguishable in the artifacts
    # and corrupts every cross-run lookup. Refuse rather than run.
    seen = {}
    dupes = []
    for c in cases:
        if c.cid in seen:
            dupes.append(c.cid)
        seen[c.cid] = True
    if dupes:
        print(f"FATAL: duplicate case ids: {sorted(set(dupes))}", file=sys.stderr)
        return 2

    results = []
    t_start = time.time()
    for i, case in enumerate(cases, 1):
        res = case.run(args.exe)
        results.append(res)
        flag = ""
        if res["sanitizer"]:
            flag = " SANITIZER"
        if res["hang"]:
            flag += " HANG"
        if res["exit"] not in (0, None):
            flag += f" EXIT={res['exit']}"
        print(f"[{i:3d}/{len(cases)}] {case.cid:52s} {case.cls:20s}{flag}", flush=True)

    up = usability_probe(args.exe)
    payload = {
        "exe": args.exe,
        "elapsed_s": round(time.time() - t_start, 1),
        "n_cases": len(cases),
        "usability": up,
        "results": results,
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=1)

    n_san = sum(1 for r in results if r["sanitizer"])
    n_hang = sum(1 for r in results if r["hang"])
    n_bad = sum(1 for r in results if r["exit"] not in (0, None))
    n_unb = sum(1 for r in results if r.get("unbounded"))
    print(f"\nran {len(cases)} cases in {payload['elapsed_s']}s: "
          f"sanitizer={n_san} hang={n_hang} unbounded={n_unb} bad_exit={n_bad}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
