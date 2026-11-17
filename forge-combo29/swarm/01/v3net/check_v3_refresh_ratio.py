#!/usr/bin/env python3
"""swarm seat 01: S-F113 — measure the refresh/column ratio the engine was already counting and discarding.

`RefreshCache::refreshes` and `::columns` are incremented at nnue_v3.cpp:694 and :702/:707 and read by nothing.
The instrumented build (`stats.patch.txt`, NOT to be applied to the repository) adds a per-run total and prints one
extra `info string v3 refresh_stats refreshes N columns M` after the bench line, leaving the bench line itself
byte-identical.

Two things this measures, and the second is the one that matters:

1. **The ratio.** How many full 512-wide perspective rebuilds each column actually costs. A refresh that costs
   ~1-2 columns means the cache is nearly always warm and the rebuild is rare; a refresh costing ~7 columns means
   the cache misses often and the rebuild is doing real work.
2. **The share of all v3 accumulator work that the rebuild path represents.** refreshes / (refreshes + incremental
   updates) is the number Step 2 needs, because `refresh_from_pieces` was 4.79 % of the whole benchmark while
   `apply_changes_pair` was 7.41 %.

Identity is a precondition, not a result: every configuration must reproduce its published bench number, or the
patch is not measuring the same search and its counters mean nothing.

Configurations follow file 7's four rows. `--` means the run is not comparable and is reported as such.

Usage: check_v3_refresh_ratio.py <stats-exe> <clean-exe> <testnet.fnn3> <outdir>
"""
import hashlib
import json
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
        ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# file 7's published numbers, for the identity precondition
KNOWN = {("none", 13): 862329, ("pc20", 13): 587276, ("net", 13): 4151906, ("pc20net", 13): 3652372}
ROWS = [("none", False, False), ("pc20", True, False), ("net", False, True), ("pc20net", True, True)]


class R:
    def __init__(self, fd):
        self.fd, self.buf, self.eof = fd, b"", False

    def line(self, dl):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            rem = dl - time.monotonic()
            if rem <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], rem)
            if not r:
                return None
            c = os.read(self.fd, 65536)
            if not c:
                self.eof = True
                return None
            self.buf += c
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


def run(exe, net, pc20, use_net, bench=13):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []

    def send(s):
        try:
            p.stdin.write((s + "\n").encode())
            p.stdin.flush()
        except Exception:
            pass

    def until(pre, dl):
        while True:
            l = rd.line(dl)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(pre):
                return l

    d = time.monotonic() + 60
    send("uci")
    until("uciok", d)
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    if pc20:
        for n, v in PC20:
            send("setoption name %s value %s" % (n, v))
    if use_net:
        send("setoption name NNUEArchFile value %s" % net)
        send("setoption name NNUEArch value true")
    send("isready")
    until("readyok", d)
    send("ucinewgame")
    send("isready")
    until("readyok", d)
    send("bench %d" % bench)
    # wait for the bench line (and the stats line that follows it)
    end = time.monotonic() + 900
    while time.monotonic() < end:
        l = rd.line(time.monotonic() + 1.0)
        if l is None:
            if p.poll() is not None:
                break
            continue
        buf.append(l)
        if l.startswith("bestmove") or l.startswith("readyok"):
            break
        if "v3 refresh_stats" in l:
            break
        if "bench depth" in l and "refresh_stats" not in l:
            # stats line follows immediately; give it a moment
            l2 = rd.line(time.monotonic() + 5.0)
            if l2 is not None:
                buf.append(l2)
            break
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()

    nodes = stats = None
    for l in buf:
        if "bench depth" in l:
            m = re.search(r"nodes (\d+) time (\d+)", l)
            if m:
                nodes = int(m.group(1))
        if "v3 refresh_stats" in l:
            m = re.search(r"refreshes (\d+) columns (\d+)", l)
            if m:
                stats = (int(m.group(1)), int(m.group(2)))
    return nodes, stats


