"""Minimal persistent UCI driver.

Two traps this exists to avoid, both documented by earlier seats:
  * sending `quit` (or closing stdin) before reading `bestmove` makes the engine
    abort and print a fabricated `bestmove a2a3` with zero info lines;
  * every search must therefore be read through to `bestmove` before the next
    command is written.
"""
from __future__ import annotations

import subprocess
import threading


class Engine:
    def __init__(self, path: str, options: dict[str, str] | None = None):
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._send("uci")
        self._read_until("uciok")
        opts = {"Threads": "1", "Hash": "16", "OwnBook": "false", "Ponder": "false",
                "MultiPV": "1"}
        if options:
            opts.update(options)
        for name, value in opts.items():
            self._send(f"setoption name {name} value {value}")
        self._sync()

    def _send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def _read_until(self, token: str) -> list[str]:
        assert self.proc.stdout is not None
        lines = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise RuntimeError(f"{self.path}: engine closed stdout while waiting for {token!r}")
            line = line.strip()
            lines.append(line)
            if line.split(" ")[0] == token or line == token:
                return lines

    def _sync(self) -> None:
        self._send("isready")
        self._read_until("readyok")

    def search(self, position_cmd: str, go: str) -> dict:
        """Run one search. `position_cmd` is a full `position ...` line."""
        self._send(position_cmd)
        self._sync()
        self._send(go)
        assert self.proc.stdout is not None
        info = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise RuntimeError(f"{self.path}: engine closed stdout during search")
            line = line.strip()
            if line.startswith("bestmove"):
                parts = line.split()
                return {
                    "bestmove": parts[1] if len(parts) > 1 else None,
                    "ponder": parts[3] if len(parts) > 3 and parts[2] == "ponder" else None,
                    "info": info,
                    "last_info": info[-1] if info else None,
                    "bestmove_line": line,
                }
            if line.startswith("info"):
                info.append(line)

    def quit(self) -> None:
        try:
            self._send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def parse_info(line: str) -> dict:
    """Parse one `info ...` line into the fields the harness needs."""
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
        elif t == "score" and i + 2 < len(toks):
            kind = toks[i + 1]
            val = int(toks[i + 2])
            out["score_kind"] = kind
            out["score"] = val
            out["cp"] = val * 100 if kind == "mate" else val
            out["mate"] = val if kind == "mate" else None
            i += 3
        elif t == "pv":
            out["pv"] = toks[i + 1:]
            break
        else:
            i += 1
    return out
