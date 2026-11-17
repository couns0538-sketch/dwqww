#!/usr/bin/env python3
"""Strict UCI harness for the MultiPV output audit (swarm/multipv).

Every rule encoded here is a measured failure mode from forge-findings.md, not a preference:

  1. Threads 1 and an explicit Hash on every search.  Above Threads 1 no result is reportable
     (findings section 3).
  2. WAIT ON `bestmove`, never on an `info depth` line.  The book path emits ZERO info lines and
     the drawn-root bail is instant; a reader that waits for `info depth` deadlocks (trap 21).
     Every read carries a wall timeout.
  3. Scan every reply for `info string invalid FEN` and `info string illegal move`.  An illegal FEN
     makes the engine search the PREVIOUS position and answer normally (findings 1b).
  4. Validate each FEN with python-chess before sending it, so rule 3 never has to fire.
  5. `go infinite` is always followed by `stop` (trap 24).
  6. Do not pipe into `quit`: `quit` calls stop_search() and the search thread can be killed before
     it prints.  One search per process, read to `bestmove`, then `quit` and wait.
"""
import os
import subprocess
import time

import chess

DEFAULT_EXE = os.environ.get("FORGE_EXE", "build/forge")
TIMEOUT = float(os.environ.get("FORGE_TIMEOUT", "120"))


class EngineFault(RuntimeError):
    pass


class Engine:
    """One long-lived process; each search is read to `bestmove`."""

    def __init__(self, exe=None, hash_mb=16, multipv=1, ownbook=False, extra_options=()):
        self.exe = exe or DEFAULT_EXE
        self.proc = subprocess.Popen(
            [self.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1,
        )
        self.pending = []
        self._send("uci")
        self._read_until(lambda ln: ln.strip() == "uciok", "uciok")
        self.setoption("Threads", 1)
        self.setoption("Hash", hash_mb)
        self.setoption("MultiPV", multipv)
        self.setoption("OwnBook", "true" if ownbook else "false")
        self.setoption("Move Overhead", 10)
        for name, value in extra_options:
            self.setoption(name, value)
        self.sync()
        self.multipv = multipv
        self.hash_mb = hash_mb
        self.ownbook = ownbook

    # -- plumbing ---------------------------------------------------------
    def _send(self, line):
        if self.proc.poll() is not None:
            raise EngineFault("engine exited before %r" % line)
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def _readline(self, deadline, what):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise EngineFault("timeout after %.1fs waiting for %s" % (TIMEOUT, what))
        ln = self.proc.stdout.readline()
        if ln == "":
            raise EngineFault("engine closed stdout while waiting for %s" % what)
        return ln.rstrip("\n")

    def _read_until(self, pred, what):
        deadline = time.monotonic() + TIMEOUT
        out = []
        while True:
            ln = self._readline(deadline, what)
            out.append(ln)
            if pred(ln):
                return out

    @staticmethod
    def _scan(lines):
        for ln in lines:
            if "invalid FEN" in ln or "illegal move" in ln:
                raise EngineFault("engine reported a refusal: %s" % ln.strip())

    def setoption(self, name, value):
        self._send("setoption name %s value %s" % (name, value))

    def sync(self):
        self._send("isready")
        self._read_until(lambda ln: ln.strip() == "readyok", "readyok")

    def new_game(self):
        """Reset the TT between searches so a search cannot be read off the previous one."""
        self._send("ucinewgame")
        self.sync()

    # -- commands ---------------------------------------------------------
    def position(self, board_or_fen, moves=()):
        fen = board_or_fen.fen() if isinstance(board_or_fen, chess.Board) else board_or_fen
        if chess.Board(fen).fen() != fen:
            raise EngineFault("FEN does not round-trip through python-chess: %s" % fen)
        self._send("position fen %s" % fen)
        if moves:
            self._send("position fen %s moves %s" % (fen, " ".join(moves)))
        self.sync()

    def go(self, cmd, stop_after=None):
        """Send one `go` and return every line up to and including `bestmove`."""
        self._send(cmd)
        lines = self._read_until(lambda ln: ln.startswith("bestmove"), "bestmove")
        self._scan(lines)
        if stop_after is not None:
            raise EngineFault("stop_after is for infinite; use go_infinite")
        return lines

    def go_infinite(self, stop_after):
        self._send("go infinite")
        time.sleep(stop_after)
        self._send("stop")
        lines = self._read_until(lambda ln: ln.startswith("bestmove"), "bestmove")
        self._scan(lines)
        return lines

    def close(self):
        try:
            self._send("quit")
        except EngineFault:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


# -- parsing -------------------------------------------------------------
def parse_score(tokens):
    """Return (kind, value) in centipawns for comparison, from a token list."""
    for i, tok in enumerate(tokens):
        if tok == "cp":
            return ("cp", int(tokens[i + 1]))
        if tok == "mate":
            return ("mate", int(tokens[i + 1]))
    return (None, None)


def score_cp(kind, value, mate_bonus=100000):
    """Map a score to a comparable integer, larger = better for the side to move.

    A mate distance and a cp score are not on one scale, so mates are lifted clear of any cp
    value; a shorter mate outranks a longer one.
    """
    if kind == "cp":
        return value
    if kind == "mate":
        if value > 0:
            return mate_bonus - value
        return -mate_bonus - value
    return None


def parse_info(line):
    """Parse an `info depth ...` line into a dict, or None for non-depth lines."""
    tok = line.split()
    if len(tok) < 2 or tok[0] != "info" or tok[1] != "depth":
        return None
    out = {"raw": line, "depth": None, "multipv": 1, "score_kind": None, "score": None,
           "seldepth": None, "nodes": None, "nps": None, "hashfull": None, "time": None,
           "pv": [], "has_multipv_token": False}
    try:
        out["depth"] = int(tok[2])
    except (IndexError, ValueError):
        raise EngineFault("info depth line without an integer depth: %r" % line)
    i = 3
    while i < len(tok):
        t = tok[i]
        if t == "depth":
            out["depth"] = int(tok[i + 1]); i += 2
        elif t == "multipv":
            out["multipv"] = int(tok[i + 1]); out["has_multipv_token"] = True; i += 2
        elif t == "score":
            kind, value = parse_score(tok[i + 1:])
            out["score_kind"], out["score"] = kind, value
            i += 2 if kind == "cp" else 2
        elif t == "seldepth":
            out["seldepth"] = int(tok[i + 1]); i += 2
        elif t == "nodes":
            out["nodes"] = int(tok[i + 1]); i += 2
        elif t == "nps":
            out["nps"] = int(tok[i + 1]); i += 2
        elif t == "hashfull":
            out["hashfull"] = int(tok[i + 1]); i += 2
        elif t == "time":
            out["time"] = int(tok[i + 1]); i += 2
        elif t == "wdl":
            i += 4
        elif t == "string":
            out["string"] = " ".join(tok[i + 1:]); break
        elif t == "pv":
            out["pv"] = tok[i + 1:]; break
        else:
            i += 1
    return out


def depth_lines(lines):
    return [p for p in (parse_info(ln) for ln in lines) if p is not None]


def bestmove_of(lines):
    for ln in reversed(lines):
        if ln.startswith("bestmove"):
            tok = ln.split()
            return tok[1] if len(tok) > 1 else None
    raise EngineFault("no bestmove line")


def final_depth_group(infos):
    """All info lines at the highest depth present (the last iteration's block)."""
    if not infos:
        return 0, []
    top = max(p["depth"] for p in infos)
    return top, [p for p in infos if p["depth"] == top]
