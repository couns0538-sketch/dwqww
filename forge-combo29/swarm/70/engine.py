"""Re-runnable UCI driver for the searchmoves semantics audit. Seat 70.

Every search is one fresh engine process.  The driver:

  * sends  uci -> set options -> ucinewgame -> position -> isready
  * READS THE POSITION REPLY up to readyok and keeps every `info string` in it
  * sends  go <limits> [searchmoves ...]  and reads to `bestmove` with a timeout
  * scans BOTH the position reply and the go output for `invalid FEN`
    (the diagnostic's location depends on whether isready follows position)

A search whose reply stream contained `invalid FEN` is returned with
fatal="invalid FEN" and is never counted as a data point.
"""

import os
import queue
import re
import subprocess
import threading

ENGINE = os.environ.get("FORGE_BIN", "/tmp/build-rel/forge")

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]

SCORE_RE = re.compile(r"\bscore\s+(cp|mate)\s+(-?\d+)\b")
DEPTH_RE = re.compile(r"\binfo\s+depth\s+(\d+)\b")
BEST_RE = re.compile(r"^bestmove\s+(\S+)(?:\s+ponder\s+(\S+))?\s*$")
PERFT_TOTAL_RE = re.compile(r"^nodes\s+(\d+)\s*$", re.M)


class SearchResult:
    __slots__ = ("bestmove", "score_kind", "score", "depth", "info_lines",
                 "position_strings", "fatal", "raw_position", "raw_go")

    def __init__(self):
        self.bestmove = None
        self.score_kind = None
        self.score = None
        self.depth = None
        self.info_lines = []
        self.position_strings = []
        self.fatal = None
        self.raw_position = ""
        self.raw_go = ""

    @property
    def signed_score(self):
        """cp value; mate scores mapped far outside the cp range so ordering is total."""
        if self.score is None:
            return None
        if self.score_kind == "cp":
            return self.score
        return 100000 - self.score if self.score > 0 else -100000 - self.score

    def __repr__(self):
        return (f"<{self.bestmove} {self.score_kind} {self.score} d{self.depth}"
                f"{' FATAL=' + self.fatal if self.fatal else ''}>")


def _reader(stream, sink):
    for line in stream:
        sink.put(line.rstrip("\n"))
    sink.put(None)


class _Session:
    def __init__(self, engine=None, timeout=120.0):
        self.timeout = timeout
        self.proc = subprocess.Popen(
            [engine or ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
        self.sink: queue.Queue = queue.Queue()
        threading.Thread(target=_reader, args=(self.proc.stdout, self.sink), daemon=True).start()
        self.pos_lines = []
        self.go_lines = []
        self.phase = "setup"
        self.fatal = None

    def send(self, text):
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def _emit(self, line):
        if self.phase == "position":
            self.pos_lines.append(line)
        elif self.phase == "go":
            self.go_lines.append(line)

    def read_until(self, predicate, label):
        """Block until predicate(line) or EOF/timeout.  Returns True on success."""
        while True:
            try:
                line = self.sink.get(timeout=self.timeout)
            except queue.Empty:
                self.fatal = f"timeout waiting for {label}"
                return False
            if line is None:
                self.fatal = f"EOF waiting for {label}"
                return False
            self._emit(line)
            if predicate(line):
                return True

    def drain(self, seconds=0.15):
        while True:
            try:
                line = self.sink.get(timeout=seconds)
            except queue.Empty:
                return
            if line is None:
                return
            self._emit(line)
            seconds = 0.02

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
        try:
            self.proc.stdin.close()
        except Exception:
            pass


def run_session(position_cmd, go_cmd, options=None, timeout=120.0, engine=None):
    """One fresh process, one search.  Returns SearchResult."""
    opts = list(S14) if options is None else list(options)
    s = _Session(engine=engine, timeout=timeout)
    res = SearchResult()
    try:
        s.send("uci")
        if not s.read_until(lambda l: l.strip() == "uciok", "uciok"):
            return _finish(res, s)
        for name, value in opts:
            s.send(f"setoption name {name} value {value}")
        s.send("isready")
        if not s.read_until(lambda l: l.strip() == "readyok", "readyok after setoption"):
            return _finish(res, s)

        # ucinewgame must come BEFORE position, or it resets the board to startpos.
        s.send("ucinewgame")
        s.send("isready")
        if not s.read_until(lambda l: l.strip() == "readyok", "readyok after ucinewgame"):
            return _finish(res, s)

        s.phase = "position"
        s.send(position_cmd)
        s.send("isready")
        if not s.read_until(lambda l: l.strip() == "readyok", "readyok after position"):
            return _finish(res, s)

        s.phase = "go"
        s.send(go_cmd)
        if not s.read_until(lambda l: l.strip().startswith("bestmove"), "bestmove"):
            return _finish(res, s)
        s.drain()
    finally:
        s.close()
    return _finish(res, s)


def _finish(res, s):
    res.raw_position = "\n".join(s.pos_lines)
    res.raw_go = "\n".join(s.go_lines)
    res.position_strings = [l for l in s.pos_lines if l.startswith("info string")]

    # Defence from the brief: scan BOTH streams for the FEN diagnostic.
    for line in s.pos_lines + s.go_lines:
        if "invalid FEN" in line:
            res.fatal = "invalid FEN"
            break
        if "illegal move" in line:
            res.fatal = "illegal move"
            break

    for line in s.go_lines:
        m = BEST_RE.match(line.strip())
        if m:
            res.bestmove = m.group(1)
            continue
        sm = SCORE_RE.search(line)
        dm = DEPTH_RE.search(line)
        if sm:
            res.info_lines.append(line)
            res.score_kind = sm.group(1)
            res.score = int(sm.group(2))
        if dm:
            res.depth = max(res.depth or 0, int(dm.group(1)))
    if res.fatal is None and s.fatal:
        res.fatal = s.fatal
    return res


def perft_count(fen, depth, engine=None, timeout=300.0):
    """`go perft <depth>` node total.  `go perft` ends at `nodes N`, never at `bestmove`."""
    s = _Session(engine=engine, timeout=timeout)
    try:
        s.send("uci")
        if not s.read_until(lambda l: l.strip() == "uciok", "uciok"):
            return None, s.fatal, ""
        s.send("isready")
        if not s.read_until(lambda l: l.strip() == "readyok", "readyok"):
            return None, s.fatal, ""
        s.phase = "position"
        s.send(f"position fen {fen}")
        s.send("isready")
        if not s.read_until(lambda l: l.strip() == "readyok", "readyok after position"):
            return None, s.fatal, "\n".join(s.pos_lines)
        s.phase = "go"
        s.send(f"go perft {depth}")
        if not s.read_until(lambda l: PERFT_TOTAL_RE.match(l), f"perft {depth} total"):
            return None, s.fatal, "\n".join(s.go_lines)
        s.drain()
    finally:
        s.close()
    pos_text = "\n".join(s.pos_lines)
    for line in s.pos_lines + s.go_lines:
        if "invalid FEN" in line:
            return None, "invalid FEN", pos_text
    m = PERFT_TOTAL_RE.search("\n".join(s.go_lines))
    return (int(m.group(1)) if m else None), None, pos_text


def perft1(fen, engine=None):
    """perft-1 node count, an independent check that the engine holds the board we meant."""
    n, err, pos = perft_count(fen, 1, engine=engine)
    return n, err, pos
