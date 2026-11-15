#!/usr/bin/env python3
"""Job 3 A2: the checking build (-DFORGE_NNUE_V3_VERIFY=1) over a net and 500 positions.

The checking build compares every evaluation made inside the search with
evaluate_reference and calls std::_Exit(3) on a difference, so a run that ends with
exit code 0 and no "verification mismatch" line means every incremental evaluation
agreed with the reference.

go depth 8, Threads 1 then Threads 4, one process each, waiting for bestmove.

Usage: a2_verify_build.py <net> <fens> <outdir> <tag>
"""
import json
import os
import subprocess
import sys
import threading
import queue
import time

ENGINE = "/tmp/ds/build-verify/forge"


class Run:
    """One engine process; stdout drained on a thread so nothing is lost."""

    def __init__(self, threads, out_path, err_path):
        self.out = open(out_path, "w")
        self.err = open(err_path, "w")
        self.proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=self.err, text=True, bufsize=1)
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._read, daemon=True)
        self.t.start()
        self.send(f"setoption name Threads value {threads}")
        self.send("setoption name Hash value 16")

    def _read(self):
        for line in self.proc.stdout:
            self.out.write(line)
            self.out.flush()
            self.q.put(line.rstrip("\n"))
        self.q.put(None)

    def send(self, command):
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def until(self, needle, timeout):
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty:
                return None
            if line is None:
                return None
            if line.startswith(needle):
                return line

    def close(self):
        try:
            self.send("quit")
        except (BrokenPipeError, ValueError):
            pass
        try:
            self.proc.wait(timeout=120)
            code = self.proc.returncode
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
            code = "did-not-quit"
        self.t.join(timeout=10)
        self.out.close()
        self.err.close()
        return code


def run_one(net, fens, threads, out_path, err_path):
    run = Run(threads, out_path, err_path)
    run.send(f"setoption name NNUEArchFile value {net}")
    run.send("setoption name NNUEArch value true")
    run.send("isready")
    if run.until("readyok", 300) is None:
        run.close()
        return {"error": "no readyok (net did not load?)"}
    no_bestmove = 0
    done = 0
    t0 = time.time()
    for i, fen in enumerate(fens):
        run.send(f"position fen {fen}")
        run.send("go depth 8")
        if run.until("bestmove", 600) is None:
            no_bestmove += 1
            break
        done += 1
    code = run.close()
    return {"threads": threads, "positions": done, "no_bestmove": no_bestmove,
            "exit_code": code, "wall_s": round(time.time() - t0, 1)}


def main():
    net, fens_path, outdir, tag = sys.argv[1:5]
    os.makedirs(outdir, exist_ok=True)
    with open(fens_path) as f:
        fens = [l.strip() for l in f if l.strip()]
    results = []
    for threads in (1, 4):
        r = run_one(net, fens, threads,
                    f"{outdir}/A2-{tag}-t{threads}.stdout.log",
                    f"{outdir}/A2-{tag}-t{threads}.stderr.log")
        # The checking code prints "NNUE v3 verification mismatch ..." on stdout? It uses
        # std::cerr, so look in both logs.
        mismatch_lines = 0
        for path in (f"{outdir}/A2-{tag}-t{threads}.stdout.log",
                     f"{outdir}/A2-{tag}-t{threads}.stderr.log"):
            try:
                with open(path, errors="replace") as f:
                    mismatch_lines += sum(1 for line in f if "verification mismatch" in line)
            except OSError:
                pass
        r["verification_mismatch_lines"] = mismatch_lines
        stderr_size = os.path.getsize(f"{outdir}/A2-{tag}-t{threads}.stderr.log")
        r["stderr_bytes"] = stderr_size
        results.append(r)
    summary = {"net": net, "tag": tag, "positions_supplied": len(fens), "runs": results}
    with open(f"{outdir}/A2-{tag}.summary.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
