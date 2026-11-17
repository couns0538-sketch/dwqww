"""Robust minimal UCI client for the hash-resize audit.

Two rules from the audit are encoded here:
  * never use `select()` + `.readline()` on a buffered pipe (forge-findings.md S7.2);
  * never let EOF reach a running search (S7.3a), so `quit()` waits for `bestmove`.
"""

import os
import select
import subprocess
import time

ENGINE = "/tmp/work/base/forge-combo29/build/forge"


class Engine:
    def __init__(self, path=ENGINE, cpu_affinity=None, stderr_to_file=None):
        self.path = path
        if stderr_to_file:
            self.errfh = open(stderr_to_file, "wb")
            stderr = self.errfh
        else:
            self.errfh = None
            stderr = subprocess.DEVNULL
        self.p = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr,
            bufsize=0,
        )
        if cpu_affinity is not None:
            try:
                os.sched_setaffinity(self.p.pid, {cpu_affinity})
            except OSError:
                pass
        self.fd = self.p.stdout.fileno()
        self.buf = b""
        self.eof = False

    # -- io ---------------------------------------------------------------
    def send(self, line):
        self.p.stdin.write((line + "\n").encode())
        self.p.stdin.flush()

    def _fill(self, timeout):
        r, _, _ = select.select([self.fd], [], [], timeout)
        if not r:
            return False
        chunk = os.read(self.fd, 1 << 16)
        if not chunk:
            self.eof = True
            return False
        self.buf += chunk
        return True

    def _take_line(self):
        if b"\n" not in self.buf:
            return None
        raw, self.buf = self.buf.split(b"\n", 1)
        return raw.decode("utf-8", "replace").rstrip("\r")

    def lines_until(self, prefix, timeout=600.0):
        """Collect lines up to and including one starting with `prefix`."""
        out = []
        deadline = time.time() + timeout
        while True:
            line = self._take_line()
            if line is not None:
                out.append(line)
                if line.startswith(prefix):
                    return out, True
                continue
            if self.eof:
                return out, False
            remaining = deadline - time.time()
            if remaining <= 0:
                return out, False
            self._fill(min(0.25, remaining))

    def drain(self, quiet_for=0.03, cap=5.0):
        """Read whatever is pending until the stream goes quiet for `quiet_for`."""
        out = []
        deadline = time.time() + cap
        while time.time() < deadline:
            line = self._take_line()
            if line is not None:
                out.append(line)
                continue
            if self.eof:
                break
            if not self._fill(quiet_for):
                break
        return out

    # -- protocol ---------------------------------------------------------
    def handshake(self):
        self.send("uci")
        lines, ok = self.lines_until("uciok", timeout=60)
        if not ok:
            raise RuntimeError("no uciok")
        return lines

    def sync(self, timeout=120.0):
        self.send("isready")
        lines, ok = self.lines_until("readyok", timeout=timeout)
        if not ok:
            raise RuntimeError("no readyok")
        return [l for l in lines if not l.startswith("readyok")]

    def setoption(self, name, value=None):
        cmd = "setoption name " + name
        if value is not None:
            cmd += " value " + str(value)
        self.send(cmd)
        return self.sync()

    def newgame(self):
        self.send("ucinewgame")
        return self.sync()

    def search(self, position_cmd, go_cmd, timeout=600.0):
        self.send(position_cmd)
        self.send(go_cmd)
        lines, ok = self.lines_until("bestmove", timeout=timeout)
        return summarize(lines, ok)

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=15)
        except Exception:
            try:
                self.p.kill()
            except Exception:
                pass
        try:
            self.p.stdout.close()
        except Exception:
            pass
        try:
            if self.errfh is not None:
                self.errfh.close()
        except Exception:
            pass


def summarize(lines, ok):
    bestmove = None
    depth_lines = []
    infos = []
    for line in lines:
        if line.startswith("bestmove"):
            toks = line.split()
            bestmove = toks[1] if len(toks) > 1 else None
        elif line.startswith("info depth"):
            depth_lines.append(line)
            infos.append(parse_info(line))
        elif line.startswith("info string"):
            infos.append({"string": line})
    last = infos[-1] if infos else {}
    return {
        "ok": ok,
        "bestmove": bestmove,
        "depth": last.get("depth"),
        "seldepth": last.get("seldepth"),
        "nodes": last.get("nodes"),
        "score": last.get("score"),
        "score_kind": last.get("score_kind"),
        "hashfull": last.get("hashfull"),
        "pv": last.get("pv"),
        "info_depth_lines": len(depth_lines),
        "info_strings": [i["string"] for i in infos if "string" in i],
        "lines": lines,
    }


def parse_info(line):
    toks = line.split()
    fields = {}
    i = 1
    while i < len(toks):
        k = toks[i]
        if k in ("depth", "seldepth", "multipv", "nodes", "nps", "time", "hashfull", "tbhits"):
            try:
                fields[k] = int(toks[i + 1])
            except (IndexError, ValueError):
                pass
            i += 2
        elif k == "score":
            fields["score_kind"] = toks[i + 1] if i + 1 < len(toks) else None
            try:
                fields["score"] = int(toks[i + 2])
            except (IndexError, ValueError):
                pass
            i += 3
        elif k == "pv":
            fields["pv"] = toks[i + 1:]
            break
        else:
            i += 1
    return fields


def proc_mem(pid):
    out = {}
    try:
        with open("/proc/%d/status" % pid) as fh:
            for line in fh:
                if line.startswith(("VmRSS", "VmHWM", "VmSize", "VmPeak", "VmData")):
                    key, val = line.split(":", 1)
                    out[key] = int(val.split()[0])
    except OSError:
        pass
    return out
