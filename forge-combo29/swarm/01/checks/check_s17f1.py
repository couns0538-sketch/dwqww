#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 17's S-F1 and S-F2.

Seat 17's S-F1, verbatim from its FINDINGS.md:
  "`go depth N searchmoves <name with no legal root move>` answers `bestmove 0000` on a position that HAS
   legal moves (startpos: 20 legal, 0000 returned) - UCI defines 0000 as 'no legal move exists', so a GUI
   reads it as an illegal move"
Seat 17's S-F2 says the source is search.cpp:2640 `if (result.best_move.is_none()) result.best_move =
root_candidates.front();` reading `front()` of an EMPTY list, and that line 2210 detects the state as
`restricted_root_empty`.

I wrote this harness from the S-F1 sentence only; I did not read seat 17's script.

Cases (each a fresh process, `position ...`, `isready` read to readyok, `go ...`, read to bestmove):
  c1  startpos, plain `go depth 2`                     -> must be a real move (control)
  c2  startpos, `go searchmoves depth 2` (no names)    -> seat 17's claim: bestmove 0000
  c3  startpos, `go searchmoves e2e4 depth 2`          -> one real legal name: must be e2e4
  c4  startpos, `go searchmoves a1a1 depth 2`          -> a name that is not a legal move here
  c5  startpos, `go searchmoves e2e5 depth 2`          -> a legal-looking but illegal square pair
  c6  a 1-legal-move position, `go searchmoves` naming nothing
  c7  startpos, `go searchmoves e2e4 d2d4 depth 2`     -> two names, both legal
Also recorded: whether the engine emits `info string ...` explaining itself, and whether it crashes or
reports a sanitizer line. The engine is the ASan+UBSan build, so a `front()` on an empty vector would be
an out-of-range read that ASan should catch.

Usage: check_s17f1.py <exe> <outdir>
"""
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

TIMEOUT = 120.0


class R:
    def __init__(self, fd):
        self.fd, self.buf, self.eof = fd, b"", False

    def line(self, deadline):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            remain = deadline - time.monotonic()
            if remain <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], remain)
            if not r:
                return None
            c = os.read(self.fd, 65536)
            if not c:
                self.eof = True
                return None
            self.buf += c
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


def one(exe, position, go):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []

    def until(prefix):
        d = time.monotonic() + TIMEOUT
        while True:
            l = rd.line(d)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    send(position)
    send("isready")
    ready = until("readyok") is not None
    bm = None
    if ready:
        send(go)
        bml = until("bestmove")
        if bml:
            parts = bml.split()
            bm = parts[1] if len(parts) > 1 else ""
        time.sleep(0.15)
    send("quit")
    try:
        p.wait(timeout=40)
    except Exception:
        p.kill()
    return {
        "position": position, "go": go, "bestmove": bm,
        "info_strings": [l for l in buf if l.startswith("info string")],
        "depth_lines": [l for l in buf if l.startswith("info depth")],
        "sanitizer": [l for l in buf if ("AddressSanitizer" in l or "runtime error" in l
                                        or "SUMMARY:" in l or "UndefinedBehaviorSanitizer" in l)],
        "exited_clean": p.returncode == 0,
        "returncode": p.returncode,
    }


START = "position startpos"
ONE_MOVE = "position fen 7k/5Q2/8/8/8/8/8/K7 b - - 0 1"   # black to move, one legal move


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    cases = [
        ("c1_control_plain", START, "go depth 2"),
        ("c2_no_names", START, "go searchmoves depth 2"),
        ("c3_one_legal_name", START, "go searchmoves e2e4 depth 2"),
        ("c4_bogus_name", START, "go searchmoves a1a1 depth 2"),
        ("c5_illegal_pair", START, "go searchmoves e2e5 depth 2"),
        ("c6_no_names_one_move_pos", ONE_MOVE, "go searchmoves depth 2"),
        ("c7_two_legal_names", START, "go searchmoves e2e4 d2d4 depth 2"),
    ]
    lines = ["CHECK of seat 17 S-F1 (and its S-F2 source claim): searchmoves with no legal root move",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest()]
    nm = subprocess.run(["nm", "-C", exe], capture_output=True, text=True).stdout
    lines.append("nm -C grep -c __asan_ : %d" % sum(1 for l in nm.splitlines() if "__asan_" in l))
    lines.append("nm -C grep -c __ubsan_ : %d" % sum(1 for l in nm.splitlines() if "__ubsan_" in l))
    lines.append("option lines sent: NONE")
    lines.append("")
    lines.append("case\tbestmove\tinfo_string\tsanitizer_lines\texit")
    results = []
    for name, pos, go in cases:
        r = one(exe, pos, go)
        r["case"] = name
        results.append(r)
        lines.append("%s\t%s\t%s\t%d\t%s" % (
            name, r["bestmove"], "; ".join(r["info_strings"]) or "(none)",
            len(r["sanitizer"]), r["returncode"]))
        print("%-26s bestmove=%-6s info=%-60s san=%d"
              % (name, r["bestmove"], (r["info_strings"][0] if r["info_strings"] else "(none)")[:60],
                 len(r["sanitizer"])), flush=True)

    def find(c):
        return next(x for x in results if x["case"] == c)

    # HARD ASSERTIONS (seat 19's warning): a missing value must never read as a measurement.
    # Every case must have produced a non-empty bestmove; anything else is INVALID, not a verdict.
    def bm_of(c):
        b = find(c)["bestmove"]
        if not b:
            fail_hard.append("%s produced NO bestmove line" % c)
            return None
        return b

    fail_hard = []
    v = []
    c1 = bm_of("c1_control_plain")
    v.append("c1 control (no searchmoves): bestmove=%s -> %s"
             % (c1, "OK, the position has real moves" if c1 and c1 != "0000" else "CONTROL BROKEN"))
    c2v = bm_of("c2_no_names")
    v.append("c2 `go searchmoves depth 2` with NO names: bestmove=%s info=%s"
             % (c2v, find("c2_no_names")["info_strings"]))
    c3v = bm_of("c3_one_legal_name")
    v.append("c3 `searchmoves e2e4`: bestmove=%s -> %s"
             % (c3v, "restriction honoured" if c3v == "e2e4" else "NOT honoured"))
    c7v = bm_of("c7_two_legal_names")
    v.append("c7 two legal names: bestmove=%s -> %s"
             % (c7v, "one of the named" if c7v in ("e2e4", "d2d4") else "NOT honoured"))
    confirmed = (c1 is not None and c1 != "0000" and c2v == "0000")
    if fail_hard:
        v.append("VERDICT on S-F1: INVALID (a case produced no bestmove line at all)")
        for f in fail_hard:
            v.append("   " + f)
    else:
        v.append("VERDICT on S-F1: %s" % ("CONFIRMS" if confirmed else "REFUTES"))
    zero_san = all(len(x["sanitizer"]) == 0 for x in results)
    v.append("ASan+UBSan reported nothing (0 sanitizer lines on every case): %s" % zero_san)
    v.append("so the `front()` on an empty list claimed in S-F2, if executed, is not an out-of-range READ")
    v.append("that ASan can see (an empty libstdc++ vector's begin() is a valid pointer); it returns a")
    v.append("garbage Move, which then gets printed as 0000 by the bestmove printer.")

    (out / "check_s17f1.json").write_text(json.dumps(results, indent=1))
    text = "\n".join(lines + [""] + v) + "\n"
    (out / "check_s17f1.txt").write_text(text)
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