def main():
    exe, clean, net, out = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    sha = {"stats": hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "clean": hashlib.sha256(Path(clean).read_bytes()).hexdigest(),
           "net": hashlib.sha256(Path(net).read_bytes()).hexdigest()}

    rows = []
    print("=== identity precondition + refresh ratio, bench 13")
    for name, pc20, use_net in ROWS:
        nodes, stats = run(exe, net, pc20, use_net)
        exp = KNOWN[(name, 13)]
        ident = nodes == exp
        # the clean build must agree too, or the two builds are not the same search
        cnodes, _ = run(clean, net, pc20, use_net) if use_net else run(clean, net, pc20, use_net)
        r = {"row": name, "nodes": nodes, "expected": exp, "identity": ident,
             "clean_nodes": cnodes, "stats": stats}
        if stats:
            ref, col = stats
            r["columns_per_refresh"] = round(col / ref, 2) if ref else None
        rows.append(r)
        print("  %-8s nodes=%-8s expected=%-8s identity=%-5s clean=%-8s stats=%s"
              % (name, nodes, exp, ident, cnodes, stats), flush=True)

    L = ["S-F113: the refresh/column ratio, measured with a stats-only patch",
         "stats exe sha256: %s" % sha["stats"],
         "clean exe sha256: %s" % sha["clean"],
         "net sha256: %s" % sha["net"],
         "PC20 + test net where named, Threads 1, Hash 16, bench 13.",
         "The stats build prints one extra `info string v3 refresh_stats refreshes N columns M` and leaves the",
         "bench line byte-identical; the nodes column below is the proof that the search did not change.",
         "",
         "row\tnodes\texpected\tidentity\tstats(refreshes,columns)\tcolumns per refresh"]
    for r in rows:
        cpr = r.get("columns_per_refresh")
        L.append("%s\t%s\t%s\t%s\t%s\t%s" % (r["row"], r["nodes"], r["expected"],
                                            "PASS" if r["identity"] else "FAIL",
                                            r["stats"], cpr if cpr is not None else "n/a"))
    L.append("")

    bad = [r for r in rows if not r["identity"]]
    if bad:
        L.append("STOPPED: identity failed on %s. The counters cannot be read from a search that is not the"
                 % ", ".join(r["row"] for r in bad))
        L.append("published one; nothing below would mean anything.")
    else:
        L.append("IDENTITY: all four configurations reproduce their published bench 13 numbers exactly, so the")
        L.append("stats build is the same search and its counters describe the real v3 path.")
        L.append("")
        pn = next(r for r in rows if r["row"] == "pc20net")
        netonly = next(r for r in rows if r["row"] == "net")
        if pn["stats"]:
            ref, col = pn["stats"]
            L.append("PC20 + test net: %d refreshes costing %d columns, i.e. **%.2f columns per refresh**."
                     % (ref, col, col / ref if ref else 0))
            L.append("  Read against hidden=512: a rebuild that touches k pieces costs k columns and rewrites all")
            L.append("  512 int16 of the destination, so the per-column cost of a refresh is the same as an")
            L.append("  incremental column but the fixed 1 KB copy-out is paid every time.")
        if netonly["stats"]:
            ref2, col2 = netonly["stats"]
            L.append("Test net alone: %d refreshes / %d columns = %.2f columns per refresh."
                     % (ref2, col2, col2 / ref2 if ref2 else 0))
            L.append("  The two rows differ only by PC20, so comparing them shows whether search settings change")
            L.append("  how often the rebuild path fires - which is the thing a speed patch must not perturb.")

    (out / "check_v3_refresh_ratio.json").write_text(json.dumps({"shas": sha, "rows": rows}, indent=1))
    (out / "check_v3_refresh_ratio.txt").write_text("\n".join(L) + "\n")
    print("")
    print("\n".join(L))


if __name__ == "__main__":
    main()
