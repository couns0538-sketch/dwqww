#!/usr/bin/env python3
"""UCI driver for the switch audit.

Built around the harness traps rather than after them:

* No piped stdin. A pipe that hits EOF while a search is running aborts the
  search and the engine fabricates a `bestmove` (trap 3a). This driver keeps a
  live pipe, sends `stop`, and waits for `bestmove` with a timeout on
  non-blocking reads. `quit` is the last thing it ever sends.
* Both reply streams are accumulated and scanned, not read-and-discarded
  (trap 6: the `invalid FEN` diagnostic arrives on the `position` reply, which
  the normal `isready`-after-`position` pattern swallows).
* Every FEN is validated by python-chess BEFORE it is sent, and the engine's own
  acceptance is asserted separately, because reference validity and engine
  acceptance are different gates (trap 3b).
* Every search asserts it produced at least one `info depth` line, so a
  fabricated bestmove is a failure rather than a datum (trap 3a detector).
* The configuration is asserted from the engine's own `uci` reply, not from the
  name of the arm (trap 15).
"""

from __future__ import annotations

import os
import re
import select
import subprocess
import time

INFO_DEPTH = re.compile(r"^info depth (\d+)\b(.*)$")
SCORE_CP = re.compile(r"\bscore cp (-?\d+)")
SCORE_MATE = re.compile(r"\bscore mate (-?\d+)")
NODES = re.compile(r"\bnodes (\d+)")
BESTMOVE = re.compile(r"^bestmove (\S+)")


class EngineError(RuntimeError):
    pass


