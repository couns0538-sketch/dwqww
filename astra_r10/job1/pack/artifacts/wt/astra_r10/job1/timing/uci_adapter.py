"""R9 reviewed Engine lifecycle, copied for R10 timing; create-new logs and bounded startup.

IDEA_SOURCE: Forge R9 validate_uci.py, f43a26ae; project-owned code.
Only children created by this class can be terminated by it.
"""
import pathlib
import queue
import re
import subprocess
import sys
import threading
import time
sys.path.insert(0, 'D:/a10/pydeps')
import psutil


class Engine:
    def __init__(self, exe, log, on=False, timeout=30):
        self.log = open(log, 'x', encoding='utf-8')
        self.q = queue.Queue()
        self.p = None
        self.reader = None
        def pump():
            try:
                for line in self.p.stdout:
                    self.log.write(line); self.log.flush(); self.q.put(line.strip())
            finally:
                self.q.put(None)
        try:
            self.p = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, text=True,
                                      creationflags=subprocess.IDLE_PRIORITY_CLASS)
            process = psutil.Process(self.p.pid)
            process.cpu_affinity([2])
            if process.nice() != psutil.IDLE_PRIORITY_CLASS or process.cpu_affinity() != [2]:
                raise RuntimeError('engine scheduling differs')
            self.reader = threading.Thread(target=pump, daemon=True)
            self.reader.start()
            self.send('uci'); self.options = '\n'.join(self.wait('^uciok$', timeout))
            for expected in ('option name Threads type spin default 1 ', 'option name Hash type spin ', 'option name OwnBook type check '):
                if expected not in self.options:
                    raise RuntimeError('missing expected UCI option: ' + expected)
            for name, value in [('Threads','1'), ('Hash','16'), ('OwnBook','false')]:
                self.send(f'setoption name {name} value {value}')
            if on:
                if 'option name NNUEWideOutput type check default false' not in self.options:
                    raise RuntimeError('missing default-off wide option')
                self.send('setoption name NNUEWideOutput value true')
            self.send('isready'); self.wait('^readyok$', timeout)
        except BaseException:
            self.abort(); raise

    def send(self, text):
        self.log.write('> ' + text + '\n'); self.log.flush()
        self.p.stdin.write(text + '\n'); self.p.stdin.flush()

    def wait(self, pattern, timeout=300):
        end = time.monotonic() + timeout
        lines = []
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('absolute UCI deadline: ' + pattern)
            line = self.q.get(timeout=remaining)
            if line is None:
                raise RuntimeError('engine exited: ' + str(self.p.poll()))
            lines.append(line)
            if re.search(pattern, line):
                return lines

    def close(self):
        if self.p.poll() is None:
            self.send('quit')
            try:
                self.p.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.p.kill(); self.p.wait(); raise
        self.reader.join(timeout=5)
        if self.reader.is_alive():
            raise RuntimeError('transcript drain incomplete')
        self.log.close()
        if self.p.returncode != 0:
            raise RuntimeError('engine exit ' + str(self.p.returncode))

    def abort(self):
        if self.p is not None and self.p.poll() is None:
            self.p.kill(); self.p.wait(timeout=15)
        if self.reader is not None:
            self.reader.join(timeout=5)
        self.log.close()
