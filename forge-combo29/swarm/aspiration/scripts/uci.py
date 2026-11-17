"""Minimal UCI driver for the aspiration audit.

Rules this enforces (from the shared brief):
  * `quit` is NEVER piped into a live search: every search is read to `bestmove`.
  * A refused FEN is caught. The engine reports `invalid FEN` on the `position`
    command, not in the search output, so the driver reads that reply.
"""
import os
import pathlib
import re
import subprocess

MATE_RE = re.compile(r"score (cp|mate) (-?\d+)")
DEPTH_RE = re.compile(r"\bdepth (\d+)")
SELDEPTH_RE = re.compile(r"\bseldepth (\d+)")
NODES_RE = re.compile(r"\bnodes (\d+)")
TIME_RE = re.compile(r"\btime (\d+)")
PV_RE = re.compile(r"\bpv (.*)$")
ASP_PREFIX = "info string ASPTRACE "
INT_RE = re.compile(r"-?\d+")
# Anchored and possessive-ish (`[^ ]` classes instead of `.+?`), because the
# original `(.+?) type \S+(?: default (.*))?$` backtracked super-linearly on a
# long option line. Only the shape the engine actually emits is accepted.
OPTION_RE = re.compile(r"option name ([^ ](?:[^ ]| [^ ])*?) type [^ ]+(?: default (.*))?$")


class RefusedFen(RuntimeError):
    pass


class EngineDied(RuntimeError):
    pass


def parse_asptrace(payload):
    """`depth=4 a0=-32001 b0=32001 tries=2 fa=-11 fb=43 score=43 exit=exact inside=1 win=...`

    Everything is `key=value`, so a string value (`exit=exact`) is unambiguous.
    Only `win=` is a list: it continues to the end of the line, holding the
    windows actually searched (`alpha/beta`) interleaved with a `[n:low|high|
    abort|]` tag per try.
    """
    out = {"windows": [], "events": []}
    in_win = False
    for tok in payload.split():
        key, sep, value = tok.partition("=")
        if sep and key != "win":
            in_win = False
            out[key] = int(value) if INT_RE.fullmatch(value) else value
            continue
        if key == "win":
            in_win = True
            if value:
                out["windows"].append(value)
            continue
        if in_win:
            if re.fullmatch(r"-?\d+/-?\d+", tok):
                out["windows"].append(tok)
            elif tok.startswith("["):
                out["events"].append(tok)
    return out


def parse_info(line):
    row = {"raw": line, "is_mate": False, "score": None, "score_kind": None}
    m = MATE_RE.search(line)
    if m:
        row["score_kind"] = m.group(1)
        row["score"] = int(m.group(2))
        row["is_mate"] = m.group(1) == "mate"
    for key, rx in (("depth", DEPTH_RE), ("seldepth", SELDEPTH_RE),
                    ("nodes", NODES_RE), ("time", TIME_RE)):
        mm = rx.search(line)
        row[key] = int(mm.group(1)) if mm else None
    m = PV_RE.search(line)
    row["pv"] = m.group(1).split() if m else []
    # This engine prints no `lowerbound` / `upperbound` token at all, so the
    # wire cannot distinguish a value from a bound. Recorded, not guessed.
    row["bound"] = "unstated"
    return row


class Engine:
    """Drives one engine process.

    `path` is executed, so it is accepted only when it resolves to an existing
    executable file. That is not a substitute for trusting the caller — this is
    an audit harness, not a sandbox — but it turns "some string got executed"
    into "a real binary at a known path got executed", which is the property the
    scripts in this folder actually rely on.
    """

    def __init__(self, path, options=None):
        resolved = pathlib.Path(path).resolve()
        if not resolved.is_file() or not os.access(resolved, os.X_OK):
            raise ValueError(f"engine path is not an executable file: {path!r}")
        self.path = str(resolved)
        self.proc = subprocess.Popen(
            [self.path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1)
        self._send("uci")
        self.options = {}
        self._handshake()
        for name, value in (options or {}).items():
            self.setoption(name, value)
        self.sync()

    def _readline(self):
        line = self.proc.stdout.readline()
        if line == "":
            raise EngineDied(f"{self.path} closed stdout")
        return line.rstrip("\n")

    def _send(self, cmd):
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def _handshake(self):
        while True:
            line = self._readline()
            if line.startswith("option name"):
                m = OPTION_RE.match(line)
                if m:
                    self.options[m.group(1).strip()] = (m.group(2) or "").strip()
            elif line.startswith("uciok"):
                return

    def has_option(self, name):
        return name in self.options

    def setoption(self, name, value):
        self._send(f"setoption name {name} value {value}")

    def sync(self):
        self._send("isready")
        while self._readline() != "readyok":
            pass

    def clear_hash(self):
        self._send("setoption name Clear Hash")
        self.sync()

    def newgame(self):
        self._send("ucinewgame")
        self.sync()

    def position(self, fen):
        self._send(f"position fen {fen}")
        # A refused FEN is reported here, on the position command.
        self.sync_refusing()

    def sync_refusing(self):
        """isready flush, watching for an `invalid FEN` diagnostic."""
        self._send("isready")
        while True:
            line = self._readline()
            if "invalid FEN" in line or "Invalid FEN" in line:
                raise RefusedFen(line)
            if line == "readyok":
                return

    def search(self, go, collect_trace=True):
        self._send(go)
        return self._read_to_bestmove(go, collect_trace)

    def _read_to_bestmove(self, go, collect_trace):
        info, strings, traces = [], [], []
        while True:
            line = self._readline()
            if line.startswith("bestmove"):
                parts = line.split()
                return {"info": info, "strings": strings, "traces": traces,
                        "bestmove": parts[1] if len(parts) > 1 else "0000",
                        "bestmove_line": line, "go": go}
            if line.startswith(ASP_PREFIX):
                if collect_trace:
                    traces.append(parse_asptrace(line[len(ASP_PREFIX):]))
                continue
            if line.startswith("info string"):
                strings.append(line)
                continue
            if line.startswith("info "):
                info.append(parse_info(line))

    def close(self):
        try:
            self._send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