class Engine:
    def __init__(self, path: str, options: dict[str, str] | None = None,
                 threads: int = 1, hash_mb: int = 16, timeout: float = 60.0) -> None:
        self.path = path
        self.timeout = timeout
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            bufsize=0,
        )
        self.buf = b""
        self.log: list[str] = []
        self.send("uci")
        self.options = self._read_until(lambda lines: any(l.startswith("uciok") for l in lines))
        self.assert_option("Threads")
        self.assert_option("Hash")
        self.assert_option("UseNNUE")
        self.set_option("Threads", str(threads))
        self.set_option("Hash", str(hash_mb))
        # OwnBook false everywhere: a book move has no info depth line and would
        # look like a fabricated bestmove.
        self.set_option("OwnBook", "false")
        self.set_option("UseNNUE", "true")
        if options:
            for name, value in options.items():
                self.set_option(name, value)
        self.isready()

    # ------------------------------------------------------------- plumbing

    def send(self, line: str) -> None:
        self.log.append(">> " + line)
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def _read_line(self, deadline: float) -> str | None:
        while b"\n" not in self.buf:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            ready, _, _ = select.select([self.proc.stdout], [], [], min(remaining, 0.2))
            if not ready:
                continue
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if not chunk:
                return None
            self.buf += chunk
        line, _, self.buf = self.buf.partition(b"\n")
        text = line.decode("utf-8", "replace").rstrip("\r")
        self.log.append("<< " + text)
        return text

    def _read_until(self, stop, timeout: float | None = None) -> list[str]:
        deadline = time.monotonic() + (self.timeout if timeout is None else timeout)
        lines: list[str] = []
        while True:
            line = self._read_line(deadline)
            if line is None:
                raise EngineError(f"timeout waiting for reply; got {lines[-6:]!r}")
            lines.append(line)
            if stop(lines):
                return lines

    def isready(self) -> None:
        self.send("isready")
        self._read_until(lambda ls: ls and ls[-1] == "readyok")

    def quit(self) -> None:
        try:
            self.send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()

    def __enter__(self) -> "Engine":
        return self

    def __exit__(self, *exc) -> None:
        self.quit()

    # -------------------------------------------------------------- options

    def assert_option(self, name: str) -> None:
        # The name must appear in the engine's own advertised option list. A
        # misspelled setoption is silently ignored (trap 4), and the reply is
        # indistinguishable from a correct one, so the list is the only witness.
        if not any(re.match(rf"option name {re.escape(name)} type ", l) for l in self.options):
            raise EngineError(f"engine does not advertise option {name}")

    def set_option(self, name: str, value: str) -> None:
        before = len(self.log)
        self.send(f"setoption name {name} value {value}")
        self.isready()
        # Only the lines produced BY THIS COMMAND. Scanning a fixed-size tail of
        # the whole log reads a neighbouring command's diagnostic as this one's
        # answer, which is how a clean restore looked like a refusal.
        bad = [l for l in self.log[before:] if "invalid value" in l or "unknown option" in l]
        if bad:
            raise EngineError(f"option {name}={value} refused: {bad}")

    def option_default(self, name: str) -> str | None:
        for line in self.options:
            m = re.match(rf"option name {re.escape(name)} type \S+ default (\S+)", line)
            if m:
                return m.group(1)
        return None

    # -------------------------------------------------------------- position

    def set_position(self, fen: str, moves: list[str] | None = None,
                     cold: bool = True) -> list[str]:
        """Send a position and return the position reply lines.

        `cold` sends `ucinewgame` first, which is a true reset (it wipes the
        transposition table AND the histories, unlike `Clear Hash`). Without it
        a reused process carries TT state between positions and the same request
        returns different nodes — a stable-looking wrong number rather than
        noise.

        The reply is accumulated before `isready` so the invalid-FEN diagnostic
        is seen where it actually appears: on the `position` command itself.
        """
        if cold:
            self.send("ucinewgame")
            self.isready()
        cmd = f"position fen {fen}"
        if moves:
            cmd += " moves " + " ".join(moves)
        self.send(cmd)
        time.sleep(0.005)
        deadline = time.monotonic() + 1.0
        lines: list[str] = []
        while True:
            line = self._read_line(deadline)
            if line is None:
                break
            lines.append(line)
            if line == "readyok":
                break
        self.isready()
        bad = [l for l in lines if "invalid FEN" in l or "illegal move" in l]
        if bad:
            raise EngineError(f"position refused: {bad} (fen={fen} moves={moves})")
        return lines

    # ---------------------------------------------------------------- search

    def go_depth(self, depth: int) -> dict:
        """Search to a fixed depth and return the parsed result.

        Asserts an `info depth` line was produced: a search that emitted none
        is the signature of the EOF-abort fabrication (trap 3a) and must fail
        rather than be recorded.
        """
        self.send(f"go depth {depth}")
        lines = self._read_until(lambda ls: any(BESTMOVE.match(l) for l in ls),
                                 timeout=self.timeout)
        return self._parse(lines)

    def _parse(self, lines: list[str]) -> dict:
        depths: list[dict] = []
        bestmove = None
        for line in lines:
            m = INFO_DEPTH.match(line)
            if m:
                entry = {"depth": int(m.group(1)), "rest": m.group(2)}
                cp = SCORE_CP.search(line)
                mate = SCORE_MATE.search(line)
                nodes = NODES.search(line)
                entry["cp"] = int(cp.group(1)) if cp else None
                entry["mate"] = int(mate.group(1)) if mate else None
                entry["nodes"] = int(nodes.group(1)) if nodes else None
                pv = re.search(r"\bpv (.+)$", line)
                entry["pv"] = pv.group(1).split() if pv else []
                depths.append(entry)
            bm = BESTMOVE.match(line)
            if bm:
                bestmove = bm.group(1)
        if not depths:
            raise EngineError(f"search produced no info depth line: {lines[-4:]!r}")
        if bestmove is None:
            raise EngineError("search produced no bestmove")
        final = depths[-1]
        return {
            "bestmove": bestmove,
            "depth": final["depth"],
            "cp": final["cp"],
            "mate": final["mate"],
            "nodes": final["nodes"],
            "pv": final["pv"],
            "info_depths": len(depths),
            "lines": lines,
        }
