#!/usr/bin/env python3
"""swarm seat 01: settle the 2640 question with MY OWN instrument (`-D_GLIBCXX_DEBUG`).

Seat 17 and seat 07 both say line 2640 `root_candidates.front()` is NEVER reached with an empty list, and
that the printed `bestmove 0000` comes from the empty-root early path at search.cpp:2253. My earlier S-C3
said the opposite, which was an INFERENCE from the printed 0000, not a measurement.

`-D_GLIBCXX_DEBUG` makes libstdc++ check container access: `front()` on an empty vector aborts the process
with a diagnostic. So:
  CONTROL   a tiny program that calls front() on an empty vector under the SAME flag must abort, proving the
            build really has the checking enabled (without this the whole test means nothing).
  CASES     the six searchmoves cases must NOT abort if 2640 is never reached with an empty list.
If a case aborts, 2640 IS reached empty. If no case aborts and the control does, the line is not reached.

Usage: check_2640_instrument.py <debug-exe> <outdir>
"""
import hashlib
import json
import os
import select
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TIMEOUT = 120.0
CONTROL_SRC = """
#include <vector>
#include <iostream>
int main() {
    std::vector<int> v;              // empty
    std::cout << "about to call front() on an empty vector" << std::endl;
    std::cout << v.front() << std::endl;   // must abort under _GLIBCXX_DEBUG
    std::cout << "NOT REACHED" << std::endl;
    return 0;
}
"""


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
    until("readyok")
    send(go)
    bml = until("bestmove")
    time.sleep(0.1)
    send("quit")
    try:
        p.wait(timeout=40)
    except Exception:
        p.kill()
    text = "\n".join(buf)
    aborted = ("__glibcxx_requires_nonempty" in text or "attempt to access" in text
               or "Error: attempt to access an element" in text
               or "Aborted" in text or p.returncode not in (0, None) and p.returncode < 0)
    return {"position": position, "go": go, "bestmove": bml.split()[1] if bml else None,
            "aborted": aborted, "returncode": p.returncode, "text": text}


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    lines = ["settling search.cpp:2640 with my own -D_GLIBCXX_DEBUG instrument",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest()]

    # CONTROL: same flag, same standard library, an empty front() must abort.
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "c.cpp"
        src.write_text(CONTROL_SRC)
        binp = Path(td) / "c"
        cp = subprocess.run(["g++", "-std=c++20", "-O1", "-D_GLIBCXX_DEBUG", str(src), "-o", str(binp)],
                            capture_output=True, text=True)
        if cp.returncode != 0:
            print("control failed to compile:\n" + cp.stderr)
            (out / "check_2640_instrument.txt").write_text(
                "CONTROL FAILED TO COMPILE, so the -D_GLIBCXX_DEBUG library is not usable here and this\n"
                "test proves nothing. Compiler said:\n" + cp.stderr + "\n")
            return
        cr = subprocess.run([str(binp)], capture_output=True, text=True)
        control_aborted = cr.returncode != 0
        lines.append("control (empty front() under the same flag): returncode %d -> %s"
                     % (cr.returncode, "ABORTS (checking is really on)" if control_aborted
                        else "DID NOT ABORT (test would be meaningless)"))
        lines.append("control output: " + (cr.stdout + cr.stderr).strip().replace("\n", " | ")[:400])

    cases = [
        ("no_names", "position startpos", "go searchmoves depth 2"),
        ("bogus_name", "position startpos", "go searchmoves a1a1 depth 2"),
        ("illegal_pair", "position startpos", "go searchmoves e2e5 depth 2"),
        ("one_legal", "position startpos", "go searchmoves e2e4 depth 2"),
        ("two_legal", "position startpos", "go searchmoves e2e4 d2d4 depth 2"),
        ("plain_control", "position startpos", "go depth 2"),
    ]
    lines.append("")
    lines.append("case\tbestmove\texit\tglibcxx_diagnostic\tverdict")
    rows = []
    any_abort = False
    for name, pos, go in cases:
        r = one(exe, pos, go)
        r["case"] = name
        rows.append(r)
        diag = "__glibcxx" in r["text"] or "attempt to access" in r["text"]
        if r["aborted"]:
            any_abort = True
        verdict = ("ABORTED -> the line CAN see an empty list" if r["aborted"]
                   else "no abort -> 2640 never saw an empty list here")
        lines.append("%s\t%s\t%s\t%s\t%s" % (name, r["bestmove"], r["returncode"], diag, verdict))
        print("%-14s bm=%-6s rc=%-3s diag=%-5s %s"
              % (name, r["bestmove"], r["returncode"], diag, verdict), flush=True)

    lines.append("")
    if control_aborted and not any_abort:
        lines.append("VERDICT: the instrument works (control aborts) and NO searchmoves case aborts, so line")
        lines.append("2640 does NOT execute with an empty root_candidates on any of these six cases.")
        lines.append("This REFUTES my own earlier mechanism claim in S-C3. The bestmove 0000 must come from")
        lines.append("the empty-root path, not from an empty front() at 2640.")
    elif not control_aborted:
        lines.append("VERDICT: INCONCLUSIVE — the control did not abort, so the flag is not checking.")
    else:
        lines.append("VERDICT: at least one case aborted -> 2640 DOES see an empty list.")
    (out / "check_2640_instrument.json").write_text(json.dumps(
        {"control_aborted": control_aborted, "cases": rows}, indent=1))
    text = "\n".join(lines) + "\n"
    (out / "check_2640_instrument.txt").write_text(text)
    print("")
    print(text)


if __name__ == "__main__":
    main()
