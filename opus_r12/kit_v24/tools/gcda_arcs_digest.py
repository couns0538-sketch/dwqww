#!/usr/bin/env python3
"""gcda_arcs_digest.py PROFILE_DIR [GCOV_DUMP] - per .gcda, sha256 of the FUNCTION headers + 'arcs' (edge) counters only.
Edge counts from the frozen bench workload are deterministic, so this digest must be identical between two training runs
of the same instrumented exe. The value-profile counters (topn/ior/average/indirect_call/time_profiler) are left out on
purpose: they record addresses (ASLR) and bench elapsed-ms divisors, so whole-file .gcda sha256s differ run to run.
Names are printed relative to PROFILE_DIR, sorted bytewise. Default GCOV_DUMP: gcov-dump-14, else gcov-dump.
v2.1: gcov-dump prefixes each line with "<path>:". The prefix is now stripped as an exact string (QA fix), so a Windows
drive colon (C:\\...) no longer leaks the path into the digest; \\ and / spellings of the path are both accepted."""
import hashlib, os, re, shutil, subprocess, sys

def prefixes(path):
    """Exact gcov-dump line prefixes for this file: as given, plus / and \\ spellings (longest first)."""
    c = {path + ":", path.replace("\\", "/") + ":", path.replace("/", "\\") + ":"}
    return sorted(c, key=len, reverse=True)

def strip_prefix(line, pres):
    for pre in pres:
        if line.startswith(pre): return line[len(pre):], True
    return line, False

def digest_dump(text, path):
    """sha256 hex of FUNCTION headers + arcs counters in one gcov-dump -l output; returns (hex, unmatched_line_count)."""
    pres, keep, h, unmatched = prefixes(path), False, hashlib.sha256(), 0
    for line in text.splitlines():
        body, ok = strip_prefix(line, pres); unmatched += (not ok)
        if "FUNCTION ident=" in body: keep = False; h.update(body.strip().encode() + b"\n"); continue
        if "COUNTERS" in body: keep = " COUNTERS arcs " in body or body.strip().split(":COUNTERS")[-1].strip().startswith("arcs")
        if keep: h.update(re.sub(r"\s+", " ", body.strip()).encode() + b"\n")
    return h.hexdigest(), unmatched

def main(argv):
    d = argv[1]
    tool = argv[2] if len(argv) > 2 else (shutil.which("gcov-dump-14") or shutil.which("gcov-dump"))
    files = []
    for root, _, fs in os.walk(d):
        files += [os.path.relpath(os.path.join(root, f), d) for f in fs if f.endswith(".gcda")]
    for rel in sorted(files, key=lambda s: s.encode()):
        path = os.path.join(d, rel)
        out = subprocess.run([tool, "-l", path], capture_output=True, text=True, check=True).stdout
        hexd, unmatched = digest_dump(out, path)
        if unmatched: print(f"warning: {unmatched} gcov-dump lines without the file prefix in {rel}", file=sys.stderr)
        print(f"{hexd}  {rel.replace(os.sep, '/')}")

if __name__ == "__main__":
    main(sys.argv)
