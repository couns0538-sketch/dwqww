#!/usr/bin/env python3
"""paced_session.py <exe> <session-file> <out-prefix> [--wait-after-go S]

Feeds a UCI session ONE LINE AT A TIME and waits after every `go` until the engine prints
`bestmove`, or a timeout. This is required: if the whole session is written at once, the next
`position`/`ucinewgame`/`setoption` line calls stop_search() and the running search is aborted
(that trap is described in REPORT_job1.md; it silently ruined my first version of this test).

Output: <prefix>.out.txt (engine stdout+stderr, interleaved by arrival), <prefix>.meta
"""
import json
import os
import re
import selectors
import subprocess
import sys
import time


def main():
    exe = os.path.realpath(sys.argv[1])
    session = sys.argv[2]
    prefix = sys.argv[3]
    wait_after_go = 120.0
    if len(sys.argv) > 4:
        wait_after_go = float(sys.argv[4])

    with open(session) as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]

    env = dict(os.environ)
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    sel = selectors.DefaultSelector()
    sel.register(p.stdout, selectors.EVENT_READ)
    transcript = []
    starts = []          # (label, monotonic time) for each go
    search_ends = []     # monotonic time bestmove seen

    def drain(wait_until_readyok=False, wait_until_bestmove=False, timeout=None):
        """Read whatever the engine says; return when the condition or the timeout hits."""
        t0 = time.monotonic()
        bestmoves = 0
        readyoks = 0
        while True:
            if wait_until_bestmove and bestmoves:
                return
            if wait_until_readyok and readyoks:
                return
            for key, _ in sel.select(timeout=0.05):
                chunk = os.read(key.fileobj.fileno(), 65536).decode(errors="replace")
                if not chunk:
                    return
                for ln in chunk.splitlines(True):
                    transcript.append(ln)
                    s = ln.strip()
                    if s.startswith("bestmove"):
                        bestmoves += 1
                        search_ends.append(time.monotonic())
                    if s == "readyok":
                        readyoks += 1
            if timeout is not None and time.monotonic() - t0 > timeout:
                return

    for ln in lines:
        s = ln.strip()
        p.stdin.write(ln + "\n")
        p.stdin.flush()
        if s.startswith("go "):
            starts.append((s, time.monotonic()))
            if " infinite" in s:
                drain(timeout=0.5)
            else:
                drain(wait_until_bestmove=True, timeout=wait_after_go)
        elif s == "isready":
            drain(wait_until_readyok=True, timeout=30)
        elif s == "uci":
            drain(wait_until_readyok=False, timeout=1.0)
        elif s.startswith("stop"):
            drain(wait_until_bestmove=True, timeout=wait_after_go)
        else:
            drain(timeout=0.05)

    if p.stdin and not p.stdin.closed:
        p.stdin.close()
    drain(timeout=5.0)
    p.wait(timeout=60)

    with open(prefix + ".out.txt", "w") as f:
        f.write("".join(transcript))
    meta = {
        "exe_started": exe,
        "exe_sha256": subprocess.run(["sha256sum", exe], capture_output=True,
                                     text=True).stdout.split()[0],
        "id_name": next((l.strip() for l in transcript if l.startswith("id name")), ""),
        "session_file": os.path.abspath(session),
        "go_lines": [s for s, _ in starts],
        "exit_code": p.returncode,
        "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                   capture_output=True, text=True).stdout.strip(),
    }
    with open(prefix + ".meta", "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
