#!/usr/bin/env python3
"""Native UCI regression for external Polyglot Book File and OwnBook=false.

--expect-leak=yes: authentic unfixed baseline MUST use book despite OwnBook=false.
--expect-leak=no: corrected candidate MUST NOT use book with OwnBook=false.
Both must use the fixture when OwnBook=true, and bypass it for depth analysis.
Writes unmodified UCI transcript and machine-readable results.
"""
import argparse
import hashlib
import json
import pathlib
import queue
import re
import struct
import subprocess
import tempfile
import threading
import time

KEY = 0x463B96181691FC9C
E2E4 = (12 << 6) | 28

class UCI:
    def __init__(self, exe):
        self.p = subprocess.Popen([str(exe.resolve())], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1)
        self.records = []
        self.q = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        for raw in self.p.stdout:
            line = raw.rstrip("\r\n")
            self.records.append("< " + line)
            self.q.put(line)
        self.q.put(None)

    def send(self, command):
        self.records.append("> " + command)
        self.p.stdin.write(command + "\n")
        self.p.stdin.flush()

    def until(self, pred, timeout=25):
        deadline = time.monotonic() + timeout
        seen = []
        while True:
            remain = deadline - time.monotonic()
            if remain <= 0:
                raise AssertionError("UCI timeout: " + repr(seen[-20:]))
            try:
                line = self.q.get(timeout=remain)
            except queue.Empty:
                raise AssertionError("UCI timeout: " + repr(seen[-20:])) from None
            if line is None:
                raise AssertionError("engine exited: " + repr(seen[-20:]))
            seen.append(line)
            if pred(line):
                return seen

    def ready(self):
        self.send("isready")
        return self.until(lambda x: x == "readyok")

    def search(self, cmd):
        self.send("position startpos")
        self.ready()
        self.send(cmd)
        rows = self.until(lambda x: x.startswith("bestmove "))
        best = rows[-1].split()[1]
        assert re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?", best), best
        book_rows = [x for x in rows if x.startswith("info string book move ")]
        return {"move": best, "book": bool(book_rows), "lines": rows}

    def close(self):
        if self.p.poll() is None:
            self.send("quit")
            try:
                self.p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.p.kill()
                self.p.wait()
                raise AssertionError("quit deadline")
        self.reader.join(timeout=2)
        assert self.p.returncode == 0, self.p.returncode

def run(exe, expected_leak, out):
    out.mkdir(parents=True, exist_ok=True)
    report = {"expected_baseline_leak": expected_leak,
              "tests": [], "result": "FAIL"}
    client = None
    try:
        with tempfile.TemporaryDirectory(prefix="forge-book-") as d:
            filename = pathlib.Path(d) / "book with spaces.bin"
            record = struct.pack(">QHHI", KEY, E2E4, 100, 0)
            assert len(record) == 16
            filename.write_bytes(record)
            report["fixture_sha256"] = hashlib.sha256(record).hexdigest()
            client = UCI(exe)
            client.send("uci")
            hello = client.until(lambda x: x == "uciok")
            assert any(x.startswith("id name Chess Engine Forge") for x in hello), hello
            client.ready()
            for cmd in ("setoption name OwnBook value false",
                        "setoption name Book Variety value 0",
                        "setoption name Book Depth value 30",
                        "setoption name Book File value " + str(filename)):
                client.send(cmd)
            loaded = client.ready()
            assert any("info string loaded book " in x and
                       " with 1 entries" in x for x in loaded), loaded
            report["tests"].append("one-entry Polyglot fixture loaded")
            disabled = client.search("go movetime 150")
            report["disabled_first"] = disabled["book"]
            assert disabled["book"] == expected_leak, disabled
            report["tests"].append("original bypass reproduced" if expected_leak else
                                   "OwnBook false respected")
            client.send("setoption name OwnBook value true")
            client.ready()
            enabled = client.search("go movetime 150")
            report["enabled"] = enabled["book"]
            assert enabled["book"] and enabled["move"] == "e2e4", enabled
            report["tests"].append("enabled external book selects e2e4")
            analyzed = client.search("go depth 2")
            assert not analyzed["book"], analyzed
            report["tests"].append("depth analysis bypasses book")
            client.send("setoption name OwnBook value false")
            client.ready()
            again = client.search("go movetime 150")
            report["disabled_after_toggle"] = again["book"]
            assert again["book"] == expected_leak, again
            report["tests"].append("post-toggle behavior verified")
            report["result"] = "PASS"
    except Exception as exc:
        report["error"] = type(exc).__name__ + ": " + str(exc)
    finally:
        if client is not None:
            try:
                client.close()
            except Exception as exc:
                report["close_error"] = str(exc)
                report["result"] = "FAIL"
            (out / "raw_uci.log").write_text("\n".join(client.records) + "\n")
        (out / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["result"] == "PASS" else 1

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("exe", type=pathlib.Path)
    p.add_argument("--expect-leak", choices=("yes", "no"), required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    raise SystemExit(run(a.exe, a.expect_leak == "yes", a.out))
