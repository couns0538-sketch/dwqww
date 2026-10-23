"""TEST ONLY: this runner's /proc uses different PIDs from its PID namespace.

Use POSIX syscalls for the psutil operations exercised by the Linux integration
test. This file is never needed, imported or shipped as a production dependency.
Windows affinity/priority behavior is separately tested with mocked psutil calls.
"""
import os
import time
import psutil


class NamespaceProcess:
    def __init__(self, pid=None):
        self.pid = os.getpid() if pid is None else pid
        if not self.is_running():
            raise psutil.NoSuchProcess(self.pid)

    def is_running(self):
        try:
            os.kill(self.pid, 0)
            return True
        except ProcessLookupError:
            return False

    def cpu_affinity(self, values=None):
        if values is not None:
            os.sched_setaffinity(self.pid, values)
        return sorted(os.sched_getaffinity(self.pid))

    def nice(self, value=None):
        if value is not None:
            os.setpriority(os.PRIO_PROCESS, self.pid, value)
        return os.getpriority(os.PRIO_PROCESS, self.pid)

    def wait(self, timeout=None):
        start = time.monotonic()
        while self.is_running():
            if timeout is not None and time.monotonic() - start >= timeout:
                raise psutil.TimeoutExpired(timeout, pid=self.pid)
            time.sleep(0.01)

    def kill(self):
        try:
            os.kill(self.pid, 9)
        except ProcessLookupError:
            raise psutil.NoSuchProcess(self.pid)


psutil.Process = NamespaceProcess
