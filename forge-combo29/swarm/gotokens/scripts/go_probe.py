#!/usr/bin/env python3
"""One UCI `go` cell, one fresh engine process, with a hard wall-clock cap.

Discipline this file exists to enforce (see FINDINGS.md "Method"):
  * a fresh process per cell, so no TT / history warmth crosses cells (trap 3);
  * no EOF while a search runs (trap 1) -- stdin stays open until we have
    either a `bestmove` or we have sent `stop` and collected its reply;
  * a real deadline on a pipe, implemented by a reader thread rather than
    select()+readline() (trap 2);
  * RETURNED and CAPPED are separate outcomes; a capped cell still gets a
    post-`stop` reading so "never returns" and "slow" are distinguishable.
"""

from __future__ import annotations

import subprocess
import threading
import time
from dataclasses import dataclass, field, asdict

MIDGAME_WHITE = "fen r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1"
MIDGAME_BLACK = "fen r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N1PN2/PPPP1PPP/R1BQ1RK1 b kq - 1 1"
STARTPOS = "startpos"


def as_position_command(position: str) -> str:
    """`position` argument -> a command the engine actually applies.

    A bare FEN without the `fen` keyword is silently treated as an unknown
    position TYPE and the previous board is kept (trap 3ab), which would make
    every cell in a matrix quietly measure startpos. Prefix it here, once.
    """
    text = position.strip()
    if text.startswith(("startpos", "fen ")):
        return text
    return "fen " + text


class Engine:
    """A live engine process with a deadline-aware line reader."""

    def __init__(self, exe: str):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self._lock = threading.Lock()
        self._lines: list[tuple[float, str]] = []
        self._closed = False
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self) -> None:
        stream = self.proc.stdout
        assert stream is not None
        for raw in iter(stream.readline, b""):
            text = raw.decode("utf-8", "replace").rstrip("\r\n")
            with self._lock:
                self._lines.append((time.monotonic(), text))
        with self._lock:
            self._closed = True

    def send(self, text: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write((text + "\n").encode())
        self.proc.stdin.flush()

    def mark(self) -> int:
        with self._lock:
            return len(self._lines)

    def since(self, mark: int) -> list[str]:
        with self._lock:
            return [text for _, text in self._lines[mark:]]

    def wait_for(self, predicate, deadline_s: float, since: int = 0) -> bool:
        """True when a line at or after `since` matches, before the deadline.

        `since` matters: scanning from index 0 lets a readyok from one command
        satisfy the wait for the NEXT command's readyok, which puts the mark for
        the measured command in the wrong place and leaks stale lines into its
        wire. Every wait in this file passes the mark it is waiting past.
        """
        end = time.monotonic() + deadline_s
        while time.monotonic() < end:
            with self._lock:
                texts = [text for _, text in self._lines[since:]]
                closed = self._closed
            if any(predicate(text) for text in texts):
                return True
            if closed:
                return False
            time.sleep(0.002)
        return False

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)


@dataclass
class Cell:
    go: str
    position: str
    own_book: bool
    timeout_s: float
    terminated: bool = False
    elapsed_ms: float = 0.0
    bestmove: str | None = None
    info_depth_lines: int = 0
    max_depth: int | None = None
    last_nodes: int | None = None
    last_score: str | None = None
    pv_present: bool = False
    book_move_line: str | None = None
    info_string_lines: list[str] = field(default_factory=list)
    wire: list[str] = field(default_factory=list)
    stop_bestmove: str | None = None
    stop_wire: list[str] = field(default_factory=list)
    build: str = "base@6b98f217"

    def as_dict(self) -> dict:
        return asdict(self)


def _parse_info(text: str) -> dict:
    """Fields of one `info` line, best effort."""
    out: dict = {}
    parts = text.split()
    if not parts or parts[0] != "info":
        return out
    for i, token in enumerate(parts):
        if token in ("depth", "seldepth", "nodes", "multipv", "nps", "time", "hashfull", "tbhits") and i + 1 < len(parts):
            try:
                out[token] = int(parts[i + 1])
            except ValueError:
                pass
        elif token == "score" and i + 2 < len(parts):
            out["score"] = " ".join(parts[i + 1:i + 3])
    if "pv" in parts:
        out["pv"] = " ".join(parts[parts.index("pv") + 1:])
    return out


