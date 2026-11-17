#!/usr/bin/env python3
"""Loudness: when the engine refuses a net, is the refusal visible, and does it stop?

A refusal printed on a stream nobody reads, or one that leaves the engine silently
evaluating with the compiled-in network, is not a loud refusal. For each mutant this
records:

  1. the exact text, on stdout and stderr kept apart
  2. whether `isready` still answers readyok (a GUI waiting on it must not hang)
  3. whether a search after the refusal runs, and whether it produces a bestmove
  4. the exit code, and whether the process died mid-protocol
  5. node counts from a search that should NOT have run, as the second proof

DRIVER DISCIPLINE (brief rule 1): never pipe `quit` into a live search. Every
command that can start a search is sent only after the previous one has been read
to its terminal line, and `quit` goes out only once no search is outstanding.

Stdout/stderr are drained by reader threads, not by select() on the buffered text
objects: select() on a TextIOWrapper's fileno() reports nothing while Python is
still holding decoded lines in its own buffer, which makes a perfectly responsive
engine look like it timed out. That defect was in the first version of this script
and cost a 30 s stall per session.

Usage: loudness.py <forge> <manifest.json> <out.json>
"""
import json
import os
import queue
import subprocess
import sys
import threading
import time


class Engine:
    """A real UCI driver: write a command, then read until the expected terminal line."""

    def __init__(self, exe, default_timeout=60.0):
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1)
        self.default_timeout = default_timeout
        self.out_lines = []
        self.err_lines = []
        self.q = queue.Queue()
        self.errq = queue.Queue()
        self._threads = [
            threading.Thread(target=self._pump, args=(self.proc.stdout, self.q, self.out_lines), daemon=True),
            threading.Thread(target=self._pump, args=(self.proc.stderr, self.errq, self.err_lines), daemon=True),
        ]
        for thread in self._threads:
            thread.start()

    @staticmethod
    def _pump(stream, target_queue, sink):
        for line in stream:
            text = line.rstrip("\n")
            sink.append(text)
            target_queue.put(text)
        target_queue.put(None)          # EOF marker

    def send(self, line):
        if self.proc.poll() is not None:
            return False
        try:
            self.proc.stdin.write(line + "\n")
            self.proc.stdin.flush()
            return True
        except (BrokenPipeError, ValueError):
            return False

    def read_until(self, predicate, timeout=None):
        """Read stdout lines until predicate(line), EOF, or the timeout."""
        limit = self.default_timeout if timeout is None else timeout
        deadline = time.monotonic() + limit
        collected = []
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return collected, "timeout"
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty:
                return collected, "timeout"
            if line is None:
                return collected, "eof"
            collected.append(line)
            if predicate(line):
                return collected, "ok"

    def close(self, timeout=20):
        """Quit only when no search is outstanding; then reap."""
        if self.proc.poll() is None:
            self.send("quit")
            try:
                self.proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=timeout)
        time.sleep(0.05)                # let the reader threads drain
        try:
            self.proc.stdin.close()
        except (BrokenPipeError, ValueError):
            pass
        return self.proc.returncode


def run_session(exe, path, search_depth=None):
    eng = Engine(exe)
    rec = {"path": path}

    eng.send("uci")
    eng.read_until(lambda ln: ln.strip() == "uciok", timeout=30)
    eng.send("isready")
    eng.read_until(lambda ln: ln.strip() == "readyok", timeout=30)

    eng.send("setoption name NNUEArchFile value %s" % path)
    # The loader runs synchronously inside setoption; its only reply is an info string.
    load_lines, _ = eng.read_until(
        lambda ln: ln.startswith("info string NNUE v3:") or ln.strip() == "readyok", timeout=180)
    rec["load_reply"] = [ln for ln in load_lines if ln.startswith("info string NNUE v3:")]

    eng.send("isready")
    ready_lines, why = eng.read_until(lambda ln: ln.strip() == "readyok", timeout=30)
    rec["readyok_after_load"] = any(ln.strip() == "readyok" for ln in ready_lines)
    rec["isready_timeout"] = why == "timeout"
    rec["process_alive_after_load"] = eng.proc.poll() is None

    if search_depth is not None and eng.proc.poll() is None:
        eng.send("setoption name NNUEArch value true")
        eng.send("position startpos")
        eng.send("go depth %d" % search_depth)
        search_lines, why3 = eng.read_until(lambda ln: ln.startswith("bestmove"), timeout=120)
        rec["bestmove"] = [ln for ln in search_lines if ln.startswith("bestmove")]
        rec["search_timeout"] = why3 == "timeout"
        rec["search_nodes"] = [ln.split(" nodes ")[1].split()[0]
                               for ln in search_lines if " nodes " in ln]
        rec["search_error_lines"] = [ln for ln in search_lines if "ERROR" in ln]

    rec["alive_before_quit"] = eng.proc.poll() is None
    rec["exit_code"] = eng.close()
    rec["stderr"] = list(eng.err_lines)
    rec["stdout_nnue"] = [ln for ln in eng.out_lines if "NNUE" in ln]
    return rec


def main():
    exe, manifest_path, outpath = sys.argv[1], sys.argv[2], sys.argv[3]
    manifest = json.load(open(manifest_path))
    results = []
    for case in manifest["cases"]:
        path = os.path.join(manifest["outdir"], case["name"] + ".fnn3")
        rec = run_session(exe, path, search_depth=6)
        rec["name"] = case["name"]
        rec["class"] = case["class"]
        rec["expect"] = case["expect"]
        results.append(rec)
        loaded = any("loaded v3" in ln for ln in rec.get("load_reply", []))
        print("%-24s %-9s want %-6s %-6s readyok %-5s bestmove %-2s nodes %-9s err %d exit %s"
              % (case["name"], case["class"], case["expect"],
                 "accept" if loaded else "refuse",
                 rec["readyok_after_load"], len(rec.get("bestmove", [])),
                 (rec.get("search_nodes") or ["-"])[-1], len(rec["stderr"]), rec["exit_code"]))
    with open(outpath, "w") as handle:
        json.dump(results, handle, indent=1)
    print("wrote", outpath)


if __name__ == "__main__":
    main()
