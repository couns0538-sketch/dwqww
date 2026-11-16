#!/usr/bin/env python3
"""uci_guard.py — a small, self-contained wrapper that makes the two hazards safe.

Implements the rule from HAZARD_stale_board.md:

    Fatal on `invalid FEN` or `illegal move`:
    resync only with `ucinewgame` plus a well-formed `position`, never `isready`.

and from HAZARD_match_protocol.md:

    Always send BOTH wtime and btime.
    A fixed node budget is not depth-equal across builds; use depth or the clock.

Why this exists
---------------
A rejected `position` command leaves the engine on the PREVIOUS board and it still answers
`readyok`, so a harness that syncs on `readyok` receives a legal, confident move for the wrong
position. Measured on PC r15 / PC20 / Threads 1; see HAZARD_stale_board.md for the evidence.

Usage
-----
    g = UciGuard("/path/to/forge", options=["Threads 1", "Hash 16"])
    g.start()
    try:
        g.set_position(fen="rnbq...")           # raises PositionRejected if refused
        move = g.bestmove(nodes=20000)          # or depth=..., or clock(wtime=6000,btime=6000)
        g.set_position(startpos_moves=["e2e4"]) # either form
        move2 = g.bestmove(depth=12)
    finally:
        g.stop()

If `set_position` raises PositionRejected, the guard has ALREADY recovered (ucinewgame plus a
known-good position) and the caller should skip that game. That is the documented defence: the
cost is one game, never a session.

Deliberately small: no threads above one, no pondering, no book. Every option string must be
either "Name value" or a full "setoption name ... value ..." line.
"""
from __future__ import annotations

import queue
import subprocess
import threading
from typing import Iterable, Sequence

SANITIZER_MARKERS = ("ERROR: AddressSanitizer", "runtime error:", "SUMMARY:", "ThreadSanitizer")


class GuardError(RuntimeError):
    """The engine did something the guard cannot interpret."""


class PositionRejected(GuardError):
    """`position` was refused. The guard has already resynced; skip this game."""