def run_cell(
    exe: str,
    go: str,
    position: str = MIDGAME_WHITE,
    own_book: bool = False,
    timeout_s: float = 20.0,
    collect_after_stop: bool = True,
    build: str = "base@6b98f217",
    expect_move: str | None = None,
) -> Cell:
    position = as_position_command(position)
    engine = Engine(exe)
    try:
        setup_mark = engine.mark()
        engine.send("uci")
        if not engine.wait_for(lambda t: t == "uciok", 10.0, setup_mark):
            raise RuntimeError("no uciok")
        engine.send("setoption name Hash value 16")
        engine.send("setoption name Threads value 1")
        engine.send("setoption name OwnBook value " + ("true" if own_book else "false"))
        engine.send("position " + position)
        # A single isready AFTER the position command both confirms setup and
        # gives this harness a known last line, so the measured mark can sit
        # exactly after it. Nothing from setup can then be read as the search's
        # output, and a surplus readyok cannot satisfy the bestmove wait.
        setup_mark = engine.mark()
        engine.send("isready")
        if not engine.wait_for(lambda t: t == "readyok", 20.0, setup_mark):
            raise RuntimeError("no readyok after setup")
        if expect_move is not None:
            # Probe the board with a depth-1 search and refuse to measure if the
            # engine is not on the position we think it is. `position fen` can
            # be refused (short/illegal FEN) and leave the previous board, and
            # an unknown type is silent, so the setup needs its own check.
            check_mark = engine.mark()
            engine.send("go depth 1")
            if not engine.wait_for(lambda t: t.startswith("bestmove"), 20.0, check_mark):
                raise RuntimeError("position check did not return")
            check = [t for t in engine.since(check_mark) if t.startswith("bestmove")]
            got = check[-1].split()[1] if check and len(check[-1].split()) > 1 else None
            if got != expect_move:
                raise RuntimeError(f"position check failed: expected {expect_move}, engine played {got}")

        # Drain anything the setup left queued (the depth-1 probe's info lines),
        # then take the mark. Without this the probe's lines would be counted as
        # the measured command's.
        time.sleep(0.02)
        mark = engine.mark()
        started = time.monotonic()
        engine.send(go)
        got = engine.wait_for(lambda t: t.startswith("bestmove"), timeout_s, mark)
        cell = Cell(go=go, position=position, own_book=own_book, timeout_s=timeout_s, build=build)
        cell.terminated = got
        cell.elapsed_ms = round((time.monotonic() - started) * 1000.0, 1)
        wire = engine.since(mark)
        if got:
            cell.wire = wire
        else:
            # Keep a bounded slice of an unbounded cell's output: the ladder is
            # what shows it is still climbing rather than stalled. Head and tail
            # must not overlap, or a short wire is concatenated with itself and
            # the cell reports duplicated lines and a second bestmove that the
            # engine never sent.
            cell.wire = _head_tail(wire, 12, 12)
            if collect_after_stop:
                stop_mark = engine.mark()
                engine.send("stop")
                if engine.wait_for(lambda t: t.startswith("bestmove"), 15.0, stop_mark):
                    stop_wire = engine.since(stop_mark)
                    cell.stop_wire = _head_tail(stop_wire, 6, 3)
                    for text in stop_wire:
                        if text.startswith("bestmove"):
                            cell.stop_bestmove = text.split()[1] if len(text.split()) > 1 else None
        populate(cell)
        return cell
    finally:
        engine.close()


def _head_tail(lines: list[str], head: int, tail: int) -> list[str]:
    """A bounded view of a long line list, never overlapping itself.

    Written as a function because the obvious one-liner (`lines[:n] + lines[-n:]`)
    duplicates the entire list whenever `len(lines) <= 2n`, which silently
    fabricated a repeated depth ladder and a second `bestmove` in this seat's
    first pass. A truncation helper has to be correct for SHORT input, not just
    for the long input it was written for.
    """
    if len(lines) <= head + tail + 1:
        return list(lines)
    return lines[:head] + ["..."] + lines[-tail:]


def populate(cell: Cell) -> None:
    for text in cell.wire:
        if text.startswith("info string"):
            cell.info_string_lines.append(text)
            if "book move" in text:
                cell.book_move_line = text
        if text.startswith("info depth"):
            cell.info_depth_lines += 1
        info = _parse_info(text)
        if "depth" in info:
            cell.max_depth = info["depth"] if cell.max_depth is None else max(cell.max_depth, info["depth"])
        if "nodes" in info:
            cell.last_nodes = info["nodes"]
        if "score" in info:
            cell.last_score = info["score"]
        if "pv" in info and info["pv"].strip():
            cell.pv_present = True
        if text.startswith("bestmove"):
            parts = text.split()
            cell.bestmove = parts[1] if len(parts) > 1 else None


def verdict(cell: Cell) -> str:
    if not cell.terminated:
        return "CAPPED-UNBOUNDED"
    if cell.info_depth_lines == 0:
        return "RETURNED-NO-INFO"
    return "RETURNED"


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="probe one UCI go command on one fresh process")
    ap.add_argument("exe")
    ap.add_argument("go")
    ap.add_argument("--position", default=MIDGAME_WHITE)
    ap.add_argument("--own-book", action="store_true")
    ap.add_argument("--timeout", type=float, default=20.0)
    args = ap.parse_args()
    c = run_cell(args.exe, args.go, args.position, args.own_book, args.timeout)
    c.wire = c.wire if len(c.wire) <= 40 else c.wire[:8] + ["..."] + c.wire[-8:]
    print(json.dumps({"verdict": verdict(c), **c.as_dict()}, indent=2))
