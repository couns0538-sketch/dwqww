"""Persistent UCI driver. Every search is read through to `bestmove` before the
next command is written: piping `quit` into a live search makes this engine abort
and fabricate `bestmove a2a3` with zero info lines.

Two protocol facts this driver encodes:
  * `go perft N` ends with a bare `nodes N` line and NO `bestmove`.
  * `bench N` prints one `info string bench depth ... nodes N ...` line.
"""
from __future__ import annotations

import subprocess
import time

DEFAULT_OPTS = {
    "Threads": "1",
    "Hash": "16",
    "MultiPV": "1",
    "Ponder": "false",
    "OwnBook": "false",
}


class Engine:
    def __init__(self, path: str, options: dict | None = None):
        self.path = path
        self.proc = subprocess.Popen(
            [path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1,
        )
        self.banner = []
        self._send("uci")
        self._read_until("uciok")
        opts = dict(DEFAULT_OPTS)
        if options:
            opts.update(options)
        for k, v in opts.items():
            self._send(f"setoption name {k} value {v}")
        self._sync()

    def _send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def _read_until(self, token: str, collect: bool = False) -> list[str]:
        assert self.proc.stdout is not None
        lines = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise RuntimeError(f"{self.path}: closed stdout waiting for {token!r}")
            line = line.rstrip("\n")
            lines.append(line)
            if line.strip() == token:
                return lines

    def _sync(self) -> None:
        self._send("isready")
        self._read_until("readyok")

    def set_position(self, position_cmd: str) -> None:
        self._send(position_cmd)
        self._sync()

    def search(self, go: str, timeout_s: float | None = None) -> dict:
        """Send `go ...` and read to `bestmove`. Returns the whole record.

        `timeout_s` sends UCI `stop` from a watchdog thread and then keeps reading to
        `bestmove`. That is the documented way to end a search early and it leaves the
        engine able to answer the next command. `quit` (or closing stdin) before
        `bestmove` instead makes this engine abort and FABRICATE `bestmove a2a3` with
        zero info lines, which is why the watchdog stops rather than kills.
        """
        self._send(go)
        stop_sent = False
        watchdog = None
        if timeout_s:
            import threading

            def _fire():
                nonlocal stop_sent
                time.sleep(timeout_s)
                stop_sent = True
                try:
                    self._send("stop")
                except Exception:
                    pass

            watchdog = threading.Thread(target=_fire, daemon=True)
            watchdog.start()
        assert self.proc.stdout is not None
        info = []
        try:
            while True:
                line = self.proc.stdout.readline()
                if line == "":
                    raise RuntimeError(f"{self.path}: closed stdout during search")
                line = line.strip()
                if line.startswith("bestmove"):
                    parts = line.split()
                    return {
                        "bestmove": parts[1] if len(parts) > 1 else None,
                        "info": info,
                        "last": info[-1] if info else None,
                        "raw_bestmove": line,
                        "timed_out": stop_sent,
                    }
                if line.startswith("info"):
                    info.append(line)
        finally:
            if watchdog is not None:
                # let the watchdog exit on its own; joining would block for timeout_s
                pass

    def eval_line(self) -> str | None:
        """`eval` prints `info string eval hce H nnue N total T`. Not a search."""
        self._send("eval")
        assert self.proc.stdout is not None
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise RuntimeError("closed stdout reading eval")
            if line.startswith("info string eval"):
                return line.strip()

    def perft(self, depth: int) -> int | None:
        self._send(f"go perft {depth}")
        assert self.proc.stdout is not None
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise RuntimeError("closed stdout in perft")
            if line.startswith("nodes "):
                return int(line.split()[1])

    def quit(self) -> None:
        try:
            self._send("quit")
            self.proc.wait(timeout=15)
        except Exception:
            self.proc.kill()


def parse_info(line: str) -> dict:
    out: dict = {"pv": []}
    toks = line.split()
    i = 1
    while i < len(toks):
        t = toks[i]
        if t == "depth" and i + 1 < len(toks):
            out["depth"] = int(toks[i + 1]); i += 2
        elif t == "seldepth" and i + 1 < len(toks):
            out["seldepth"] = int(toks[i + 1]); i += 2
        elif t == "nodes" and i + 1 < len(toks):
            out["nodes"] = int(toks[i + 1]); i += 2
        elif t == "nps" and i + 1 < len(toks):
            out["nps"] = int(toks[i + 1]); i += 2
        elif t == "time" and i + 1 < len(toks):
            out["time"] = int(toks[i + 1]); i += 2
        elif t == "hashfull" and i + 1 < len(toks):
            out["hashfull"] = int(toks[i + 1]); i += 2
        elif t == "score" and i + 2 < len(toks):
            kind = toks[i + 1]
            val = int(toks[i + 2])
            out["score_kind"] = kind
            out["score"] = val
            out["mate"] = val if kind == "mate" else None
            i += 3
        elif t == "pv":
            out["pv"] = toks[i + 1:]
            break
        else:
            i += 1
    return out
