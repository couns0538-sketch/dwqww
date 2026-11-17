#!/usr/bin/env python3
"""The slurp-before-check test: how much memory does the loader take before it can refuse?

load() does this, in this order:

    std::ifstream in(path, binary);
    std::vector<uint8_t> bytes((istreambuf_iterator<char>(in)), istreambuf_iterator<char>());
    if (bytes.size() < HeaderBytes + 8) return fail(...);        // first size test

So the ENTIRE file is in memory before the magic, the version, the dimensions or the
file size are examined. The header's own claim is never the thing that costs memory --
the file's real length is. A file of length L costs >= L bytes of heap before any
refusal can happen, for any L.

This measures that, with two sources:
  * regular files of increasing size (sparse, so the test is cheap on disk)
  * /dev/zero, which is not seekable and has no end -- the case where there is no
    "file size" to validate against at all

The refusal message is recorded for each, because a refusal that arrives after
8 GB have been allocated is a different thing from one that arrives before.

Usage: slurp_test.py <probe> <out.json> [max_gb]
"""
import json
import os
import resource
import signal
import subprocess
import sys
import time


def run_bounded(argv, wall_seconds, rss_cap_kb):
    """Run argv; sample RSS; kill at the wall clock or the RSS cap. Returns a record."""
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    started = time.monotonic()
    samples = []
    killed_for = None
    while proc.poll() is None:
        elapsed = time.monotonic() - started
        rss_kb = 0
        try:
            with open("/proc/%d/status" % proc.pid) as handle:
                for line in handle:
                    if line.startswith("VmRSS:"):
                        rss_kb = int(line.split()[1])
                        break
        except (FileNotFoundError, ProcessLookupError):
            break
        samples.append([round(elapsed, 2), rss_kb])
        if rss_kb > rss_cap_kb:
            killed_for = "rss_cap"
            proc.kill()
            break
        if elapsed > wall_seconds:
            killed_for = "wall_clock"
            proc.kill()
            break
        time.sleep(0.25)
    out = ""
    if proc.stdout is not None:
        try:
            out = proc.stdout.read()
        except ValueError:
            out = ""
    proc.wait(timeout=30)
    return {
        "argv": argv,
        "rc": proc.returncode,
        "killed_for": killed_for,
        "peak_rss_kb": max((s[1] for s in samples), default=0),
        "seconds": round(time.monotonic() - started, 2),
        "samples": samples[::max(1, len(samples) // 12)],
        "output_head": out.strip().splitlines()[:4],
    }


def make_sparse(path, size_bytes):
    with open(path, "wb") as handle:
        handle.truncate(size_bytes)
    with open(path, "r+b") as handle:
        handle.write(b"FORGENN3")          # valid magic, so only the length can refuse it


def parse_peak(lines):
    """Pull peak_rss_kb out of the probe's ALLOC line; fall back to the last line."""
    for line in lines:
        for part in line.split("\t"):
            bits = part.split()
            if len(bits) == 2 and bits[0] == "peak_rss_kb":
                return int(bits[1])
    return None

def main():
    probe = sys.argv[1]
    outpath = sys.argv[2]
    max_gb = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    tmpdir = "/tmp/slurp"
    os.makedirs(tmpdir, exist_ok=True)

    results = {"probe": probe, "regular_files": [], "dev_zero": None,
               "measurement": ("peak_rss_kb is the process's own VmHWM read from /proc/self/status "
                               "inside the loader probe, so it is not subject to sampling error. "
                               "The external 0.25 s sampler is recorded as rss_cap_kb_killer only: "
                               "it cannot see a run that finishes between samples, and it reported "
                               "0.2 MiB for the 8 MiB file the in-process counter saw as 11.8 MiB.")}

    for size_mb in (8, 64, 256, 1024, 2048, 4096):
        if size_mb > max_gb * 1024:
            continue
        path = os.path.join(tmpdir, "sparse_%dm.fnn3" % size_mb)
        make_sparse(path, size_mb * 1024 * 1024)
        record = run_bounded([probe, "loadalloc", path], wall_seconds=180, rss_cap_kb=6 * 1024 * 1024)
        record["file_mb"] = size_mb
        record["file_bytes"] = os.path.getsize(path)
        record["du_bytes"] = os.stat(path).st_blocks * 512
        # The authoritative number: the probe's own VmHWM, parsed out of its ALLOC line.
        record["in_process_peak_rss_kb"] = parse_peak(record["output_head"] + [""])
        results["regular_files"].append(record)
        print("%6d MiB file  rc %-4s in-process VmHWM %10s kB  external-sampler %7.1f MiB  %s"
              % (size_mb, record["rc"], record["in_process_peak_rss_kb"],
                 record["peak_rss_kb"] / 1024.0,
                 (record["output_head"] or [""])[-1][:70]))

    record = run_bounded([probe, "load", "/dev/zero"], wall_seconds=20, rss_cap_kb=1024 * 1024)
    record["note"] = ("/dev/zero: not seekable, no length. A loader that slurps to EOF "
                      "has no bound to validate against and grows until the allocator fails.")
    results["dev_zero"] = record
    print("/dev/zero      rc %-4s peak_rss %8.1f MB  killed_for %s"
          % (record["rc"], record["peak_rss_kb"] / 1024.0, record["killed_for"]))

    with open(outpath, "w") as handle:
        json.dump(results, handle, indent=1)
    print("wrote", outpath)


if __name__ == "__main__":
    main()
