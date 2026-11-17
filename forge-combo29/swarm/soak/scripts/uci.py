"""Minimal, non-blocking UCI driver for soak measurements.

Design rules taken from the findings doc (S6/S7):
 - never let EOF reach a running search: we always read to `bestmove` (or `nodes N` for perft)
   before sending anything else, and we never close stdin while a search is active.
 - os.read() on a non-blocking fd, with a hard deadline. select()+.readline() is not a timeout.
 - every setoption / position is followed by isready and all lines up to readyok are read;
   `unknown option`, `invalid value`, `invalid FEN`, `illegal move` are errors unless the
   caller asked for a tolerant run.
 - the position reply is what carries `invalid FEN`, so we scan the reply we accumulate
   from the position command, not only the go output.
"""

import os
import re
import select
import subprocess
import time


class EngineError(RuntimeError):
    pass


class Engine:
    def __init__(self, exe, args=None, env=None, options=None):
        self.exe = exe
        e = dict(os.environ)
        if env:
            e.update(env)
        self.proc = subprocess.Popen(
            [exe] + (args or []),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            env=e,
        )
        self.buf = b""
        self.sent = []          # every option line sent, for the .meta file
        self.id_name = None
        self._handshake(options or {})

    # ---------- low level ----------
    def write(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def _fd(self):
        return self.proc.stdout.fileno()

    def read_until(self, pred, deadline_s, what):
        """Accumulate lines until pred(list_of_lines_since_last_call) is true.

        Returns (matched_lines, all_lines). Raises EngineError on deadline or EOF.
        """
        os.set_blocking(self._fd(), False)
        all_lines = []
        end = time.monotonic() + deadline_s
        while True:
            while b"\n" in self.buf:
                raw, self.buf = self.buf.split(b"\n", 1)
                line = raw.decode("utf-8", "replace").rstrip("\r")
                all_lines.append(line)
                if pred(all_lines):
                    return all_lines
            left = end - time.monotonic()
            if left <= 0:
                raise EngineError("timeout after %.1fs waiting for %s; got %r"
                                  % (deadline_s, what, all_lines[-3:]))
            r, _, _ = select.select([self._fd()], [], [], min(left, 0.5))
            if r:
                chunk = os.read(self._fd(), 65536)
                if not chunk:
                    raise EngineError("EOF from engine while waiting for %s" % what)
                self.buf += chunk

    def read_to_readyok(self, deadline_s=30.0):
        return self.read_until(lambda ls: ls and ls[-1].startswith("readyok"),
                               deadline_s, "readyok")

    def _send_expect(self, line, deadline_s=30.0):
        self.write(line)
        self.write("isready")
        return self.read_to_readyok(deadline_s)

    @staticmethod
    def _bad(lines, tolerant):
        if tolerant:
            return []
        bad = [l for l in lines
               if l.startswith("info string unknown option")
               or l.startswith("info string invalid value")
               or l.startswith("info string invalid FEN")
               or l.startswith("info string illegal move")]
        if bad:
            raise EngineError("engine refused input: %r" % (bad,))
        return bad

    # ---------- handshake ----------
    def _handshake(self, options):
        self.write("uci")
        lines = self.read_until(lambda ls: ls and ls[-1].startswith("uciok"), 30, "uciok")
        for l in lines:
            if l.startswith("id name "):
                self.id_name = l[len("id name "):]
        self.option_lines = [l for l in lines if l.startswith("option name ")]
        self._send_expect("setoption name OwnBook value false")
        self.sent.append("setoption name OwnBook value false")
        for name, value in options.items():
            self.setoption(name, value)

    def setoption(self, name, value):
        line = "setoption name %s value %s" % (name, value)
        self.sent.append(line)
        lines = self._send_expect(line)
        self._bad(lines, False)
        return lines

    def newgame(self):
        self.write("ucinewgame")
        self.write("isready")
        return self.read_to_readyok(60)

    def position_fen(self, fen, tolerant=False):
        lines = self._send_expect("position fen " + fen)
        self._bad(lines, tolerant)
        return lines

    def position_startpos_moves(self, moves, tolerant=False):
        lines = self._send_expect("position startpos moves " + " ".join(moves))
        self._bad(lines, tolerant)
        return lines

    # ---------- search ----------
    def go(self, cmd="go depth 12", deadline_s=600.0):
        """Run one search. Returns dict with bestmove, last info, all info lines."""
        self.write(cmd)
        lines = self.read_until(lambda ls: ls and ls[-1].startswith("bestmove"),
                                deadline_s, "bestmove")
        best = lines[-1].split()[1] if len(lines[-1].split()) > 1 else None
        infos = [l for l in lines if l.startswith("info ") and " pv " in l or
                 (l.startswith("info depth") and " pv " not in l)]
        depth_lines = [l for l in lines if l.startswith("info depth")]
        last = depth_lines[-1] if depth_lines else None
        nodes = None
        if last:
            m = re.search(r"\bnodes (\d+)", last)
            if m:
                nodes = int(m.group(1))
        return {"bestmove": best, "lines": lines, "info": depth_lines,
                "last": last, "nodes": nodes, "n_depth_lines": len(depth_lines)}

    def perft(self, n, deadline_s=600.0):
        self.write("go perft %d" % n)
        lines = self.read_until(
            lambda ls: any(l.startswith("nodes ") for l in ls), deadline_s, "nodes")
        for l in lines:
            if l.startswith("nodes "):
                return int(l.split()[1])
        raise EngineError("no nodes line")

    def bench(self, depth, deadline_s=1800.0):
        self.write("bench %d" % depth)
        lines = self.read_until(
            lambda ls: any(l.startswith("nodes ") for l in ls), deadline_s, "nodes")
        for l in lines:
            if l.startswith("nodes "):
                return int(l.split()[1])
        raise EngineError("no nodes line in bench")

    # ---------- lifecycle ----------
    def quit(self, deadline_s=10.0):
        try:
            self.write("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=deadline_s)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
            return "killed"
        return "exited"

    def rss_kb(self):
        """Resident set size of the engine process, in kB, read from /proc."""
        with open("/proc/%d/status" % self.proc.pid) as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
        return None

    def vm_kb(self):
        with open("/proc/%d/status" % self.proc.pid) as f:
            out = {}
            for line in f:
                if line.startswith(("VmRSS:", "VmPeak:", "VmSize:", "VmHWM:")):
                    k = line.split(":")[0]
                    out[k] = int(line.split()[1])
            return out

    def alive(self):
        return self.proc.poll() is None
