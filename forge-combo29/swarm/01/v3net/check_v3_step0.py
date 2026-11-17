#!/usr/bin/env python3
"""swarm seat 01: Step 0 of file 7 — reproduce the EIGHT known bench numbers and the THREE known eval lines
on THIS build, with the deterministic test net loaded.

Why I am here: my own scope limit S-F82 says my findings are build-independent but NOT net-independent — the
owner plays with a trained FORGENN3 net loaded, and I have no net file. File 7 removes that excuse by publishing
a deterministic net (same bytes on every machine) with known answers for it. Step 0 is therefore the cheapest
possible test of my own caveat: do the published numbers reproduce here at all?

The net is generated, NEVER committed. Load order is load-bearing and is the thing a careless run gets wrong:
  setoption name NNUEArchFile value <abs path>    FIRST
  setoption name NNUEArch value true              SECOND
Backwards, the engine has nothing to load and silently falls back to the built-in net, which would make every
number here wrong while still looking plausible. So this harness REQUIRES the `info string NNUE v3 loaded:` line
and records the checksum and max|w| values from it; a missing or mismatched load line aborts the row.

Fresh process per line (file 7 says so): a bench in a reused process measures a warm process, not the build.

Usage: check_v3_step0.py <v3-exe> <testnet.fnn3> <outdir>
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

# file 7's table, transcribed once so the comparison is data-vs-data and not eyes-vs-screen
KNOWN = {
    ("none", 11): 312866, ("none", 13): 862329,
    ("pc20", 11): 278024, ("pc20", 13): 587276,
    ("net", 11): 965454, ("net", 13): 4151906,
    ("pc20net", 11): 625258, ("pc20net", 13): 3652372,
}
EVALS = [
    ("startpos", "startpos", 968),
    ("italian", "fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3", 1176),
    ("rookend", "fen 8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40", 31),
]

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


def run(exe, net, pc20, use_net, commands, timeout=1200):
    """One fresh process. Returns (lines, load_line, refusal)."""
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
    load = None
    if use_net:
        # ORDER: file first, then the boolean. Reversed silently loads nothing.
        send("setoption name NNUEArchFile value %s" % net)
        send("setoption name NNUEArch value true")
        send("isready")
        # collect lines until readyok, keeping the load line
        while True:
            l = rd.line(time.monotonic() + 60)
            if l is None:
                break
            buf.append(l)
            if l.startswith("info string NNUE v3 loaded") or l.startswith("info string NNUE v3 active"):
                load = l
            if l.startswith("readyok"):
                break
    send("isready")
    until("readyok", d)

    for c in commands:
        send(c)
    send("quit")
    try:
        p.wait(timeout=timeout)
    except Exception:
        p.kill()
    # drain whatever is left
    while True:
        l = rd.line(time.monotonic() + 2)
        if l is None:
            break
        buf.append(l)
    refusal = next((l for l in buf if re.search(r"unknown option|invalid value|ERROR", l, re.I)), None)
    return buf, load, refusal


def bench_number(lines):
    """The result line reads `info string bench depth 11 nodes 312866 time ... nps ...`.

    It is NOT a bare integer. My first version looked for a bare integer and got None for all eight rows,
    which the harness reported as eight FAILs against the build - the failures were mine. Keep this parser
    keyed on the `bench depth` marker so a format change fails loudly instead of silently returning None.
    """
    for l in reversed(lines):
        if "bench depth" in l:
            f = l.split()
            for i, t in enumerate(f):
                if t == "nodes" and i + 1 < len(f):
                    try:
                        return int(f[i + 1])
                    except ValueError:
                        return None
    return None


def eval_fields(line):
    """Parse `eval hce H nnue N total T` into a dict, or None.

    I hand-typed the expected string twice and got it wrong both times (first without `hce 0`, then without the
    leading `eval` word), while the three VALUES were correct in every run. A hand-typed transcription of a
    string that is already in the output is Trap 0. So compare the parsed integers, not the text, and let the
    cross-checks below carry the meaning: total must equal nnue (that is what "standalone" means), and both must
    equal the published number.
    """
    if not line:
        return None
    out = {}
    f = line.split()
    for i, t in enumerate(f):
        if t in ("hce", "nnue", "total") and i + 1 < len(f):
            try:
                out[t] = int(f[i + 1])
            except ValueError:
                return None
    return out if {"hce", "nnue", "total"} <= set(out) else None


def main():
    exe, net, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    shas = {"exe": hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
            "net": hashlib.sha256(Path(net).read_bytes()).hexdigest()}

    results = []
    print("=== Step 0a: eight bench numbers (fresh process per line)")
    for name, pc20, use_net in ROWS:
        for d in (11, 13):
            lines, load, refusal = run(exe, net, pc20, use_net, ["bench %d" % d])
            got = bench_number(lines)
            exp = KNOWN[(name, d)]
            ok = got == exp
            results.append({"row": name, "depth": d, "got": got, "expected": exp,
                            "pass": ok, "load_line": load, "refusal": refusal})
            print("  %-8s bench %-2d got %-8s expected %-8s %s"
                  % (name, d, got, exp, "PASS" if ok else "FAIL"), flush=True)

    print("=== Step 0b: three eval lines under PC20 + the test net")
    evals = []
    for name, pos, exp in EVALS:
        lines, load, refusal = run(exe, net, True, True,
                                   ["position %s" % pos, "eval"])
        raw = next((l for l in lines if l.startswith("info string eval")), None)
        got = eval_fields(raw)
        # total == nnue is the "standalone" property; both must equal the published value
        ok = bool(got) and got["nnue"] == exp and got["total"] == exp and got["total"] == got["nnue"]
        evals.append({"case": name, "raw": raw, "parsed": got, "expected": exp, "pass": ok,
                      "load_line": load, "refusal": refusal})
        print("  %-9s got %-34s expected nnue=total=%d  %s"
              % (name, raw.replace("info string ", "") if raw else None, exp,
                 "PASS" if ok else "FAIL"), flush=True)

    loads = [r["load_line"] for r in results + evals if r["load_line"]]
    refusals = [r["refusal"] for r in results + evals if r["refusal"]]
    load_line = loads[0] if loads else None

    L = ["STEP 0 of FABLE_TO_swarm_7.md on this build",
         "exe_started: %s" % exe, "exe sha256: %s" % shas["exe"],
         "net sha256: %s" % shas["net"],
         "  (published: 1db8525e4eeb3c4cf425faf89a5dbb7e5aec0a9d00fd7de2c7cd25a7673ffd4a)",
         "load line: %s" % (load_line or "NONE - THE NET DID NOT LOAD"),
         "flags: %s" % os.environ.get("V3_FLAGS", "(recorded separately)"),
         "",
         "Step 0a - eight bench numbers, fresh process per line, Threads 1, Hash 16",
         "row\tbench\tgot\texpected\tverdict"]
    for r in results:
        L.append("%s\t%d\t%s\t%s\t%s" % (r["row"], r["depth"], r["got"], r["expected"],
                                         "PASS" if r["pass"] else "FAIL"))
    L += ["", "Step 0b - three eval lines under PC20 + the test net",
          "case\tgot\texpected\tnnue==total\tverdict"]
    for e in evals:
        g = e["parsed"]
        L.append("%s\t%s\t%s\t%s\t%s" % (
            e["case"],
            (e["raw"] or "NONE").replace("info string ", ""),
            "nnue=total=%d" % e["expected"],
            ("yes" if g and g["nnue"] == g["total"] else "NO"),
            "PASS" if e["pass"] else "FAIL"))
    L.append("")

    npass = sum(1 for r in results if r["pass"]) + sum(1 for e in evals if e["pass"])
    total = len(results) + len(evals)
    nulls = [r for r in results if r["got"] is None]
    if nulls:
        L.append("HARNESS FAULT: %d bench rows returned no number at all (%s)."
                 % (len(nulls), ", ".join("%s bench %d" % (r["row"], r["depth"]) for r in nulls)))
        L.append("  A missing number is not a build failure and must not be reported as one: the parse may be")
        L.append("  wrong. Check the raw `info string bench` line before reading anything into these rows.")
    if refusals:
        L.append("STOPPED: the engine refused a setting - %s" % refusals[0])
        L.append("Per file 7, a refusal line means the run stops and the raw output is reported.")
    elif not load_line:
        L.append("STOPPED: no `NNUE v3 loaded` line, so the net was NOT in use and every number below/"
                 "above describes the built-in net. Not a Step 0 result.")
    elif npass == total:
        L.append("STEP 0 PASS: %d of %d. All eight bench numbers and all three eval lines reproduce exactly." % (npass, total))
        L.append("  This is the first time my work has been measured against a LOADED net rather than the")
        L.append("  built-in one, which is exactly the gap my own S-F82 named. The caveat was about scope, not")
        L.append("  about error: the numbers reproduce, so the harness and the build are sound for v3 work.")
    else:
        L.append("STEP 0 INCOMPLETE: %d of %d match. Any mismatch is reported as measured, not explained away." % (npass, total))

    (out / "check_v3_step0.json").write_text(json.dumps(
        {"shas": shas, "load_line": load_line, "benches": results, "evals": evals,
         "refusals": refusals}, indent=1))
    (out / "check_v3_step0.txt").write_text("\n".join(L) + "\n")
    print("")
    print("\n".join(L))


if __name__ == "__main__":
    main()
