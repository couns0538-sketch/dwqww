#!/usr/bin/env python3
"""seat 17: run the engine under valgrind memcheck with a proper UCI driver.

Sends each command, waits for its answer (readyok / bestmove) before the next, so `quit`
never races a running search. Collects memcheck's own report from stderr.

usage: vg_run.py <exe> <cmds-file> <outdir> <tag>
cmds-file: one command per line, the same grammar the uci_driver uses.
"""
import os
import subprocess
import sys
import time


def main():
    exe, cmds_file, outdir, tag = sys.argv[1:5]
    os.makedirs(outdir, exist_ok=True)
    commands = [line.rstrip("\n") for line in open(cmds_file) if line.strip()]
    log_path = os.path.join(outdir, tag + ".engine.log")
    vg_path = os.path.join(outdir, tag + ".valgrind.log")

    with open(vg_path, "w") as vg_handle:
        proc = subprocess.Popen(
            ["valgrind", "--error-exitcode=9", "--track-origins=yes", "--num-callers=25",
             "--leak-check=no", exe],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=vg_handle,
            text=True, bufsize=1)
        out = []
        start = time.monotonic()
        for line in commands:
            proc.stdin.write(line + "\n")
            proc.stdin.flush()
            if line.startswith("go"):
                deadline = time.monotonic() + 300
                while time.monotonic() < deadline:
                    reply = proc.stdout.readline()
                    if reply == "":
                        break
                    out.append(reply.rstrip("\n"))
                    if reply.startswith("bestmove"):
                        break
            elif line == "isready" or line.startswith("setoption"):
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    reply = proc.stdout.readline()
                    if reply == "":
                        break
                    out.append(reply.rstrip("\n"))
                    if reply.strip() == "readyok":
                        break
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        try:
            rc = proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()
            rc = proc.wait()
    with open(log_path, "w") as handle:
        handle.write("\n".join(out) + "\n")
    elapsed = time.monotonic() - start
    report = open(vg_path).read()
    interesting = [ln for ln in report.splitlines()
                   if "Conditional jump" in ln or "uninitialised" in ln or "Invalid read" in ln
                   or "Invalid write" in ln or "ERROR SUMMARY" in ln or "depends on" in ln]
    print("rc=%s elapsed=%.1fs engine_lines=%d" % (rc, elapsed, len(out)))
    print("depths=%d" % sum(1 for ln in out if ln.startswith("info depth")))
    print("bestmove=%s" % ([ln for ln in out if ln.startswith("bestmove")] or ["NONE"])[-1])
    for ln in interesting[:20]:
        print(ln)


if __name__ == "__main__":
    main()
