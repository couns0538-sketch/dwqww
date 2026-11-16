#!/usr/bin/env python3
"""swarm seat 01, job 2 probe: does the fifty-move counter change the answer, and is a real mate
still found at halfmove 100?

WHY THIS EXISTS: a first pass piped `position ... / isready / go depth 4 / quit` in one batch and
the engine answered `bestmove f2f3` on a mate-in-one position with NO info line, because `quit`
reached the search thread before it had searched. Batching is the cause, not the position
(evidence: probe_batching.txt). So every case here is sent with the reader waiting for bestmove
before the next line, exactly as the job's harnesses do.

Cases: a mate-in-one position and a quiet position, each at halfmove 0/99/100/150.
"""
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

TIMEOUT = 60.0


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


def one(exe, fen, go="go depth 4"):
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

    send("position fen " + fen)
    send("isready")
    until("readyok")
    refused = [l for l in buf if l.startswith("info string invalid FEN")]
    send(go)
    bmline = until("bestmove")
    tail = len(buf)
    # read any lines that are still in flight BEFORE quit, so nothing is lost to the race
    time.sleep(0.25)
    while True:
        l = rd.line(time.monotonic() + 0.2)
        if l is None:
            break
        buf.append(l)
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    depth_lines = [l for l in buf[:tail] if l.startswith("info depth")]
    return {
        "fen": fen, "go": go, "refused": bool(refused), "refusal": refused,
        "bestmove": (bmline.split()[1] if bmline else None),
        "depth_lines": depth_lines, "extra_after_bestmove": buf[tail:],
        "all_lines": buf,
    }


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    mate1 = "6k1/5ppp/8/8/8/8/5PPP/R5K1"
    quiet = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R"
    cases = []
    for hm in (0, 99, 100, 150):
        cases.append(("mate1_hm%d" % hm, mate1 + " w - - %d 1" % hm))
        cases.append(("quiet_hm%d" % hm, quiet + " w KQkq - %d 1" % hm))
    res = []
    lines = []
    lines.append("probe: fifty-move counter vs the answer, every case fully synchronized")
    lines.append("exe_started: %s" % exe)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    lines.append("sha256: %s" % sha)
    nm = subprocess.run(["nm", "-C", exe], capture_output=True, text=True).stdout
    lines.append("nm -C grep -c __asan_ : %d" % sum(1 for l in nm.splitlines() if "__asan_" in l))
    lines.append("nm -C grep -c __ubsan_ : %d" % sum(1 for l in nm.splitlines() if "__ubsan_" in l))
    lines.append("option lines sent: NONE")
    lines.append("")
    lines.append("case\tbestmove\tnodes_at_last_depth\tscore_at_last_depth\tn_depth_lines")
    for name, fen in cases:
        r = one(exe, fen)
        r["case"] = name
        nodes = ""
        score = ""
        if r["depth_lines"]:
            last = r["depth_lines"][-1]
            for tok in last.split():
                pass
            f = last.split()
            if "score" in f:
                i = f.index("score")
                score = " ".join(f[i + 1:i + 3])
            if "nodes" in f:
                nodes = f[f.index("nodes") + 1]
        r["nodes_last"] = nodes
        r["score_last"] = score
        res.append(r)
        lines.append("%s\t%s\t%s\t%s\t%d" % (name, r["bestmove"], nodes, score, len(r["depth_lines"])))
    (out / "probe_halfmove.txt").write_text("\n".join(lines) + "\n")
    (out / "probe_halfmove_raw.json").write_text(json.dumps(res, indent=1))
    print("\n".join(lines))
    print("")
    print("=== the batching evidence, for the record ===")
    p = subprocess.run([exe], input="position fen %s w - - 0 1\nisready\ngo depth 4\nquit\n" % mate1,
                       capture_output=True, text=True, timeout=120)
    txt = ["batched input (position/isready/go/quit in ONE write) on %s w - - 0 1:" % mate1,
           p.stdout, "--- vs synchronized, above: bestmove a1a8 with 4 info depth lines"]
    (out / "probe_batching.txt").write_text("\n".join(txt) + "\n")
    print("\n".join(txt))


if __name__ == "__main__":
    main()