class UciGuard:
    def __init__(self, exe: str, options: Iterable[str] = (), timeout: float = 60.0):
        self.exe = exe
        self.timeout = timeout
        self.options = list(options)
        self.proc: subprocess.Popen | None = None
        self._q: queue.Queue[str | None] | None = None
        self._err_q: queue.Queue[str | None] | None = None
        self._stderr: list[str] = []

    # ---- lifecycle -------------------------------------------------------------------
    def start(self) -> "UciGuard":
        self.proc = subprocess.Popen(
            [self.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1)
        self._q = queue.Queue()
        self._err_q = queue.Queue()
        threading.Thread(target=self._pump, args=(self.proc.stdout, self._q), daemon=True).start()
        threading.Thread(target=self._pump, args=(self.proc.stderr, self._err_q), daemon=True).start()
        self._send("uci")
        self._read_until("uciok")
        for opt in self.options:
            # Accept both "Threads 1" and a complete "setoption name Threads value 1".
            if opt.startswith("setoption"):
                self._send(opt)
            else:
                name, _, val = opt.partition(" ")
                self._send(f"setoption name {name} value {val}")
        self._sync()
        return self

    def stop(self) -> None:
        if not self.proc:
            return
        try:
            self._send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        self.proc = None

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()

    # ---- plumbing --------------------------------------------------------------------
    @staticmethod
    def _pump(stream, q: "queue.Queue[str | None]") -> None:
        try:
            for line in iter(stream.readline, ""):
                q.put(line.rstrip("\n"))
        except Exception:
            pass
        q.put(None)

    def _send(self, line: str) -> None:
        if not self.proc or not self.proc.stdin:
            raise GuardError("engine is not running")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def _read_until(self, token: str, timeout: float | None = None) -> list[str]:
        if self._q is None:
            raise GuardError("engine is not running")
        deadline_timeout = timeout if timeout is not None else self.timeout
        out: list[str] = []
        while True:
            try:
                # A real deadline, so a hung engine can never hang the harness.
                line = self._q.get(timeout=deadline_timeout)
            except queue.Empty:
                raise GuardError(
                    f"no {token!r} within {deadline_timeout}s. NOTE: a timeout is only a hang "
                    "once you have shown the search is doing nothing — read the info lines first "
                    "(PROBES_THAT_LIED.md, trap 2b).")
            if line is None:
                raise GuardError("engine closed stdout")
            out.append(line)
            if line.strip() == token or line.startswith(token):
                self._drain_stderr()
                return out

    def _drain_stderr(self) -> None:
        if self._err_q is None:
            return
        while True:
            try:
                line = self._err_q.get_nowait()
            except queue.Empty:
                return
            if line is None:
                return
            self._stderr.append(line)

    def sanitizer_lines(self) -> list[str]:
        self._drain_stderr()
        return [l for l in self._stderr if any(m in l for m in SANITIZER_MARKERS)]

    def _sync(self) -> None:
        self._send("isready")
        self._read_until("readyok")

    # ---- position handling: the guarded part -----------------------------------------
    def set_position(self, fen: str | None = None, startpos_moves: Sequence[str] | None = None) -> None:
        """Set a position. Raises PositionRejected if the engine refuses it.

        On refusal the guard RESYNCS (ucinewgame + a known-good startpos) before raising, so the
        next search cannot silently answer for the previous board.
        """
        if fen is not None and startpos_moves is not None:
            raise ValueError("give fen OR startpos_moves, not both")
        if fen is None and startpos_moves is None:
            self._send("position startpos")
        elif fen is not None:
            self._send(f"position fen {fen}")
        else:
            self._send("position startpos moves " + " ".join(startpos_moves or []))

        self._send("isready")
        answer = self._read_until("readyok")
        refusal = [l for l in answer if "invalid FEN" in l or "illegal move" in l]
        if refusal:
            self._recover()
            raise PositionRejected(
                "position refused (" + "; ".join(r.strip() for r in refusal) + "). "
                "The guard resynced with ucinewgame + startpos; skip this game. "
                "Do NOT continue on the previous board (HAZARD_stale_board.md).")

    def _recover(self) -> None:
        """The documented defence: ucinewgame, never isready alone."""
        self._send("ucinewgame")
        self._sync()
        self._send("position startpos")
        self._sync()

    # ---- searching -------------------------------------------------------------------
    def bestmove(self, *, depth: int | None = None, nodes: int | None = None,
                 movetime: int | None = None,
                 wtime: int | None = None, btime: int | None = None,
                 winc: int = 0, binc: int = 0) -> str:
        """Start a search and return the bestmove. Refuses to send a clock with only one side."""
        forms = [("depth", depth), ("nodes", nodes), ("movetime", movetime)]
        chosen = [(n, v) for n, v in forms if v is not None]
        has_clock = wtime is not None or btime is not None
        if len(chosen) + (1 if has_clock else 0) != 1:
            raise ValueError("give exactly one of depth, nodes, movetime, or a clock pair")

        if has_clock:
            if wtime is None or btime is None:
                # Measured: 136 ms with both clocks vs ~12 s with only wtime.
                raise ValueError(
                    "a clock search needs BOTH wtime and btime: with only the side to move's "
                    "clock the engine searches ~12 s instead of 0.14 s (S-F78)")
            go = f"go wtime {wtime} btime {btime} winc {winc} binc {binc}"
        else:
            name, value = chosen[0]
            go = f"go {name} {value}"

        self._send(go)
        lines = self._read_until("bestmove")
        tail = lines[-1].split()
        move = tail[1] if len(tail) > 1 else ""
        if not move:
            raise GuardError(f"could not parse a move from {lines[-1]!r}")
        if self.sanitizer_lines():
            raise GuardError(f"sanitizer output: {self.sanitizer_lines()[:3]}")
        return move

    def eval_line(self) -> str:
        """Raw `eval` output (the engine's static evaluation line), for bookkeeping."""
        self._send("eval")
        self._send("isready")
        lines = self._read_until("readyok")
        for line in lines:
            if "info string eval" in line:
                return line
        raise GuardError("no `info string eval` line")


if __name__ == "__main__":
    import sys
    exe = sys.argv[1] if len(sys.argv) > 1 else "forge"
    with UciGuard(exe, options=["Threads 1", "Hash 16"]) as g:
        g.set_position(fen="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3")
        print("nodes 20000 ->", g.bestmove(nodes=20000))
        g.set_position(fen=None, startpos_moves=["e2e4", "e7e5"])
        print("depth 12    ->", g.bestmove(depth=12))
        print("clock       ->", g.bestmove(wtime=6000, btime=6000, winc=60, binc=60))
        try:
            g.set_position(fen="4k3/8/8/8/8/8/8/4K3 w - -")   # truncated: must be refused
            print("UNEXPECTED: truncated FEN was accepted")
        except PositionRejected as exc:
            print("guarded    ->", str(exc)[:70], "...")
        print("after guard->", g.bestmove(depth=6), "(startpos board, correct)")
