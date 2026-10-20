#!/usr/bin/env python3
"""Linux-only UCI go-to-worker latency regression. Records original process output.

Compare a frozen engine tree with a *disposable, exactly patched* copy. The
LD_PRELOAD shim delays pthread_create, not the worker's own clock. This script
verifies UCI-visible elapsed accounting; it is not an Elo or forfeit test.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import threading
import time

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run_trial(binary: Path, shim: Path, label: str, command: str, out: Path, delay_ms: int) -> dict:
    env = os.environ.copy()
    env["LD_PRELOAD"] = str(shim)
    env["FORGE_TEST_CREATE_DELAY_MS"] = str(delay_ms)
    q: queue.Queue[tuple[float, str]] = queue.Queue()
    journal = out / f"{label}.jsonl"
    stderr_path = out / f"{label}.stderr"
    with stderr_path.open("xb") as stderr:
        proc = subprocess.Popen([str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=stderr, text=True, bufsize=1, env=env)
        assert proc.stdin is not None and proc.stdout is not None
        def read_stdout() -> None:
            for line in proc.stdout:
                q.put((time.monotonic(), line.rstrip("\r\n")))
        threading.Thread(target=read_stdout, daemon=True).start()
        t0 = time.monotonic()
        lines: list[str] = []
        try:
            with journal.open("x", encoding="utf-8") as log:
                def issue(cmd: str) -> None:
                    proc.stdin.write(cmd + "\n")
                    proc.stdin.flush()
                    log.write(json.dumps({"event": "send", "clock_s": time.monotonic()-t0, "text": cmd}) + "\n")
                    log.flush()

                def until(predicate, timeout_s: float) -> str:
                    deadline = time.monotonic() + timeout_s
                    while time.monotonic() < deadline:
                        try:
                            stamp, line = q.get(timeout=min(0.2, max(0.001, deadline-time.monotonic())))
                        except queue.Empty:
                            if proc.poll() is not None and q.empty():
                                raise RuntimeError(f"exited {proc.returncode} before expected UCI response")
                            continue
                        lines.append(line)
                        log.write(json.dumps({"event": "recv", "clock_s": stamp-t0, "text": line}) + "\n")
                        log.flush()
                        if predicate(line):
                            return line
                    raise TimeoutError(f"timeout waiting for UCI response ({label})")

                issue("uci")
                until(lambda s: s == "uciok", 8.0)
                issue("isready")
                until(lambda s: s == "readyok", 8.0)
                issue("position startpos")
                sent_go = time.monotonic()
                issue(command)
                until(lambda s: s.startswith("bestmove "), 8.0)
                best_wall_ms = round((time.monotonic()-sent_go)*1000, 3)
                issue("quit")
            proc.wait(timeout=5)
            if proc.returncode != 0:
                raise RuntimeError(f"engine abnormal exit {proc.returncode}")
            info = next((s for s in lines if s.startswith("info depth ") and re.search(r"\btime \d+", s)), None)
            if info is None:
                raise RuntimeError("no complete depth/time information before bestmove")
            m = re.search(r"\btime (\d+)\b", info)
            assert m is not None
            best = next((s for s in reversed(lines) if s.startswith("bestmove ")), None)
            if best is None or not re.fullmatch(r"bestmove (?:[a-h][1-8][a-h][1-8][qrbn]?|0000)(?: ponder [a-h][1-8][a-h][1-8][qrbn]?)?", best):
                raise RuntimeError(f"invalid bestmove UCI response: {best}")
            return {"label": label, "command": command, "first_info_time_ms": int(m.group(1)),
                    "bestmove_wall_ms": best_wall_ms, "bestmove": best, "exit": proc.returncode,
                    "journal_sha256": digest(journal), "stderr_sha256": digest(stderr_path)}
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--shim", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--delay-ms", type=int, default=440)
    args = parser.parse_args()
    if not 200 <= args.delay_ms <= 1000:
        parser.error("delay must be 200..1000 ms")
    args.out.mkdir(parents=True, exist_ok=True)
    paths = (args.baseline.resolve(), args.candidate.resolve(), args.shim.resolve())
    if not all(p.is_file() for p in paths):
        parser.error("baseline, candidate, and shim must exist")
    results = []
    try:
        results.append(run_trial(paths[0], paths[2], "baseline_timed", "go movetime 1200", args.out, args.delay_ms))
        results.append(run_trial(paths[1], paths[2], "candidate_timed", "go movetime 1200", args.out, args.delay_ms))
        results.append(run_trial(paths[1], paths[2], "candidate_depth", "go depth 1", args.out, args.delay_ms))
        base, candidate, depth = results
        # A host pause could invalidate these separation thresholds. Fail closed.
        ok = (base["first_info_time_ms"] < args.delay_ms//2 and
              candidate["first_info_time_ms"] >= args.delay_ms-60 and
              depth["first_info_time_ms"] < args.delay_ms//2)
        status = "PASS" if ok else "INCONCLUSIVE_OR_FAIL"
    except Exception as exc:
        status = "FAIL"
        error = repr(exc)
    else:
        error = None
    summary = {"schema": 1, "utc": datetime.now(timezone.utc).isoformat(),
               "status": status, "error": error, "delay_ms": args.delay_ms,
               "binary_shas": {"baseline": digest(paths[0]), "candidate": digest(paths[1]), "shim": digest(paths[2])},
               "results": results, "kind": "UCI wall-clock origin only; not fastchess or Elo"}
    (args.out/"result.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if status == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
