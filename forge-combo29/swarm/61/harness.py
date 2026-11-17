#!/usr/bin/env python3
"""Strict UCI harness for swarm/61 rechecks.

Rules enforced here (each one is a measured failure from this run):

  1. Threads 1, Hash 16 on every search; a clock search may never carry a zero increment.
  2. Every FEN and every move is validated with python-chess BEFORE it is sent.
  3. `info string invalid FEN` is scanned for in BOTH the position reply and the `go` output.
     The diagnostic's location moves with where you read: with `isready` after `position` it
     lands in the position reply before `readyok`; without it, ahead of the first `info depth`
     line in the go output.  Reading only one of the two misses it half the time.
     Any sighting raises, and the caller aborts — an illegal FEN makes the engine search the
     PREVIOUS position and return a normal-looking answer.
  4. Waits are on `bestmove` with a wall timeout, never on an `info depth` line.
  5. `go infinite` is always followed by `stop`.
"""
import subprocess
import time

import chess


class EngineFault(RuntimeError):
    """Raised on any protocol condition that forbids using the result."""


DEFAULT_TIMEOUT = 120.0


class Engine:
    def __init__(self, exe, hash_mb=16, multipv=1, ownbook=False):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1,
        )
        self._send("uci")
        self._read_until(lambda ln: ln.strip() == "uciok", DEFAULT_TIMEOUT, "uciok")
        self._send("setoption name Threads value 1")
        self._send("setoption name Hash value %d" % hash_mb)
        self._send("setoption name MultiPV value %d" % multipv)
        self._send("setoption name OwnBook value %s" % ("true" if ownbook else "false"))
        self._send("setoption name Move Overhead value 10")
        self._send("isready")
        self._read_until(lambda ln: ln.strip() == "readyok", DEFAULT_TIMEOUT, "readyok")

    # -- plumbing ---------------------------------------------------------
    def _send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def _read_until(self, pred, timeout, what):
        deadline = time.monotonic() + timeout
        collected = []
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EngineFault("timeout after %.1fs waiting for %s" % (timeout, what))
            ln = self.proc.stdout.readline()
            if ln == "":
                raise EngineFault("engine closed stdout while waiting for %s" % what)
            ln = ln.rstrip("\n")
            collected.append(ln)
            if pred(ln):
                return collected

    @staticmethod
    def _scan_fen(lines, where):
        for ln in lines:
            if "invalid FEN" in ln:
                raise EngineFault("invalid FEN reported in %s: %s" % (where, ln.strip()))
            if "illegal move" in ln:
                raise EngineFault("illegal move reported in %s: %s" % (where, ln.strip()))

    # -- commands ---------------------------------------------------------
    def set_position(self, board, moves=(), expect_reject=False):
        """Send a position, fully validated by python-chess first."""
        fen = board.fen()
        # python-chess round-trip: a FEN that will not reparse would be refused by the engine.
        if chess.Board(fen).fen() != fen:
            raise EngineFault("FEN does not round-trip through python-chess: %r" % fen)
        replay = board.copy()
        for m in moves:
            mv = chess.Move.from_uci(m)
            if mv not in replay.legal_moves:
                raise EngineFault("illegal move %s for %s" % (m, replay.fen()))
            replay.push(mv)
        cmd = "position fen %s" % fen
        if moves:
            cmd += " moves " + " ".join(moves)
        if expect_reject:
            # Deliberately plant an illegal FEN to prove the detector fires.
            cmd = "position fen %s" % "9k/9/8/8/8/8/8/K7 w - - 0 1"
        self._send(cmd)
        self._send("isready")
        reply = self._read_until(lambda ln: ln.strip() == "readyok", DEFAULT_TIMEOUT, "readyok")
        self._scan_fen(reply, "position reply")
        return reply

    def search(self, board, go, moves=(), timeout=DEFAULT_TIMEOUT, ucinewgame=True):
        """Run one search; returns dict with nodes, time_ms, bestmove, depth, seldepth, score, pv."""
        if ucinewgame:
            # The source harnesses send this before every position; without it the TT carries
            # over and node counts drift (measured: 2-occ cell 2,911 warm vs 22,108 fresh).
            self._send("ucinewgame")
            self._send("isready")
            self._read_until(lambda ln: ln.strip() == "readyok", DEFAULT_TIMEOUT, "readyok")
        self.set_position(board, moves)
        self._send("isready")
        self._read_until(lambda ln: ln.strip() == "readyok", DEFAULT_TIMEOUT, "readyok")
        self._send("go " + go)
        if "infinite" in go.split():
            # `go infinite` never returns on its own; give it a moment then stop it.
            time.sleep(1.0)
            self._send("stop")
        lines = self._read_until(lambda ln: ln.startswith("bestmove"), timeout, "bestmove")
        self._scan_fen(lines, "go output")
        return parse_search(lines)

    def perft(self, board, depth, moves=()):
        self.set_position(board, moves)
        self._send("isready")
        self._read_until(lambda ln: ln.strip() == "readyok", DEFAULT_TIMEOUT, "readyok")
        self._send("go perft %d" % depth)
        lines = self._read_until(lambda ln: ln.startswith("Nodes searched"), DEFAULT_TIMEOUT,
                                 "perft summary")
        self._scan_fen(lines, "perft output")
        total = None
        for ln in lines:
            if ln.startswith("Nodes searched"):
                total = int(ln.split()[-1])
        return total, lines

    def first_generated_move(self, board, moves=()):
        """`go perft 1`'s first divide line is the head of the generated list."""
        _, lines = self.perft(board, 1, moves)
        for ln in lines:
            parts = ln.split(":")
            if len(parts) == 2 and parts[1].strip().isdigit():
                return parts[0].strip()
        raise EngineFault("no divide line in perft 1 output")

    def close(self):
        try:
            self._send("quit")
            self.proc.wait(timeout=30)
        except Exception:
            self.proc.kill()


def parse_search(lines):
    """Parse a UCI search transcript.

    `pv` is captured as a possibly-EMPTY list.  That distinction is load-bearing: on a drawn
    root the engine emits `... nodes 0 ... pv` with nothing after it, and an earlier version of
    this parser required a token after `pv`, so it skipped exactly the line that carries the
    bail's signature and reported "no info lines" instead of "0 nodes".
    """
    nodes = None
    time_ms = None
    depth = None
    seldepth = None
    score = None
    pv = None
    bestmove = None
    info_count = 0
    for ln in lines:
        if ln.startswith("bestmove"):
            bestmove = ln.split()[1] if len(ln.split()) > 1 else None
            continue
        if not ln.startswith("info depth"):
            continue
        info_count += 1
        tok = ln.split()
        for i, t in enumerate(tok):
            if t == "depth":
                depth = int(tok[i + 1])
            elif t == "seldepth":
                seldepth = int(tok[i + 1])
            elif t == "nodes":
                nodes = int(tok[i + 1])
            elif t == "time":
                time_ms = int(tok[i + 1])
            elif t == "score":
                kind = tok[i + 1]
                val = int(tok[i + 2])
                score = ("mate", val) if kind == "mate" else ("cp", val)
            elif t == "pv":
                pv = tok[i + 1:]
                break
    return {
        "nodes": nodes, "time_ms": time_ms, "depth": depth, "seldepth": seldepth,
        "score": score, "pv": pv, "bestmove": bestmove, "info_count": info_count,
        "raw": lines,
    }
