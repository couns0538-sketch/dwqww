"""A UCI driver that reads to bestmove before sending anything else.

Why this exists: `printf '...\\ngo depth 8\\nquit\\n' | ./forge` makes the engine
abort and fabricate a bestmove with zero info lines (brief rule 1, five seats
have hit it). Nothing here writes to stdin while a search is running, and
`quit` is only ever sent after the bestmove line has been read.
"""
import queue
import re
import subprocess
import threading
import time

INFO_DEPTH = re.compile(
    r"^info depth (\d+)(?: multipv (\d+))? seldepth (\d+) score (cp|mate) (-?\d+)"
    r"(?: .*?)? nodes (\d+) nps (\d+) hashfull (\d+) time (\d+)(?: pv (.*))?$"
)


class Engine:
    """One long-lived process. Sequential `go` calls share the transposition table,
    which is the whole point: no `setoption Hash` re-send (that clears the table)."""

    def __init__(self, exe, hash_mb=16, timeout=180.0):
        self.exe = exe
        self.timeout = timeout
        self.proc = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
        self.q = queue.Queue()
        self.lines = []
        threading.Thread(target=self._pump, daemon=True).start()
        self.send("uci")
        self.wait_for(lambda l: l.strip() == "uciok")
        self.send("setoption name Threads value 1")
        if hash_mb is not None:
            self.send(f"setoption name Hash value {hash_mb}")
        self.send("setoption name OwnBook value false")
        self.sync()

    def _pump(self):
        for line in self.proc.stdout:
            self.q.put(line.rstrip("\r\n"))
        self.q.put(None)

    def send(self, cmd):
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def _next(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        try:
            return self.q.get(timeout=remaining)
        except queue.Empty:
            return None

    def wait_for(self, pred, collect=False):
        deadline = time.monotonic() + self.timeout
        seen = []
        while True:
            line = self._next(deadline)
            if line is None:
                if collect:
                    raise TimeoutError(f"no match within {self.timeout}s; last line {seen[-1] if seen else None!r}")
                raise TimeoutError(f"no match within {self.timeout}s")
            seen.append(line)
            if pred(line):
                return seen if collect else line

    def sync(self):
        """isready/readyok, keeping every line seen so a caller can inspect what the
        preceding command said (e.g. `info string invalid FEN`)."""
        self.send("isready")
        self.last_sync_lines = self.wait_for(lambda l: l.strip() == "readyok", collect=True)
        return self.last_sync_lines

    def uci(self, cmd):
        """Send one command and return every line up to and including bestmove."""
        self.send(cmd)
        return self.wait_for(lambda l: l.startswith("bestmove"), collect=True)

    def search(self, posline, go, collect_all=False):
        # Lines emitted by `position` (notably `info string invalid FEN`) arrive
        # before `go` and must be captured here, not skipped.
        self.send(posline)
        self.sync()                      # forces the position reply to be flushed
        pre = self.last_sync_lines
        self.send(go)
        lines = pre + self.wait_for(lambda l: l.startswith("bestmove"), collect=True)
        infos = [INFO_DEPTH.match(l) for l in lines]
        infos = [m for m in infos if m]
        best = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
        last = infos[-1] if infos else None
        row = {
            "pos": posline,
            "go": go,
            "bestmove": best,
            "invalid_fen": any("invalid FEN" in l for l in lines),
            "illegal_move": any("illegal move" in l for l in pre),
            "depth": int(last.group(1)) if last else None,
            "score_kind": last.group(4) if last else None,
            "score": int(last.group(5)) if last else None,
            "nodes": int(last.group(6)) if last else None,
            "hashfull": int(last.group(8)) if last else None,
            "time_ms": int(last.group(9)) if last else None,
            "pv": (last.group(10) or "").split() if last else [],
            "info_lines": len(infos),
        }
        if collect_all:
            row["all"] = lines
        return row

    def close(self):
        try:
            self.send("quit")
            self.proc.stdin.close()
        except OSError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
