#!/usr/bin/env python3
"""Minimal UCI client: line reader thread, never sends anything before a bestmove arrives."""
import subprocess, threading, queue, time, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uciparse import info_record


class Engine:
    def __init__(self, path, cwd=None):
        self.path = path
        self.p = subprocess.Popen([path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1, cwd=cwd)
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._reader, daemon=True)
        self.t.start()

    def _reader(self):
        for line in self.p.stdout:
            self.q.put(line.rstrip("\n"))
        self.q.put(None)

    def send(self, cmd):
        self.p.stdin.write(cmd + "\n")
        self.p.stdin.flush()

    def read_until(self, pred, timeout=600.0):
        """Read lines until pred(line) is true. Returns collected lines. Never returns early."""
        out, t0 = [], time.time()
        while True:
            try:
                line = self.q.get(timeout=max(1.0, timeout - (time.time() - t0)))
            except queue.Empty:
                raise TimeoutError(f"timeout after {timeout}s waiting for {pred}")
            if line is None:
                raise EOFError("engine closed stdout")
            out.append(line)
            if pred(line):
                return out
            if time.time() - t0 > timeout:
                raise TimeoutError(f"timeout waiting for {pred}")

    def sync(self):
        self.send("isready")
        self.read_until(lambda l: l.strip() == "readyok")

    def uci(self):
        self.send("uci")
        return self.read_until(lambda l: l.strip() == "uciok")

    def rss_kb(self):
        try:
            with open(f"/proc/{self.p.pid}/status", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1])
        except OSError:
            return None
        return None

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def parse_info_lines(lines):
    """Per-depth records from the info lines; the last one is the deepest completed iteration.

    Delegates to uciparse.info_record, which returns None for a field the line does not carry
    rather than an index error or a guess.
    """
    return [rec for rec in (info_record(line) for line in lines) if rec is not None]


def search(eng, position_cmd, go_cmd="go depth 8", timeout=600.0):
    """Send position then go; return dict with bestmove, deepest info, all info records."""
    eng.send(position_cmd)
    eng.send(go_cmd)
    lines = eng.read_until(lambda l: l.startswith("bestmove"), timeout=timeout)
    bm = lines[-1].split()[1] if len(lines[-1].split()) > 1 else None
    recs = parse_info_lines(lines[:-1])
    deepest = recs[-1] if recs else None
    return {
        "bestmove": bm,
        "score": deepest["score"] if deepest else None,
        "nodes": deepest["nodes"] if deepest else None,
        "depth": deepest["depth"] if deepest else None,
        "seldepth": deepest["seldepth"] if deepest else None,
        "hashfull": deepest["hashfull"] if deepest else None,
        "time_ms": deepest["time"] if deepest else None,
        "pv": deepest["pv"] if deepest else [],
        "n_info": len(recs),
        "info": lines[:-1],
    }
