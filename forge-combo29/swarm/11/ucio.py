#!/usr/bin/env python3
"""ucio.py — a small interactive UCI driver for seat 11.

WHY: piping every command at once (`printf '...\\ngo depth 10\\nquit\\n' | forge`) makes the
engine read `quit` while the search is still running, so it aborts and prints NO `info depth`
lines at all. Any harness that reads scores from a fully-piped run measures nothing. This
driver writes a command, then WAITS for the expected reply before sending the next one.

    eng = Engine(exe)
    eng.start()                       # uci -> uciok, options applied
    eng.position(fen or move list)    # position + isready -> readyok
    infos, bm = eng.go("go depth 10")  # writes go, reads until bestmove
    eng.quit()
"""
import queue, subprocess, threading

SAN = ("ERROR: AddressSanitizer", "runtime error:", "SUMMARY:", "ThreadSanitizer")


class Engine:
    def __init__(self, exe, options=(), timeout=300.0, env=None):
        self.exe = exe
        self.options = list(options)
        self.timeout = timeout
        self.env = dict(env or {})
        self.proc = None
        self.q = None
        self.stderr_lines = []
        self.id_name = ""

    def start(self):
        self.proc = subprocess.Popen([self.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1,
                                     env=self.env or None)
        self.q = queue.Queue()
        threading.Thread(target=self._pump, args=(self.proc.stdout, self.q), daemon=True).start()
        self.erq = queue.Queue()
        threading.Thread(target=self._pump, args=(self.proc.stderr, self.erq), daemon=True).start()
        self.send("uci")
        lines = self.read_until("uciok")
        for l in lines:
            if l.startswith("id name"):
                self.id_name = l[7:].strip()
        for opt in self.options:
            # Accept BOTH shapes: the short form "Threads 1" and a complete
            # "setoption name Threads value 1" line. Re-wrapping a complete line would send
            # "setoption name setoption value name Threads value 1" and silently apply nothing.
            if opt.startswith("setoption"):
                line = opt
            else:
                name, _, val = opt.partition(" ")
                line = f"setoption name {name} value {val}"
            self.send(line)
        if self.options:
            self.send("isready")
            self.read_until("readyok")
        return lines

    @staticmethod
    def _pump(stream, q):
        try:
            for line in iter(stream.readline, ""):
                q.put(line.rstrip("\n"))
        except Exception:
            pass
        q.put(None)

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, token, optional=False, timeout=None):
        timeout = timeout or self.timeout
        out = []
        while True:
            try:
                line = self.q.get(timeout=timeout)
            except queue.Empty:
                raise TimeoutError(f"no line while waiting for {token!r}")
            if line is None:
                raise EOFError("engine closed stdout")
            out.append(line)
            if line.strip() == token or line.startswith(token):
                return out

    def position(self, fen=None, moves=None):
        cmd = "position " + (f"fen {fen}" if fen else "startpos")
        if moves:
            cmd += " moves " + " ".join(moves)
        self.send(cmd)
        self.send("isready")
        answer = self.read_until("readyok")
        refused = [l for l in answer if "invalid" in l or "illegal" in l]
        return answer, refused

    def go(self, go_line, timeout=None):
        """Send a go command and read every line up to bestmove. Returns (infos, bestmove, all)."""
        self.send(go_line)
        lines = self.read_until("bestmove", timeout=timeout)
        bm = lines[-1].split()[1] if len(lines[-1].split()) > 1 else None
        infos = [l for l in lines if l.startswith("info")]
        return infos, bm, lines

    def drain_stderr(self):
        while True:
            try:
                l = self.erq.get_nowait()
            except queue.Empty:
                break
            if l is None:
                break
            self.stderr_lines.append(l)
        return [l for l in self.stderr_lines if any(s in l for s in SAN)]

    def quit(self):
        try:
            self.send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
