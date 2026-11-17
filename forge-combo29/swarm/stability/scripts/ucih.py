"""Minimal UCI driver that never pipes `quit` into a live search.

Every interaction is send-then-read-to-a-terminator. A search is finished when
`bestmove` arrives; nothing else is allowed to be written while a search is
outstanding. That rule exists because the audit records five separate seats
fabricating a `bestmove` by piping `quit` into an unfinished search.
"""
import os
import select
import subprocess
import time


class Uci:
    def __init__(self, path, timeout=600.0):
        self.path = path
        self.timeout = timeout
        self.p = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # engine echoes diagnostics on both streams
            bufsize=0,
        )
        self.fd = self.p.stdout.fileno()
        self._buf = b""

    # ---- raw io -------------------------------------------------------
    def _read_some(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("engine read timeout")
        r, _, _ = select.select([self.fd], [], [], remaining)
        if not r:
            raise TimeoutError("engine read timeout")
        chunk = os.read(self.fd, 65536)
        if not chunk:
            raise EOFError("engine closed stdout")
        self._buf += chunk

    def readline(self, timeout=None):
        """Return one decoded line (without newline). Raises on timeout/EOF."""
        deadline = time.monotonic() + (self.timeout if timeout is None else timeout)
        while b"\n" not in self._buf:
            self._read_some(deadline)
        line, self._buf = self._buf.split(b"\n", 1)
        return line.decode("utf-8", "replace").rstrip("\r")

    def send(self, cmd):
        self.p.stdin.write((cmd + "\n").encode())
        self.p.stdin.flush()

    # ---- protocol steps ----------------------------------------------
    def handshake(self):
        self.send("uci")
        opts = []
        while True:
            line = self.readline()
            if line.startswith("option "):
                opts.append(line)
            if line == "uciok":
                break
        self.send("isready")
        while self.readline() != "readyok":
            pass
        return opts

    def read_until(self, prefix, timeout=None):
        """Read lines until one starts with `prefix`; return (matched, lines)."""
        lines = []
        while True:
            line = self.readline(timeout)
            lines.append(line)
            if line.startswith(prefix):
                return line, lines

    def search(self, position_cmd, go_cmd):
        """Run one search to completion. Returns dict of parsed fields.

        Never returns before `bestmove`, so no caller can truncate a search.
        """
        self.send(position_cmd)
        self.send("isready")
        # A refused FEN answers on the position command, not in search output.
        pos_reply = []
        while True:
            line = self.readline()
            pos_reply.append(line)
            if line == "readyok":
                break

        self.send(go_cmd)
        _, lines = self.read_until("bestmove ")
        return parse_search(lines, pos_reply)


def parse_search(lines, pos_reply=None):
    """Pull every field we compare out of a search transcript.

    `nodes` and `depth` come from the LAST info line carrying them, which is how
    the engine reports its final completed iteration.
    """
    out = {
        "bestmove": None,
        "score_cp": None,
        "score_mate": None,
        "depth": None,
        "seldepth": None,
        "nodes": None,
        "hashfull": None,
        "time": None,
        "pv": None,
        "n_info": 0,
        "n_info_depth": 0,
        "bail": False,          # empty pv + nodes 0: adjudicated draw
        "pos_refused": False,
        "pos_reply": list(pos_reply or []),
        "raw_tail": lines[-3:],
    }
    for line in lines:
        if line.startswith("bestmove"):
            parts = line.split()
            if len(parts) >= 2:
                out["bestmove"] = parts[1]
            continue
        if not line.startswith("info "):
            continue
        out["n_info"] += 1
        toks = line.split()
        pv = None
        if "pv" in toks:
            i = toks.index("pv")
            pv = " ".join(toks[i + 1:])
        has_depth = False
        for i, t in enumerate(toks):
            if t == "depth" and i + 1 < len(toks):
                out["depth"] = int(toks[i + 1]); has_depth = True
            elif t == "seldepth" and i + 1 < len(toks):
                out["seldepth"] = int(toks[i + 1])
            elif t == "nodes" and i + 1 < len(toks):
                out["nodes"] = int(toks[i + 1])
            elif t == "hashfull" and i + 1 < len(toks):
                out["hashfull"] = int(toks[i + 1])
            elif t == "time" and i + 1 < len(toks):
                out["time"] = int(toks[i + 1])
            elif t == "score" and i + 2 < len(toks):
                if toks[i + 1] == "cp":
                    out["score_cp"] = int(toks[i + 2])
                    out["score_mate"] = None
                elif toks[i + 1] == "mate":
                    out["score_mate"] = int(toks[i + 2])
                    out["score_cp"] = None
        if has_depth:
            out["n_info_depth"] += 1
            # A drawn root prints a bare `pv` token with NOTHING after it, so the
            # value is the empty string, not a missing token. Testing `is None`
            # here missed every real bail; found by inspecting the raw wire.
            if pv is not None:
                out["pv"] = pv
    out["pv_empty"] = (out["pv"] is not None and out["pv"].strip() == "")
    out["bail"] = (out["nodes"] == 0 and out["pv_empty"]
                   and out["bestmove"] not in (None, "0000"))
    for line in out["pos_reply"]:
        if "invalid" in line.lower() or "illegal" in line.lower():
            out["pos_refused"] = True
    return out


def score_key(r):
    """Comparable score token: ('cp', n) / ('mate', n) / (None, None)."""
    if r.get("score_mate") is not None:
        return ("mate", r["score_mate"])
    if r.get("score_cp") is not None:
        return ("cp", r["score_cp"])
    return (None, None)


def close(self):
    try:
        self.send("quit")
    except Exception:
        pass
    try:
        self.p.wait(timeout=5)
    except Exception:
        self.p.kill()


Uci.close = close


def run_one(path, position_cmd, go_cmd, options=(), pre=(), timeout=600.0):
    """Fresh process, apply options, run exactly one search, exit.

    `options` are full `setoption name X value Y` strings. `pre` are extra
    commands sent after the handshake and before the position (e.g. ucinewgame).
    """
    u = Uci(path, timeout=timeout)
    try:
        u.handshake()
        for o in options:
            u.send(o)
        for c in pre:
            u.send(c)
        if options or pre:
            u.send("isready")
            while u.readline() != "readyok":
                pass
        return u.search(position_cmd, go_cmd)
    finally:
        u.close()
